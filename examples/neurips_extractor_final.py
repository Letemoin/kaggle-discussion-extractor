#!/usr/bin/env python3
"""
NeurIPS 2025 Discussion Extractor - FINAL STANDALONE VERSION
- Properly splits content between parent and nested replies (no duplication)
- Completely standalone - no external dependencies except standard libraries
- Dynamic extraction (can process all discussions or limited number)
"""

import sys
import asyncio
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

# Check for playwright
try:
    from playwright.async_api import async_playwright, Page, ElementHandle
except ImportError:
    print("ERROR: playwright not installed. Please run: pip install playwright")
    print("Then run: playwright install chromium")
    sys.exit(1)


@dataclass
class Author:
    """Author information with ranking/badges"""
    name: str
    username: str
    rank: Optional[str] = None
    badges: List[str] = None
    profile_url: str = ""
    
    def __post_init__(self):
        if self.badges is None:
            self.badges = []


@dataclass
class Reply:
    """Represents a discussion reply with hierarchy"""
    reply_number: str  # e.g., "1", "1.1", "1.1.1"
    content: str
    author: Author
    upvotes: int
    timestamp: str
    depth: int = 0
    sub_replies: List['Reply'] = None
    
    def __post_init__(self):
        if self.sub_replies is None:
            self.sub_replies = []


@dataclass
class Discussion:
    """Complete discussion thread"""
    title: str
    url: str
    main_content: str
    main_author: Author
    main_upvotes: int
    replies: List[Reply]
    total_replies: int
    extraction_time: str


class ContentExtractor:
    """Handles content extraction and deduplication"""
    
    @staticmethod
    def extract_author_content_only(element_html: str, author_username: str) -> str:
        """Extract only the content from a specific author, removing nested replies"""
        # Remove nested comment containers first
        # These patterns indicate nested/child comments
        nested_patterns = [
            r'<div[^>]*class="[^"]*sc-gGOevJ[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*class="[^"]*hvAeBk[^"]*"[^>]*>.*?</div>',
            r'<div[^>]*data-testid="discussions-comment"[^>]*>.*?</div>'
        ]
        
        clean_html = element_html
        for pattern in nested_patterns:
            # Remove nested divs but keep the current level
            parts = re.split(pattern, clean_html)
            if len(parts) > 1:
                clean_html = parts[0]  # Keep only content before nested elements
        
        # Extract text content
        # Remove HTML tags but preserve text
        text = re.sub(r'<[^>]+>', ' ', clean_html)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove metadata lines
        lines = text.split('.')
        content_lines = []
        for line in lines:
            line = line.strip()
            # Skip lines that are metadata
            if not any(skip in line.lower() for skip in [
                'posted', 'edited', 'vote', 'reply', 
                'in this competition', author_username.lower(),
                'timestamp', 'upvote'
            ]):
                if len(line) > 20:  # Meaningful content
                    content_lines.append(line)
        
        return '. '.join(content_lines).strip() if content_lines else ""


async def extract_author_info(element) -> Author:
    """Extract detailed author information from an element"""
    try:
        # Find author link
        author_links = await element.query_selector_all('a[href^="/"]')
        author_link = None
        username = "unknown"
        
        for link in author_links:
            href = await link.get_attribute('href')
            if href and href.startswith('/') and not any(skip in href for skip in ['/competitions/', '/discussion/', '/code/', '/datasets/']):
                username_match = re.match(r'^/([^/]+)$', href)
                if username_match:
                    author_link = link
                    username = username_match.group(1)
                    break
        
        if not author_link:
            return Author(name="Unknown", username="unknown")
        
        # Get author name
        name = username
        link_text = await author_link.text_content()
        if link_text and link_text.strip():
            name = link_text.strip()
        
        # Extract rank
        rank = None
        try:
            parent_html = await element.inner_html()
            rank_match = re.search(r'(\d+(?:st|nd|rd|th))\s+in\s+this\s+Competition', parent_html)
            if rank_match:
                rank = rank_match.group(0)
        except:
            pass
        
        # Extract badges
        badges = []
        badge_spans = await element.query_selector_all('span')
        for span in badge_spans:
            text = await span.text_content()
            if text and any(badge_word in text for badge_word in ['Host', 'Expert', 'Master', 'Grandmaster']):
                if text not in badges:
                    badges.append(text)
        
        return Author(
            name=name,
            username=username,
            rank=rank,
            badges=badges if badges else None,
            profile_url=f"https://www.kaggle.com/{username}"
        )
    except Exception as e:
        print(f"     Warning: Error extracting author: {e}")
        return Author(name="Unknown", username="unknown")


async def extract_upvotes(element) -> int:
    """Extract upvote count from element"""
    try:
        vote_buttons = await element.query_selector_all('button[aria-label*="vote"]')
        for vote_button in vote_buttons:
            aria_label = await vote_button.get_attribute('aria-label')
            if aria_label:
                match = re.search(r'(-?\d+)\s+votes?', aria_label)
                if match:
                    return int(match.group(1))
        
        buttons = await element.query_selector_all('button')
        for button in buttons:
            text = await button.text_content()
            if text and re.match(r'^-?\d+$', text.strip()):
                return int(text.strip())
    except:
        pass
    return 0


async def extract_comment_content(element, author_username: str) -> str:
    """Extract only the content from this specific comment, excluding nested replies"""
    try:
        # Get the element's outer HTML
        outer_html = await element.evaluate('el => el.outerHTML')
        
        # Find the content container
        content_match = re.search(r'<div[^>]*class="[^"]*(?:eTCgfj|jMpVQY)[^"]*"[^>]*>(.*?)</div>', outer_html, re.DOTALL)
        
        if content_match:
            content_html = content_match.group(1)
            
            # Remove any nested comment divs
            content_html = re.sub(r'<div[^>]*data-testid="discussions-comment"[^>]*>.*?</div>', '', content_html, flags=re.DOTALL)
            
            # Extract text from paragraphs
            paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', content_html, re.DOTALL)
            
            if paragraphs:
                content_parts = []
                for p_content in paragraphs:
                    # Clean HTML tags
                    text = re.sub(r'<[^>]+>', '', p_content)
                    text = text.strip()
                    if text and len(text) > 10:
                        content_parts.append(text)
                
                return '\n'.join(content_parts)
        
        # Fallback: get all text and filter
        all_text = await element.text_content()
        if all_text:
            lines = all_text.split('\n')
            content_lines = []
            skip_next = False
            
            for line in lines:
                line = line.strip()
                
                # Skip metadata lines
                if any(skip in line.lower() for skip in [
                    'posted', 'edited', 'reply', 'vote', 
                    f'{author_username.lower()}',
                    'in this competition', '·'
                ]):
                    skip_next = True
                    continue
                
                if skip_next:
                    skip_next = False
                    continue
                
                if len(line) > 20:
                    content_lines.append(line)
            
            return '\n'.join(content_lines[:3])  # Limit to avoid capturing child content
        
        return ""
        
    except Exception as e:
        print(f"     Warning: Error extracting content: {e}")
        return ""


async def extract_hierarchical_replies_final(page: Page) -> List[Reply]:
    """Extract replies with proper content separation - no duplication"""
    replies = []
    
    try:
        # Get ALL comment elements
        all_comments = await page.query_selector_all('div[data-testid="discussions-comment"]')
        
        if not all_comments:
            print("     No comment elements found")
            return replies
        
        print(f"     Found {len(all_comments)} total comment elements")
        
        # Map to track which comments are nested
        comment_hierarchy = {}
        processed_comments = []
        
        # First pass: identify hierarchy
        for i, comment_elem in enumerate(all_comments):
            try:
                # Check if nested
                is_nested = await comment_elem.evaluate('''
                    (element) => {
                        let current = element.parentElement;
                        while (current) {
                            if (current.classList && 
                                (current.classList.contains('sc-gGOevJ') || 
                                 current.classList.contains('hvAeBk'))) {
                                return true;
                            }
                            current = current.parentElement;
                        }
                        return false;
                    }
                ''')
                
                # Extract author first to get username
                author = await extract_author_info(comment_elem)
                
                if author.username == "unknown":
                    continue
                
                # Extract content specific to this comment only
                content = await extract_comment_content(comment_elem, author.username)
                
                if not content or len(content.strip()) < 5:
                    continue
                
                # Extract other metadata
                upvotes = await extract_upvotes(comment_elem)
                
                timestamp = ""
                time_elem = await comment_elem.query_selector('span[title]')
                if time_elem:
                    timestamp = await time_elem.get_attribute('title') or ""
                
                # Find parent if nested
                parent_idx = None
                if is_nested:
                    # Find the most recent non-nested comment as parent
                    for j in range(len(processed_comments) - 1, -1, -1):
                        if not processed_comments[j]['is_nested']:
                            parent_idx = j
                            break
                
                processed_comments.append({
                    'author': author,
                    'content': content,
                    'upvotes': upvotes,
                    'timestamp': timestamp,
                    'is_nested': is_nested,
                    'parent_idx': parent_idx,
                    'original_idx': i
                })
                
            except Exception as e:
                print(f"     Warning: Error processing comment {i}: {e}")
                continue
        
        print(f"     Processed {len(processed_comments)} valid comments")
        
        # Second pass: build hierarchy
        reply_objects = []
        for data in processed_comments:
            reply = Reply(
                reply_number="",
                content=data['content'],
                author=data['author'],
                upvotes=data['upvotes'],
                timestamp=data['timestamp'],
                depth=0
            )
            reply_objects.append(reply)
        
        # Build parent-child relationships
        for i, data in enumerate(processed_comments):
            if data['is_nested'] and data['parent_idx'] is not None:
                parent_reply = reply_objects[data['parent_idx']]
                child_reply = reply_objects[i]
                parent_reply.sub_replies.append(child_reply)
                child_reply.depth = parent_reply.depth + 1
        
        # Get only top-level replies
        top_level_replies = []
        for i, data in enumerate(processed_comments):
            if not data['is_nested']:
                top_level_replies.append(reply_objects[i])
        
        # Assign reply numbers
        reply_counter = 1
        for reply in top_level_replies:
            reply.reply_number = str(reply_counter)
            
            for sub_idx, sub_reply in enumerate(reply.sub_replies, 1):
                sub_reply.reply_number = f"{reply_counter}.{sub_idx}"
                
                for sub_sub_idx, sub_sub_reply in enumerate(sub_reply.sub_replies, 1):
                    sub_sub_reply.reply_number = f"{reply_counter}.{sub_idx}.{sub_sub_idx}"
            
            reply_counter += 1
        
        nested_count = sum(len(r.sub_replies) for r in top_level_replies)
        if nested_count > 0:
            print(f"     Found {len(top_level_replies)} top-level and {nested_count} nested replies")
        else:
            print(f"     Found {len(top_level_replies)} top-level replies (no nested detected)")
        
        return top_level_replies
        
    except Exception as e:
        print(f"   Error extracting replies: {e}")
        return []


async def extract_single_discussion(page: Page, url: str) -> Optional[Discussion]:
    """Extract a single discussion with all replies"""
    try:
        print(f"   Loading: {url.split('/')[-1]}")
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        
        # Get title
        title = "Unknown Title"
        title_selectors = ['h1', 'h2', 'h3[class*="kvnevz"]', '[data-testid*="title"]']
        for selector in title_selectors:
            title_elem = await page.query_selector(selector)
            if title_elem:
                text = await title_elem.text_content()
                if text and text.strip():
                    title = text.strip()
                    break
        
        # Get main post
        main_content = ""
        main_author = Author(name="Unknown", username="unknown")
        main_upvotes = 0
        
        main_selectors = [
            'div[data-testid="discussions-topic-header"]',
            'div[class*="topic-header"]',
            'article:first-of-type'
        ]
        
        for selector in main_selectors:
            main_elem = await page.query_selector(selector)
            if main_elem:
                main_author = await extract_author_info(main_elem)
                main_upvotes = await extract_upvotes(main_elem)
                
                # Extract main content
                content_elem = await main_elem.query_selector('div[class*="eTCgfj"], div[class*="jMpVQY"]')
                if content_elem:
                    main_content = await content_elem.text_content()
                    if main_content:
                        main_content = main_content.strip()
                        break
        
        print(f"   Author: {main_author.name} (@{main_author.username})")
        if main_author.rank:
            print(f"   Rank: {main_author.rank}")
        
        # Extract replies with proper content separation
        replies = await extract_hierarchical_replies_final(page)
        
        return Discussion(
            title=title,
            url=url,
            main_content=main_content,
            main_author=main_author,
            main_upvotes=main_upvotes,
            replies=replies,
            total_replies=count_all_replies(replies),
            extraction_time=datetime.now().isoformat()
        )
        
    except Exception as e:
        print(f"   Error extracting discussion: {e}")
        return None


def count_all_replies(replies: List[Reply]) -> int:
    """Count all replies including sub-replies recursively"""
    count = 0
    for reply in replies:
        count += 1
        count += count_all_replies(reply.sub_replies)
    return count


def save_discussion_markdown(discussion: Discussion, output_file: Path):
    """Save discussion in markdown format with proper hierarchy"""
    content = f"# {discussion.title}\n\n"
    content += f"**URL**: {discussion.url}\n"
    content += f"**Total Comments**: {discussion.total_replies}\n"
    content += f"**Extracted**: {discussion.extraction_time}\n\n"
    content += "---\n\n"
    
    # Main post
    content += "## Main Post\n\n"
    content += f"**Author**: {discussion.main_author.name} (@{discussion.main_author.username})\n"
    if discussion.main_author.rank:
        content += f"**Rank**: {discussion.main_author.rank}\n"
    if discussion.main_author.badges:
        content += f"**Badges**: {', '.join(discussion.main_author.badges)}\n"
    content += f"**Upvotes**: {discussion.main_upvotes}\n\n"
    content += f"{discussion.main_content}\n\n"
    content += "---\n\n"
    
    # Replies with hierarchy
    if discussion.replies:
        content += "## Replies\n\n"
        
        def format_reply(reply: Reply, indent_level: int = 0) -> str:
            indent = "  " * indent_level
            result = ""
            
            # Format header based on depth
            if indent_level == 0:
                result += f"### Reply {reply.reply_number}\n\n"
            elif indent_level == 1:
                result += f"{indent}#### Reply {reply.reply_number}\n\n"
            else:
                result += f"{indent}##### Reply {reply.reply_number}\n\n"
            
            result += f"{indent}- **Author**: {reply.author.name} (@{reply.author.username})\n"
            if reply.author.rank:
                result += f"{indent}- **Rank**: {reply.author.rank}\n"
            if reply.author.badges:
                result += f"{indent}- **Badges**: {', '.join(reply.author.badges)}\n"
            result += f"{indent}- **Upvotes**: {reply.upvotes}\n"
            if reply.timestamp:
                result += f"{indent}- **Timestamp**: {reply.timestamp}\n"
            result += "\n"
            
            # Reply content
            for line in reply.content.split('\n'):
                result += f"{indent}{line}\n"
            result += "\n"
            
            # Add sub-replies
            for sub_reply in reply.sub_replies:
                result += format_reply(sub_reply, indent_level + 1)
            
            if indent_level == 0:
                result += "---\n\n"
            
            return result
        
        for reply in discussion.replies:
            content += format_reply(reply)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"   [SAVED] {output_file.name}")


async def extract_neurips_discussions(limit: Optional[int] = None):
    """
    Main function to extract NeurIPS discussions
    
    Args:
        limit: Number of discussions to extract. None = extract all
    """
    competition_url = "https://www.kaggle.com/competitions/neurips-open-polymer-prediction-2025"
    
    print("=" * 60)
    print("NeurIPS 2025 - FINAL Discussion Extractor")
    print("=" * 60)
    print(f"Competition: {competition_url}")
    print("Features:")
    print("  - No content duplication between parent/child replies")
    print("  - Proper hierarchy (Reply 1, 1.1, 1.2, etc.)")
    print("  - Standalone code (no external dependencies)")
    print("  - Dynamic extraction (configurable limit)")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            print("[LOADING] Competition page...")
            await page.goto(competition_url, wait_until="domcontentloaded")
            await asyncio.sleep(3)
            
            discussions_url = f"{competition_url}/discussion"
            print(f"[LOADING] Discussions page...")
            await page.goto(discussions_url, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            print("[SEARCHING] Finding discussion links across all pages...")
            discussion_links = []
            page_num = 1
            
            while True:
                # Load page with page number
                page_url = f"{discussions_url}?page={page_num}" if page_num > 1 else discussions_url
                print(f"[PAGE {page_num}] Loading discussions page...")
                await page.goto(page_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                # Get discussion links from current page
                all_links = await page.query_selector_all('a[href*="/discussion/"]')
                page_links = []
                
                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and '/discussion/' in href:
                        full_url = f"https://www.kaggle.com{href}" if href.startswith('/') else href
                        base_url = full_url.split('#')[0]
                        if not base_url.endswith('/discussion') and base_url not in discussion_links:
                            page_links.append(base_url)
                            discussion_links.append(base_url)
                
                print(f"[PAGE {page_num}] Found {len(page_links)} discussions")
                
                # Check if there's a next page
                next_button = await page.query_selector('button[aria-label="Go to next page"], a[aria-label="Go to next page"], [data-testid="pagination-next"]')
                
                # Also check if next button is disabled
                is_disabled = False
                if next_button:
                    is_disabled = await next_button.evaluate('el => el.disabled || el.classList.contains("disabled")')
                
                if not next_button or is_disabled or len(page_links) == 0:
                    print(f"[PAGINATION] Reached last page (page {page_num})")
                    break
                
                page_num += 1
                
                # Safety limit to prevent infinite loops
                if page_num > 50:
                    print("[WARNING] Reached maximum page limit (50)")
                    break
            
            # Remove duplicates while preserving order
            discussion_links = list(dict.fromkeys(discussion_links))
            
            if not discussion_links:
                print("[ERROR] No discussion links found!")
                return False
            
            print(f"[FOUND] {len(discussion_links)} unique discussions")
            
            # Apply limit if specified
            if limit:
                extract_count = min(limit, len(discussion_links))
                print(f"[LIMIT] Extracting {extract_count} discussions (user specified: {limit})")
            else:
                extract_count = len(discussion_links)
                print(f"[EXTRACTING] All {extract_count} discussions")
            
            # Create output directory
            output_dir = Path("NEURIPS_FINAL_EXTRACTION")
            if output_dir.exists():
                import shutil
                shutil.rmtree(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            print(f"\n[PROCESSING] Starting extraction...\n")
            
            successful_extractions = 0
            for i, url in enumerate(discussion_links[:extract_count], 1):
                print(f"[{i}/{extract_count}] Processing discussion...")
                
                try:
                    discussion = await extract_single_discussion(page, url)
                    
                    if discussion:
                        safe_title = re.sub(r'[<>:"/\\|?*]', '_', discussion.title[:50])
                        md_file = output_dir / f"{i:02d}_{safe_title}.md"
                        
                        save_discussion_markdown(discussion, md_file)
                        
                        successful_extractions += 1
                        
                        nested = sum(len(r.sub_replies) for r in discussion.replies)
                        if nested > 0:
                            print(f"   [STATS] {len(discussion.replies)} top-level, {nested} nested replies")
                        else:
                            print(f"   [STATS] {discussion.total_replies} replies total")
                        
                        await asyncio.sleep(2)
                    
                except Exception as e:
                    print(f"   [ERROR] {e}")
                    continue
                
                print()
            
            if successful_extractions > 0:
                print("=" * 60)
                print(f"[SUCCESS] Extracted {successful_extractions}/{extract_count} discussions")
                print(f"[OUTPUT] Files saved in: {output_dir.absolute()}")
                print("=" * 60)
                return True
            else:
                print("[FAILED] No discussions successfully extracted!")
                return False
                
        finally:
            await browser.close()


if __name__ == "__main__":
    # Check command line arguments
    import sys
    
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Extracting {limit} discussions as specified...")
        except ValueError:
            print(f"Invalid argument: {sys.argv[1]}")
            print("Usage: python neurips_extractor_final.py [number_of_discussions]")
            print("Example: python neurips_extractor_final.py 5")
            print("Or run without arguments to extract all discussions")
            sys.exit(1)
    else:
        limit = 4  # Default to 4 for testing
        print("No limit specified, extracting 4 discussions by default...")
    
    success = asyncio.run(extract_neurips_discussions(limit))
    
    if success:
        print("\n[COMPLETE] Extraction finished successfully!")
    else:
        print("\n[FAILED] Extraction failed!")