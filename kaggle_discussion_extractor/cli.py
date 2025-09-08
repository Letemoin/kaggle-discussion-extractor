#!/usr/bin/env python3
"""
Command Line Interface for Kaggle Discussion Extractor
"""

import argparse
import asyncio
import sys
from pathlib import Path
from .core import KaggleDiscussionExtractor
from .writeup_extractor import KaggleWriteupExtractor
from .notebook_downloader import KaggleNotebookDownloader


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description='Extract discussions from Kaggle competitions with hierarchical reply structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all discussions from a competition
  %(prog)s https://www.kaggle.com/competitions/neurips-2025
  
  # Extract only 10 discussions
  %(prog)s https://www.kaggle.com/competitions/neurips-2025 --limit 10
  
  # Enable development mode for detailed logging
  %(prog)s https://www.kaggle.com/competitions/neurips-2025 --dev-mode
  
  # Run with visible browser (non-headless)
  %(prog)s https://www.kaggle.com/competitions/neurips-2025 --no-headless
  
  # Include date in filename with prefix position
  %(prog)s https://www.kaggle.com/competitions/neurips-2025 --date-format --date-position prefix
  
  # Extract top 10 writeups from private leaderboard
  %(prog)s https://www.kaggle.com/competitions/neurips-2025 --extract-writeups --limit 10
        """
    )
    
    parser.add_argument(
        'competition_url',
        help='URL of the Kaggle competition to extract discussions from'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=None,
        help='Limit the number of discussions to extract (default: extract all)'
    )
    
    parser.add_argument(
        '--dev-mode', '-d',
        action='store_true',
        help='Enable development mode with detailed logging'
    )
    
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help='Run browser in visible mode (not headless)'
    )
    
    parser.add_argument(
        '--date-format',
        action='store_true',
        help='Include YYMMDD date in filename (e.g., 250907)'
    )
    
    parser.add_argument(
        '--date-position',
        choices=['prefix', 'suffix'],
        default='suffix',
        help='Position of date in filename: prefix or suffix (default: suffix)'
    )
    
    parser.add_argument(
        '--extract-writeups',
        action='store_true',
        help='Extract writeups from leaderboard instead of discussions'
    )
    
    parser.add_argument(
        '--leaderboard-tab',
        choices=['private', 'public'],
        default='private',
        help='Leaderboard tab to extract from (default: private)'
    )
    
    parser.add_argument(
        '--download-notebooks',
        action='store_true',
        help='Download and convert notebooks from competition to Python files'
    )
    
    parser.add_argument(
        '--notebooks-input',
        type=str,
        help='Text file with list of notebook URLs (one per line) for batch download'
    )
    
    parser.add_argument(
        '--extraction-attempts',
        type=int,
        default=1,
        help='Number of times to retry URL extraction logic for notebooks (default: 1)'
    )
    
    # Version handled in cli_main() to avoid async issues
    
    return parser


async def main(args):
    """Main CLI function"""
    
    # Validate competition URL
    if not args.competition_url.startswith('https://www.kaggle.com/competitions/'):
        print("Error: Please provide a valid Kaggle competition URL")
        print("Example: https://www.kaggle.com/competitions/neurips-2025")
        sys.exit(1)
    
    # Choose extractor type based on mode
    if args.download_notebooks:
        extractor = KaggleNotebookDownloader(
            dev_mode=args.dev_mode,
            headless=not args.no_headless,
            extraction_attempts=args.extraction_attempts
        )
    elif args.extract_writeups:
        extractor = KaggleWriteupExtractor(
            dev_mode=args.dev_mode,
            headless=not args.no_headless
        )
    else:
        extractor = KaggleDiscussionExtractor(
            dev_mode=args.dev_mode,
            headless=not args.no_headless,
            date_format=args.date_format,
            date_position=args.date_position
        )
    
    print("=" * 60)
    if args.download_notebooks:
        print("Kaggle Notebook Downloader")
    elif args.extract_writeups:
        print("Kaggle Writeup Extractor")
    else:
        print("Kaggle Discussion Extractor")
    print("=" * 60)
    print(f"Competition: {args.competition_url}")
    
    if args.download_notebooks:
        print("Features:")
        print("  - Competition notebook discovery and download")
        print("  - Automatic conversion from .ipynb to .py files") 
        print("  - Custom naming: {title}_{last_updated}.py")
        print("  - Support for batch processing from URL list")
    elif args.extract_writeups:
        print("Features:")
        print("  - Leaderboard scraping for writeup URLs")
        print("  - Automatic writeup discussion extraction")
        print(f"  - Leaderboard tab: {args.leaderboard_tab}")
        print("  - Custom naming: {contest}_{rank}_{team}.md")
        print("  - Rich metadata in extracted files")
    else:
        print("Features:")
        print("  - Hierarchical reply extraction (1, 1.1, 1.2, etc.)")
        print("  - No content duplication between parent/child replies")
        print("  - Pagination support for all discussions")
        print("  - Rich metadata extraction (rankings, badges, upvotes)")
        print("  - Clean markdown output")
    
    if args.dev_mode:
        print("  - Development mode: ENABLED")
    if args.no_headless:
        print("  - Browser mode: VISIBLE")
    if not args.extract_writeups and args.date_format:
        print(f"  - Date format: ENABLED ({args.date_position})")
        
    print()
    
    try:
        # Start extraction
        if args.download_notebooks:
            # Handle notebook download mode
            if args.notebooks_input:
                # Batch mode: read URLs from file
                input_file = Path(args.notebooks_input)
                if not input_file.exists():
                    print(f"Error: File not found: {args.notebooks_input}")
                    sys.exit(1)
                
                with open(input_file, 'r') as f:
                    notebook_urls = [line.strip() for line in f if line.strip()]
                
                print(f"Processing {len(notebook_urls)} notebooks from file...")
                # TODO: Implement batch processing from URL list
                success = True  # Placeholder
            else:
                # Competition mode: extract all notebooks from competition
                success = await extractor.download_competition_notebooks(
                    competition_url=args.competition_url,
                    limit=args.limit
                )
        elif args.extract_writeups:
            success = await extractor.extract_competition_writeups(
                competition_url=args.competition_url,
                limit=args.limit,
                tab=args.leaderboard_tab
            )
        else:
            success = await extractor.extract_competition_discussions(
                competition_url=args.competition_url,
                limit=args.limit
            )
        
        if success:
            print("\n" + "=" * 60)
            if args.download_notebooks:
                print("NOTEBOOK DOWNLOAD COMPLETED SUCCESSFULLY!")
                print("Check the 'kaggle_notebooks_downloaded' directory for results")
            else:
                print("EXTRACTION COMPLETED SUCCESSFULLY!")
                if args.extract_writeups:
                    print("Check the 'writeups_extracted' directory for results")
                else:
                    print("Check the 'kaggle_discussions_extracted' directory for results")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("EXTRACTION FAILED!")
            print("Check the error messages above for details")
            print("=" * 60)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nExtraction cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        if args.dev_mode:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def cli_main():
    """Entry point for console script"""
    # Handle version and help before argparse to avoid async issues
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--version', '-v']:
            print('kaggle-discussion-extractor 1.1.0')
            return
        elif sys.argv[1] in ['--help', '-h']:
            parser = create_parser()
            parser.print_help()
            return
    
    # Parse arguments first in the non-async context
    parser = create_parser()
    
    try:
        args = parser.parse_args()
        # Now run the async main with parsed args
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\nExtraction cancelled by user")
        exit(0)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == '__main__':
    cli_main()