/**
 * Strict 3-Step AI Response Script for GitHub Issues
 *
 * This script implements a strict 3-step protocol for AI-powered issue responses:
 *
 * STEP 1: Issue-only analysis
 *   - Input: Only issue details (title, body, labels, author)
 *   - Output: { classification?, requested_files[] }
 *   - AI analyzes issue and requests first batch of files
 *
 * STEP 2: First batch of files (mutually exclusive)
 *   - Input: Issue + first batch file contents
 *   - Output: EITHER { classification?, response } OR { classification?, requested_files[] }
 *   - AI must choose: final response OR request more files (not both)
 *   - If response provided, workflow ends
 *
 * STEP 3: Second batch of files (final mandatory answer)
 *   - Input: Issue + first batch + second batch file contents
 *   - Output: { classification?, response }
 *   - AI must provide final response (requested_files ignored)
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
    const structureMatch = agentsMd.match(/#{2,6}\s+Directory Structure[\s\S]*?```(?:\w+)?\s*\n([\s\S]*?)\n```/i);
    if (!structureMatch) {
      core.setFailed('Failed to extract Directory Structure from AGENTS.md.');
      return;
    }
    directoryStructure = structureMatch[1].trim();

    if (!systemPrompt.includes('{{DirectoryStructure}}')) {
      console.log('Warning: {{DirectoryStructure}} placeholder not found in system prompt');
    }
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
  const issueLabels = context.payload.issue.labels.map(function(label) { return label.name; }).join(', ') || '(None)';

  // Constants
  const MAX_FILES_PER_STEP = 10;
  const MAX_FILE_SIZE = 50000; // 50KB
  const RATE_LIMIT_DELAY_MS = parseInt(process.env.RATE_LIMIT_DELAY_MS || '31000', 10);

  /**
   * Check if content appears to be a binary file
   */
  function isBinaryContent(content) {
    return content.includes('\0');
  }

  /**
   * Call OpenAI API with messages
   */
  async function callOpenAI(messages, expectJson) {
    if (expectJson === undefined) expectJson = true;
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
      console.error('OpenAI API error: ' + response.status + ' ' + errorText);
      throw new Error('API error: ' + response.status + ' ' + errorText);
    }

    const data = await response.json();
    if (!data.choices || !data.choices[0] || !data.choices[0].message || !data.choices[0].message.content) {
      console.error('Invalid API response structure.', data);
      throw new Error('Invalid API response structure.');
    }

    console.log('OpenAI API response received successfully.', data);
    return data.choices[0].message.content.trim();
  }

  /**
   * Read file content safely with path traversal protection
   */
  function readFileContent(filePath) {
    try {
      const repoRoot = process.cwd();
      const fullPath = path.resolve(repoRoot, filePath);
      const normalizedFull = path.normalize(fullPath);
      const normalizedRoot = path.normalize(repoRoot);
      const relativePath = path.relative(normalizedRoot, normalizedFull);
      if (relativePath.startsWith('..')) {
        return '[Access denied: ' + filePath + ' is outside the repository]';
      }

      if (!fs.existsSync(fullPath)) {
        return '[File not found: ' + filePath + ']';
      }

      const stats = fs.statSync(fullPath);
      if (stats.isDirectory()) {
        return '[' + filePath + ' is a directory, not a file]';
      }

      if (stats.size > MAX_FILE_SIZE) {
        const fd = fs.openSync(fullPath, 'r');
        const buffer = Buffer.alloc(MAX_FILE_SIZE);
        let bytesRead;
        try {
          bytesRead = fs.readSync(fd, buffer, 0, MAX_FILE_SIZE, 0);
        } finally {
          fs.closeSync(fd);
        }
        const { StringDecoder } = require('string_decoder');
        const decoder = new StringDecoder('utf8');
        const content = decoder.write(buffer.slice(0, bytesRead)) + decoder.end();
        if (isBinaryContent(content)) {
          return '[' + filePath + ' appears to be a binary file]';
        }
        return content + '\n\n[File truncated - exceeded 50KB limit]';
      }

      const content = fs.readFileSync(fullPath, 'utf8');
      if (isBinaryContent(content)) {
        return '[' + filePath + ' appears to be a binary file]';
      }
      return content;
    } catch (error) {
      return '[Error reading file ' + filePath + ': ' + (error && error.message ? error.message : 'File could not be accessed') + ']';
    }
  }

  /**
   * Parse JSON response, handling markdown code fences
   */
  function parseJsonResponse(content) {
    let jsonContent = content;
    const codeBlockMatch = content.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$/);
    if (codeBlockMatch) {
      jsonContent = codeBlockMatch[1].trim();
    }
    return JSON.parse(jsonContent);
  }

  /**
   * Extract classification from parsed JSON or legacy text pattern
   */
  function extractClassification(parsed, rawContent) {
    if (parsed && parsed.classification) {
      const c = parsed.classification.toLowerCase();
      if (classifications.indexOf(c) !== -1) {
        return c;
      }
    }
    // Legacy pattern: "Classification: bug"
    const match = rawContent.match(/classification\s*:\s*([a-zA-Z0-9_-]+)/i);
    if (match) {
      const c = match[1].toLowerCase();
      if (classifications.indexOf(c) !== -1) {
        return c;
      }
    }
    return null;
  }

  /**
   * Build file contents message from file paths
   */
  function buildFileContentsMessage(filePaths) {
    let msg = '## Requested File Contents\n\n';
    const paths = filePaths.slice(0, MAX_FILES_PER_STEP);
    for (let i = 0; i < paths.length; i++) {
      const filePath = paths[i];
      const content = readFileContent(filePath);
      msg += '### `' + filePath + '`\n\n```\n' + content + '\n```\n\n';
    }
    return msg;
  }

  try {
    const messages = [];
    messages.push({ role: 'system', content: systemPrompt });

    // Issue details for all steps
    const issueDetailsBlock = '## Issue Details\n\n' +
      '**Title:** ' + issueTitle + '\n\n' +
      '**Author:** @' + issueAuthor + '\n\n' +
      '**Labels:** ' + issueLabels + '\n\n' +
      '**Body:**\n' + issueBody;

    let finalClassification = null;
    let finalResponse = null;
    let firstBatchFiles = [];
    let secondBatchFiles = [];

    // ========== STEP 1 ==========
    console.log('Step 1: Issue-only analysis...');
    const step1Prompt = 'Step 1: Analyze this issue. Return JSON with classification (optional) and requested_files.\n\n' + issueDetailsBlock;
    messages.push({ role: 'user', content: step1Prompt });

    const step1Content = await callOpenAI(messages);
    console.log('Step 1 response received');

    let step1Parsed;
    try {
      step1Parsed = parseJsonResponse(step1Content);
    } catch (parseError) {
      console.log('Step 1: Failed to parse JSON, treating as final response');
      finalClassification = extractClassification(null, step1Content);
      finalResponse = step1Content;
    }

    if (!finalResponse) {
      finalClassification = extractClassification(step1Parsed, step1Content);
      firstBatchFiles = (step1Parsed.requested_files || []).slice(0, MAX_FILES_PER_STEP);
      console.log('Step 1: Requested files: ' + firstBatchFiles.join(', '));

      if (firstBatchFiles.length === 0) {
        // No files requested, force a fallback response
        finalResponse = 'I was unable to determine which files to analyze. Please provide more details about your issue.';
      }
    }

    // ========== STEP 2 ==========
    let step2Content;
    if (!finalResponse && firstBatchFiles.length > 0) {
      console.log('Waiting ' + (RATE_LIMIT_DELAY_MS / 1000) + ' seconds before Step 2...');
      await new Promise(function(resolve) { setTimeout(resolve, RATE_LIMIT_DELAY_MS); });

      console.log('Step 2: First batch of files...');
      messages.push({ role: 'assistant', content: step1Content });

      const step2Prompt = 'Step 2: Here are the requested files. Choose ONE:\n' +
        '- Option A: Provide final response → { "classification": "...", "response": "..." }\n' +
        '- Option B: Request more files → { "classification": "...", "requested_files": [...] }\n' +
        'Do NOT include both response and requested_files.\n\n' +
        buildFileContentsMessage(firstBatchFiles);
      messages.push({ role: 'user', content: step2Prompt });

      step2Content = await callOpenAI(messages);
      console.log('Step 2 response received');

      let step2Parsed;
      try {
        step2Parsed = parseJsonResponse(step2Content);
      } catch (parseError) {
        console.log('Step 2: Failed to parse JSON, treating as final response');
        const newClass = extractClassification(null, step2Content);
        if (newClass) finalClassification = newClass;
        finalResponse = step2Content;
      }

      if (!finalResponse) {
        const newClass = extractClassification(step2Parsed, step2Content);
        if (newClass) finalClassification = newClass;

        const hasResponse = step2Parsed.response && typeof step2Parsed.response === 'string' && step2Parsed.response.trim().length > 0;
        const hasFiles = step2Parsed.requested_files && Array.isArray(step2Parsed.requested_files) && step2Parsed.requested_files.length > 0;

        if (hasResponse && hasFiles) {
          // Protocol violation: both response and requested_files present
          console.log('Step 2: Protocol violation - both response and requested_files present');
          finalResponse = 'An internal error occurred while processing this issue. Please try again or provide more details.';
        } else if (hasResponse) {
          // Option A: Final response
          finalResponse = step2Parsed.response;
          console.log('Step 2: Final response received (Option A)');
        } else if (hasFiles) {
          // Option B: Request more files
          secondBatchFiles = step2Parsed.requested_files.slice(0, MAX_FILES_PER_STEP);
          console.log('Step 2: Requested more files (Option B): ' + secondBatchFiles.join(', '));
        } else {
          // Neither response nor files - invalid
          console.log('Step 2: Invalid response - neither response nor requested_files');
          finalResponse = 'I was unable to process this issue properly. Please provide more details.';
        }
      }
    }

    // ========== STEP 3 ==========
    if (!finalResponse && secondBatchFiles.length > 0) {
      console.log('Waiting ' + (RATE_LIMIT_DELAY_MS / 1000) + ' seconds before Step 3...');
      await new Promise(function(resolve) { setTimeout(resolve, RATE_LIMIT_DELAY_MS); });

      console.log('Step 3: Second batch of files (final answer)...');
      messages.push({ role: 'assistant', content: step2Content });

      const step3Prompt = 'Step 3: Final step. You MUST provide a response now.\n' +
        'Return: { "classification": "...", "response": "..." }\n' +
        'Do NOT request more files.\n\n' +
        buildFileContentsMessage(secondBatchFiles);
      messages.push({ role: 'user', content: step3Prompt });

      const step3Content = await callOpenAI(messages);
      console.log('Step 3 response received');

      let step3Parsed;
      try {
        step3Parsed = parseJsonResponse(step3Content);
      } catch (parseError) {
        console.log('Step 3: Failed to parse JSON, treating as final response');
        const newClass = extractClassification(null, step3Content);
        if (newClass) finalClassification = newClass;
        finalResponse = step3Content;
      }

      if (!finalResponse) {
        const newClass = extractClassification(step3Parsed, step3Content);
        if (newClass) finalClassification = newClass;

        if (step3Parsed.response && typeof step3Parsed.response === 'string') {
          finalResponse = step3Parsed.response;
        } else {
          // Fallback if no response field
          finalResponse = 'Unable to provide a complete analysis. Please provide more details about your issue.';
        }
        // Ignore any requested_files in Step 3
        if (step3Parsed.requested_files) {
          console.log('Step 3: Ignoring requested_files (not allowed in final step)');
        }
      }
    }

    if (!finalResponse) {
      core.setFailed('Failed to get a valid response after all steps.');
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
    if (finalClassification && classifications.indexOf(finalClassification) !== -1) {
      try {
        await github.rest.issues.addLabels({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: context.payload.issue.number,
          labels: [finalClassification]
        });
        console.log('Label \'' + finalClassification + '\' added successfully');
      } catch (labelError) {
        console.log('Failed to add label: ' + labelError.message);
      }
    }

    console.log('AI response workflow completed successfully');
  } catch (error) {
    const errorDetails = error && error.stack ? error.stack : error.message;
    core.setFailed('Failed to generate AI response: ' + error.message + '\n\nDetails: ' + errorDetails);
    console.error('Full error:', error);
  }
};
