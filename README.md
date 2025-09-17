# Kaggle Discussion Extractor

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool for extracting Kaggle competition discussions and writeups with proper hierarchical structure and complete content preservation.

## 🎯 Features

- **Complete Discussion Extraction**: Full content from competition discussions and writeups
- **Hierarchical Comments**: Proper reply nesting (1, 1.1, 1.1.1, etc.)
- **Leaderboard Integration**: Extract writeups directly from competition leaderboards
- **Rich Metadata**: Author info, rankings, timestamps, upvotes
- **Multiple Formats**: Markdown, HTML, and JSON output

## 📦 Installation

```bash
pip install kaggle-discussion-extractor
playwright install chromium
```

## 🚀 Quick Start

### Command Line

```bash
# Extract discussions from a competition
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025

# Extract top 5 discussions only
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --limit 5

# Enable detailed logging
kaggle-discussion-extractor https://www.kaggle.com/competitions/neurips-2025 --dev-mode
```

### Python API

```python
import asyncio
from kaggle_discussion_extractor import KaggleDiscussionExtractor

async def extract_discussions():
    extractor = KaggleDiscussionExtractor()

    # Extract all discussions
    await extractor.extract_competition_discussions(
        "https://www.kaggle.com/competitions/neurips-2025"
    )

    # Extract writeups from leaderboard
    await extractor.extract_competition_writeups(
        "https://www.kaggle.com/competitions/neurips-2025",
        limit=5
    )

asyncio.run(extract_discussions())
```

## 📋 Commands

| Command | Description |
|---------|-------------|
| `kaggle-discussion-extractor <url>` | Extract all discussions |
| `--limit N` | Extract only N discussions |
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
await extractor.extract_competition_discussions(url, limit=10)

# Extract writeups only
await extractor.extract_competition_writeups(url, limit=5)

# Extract single discussion
discussion = await extractor.extract_single_discussion(page, discussion_url)
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

## 🎯 Key Features

- **Leaderboard-Based Extraction**: Automatically finds top writeups from competition leaderboards
- **Complete Content Preservation**: No trimming or content loss
- **Team Detection**: Properly handles multi-member team writeups
- **Hierarchical Comments**: Perfect reply nesting with correct numbering
- **Multiple Output Formats**: MD for reading, HTML for viewing, JSON for processing

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

**Made for the Kaggle community** 🏆