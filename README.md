# Kaggle Discussion Extractor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=flat&logo=playwright&logoColor=white)](https://playwright.dev/python/)

A professional-grade Python tool for extracting and analyzing discussions, solution writeups, and notebooks from Kaggle competitions. Features hierarchical reply extraction, automatic writeup extraction from leaderboards, competition notebook downloading with conversion to Python files, and clean markdown output with rich metadata.

## 🚀 Key Features

### 📓 Notebook Download & Conversion
- **Competition Notebook Discovery**: Automatically finds all public notebooks from competitions
- **Kaggle API Integration**: Uses Kaggle CLI API for reliable notebook listing (primary method)
- **Web Scraping Fallback**: Advanced lazy loading with configurable retry attempts
- **Automatic Conversion**: Converts `.ipynb` files to clean Python `.py` files
- **Smart Naming**: Files saved as `{NotebookTitle}_{YYMMDD}.py` with metadata headers
- **Batch Processing**: Download and convert multiple notebooks efficiently

### Competition Writeup Extraction
- **Leaderboard Scraping**: Automatically extracts writeup URLs from competition leaderboards
- **Private/Public Leaderboards**: Supports both private and public leaderboard tabs
- **Custom Naming**: Files saved as `{contest_name}_{rank}_{team_name}.md`
- **Rich Metadata**: Includes rank, team members, scores, and extraction timestamps
- **Top-N Selection**: Extract only top performers (e.g., top 10)

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
- **Lazy Loading Handling**: Advanced infinite scroll with configurable retry attempts
- **Batch Processing**: Extract all discussions, writeups, or notebooks from a competition at once
- **Rate Limiting**: Built-in delays to respect server resources
- **Error Recovery**: Robust error handling with detailed logging
- **Multiple Output Formats**: Clean Markdown export and Python file conversion
- **Hybrid Extraction**: Kaggle API integration with web scraping fallback

## 📦 Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install kaggle-discussion-extractor
playwright install chromium
```

### Method 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/Letemoin/kaggle-discussion-extractor.git
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

# Extract top 10 writeups from private leaderboard
kaggle-discussion-extractor https://www.kaggle.com/competitions/cmi-detect-behavior --extract-writeups --limit 10

# Extract from public leaderboard with development mode
kaggle-discussion-extractor https://www.kaggle.com/competitions/cmi-detect-behavior --extract-writeups --leaderboard-tab public --dev-mode

# Download competition notebooks and convert to Python files
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --download-notebooks

# Download notebooks with enhanced extraction (2 retry attempts)
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --download-notebooks --extraction-attempts 2 --limit 20
```

### Python API Usage

#### Extract Discussions
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

#### Extract Writeups
```python
import asyncio
from kaggle_discussion_extractor import KaggleWriteupExtractor

async def extract_writeups():
    # Initialize writeup extractor
    extractor = KaggleWriteupExtractor(dev_mode=True)
    
    # Extract top 5 writeups from private leaderboard
    success = await extractor.extract_writeups(
        competition_url="https://www.kaggle.com/competitions/cmi-detect-behavior",
        limit=5,
        leaderboard_tab="private"
    )
    
    if success:
        print("Writeup extraction completed successfully!")
    else:
        print("Writeup extraction failed!")

# Run the extraction
asyncio.run(extract_writeups())
```

#### Download Notebooks
```python
import asyncio
from kaggle_discussion_extractor import KaggleNotebookDownloader

async def download_notebooks():
    # Initialize notebook downloader
    downloader = KaggleNotebookDownloader(
        dev_mode=True,
        extraction_attempts=2  # Enhanced extraction with 2 retry attempts
    )
    
    # Extract notebook list from competition
    notebooks = await downloader.extract_notebook_list(
        competition_url="https://www.kaggle.com/competitions/neurips-2025",
        limit=20  # Download top 20 notebooks
    )
    
    print(f"Found {len(notebooks)} notebooks:")
    for notebook in notebooks:
        print(f"  - {notebook.title} by {notebook.author}")
    
    # Download and convert notebooks to Python files
    output_dir = Path("competition_notebooks")
    success_count = 0
    
    for notebook in notebooks:
        success = await downloader.extract_notebook_comments(notebook, output_dir)
        if success:
            success_count += 1
    
    print(f"Successfully downloaded {success_count}/{len(notebooks)} notebooks")

# Run the download
asyncio.run(download_notebooks())
```

## 📋 CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `competition_url` | URL of the Kaggle competition (required) | - |
| `--limit, -l` | Number of discussions/writeups/notebooks to extract | All |
| `--dev-mode, -d` | Enable detailed logging | False |
| `--no-headless` | Run browser in visible mode | False (headless) |
| `--date-format` | Include YYMMDD date in filename | False |
| `--date-position` | Position of date (prefix/suffix) | suffix |
| `--extract-writeups` | Extract writeups from leaderboard | False |
| `--leaderboard-tab` | Leaderboard tab (private/public) | private |
| `--download-notebooks` | Download and convert notebooks to Python | False |
| `--extraction-attempts` | Number of retry attempts for notebook extraction | 1 |
| `--notebooks-input` | Text file with notebook URLs for batch download | - |
| `--version, -v` | Show version information | - |

## 📁 Output Structure

### 📓 Notebook Downloads
The notebook downloader creates a custom output directory (default: current directory) with:

```
competition_notebooks/
├── Neurips Simple Baseline With Lightgbm_250908.py
├── Multi Seed Ensemble Of Gbdts And A Neural Network_250908.py
├── Lb 0 067 2Gpu Chemberta Train_250908.py
├── End To End Best Practice Solution_250908.py
└── ...
```

Each Python file includes:
- **Metadata Header**: Original title, author, source URL, download timestamp
- **Clean Python Code**: Converted from Jupyter notebook cells
- **Preserved Structure**: In[ ] comments maintain original cell organization

### Writeup Extraction
The writeup extractor creates a `writeups_extracted` directory with:

```
writeups_extracted/
├── contest-name_01_TeamName.md
├── contest-name_02_AnotherTeam.md 
├── contest-name_03_ThirdPlace.md
└── ...
```

### Discussion Extraction
The discussion extractor creates a `kaggle_discussions_extracted` directory with:

```
kaggle_discussions_extracted/
├── 01_Discussion_Title.md
├── 02_Another_Discussion.md
├── 03_Third_Discussion.md
└── ...
```

### Sample Notebook Output Format

```python
#!/usr/bin/env python3
"""
Neurips Simple Baseline With Lightgbm
Author: jade290395
Last Updated: 250908
Source: https://www.kaggle.com/code/jade290395/neurips-simple-baseline-with-lightgbm
Downloaded: 2025-09-08 22:04:47
"""

#!/usr/bin/env python
# coding: utf-8

# In[ ]:

import pandas as pd
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from lightgbm import LGBMRegressor

# In[ ]:

# Load data and build features
tg = pd.read_csv('/kaggle/input/modred-dataset/desc_tg.csv')
tc = pd.read_csv('/kaggle/input/modred-dataset/desc_tc.csv')

# Continue with notebook code...
```

### Sample Discussion Output Format

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

### Notebook Download Example

```python
from kaggle_discussion_extractor import KaggleNotebookDownloader
import asyncio
from pathlib import Path

async def download_competition_notebooks():
    # Initialize with enhanced extraction settings
    downloader = KaggleNotebookDownloader(
        dev_mode=True,           # Enable detailed logging
        headless=True,           # Run in background
        extraction_attempts=2    # Try extraction twice for better results
    )
    
    # Download notebooks from competition
    notebooks = await downloader.extract_notebook_list(
        "https://www.kaggle.com/competitions/neurips-2025",
        limit=15  # Download top 15 notebooks
    )
    
    # Create output directory
    output_dir = Path("neurips_notebooks")
    output_dir.mkdir(exist_ok=True)
    
    # Download and convert each notebook
    for i, notebook in enumerate(notebooks, 1):
        print(f"Processing {i}/{len(notebooks)}: {notebook.title}")
        success = await downloader.extract_notebook_comments(notebook, output_dir)
        if success:
            print(f"✅ Downloaded: {notebook.filename}")
        else:
            print(f"❌ Failed: {notebook.title}")

asyncio.run(download_competition_notebooks())
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
git clone https://github.com/Letemoin/kaggle-discussion-extractor.git
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
├── __init__.py              # Package initialization and exports
├── core.py                 # Discussion extraction logic
├── writeup_extractor.py    # Leaderboard writeup extraction
├── notebook_downloader.py  # Competition notebook downloading
└── cli.py                  # Command-line interface
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.


## 🙏 Acknowledgments

- Built with [Playwright](https://playwright.dev/) for reliable browser automation
- Uses [nbformat](https://nbformat.readthedocs.io/) and [nbconvert](https://nbconvert.readthedocs.io/) for Jupyter notebook processing
- Integrates with [Kaggle CLI](https://github.com/Kaggle/kaggle-api) for robust notebook discovery
- Inspired by the need for better Kaggle competition analysis tools
- Thanks to the open-source community for continuous support

