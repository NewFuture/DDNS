#!/usr/bin/env python3
"""
Auto-reply script for GitHub issues using Azure OpenAI.

This script reads issue information from environment variables,
calls Azure OpenAI API to generate a response, and saves it to a file.
"""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def get_env_var(name, required=True, default=None):
    """Get environment variable with optional default value."""
    value = os.environ.get(name, default)
    if required and not value:
        print(f"Error: Environment variable {name} is required but not set.", file=sys.stderr)
        sys.exit(1)
    return value


def call_azure_openai(api_url, api_key, issue_title, issue_body, issue_author):
    """
    Call Azure OpenAI API to generate a response for the issue.
    
    Args:
        api_url: Azure OpenAI endpoint URL
        api_key: Azure OpenAI API key
        issue_title: Title of the GitHub issue
        issue_body: Body content of the GitHub issue
        issue_author: Username of the issue author
    
    Returns:
        str: Generated response text
    """
    # Prepare the prompt for Azure OpenAI
    system_prompt = """You are a helpful assistant for the DDNS project, a Python-based Dynamic DNS client.
Your role is to provide friendly, informative responses to GitHub issues.

Project context:
- DDNS automatically updates DNS records to match the current IP address
- Supports multiple DNS providers (DNSPod, AliDNS, CloudFlare, etc.)
- Supports IPv4/IPv6, public/private IPs
- Can be deployed via Docker, pip, or binary files
- Uses Python standard library only (no external dependencies)
- Supports Python 2.7 and 3.x

When responding to issues:
1. Be welcoming and professional
2. Ask clarifying questions if the issue is unclear
3. Provide relevant documentation links when applicable
4. Suggest troubleshooting steps for bug reports
5. Thank users for feature requests and explain next steps
6. Use Chinese (中文) for responses as this is primarily a Chinese project
7. Keep responses concise but helpful"""

    user_prompt = f"""A new issue has been opened:

Title: {issue_title}

Body:
{issue_body or '(No description provided)'}

Author: @{issue_author}

Please generate a helpful initial response to this issue. The response should acknowledge the issue and provide guidance or ask for more information if needed."""

    # Prepare the API request
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    data = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 800,
        "top_p": 0.95
    }
    
    try:
        # Ensure the URL has the correct format for Azure OpenAI
        if not api_url.endswith("/chat/completions"):
            if api_url.endswith("/"):
                api_url = api_url + "chat/completions"
            else:
                api_url = api_url + "/chat/completions"
        
        request = Request(
            api_url,
            data=json.dumps(data).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        print(f"Calling Azure OpenAI API at: {api_url}")
        with urlopen(request, timeout=30) as response:
            response_data = json.loads(response.read().decode("utf-8"))
            
        # Extract the generated response
        if "choices" in response_data and len(response_data["choices"]) > 0:
            ai_response = response_data["choices"][0]["message"]["content"].strip()
            return ai_response
        else:
            print("Error: No response from Azure OpenAI", file=sys.stderr)
            print(f"Response data: {response_data}", file=sys.stderr)
            return None
            
    except HTTPError as e:
        print(f"HTTP Error calling Azure OpenAI: {e.code} {e.reason}", file=sys.stderr)
        print(f"Response: {e.read().decode('utf-8', errors='ignore')}", file=sys.stderr)
        return None
    except URLError as e:
        print(f"URL Error calling Azure OpenAI: {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        return None


def main():
    """Main function to orchestrate the auto-reply process."""
    # Get environment variables
    issue_number = get_env_var("ISSUE_NUMBER")
    issue_title = get_env_var("ISSUE_TITLE")
    issue_body = get_env_var("ISSUE_BODY", required=False, default="")
    issue_author = get_env_var("ISSUE_AUTHOR")
    repository = get_env_var("REPOSITORY")
    
    # Azure OpenAI configuration
    # Support both AI_TOKEN and OPENAI_KEY for flexibility
    api_key = get_env_var("OPENAI_KEY", required=False) or get_env_var("AI_TOKEN", required=False)
    if not api_key:
        print("Error: Either OPENAI_KEY or AI_TOKEN must be set", file=sys.stderr)
        sys.exit(1)
    
    api_url = get_env_var("OPENAI_URL")
    
    print(f"Processing issue #{issue_number} in {repository}")
    print(f"Title: {issue_title}")
    print(f"Author: @{issue_author}")
    
    # Call Azure OpenAI to generate response
    response = call_azure_openai(api_url, api_key, issue_title, issue_body, issue_author)
    
    if response:
        print("\n=== Generated Response ===")
        print(response)
        print("=========================\n")
        
        # Save response to file for GitHub Actions to use
        output_file = "/tmp/ai_response.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response)
        
        # Set output for GitHub Actions
        github_output = os.environ.get("GITHUB_OUTPUT")
        if github_output:
            with open(github_output, "a", encoding="utf-8") as f:
                f.write(f"response=success\n")
        
        print(f"Response saved to {output_file}")
        sys.exit(0)
    else:
        print("Failed to generate response", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
