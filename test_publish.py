#!/usr/bin/env python3
"""
Test script for PyPI publishing workflow

This script validates the publishing setup without actually publishing.
"""

import sys
import subprocess
from pathlib import Path

def test_import():
    """Test that the package can be imported"""
    try:
        import kaggle_discussion_extractor
        print("PASS: Package imports successfully")
        print(f"Package location: {kaggle_discussion_extractor.__file__}")
        return True
    except ImportError as e:
        print(f"FAIL: Import failed: {e}")
        return False

def test_cli_entry_point():
    """Test CLI entry point"""
    try:
        result = subprocess.run([
            sys.executable, '-c',
            'from kaggle_discussion_extractor.cli import cli_main; print("CLI entry point works")'
        ], capture_output=True, text=True, check=True)
        print("PASS: CLI entry point accessible")
        return True
    except subprocess.CalledProcessError as e:
        print(f"FAIL: CLI entry point failed: {e}")
        return False

def test_build_system():
    """Test build system without building"""
    try:
        # Check if build files are present
        project_root = Path(__file__).parent
        setup_py = project_root / "setup.py"
        pyproject_toml = project_root / "pyproject.toml"

        if not setup_py.exists():
            print("FAIL: setup.py not found")
            return False

        if not pyproject_toml.exists():
            print("FAIL: pyproject.toml not found")
            return False

        print("PASS: Build configuration files present")
        return True
    except Exception as e:
        print(f"FAIL: Build system check failed: {e}")
        return False

def test_version_consistency():
    """Test version consistency between files"""
    try:
        project_root = Path(__file__).parent

        # Get version from setup.py
        setup_py = project_root / "setup.py"
        with open(setup_py, 'r') as f:
            setup_content = f.read()

        import re
        setup_version = re.search(r'version\s*=\s*["\']([^"\']+)["\']', setup_content)
        setup_version = setup_version.group(1) if setup_version else None

        # Get version from pyproject.toml
        pyproject_toml = project_root / "pyproject.toml"
        with open(pyproject_toml, 'r') as f:
            pyproject_content = f.read()

        pyproject_version = re.search(r'version\s*=\s*["\']([^"\']+)["\']', pyproject_content)
        pyproject_version = pyproject_version.group(1) if pyproject_version else None

        if setup_version and pyproject_version and setup_version == pyproject_version:
            print(f"PASS: Version consistency: {setup_version}")
            return True
        else:
            print(f"FAIL: Version mismatch: setup.py={setup_version}, pyproject.toml={pyproject_version}")
            return False

    except Exception as e:
        print(f"FAIL: Version check failed: {e}")
        return False

def test_dependencies():
    """Test that required dependencies are available"""
    try:
        import playwright
        print("PASS: Playwright dependency available")
        return True
    except ImportError:
        print("FAIL: Playwright dependency missing")
        return False

def main():
    """Run all tests"""
    print("Testing PyPI publishing setup")
    print("=" * 40)

    tests = [
        ("Package Import", test_import),
        ("CLI Entry Point", test_cli_entry_point),
        ("Build System", test_build_system),
        ("Version Consistency", test_version_consistency),
        ("Dependencies", test_dependencies),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        if test_func():
            passed += 1

    print(f"\nTest Results: {passed}/{total} passed")

    if passed == total:
        print("All tests passed! Publishing setup is ready.")
        print("\nUsage examples:")
        print("  python publish_pypi.py --version patch --test    # Test PyPI")
        print("  python publish_pypi.py --version minor           # Production PyPI")
        return True
    else:
        print("Some tests failed. Fix issues before publishing.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)