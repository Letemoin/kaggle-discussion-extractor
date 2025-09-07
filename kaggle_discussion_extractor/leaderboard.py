#!/usr/bin/env python3
"""
Leaderboard Scraper for Kaggle Discussion Extractor

Extracts writeup URLs from competition leaderboards and processes them 
using the existing discussion extraction system.
"""

import re
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Page, Browser
from bs4 import BeautifulSoup


@dataclass
class WriteupEntry:
    """Represents a writeup entry from leaderboard"""
    rank: int
    team_name: str
    writeup_url: str
    score: str
    members: List[str]


class KaggleLeaderboardScraper:
    """Scraper for extracting writeup URLs from Kaggle competition leaderboards"""
    
    def __init__(self, dev_mode: bool = False, headless: bool = True):
        self.dev_mode = dev_mode
        self.headless = headless
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the scraper"""
        logger = logging.getLogger(f"{__name__}.KaggleLeaderboardScraper")
        
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

    def _extract_competition_name(self, competition_url: str) -> str:
        """Extract competition name from URL"""
        # Extract competition name from URL like: https://www.kaggle.com/competitions/cmi-detect-behavior-with-sensor-data
        parsed = urlparse(competition_url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) >= 2 and path_parts[0] == 'competitions':
            return path_parts[1]
        else:
            # Fallback: use the last part of the path
            return path_parts[-1] if path_parts else 'unknown-competition'

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for use in filename"""
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[<>:"/\\|?*\s]+', '_', text)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r'_+', '_', sanitized)
        # Remove leading/trailing underscores
        return sanitized.strip('_')

    def _parse_leaderboard_html(self, html: str, base_url: str) -> List[WriteupEntry]:
        """Parse leaderboard HTML to extract writeup entries"""
        self.logger.debug("Parsing leaderboard HTML...")
        
        soup = BeautifulSoup(html, 'html.parser')
        entries = []
        
        # Save HTML for debugging if in dev mode
        if self.dev_mode:
            debug_file = Path("debug_leaderboard.html")
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html)
            self.logger.debug(f"Saved HTML to {debug_file} for debugging")
        
        # Try different parsing strategies
        list_items = []
        
        # Strategy 1: MUI List items
        mui_items = soup.find_all('li', class_='MuiListItem-root')
        if mui_items:
            self.logger.debug(f"Found {len(mui_items)} MUI list items")
            list_items = mui_items
        
        # Strategy 2: Table rows
        if not list_items:
            table_rows = soup.find_all('tr')
            if table_rows:
                self.logger.debug(f"Found {len(table_rows)} table rows")
                list_items = table_rows
        
        # Strategy 3: Any elements with writeup links
        if not list_items:
            elements_with_writeups = soup.find_all(lambda tag: tag.find('a', href=lambda x: x and '/writeups/' in x))
            if elements_with_writeups:
                self.logger.debug(f"Found {len(elements_with_writeups)} elements with writeup links")
                list_items = elements_with_writeups
        
        for i, item in enumerate(list_items):
            try:
                # Skip header row
                if 'aria-label' in item.attrs and 'List Item' in item.attrs.get('aria-label', ''):
                    # Check if this is a data row (not header)
                    rank_spans = item.find_all('span')
                    rank_text = None
                    
                    # Look for rank in various span classes
                    for span in rank_spans:
                        text = span.text.strip()
                        if text.isdigit() and int(text) > 0:
                            rank_text = text
                            break
                    
                    if not rank_text:
                        self.logger.debug(f"Skipping item {i}: no valid rank found")
                        continue
                        
                    rank = int(rank_text)
                    
                    # Extract team name - try multiple strategies
                    team_name = f"Team_{rank}"  # fallback
                    
                    # Strategy 1: Look for team name in specific classes
                    team_spans = item.find_all('span')
                    for span in team_spans:
                        text = span.text.strip()
                        # Skip if it's just a number, medal, or score
                        if text and not text.isdigit() and '.' not in text and len(text) > 2:
                            # Check if it looks like a team name (not a score or medal)
                            if not any(word in text.lower() for word in ['gold', 'silver', 'bronze', 'medal']):
                                team_name = text
                                break
                    
                    # Extract score - look for decimal numbers
                    score = "N/A"
                    score_spans = item.find_all('span')
                    for span in score_spans:
                        text = span.text.strip()
                        # Look for decimal scores (e.g., 0.886193)
                        if '.' in text and text.replace('.', '').isdigit():
                            score = text
                            break
                    
                    # Extract member names (from avatar links)
                    members = []
                    member_links = item.find_all('a')
                    for link in member_links:
                        aria_label = link.get('aria-label', '')
                        if "'s profile" in aria_label:
                            member_name = aria_label.replace("'s profile", '')
                            if member_name:
                                members.append(member_name)
                    
                    # Extract writeup URL from Solution column - most important part!
                    solution_link = item.find('a', href=lambda x: x and '/writeups/' in x)
                    if solution_link:
                        writeup_url = urljoin(base_url, solution_link.get('href'))
                        
                        entry = WriteupEntry(
                            rank=rank,
                            team_name=team_name,
                            writeup_url=writeup_url,
                            score=score,
                            members=members
                        )
                        entries.append(entry)
                        self.logger.info(f"Found writeup: Rank {rank}, Team: {team_name}, URL: {writeup_url}")
                    else:
                        self.logger.debug(f"No writeup link found for rank {rank}, team: {team_name}")
                        
            except Exception as e:
                self.logger.warning(f"Error parsing leaderboard entry {i}: {e}")
                if self.dev_mode:
                    import traceback
                    traceback.print_exc()
                continue
        
        self.logger.info(f"Found {len(entries)} writeup entries from leaderboard")
        return entries

    async def extract_leaderboard_writeups(
        self, 
        competition_url: str, 
        limit: Optional[int] = None,
        tab: str = "private"
    ) -> List[WriteupEntry]:
        """
        Extract writeup URLs from competition leaderboard
        
        Args:
            competition_url: URL of the competition
            limit: Maximum number of writeups to extract
            tab: Leaderboard tab to use ('private' or 'public')
            
        Returns:
            List of WriteupEntry objects
        """
        self.logger.info(f"Extracting writeups from {competition_url} ({tab} leaderboard)")
        
        # Construct leaderboard URL
        base_url = competition_url.rstrip('/')
        leaderboard_url = f"{base_url}/leaderboard?tab={tab}"
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=self.headless)
            
            try:
                page = await browser.new_page()
                
                # Navigate to leaderboard
                self.logger.info(f"Loading leaderboard: {leaderboard_url}")
                await page.goto(leaderboard_url, wait_until="networkidle")
                
                # Wait for leaderboard content to load
                # Try multiple possible selectors for the leaderboard
                selectors_to_try = [
                    '.MuiList-root',
                    '[data-testid="leaderboard-table"]', 
                    '.leaderboard-table',
                    'table',
                    '.km-list',
                    '[role="list"]'
                ]
                
                page_content = None
                for selector in selectors_to_try:
                    try:
                        await page.wait_for_selector(selector, timeout=10000)
                        self.logger.info(f"Found leaderboard with selector: {selector}")
                        page_content = await page.content()
                        break
                    except Exception as e:
                        self.logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                if not page_content:
                    # Fallback: just wait a bit and get content anyway
                    self.logger.warning("No leaderboard selector found, trying fallback...")
                    await page.wait_for_timeout(5000)  # Wait 5 seconds
                    page_content = await page.content()
                
                # Use the content we already got
                html = page_content
                
                # Parse the leaderboard
                entries = self._parse_leaderboard_html(html, competition_url)
                
                # Apply limit if specified
                if limit:
                    entries = entries[:limit]
                    self.logger.info(f"Limited to top {limit} entries")
                
                return entries
                
            except Exception as e:
                self.logger.error(f"Error extracting leaderboard: {e}")
                return []
            finally:
                await browser.close()

    def generate_writeup_filename(
        self, 
        competition_url: str, 
        entry: WriteupEntry
    ) -> str:
        """
        Generate filename for writeup using format: {contest_name}_{solution_rank}_{team_name}.md
        
        Args:
            competition_url: Competition URL
            entry: WriteupEntry object
            
        Returns:
            Generated filename
        """
        contest_name = self._extract_competition_name(competition_url)
        sanitized_contest = self._sanitize_filename(contest_name)
        sanitized_team = self._sanitize_filename(entry.team_name)
        
        filename = f"{sanitized_contest}_{entry.rank:02d}_{sanitized_team}.md"
        self.logger.debug(f"Generated filename: {filename}")
        
        return filename

    async def extract_writeups_from_competition(
        self, 
        competition_url: str,
        limit: Optional[int] = None,
        tab: str = "private",
        output_dir: Optional[str] = None
    ) -> List[Tuple[WriteupEntry, str]]:
        """
        Main method to extract all writeups from a competition leaderboard
        
        Args:
            competition_url: Competition URL
            limit: Maximum number of writeups to extract
            tab: Leaderboard tab ('private' or 'public')
            output_dir: Output directory for writeups
            
        Returns:
            List of (WriteupEntry, filename) tuples
        """
        self.logger.info("="*60)
        self.logger.info("Kaggle Writeup Extractor")
        self.logger.info("="*60)
        self.logger.info(f"Competition: {competition_url}")
        self.logger.info(f"Leaderboard tab: {tab}")
        if limit:
            self.logger.info(f"Limit: {limit}")
        
        # Extract writeup entries from leaderboard
        entries = await self.extract_leaderboard_writeups(competition_url, limit, tab)
        
        if not entries:
            self.logger.warning("No writeup entries found!")
            return []
        
        # Generate filenames for each entry
        results = []
        for entry in entries:
            filename = self.generate_writeup_filename(competition_url, entry)
            results.append((entry, filename))
            
        self.logger.info(f"Ready to extract {len(results)} writeups")
        return results


# Convenience function for CLI usage
async def extract_competition_writeups(
    competition_url: str,
    limit: Optional[int] = None,
    tab: str = "private",
    dev_mode: bool = False,
    headless: bool = True
) -> List[Tuple[WriteupEntry, str]]:
    """
    Convenience function to extract writeups from competition
    
    Args:
        competition_url: Competition URL
        limit: Maximum number of writeups to extract  
        tab: Leaderboard tab ('private' or 'public')
        dev_mode: Enable debug logging
        headless: Run browser in headless mode
        
    Returns:
        List of (WriteupEntry, filename) tuples
    """
    scraper = KaggleLeaderboardScraper(dev_mode=dev_mode, headless=headless)
    return await scraper.extract_writeups_from_competition(
        competition_url=competition_url,
        limit=limit,
        tab=tab
    )