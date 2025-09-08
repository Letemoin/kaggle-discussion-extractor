#!/usr/bin/env python3
"""
Kaggle Notebook Downloader and Converter
Downloads notebooks from Kaggle competitions and converts them to Python files
"""

import sys
import asyncio
import json
import re
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin

# Setup logging
logger = logging.getLogger(__name__)

# Check for dependencies
try:
    from playwright.async_api import async_playwright, Page
    import nbformat
    from nbconvert import PythonExporter
except ImportError as e:
    logger.error(f"Missing dependencies: {e}. Please run: pip install playwright nbformat nbconvert")
    sys.exit(1)


@dataclass
class NotebookInfo:
    """Information about a Kaggle notebook"""
    title: str
    url: str
    author: str
    last_updated: str
    votes: int = 0
    comments: int = 0
    filename: str = ""


class KaggleNotebookDownloader:
    """Downloads and converts Kaggle notebooks to Python files"""
    
    def __init__(self, dev_mode: bool = False, headless: bool = True, extraction_attempts: int = 1):
        """
        Initialize the notebook downloader
        
        Args:
            dev_mode: Enable development mode with detailed logging
            headless: Run browser in headless mode
            extraction_attempts: Number of times to retry URL extraction logic (default: 1)
        """
        self.dev_mode = dev_mode
        self.headless = headless
        self.extraction_attempts = max(1, extraction_attempts)  # Ensure at least 1 attempt
        
        # Setup logging based on mode
        log_level = logging.DEBUG if dev_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if dev_mode:
            logger.info("Development mode enabled - detailed logging active")

    async def extract_notebook_list(self, competition_url: str, limit: Optional[int] = None) -> List[NotebookInfo]:
        """
        Extract notebook list from competition using Kaggle API (primary) or web scraping (fallback)
        
        Args:
            competition_url: Competition URL (e.g., https://www.kaggle.com/competitions/neurips-2025)
            limit: Maximum number of notebooks to extract
            
        Returns:
            List of NotebookInfo objects
        """
        # First try Kaggle API (more reliable)
        try:
            api_notebooks = await self._extract_via_kaggle_api(competition_url, limit)
            if api_notebooks:
                logger.info(f"Found {len(api_notebooks)} notebooks via Kaggle API")
                return api_notebooks
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Kaggle API failed, falling back to web scraping: {e}")
        
        # Fallback to web scraping
        return await self._extract_via_web_scraping(competition_url, limit)

    async def _extract_via_kaggle_api(self, competition_url: str, limit: Optional[int] = None) -> List[NotebookInfo]:
        """Extract notebooks using Kaggle API"""
        try:
            # Extract competition slug from URL
            competition_slug = competition_url.rstrip('/').split('/')[-1]
            
            import subprocess
            import csv
            import io
            
            # Use Kaggle CLI to list kernels
            page_size = min(limit or 200, 200)  # Max 200 per API
            cmd = [
                'kaggle', 'kernels', 'list',
                '--competition', competition_slug,
                '--page-size', str(page_size),
                '--csv'
            ]
            
            if self.dev_mode:
                logger.debug(f"Running Kaggle API command: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                raise Exception(f"Kaggle API error: {result.stderr}")
            
            # Parse CSV output
            csv_reader = csv.DictReader(io.StringIO(result.stdout))
            notebooks = []
            
            for i, row in enumerate(csv_reader):
                if limit and i >= limit:
                    break
                    
                # Extract data from API response
                ref = row.get('ref', '')
                title = row.get('title', 'Unknown Title')
                author = row.get('author', 'Unknown Author')
                last_run = row.get('lastRunTime', '')
                votes = int(row.get('totalVotes', 0))
                
                # Build notebook URL
                notebook_url = f"https://www.kaggle.com/code/{ref}"
                
                # Generate filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                filename = f"{safe_title}_{datetime.now().strftime('%y%m%d')}.py"
                
                notebook = NotebookInfo(
                    title=title,
                    url=notebook_url,
                    author=author,
                    last_updated=datetime.now().strftime("%y%m%d"),
                    votes=votes,
                    filename=filename
                )
                
                notebooks.append(notebook)
                
                if self.dev_mode:
                    logger.debug(f"Found notebook via API: {title} by {author}")
            
            return notebooks
            
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Kaggle API extraction failed: {e}")
            raise e

    async def _extract_via_web_scraping(self, competition_url: str, limit: Optional[int] = None) -> List[NotebookInfo]:
        """Extract notebooks using web scraping (fallback method)"""
        # Ensure URL ends with /code
        if not competition_url.endswith('/code'):
            competition_url = competition_url.rstrip('/') + '/code'
        
        logger.info(f"Extracting notebooks from: {competition_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # Load competition code page
                await page.goto(competition_url, wait_until="domcontentloaded")
                await asyncio.sleep(5)  # Increased wait for initial load
                
                # Handle lazy loading with infinite scroll - try multiple times if configured
                best_notebooks = []
                for attempt in range(self.extraction_attempts):
                    if self.dev_mode and self.extraction_attempts > 1:
                        logger.debug(f"URL extraction attempt {attempt + 1}/{self.extraction_attempts}")
                    
                    try:
                        await self._handle_lazy_loading(page, limit or 50)
                    except Exception as e:
                        if self.dev_mode:
                            logger.warning(f"Error during page loading attempt {attempt + 1}: {e}")
                    
                    # Extract notebook links and metadata for this attempt
                    attempt_notebooks = await self._extract_notebooks_from_page(page, limit)
                    
                    if len(attempt_notebooks) > len(best_notebooks):
                        best_notebooks = attempt_notebooks
                        if self.dev_mode and self.extraction_attempts > 1:
                            logger.debug(f"Attempt {attempt + 1} found {len(attempt_notebooks)} notebooks (new best)")
                    
                    # If we have multiple attempts, wait between them and refresh containers
                    if attempt < self.extraction_attempts - 1:
                        await asyncio.sleep(3)  # Wait before next attempt
                        # Small scroll to refresh any lazy loading state
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.1);")
                        await asyncio.sleep(2)
                
                return best_notebooks
                
            finally:
                await browser.close()

    async def _extract_notebooks_from_page(self, page: Page, limit: Optional[int] = None) -> List[NotebookInfo]:
        """Extract notebook information from the current page state"""
        notebooks = []
        
        # Try multiple strategies to find notebook containers
        notebook_containers = []
        
        # Strategy 1: Look for specific notebook containers
        containers_1 = await page.query_selector_all('div[data-testid*="code"], .code-card, .notebook-card, [class*="code-list"]')
        notebook_containers.extend(containers_1)
        
        # Strategy 2: Look for general containers that might hold notebooks
        containers_2 = await page.query_selector_all('[class*="DatasetItem"], [class*="CodeItem"], [class*="KernelItem"]')
        notebook_containers.extend(containers_2)
        
        # Strategy 3: Look for list items or article elements that might contain notebooks
        containers_3 = await page.query_selector_all('li, article, .item, [class*="list-item"]')
        notebook_containers.extend(containers_3)
        
        # Strategy 4: Fallback to all links containing /code/
        if not notebook_containers:
            notebook_containers = await page.query_selector_all('a[href*="/code/"]')
        
        # Simple deduplication by removing None/invalid containers
        notebook_containers = [c for c in notebook_containers if c is not None]
        
        if self.dev_mode:
            logger.debug(f"Found {len(notebook_containers)} unique containers after deduplication")
        
        # Filter out comment links and get only actual notebook links
        notebook_elements = []
        for container in notebook_containers:
            try:
                # Check if this is already a link or contains links
                tag_name = await container.evaluate('el => el.tagName.toLowerCase()')
                
                if tag_name == 'a':
                    # This container is already a link
                    links = [container]
                else:
                    # Look for actual notebook links within containers
                    links = await container.query_selector_all('a[href*="/code/"]')
                
                for link in links:
                    href = await link.get_attribute('href')
                    if self.dev_mode:
                        logger.debug(f"Checking link: {href}")
                    
                    if href and '/code/' in href and '?scriptVersionId' not in href:
                        # Convert comment URLs to main notebook URLs
                        if href.endswith('/comments'):
                            href = href.replace('/comments', '')
                            # Update the link's href for consistency
                            try:
                                await link.evaluate(f'el => el.setAttribute("href", "{href}")')
                            except:
                                pass
                        
                        notebook_elements.append(link)
                        if self.dev_mode:
                            logger.debug(f"✓ Added notebook link: {href}")
                    elif href and self.dev_mode:
                        logger.debug(f"✗ Filtered out: {href}")
            except Exception as e:
                if self.dev_mode:
                    logger.warning(f"Error processing container: {e}")
                continue
        
        if self.dev_mode:
            logger.debug(f"Found {len(notebook_elements)} potential notebook elements")
        
        # Process each notebook element with enhanced duplicate filtering
        seen_urls = set()
        for element in notebook_elements:
            try:
                # Extract URL
                href = await element.get_attribute('href')
                if not href or '/code/' not in href:
                    continue
                
                # Make absolute URL
                notebook_url = urljoin('https://www.kaggle.com', href)
                
                # Skip duplicates
                if notebook_url in seen_urls:
                    continue
                seen_urls.add(notebook_url)
                
                # Extract metadata from the element or its parent
                title = await self._extract_notebook_title(element, page)
                author = await self._extract_notebook_author(element)
                last_updated = await self._extract_last_updated(element)
                votes = await self._extract_votes(element)
                
                # Generate safe filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                filename = f"{safe_title}_{last_updated}.py"
                
                notebook = NotebookInfo(
                    title=title,
                    url=notebook_url,
                    author=author,
                    last_updated=last_updated,
                    votes=votes,
                    filename=filename
                )
                
                notebooks.append(notebook)
                
                if self.dev_mode:
                    logger.debug(f"Found notebook: {title} by {author}")
                
                # Apply limit
                if limit and len(notebooks) >= limit:
                    break
                    
            except Exception as e:
                if self.dev_mode:
                    logger.warning(f"Error processing notebook element: {e}")
                continue
        
        logger.info(f"Found {len(notebooks)} notebooks")
        return notebooks

    async def _handle_lazy_loading(self, page, target_limit):
        """Handle infinite scroll lazy loading to extract all possible notebooks"""
        try:
            previous_notebook_count = 0
            consecutive_no_change = 0
            max_scrolls = 50  # Maximum scroll attempts
            scroll_attempts = 0
            
            if self.dev_mode:
                logger.debug(f"Starting lazy loading to find up to {target_limit} notebooks")
            
            while scroll_attempts < max_scrolls and consecutive_no_change < 5:
                scroll_attempts += 1
                
                # Scroll down to trigger lazy loading
                await page.evaluate("""
                    window.scrollTo(0, document.body.scrollHeight);
                    // Also try scrolling to specific elements that might trigger loading
                    const containers = document.querySelectorAll('[class*="code"], [class*="notebook"], .list-item, li, article');
                    if (containers.length > 0) {
                        containers[containers.length - 1].scrollIntoView();
                    }
                """)
                
                # Wait for content to load - increased from 3 to 5 seconds
                await asyncio.sleep(5)
                
                # Count current notebook links
                current_links = await page.query_selector_all('a[href*="/code/"]')
                current_count = len([link for link in current_links if link])
                
                if self.dev_mode:
                    logger.debug(f"Scroll {scroll_attempts}: Found {current_count} notebook links (+{current_count - previous_notebook_count} new)")
                
                # Check if we found new content
                if current_count > previous_notebook_count:
                    consecutive_no_change = 0
                    previous_notebook_count = current_count
                    
                    # If we've reached our target, we can stop
                    if target_limit and current_count >= target_limit * 2:  # *2 because we filter duplicates
                        if self.dev_mode:
                            logger.debug(f"Reached target limit, stopping scroll")
                        break
                else:
                    consecutive_no_change += 1
                
                # Try to find and click "Load More" or "Show More" buttons
                load_more_selectors = [
                    'button:contains("Load More")',
                    'button:contains("Show More")', 
                    'a:contains("Load More")',
                    'a:contains("Show More")',
                    '[class*="load-more"]',
                    '[class*="show-more"]',
                    'button[aria-label*="Load"]',
                    'button[aria-label*="Show"]'
                ]
                
                for selector in load_more_selectors:
                    try:
                        if 'contains' not in selector:
                            load_btn = await page.query_selector(selector)
                            if load_btn and await load_btn.is_visible():
                                await load_btn.click()
                                await asyncio.sleep(4)  # Increased wait after clicking load more
                                if self.dev_mode:
                                    logger.debug(f"Clicked load more button: {selector}")
                                break
                        else:
                            # Handle text-based selectors
                            buttons = await page.query_selector_all('button, a')
                            for btn in buttons:
                                try:
                                    if await btn.is_visible():
                                        text = await btn.text_content()
                                        if text and any(word in text.lower() for word in ['load more', 'show more', 'more']):
                                            await btn.click()
                                            await asyncio.sleep(4)  # Increased wait after clicking text-based load more
                                            if self.dev_mode:
                                                logger.debug(f"Clicked load more button with text: {text}")
                                            break
                                except:
                                    continue
                    except:
                        continue
            
            final_count = len(await page.query_selector_all('a[href*="/code/"]'))
            if self.dev_mode:
                logger.debug(f"Lazy loading completed after {scroll_attempts} scrolls. Final count: {final_count} links")
                
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error during lazy loading: {e}")

    async def _extract_notebook_title(self, element, page) -> str:
        """Extract notebook title from element"""
        try:
            # Strategy 1: Extract title from URL (most reliable)
            href = await element.get_attribute('href')
            if href:
                # Remove /comments suffix if present
                clean_href = href.replace('/comments', '')
                parts = clean_href.split('/')
                if len(parts) >= 2:
                    # Get the notebook name part (last segment)
                    notebook_name = parts[-1]
                    # Convert dashes to spaces and title case
                    title_from_url = notebook_name.replace('-', ' ').title()
                    if len(title_from_url) > 3:  # Valid title
                        return title_from_url[:50]
            
            # Strategy 2: Try to find actual title elements
            title_selectors = [
                'h3', 'h4', 'h5',
                '[class*="title"]', 
                '.sc-notebook-title',
                '[data-testid*="title"]',
                'a[title]'  # Look for title attributes
            ]
            
            for selector in title_selectors:
                title_elem = await element.query_selector(selector)
                if title_elem:
                    # Try title attribute first
                    title_attr = await title_elem.get_attribute('title')
                    if title_attr and title_attr.strip() and 'comment' not in title_attr.lower():
                        return title_attr.strip()[:50]
                    
                    # Try text content
                    title = await title_elem.text_content()
                    if title and title.strip() and 'comment' not in title.lower():
                        clean_title = title.strip()
                        # Filter out obvious non-titles
                        if not any(word in clean_title.lower() for word in ['comment', 'vote', 'upvote', 'ago', 'days']):
                            return clean_title[:50]
            
            # Strategy 3: Look for author name if available (fallback)
            author_selectors = ['.username', '[class*="author"]', '.user-name']
            for selector in author_selectors:
                author_elem = await element.query_selector(selector)
                if author_elem:
                    author = await author_elem.text_content()
                    if author and author.strip():
                        return f"Notebook by {author.strip()}"[:50]
            
            # Final fallback: use cleaned URL
            if href:
                parts = href.replace('/comments', '').split('/')
                if len(parts) >= 2:
                    return parts[-1].replace('-', ' ').title()[:50]
            
            return "Unknown Notebook"
            
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error extracting title: {e}")
            return "Unknown Notebook"

    async def _extract_notebook_author(self, element) -> str:
        """Extract notebook author from element"""
        try:
            # Look for author-related elements
            author_selectors = ['.sc-author', '[class*="author"]', '.username']
            
            for selector in author_selectors:
                author_elem = await element.query_selector(selector)
                if author_elem:
                    author = await author_elem.text_content()
                    if author and author.strip():
                        return author.strip()
            
            return "unknown"
            
        except:
            return "unknown"

    async def _extract_last_updated(self, element) -> str:
        """Extract last updated date from element"""
        try:
            # Look for date-related elements
            date_selectors = ['.sc-date', '[class*="date"]', '[class*="time"]', 'time']
            
            for selector in date_selectors:
                date_elem = await element.query_selector(selector)
                if date_elem:
                    date_text = await date_elem.text_content()
                    if date_text:
                        # Try to parse and format date
                        return self._format_date(date_text.strip())
            
            # Fallback to current date
            return datetime.now().strftime("%y%m%d")
            
        except:
            return datetime.now().strftime("%y%m%d")

    async def _extract_votes(self, element) -> int:
        """Extract vote count from element"""
        try:
            vote_selectors = ['.sc-votes', '[class*="vote"]', '[class*="score"]']
            
            for selector in vote_selectors:
                vote_elem = await element.query_selector(selector)
                if vote_elem:
                    vote_text = await vote_elem.text_content()
                    if vote_text:
                        # Extract number from text
                        numbers = re.findall(r'\d+', vote_text)
                        if numbers:
                            return int(numbers[0])
            
            return 0
            
        except:
            return 0

    def _format_date(self, date_text: str) -> str:
        """Format date text to YYMMDD format"""
        try:
            # Common date patterns
            patterns = [
                r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})',  # MM-DD-YYYY
            ]
            
            for pattern in patterns:
                match = re.search(pattern, date_text)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Determine order based on pattern
                        if pattern.startswith(r'(\d{4})'):  # YYYY first
                            year, month, day = groups
                        else:  # MM first
                            month, day, year = groups
                        
                        # Convert to YYMMDD
                        year_short = str(int(year))[-2:]
                        month_padded = f"{int(month):02d}"
                        day_padded = f"{int(day):02d}"
                        
                        return f"{year_short}{month_padded}{day_padded}"
            
            # If no pattern matches, use current date
            return datetime.now().strftime("%y%m%d")
            
        except:
            return datetime.now().strftime("%y%m%d")

    async def extract_notebook_comments(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """
        Extract comments/discussions from notebook page and download notebook via API
        
        Args:
            notebook: NotebookInfo object
            output_dir: Directory to save files
            
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing: {notebook.title}")
            
            # Step 1: Extract comments/discussions from the page
            comments_success = await self._extract_and_save_comments(notebook, output_dir)
            
            # Step 2: Extract username/kernel_name from URL and download via API
            api_success = await self._download_via_kaggle_api(notebook, output_dir)
            
            # Step 3: Convert notebook to Python file
            convert_success = self._convert_notebook_to_python_file(notebook, output_dir)
            
            overall_success = comments_success or api_success or convert_success
            if overall_success:
                logger.info(f"✓ Completed processing: {notebook.title}")
            else:
                logger.warning(f"✗ Failed to process: {notebook.title}")
            
            return overall_success
                    
        except Exception as e:
            logger.error(f"✗ Error processing {notebook.title}: {e}")
            return False

    async def _extract_and_save_comments(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """Extract comments/discussions from notebook code page"""
        try:
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=self.headless)
                page = await browser.new_page()
                
                try:
                    # Load notebook page
                    await page.goto(notebook.url, wait_until="domcontentloaded")
                    await asyncio.sleep(3)  # Wait for dynamic content
                    
                    # Extract comments/discussions
                    comments = []
                    
                    # Look for comment sections using various selectors
                    comment_selectors = [
                        '[class*="comment"]',
                        '[class*="discussion"]', 
                        '[data-testid*="comment"]',
                        '.sc-comment',
                        '.comment-container',
                        '.discussion-container'
                    ]
                    
                    for selector in comment_selectors:
                        comment_elements = await page.query_selector_all(selector)
                        for element in comment_elements:
                            try:
                                text = await element.text_content()
                                if text and len(text.strip()) > 10:  # Filter out empty/short content
                                    comments.append(text.strip())
                            except:
                                continue
                    
                    # Also try to get discussion thread content
                    thread_elements = await page.query_selector_all('[class*="thread"], [class*="reply"], .sc-thread')
                    for element in thread_elements:
                        try:
                            text = await element.text_content()
                            if text and len(text.strip()) > 10:
                                comments.append(text.strip())
                        except:
                            continue
                    
                    # Save comments to file if found
                    if comments:
                        comments_file = output_dir / f"{notebook.filename.replace('.py', '_comments.md')}"
                        with open(comments_file, 'w', encoding='utf-8') as f:
                            f.write(f"# Comments for {notebook.title}\n\n")
                            f.write(f"**Author:** {notebook.author}\n")
                            f.write(f"**Source:** {notebook.url}\n")
                            f.write(f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                            f.write("---\n\n")
                            
                            for i, comment in enumerate(comments, 1):
                                f.write(f"## Comment {i}\n\n{comment}\n\n")
                        
                        logger.info(f"Saved {len(comments)} comments to {comments_file}")
                        return True
                    else:
                        logger.info(f"No comments found for {notebook.title}")
                        return False
                        
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"Error extracting comments for {notebook.title}: {e}")
            return False

    async def _download_via_kaggle_api(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """Download notebook using Kaggle API"""
        try:
            # Convert to absolute path to avoid issues with directory changes
            output_dir = output_dir.resolve()
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract username/kernel_name from URL
            # URL format: https://www.kaggle.com/code/username/kernel-name
            url_parts = notebook.url.split('/')
            if len(url_parts) < 5 or '/code/' not in notebook.url:
                logger.error(f"Invalid notebook URL format: {notebook.url}")
                return False
            
            username = url_parts[-2]  # Second to last part
            kernel_name = url_parts[-1]  # Last part
            kernel_slug = f"{username}/{kernel_name}"
            
            logger.info(f"Downloading notebook: {kernel_slug}")
            
            # Use kaggle CLI to download notebook
            import subprocess
            import tempfile
            import os
            
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Change to temp directory and download
                original_dir = os.getcwd()
                
                try:
                    os.chdir(temp_dir)
                    
                    # Run kaggle kernels pull command (correct format)
                    if self.dev_mode:
                        logger.debug(f"Running command: kaggle kernels pull {kernel_slug} in {temp_dir}")
                    
                    result = subprocess.run(
                        ['kaggle', 'kernels', 'pull', kernel_slug],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if self.dev_mode:
                        logger.debug(f"Command return code: {result.returncode}")
                        logger.debug(f"Command stdout: {result.stdout}")
                        logger.debug(f"Command stderr: {result.stderr}")
                    
                    if result.returncode == 0:
                        # Look for downloaded .ipynb file
                        ipynb_files = list(Path(temp_dir).glob("*.ipynb"))
                        if self.dev_mode:
                            logger.debug(f"Found .ipynb files: {ipynb_files}")
                        
                        if ipynb_files:
                            ipynb_file = ipynb_files[0]
                            # Copy to output directory with proper name (use absolute path)
                            target_file = output_dir / f"{notebook.filename.replace('.py', '.ipynb')}"
                            import shutil
                            
                            if self.dev_mode:
                                logger.debug(f"Copying from: {ipynb_file}")
                                logger.debug(f"Copying to: {target_file}")
                                logger.debug(f"Output dir absolute: {output_dir}")
                            
                            try:
                                shutil.copy2(str(ipynb_file), str(target_file))
                                logger.info(f"Downloaded notebook to: {target_file}")
                                return True
                            except Exception as copy_error:
                                logger.error(f"Error copying file: {copy_error}")
                                return False
                        else:
                            logger.error(f"No .ipynb file found after download in {temp_dir}")
                            # List files in temp directory for debugging
                            if self.dev_mode:
                                temp_files = list(Path(temp_dir).glob("*"))
                                logger.debug(f"Files in temp directory: {temp_files}")
                            return False
                    else:
                        logger.error(f"Kaggle API error (return code {result.returncode}): {result.stderr}")
                        return False
                        
                finally:
                    os.chdir(original_dir)
                    
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout downloading notebook: {kernel_slug}")
            return False
        except Exception as e:
            logger.error(f"Error downloading notebook {notebook.title}: {e}")
            return False

    def _convert_notebook_to_python_file(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """Convert downloaded notebook to Python file"""
        try:
            # Convert to absolute path for consistency
            output_dir = output_dir.resolve()
            
            # Look for the downloaded .ipynb file
            ipynb_file = output_dir / f"{notebook.filename.replace('.py', '.ipynb')}"
            
            if not ipynb_file.exists():
                logger.warning(f"Notebook file not found: {ipynb_file}")
                return False
            
            # Read and convert notebook
            with open(ipynb_file, 'r', encoding='utf-8') as f:
                nb_data = json.load(f)
            
            nb = nbformat.from_dict(nb_data)
            
            # Use nbconvert to convert to Python
            exporter = PythonExporter()
            python_code, _ = exporter.from_notebook_node(nb)
            
            # Add header with metadata
            header = f'''#!/usr/bin/env python3
"""
{notebook.title}
Author: {notebook.author}
Last Updated: {notebook.last_updated}
Source: {notebook.url}
Downloaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

'''
            
            # Save Python file
            python_file = output_dir / notebook.filename
            with open(python_file, 'w', encoding='utf-8') as f:
                f.write(header + python_code)
            
            logger.info(f"Converted notebook to Python: {python_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error converting notebook {notebook.title}: {e}")
            return False

    async def _extract_notebook_content(self, page: Page) -> Optional[str]:
        """Extract notebook content from page"""
        try:
            # Look for JSON content or downloadable notebook
            selectors = [
                '[data-jupyter-content]',
                'script[type="application/json"]',
                'pre[class*="notebook"]',
                '.notebook-content'
            ]
            
            for selector in selectors:
                content_elem = await page.query_selector(selector)
                if content_elem:
                    content = await content_elem.text_content()
                    if content and 'cells' in content:
                        return content
            
            # Alternative: look for code cells directly
            code_cells = await page.query_selector_all('.code-cell, .markdown-cell, [class*="cell"]')
            if code_cells:
                # Build notebook structure from visible cells
                cells = []
                for cell in code_cells:
                    cell_content = await cell.text_content()
                    if cell_content and cell_content.strip():
                        cell_type = 'code'  # Default assumption
                        cells.append({
                            'cell_type': cell_type,
                            'source': [cell_content.strip()]
                        })
                
                if cells:
                    notebook_structure = {
                        'cells': cells,
                        'metadata': {},
                        'nbformat': 4,
                        'nbformat_minor': 2
                    }
                    return json.dumps(notebook_structure)
            
            return None
            
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error extracting notebook content: {e}")
            return None

    def _convert_notebook_to_python(self, notebook_json: str, notebook_info: NotebookInfo) -> str:
        """Convert notebook JSON to Python code"""
        try:
            # Parse notebook JSON
            nb_data = json.loads(notebook_json)
            nb = nbformat.from_dict(nb_data)
            
            # Use nbconvert to convert to Python
            exporter = PythonExporter()
            python_code, _ = exporter.from_notebook_node(nb)
            
            # Add header with metadata
            header = f'''#!/usr/bin/env python3
"""
{notebook_info.title}
Author: {notebook_info.author}
Last Updated: {notebook_info.last_updated}
Source: {notebook_info.url}
Downloaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

'''
            
            return header + python_code
            
        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error converting notebook: {e}")
            
            # Fallback: basic conversion
            try:
                nb_data = json.loads(notebook_json)
                cells = nb_data.get('cells', [])
                
                python_lines = [
                    f'#!/usr/bin/env python3',
                    f'"""',
                    f'{notebook_info.title}',
                    f'Author: {notebook_info.author}',
                    f'Last Updated: {notebook_info.last_updated}',
                    f'Source: {notebook_info.url}',
                    f'Downloaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                    f'"""',
                    '',
                ]
                
                for cell in cells:
                    if cell.get('cell_type') == 'code':
                        source = cell.get('source', [])
                        if isinstance(source, list):
                            python_lines.extend(source)
                        else:
                            python_lines.append(str(source))
                        python_lines.append('')
                    elif cell.get('cell_type') == 'markdown':
                        source = cell.get('source', [])
                        if isinstance(source, list):
                            for line in source:
                                python_lines.append(f'# {line}')
                        else:
                            python_lines.append(f'# {source}')
                        python_lines.append('')
                
                return '\n'.join(python_lines)
                
            except:
                return f'''#!/usr/bin/env python3
"""
{notebook_info.title}
Author: {notebook_info.author}
Last Updated: {notebook_info.last_updated}
Source: {notebook_info.url}
Downloaded: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

ERROR: Could not parse notebook content
"""

# Notebook content extraction failed
print("Error: Could not extract notebook content")
'''

    async def download_competition_notebooks(self, competition_url: str, limit: Optional[int] = None, output_dir: Optional[Path] = None) -> bool:
        """
        Download and convert all notebooks from a competition
        
        Args:
            competition_url: Competition URL
            limit: Maximum number of notebooks to download
            output_dir: Output directory (default: kaggle_notebooks_downloaded)
            
        Returns:
            bool: Success status
        """
        # Set default output directory
        if output_dir is None:
            output_dir = Path("kaggle_notebooks_downloaded")
        
        # Create output directory
        output_dir.mkdir(exist_ok=True)
        
        # Extract competition name for subfolder
        comp_name = competition_url.rstrip('/').split('/')[-1]
        comp_output_dir = output_dir / comp_name
        comp_output_dir.mkdir(exist_ok=True)
        
        # Get notebook list
        notebooks = await self.extract_notebook_list(competition_url, limit)
        
        if not notebooks:
            logger.error("No notebooks found!")
            return False
        
        # Download and convert each notebook
        successful_downloads = 0
        total_notebooks = len(notebooks)
        
        for i, notebook in enumerate(notebooks, 1):
            logger.info(f"[{i}/{total_notebooks}] Processing notebook: {notebook.title}")
            
            success = await self.extract_notebook_comments(notebook, comp_output_dir)
            if success:
                successful_downloads += 1
            
            # Small delay between downloads
            await asyncio.sleep(2)
        
        # Report results
        logger.info(f"SUCCESS: Downloaded {successful_downloads}/{total_notebooks} notebooks")
        logger.info(f"Output saved in: {comp_output_dir.absolute()}")
        
        return successful_downloads > 0