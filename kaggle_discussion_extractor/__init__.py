"""
Kaggle Discussion Extractor

A professional-grade Python tool for extracting and analyzing discussions from Kaggle competitions.
Features hierarchical reply extraction, pagination support, and clean output formats.
"""

from .core import KaggleDiscussionExtractor, Discussion, Reply, Author
from .leaderboard import KaggleLeaderboardScraper, WriteupEntry
from .writeup_extractor import KaggleWriteupExtractor
from .notebook_downloader import KaggleNotebookDownloader, NotebookInfo
from .cli import cli_main

__version__ = "1.1.0"
__author__ = "Kaggle Discussion Extractor Team"
__email__ = "contact@kaggle-extractor.com"

__all__ = [
    "KaggleDiscussionExtractor",
    "KaggleLeaderboardScraper",
    "KaggleWriteupExtractor",
    "KaggleNotebookDownloader",
    "Discussion", 
    "Reply",
    "Author",
    "WriteupEntry",
    "NotebookInfo",
    "cli_main"
]