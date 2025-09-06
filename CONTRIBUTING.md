# Contributing to Kaggle Discussion Extractor

First off, thank you for considering contributing to Kaggle Discussion Extractor! It's people like you that make this tool better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Describe the behavior you observed and expected**
- **Include screenshots if relevant**
- **Include your environment details** (OS, Python version, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:

- **Use a clear and descriptive title**
- **Provide a detailed description of the suggested enhancement**
- **Provide specific examples to demonstrate the enhancement**
- **Describe the current behavior and expected behavior**
- **Explain why this enhancement would be useful**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure the test suite passes
4. Make sure your code follows the existing style
5. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/kaggle-discussion-extractor.git
cd kaggle-discussion-extractor

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[dev,enhanced]"

# Install pre-commit hooks
pre-commit install

# Install playwright browsers
playwright install chromium
```

## Development Guidelines

### Code Style

We use [Black](https://github.com/psf/black) for code formatting:

```bash
# Format code
black .

# Check formatting
black --check .
```

### Type Hints

We use type hints throughout the codebase:

```python
from typing import List, Optional, Dict, Any

def extract_discussions(
    url: str,
    limit: Optional[int] = None
) -> List[Discussion]:
    ...
```

### Testing

Write tests for new functionality:

```python
# tests/test_extractor.py
import pytest
from kaggle_discussion_extractor import KaggleDiscussionExtractor

@pytest.mark.asyncio
async def test_extract_single_discussion():
    async with KaggleDiscussionExtractor() as extractor:
        discussion = await extractor.extract_single_discussion(url)
        assert discussion is not None
        assert discussion.title != ""
```

Run tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kaggle_discussion_extractor

# Run specific test file
pytest tests/test_extractor.py
```

### Documentation

- Add docstrings to all public functions and classes
- Update README.md if adding new features
- Include examples in docstrings

Example docstring:

```python
def extract_author_info(element: ElementHandle) -> Author:
    """
    Extract author information from a page element.
    
    Args:
        element: Playwright ElementHandle containing author data
        
    Returns:
        Author object with extracted information
        
    Example:
        >>> author = await extract_author_info(element)
        >>> print(author.name)
        'John Doe'
    """
```

### Commit Messages

Follow these conventions for commit messages:

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
- `feat: Add support for dataset discussions`
- `fix: Handle pagination edge case`
- `docs: Update installation instructions`
- `test: Add tests for reply extraction`
- `refactor: Simplify content cleaning logic`

## Project Structure

```
kaggle_discussion_extractor/
├── core/              # Core functionality
│   ├── extractor.py   # Main extraction logic
│   └── models.py      # Data models
├── utils/             # Utility functions
├── tests/             # Test suite
├── examples/          # Example scripts
└── docs/              # Documentation
```

### Adding New Features

1. **Discuss First**: Open an issue to discuss the feature
2. **Design**: Consider the API and user experience
3. **Implement**: Write clean, documented code
4. **Test**: Add comprehensive tests
5. **Document**: Update README and add examples

### Code Review Process

All submissions require review. We use GitHub pull requests for this purpose:

1. **Automated Checks**: Ensure CI passes
2. **Code Quality**: Maintainers review for quality and style
3. **Functionality**: Test the changes work as expected
4. **Documentation**: Ensure docs are updated

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md
3. Create a git tag: `git tag -a v1.0.0 -m "Release version 1.0.0"`
4. Push to GitHub: `git push origin v1.0.0`
5. Create GitHub release
6. Deploy to PyPI

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers directly.

Thank you for contributing!