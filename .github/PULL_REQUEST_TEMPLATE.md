## Description

<!-- Provide a clear and concise description of the changes -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Code refactoring (no functional changes)
- [ ] Performance improvement
- [ ] New DNS provider
- [ ] Other (please describe):

## Related Issues

<!-- Link to related issues using #issue_number -->

Fixes #
Related to #

## Changes Made

<!-- List the specific changes made in this PR -->

- 
- 
- 

## Testing

<!-- Describe the tests you ran to verify your changes -->

- [ ] Existing tests pass: `python3 -m unittest discover tests -v`
- [ ] Code formatted: `ruff format .`
- [ ] Code linted: `ruff check --fix --unsafe-fixes .`
- [ ] Added new tests for new functionality
- [ ] Tested on Python 2.7 (if applicable)
- [ ] Tested on Python 3.x

## Checklist

<!-- Mark completed items with an "x" -->

- [ ] My code follows the [Python coding standards](.github/instructions/python.instructions.md)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## For New DNS Providers

<!-- Only fill this section if adding a new DNS provider -->

- [ ] Provider implementation inherits from `BaseProvider` or `SimpleProvider`
- [ ] All required methods are implemented
- [ ] Provider added to `ddns/__init__.py`
- [ ] Unit tests created in `tests/`
- [ ] Documentation created in `doc/providers/[provider].md`
- [ ] Schema updated in `schema/v4.0.json` (if needed)
- [ ] Tested against real API (if possible)

## Additional Notes

<!-- Any additional information that reviewers should know -->
