"""
Kaggle Discussion Extractor

A professional-grade Python tool for extracting and analyzing discussions from Kaggle competitions.
Features hierarchical reply extraction, pagination support, and clean output formats.
"""

from .core import KaggleDiscussionExtractor, Discussion, Reply, Author
from .cli import main as cli_main

__version__ = "1.0.0"
__author__ = "Kaggle Discussion Extractor Team"
__email__ = "contact@kaggle-extractor.com"

__all__ = [
    "KaggleDiscussionExtractor",
    "Discussion", 
    "Reply",
    "Author",
    "cli_main"
]