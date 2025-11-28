/**
 * Multi-turn AI Response Script for GitHub Issues
 * 
 * This script handles AI-powered responses to GitHub issues using a multi-turn
 * conversation approach. It provides project context, allows the AI to request
 * specific files, and generates classification labels and responses.
 */

module.exports = async ({ github, context, core, fs, path }) => {
  const apiUrl = process.env.OPENAI_URL;
  const apiKey = process.env.OPENAI_KEY;

  if (!apiUrl || !apiKey) {
    core.setFailed('OPENAI_URL and OPENAI_KEY must be set');
    return;
  }

  // Read system prompt and repository index
  const systemPrompt = fs.readFileSync('.github/prompts/issue-assistant.md', 'utf8');
  const repoIndex = fs.readFileSync('/tmp/repo_index.md', 'utf8');

  // Issue details
  const issueTitle = context.payload.issue.title;
  const issueBody = context.payload.issue.body || '(No description provided)';
  const issueAuthor = context.payload.issue.user.login;

  // Constants
  const MAX_FILES_PER_TURN = 5;
  // Maximum file size (in bytes) for context sent to the AI. 50KB was chosen to balance
  // providing enough context for the AI to understand the code, while staying well within
  // OpenAI API token and processing limits. Larger files may exceed token limits or slow
  // down processing, while smaller limits may omit important context.
  const MAX_FILE_SIZE = 50000; // 50KB
  const MAX_TURNS = 3;

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
        temperature: 1,
        max_completion_tokens: 2000,
        response_format: expectJson ? { type: "json_object" } : undefined
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API error: ${response.status} ${errorText}`);
    }

    const data = await response.json();
    if (!data.choices?.[0]?.message?.content) {
      throw new Error(`Invalid API response structure. Received: ${JSON.stringify(data)}`);
    }

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
        try {
          fs.readSync(fd, buffer, 0, MAX_FILE_SIZE, 0);
        } finally {
          fs.closeSync(fd);
        }
        const content = buffer.toString('utf8');
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
      return `[Error reading file ${filePath}: ${error?.message||"File could not be accessed"}]`;
    }
  }

  /**
   * Parse JSON response, handling markdown code fences
   * @param {string} content - Raw response content
   * @returns {Object} - Parsed JSON object
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

    // System prompt for multi-turn conversation
    const multiTurnSystemPrompt = `${systemPrompt}

## Multi-turn Conversation Mode

You are in a multi-turn conversation mode. In each turn, you can either:
1. Request more files to better understand the issue
2. Provide your final response with classification

### Response Format

**If you need more files**, respond with:
\`\`\`json
{
  "needs_files": true,
  "requested_files": ["path/to/file1.py", "path/to/file2.md"],
  "reason": "Brief explanation of why these files are needed"
}
\`\`\`

**If you have enough information**, respond with:
\`\`\`json
{
  "needs_files": false,
  "classification": "bug|feature|question",
  "response": "Your detailed response to the issue..."
}
\`\`\`

### Guidelines
- Request only files that are directly relevant to the issue
- Request at most 5 files per turn
- After receiving requested files, analyze them and either request more or provide final response
- You have at most 3 turns to gather information before providing a final response`;

    messages.push({ role: 'system', content: multiTurnSystemPrompt });

    // First turn: Provide project context and issue
    const firstTurnPrompt = `## Repository Context

${repoIndex}

## Issue Details

**Title:** ${issueTitle}

**Author:** @${issueAuthor}

**Body:**
${issueBody}

---

Please analyze this issue. If you need to see specific files to provide an accurate response, request them. Otherwise, provide your classification and response.`;

    messages.push({ role: 'user', content: firstTurnPrompt });

    let finalClassification = null;
    let finalResponse = null;

    for (let turn = 1; turn <= MAX_TURNS; turn++) {
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

      if (turn === MAX_TURNS) {
        // Force final response on last turn
        finalClassification = parsed.classification?.toLowerCase() || null;
        finalResponse = parsed.response || aiContent;
        console.log(`Forced final response on last turn ${turn}`);
        break;
      }

      if (!parsed.needs_files) {
        // Final response provided before last turn
        finalClassification = parsed.classification?.toLowerCase() || null;
        finalResponse = parsed.response || aiContent;
        console.log(`Final response received in turn ${turn}`);
        break;
      }

      // Need more files
      const requestedFiles = parsed.requested_files || [];
      console.log(`Turn ${turn}: Requested files: ${requestedFiles.join(', ')}`);

      // Add assistant's response to history
      messages.push({ role: 'assistant', content: aiContent });

      // Read requested files and add to conversation
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
      core.setFailed('Failed to get a valid response after all turns');
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
    if (finalClassification && ['bug', 'feature', 'question'].includes(finalClassification)) {
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
    core.setFailed(`Failed to generate AI response: ${error.message}`);
  }
};
