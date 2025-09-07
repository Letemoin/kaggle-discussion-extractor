#!/usr/bin/env python3
"""
Writeup Extractor - Combines leaderboard scraping with discussion extraction

This module provides the complete workflow for extracting competition writeups:
1. Scrape leaderboard for writeup URLs
2. Extract writeups using existing discussion extractor
3. Save with proper naming convention
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple
from datetime import datetime

from .leaderboard import KaggleLeaderboardScraper, WriteupEntry
from .core import KaggleDiscussionExtractor


class KaggleWriteupExtractor:
    """Combined extractor for competition writeups from leaderboards"""
    
    def __init__(self, dev_mode: bool = False, headless: bool = True):
        self.dev_mode = dev_mode
        self.headless = headless
        self.logger = self._setup_logger()
        
        # Initialize sub-components
        self.leaderboard_scraper = KaggleLeaderboardScraper(
            dev_mode=dev_mode, 
            headless=headless
        )
        self.discussion_extractor = KaggleDiscussionExtractor(
            dev_mode=dev_mode, 
            headless=headless
        )
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the writeup extractor"""
        logger = logging.getLogger(f"{__name__}.KaggleWriteupExtractor")
        
        if self.dev_mode:
            logger.setLevel(logging.DEBUG)
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '[%(levelname)s] %(name)s: %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        else:
            logger.setLevel(logging.INFO)
            
        return logger

    async def extract_competition_writeups(
        self,
        competition_url: str,
        limit: Optional[int] = None,
        tab: str = "private",
        output_dir: Optional[str] = None
    ) -> bool:
        """
        Main method to extract writeups from a competition
        
        Args:
            competition_url: URL of the Kaggle competition
            limit: Maximum number of writeups to extract (None for all)
            tab: Leaderboard tab to use ('private' or 'public')  
            output_dir: Custom output directory (default: writeups_extracted)
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("="*60)
        self.logger.info("Kaggle Writeup Extractor")
        self.logger.info("="*60)
        self.logger.info(f"Competition: {competition_url}")
        self.logger.info(f"Leaderboard tab: {tab}")
        if limit:
            self.logger.info(f"Limit: top {limit} entries")
        
        # Setup output directory
        if not output_dir:
            output_dir = "writeups_extracted"
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        try:
            # Step 1: Extract writeup entries from leaderboard
            self.logger.info("\n[STEP 1] Extracting writeup URLs from leaderboard...")
            writeup_entries = await self.leaderboard_scraper.extract_leaderboard_writeups(
                competition_url=competition_url,
                limit=limit,
                tab=tab
            )
            
            if not writeup_entries:
                self.logger.error("No writeup entries found in leaderboard!")
                return False
                
            self.logger.info(f"Found {len(writeup_entries)} writeup entries")
            
            # Step 2: Extract each writeup discussion
            self.logger.info("\n[STEP 2] Extracting writeup discussions...")
            
            successful_extractions = 0
            failed_extractions = 0
            
            for i, entry in enumerate(writeup_entries, 1):
                self.logger.info(f"\n[{i}/{len(writeup_entries)}] Processing writeup...")
                self.logger.info(f"   Rank: {entry.rank}")
                self.logger.info(f"   Team: {entry.team_name}")
                self.logger.info(f"   URL: {entry.writeup_url}")
                
                try:
                    # Extract the discussion using existing extractor
                    discussion = await self.discussion_extractor.extract_single_discussion_from_url(
                        entry.writeup_url
                    )
                    
                    if discussion:
                        # Generate custom filename
                        filename = self.leaderboard_scraper.generate_writeup_filename(
                            competition_url, entry
                        )
                        output_file = output_path / filename
                        
                        # Save with custom discussion extractor
                        self.discussion_extractor.save_discussion_markdown(discussion, output_file)
                        
                        successful_extractions += 1
                        self.logger.info(f"   [SUCCESS] Saved as: {filename}")
                        
                        # Add metadata comment to the file
                        self._add_metadata_to_writeup(output_file, entry)
                        
                        # Respectful delay
                        await asyncio.sleep(2)
                        
                    else:
                        self.logger.warning(f"   [FAILED] Could not extract writeup")
                        failed_extractions += 1
                        
                except Exception as e:
                    self.logger.error(f"   [ERROR] {e}")
                    failed_extractions += 1
                    continue
            
            # Summary
            self.logger.info("\n" + "="*60)
            self.logger.info("EXTRACTION SUMMARY")
            self.logger.info("="*60)
            self.logger.info(f"Successfully extracted: {successful_extractions}")
            self.logger.info(f"Failed extractions: {failed_extractions}")
            self.logger.info(f"Output directory: {output_path.absolute()}")
            
            return successful_extractions > 0
            
        except Exception as e:
            self.logger.error(f"Critical error during writeup extraction: {e}")
            if self.dev_mode:
                import traceback
                traceback.print_exc()
            return False

    def _add_metadata_to_writeup(self, output_file: Path, entry: WriteupEntry):
        """Add metadata header to the writeup file"""
        try:
            # Read existing content
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create metadata header
            metadata = f"""<!-- Writeup Metadata
Competition Rank: {entry.rank}
Team: {entry.team_name}
Score: {entry.score}
Members: {', '.join(entry.members) if entry.members else 'N/A'}
Original URL: {entry.writeup_url}
Extracted: {datetime.now().isoformat()}
-->

"""
            
            # Prepend metadata to content
            new_content = metadata + content
            
            # Write back to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            self.logger.debug(f"Added metadata to {output_file.name}")
            
        except Exception as e:
            self.logger.warning(f"Could not add metadata to {output_file.name}: {e}")

    async def extract_single_writeup_from_url(self, writeup_url: str) -> Optional[object]:
        """
        Extract a single writeup from URL using the discussion extractor
        
        Args:
            writeup_url: Direct URL to the writeup
            
        Returns:
            Discussion object or None if failed
        """
        return await self.discussion_extractor.extract_single_discussion_from_url(writeup_url)


# Add method to existing KaggleDiscussionExtractor to handle single URL extraction
async def extract_single_discussion_from_url_method(self, url: str):
    """
    Extract a single discussion from a direct URL
    This method is added to the existing KaggleDiscussionExtractor
    """
    from playwright.async_api import async_playwright
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=self.headless)
        
        try:
            page = await browser.new_page()
            return await self.extract_single_discussion(page, url)
        finally:
            await browser.close()


# Monkey patch the method into KaggleDiscussionExtractor
KaggleDiscussionExtractor.extract_single_discussion_from_url = extract_single_discussion_from_url_method


# Convenience function for CLI usage
async def extract_competition_writeups(
    competition_url: str,
    limit: Optional[int] = None,
    tab: str = "private", 
    output_dir: Optional[str] = None,
    dev_mode: bool = False,
    headless: bool = True
) -> bool:
    """
    Convenience function to extract writeups from competition
    
    Args:
        competition_url: Competition URL
        limit: Maximum number of writeups to extract
        tab: Leaderboard tab ('private' or 'public')
        output_dir: Output directory
        dev_mode: Enable debug logging
        headless: Run browser in headless mode
        
    Returns:
        True if successful, False otherwise
    """
    extractor = KaggleWriteupExtractor(dev_mode=dev_mode, headless=headless)
    return await extractor.extract_competition_writeups(
        competition_url=competition_url,
        limit=limit,
        tab=tab,
        output_dir=output_dir
    )