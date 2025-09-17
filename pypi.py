#!/usr/bin/env python3
"""
Simple PyPI Package Builder
Just builds the package without uploading
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime

class SimplePackageBuilder:
    """Simple package builder"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.setup_py = self.project_root / "setup.py"
        self.pyproject_toml = self.project_root / "pyproject.toml"

    def get_current_version(self) -> str:
        """Extract current version from setup.py"""
        with open(self.setup_py, 'r') as f:
            content = f.read()
            match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        raise ValueError("Could not find version in setup.py")

    def bump_version(self, current_version: str) -> str:
        """Bump patch version"""
        parts = current_version.split('.')

        if len(parts) == 2:
            major, minor = map(int, parts)
            patch = 0
        elif len(parts) == 3:
            major, minor, patch = map(int, parts)
        else:
            raise ValueError(f"Invalid version format: {current_version}")

        return f"{major}.{minor}.{patch + 1}"

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

        print(f"Updated version to {new_version}")

    def run_command(self, cmd: list, description: str):
        """Run a command and handle errors"""
        print(f"Running: {description}...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=self.project_root)
            print(f"PASS: {description}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"FAIL: {description}")
            print(f"Error: {e.stderr}")
            return None

    def clean_build_artifacts(self):
        """Clean previous build artifacts"""
        import shutil

        dirs_to_clean = ['build', 'dist']
        for dir_name in dirs_to_clean:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)
                print(f"Cleaned {dir_name}/")

        # Clean egg-info
        for egg_info in self.project_root.glob("*.egg-info"):
            if egg_info.is_dir():
                shutil.rmtree(egg_info)
                print(f"Cleaned {egg_info.name}")

    def build_package(self):
        """Build the package"""
        result = self.run_command(['python', '-m', 'build'], "Building package")
        return result is not None

    def check_package(self):
        """Check package with twine if available"""
        result = self.run_command(['twine', 'check', 'dist/*'], "Checking package")
        return result is not None

    def build(self):
        """Main build workflow"""
        print("Simple Package Builder")
        print("=" * 30)

        # Get current version and bump it
        current_version = self.get_current_version()
        print(f"Current version: {current_version}")

        new_version = self.bump_version(current_version)
        print(f"New version: {new_version}")

        # Update version files
        self.update_version_files(new_version)

        # Clean and build
        self.clean_build_artifacts()

        if self.build_package():
            print(f"\nSUCCESS: Package {new_version} built successfully!")
            print("Files created:")
            dist_dir = self.project_root / "dist"
            if dist_dir.exists():
                for file in dist_dir.iterdir():
                    print(f"  - {file.name}")

            # Try to check package if twine is available
            self.check_package()

            print(f"\nTo upload to PyPI manually:")
            print(f"  twine upload dist/*")
        else:
            print("FAIL: Build failed")
            return False

        return True

def main():
    builder = SimplePackageBuilder()
    success = builder.build()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()