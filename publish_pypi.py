#!/usr/bin/env python3
"""
PyPI Publishing Script for Kaggle Discussion Extractor

This script handles:
1. Version management and bumping
2. Building the package
3. Publishing to PyPI (test and production)
4. Git tagging and changelog updates

Usage:
    python publish_pypi.py --version patch --test     # Publish to test PyPI
    python publish_pypi.py --version minor            # Publish to production PyPI
    python publish_pypi.py --version 1.2.0            # Specific version
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

class PyPIPublisher:
    """Handles PyPI publishing workflow"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.setup_py = self.project_root / "setup.py"
        self.pyproject_toml = self.project_root / "pyproject.toml"
        self.changelog = self.project_root / "CHANGELOG.md"

    def get_current_version(self) -> str:
        """Extract current version from setup.py"""
        with open(self.setup_py, 'r') as f:
            content = f.read()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        raise ValueError("Could not find version in setup.py")

    def bump_version(self, current_version: str, bump_type: str) -> str:
        """Bump version based on type (major, minor, patch)"""
        parts = current_version.split('.')

        # Handle 2-part or 3-part versions
        if len(parts) == 2:
            major, minor = map(int, parts)
            patch = 0
        elif len(parts) == 3:
            major, minor, patch = map(int, parts)
        else:
            raise ValueError(f"Invalid version format: {current_version}")

        if bump_type == 'major':
            return f"{major + 1}.0.0"
        elif bump_type == 'minor':
            return f"{major}.{minor + 1}.0"
        elif bump_type == 'patch':
            return f"{major}.{minor}.{patch + 1}"
        else:
            # Assume it's a specific version
            return bump_type

    def update_version_files(self, new_version: str):
        """Update version in setup.py and pyproject.toml"""
        # Update setup.py
        with open(self.setup_py, 'r') as f:
            content = f.read()

        content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version="{new_version}"',
            content
        )

        with open(self.setup_py, 'w') as f:
            f.write(content)

        # Update pyproject.toml
        with open(self.pyproject_toml, 'r') as f:
            content = f.read()

        content = re.sub(
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content
        )

        with open(self.pyproject_toml, 'w') as f:
            f.write(content)

        print(f"Updated version to {new_version} in setup.py and pyproject.toml")

    def update_changelog(self, version: str, changes: list = None):
        """Update CHANGELOG.md with new version"""
        if not self.changelog.exists():
            # Create initial changelog
            changelog_content = "# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"
        else:
            with open(self.changelog, 'r') as f:
                changelog_content = f.read()

        # Add new version entry
        date = datetime.now().strftime('%Y-%m-%d')
        new_entry = f"## [{version}] - {date}\n\n"

        if changes:
            for change in changes:
                new_entry += f"- {change}\n"
        else:
            new_entry += "- Fixed leaderboard extraction with proper team detection\n"
            new_entry += "- Enhanced hierarchical comment structure\n"
            new_entry += "- Added complete content preservation\n"
            new_entry += "- Improved writeup extraction with multiple output formats\n"

        new_entry += "\n"

        # Insert after the header
        lines = changelog_content.split('\n')
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith('## ['):
                header_end = i
                break
            elif i > 10:  # Safety limit
                header_end = len(lines)
                break

        if header_end == 0:
            header_end = len(lines)

        lines.insert(header_end, new_entry)

        with open(self.changelog, 'w') as f:
            f.write('\n'.join(lines))

        print(f"Updated CHANGELOG.md with version {version}")

    def run_command(self, cmd: list, description: str):
        """Run a command and handle errors"""
        print(f"Running: {description}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=self.project_root)
            print(f"PASS: {description} completed")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"FAIL: {description} failed:")
            print(f"Error: {e.stderr}")
            sys.exit(1)

    def clean_build_artifacts(self):
        """Clean previous build artifacts"""
        dirs_to_clean = ['build', 'dist', '*.egg-info']
        for dir_pattern in dirs_to_clean:
            self.run_command(['rm', '-rf'] + list(self.project_root.glob(dir_pattern)),
                           f"Cleaning {dir_pattern}")

    def build_package(self):
        """Build the package"""
        self.run_command(['python', '-m', 'build'], "Building package")

    def check_package(self):
        """Check package with twine"""
        self.run_command(['twine', 'check', 'dist/*'], "Checking package")

    def publish_to_test_pypi(self):
        """Publish to Test PyPI"""
        self.run_command([
            'twine', 'upload', '--repository', 'testpypi', 'dist/*'
        ], "Publishing to Test PyPI")

    def publish_to_pypi(self):
        """Publish to production PyPI"""
        self.run_command(['twine', 'upload', 'dist/*'], "Publishing to PyPI")

    def create_git_tag(self, version: str):
        """Create git tag for the version"""
        tag_name = f"v{version}"
        self.run_command(['git', 'add', '.'], "Staging changes")
        self.run_command([
            'git', 'commit', '-m', f"Release {version}: Enhanced leaderboard extraction and writeup support"
        ], "Committing version changes")
        self.run_command(['git', 'tag', '-a', tag_name, '-m', f"Release {version}"], f"Creating tag {tag_name}")
        print(f"Created git tag {tag_name}")

    def push_changes(self):
        """Push changes and tags to remote"""
        self.run_command(['git', 'push', 'origin', 'master'], "Pushing changes")
        self.run_command(['git', 'push', 'origin', '--tags'], "Pushing tags")

    def verify_dependencies(self):
        """Verify required tools are installed"""
        required_tools = ['build', 'twine']
        missing_tools = []

        for tool in required_tools:
            try:
                subprocess.run([sys.executable, '-m', tool, '--help'],
                             capture_output=True, check=True)
            except subprocess.CalledProcessError:
                missing_tools.append(tool)

        if missing_tools:
            print(f"FAIL: Missing required tools: {', '.join(missing_tools)}")
            print("Install them with:")
            print(f"pip install {' '.join(missing_tools)}")
            sys.exit(1)

        print("PASS: All required tools are available")

    def publish(self, version_bump: str, test_only: bool = False, skip_git: bool = False):
        """Main publishing workflow"""
        print("Starting PyPI publishing workflow")
        print("=" * 50)

        # Verify dependencies
        self.verify_dependencies()

        # Get current version and calculate new version
        current_version = self.get_current_version()
        print(f"Current version: {current_version}")

        new_version = self.bump_version(current_version, version_bump)
        print(f"New version: {new_version}")

        # Update version files
        self.update_version_files(new_version)

        # Update changelog
        self.update_changelog(new_version)

        # Clean and build
        self.clean_build_artifacts()
        self.build_package()
        self.check_package()

        # Publish
        if test_only:
            print("Publishing to Test PyPI only")
            self.publish_to_test_pypi()
            print(f"Successfully published to Test PyPI!")
            print(f"Test it: pip install -i https://test.pypi.org/simple/ kaggle-discussion-extractor=={new_version}")
        else:
            print("Publishing to production PyPI")
            self.publish_to_pypi()
            print(f"Successfully published to PyPI!")
            print(f"Install: pip install kaggle-discussion-extractor=={new_version}")

        # Git operations
        if not skip_git:
            self.create_git_tag(new_version)

            if not test_only:
                self.push_changes()
                print(f"Pushed changes and tags to remote")

        print("\nPublishing workflow completed successfully!")
        print(f"Version {new_version} is now available")

def main():
    # Simple defaults - patch version bump to production PyPI
    publisher = PyPIPublisher()
    publisher.publish(
        version_bump='patch',
        test_only=False,
        skip_git=False
    )

if __name__ == "__main__":
    main()