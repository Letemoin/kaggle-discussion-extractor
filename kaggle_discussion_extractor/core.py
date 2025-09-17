#!/usr/bin/env python3
"""
Kaggle Discussion Extractor - Core Module
Based on the working neurips_extractor_final.py with all functionality preserved
"""

import sys
import asyncio
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# Setup logging
logger = logging.getLogger(__name__)

# Check for playwright
try:
    from playwright.async_api import async_playwright, Page, ElementHandle
except ImportError:
    logger.error("playwright not installed. Please run: pip install playwright && playwright install chromium")
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


class KaggleDiscussionExtractor:
    """Main extractor class with all functionality from neurips_extractor_final.py"""
    
    def __init__(self, dev_mode: bool = False, headless: bool = True):
        """
        Initialize the extractor
        
        Args:
            dev_mode: Enable development mode with detailed logging
            headless: Run browser in headless mode
        """
        self.dev_mode = dev_mode
        self.headless = headless
        
        # Setup logging based on mode
        log_level = logging.DEBUG if dev_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        if dev_mode:
            logger.info("Development mode enabled - detailed logging active")
    
    async def extract_author_info(self, element) -> Author:
        """Extract detailed author information with proper display names and ranking"""
        try:
            # Find author link and extract username
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

            # Get display name from link text (this is the actual display name)
            display_name = username  # fallback
            link_text = await author_link.text_content()
            if link_text and link_text.strip():
                display_name = link_text.strip()

            # Enhanced rank extraction - multiple strategies
            rank = None
            try:
                # Get full text content for better rank detection
                full_text = await element.text_content()
                element_html = await element.inner_html()

                # Strategy 1: Look for "Xth in this Competition" pattern
                rank_patterns = [
                    r'(\d+)(?:st|nd|rd|th)\s+in\s+this\s+Competition',
                    r'(\d+)(?:st|nd|rd|th)\s+in\s+Competition',
                    r'(\d+)(?:st|nd|rd|th)\s+place',
                    r'Rank\s*[:#]?\s*(\d+)',
                    r'#(\d+)\s+in\s+competition'
                ]

                for pattern in rank_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        rank_num = int(match.group(1))
                        # Add proper ordinal suffix
                        if rank_num % 10 == 1 and rank_num % 100 != 11:
                            suffix = "st"
                        elif rank_num % 10 == 2 and rank_num % 100 != 12:
                            suffix = "nd"
                        elif rank_num % 10 == 3 and rank_num % 100 != 13:
                            suffix = "rd"
                        else:
                            suffix = "th"
                        rank = f"{rank_num}{suffix} in this Competition"
                        break

                    # Also check HTML content
                    match = re.search(pattern, element_html, re.IGNORECASE)
                    if match:
                        rank_num = int(match.group(1))
                        # Add proper ordinal suffix
                        if rank_num % 10 == 1 and rank_num % 100 != 11:
                            suffix = "st"
                        elif rank_num % 10 == 2 and rank_num % 100 != 12:
                            suffix = "nd"
                        elif rank_num % 10 == 3 and rank_num % 100 != 13:
                            suffix = "rd"
                        else:
                            suffix = "th"
                        rank = f"{rank_num}{suffix} in this Competition"
                        break

            except Exception as rank_err:
                if self.dev_mode:
                    logger.debug(f"Rank extraction failed: {rank_err}")

            # Extract badges with improved detection
            badges = []
            try:
                badge_elements = await element.query_selector_all('span, div')
                for elem in badge_elements:
                    text = await elem.text_content()
                    if text:
                        text = text.strip()
                        # Look for Kaggle tier badges
                        badge_keywords = ['Host', 'Expert', 'Master', 'Grandmaster', 'Contributor', 'Novice']
                        for badge_word in badge_keywords:
                            if badge_word.lower() in text.lower() and len(text) < 30:  # Avoid long content
                                if text not in badges:
                                    badges.append(text)
                                    break
            except Exception as badge_err:
                if self.dev_mode:
                    logger.debug(f"Badge extraction failed: {badge_err}")

            return Author(
                name=display_name,  # Use display name instead of username
                username=username,
                rank=rank,
                badges=badges if badges else None,
                profile_url=f"https://www.kaggle.com/{username}"
            )

        except Exception as e:
            if self.dev_mode:
                logger.warning(f"Error extracting author: {e}")
            return Author(name="Unknown", username="unknown")

    async def extract_upvotes(self, element) -> int:
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

    async def extract_comment_content(self, element, author_username: str) -> str:
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
            if self.dev_mode:
                logger.warning(f"Error extracting content: {e}")
            return ""

    async def extract_hierarchical_replies(self, page: Page) -> List[Reply]:
        """Extract replies with proper hierarchical numbering and content separation"""
        replies = []

        try:
            # Get ALL comment elements
            all_comments = await page.query_selector_all('div[data-testid="discussions-comment"]')

            if not all_comments:
                if self.dev_mode:
                    logger.debug("No comment elements found")
                return replies

            if self.dev_mode:
                logger.debug(f"Found {len(all_comments)} total comment elements")

            processed_comments = []

            # First pass: identify hierarchy with better nesting detection
            for i, comment_elem in enumerate(all_comments):
                try:
                    # Enhanced hierarchy detection using DOM structure and visual cues
                    hierarchy_info = await comment_elem.evaluate('''
                        (element) => {
                            let depth = 0;
                            let current = element;
                            let isNested = false;

                            // Check for visual indentation or padding indicators
                            const rect = element.getBoundingClientRect();
                            const computedStyle = window.getComputedStyle(element);
                            const marginLeft = parseInt(computedStyle.marginLeft) || 0;
                            const paddingLeft = parseInt(computedStyle.paddingLeft) || 0;

                            // Method 1: Check parent containers for nesting patterns
                            while (current && current.parentElement) {
                                current = current.parentElement;
                                const classes = current.className || '';

                                // Look for reply container patterns
                                if (classes.includes('reply') ||
                                    classes.includes('nested') ||
                                    classes.includes('thread') ||
                                    current.getAttribute('data-testid') === 'discussions-comment') {
                                    depth++;
                                }

                                // Safety limit
                                if (depth > 5) break;
                            }

                            // Method 2: Check visual indentation (replies are usually indented)
                            const totalIndent = marginLeft + paddingLeft;
                            if (totalIndent > 40) { // Threshold for nested replies
                                isNested = true;
                                if (depth === 0) depth = Math.floor(totalIndent / 40);
                            }

                            // Method 3: Check for "Reply" button proximity to determine if this is a response
                            const replyButtons = element.querySelectorAll('button');
                            let hasReplyButton = false;
                            for (let btn of replyButtons) {
                                if (btn.textContent && btn.textContent.toLowerCase().includes('reply')) {
                                    hasReplyButton = true;
                                    break;
                                }
                            }

                            // If we found visual indicators but no depth, set depth to 1
                            if (isNested && depth === 0) {
                                depth = 1;
                            }

                            return {
                                depth: Math.max(0, depth),
                                isNested: depth > 0 || isNested,
                                visualIndent: totalIndent,
                                hasReplyButton: hasReplyButton
                            };
                        }
                    ''')

                    # Extract author first to get username
                    author = await self.extract_author_info(comment_elem)

                    if author.username == "unknown":
                        continue

                    # Extract content specific to this comment only
                    content = await self.extract_comment_content(comment_elem, author.username)

                    if not content or len(content.strip()) < 5:
                        continue

                    # Extract other metadata
                    upvotes = await self.extract_upvotes(comment_elem)

                    timestamp = ""
                    time_elem = await comment_elem.query_selector('span[title]')
                    if time_elem:
                        timestamp = await time_elem.get_attribute('title') or ""

                    processed_comments.append({
                        'author': author,
                        'content': content,
                        'upvotes': upvotes,
                        'timestamp': timestamp,
                        'depth': hierarchy_info['depth'],
                        'is_nested': hierarchy_info['isNested'],
                        'visual_indent': hierarchy_info['visualIndent'],
                        'original_idx': i
                    })

                except Exception as e:
                    if self.dev_mode:
                        logger.warning(f"Error processing comment {i}: {e}")
                    continue

            if self.dev_mode:
                logger.debug(f"Processed {len(processed_comments)} valid comments")
                # Debug: Show hierarchy detection results
                for i, comment in enumerate(processed_comments):
                    logger.debug(f"Comment {i}: depth={comment['depth']}, nested={comment['is_nested']}, indent={comment.get('visual_indent', 0)}, author={comment['author'].name}")

            # Build hierarchical structure with proper numbering
            return self._build_reply_hierarchy(processed_comments)

        except Exception as e:
            logger.error(f"Error extracting replies: {e}")
            return []

    def _build_reply_hierarchy(self, processed_comments: List[Dict]) -> List[Reply]:
        """Build proper hierarchical reply structure with correct numbering - FIXED VERSION"""
        if not processed_comments:
            return []

        # Create reply objects
        reply_objects = []
        for data in processed_comments:
            reply = Reply(
                reply_number="",
                content=data['content'],
                author=data['author'],
                upvotes=data['upvotes'],
                timestamp=data['timestamp'],
                depth=data['depth']
            )
            reply_objects.append(reply)

        # Build hierarchy using a stack-based approach with FIXED numbering
        reply_stack = []  # Stack to track parent chain
        top_level_replies = []
        depth_counters = {}  # Track counters for each depth level

        for i, reply in enumerate(reply_objects):
            current_depth = processed_comments[i]['depth']

            # Adjust stack to current depth
            while len(reply_stack) > current_depth:
                popped = reply_stack.pop()
                # Reset deeper counters when going back up
                for d in list(depth_counters.keys()):
                    if d > len(reply_stack):
                        del depth_counters[d]

            if current_depth == 0:
                # Top-level reply
                top_level_replies.append(reply)
                reply_stack = [reply]
                reply.reply_number = str(len(top_level_replies))
                depth_counters[0] = len(top_level_replies)

            else:
                # Nested reply
                if reply_stack and len(reply_stack) >= current_depth:
                    parent_reply = reply_stack[-1]

                    # Add to parent's sub_replies
                    parent_reply.sub_replies.append(reply)
                    reply_stack.append(reply)

                    # FIXED: Generate hierarchical number correctly
                    number_parts = []

                    # Build number from the stack path
                    for depth_level in range(current_depth + 1):
                        if depth_level == 0:
                            # Top-level number
                            number_parts.append(str(depth_counters.get(0, 1)))
                        else:
                            # Count position in parent's sub_replies
                            if depth_level <= len(reply_stack) - 1:
                                parent_at_level = reply_stack[depth_level - 1]
                                position = len(parent_at_level.sub_replies)
                                number_parts.append(str(position))

                    reply.reply_number = ".".join(number_parts)

                else:
                    # Fallback: treat as top-level if stack is inconsistent
                    top_level_replies.append(reply)
                    reply_stack = [reply]
                    reply.reply_number = str(len(top_level_replies))
                    depth_counters[0] = len(top_level_replies)

        if self.dev_mode:
            total_nested = sum(self._count_all_replies([r]) - 1 for r in top_level_replies)
            logger.info(f"Built hierarchy: {len(top_level_replies)} top-level, {total_nested} nested replies")

        return top_level_replies

    async def extract_single_discussion(self, page: Page, url: str) -> Optional[Discussion]:
        """Extract a single discussion or writeup with all replies"""
        try:
            # Detect if this is a writeup URL
            is_writeup = '/writeups/' in url

            if self.dev_mode:
                content_type = "writeup" if is_writeup else "discussion"
                logger.debug(f"Loading {content_type}: {url.split('/')[-1]}")

            await page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)  # Give writeups more time to load
            
            # Get title with improved extraction for both discussions and writeups
            title = "Unknown Title"

            if is_writeup:
                # Writeup-specific title extraction
                writeup_title_selectors = [
                    'h1[class*="writeup"]',
                    'h1[class*="solution"]',
                    'h1',
                    'h2',
                    'title',  # From page title
                    '[data-testid*="writeup"]',
                    '[data-testid*="solution"]'
                ]

                # Try to get from page title first for writeups
                page_title = await page.title()
                if page_title and '|' in page_title:
                    writeup_title = page_title.split('|')[0].strip()
                    if writeup_title and writeup_title != "Kaggle":
                        title = writeup_title

                # If page title didn't work, try DOM selectors
                if title == "Unknown Title":
                    for selector in writeup_title_selectors:
                        title_elem = await page.query_selector(selector)
                        if title_elem:
                            text = await title_elem.text_content()
                            if text and text.strip():
                                if not any(skip in text.lower() for skip in ['kaggle', 'competition']):
                                    title = text.strip()
                                    break

                # Extract from URL for writeups (e.g., "2nd-place-solution")
                if title == "Unknown Title":
                    url_parts = url.split('/')
                    if 'writeups' in url_parts:
                        writeup_idx = url_parts.index('writeups')
                        if writeup_idx + 1 < len(url_parts):
                            url_title = url_parts[writeup_idx + 1]
                            # Convert URL format to readable title
                            title = url_title.replace('-', ' ').title()
            else:
                # Discussion-specific title extraction
                discussion_title_selectors = [
                    'h1[class*="title"]',
                    'h1[class*="topic"]',
                    'h1',
                    'h2[class*="title"]',
                    'h2',
                    'h3[class*="kvnevz"]',
                    '[data-testid*="title"]',
                    '[data-testid*="topic"]'
                ]

                for selector in discussion_title_selectors:
                    title_elem = await page.query_selector(selector)
                    if title_elem:
                        text = await title_elem.text_content()
                        if text and text.strip():
                            # Skip generic competition titles
                            if not any(skip in text.lower() for skip in ['cmi - detect behavior', 'kaggle']):
                                title = text.strip()
                                break
                            elif title == "Unknown Title":  # Keep as fallback
                                title = text.strip()

                # If we still have a generic title, try to get it from the URL or page
                if title in ["Unknown Title", "CMI - Detect Behavior with Sensor Data"]:
                    # Try to extract from URL path
                    url_parts = url.split('/')
                    if len(url_parts) > 2 and url_parts[-1].isdigit():
                        # Look for discussion-specific content
                        specific_elements = await page.query_selector_all('[class*="discussion"], [class*="topic"], [class*="thread"]')
                        for elem in specific_elements:
                            text = await elem.text_content()
                            if text and len(text.strip()) > 10 and len(text.strip()) < 200:
                                lines = text.strip().split('\n')
                                if lines and len(lines[0]) > 5:
                                    title = lines[0].strip()
                                    break
            
            # Get main post content - different approach for writeups vs discussions
            main_content = ""
            main_author = Author(name="Unknown", username="unknown")
            main_upvotes = 0

            if is_writeup:
                # Writeup-specific content extraction
                writeup_selectors = [
                    'div[class*="writeup"]',
                    'div[class*="solution"]',
                    'article[class*="writeup"]',
                    'article',
                    'div[class*="content"]',
                    'div[class*="post"]',
                    'div[class*="body"]',
                    '[data-testid*="writeup"]',
                    '[data-testid*="content"]'
                ]

                # Try to find writeup content
                for selector in writeup_selectors:
                    main_elem = await page.query_selector(selector)
                    if main_elem:
                        # Extract author info
                        main_author = await self.extract_author_info(main_elem)
                        main_upvotes = await self.extract_upvotes(main_elem)

                        # Extract writeup content
                        content_text = await main_elem.text_content()
                        if content_text and len(content_text.strip()) > 100:  # Writeups should have substantial content
                            main_content = content_text.strip()
                            break

                # Special handling for writeup author if not found
                if main_author.name == "Unknown":
                    # Try to find author in the writeup page structure
                    author_selectors = [
                        '[class*="author"]',
                        '[data-testid*="author"]',
                        'div[class*="user"]',
                        'a[href^="/"]'  # Look for any profile links
                    ]

                    for selector in author_selectors:
                        author_elements = await page.query_selector_all(selector)
                        for elem in author_elements:
                            author = await self.extract_author_info(elem)
                            if author.name != "Unknown":
                                main_author = author
                                break
                        if main_author.name != "Unknown":
                            break

                # INNOVATIVE Multi-User Writeup Author Detection System
                if main_author.name == "Unknown":
                    # Advanced multi-author detection for team writeups
                    target_placement = None
                    if "1st" in title.lower() or "first" in title.lower():
                        target_placement = ["1st", "first"]
                    elif "2nd" in title.lower() or "second" in title.lower():
                        target_placement = ["2nd", "second"]
                    elif "3rd" in title.lower() or "third" in title.lower():
                        target_placement = ["3rd", "third"]

                    if self.dev_mode:
                        logger.debug(f"INNOVATIVE: Multi-user writeup detection for placement: {target_placement}")

                    comment_elements = await page.query_selector_all('div[data-testid="discussions-comment"]')

                    # STEP 1: Collect all potential team members with target ranking
                    team_candidates = []
                    all_authors = []

                    if comment_elements and target_placement:
                        for comment in comment_elements:
                            author = await self.extract_author_info(comment)
                            if author.name != "Unknown":
                                all_authors.append(author)

                                if author.rank:
                                    # Check for exact placement match
                                    for placement in target_placement:
                                        exact_pattern = f"{placement} in this competition"
                                        if exact_pattern in author.rank.lower():
                                            team_candidates.append(author)
                                            if self.dev_mode:
                                                logger.debug(f"TEAM MEMBER: {author.name} ({author.rank})")
                                            break

                    # STEP 2: Multi-author writeup handling
                    if len(team_candidates) > 1:
                        # Multiple team members found - create composite author
                        primary_author = team_candidates[0]  # Use first found as primary
                        team_names = [author.name for author in team_candidates]
                        team_ranks = [author.rank for author in team_candidates if author.rank]

                        # Create composite author representation
                        composite_name = " & ".join(team_names[:3])  # Show up to 3 names
                        if len(team_names) > 3:
                            composite_name += f" + {len(team_names) - 3} others"

                        primary_author.name = composite_name
                        primary_author.rank = f"Team: {', '.join(team_ranks[:2])}" if len(team_ranks) > 1 else team_ranks[0] if team_ranks else None

                        main_author = primary_author

                        if self.dev_mode:
                            logger.debug(f"MULTI-USER WRITEUP: {composite_name}")

                    elif len(team_candidates) == 1:
                        # Single author with exact match
                        main_author = team_candidates[0]
                        if self.dev_mode:
                            logger.debug(f"SINGLE AUTHOR: {main_author.name} ({main_author.rank})")

                    # STEP 3: Fallback strategies for complex cases
                    if main_author.name == "Unknown" and all_authors:
                        # Strategy A: Look for authors with target placement in broader context
                        for author in all_authors:
                            if author.rank and target_placement:
                                for placement in target_placement:
                                    if placement in author.rank.lower():
                                        main_author = author
                                        if self.dev_mode:
                                            logger.debug(f"FALLBACK A: {author.name} ({author.rank})")
                                        break
                                if main_author.name != "Unknown":
                                    break

                        # Strategy B: Use highest-ranked person as proxy
                        if main_author.name == "Unknown":
                            best_author = None
                            best_rank_num = float('inf')

                            for author in all_authors:
                                if author.rank:
                                    rank_match = re.search(r'(\d+)(?:st|nd|rd|th)', author.rank)
                                    if rank_match:
                                        rank_num = int(rank_match.group(1))
                                        if rank_num < best_rank_num:
                                            best_rank_num = rank_num
                                            best_author = author

                            if best_author:
                                main_author = best_author
                                if self.dev_mode:
                                    logger.debug(f"FALLBACK B: Highest ranked {best_author.name} ({best_author.rank})")

                    # STEP 4: Multi-author content attribution
                    if main_author.name != "Unknown" and len(team_candidates) > 1:
                        # Add team composition to content for transparency
                        team_info = f"\n\n**Team Composition:**\n"
                        for i, member in enumerate(team_candidates, 1):
                            team_info += f"- {member.name} ({member.rank})\n"

                        if main_content:
                            main_content = team_info + "\n" + main_content
                        else:
                            main_content = team_info

                # Enhanced content extraction for writeups
                if not main_content:
                    # Look for writeup content more systematically
                    all_text = await page.evaluate('document.body.textContent')
                    if all_text and len(all_text.strip()) > 100:
                        # Find the main writeup content by looking for the start pattern
                        # From our debug, writeups start with "First, thanks to the organizers..."

                        # Clean the text
                        clean_text = re.sub(r'[^\x00-\x7F]+', ' ', all_text)  # Remove non-ASCII
                        lines = clean_text.split('\n')

                        # Find where the actual writeup content starts
                        content_start_idx = None
                        content_lines = []

                        for i, line in enumerate(lines):
                            line = line.strip()

                            # Look for writeup start indicators
                            if any(start_phrase in line.lower() for start_phrase in [
                                'first, thanks to the organizers',
                                'overview',
                                'if you watched the leaderboard',
                                'thanks to the organizers'
                            ]):
                                content_start_idx = i
                                break

                        # If we found the start, extract from there
                        if content_start_idx is not None:
                            for line in lines[content_start_idx:]:
                                line = line.strip()
                                if len(line) > 10 and not any(skip in line.lower() for skip in [
                                    'kaggle', 'navigation', 'menu', 'search', 'sign in', 'register',
                                    'skip to content', 'home', 'competitions', 'datasets', 'models'
                                ]):
                                    content_lines.append(line)

                                # Stop when we reach the comments section
                                if 'comments' in line.lower() or 'discussion' in line.lower():
                                    if len(content_lines) > 10:  # Only stop if we have substantial content
                                        break

                        else:
                            # Fallback: extract meaningful content from anywhere
                            for line in lines:
                                line = line.strip()
                                if len(line) > 20 and not any(skip in line.lower() for skip in [
                                    'kaggle', 'navigation', 'menu', 'search', 'sign in', 'register',
                                    'skip to content', 'home', 'competitions', 'datasets', 'models'
                                ]):
                                    content_lines.append(line)

                        if content_lines:
                            # Take substantial amount of content for writeups
                            main_content = '\n'.join(content_lines[:50])  # More content for writeups

            else:
                # Discussion-specific content extraction
                discussion_selectors = [
                    'div[data-testid="discussions-topic-header"]',
                    'div[class*="topic-header"]',
                    'article:first-of-type'
                ]

                for selector in discussion_selectors:
                    main_elem = await page.query_selector(selector)
                    if main_elem:
                        main_author = await self.extract_author_info(main_elem)
                        main_upvotes = await self.extract_upvotes(main_elem)

                        # Extract main content
                        content_elem = await main_elem.query_selector('div[class*="eTCgfj"], div[class*="jMpVQY"]')
                        if content_elem:
                            main_content = await content_elem.text_content()
                            if main_content:
                                main_content = main_content.strip()
                                break
            
            if self.dev_mode:
                logger.debug(f"Author: {main_author.name} (@{main_author.username})")
                if main_author.rank:
                    logger.debug(f"Rank: {main_author.rank}")
            
            # Extract replies with proper content separation
            replies = await self.extract_hierarchical_replies(page)
            
            return Discussion(
                title=title,
                url=url,
                main_content=main_content,
                main_author=main_author,
                main_upvotes=main_upvotes,
                replies=replies,
                total_replies=self._count_all_replies(replies),
                extraction_time=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error extracting discussion: {e}")
            return None

    def _count_all_replies(self, replies: List[Reply]) -> int:
        """Count all replies including sub-replies recursively"""
        count = 0
        for reply in replies:
            count += 1
            count += self._count_all_replies(reply.sub_replies)
        return count

    def save_discussion_markdown(self, discussion: Discussion, output_file: Path):
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
        
        if self.dev_mode:
            logger.debug(f"Saved: {output_file.name}")

    async def extract_competition_writeups(self, competition_url: str, limit: Optional[int] = None) -> bool:
        """
        Extract all writeups from a Kaggle competition

        Args:
            competition_url: Full URL to the Kaggle competition
            limit: Number of writeups to extract (None = all)

        Returns:
            bool: Success status
        """
        logger.info(f"Starting writeup extraction for: {competition_url}")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()

            try:
                # Load competition page
                await page.goto(competition_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

                writeups_url = f"{competition_url}/writeups"
                await page.goto(writeups_url, wait_until="domcontentloaded")
                await asyncio.sleep(5)

                # Get writeup links
                writeup_links = []

                # Look for writeup links
                all_links = await page.query_selector_all('a[href*="/writeups/"]')

                for link in all_links:
                    href = await link.get_attribute('href')
                    if href and '/writeups/' in href:
                        full_url = f"https://www.kaggle.com{href}" if href.startswith('/') else href
                        base_url = full_url.split('#')[0]
                        if not base_url.endswith('/writeups') and base_url not in writeup_links:
                            writeup_links.append(base_url)

                if not writeup_links:
                    logger.error("No writeup links found!")
                    return False

                logger.info(f"Found {len(writeup_links)} writeups")

                # Apply limit if specified
                extract_count = min(limit, len(writeup_links)) if limit else len(writeup_links)
                logger.info(f"Extracting {extract_count} writeups")

                # Create output directory
                output_dir = Path("kaggle_writeups_extracted")
                if output_dir.exists():
                    import shutil
                    shutil.rmtree(output_dir)
                output_dir.mkdir(exist_ok=True)

                successful_extractions = 0
                for i, url in enumerate(writeup_links[:extract_count], 1):
                    logger.info(f"[{i}/{extract_count}] Processing writeup...")

                    try:
                        writeup = await self.extract_single_discussion(page, url)  # Reuse discussion method

                        if writeup:
                            # Create a clean filename with the writeup title
                            safe_title = re.sub(r'[<>:"/\\|?*]', '_', writeup.title)
                            # Limit filename length but keep meaningful parts
                            if len(safe_title) > 100:
                                safe_title = safe_title[:97] + "..."
                            md_file = output_dir / f"{i:02d}_{safe_title}.md"

                            self.save_discussion_markdown(writeup, md_file)

                            successful_extractions += 1

                            nested = sum(len(r.sub_replies) for r in writeup.replies)
                            if nested > 0:
                                logger.info(f"   Stats: {len(writeup.replies)} top-level, {nested} nested replies")
                            else:
                                logger.info(f"   Stats: {writeup.total_replies} replies total")

                            await asyncio.sleep(2)

                    except Exception as e:
                        logger.error(f"   Error: {e}")
                        continue

                if successful_extractions > 0:
                    logger.info(f"SUCCESS: Extracted {successful_extractions}/{extract_count} writeups")
                    logger.info(f"Output saved in: {output_dir.absolute()}")
                    return True
                else:
                    logger.error("No writeups successfully extracted!")
                    return False

            finally:
                await browser.close()

    async def extract_competition_discussions(self, competition_url: str, limit: Optional[int] = None) -> bool:
        """
        Extract all discussions from a Kaggle competition
        
        Args:
            competition_url: Full URL to the Kaggle competition
            limit: Number of discussions to extract (None = all)
            
        Returns:
            bool: Success status
        """
        logger.info(f"Starting extraction for: {competition_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # Load competition page
                await page.goto(competition_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)
                
                discussions_url = f"{competition_url}/discussion"
                await page.goto(discussions_url, wait_until="domcontentloaded")
                await asyncio.sleep(5)
                
                # Get discussion links from all pages
                discussion_links = []
                page_num = 1
                
                while True:
                    page_url = f"{discussions_url}?page={page_num}" if page_num > 1 else discussions_url
                    if self.dev_mode:
                        logger.debug(f"Loading page {page_num}: {page_url}")
                    
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
                    
                    if self.dev_mode:
                        logger.debug(f"Page {page_num}: Found {len(page_links)} discussions")
                    
                    # Check if there's a next page
                    next_button = await page.query_selector('button[aria-label="Go to next page"], a[aria-label="Go to next page"], [data-testid="pagination-next"]')
                    
                    is_disabled = False
                    if next_button:
                        is_disabled = await next_button.evaluate('el => el.disabled || el.classList.contains("disabled")')
                    
                    if not next_button or is_disabled or len(page_links) == 0:
                        if self.dev_mode:
                            logger.debug(f"Reached last page (page {page_num})")
                        break
                    
                    page_num += 1
                    
                    # Safety limit
                    if page_num > 50:
                        logger.warning("Reached maximum page limit (50)")
                        break
                
                discussion_links = list(dict.fromkeys(discussion_links))
                
                if not discussion_links:
                    logger.error("No discussion links found!")
                    return False
                
                logger.info(f"Found {len(discussion_links)} unique discussions")
                
                # Apply limit if specified
                extract_count = min(limit, len(discussion_links)) if limit else len(discussion_links)
                logger.info(f"Extracting {extract_count} discussions")
                
                # Create output directory
                output_dir = Path("kaggle_discussions_extracted")
                if output_dir.exists():
                    import shutil
                    shutil.rmtree(output_dir)
                output_dir.mkdir(exist_ok=True)
                
                successful_extractions = 0
                for i, url in enumerate(discussion_links[:extract_count], 1):
                    logger.info(f"[{i}/{extract_count}] Processing discussion...")
                    
                    try:
                        discussion = await self.extract_single_discussion(page, url)
                        
                        if discussion:
                            # Create a clean filename with the discussion title
                            safe_title = re.sub(r'[<>:"/\\|?*]', '_', discussion.title)
                            # Limit filename length but keep meaningful parts
                            if len(safe_title) > 100:
                                safe_title = safe_title[:97] + "..."
                            md_file = output_dir / f"{i:02d}_{safe_title}.md"

                            self.save_discussion_markdown(discussion, md_file)
                            
                            successful_extractions += 1
                            
                            nested = sum(len(r.sub_replies) for r in discussion.replies)
                            if nested > 0:
                                logger.info(f"   Stats: {len(discussion.replies)} top-level, {nested} nested replies")
                            else:
                                logger.info(f"   Stats: {discussion.total_replies} replies total")
                            
                            await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"   Error: {e}")
                        continue
                
                if successful_extractions > 0:
                    logger.info(f"SUCCESS: Extracted {successful_extractions}/{extract_count} discussions")
                    logger.info(f"Output saved in: {output_dir.absolute()}")
                    return True
                else:
                    logger.error("No discussions successfully extracted!")
                    return False
                    
            finally:
                await browser.close()