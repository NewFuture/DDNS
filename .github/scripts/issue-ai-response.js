/**
 * 3-Step AI Response Script for GitHub Issues
 * 
 * Protocol:
 * - Step 1: Request files (no classification)
 * - Step 2: Response OR more files (mutually exclusive)
 * - Step 3: Final response required
 */

module.exports = async ({ github, context, core, fs, path }) => {
  const apiUrl = process.env.OPENAI_URL;
  const apiKey = process.env.OPENAI_KEY;

  if (!apiUrl || !apiKey) {
    core.setFailed('OPENAI_URL and OPENAI_KEY must be set');
    return;
  }

  // Read system prompt and extract directory structure from AGENTS.md
  let systemPrompt;
  try {
    systemPrompt = fs.readFileSync('.github/prompts/issue-assistant.md', 'utf8');
    const agentsMd = fs.readFileSync('AGENTS.md', 'utf8');
    const structureMatch = agentsMd.match(/#{2,6}\s+Directory Structure[\s\S]*?```(?:\w+)?\s*\n([\s\S]*?)\n```/i);
    if (!structureMatch) {
      core.setFailed('Failed to extract Directory Structure from AGENTS.md.');
      return;
    }
    systemPrompt = systemPrompt.replace('{{DirectoryStructure}}', structureMatch[1].trim());
  } catch (error) {
    core.setFailed('Failed to read required files: ' + error.message);
    return;
  }

  const classifications = ['bug', 'feature', 'question'];
  const MAX_FILES = 10;
  const MAX_FILE_SIZE = 50000;
  const MAX_TURNS = 3;
  const RATE_LIMIT_DELAY_MS = parseInt(process.env.RATE_LIMIT_DELAY_MS || '31000', 10);

  // Helper functions
  function isBinaryContent(content) {
    return content.includes('\0');
  }

  async function callOpenAI(messages) {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'api-key': apiKey },
      body: JSON.stringify({ messages, response_format: { type: "json_object" } })
    });
    if (!response.ok) {
      throw new Error('API error: ' + response.status);
    }
    const data = await response.json();
    if (!data.choices?.[0]?.message?.content) {
      throw new Error('Invalid API response');
    }
    return data.choices[0].message.content.trim();
  }

  function readFileContent(filePath) {
    try {
      const repoRoot = process.cwd();
      const fullPath = path.resolve(repoRoot, filePath);
      if (path.relative(repoRoot, fullPath).startsWith('..')) {
        return '[Access denied: ' + filePath + ']';
      }
      if (!fs.existsSync(fullPath)) {
        return '[File not found: ' + filePath + ']';
      }
      const stats = fs.statSync(fullPath);
      if (stats.isDirectory()) {
        return '[' + filePath + ' is a directory]';
      }
      if (stats.size > MAX_FILE_SIZE) {
        const fd = fs.openSync(fullPath, 'r');
        const buffer = Buffer.alloc(MAX_FILE_SIZE);
        const bytesRead = fs.readSync(fd, buffer, 0, MAX_FILE_SIZE, 0);
        fs.closeSync(fd);
        const { StringDecoder } = require('string_decoder');
        const decoder = new StringDecoder('utf8');
        const content = decoder.write(buffer.slice(0, bytesRead)) + decoder.end();
        return isBinaryContent(content) ? '[Binary file]' : content + '\n[Truncated]';
      }
      const content = fs.readFileSync(fullPath, 'utf8');
      return isBinaryContent(content) ? '[Binary file]' : content;
    } catch (error) {
      return '[Error: ' + (error.message || 'unknown') + ']';
    }
  }

  function parseJson(content) {
    const match = content.match(/^```(?:json)?\s*\n?([\s\S]*?)\n?```\s*$/);
    return JSON.parse(match ? match[1].trim() : content);
  }

  function extractClassification(parsed, raw) {
    if (parsed?.classification) {
      const c = parsed.classification.toLowerCase();
      if (classifications.includes(c)) return c;
    }
    const match = raw.match(/classification\s*:\s*([a-zA-Z0-9_-]+)/i);
    if (match) {
      const c = match[1].toLowerCase();
      if (classifications.includes(c)) return c;
    }
    return null;
  }

  function buildFileContents(files) {
    let msg = '## Requested File Contents\n\n';
    for (const f of files.slice(0, MAX_FILES)) {
      msg += '### `' + f + '`\n\n```\n' + readFileContent(f) + '\n```\n\n';
    }
    return msg;
  }

  try {
    const issue = context.payload.issue;
    const issueDetails = '## Issue Details\n\n' +
      '**Title:** ' + (issue.title || '').substring(0, 500) + '\n\n' +
      '**Author:** @' + issue.user.login + '\n\n' +
      '**Labels:** ' + (issue.labels.map(l => l.name).join(', ') || '(None)') + '\n\n' +
      '**Body:**\n' + (issue.body || '').substring(0, 10000);

    const messages = [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: issueDetails }
    ];
    
    let finalClassification = null;
    let finalResponse = null;

    for (let turn = 1; turn <= MAX_TURNS && !finalResponse; turn++) {
      if (turn > 1) {
        console.log('Waiting ' + (RATE_LIMIT_DELAY_MS / 1000) + 's before turn ' + turn);
        await new Promise(r => setTimeout(r, RATE_LIMIT_DELAY_MS));
      }

      console.log('Turn ' + turn + '/' + MAX_TURNS);
      const content = await callOpenAI(messages);
      
      let parsed;
      try {
        parsed = parseJson(content);
      } catch (e) {
        // Non-JSON response treated as final
        finalClassification = extractClassification(null, content);
        finalResponse = content;
        break;
      }

      const hasResponse = parsed.response && typeof parsed.response === 'string' && parsed.response.trim();
      const hasFiles = parsed.requested_files && Array.isArray(parsed.requested_files) && parsed.requested_files.length > 0;

      if (hasResponse) {
        finalClassification = extractClassification(parsed, content);
        finalResponse = parsed.response;
      } else if (hasFiles && turn < MAX_TURNS) {
        messages.push({ role: 'assistant', content });
        messages.push({ role: 'user', content: buildFileContents(parsed.requested_files) });
      } else if (turn === MAX_TURNS) {
        finalResponse = parsed.response || 'Unable to provide analysis. Please provide more details.';
        finalClassification = extractClassification(parsed, content);
      } else {
        finalResponse = 'Unable to process this issue. Please provide more details.';
      }
    }

    if (!finalResponse) {
      core.setFailed('Failed to get valid response');
      return;
    }

    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: issue.number,
      body: finalResponse
    });

    if (finalClassification && classifications.includes(finalClassification)) {
      try {
        await github.rest.issues.addLabels({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: issue.number,
          labels: [finalClassification]
        });
      } catch (e) {
        console.log('Failed to add label: ' + e.message);
      }
    }

    console.log('Completed successfully');
  } catch (error) {
    core.setFailed('Error: ' + error.message);
  }
};
