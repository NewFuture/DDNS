/**
 * Multi-turn AI Response Script for GitHub Issues
 * 
 * This script handles AI-powered responses to GitHub issues using a multi-turn
 * conversation approach with upfront strategy guidance:
 * 
 * - All classification-specific strategies are included in the initial system prompt
 * - This allows the AI to use "Relevant Files to Consider" guidance when requesting files
 * - The AI classifies the issue and requests appropriate files in turn 1
 * - Subsequent turns provide requested files until a final response is generated
 */

module.exports = async ({ github, context, core, fs, path }) => {
  const apiUrl = process.env.OPENAI_URL;
  const apiKey = process.env.OPENAI_KEY;

  if (!apiUrl || !apiKey) {
    core.setFailed('OPENAI_URL and OPENAI_KEY must be set');
    return;
  }

  // Read system prompt and extract directory structure from AGENTS.md
  let systemPrompt, directoryStructure;
  try {
    systemPrompt = fs.readFileSync('.github/prompts/issue-assistant.md', 'utf8');
    const agentsMd = fs.readFileSync('AGENTS.md', 'utf8');

    // Extract Directory Structure section from AGENTS.md
    // Flexible regex: allow any heading level, variable whitespace, optional code block language, case-insensitive
    const structureMatch = agentsMd.match(/#{2,6}\s+Directory Structure[\s\S]*?```(?:\w+)?\s*\n([\s\S]*?)\n```/i);
    if (!structureMatch) {
      core.setFailed('Failed to extract Directory Structure from AGENTS.md. Expected a heading like "## Directory Structure" followed by a code block (optionally with a language specifier).');
      return;
    }
    directoryStructure = structureMatch[1].trim();

    // Replace {{DirectoryStructure}} placeholder in system prompt
    systemPrompt = systemPrompt.replace('{{DirectoryStructure}}', directoryStructure);
  } catch (error) {
    console.error('Error reading required files:', error);
    core.setFailed('Failed to read required files: ' + error.message);
    return;
  }

  const classifications = ['bug', 'feature', 'question'];

  // Issue details
  const issueTitle = context.payload.issue.title ? context.payload.issue.title.substring(0, 500) : '(No title)';
  const issueBody = context.payload.issue.body ? context.payload.issue.body.substring(0, 10000) : '(No description provided)';
  const issueAuthor = context.payload.issue.user.login;

  // Constants
  const MAX_FILES_PER_TURN = 10;
  // Maximum file size (in bytes) for context sent to the AI. 50KB was chosen to balance
  // providing enough context for the AI to understand the code, while staying well within
  // OpenAI API token and processing limits. Larger files may exceed token limits or slow
  // down processing, while smaller limits may omit important context.
  const MAX_FILE_SIZE = 50000; // 50KB
  const MAX_TURNS = 3;
  // Delay in milliseconds between API calls to respect rate limits (50K tokens per minute).
  // Configurable via RATE_LIMIT_DELAY_MS environment variable. Default is 31 seconds.
  const RATE_LIMIT_DELAY_MS = parseInt(process.env.RATE_LIMIT_DELAY_MS || '31000', 10);

  /**
   * Check if content appears to be a binary file
   * @param {string} content - File content to check
   * @returns {boolean} - True if content appears to be binary
   */
  function isBinaryContent(content) {
    return content.includes('\0');
  }

  /**
   * Call OpenAI API with messages
   * @param {Array} messages - Array of message objects
   * @param {boolean} expectJson - Whether to expect JSON response
   * @returns {string} - AI response content
   * @throws {Error} - If API call fails or response is invalid
   */
  async function callOpenAI(messages, expectJson = true) {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api-key': apiKey
      },
      body: JSON.stringify({
        messages: messages,
        response_format: expectJson ? { type: "json_object" } : undefined
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`OpenAI API error: ${response.status} ${errorText}`);
      throw new Error(`API error: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    if (!data.choices?.[0]?.message?.content) {
      console.error(`Invalid API response structure.`, data);
      throw new Error(`Invalid API response structure. Received: ${JSON.stringify(data)}`);
    }

    console.log(`OpenAI API response received successfully.`, data);
    return data.choices[0].message.content.trim();
  }

  /**
   * Read file content safely with path traversal protection
   * @param {string} filePath - Path to file relative to repo root
   * @returns {string} - File content or error message
   */
  function readFileContent(filePath) {
    try {
      const repoRoot = process.cwd();

      // Resolve the full path and ensure it's within the repo
      const fullPath = path.resolve(repoRoot, filePath);
      const normalizedFull = path.normalize(fullPath);
      const normalizedRoot = path.normalize(repoRoot);
      const relativePath = path.relative(normalizedRoot, normalizedFull);
      if (relativePath.startsWith('..')) {
        return `[Access denied: ${filePath} is outside the repository]`;
      }

      // Check if file exists
      if (!fs.existsSync(fullPath)) {
        return `[File not found: ${filePath}]`;
      }

      const stats = fs.statSync(fullPath);
      if (stats.isDirectory()) {
        return `[${filePath} is a directory, not a file]`;
      }

      // Read file with size limit
      if (stats.size > MAX_FILE_SIZE) {
        // Read only first MAX_FILE_SIZE bytes for large files
        const fd = fs.openSync(fullPath, 'r');
        const buffer = Buffer.alloc(MAX_FILE_SIZE);
        let bytesRead;
        try {
          bytesRead = fs.readSync(fd, buffer, 0, MAX_FILE_SIZE, 0);
        } finally {
          fs.closeSync(fd);
        }
        // Use StringDecoder to handle incomplete multi-byte UTF-8 characters at the truncation point
        const { StringDecoder } = require('string_decoder');
        const decoder = new StringDecoder('utf8');
        const content = decoder.write(buffer.slice(0, bytesRead)) + decoder.end();
        if (isBinaryContent(content)) {
          return `[${filePath} appears to be a binary file]`;
        }
        return content + '\n\n[File truncated - exceeded 50KB limit]';
      }

      const content = fs.readFileSync(fullPath, 'utf8');
      if (isBinaryContent(content)) {
        return `[${filePath} appears to be a binary file]`;
      }
      return content;
    } catch (error) {
      return `[Error reading file ${filePath}: ${error?.message || "File could not be accessed"}]`;
    }
  }

  /**
   * Parse JSON response, handling markdown code fences
   * @param {string} content - Raw response content
   * @returns {Object} - Parsed JSON object
   * @throws {SyntaxError} - If content is not valid JSON
   */
  function parseJsonResponse(content) {
    let jsonContent = content;
    // Extract JSON from markdown code block if the entire content is wrapped in fences
    const codeBlockMatch = content.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$/);
    if (codeBlockMatch) {
      jsonContent = codeBlockMatch[1].trim();
    }
    return JSON.parse(jsonContent);
  }

  try {
    // Conversation history
    const messages = [];

    // Send the consolidated system prompt directly (already contains workflow + guidelines)
    messages.push({ role: 'system', content: systemPrompt });

    // First turn: Provide issue details
    const firstTurnPrompt = `Please analyze this issue. First classify it, then either request files you need or provide your response.

---

## Issue Details

**Title:** ${issueTitle}

**Author:** @${issueAuthor}

**Original Labels:** ${context.payload.issue.labels.map(label => label.name).join(', ') || '(None)'}

**Body:**
${issueBody}

`;

    messages.push({ role: 'user', content: firstTurnPrompt });

    let finalClassification = null;
    let finalResponse = null;
    let currentClassification = null;

    for (let turn = 1; turn <= MAX_TURNS; turn++) {
      // Add delay before subsequent turns to ensure token usage stays under rate limits
      if (turn > 1) {
        console.log(`Waiting ${RATE_LIMIT_DELAY_MS / 1000} seconds before turn ${turn} to respect rate limits...`);
        await new Promise(resolve => setTimeout(resolve, RATE_LIMIT_DELAY_MS));
      }

      console.log(`Turn ${turn}/${MAX_TURNS}: Calling OpenAI API...`);

      const aiContent = await callOpenAI(messages);
      console.log(`Turn ${turn} response received`);

      let parsed;
      try {
        parsed = parseJsonResponse(aiContent);
      } catch (parseError) {
        console.log(`Failed to parse JSON in turn ${turn}: ${parseError.message}`);
        // If we can't parse JSON, treat as final response
        // Attempt to extract classification using legacy format (e.g., regex)
        let legacyClassification = null;
        // Example: look for "Classification: <label>" in the response (case-insensitive)
        const match = aiContent.match(/classification\s*:\s*([a-zA-Z0-9_-]+)/i);
        if (match) {
          legacyClassification = match[1].toLowerCase();
          console.log(`Extracted legacy classification: ${legacyClassification}`);
        } else {
          console.log('Could not extract classification from non-JSON response');
        }
        finalResponse = aiContent;
        finalClassification = legacyClassification;
        break;
      }

      // Extract classification from response
      const newClassification = parsed.classification?.toLowerCase() || null;

      // Update current classification
      if (newClassification) {
        currentClassification = newClassification;
      }

      if (turn === MAX_TURNS) {
        // Force final response on last turn
        finalClassification = currentClassification;
        if (parsed.needs_files) {
          finalResponse = "Unable to provide a complete analysis within the turn limit. Please provide more specific details about your issue or the relevant files.";
        } else {
          finalResponse = parsed.response || aiContent;
        }
        console.log(`Forced final response on last turn ${turn}`);
        break;
      }

      if (!parsed.needs_files) {
        // Final response provided before last turn
        finalClassification = currentClassification;
        finalResponse = parsed.response || aiContent;
        console.log(`Final response received in turn ${turn}`);
        break;
      }

      // Need more files
      const requestedFiles = parsed.requested_files || [];
      console.log(`Turn ${turn}: Requested files: ${requestedFiles.join(', ')}`);

      // Add assistant's response to history
      messages.push({ role: 'assistant', content: aiContent });

      // Build the next user message with requested file contents
      let fileContents = '## Requested File Contents\n\n';
      for (const filePath of requestedFiles.slice(0, MAX_FILES_PER_TURN)) {
        const content = readFileContent(filePath);
        fileContents += `### \`${filePath}\`\n\n\`\`\`\n${content}\n\`\`\`\n\n`;
      }

      // Append remaining turns message (this code is only reached when turn < MAX_TURNS)
      fileContents += `\nYou have ${MAX_TURNS - turn} turn(s) remaining. Please analyze these files and either request more files or provide your final classification and response.`;

      messages.push({ role: 'user', content: fileContents });
    }

    if (!finalResponse) {
      core.setFailed('Failed to get a valid response after all turns. This indicates an unexpected error in the conversation flow.');
      console.error('Debug info - messages:', JSON.stringify(messages, null, 2));
      return;
    }

    // Post the response as a comment
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: context.payload.issue.number,
      body: finalResponse
    });
    console.log('Comment posted successfully');

    // Add label based on classification
    if (finalClassification && classifications.includes(finalClassification)) {
      try {
        await github.rest.issues.addLabels({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: context.payload.issue.number,
          labels: [finalClassification]
        });
        console.log(`Label '${finalClassification}' added successfully`);
      } catch (labelError) {
        console.log(`Failed to add label: ${labelError.message}`);
      }
    }

    console.log('AI response workflow completed successfully');
  } catch (error) {
    const errorDetails = error && error.stack ? error.stack : error.message;
    core.setFailed(`Failed to generate AI response: ${error.message}\n\nDetails: ${errorDetails}`);
    console.error('Full error:', error);
  }
};
