# Kaggle Discussion Extractor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=flat&logo=playwright&logoColor=white)](https://playwright.dev/python/)

A professional-grade Python tool for extracting and analyzing discussions from Kaggle competitions. Features hierarchical reply extraction with proper parent-child relationships, pagination support, and clean markdown output.

## 🚀 Key Features

### Hierarchical Discussion Extraction
- **Complete Thread Preservation**: Maintains the full discussion structure with parent-child relationships
- **Smart Reply Numbering**: Automatic hierarchical numbering (1, 1.1, 1.2, 2, 2.1, etc.)
- **No Content Duplication**: Intelligently separates parent and nested reply content
- **Deep Nesting Support**: Handles multiple levels of nested replies

### Rich Metadata Extraction
- **Author Information**: Names, usernames, profile URLs
- **Competition Rankings**: Extracts "Nth in this Competition" rankings
- **User Badges**: Competition Host, Expert, Master, Grandmaster badges
- **Engagement Metrics**: Upvotes/downvotes for all posts and replies
- **Timestamps**: Full timestamp extraction for temporal analysis

### Advanced Capabilities
- **Pagination Support**: Automatically handles multi-page discussion lists
- **Batch Processing**: Extract all discussions from a competition at once
- **Rate Limiting**: Built-in delays to respect server resources
- **Error Recovery**: Robust error handling with detailed logging
- **Multiple Output Formats**: Clean Markdown export with proper formatting

## 📦 Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install kaggle-discussion-extractor
playwright install chromium
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/kaggle-discussion-extractor.git
cd kaggle-discussion-extractor

# Install in development mode
pip install -e .
playwright install chromium
```

## 🎯 Quick Start

### Command Line Usage

```bash
# Extract all discussions from a competition
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025

# Extract only 10 discussions
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --limit 10

# Enable development mode for detailed logging
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --dev-mode

# Run with visible browser (useful for debugging)
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --no-headless
```

### Python API Usage

```python
import asyncio
from kaggle_discussion_extractor import KaggleDiscussionExtractor

async def extract_discussions():
    # Initialize extractor
    extractor = KaggleDiscussionExtractor(dev_mode=True)
    
    # Extract discussions
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=5  # Optional: limit number of discussions
    )
    
    if success:
        print("Extraction completed successfully!")
    else:
        print("Extraction failed!")

# Run the extraction
asyncio.run(extract_discussions())
```

## 📋 CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `competition_url` | URL of the Kaggle competition (required) | - |
| `--limit, -l` | Number of discussions to extract | All |
| `--dev-mode, -d` | Enable detailed logging | False |
| `--no-headless` | Run browser in visible mode | False (headless) |
| `--version, -v` | Show version information | - |

## 📁 Output Structure

The extractor creates a `kaggle_discussions_extracted` directory with:

```
kaggle_discussions_extracted/
├── 01_Discussion_Title.md
├── 02_Another_Discussion.md
├── 03_Third_Discussion.md
└── ...
```

### Sample Output Format

```markdown
# Discussion Title

**URL**: https://www.kaggle.com/competitions/neurips-2025/discussion/123456
**Total Comments**: 15
**Extracted**: 2025-01-15T10:30:00

---

## Main Post

**Author**: username (@username)
**Rank**: 27th in this Competition
**Badges**: Competition Host
**Upvotes**: 36

Main discussion content goes here...

---

## Replies

### Reply 1

- **Author**: user1 (@user1)
- **Rank**: 154th in this Competition
- **Upvotes**: 11
- **Timestamp**: Tue Jun 17 2025 11:54:57 GMT+0300

Content of reply 1...

  #### Reply 1.1

  - **Author**: user2 (@user2)
  - **Upvotes**: 6
  - **Timestamp**: Sun Jun 29 2025 04:20:43 GMT+0300

  Nested reply content...

  #### Reply 1.2

  - **Author**: user3 (@user3)
  - **Upvotes**: 2
  - **Timestamp**: Wed Jul 16 2025 12:50:34 GMT+0300

  Another nested reply...

---

### Reply 2

- **Author**: user4 (@user4)
- **Upvotes**: -3

Content of reply 2...

---
```

## ⚙️ Configuration

### Development Mode

Enable development mode to see detailed logs and debugging information:

```python
extractor = KaggleDiscussionExtractor(dev_mode=True)
```

**What dev_mode does:**
- Enables DEBUG level logging
- Shows detailed progress information
- Displays browser automation steps
- Provides error stack traces
- Logs DOM element detection details

### Browser Mode

Run with visible browser for debugging:

```python
extractor = KaggleDiscussionExtractor(headless=False)
```

## 🧪 Examples

### Basic Example

```python
from kaggle_discussion_extractor import KaggleDiscussionExtractor
import asyncio

async def main():
    extractor = KaggleDiscussionExtractor()
    
    await extractor.extract_competition_discussions(
        "https://www.kaggle.com/competitions/neurips-2025"
    )

asyncio.run(main())
```

### Advanced Example with Logging

```python
import asyncio
import logging
from kaggle_discussion_extractor import KaggleDiscussionExtractor

# Setup custom logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def extract_with_monitoring():
    extractor = KaggleDiscussionExtractor(
        dev_mode=True,  # Enable detailed logging
        headless=True   # Run in background
    )
    
    logger.info("Starting extraction...")
    
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=20  # Extract first 20 discussions
    )
    
    if success:
        logger.info("✅ Extraction completed successfully!")
        logger.info("Check 'kaggle_discussions_extracted' directory for results")
    else:
        logger.error("❌ Extraction failed!")

if __name__ == "__main__":
    asyncio.run(extract_with_monitoring())
```

## 🔧 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/kaggle-discussion-extractor.git
cd kaggle-discussion-extractor

# Install development dependencies
pip install -e ".[dev]"
playwright install chromium

# Run tests
pytest tests/
```

### Project Structure

```
kaggle_discussion_extractor/
├── __init__.py          # Package initialization
├── core.py             # Main extraction logic
└── cli.py              # Command-line interface
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
- Inspired by the need for better Kaggle competition analysis tools
- Thanks to the open-source community for continuous support

## 📊 Features Comparison

| Feature | This Tool | Other Tools |
|---------|-----------|-------------|
| Hierarchical Replies | ✅ Perfect (1, 1.1, 1.2) | ❌ Flat structure |
| No Content Duplication | ✅ Smart separation | ❌ Duplicated content |
| Pagination Support | ✅ All pages | ❌ Single page only |
| Author Rankings | ✅ Full metadata | ❌ Basic info only |
| Rate Limiting | ✅ Respectful delays | ❌ Aggressive scraping |
| Error Recovery | ✅ Robust handling | ❌ Fails on errors |

---

**Made with ❤️ for the Kaggle community**