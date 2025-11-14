# Auto-Reply GitHub Action

This GitHub Action automatically replies to newly opened issues using Azure OpenAI.

## Configuration

### Required Secrets

Configure these secrets in your repository settings (`Settings > Secrets and variables > Actions`):

1. **`ai`** or **`OPENAI_KEY`**: Azure OpenAI API key
   - The action will use `OPENAI_KEY` if set, otherwise falls back to `ai`
   - Example: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Required Variables

Configure this variable in your repository settings (`Settings > Secrets and variables > Actions > Variables`):

1. **`OPENAI_URL`**: Azure OpenAI endpoint URL
   - Example: `https://your-resource.openai.azure.com/openai/deployments/your-deployment`
   - The action will automatically append `/chat/completions` if not present

### Optional Configuration

- **Daily Limit**: The action is configured to run a maximum of 200 times per day to prevent excessive API usage
- **Timeout**: Each run has a 3-minute timeout
- **Bot Prevention**: Issues created by `github-actions[bot]` are automatically skipped

## How It Works

1. When a new issue is opened, the workflow is triggered
2. The action checks if the daily limit (200 runs) has been reached
3. If within limit, it sends issue details to Azure OpenAI
4. Azure OpenAI generates a contextual response in Chinese (中文)
5. The response is posted as a comment on the issue

## Testing

To test the Python script locally:

```bash
ISSUE_NUMBER=123 \
ISSUE_TITLE="Test Issue" \
ISSUE_BODY="Test body" \
ISSUE_AUTHOR="testuser" \
REPOSITORY="owner/repo" \
OPENAI_URL="https://your-resource.openai.azure.com/openai/deployments/your-deployment" \
OPENAI_KEY="your-api-key" \
python3 .github/scripts/auto-reply.py
```

## Files

- **`.github/workflows/auto-reply-issue.yml`**: GitHub Actions workflow definition
- **`.github/scripts/auto-reply.py`**: Python script that calls Azure OpenAI API

## Troubleshooting

### Script exits with "Environment variable X is required"
Make sure all required secrets and variables are configured in repository settings.

### "Daily limit of 200 runs reached"
The action has reached its daily limit. It will reset after 24 hours.

### "HTTP Error calling Azure OpenAI: 401"
Check that your `OPENAI_KEY` or `ai` secret is correct.

### "HTTP Error calling Azure OpenAI: 404"
Verify that your `OPENAI_URL` points to a valid Azure OpenAI deployment endpoint.
