# PyPI Publishing Guide

## Overview

This repository includes automated PyPI publishing scripts to manage package releases with proper version management, git tagging, and deployment to both Test PyPI and production PyPI.

## Files Created

1. **`publish_pypi.py`** - Main publishing script with full workflow automation
2. **`test_publish.py`** - Test script to validate publishing setup
3. **Updated `setup.py`** - Package configuration with correct repository URLs
4. **Updated `pyproject.toml`** - Modern Python packaging configuration

## Prerequisites

### Install Required Tools
```bash
pip install build twine
```

### Configure PyPI Authentication

Create `~/.pypirc` with your PyPI credentials:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = your-pypi-api-token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = your-test-pypi-api-token
```

## Usage

### 1. Test the Setup
```bash
python test_publish.py
```

This validates:
- Package imports correctly
- CLI entry points work
- Build configuration is valid
- Version consistency between files
- Dependencies are available

### 2. Publish to Test PyPI (Recommended First)
```bash
# Patch version bump (1.1.0 → 1.1.1)
python publish_pypi.py --version patch --test

# Minor version bump (1.1.0 → 1.2.0)
python publish_pypi.py --version minor --test

# Specific version
python publish_pypi.py --version 1.2.3 --test
```

### 3. Test Installation from Test PyPI
```bash
pip install -i https://test.pypi.org/simple/ kaggle-discussion-extractor==1.1.1
```

### 4. Publish to Production PyPI
```bash
# After testing, publish to production
python publish_pypi.py --version patch

# For minor releases with new features
python publish_pypi.py --version minor

# For major breaking changes
python publish_pypi.py --version major
```

## Publishing Workflow

The `publish_pypi.py` script automates:

1. **Version Management**
   - Reads current version from `setup.py`
   - Bumps version based on type (major/minor/patch)
   - Updates both `setup.py` and `pyproject.toml`

2. **Changelog Updates**
   - Updates `CHANGELOG.md` with new version
   - Adds standard change notes for recent improvements

3. **Package Building**
   - Cleans previous build artifacts
   - Builds source distribution and wheel
   - Validates package with twine

4. **Publishing**
   - Uploads to Test PyPI or production PyPI
   - Provides installation instructions

5. **Git Operations**
   - Creates commit with version changes
   - Creates git tag for the release
   - Pushes changes and tags to remote

## Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--version patch` | Bump patch version (1.1.0 → 1.1.1) | Bug fixes |
| `--version minor` | Bump minor version (1.1.0 → 1.2.0) | New features |
| `--version major` | Bump major version (1.1.0 → 2.0.0) | Breaking changes |
| `--version 1.2.3` | Set specific version | Custom version |
| `--test` | Publish to Test PyPI only | Testing |
| `--skip-git` | Skip git tagging and pushing | Local testing |

## Current Package Information

- **Package Name**: `kaggle-discussion-extractor`
- **Current Version**: `1.1.0`
- **Repository**: https://github.com/Letemoin/kaggle-discussion-extractor
- **PyPI URL**: https://pypi.org/project/kaggle-discussion-extractor/

## Features in Current Version (1.1.0)

- Fixed leaderboard extraction with proper team detection
- Enhanced hierarchical comment structure with correct numbering
- Added complete content preservation without trimming
- Improved writeup extraction with multiple output formats (MD, HTML, JSON)
- Added leaderboard integration for automatic top writeup discovery
- Enhanced team detection for multi-member competition teams

## Example Workflow

```bash
# 1. Test the setup
python test_publish.py

# 2. Test on Test PyPI first
python publish_pypi.py --version patch --test

# 3. Install and test from Test PyPI
pip install -i https://test.pypi.org/simple/ kaggle-discussion-extractor==1.1.1

# 4. If everything works, publish to production
python publish_pypi.py --version patch

# 5. Verify production installation
pip install kaggle-discussion-extractor==1.1.1
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure `.pypirc` is configured correctly
   - Use API tokens instead of username/password
   - Check token permissions

2. **Build Errors**
   - Run `python test_publish.py` to identify issues
   - Ensure all dependencies are installed
   - Check `setup.py` and `pyproject.toml` syntax

3. **Version Conflicts**
   - Cannot upload same version twice to PyPI
   - Bump version or use `--force` flag if needed
   - Check existing versions on PyPI

4. **Git Issues**
   - Use `--skip-git` flag for testing
   - Ensure working directory is clean
   - Check git remote configuration

## Best Practices

1. **Always test first**: Use `--test` flag to publish to Test PyPI
2. **Semantic versioning**: Use patch for fixes, minor for features, major for breaking changes
3. **Clean testing**: Test installation in fresh virtual environment
4. **Documentation updates**: Update README and CHANGELOG before releasing
5. **Git hygiene**: Commit all changes before publishing

## Support

For issues with publishing:
1. Run `python test_publish.py` to validate setup
2. Check logs for specific error messages
3. Verify PyPI authentication
4. Ensure package builds locally with `python -m build`