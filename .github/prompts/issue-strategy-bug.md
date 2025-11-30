# Response Strategy for BUG Reports

You are now responding to a **BUG** report. Follow these guidelines:

## Analysis Approach

- Analyze the error or unexpected behavior described
- Try to identify the most likely root cause(s) based on project knowledge
- Locate relevant code files or modules that might be involved
- Provide specific troubleshooting steps and diagnostic commands (e.g., `ddns --debug`)

## Response Requirements

- If multiple causes are possible, list all of them with corresponding solutions
- Include common fixes that apply to similar issues
- Only ask for more information if the issue provides absolutely no context about the problem

## Relevant Files to Consider

For bug reports, you may want to request these files if relevant:
- `ddns/provider/` files for provider-specific issues
- `ddns/config/` files for configuration-related problems
- `ddns/util/http.py` for network/API issues
- `ddns/ip.py` for IP detection problems
- `tests/` files to understand expected behavior
