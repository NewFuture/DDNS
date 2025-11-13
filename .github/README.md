# .github Directory Structure

This directory contains GitHub-specific configuration files and documentation for the DDNS project.

## Directory Overview

```
.github/
├── ISSUE_TEMPLATE/          # Issue templates for bug reports, features, etc.
├── workflows/               # GitHub Actions CI/CD workflows
├── instructions/            # Coding standards and guidelines for AI assistants
├── prompts/                 # AI agent prompts and configurations
├── CODEOWNERS              # Code ownership and review assignments
├── CONTRIBUTING.md         # Contribution guidelines
├── PULL_REQUEST_TEMPLATE.md # PR template for consistent submissions
├── SECURITY.md             # Security policy and vulnerability reporting
├── copilot-instructions.md # GitHub Copilot configuration
├── .copilotignore          # Files to exclude from Copilot context
├── dependabot.yml          # Automated dependency updates
└── README.md               # This file
```

## File Purposes

### Issue Templates (`ISSUE_TEMPLATE/`)
Templates for creating structured issues:
- `debug.md` - Bug reports and debugging issues
- `feature_request.md` - Feature requests and enhancements
- `new-dns-provider.md` - Template for adding new DNS providers
- `other-issues.md` - General issues

### Workflows (`workflows/`)
GitHub Actions automation:
- `build.yml` - Build and test on multiple Python versions
- `publish.yml` - Publish to PyPI on release
- `test-install.yml` - Test installation across platforms
- `build-nuitka-docker.yml` - Build optimized Docker images

See [workflows/README.md](workflows/README.md) for details.

### Instructions (`instructions/`)
AI-assisted development guidelines:
- `python.instructions.md` - Python coding standards and best practices

These files help GitHub Copilot and other AI tools understand the project's coding standards and conventions.

### Prompts (`prompts/`)
Custom AI agent configurations:
- `agent.prompt.md` - Instructions for AI agents working on this project

### Core Files

#### `CODEOWNERS`
Defines code ownership for automatic review requests. When a PR touches specific files or directories, the corresponding owners are automatically requested for review.

#### `CONTRIBUTING.md`
Comprehensive guide for contributors covering:
- Development setup
- Coding standards
- Testing requirements
- Pull request process
- Provider development

#### `PULL_REQUEST_TEMPLATE.md`
Template that appears when creating a pull request, ensuring:
- Complete description of changes
- Proper testing checklist
- Documentation updates
- Code quality verification

#### `SECURITY.md`
Security policy including:
- Supported versions
- Vulnerability reporting process
- Security best practices
- Disclosure policy

#### `copilot-instructions.md`
Main configuration file for GitHub Copilot, providing:
- Project overview
- Coding standards
- Common tasks
- Quick reference for contributors

#### `.copilotignore`
Excludes unnecessary files from Copilot context to improve performance and relevance.

#### `dependabot.yml`
Configures automated dependency updates for:
- GitHub Actions
- Python packages (dev dependencies)
- Docker base images

## AI-Native Features

This repository is optimized for AI-assisted development:

### GitHub Copilot Integration
- **Instructions**: Clear guidelines in `copilot-instructions.md`
- **Context filtering**: `.copilotignore` excludes irrelevant files
- **Coding standards**: Detailed in `instructions/python.instructions.md`
- **Examples**: Test templates and code patterns throughout

### Custom AI Agents
- **Agent prompts**: Located in `prompts/` directory
- **Task-specific instructions**: Tailored for different development tasks
- **Consistency**: Ensures AI-generated code follows project standards

### Benefits
1. **Faster onboarding**: New contributors get instant guidance
2. **Consistent code**: AI suggestions follow project conventions
3. **Better reviews**: Automated checks reduce review burden
4. **Quality assurance**: Templates ensure complete information

## Maintaining This Directory

When adding or modifying files in `.github/`:

1. **Update this README**: Document new files or changes
2. **Keep templates current**: Ensure templates match actual processes
3. **Test workflows**: Verify changes to GitHub Actions
4. **Validate instructions**: Ensure AI guidance is accurate
5. **Review regularly**: Keep documentation up to date

## References

- [GitHub Documentation](https://docs.github.com)
- [GitHub Actions](https://docs.github.com/en/actions)
- [GitHub Copilot](https://docs.github.com/en/copilot)
- [Issue Templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [CODEOWNERS](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)

## Questions?

If you have questions about any of these files:
1. Check the documentation linked above
2. Review existing issues and PRs for examples
3. Ask in a new issue with the `question` label
