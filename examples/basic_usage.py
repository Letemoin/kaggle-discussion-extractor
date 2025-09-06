#!/usr/bin/env python3
"""
Basic usage examples for Kaggle Discussion Extractor
"""

import asyncio
import logging
from kaggle_discussion_extractor import KaggleDiscussionExtractor

# Setup logging to see the progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def basic_example():
    """
    Basic example: Extract discussions from a competition
    """
    logger.info("=== Basic Example ===")
    
    # Initialize extractor
    extractor = KaggleDiscussionExtractor()
    
    # Extract discussions (limit to 5 for demonstration)
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025",
        limit=5
    )
    
    if success:
        logger.info("✅ Basic extraction completed successfully!")
    else:
        logger.error("❌ Basic extraction failed!")


async def dev_mode_example():
    """
    Development mode example: Extract with detailed logging
    """
    logger.info("=== Development Mode Example ===")
    
    # Initialize extractor with development mode enabled
    extractor = KaggleDiscussionExtractor(
        dev_mode=True,  # Enable detailed logging
        headless=True   # Keep headless for automation
    )
    
    # Extract discussions with detailed logging
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025",
        limit=3  # Small number for demo
    )
    
    if success:
        logger.info("✅ Development mode extraction completed!")
    else:
        logger.error("❌ Development mode extraction failed!")


async def visible_browser_example():
    """
    Visible browser example: Useful for debugging and seeing what happens
    """
    logger.info("=== Visible Browser Example ===")
    
    # Initialize extractor with visible browser
    extractor = KaggleDiscussionExtractor(
        dev_mode=True,   # Enable detailed logging
        headless=False   # Show browser window
    )
    
    logger.info("Browser will open in visible mode - you can watch the extraction process!")
    
    # Extract a small number of discussions
    success = await extractor.extract_competition_discussions(
        competition_url="https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025",
        limit=2  # Very small number for demo
    )
    
    if success:
        logger.info("✅ Visible browser extraction completed!")
    else:
        logger.error("❌ Visible browser extraction failed!")


async def main():
    """
    Run all examples
    """
    print("Kaggle Discussion Extractor - Usage Examples")
    print("=" * 50)
    
    try:
        # Example 1: Basic usage
        await basic_example()
        print()
        
        # Example 2: Development mode
        await dev_mode_example()
        print()
        
        # Example 3: Visible browser (uncomment if you want to see it)
        # await visible_browser_example()
        # print()
        
        print("=" * 50)
        print("All examples completed!")
        print("Check the 'kaggle_discussions_extracted' directory for results")
        
    except Exception as e:
        logger.error(f"Error running examples: {e}")


if __name__ == "__main__":
    # Run the examples
    asyncio.run(main())