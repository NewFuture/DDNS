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
    const content = data.choices[0].message.content.trim();
    console.log('OpenAI response:', content);
    return content;
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
    let msg = '';
    for (const f of files.slice(0, MAX_FILES)) {
      msg += '### `' + f + '`\n\n```\n' + readFileContent(f) + '\n```\n\n';
    }
    return msg;
  }

  // Process AI response, return { classification, response, files }
  function processResponse(raw) {
    let parsed;
    try {
      parsed = parseJson(raw);
    } catch (e) {
      return { classification: extractClassification(null, raw), response: raw, files: [] };
    }
    
    const response = parsed.response && typeof parsed.response === 'string' && parsed.response.trim() 
      ? parsed.response : null;
    const files = (parsed.requested_files || []).slice(0, MAX_FILES);
    const classification = response ? extractClassification(parsed, raw) : null;
    
    return { classification, response, files };
  }

  async function delay() {
    console.log('Waiting ' + (RATE_LIMIT_DELAY_MS / 1000) + 's...');
    await new Promise(r => setTimeout(r, RATE_LIMIT_DELAY_MS));
  }

  try {
    const issue = context.payload.issue;
    const messages = [{ role: 'system', content: systemPrompt }];

    // ========== Query 1: Analyze issue, request files ==========
    messages.push({ role: 'user', content: 
      'Analyze this issue and request relevant files.\n\n## Issue Details\n\n' +
      '**Title:** ' + (issue.title || '').substring(0, 500) + '\n\n' +
      '**Author:** @' + issue.user.login + '\n\n' +
      '**Labels:** ' + (issue.labels.map(l => l.name).join(', ') || '(None)') + '\n\n' +
      '**Body:**\n' + (issue.body || '').substring(0, 10000)
    });
    console.log('Query 1: Analyzing issue...');
    const r1 = await callOpenAI(messages);
    let result = processResponse(r1);

    // ========== Query 2: Provide files, get response or more files ==========
    if (!result.response && result.files.length > 0) {
      await delay();
      messages.push({ role: 'assistant', content: r1 });
      messages.push({ role: 'user', content: 
        'Here are the requested files. Provide your response OR request more files.\n\n' + 
        buildFileContents(result.files)
      });
      console.log('Query 2: Processing files...');
      const r2 = await callOpenAI(messages);
      result = processResponse(r2);

      // ========== Query 3: Provide more files, must respond ==========
      if (!result.response && result.files.length > 0) {
        await delay();
        messages.push({ role: 'assistant', content: r2 });
        messages.push({ role: 'user', content: 
          'Here are the additional files. You must provide your final response now.\n\n' + 
          buildFileContents(result.files)
        });
        console.log('Query 3: Final response...');
        const r3 = await callOpenAI(messages);
        result = processResponse(r3);
        if (!result.response) {
          result.response = 'Unable to provide analysis. Please provide more details.';
        }
      }
    }

    // Fallback if no response
    if (!result.response) {
      result.response = 'Unable to process this issue. Please provide more details.';
    }

    // Post comment
    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: issue.number,
      body: result.response
    });

    // Add label
    if (result.classification && classifications.includes(result.classification)) {
      try {
        await github.rest.issues.addLabels({
          owner: context.repo.owner,
          repo: context.repo.repo,
          issue_number: issue.number,
          labels: [result.classification]
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
