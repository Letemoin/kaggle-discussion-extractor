# Kaggle Discussion Extractor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://img.shields.io/pypi/v/kaggle-discussion-extractor.svg)](https://pypi.org/project/kaggle-discussion-extractor/)

A professional Python tool for extracting Kaggle competition content with proper hierarchical structure and complete content preservation.

> ℹ️ **Note**: Starting September 17, 2025, Claude is contributing to fix and enhance this repository, focusing on improved leaderboard extraction, hierarchical comment structure, and complete content preservation.

## 🎯 Main Features

The package provides **3 core extraction capabilities**:

### 1. 💬 Discussion Extraction
Extract complete competition discussions with hierarchical reply structure, author metadata, rankings, and full content preservation.

### 2. 🏆 Writeup Extraction
Extract top-performing writeups directly from competition leaderboards with team information, rankings, and complete solution details in multiple formats (Markdown, HTML, JSON).

### 3. 📓 Code Notebook Extraction
Extract competition code notebooks, download them via Kaggle API, and convert them to Python files using nbconvert. Includes metadata preservation and automatic organization.

### Key Capabilities
- **Complete Content Preservation**: No trimming or content loss
- **Hierarchical Comments**: Proper reply nesting (1, 1.1, 1.1.1, etc.)
- **Leaderboard Integration**: Direct extraction from competition leaderboards
- **Team Detection**: Multi-member team writeup handling
- **Rich Metadata**: Author info, rankings, timestamps, upvotes, badges
- **Multiple Output Formats**: Markdown (readable), HTML (complete), JSON (structured)

## 📦 Installation

```bash
pip install kaggle-discussion-extractor
playwright install chromium
```

## 🚀 Quick Start

### Command Line

```bash
# Feature 1: Extract discussions from a competition
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025

# Feature 1: Extract top 5 discussions only
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --limit 5

# Feature 2: Extract writeups from leaderboard
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --writeups --limit 5

# Feature 3: Extract and convert notebooks to Python files
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --notebooks --limit 10

# Extract all 3 features with limits
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --writeups --notebooks --limit 5

# Enable detailed logging
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --dev-mode
```

### Python API

```python
import asyncio
from kaggle_discussion_extractor import KaggleDiscussionExtractor, KaggleNotebookDownloader

async def main():
    extractor = KaggleDiscussionExtractor()

    # 1. Extract Competition Discussions
    print("Extracting discussions...")
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=10  # Optional: limit number of discussions
    )

    if success:
        print("✅ Discussions extracted to kaggle_discussions_extracted/")

    # 2. Extract Competition Writeups from Leaderboard
    print("Extracting writeups...")
    success = await extractor.extract_competition_writeups(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=5  # Extract top 5 writeups
    )

    if success:
        print("✅ Writeups extracted to kaggle_writeups_extracted/")

    # 3. Extract and Convert Competition Notebooks
    print("Extracting notebooks...")
    notebook_downloader = KaggleNotebookDownloader()
    success = await notebook_downloader.download_competition_notebooks(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=10  # Extract top 10 notebooks
    )

    if success:
        print("✅ Notebooks extracted to kaggle_notebooks_downloaded/")

# Run the extraction
asyncio.run(main())
```

## 📋 Commands

| Command | Description |
|---------|-------------|
| `kaggle-discussion-extractor <url>` | Extract all discussions (Feature 1) |
| `--writeups` | Extract writeups from leaderboard (Feature 2) |
| `--notebooks` | Extract and convert notebooks to Python (Feature 3) |
| `--limit N` | Extract only N discussions/writeups/notebooks |
| `--dev-mode` | Enable detailed logging |
| `--no-headless` | Show browser window |

## 📁 Output

### File Structure
```
kaggle_discussions_extracted/
├── 01_Discussion_Title.md
├── 02_Another_Discussion.md
└── 03_Third_Discussion.md

kaggle_writeups_extracted/
├── Rank_01_Team_Name.md        # Markdown (readable)
├── Rank_01_Team_Name.html      # Complete HTML
├── Rank_01_Team_Name.json      # Structured data
└── ...

kaggle_notebooks_downloaded/
├── competition-name/
│   ├── Notebook_Title_1_240918.py    # Converted Python
│   ├── Notebook_Title_1_240918.ipynb # Original notebook
│   ├── Notebook_Title_2_240918.py    # Converted Python
│   └── Notebook_Title_2_240918.ipynb # Original notebook
└── ...
```

### Output Format
```markdown
# Discussion Title

**URL**: https://www.kaggle.com/competitions/neurips-2025/discussion/123456
**Total Comments**: 15
**Extracted**: 2025-01-15T10:30:00

---

## Main Post

**Author**: username (@username)
**Rank**: 27th in this Competition
**Upvotes**: 36

Main discussion content...

---

## Replies

### Reply 1
- **Author**: user1 (@user1)
- **Rank**: 154th in this Competition
- **Upvotes**: 11

Reply content...

  #### Reply 1.1
  - **Author**: user2 (@user2)
  - **Upvotes**: 6

  Nested reply content...

### Reply 2
- **Author**: user3 (@user3)
- **Upvotes**: 2

Another reply...
```

## ⚙️ Configuration

### Basic Usage
```python
# Default settings
extractor = KaggleDiscussionExtractor()

# Development mode (detailed logs)
extractor = KaggleDiscussionExtractor(dev_mode=True)

# Visible browser (for debugging)
extractor = KaggleDiscussionExtractor(headless=False)
```

### Extract Specific Content
```python
# Extract discussions only
success = await extractor.extract_competition_discussions(
    competition_url="https://www.kaggle.com/competitions/your-competition",
    limit=10
)

# Extract writeups only
success = await extractor.extract_competition_writeups(
    competition_url="https://www.kaggle.com/competitions/your-competition",
    limit=5
)

# Extract single discussion (requires page object)
from playwright.async_api import async_playwright
async with async_playwright() as p:
    browser = await p.chromium.launch()
    page = await browser.new_page()
    discussion = await extractor.extract_single_discussion(page, discussion_url)
    await browser.close()
```

## 🔧 Development

### Setup
```bash
git clone https://github.com/yourusername/kaggle-discussion-extractor.git
cd kaggle-discussion-extractor
pip install -e .
playwright install chromium
```

### Run Tests
```bash
pytest tests/
```

### Project Structure
```
kaggle_discussion_extractor/
├── __init__.py          # Package exports
├── core.py             # Main extraction logic
└── cli.py              # Command-line interface
```

## 📋 Package Publishing

This package is available on PyPI and can be built/published using the included scripts:

```bash
# Build package locally
python pypi.py

# Manual upload to PyPI (requires credentials)
twine upload dist/*
```

See [PYPI_PUBLISHING_GUIDE.md](PYPI_PUBLISHING_GUIDE.md) for detailed publishing instructions.

## 🎯 Technical Features

- **🏆 Leaderboard-Based Extraction**: Automatically finds top writeups from competition leaderboards with team information
- **📝 Complete Content Preservation**: No trimming or content loss - full solution details captured
- **👥 Team Detection**: Properly handles multi-member team writeups with individual member information
- **🔄 Hierarchical Comments**: Perfect reply nesting with correct numbering (1, 1.1, 1.1.1, etc.)
- **📄 Multiple Output Formats**: MD for reading, HTML for viewing, JSON for processing
- **📊 Rich Metadata**: Author rankings, badges, timestamps, upvotes, team composition, scores
- **⚙️ Advanced Parsing**: Handles complex leaderboard structures and discussion pagination

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

**Made for the Kaggle community** 🏆