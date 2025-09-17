#!/usr/bin/env python3
"""
Setup script for Kaggle Discussion Extractor
"""

import os
from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define requirements directly
requirements = [
    "playwright>=1.40.0",
    "nbformat>=5.9.0",
    "nbconvert>=7.8.0",
]

setup(
    name="kaggle-discussion-extractor",
    version="1.0.17",
    author="Kaggle Discussion Extractor Contributors",
    author_email="contact@kaggle-extractor.com",
    description="Professional tool for extracting Kaggle competition discussions and writeups with leaderboard integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Letemoin/kaggle-discussion-extractor",
    project_urls={
        "Bug Tracker": "https://github.com/Letemoin/kaggle-discussion-extractor/issues",
        "Documentation": "https://github.com/Letemoin/kaggle-discussion-extractor#readme",
        "Source Code": "https://github.com/Letemoin/kaggle-discussion-extractor",
        "Changelog": "https://github.com/Letemoin/kaggle-discussion-extractor/blob/master/CHANGELOG.md",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Data Scientists",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0.0",
            "isort>=5.0.0",
            "flake8>=3.8.0",
            "mypy>=0.800",
        ],
    },
    entry_points={
        "console_scripts": [
            "kaggle-discussion-extractor=kaggle_discussion_extractor.cli:cli_main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="kaggle, discussion, extractor, web-scraping, competition, data-analysis, hierarchy, replies",
)