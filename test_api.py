#!/usr/bin/env python3
"""
Comprehensive API Testing Script for Kaggle Discussion Extractor
Tests all 3 main features: Discussions, Writeups, and Notebooks
"""

import asyncio
import sys
import traceback
from pathlib import Path

# Add the package to the path for testing
sys.path.insert(0, str(Path(__file__).parent))

try:
    from kaggle_discussion_extractor import (
        KaggleDiscussionExtractor,
        KaggleNotebookDownloader,
        NotebookInfo
    )
    print("PASS: All imports successful")
except ImportError as e:
    print(f"FAIL: Import failed: {e}")
    sys.exit(1)

async def test_discussion_extraction():
    """Test Feature 1: Discussion Extraction"""
    print("\n" + "="*60)
    print("TEST: TESTING FEATURE 1: DISCUSSION EXTRACTION")
    print("="*60)

    try:
        extractor = KaggleDiscussionExtractor(dev_mode=True, headless=True)

        # Test with a smaller competition
        test_url = "https://www.kaggle.com/competitions/ariel-data-challenge-2025"

        print(f"Testing discussion extraction from: {test_url}")
        print("Extracting 3 discussions for testing...")

        success = await extractor.extract_competition_discussions(
            competition_url=test_url,
            limit=3
        )

        if success:
            print("PASS: Discussion extraction completed successfully")

            # Check if files were created
            output_dir = Path("kaggle_discussions_extracted")
            if output_dir.exists():
                files = list(output_dir.glob("*.md"))
                print(f"PASS: Found {len(files)} discussion files:")
                for file in files[:3]:  # Show first 3
                    print(f"  - {file.name}")
                return True
            else:
                print("FAIL: Output directory not found")
                return False
        else:
            print("FAIL: Discussion extraction failed")
            return False

    except Exception as e:
        print(f"FAIL: Discussion extraction error: {e}")
        traceback.print_exc()
        return False

async def test_writeup_extraction():
    """Test Feature 2: Writeup Extraction"""
    print("\n" + "="*60)
    print("TEST: TESTING FEATURE 2: WRITEUP EXTRACTION")
    print("="*60)

    try:
        extractor = KaggleDiscussionExtractor(dev_mode=True, headless=True)

        # Test with a competition that has writeups
        test_url = "https://www.kaggle.com/competitions/ariel-data-challenge-2025"

        print(f"Testing writeup extraction from: {test_url}")
        print("Extracting 2 writeups for testing...")

        success = await extractor.extract_competition_writeups(
            competition_url=test_url,
            limit=2
        )

        if success:
            print("PASS: Writeup extraction completed successfully")

            # Check if files were created
            output_dir = Path("kaggle_writeups_extracted")
            if output_dir.exists():
                md_files = list(output_dir.glob("*.md"))
                html_files = list(output_dir.glob("*.html"))
                json_files = list(output_dir.glob("*.json"))

                print(f"PASS: Found {len(md_files)} MD, {len(html_files)} HTML, {len(json_files)} JSON files")

                if md_files:
                    for file in md_files[:2]:
                        print(f"  - {file.name}")

                return len(md_files) > 0
            else:
                print("FAIL: Output directory not found")
                return False
        else:
            print("FAIL: Writeup extraction failed")
            return False

    except Exception as e:
        print(f"FAIL: Writeup extraction error: {e}")
        traceback.print_exc()
        return False

async def test_notebook_extraction():
    """Test Feature 3: Notebook Extraction"""
    print("\n" + "="*60)
    print("TEST: TESTING FEATURE 3: NOTEBOOK EXTRACTION")
    print("="*60)

    try:
        downloader = KaggleNotebookDownloader(dev_mode=True, headless=True)

        # Test with a competition that has code notebooks
        test_url = "https://www.kaggle.com/competitions/ariel-data-challenge-2025"

        print(f"Testing notebook extraction from: {test_url}")
        print("Step 1: Testing notebook list extraction...")

        # First test just getting the notebook list
        notebooks = await downloader.extract_notebook_list(test_url, limit=3)

        if not notebooks:
            print("FAIL: No notebooks found in competition")
            return False

        print(f"PASS: Found {len(notebooks)} notebooks:")
        for i, notebook in enumerate(notebooks, 1):
            print(f"  {i}. {notebook.title}")
            print(f"     Author: {notebook.author}")
            print(f"     URL: {notebook.url}")
            print()

        print("Step 2: Testing notebook download and conversion...")

        # Try to download first notebook only
        if notebooks:
            test_notebook = notebooks[0]
            output_dir = Path("test_notebook_output")

            print(f"Testing download of: {test_notebook.title}")

            success = await downloader.download_and_convert_notebook(
                test_notebook,
                output_dir
            )

            if success:
                print("PASS: Notebook download and conversion successful")

                # Check if files were created
                if output_dir.exists():
                    py_files = list(output_dir.glob("*.py"))
                    ipynb_files = list(output_dir.glob("*.ipynb"))

                    print(f"PASS: Generated {len(py_files)} Python files, {len(ipynb_files)} notebook files")

                    if py_files:
                        print(f"  - Python: {py_files[0].name}")
                    if ipynb_files:
                        print(f"  - Notebook: {ipynb_files[0].name}")

                    return len(py_files) > 0 or len(ipynb_files) > 0
                else:
                    print("FAIL: Output directory not created")
                    return False
            else:
                print("FAIL: Notebook download/conversion failed")
                print("WARNING:  This might be due to Kaggle API authentication issues")
                print("WARNING:  Make sure 'kaggle' CLI is installed and authenticated")
                return False

    except Exception as e:
        print(f"FAIL: Notebook extraction error: {e}")
        traceback.print_exc()
        return False

async def test_imports_and_classes():
    """Test that all classes can be imported and instantiated"""
    print("\n" + "="*60)
    print("TEST: TESTING IMPORTS AND CLASS INSTANTIATION")
    print("="*60)

    try:
        # Test KaggleDiscussionExtractor
        print("Testing KaggleDiscussionExtractor...")
        extractor = KaggleDiscussionExtractor()
        print("PASS: KaggleDiscussionExtractor instantiated successfully")

        # Test KaggleNotebookDownloader
        print("Testing KaggleNotebookDownloader...")
        downloader = KaggleNotebookDownloader()
        print("PASS: KaggleNotebookDownloader instantiated successfully")

        # Test NotebookInfo dataclass
        print("Testing NotebookInfo...")
        notebook_info = NotebookInfo(
            title="Test Notebook",
            url="https://www.kaggle.com/code/test/notebook",
            author="test_user",
            last_updated="241218",
            filename="test_notebook.py"
        )
        print("PASS: NotebookInfo created successfully")
        print(f"  Title: {notebook_info.title}")
        print(f"  Author: {notebook_info.author}")

        return True

    except Exception as e:
        print(f"FAIL: Import/instantiation error: {e}")
        traceback.print_exc()
        return False

async def check_dependencies():
    """Check if all required dependencies are available"""
    print("\n" + "="*60)
    print("TEST: CHECKING DEPENDENCIES")
    print("="*60)

    dependencies = [
        ("playwright", "Playwright for web automation"),
        ("nbformat", "Jupyter notebook format support"),
        ("nbconvert", "Notebook conversion to Python"),
    ]

    all_available = True

    for dep_name, description in dependencies:
        try:
            __import__(dep_name)
            print(f"PASS: {dep_name}: {description}")
        except ImportError:
            print(f"FAIL: {dep_name}: Missing - {description}")
            all_available = False

    # Check kaggle CLI
    try:
        import subprocess
        result = subprocess.run(['kaggle', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"PASS: kaggle CLI: {result.stdout.strip()}")
        else:
            print("FAIL: kaggle CLI: Not available or not authenticated")
            print("  Install with: pip install kaggle")
            print("  Then setup API token: https://www.kaggle.com/docs/api")
            all_available = False
    except FileNotFoundError:
        print("FAIL: kaggle CLI: Not found")
        print("  Install with: pip install kaggle")
        all_available = False

    return all_available

async def main():
    """Run all tests"""
    print("START: KAGGLE DISCUSSION EXTRACTOR - COMPREHENSIVE API TESTING")
    print("=" * 70)

    # Check dependencies first
    deps_ok = await check_dependencies()

    # Test imports and instantiation
    imports_ok = await test_imports_and_classes()

    if not imports_ok:
        print("\nERROR: CRITICAL: Import tests failed. Cannot proceed with API tests.")
        return False

    # Run API tests
    results = {}

    # Test 1: Discussion Extraction
    print("\nRUNNING: Starting discussion extraction test...")
    results['discussions'] = await test_discussion_extraction()

    # Test 2: Writeup Extraction
    print("\nRUNNING: Starting writeup extraction test...")
    results['writeups'] = await test_writeup_extraction()

    # Test 3: Notebook Extraction
    print("\nRUNNING: Starting notebook extraction test...")
    results['notebooks'] = await test_notebook_extraction()

    # Final Results
    print("\n" + "="*70)
    print("RESULTS: FINAL TEST RESULTS")
    print("="*70)

    print(f"Dependencies: {'PASS: PASS' if deps_ok else 'FAIL: FAIL'}")
    print(f"Imports: {'PASS: PASS' if imports_ok else 'FAIL: FAIL'}")
    print(f"Feature 1 - Discussions: {'PASS: PASS' if results.get('discussions') else 'FAIL: FAIL'}")
    print(f"Feature 2 - Writeups: {'PASS: PASS' if results.get('writeups') else 'FAIL: FAIL'}")
    print(f"Feature 3 - Notebooks: {'PASS: PASS' if results.get('notebooks') else 'FAIL: FAIL'}")

    total_passed = sum([deps_ok, imports_ok] + list(results.values()))
    total_tests = 5

    print(f"\nOVERALL: {total_passed}/{total_tests} tests passed")

    if total_passed == total_tests:
        print("SUCCESS: ALL TESTS PASSED! The API is working correctly.")
    elif total_passed >= 3:
        print("WARNING:  PARTIAL SUCCESS: Core functionality works, some issues detected.")
    else:
        print("ERROR: MAJOR ISSUES: Multiple critical failures detected.")

    print("\nNOTES: NOTES:")
    print("- Notebook extraction requires Kaggle API authentication")
    print("- Some competitions may not have writeups/notebooks")
    print("- Network issues can cause test failures")

    return total_passed >= 3

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nSTOPPED:  Tests cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nCRASH: Unexpected error: {e}")
        traceback.print_exc()
        sys.exit(1)