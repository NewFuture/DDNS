# AI Issue Assessment System

This repository uses the `github/ai-assessment-comment-labeler` action to automatically assess and label issues using AI.

## How It Works

When a new issue is created, you can trigger an AI assessment by adding the `request ai review` label to the issue. The system will:

1. Analyze the issue content based on existing labels
2. Provide helpful feedback or guidance
3. Add assessment labels based on AI analysis
4. Optionally post a comment with the assessment

## Issue Types and Labels

The system supports three types of issues, each with its own specialized prompt:

### Bug Reports (`bug` label)
- Assesses completeness of bug reports
- Checks for: clear description, steps to reproduce, expected vs actual behavior, environment details, error messages
- Assessment outcomes: `Ready for Review`, `Needs More Info`, or `Unclear`

### Feature Requests (`feature` label)
- Evaluates clarity and completeness of feature requests
- Checks for: clear description, problem statement, use cases, feasibility, impact
- Assessment outcomes: `Well-Formed`, `Needs Clarification`, or `Unclear`

### Questions (`question` label)
- Provides support and guidance for general questions
- Offers direct answers, references to documentation, code examples
- Assessment outcomes: `Clear`, `Needs Clarification`, or `Complex`

## Using the AI Assessment

### Automatic Assessment on New Issues

To get an AI assessment on your issue:

1. Create or open an issue
2. Add one of the type labels: `bug`, `feature`, or `question`
3. Add the `request ai review` label
4. Wait a few seconds for the AI assessment

The system will:
- Post a comment with helpful feedback (unless the issue is complete)
- Add an assessment label like `ai:bug-review:ready for review` or `ai:feature-request:needs clarification`
- Remove the `request ai review` label (so you can re-trigger if needed)

### Re-triggering Assessment

If you update your issue with more information, you can request a new assessment by adding the `request ai review` label again.

## Prompt Files

The AI prompts are defined in `.github/prompts/*.prompt.yml` files:

- `bug-review.prompt.yml` - For bug report assessment
- `feature-request.prompt.yml` - For feature request evaluation  
- `question.prompt.yml` - For question responses

Each prompt file contains:
- System instructions for the AI model
- Project context and documentation references
- Assessment criteria and response format
- Language detection to respond in the same language as the issue

## Configuration

The workflow is configured in `.github/workflows/ai-assessment.yml`:

- **Trigger**: Adding `request ai review` label to any issue
- **Permissions**: `issues: write`, `models: read`, `contents: read`
- **Model**: OpenAI GPT-4o-mini via GitHub Models API
- **Max tokens**: 2000

## Benefits

1. **Faster triage**: Issues are automatically assessed for completeness
2. **Better issue quality**: Users get immediate feedback on what information is missing
3. **Consistent responses**: AI follows standardized prompts for each issue type
4. **Multilingual support**: Responds in the same language as the issue
5. **No external API keys**: Uses GitHub's built-in Models API

## Privacy and Security

- Uses GitHub's native Models API (no data sent to external services)
- Sensitive information in issues should still be masked by users
- AI assessments are supplementary and should be reviewed by maintainers
