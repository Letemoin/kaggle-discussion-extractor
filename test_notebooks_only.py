#!/usr/bin/env python3
"""
Quick test for notebook extraction functionality
"""

import asyncio
import sys
from pathlib import Path

# Add the package to the path for testing
sys.path.insert(0, str(Path(__file__).parent))

from kaggle_discussion_extractor import KaggleNotebookDownloader

async def test_notebook_list_only():
    """Test just the notebook list extraction"""
    print("="*60)
    print("TESTING NOTEBOOK LIST EXTRACTION")
    print("="*60)

    try:
        downloader = KaggleNotebookDownloader(dev_mode=False, headless=True)

        # Test with a competition that should have notebooks
        test_url = "https://www.kaggle.com/competitions/ariel-data-challenge-2025"

        print(f"Testing notebook list from: {test_url}")

        # Get notebook list
        notebooks = await downloader.extract_notebook_list(test_url, limit=5)

        if not notebooks:
            print("FAIL: No notebooks found")
            return False

        print(f"SUCCESS: Found {len(notebooks)} notebooks:")
        for i, notebook in enumerate(notebooks, 1):
            print(f"  {i}. Title: {notebook.title}")
            print(f"     Author: {notebook.author}")
            print(f"     URL: {notebook.url}")
            print(f"     Filename: {notebook.filename}")
            print()

        # Check if URLs are valid (not comment links)
        comment_links = [nb for nb in notebooks if '/comments' in nb.url]
        valid_links = [nb for nb in notebooks if '/comments' not in nb.url]

        print(f"Analysis:")
        print(f"  Valid notebook links: {len(valid_links)}")
        print(f"  Comment links (filtered): {len(comment_links)}")

        return len(valid_links) > 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run the test"""
    print("QUICK NOTEBOOK EXTRACTION TEST")
    print("=" * 60)

    success = await test_notebook_list_only()

    print("\n" + "="*60)
    if success:
        print("RESULT: Notebook list extraction works!")
        print("The basic functionality is working correctly.")
    else:
        print("RESULT: Issues detected with notebook extraction")

    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"CRASH: {e}")
        sys.exit(1)