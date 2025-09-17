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
    logger.error(f"Missing dependencies: {e}. Please run: pip install nbformat nbconvert")
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
                await asyncio.sleep(5)  # Wait for initial load

                # Handle lazy loading
                await self._handle_lazy_loading(page, limit or 50)

                # Extract notebook links and metadata
                notebooks = await self._extract_notebooks_from_page(page, limit)

                return notebooks

            finally:
                await browser.close()

    async def _handle_lazy_loading(self, page, target_limit):
        """Handle infinite scroll lazy loading to extract all possible notebooks"""
        try:
            previous_notebook_count = 0
            consecutive_no_change = 0
            max_scrolls = 20  # Reduced for efficiency
            scroll_attempts = 0

            if self.dev_mode:
                logger.debug(f"Starting lazy loading to find up to {target_limit} notebooks")

            while scroll_attempts < max_scrolls and consecutive_no_change < 3:
                scroll_attempts += 1

                # Scroll down to trigger lazy loading
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(3)

                # Count current notebook links
                current_links = await page.query_selector_all('a[href*="/code/"]')
                current_count = len([link for link in current_links if link])

                if self.dev_mode:
                    logger.debug(f"Scroll {scroll_attempts}: Found {current_count} notebook links")

                # Check if we found new content
                if current_count > previous_notebook_count:
                    consecutive_no_change = 0
                    previous_notebook_count = current_count

                    # If we've reached our target, we can stop
                    if target_limit and current_count >= target_limit * 2:
                        break
                else:
                    consecutive_no_change += 1

        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error during lazy loading: {e}")

    async def _extract_notebooks_from_page(self, page: Page, limit: Optional[int] = None) -> List[NotebookInfo]:
        """Extract notebook information from the current page state"""
        notebooks = []

        # Find notebook links
        notebook_links = await page.query_selector_all('a[href*="/code/"]')

        if self.dev_mode:
            logger.debug(f"Found {len(notebook_links)} potential notebook links")

        # Process each notebook link
        seen_urls = set()
        for link in notebook_links:
            try:
                href = await link.get_attribute('href')
                if not href or '/code/' not in href or '?scriptVersionId' in href:
                    continue

                # Make absolute URL
                notebook_url = urljoin('https://www.kaggle.com', href)

                # Skip duplicates
                if notebook_url in seen_urls:
                    continue
                seen_urls.add(notebook_url)

                # Extract metadata
                title = await self._extract_notebook_title(link)
                author = await self._extract_notebook_author(link)
                last_updated = datetime.now().strftime("%y%m%d")

                # Generate safe filename
                safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
                filename = f"{safe_title}_{last_updated}.py"

                notebook = NotebookInfo(
                    title=title,
                    url=notebook_url,
                    author=author,
                    last_updated=last_updated,
                    votes=0,
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
                    logger.warning(f"Error processing notebook link: {e}")
                continue

        logger.info(f"Found {len(notebooks)} notebooks")
        return notebooks

    async def _extract_notebook_title(self, element) -> str:
        """Extract notebook title from element"""
        try:
            # Try to get title from URL
            href = await element.get_attribute('href')
            if href:
                parts = href.split('/')
                if len(parts) >= 2:
                    notebook_name = parts[-1]
                    title_from_url = notebook_name.replace('-', ' ').title()
                    if len(title_from_url) > 3:
                        return title_from_url[:50]

            # Try to get text content
            text = await element.text_content()
            if text and text.strip():
                return text.strip()[:50]

            return "Unknown Notebook"

        except:
            return "Unknown Notebook"

    async def _extract_notebook_author(self, element) -> str:
        """Extract notebook author from element"""
        try:
            # Look for author in parent elements
            parent = await element.query_selector('xpath=..')
            if parent:
                author_elem = await parent.query_selector('[class*="author"], .username')
                if author_elem:
                    author = await author_elem.text_content()
                    if author and author.strip():
                        return author.strip()

            return "unknown"

        except:
            return "unknown"

    async def download_and_convert_notebook(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """
        Download and convert a single notebook to Python

        Args:
            notebook: NotebookInfo object
            output_dir: Directory to save files

        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Processing: {notebook.title}")

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Download via Kaggle API
            success = await self._download_via_kaggle_api(notebook, output_dir)

            if success:
                # Convert notebook to Python
                success = self._convert_notebook_to_python_file(notebook, output_dir)

            if success:
                logger.info(f"Successfully processed: {notebook.title}")
            else:
                logger.warning(f"Failed to process: {notebook.title}")

            return success

        except Exception as e:
            logger.error(f"Error processing {notebook.title}: {e}")
            return False

    async def _download_via_kaggle_api(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """Download notebook using Kaggle API"""
        try:
            # Extract username/kernel_name from URL
            url_parts = notebook.url.split('/')
            if len(url_parts) < 5 or '/code/' not in notebook.url:
                logger.error(f"Invalid notebook URL format: {notebook.url}")
                return False

            username = url_parts[-2]
            kernel_name = url_parts[-1]
            kernel_slug = f"{username}/{kernel_name}"

            logger.info(f"Downloading notebook: {kernel_slug}")

            import subprocess
            import os

            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                original_dir = os.getcwd()

                try:
                    os.chdir(temp_dir)

                    # Run kaggle kernels pull command
                    result = subprocess.run(
                        ['kaggle', 'kernels', 'pull', kernel_slug],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )

                    if result.returncode == 0:
                        # Look for downloaded .ipynb file
                        ipynb_files = list(Path(temp_dir).glob("*.ipynb"))

                        if ipynb_files:
                            ipynb_file = ipynb_files[0]
                            target_file = output_dir / f"{notebook.filename.replace('.py', '.ipynb')}"

                            import shutil
                            shutil.copy2(str(ipynb_file), str(target_file))
                            logger.info(f"Downloaded notebook to: {target_file}")
                            return True
                        else:
                            logger.error(f"No .ipynb file found after download")
                            return False
                    else:
                        logger.error(f"Kaggle API error: {result.stderr}")
                        return False

                finally:
                    os.chdir(original_dir)

        except Exception as e:
            logger.error(f"Error downloading notebook {notebook.title}: {e}")
            return False

    def _convert_notebook_to_python_file(self, notebook: NotebookInfo, output_dir: Path) -> bool:
        """Convert downloaded notebook to Python file"""
        try:
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

            success = await self.download_and_convert_notebook(notebook, comp_output_dir)
            if success:
                successful_downloads += 1

            # Small delay between downloads
            await asyncio.sleep(2)

        # Report results
        logger.info(f"SUCCESS: Downloaded {successful_downloads}/{total_notebooks} notebooks")
        logger.info(f"Output saved in: {comp_output_dir.absolute()}")

        return successful_downloads > 0