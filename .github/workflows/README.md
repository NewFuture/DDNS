# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD processes.

## Workflows

### Build Workflow (`build.yml`)
- **Trigger**: Push to main/master, pull requests
- **Purpose**: Build and test the application
- **Actions**:
  - Run unit tests on multiple Python versions
  - Lint and format check
  - Build package
  - Verify compatibility

### Publish Workflow (`publish.yml`)
- **Trigger**: Release published
- **Purpose**: Publish package to PyPI
- **Actions**:
  - Build distribution packages
  - Upload to PyPI
  - Create GitHub release assets

### Test Install Workflow (`test-install.yml`)
- **Trigger**: Various events
- **Purpose**: Verify installation across platforms
- **Actions**:
  - Test pip installation
  - Test Docker builds
  - Verify executables

### Build Nuitka Docker Workflow (`build-nuitka-docker.yml`)
- **Trigger**: Specific events
- **Purpose**: Build optimized Docker images with Nuitka
- **Actions**:
  - Compile with Nuitka
  - Build multi-arch Docker images
  - Push to Docker Hub

## Secrets Required

The following secrets should be configured in repository settings:

- `PYPI_API_TOKEN`: For publishing to PyPI
- `DOCKERHUB_USERNAME`: For Docker Hub publishing
- `DOCKERHUB_TOKEN`: For Docker Hub authentication

## Local Testing

To test workflows locally, you can use [act](https://github.com/nektos/act):

```bash
# Install act
# macOS: brew install act
# Linux: See https://github.com/nektos/act#installation

# Run a specific workflow
act -j test

# Run with secrets
act -j test --secret-file .secrets
```

## Maintenance

When modifying workflows:

1. Test locally when possible
2. Update this README if adding new workflows
3. Follow GitHub Actions best practices
4. Use specific action versions (not `@master`)
5. Add appropriate comments in workflow files
6. Keep secrets secure and rotated

## Security

- Never commit secrets or tokens
- Use GitHub secrets for sensitive data
- Review workflow permissions regularly
- Keep actions up to date via Dependabot

## Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
