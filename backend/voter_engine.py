"""
Core Voting Engine for CloudVoter
Adapted from brightdatavoter.py for web-based deployment
"""

import asyncio
import json
import logging
import os
import random
import re
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from playwright.async_api import async_playwright
from vote_logger import VoteLogger
from config import (
    ENABLE_RESOURCE_BLOCKING, BLOCK_IMAGES, BLOCK_STYLESHEETS, 
    BLOCK_FONTS, BLOCK_TRACKING, BROWSER_LAUNCH_DELAY, MAX_CONCURRENT_BROWSER_LAUNCHES,
    FAILURE_PATTERNS, RETRY_DELAY_TECHNICAL, RETRY_DELAY_COOLDOWN,
    GLOBAL_HOURLY_LIMIT_PATTERNS, INSTANCE_COOLDOWN_PATTERNS,
    PROXY_MAX_RETRIES, PROXY_RETRY_DELAY, PROXY_503_CIRCUIT_BREAKER_THRESHOLD,
    PROXY_503_PAUSE_DURATION, SESSION_SCAN_INTERVAL
)

logger = logging.getLogger(__name__)

class BrightDataAPI:
    """API wrapper for Bright Data proxy management"""
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.proxy_host = 'brd.superproxy.io'
        self.proxy_port = 33335  # Datacenter port
        self.zone = 'datacenter_proxy1'  # Datacenter zone
        
    def get_proxy_auth(self) -> str:
        """Get proxy authentication string"""
        return f"brd-customer-{self.username}-zone-{self.zone}-country-in:{self.password}"
    
    def get_proxy_url(self) -> str:
        """Get proxy URL"""
        return f"http://{self.proxy_host}:{self.proxy_port}"
    
    async def test_connection(self) -> bool:
        """Test proxy connection"""
        try:
            import urllib.request
            
            proxy_auth = self.get_proxy_auth()
            proxy = f'http://{proxy_auth}@{self.proxy_host}:{self.proxy_port}'
            
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
            )
            
            response = opener.open('https://geo.brdtest.com/welcome.txt?product=dc&method=native')
            result = response.read().decode()
            
            logger.info(f"[PROXY] Bright Data connection successful: {result.strip()}")
            return True
                
        except Exception as e:
            logger.error(f"[PROXY] Bright Data connection test failed: {e}")
            return False

class VoterInstance:
    """Individual voting instance with browser automation"""
    
    def __init__(self, proxy_ip: str, proxy_config: dict, instance_id: int, target_url: str, voter_manager=None):
        self.proxy_ip = proxy_ip
        self.proxy_config = proxy_config
        self.instance_id = instance_id
        self.target_url = target_url
        self.voter_manager = voter_manager
        
        # Browser state
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # Instance state
        self.status = "Initializing"
        self.is_paused = False
        self.waiting_for_login = False
        self.login_required = False
        self.pause_event = asyncio.Event()
        self.pause_event.set()
        
        # Session management
        self.session_id = None
        self.session_dir = f"brightdata_session_data/instance_{instance_id}"
        
        # Voting state
        self.last_vote_time = None
        self.last_successful_vote = None  # Timestamp of last successful vote
        self.last_attempted_vote = None   # Timestamp of last vote attempt (success or fail)
        self.last_failure_reason = None   # Reason for last failed vote attempt
        self.last_failure_type = None     # Type of failure: "ip_cooldown" or "technical"
        self.vote_count = 0
        self.failed_attempts = 0
        
        # Vote logger
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file_path = os.path.join(project_root, "voting_logs.csv")
        self.vote_logger = VoteLogger(log_file=log_file_path)
        
        # Resource blocking control (from config)
        self.enable_resource_blocking = ENABLE_RESOURCE_BLOCKING
        self.block_images = BLOCK_IMAGES
        self.block_stylesheets = BLOCK_STYLESHEETS
        self.block_fonts = BLOCK_FONTS
        self.block_tracking = BLOCK_TRACKING
    
    def get_time_until_next_vote(self) -> dict:
        """
        Calculate time remaining until next vote or retry.
        Returns dict with seconds_remaining and next_vote_time.
        
        Handles both:
        - Successful votes: 31 minute cooldown
        - Failed votes: 5 min (technical) or 31 min (IP cooldown) retry delay
        """
        current_time = datetime.now()
        
        # Check if there's a recent failure that needs retry
        if self.last_attempted_vote and self.last_failure_type:
            # Determine retry delay based on failure type
            if self.last_failure_type == "technical":
                retry_minutes = RETRY_DELAY_TECHNICAL  # 5 minutes
                retry_label = "retry"
            else:  # ip_cooldown
                retry_minutes = RETRY_DELAY_COOLDOWN  # 31 minutes
                retry_label = "cooldown"
            
            # Calculate next retry time
            next_retry_time = self.last_attempted_vote + timedelta(minutes=retry_minutes)
            time_diff = (next_retry_time - current_time).total_seconds()
            retry_seconds = max(0, int(time_diff))
            
            # If we have both successful vote and failed attempt, use whichever is later
            if self.last_vote_time:
                next_vote_time = self.last_vote_time + timedelta(minutes=31)
                vote_time_diff = (next_vote_time - current_time).total_seconds()
                vote_seconds = max(0, int(vote_time_diff))
                
                # Use the longer wait time
                if retry_seconds > vote_seconds:
                    return {
                        'seconds_remaining': retry_seconds,
                        'next_vote_time': next_retry_time.isoformat(),
                        'status': f'{retry_label}_retry' if retry_seconds > 0 else 'ready',
                        'retry_type': self.last_failure_type
                    }
                else:
                    return {
                        'seconds_remaining': vote_seconds,
                        'next_vote_time': next_vote_time.isoformat(),
                        'status': 'cooldown' if vote_seconds > 0 else 'ready',
                        'retry_type': None
                    }
            else:
                # Only failed attempt, no successful vote yet
                return {
                    'seconds_remaining': retry_seconds,
                    'next_vote_time': next_retry_time.isoformat(),
                    'status': f'{retry_label}_retry' if retry_seconds > 0 else 'ready',
                    'retry_type': self.last_failure_type
                }
        
        # No failure, check for successful vote cooldown
        if self.last_vote_time:
            # Calculate next vote time (31 minutes after last vote)
            next_vote_time = self.last_vote_time + timedelta(minutes=31)
            time_diff = (next_vote_time - current_time).total_seconds()
            seconds_remaining = max(0, int(time_diff))
            
            return {
                'seconds_remaining': seconds_remaining,
                'next_vote_time': next_vote_time.isoformat(),
                'status': 'cooldown' if seconds_remaining > 0 else 'ready',
                'retry_type': None
            }
        
        # No vote history and no failures - ready to vote
        return {
            'seconds_remaining': 0,
            'next_vote_time': None,
            'status': 'ready',
            'retry_type': None
        }
    
    async def _handle_resource_blocking(self, route):
        """
        Block unnecessary resources to reduce page load size and improve performance.
        
        Benefits:
        - Reduces page load size by 60-80%
        - Faster page loading times
        - Lower bandwidth usage
        - Reduced memory consumption
        - Blocks tracking and analytics scripts
        - Maintains voting functionality while removing visual elements
        """
        request = route.request
        resource_type = request.resource_type
        url = request.url
        
        # Block resource types based on configuration
        blocked_types = set()
        
        if self.block_images:
            blocked_types.add('image')  # Images (jpg, png, gif, svg, etc.)
            
        if self.block_stylesheets:
            blocked_types.add('stylesheet')  # CSS files
            
        if self.block_fonts:
            blocked_types.add('font')  # Font files
            
        # Always block these resource types as they're not needed for voting
        blocked_types.update({
            'media',          # Video/audio files
            'websocket',      # WebSocket connections
            'eventsource',    # Server-sent events
            'manifest',       # Web app manifests
            'texttrack',      # Video text tracks
        })
        
        # Block specific domains/patterns based on configuration
        blocked_domains = []
        
        if self.block_tracking:
            blocked_domains.extend([
                'googletagmanager.com',
                'google-analytics.com',
                'googleadservices.com',
                'googlesyndication.com',
                'doubleclick.net',
                'facebook.com/tr',
                'facebook.net',
                'twitter.com/i/adsct',
                'analytics.',
                'tracking.',
                'ads.',
            ])
        
        # Block specific file extensions based on configuration
        blocked_extensions = []
        
        if self.block_images:
            blocked_extensions.extend(['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.ico'])
            
        if self.block_stylesheets:
            blocked_extensions.append('.css')
            
        if self.block_fonts:
            blocked_extensions.extend(['.woff', '.woff2', '.ttf', '.otf', '.eot'])
            
        # Always block these file types as they're not needed for voting
        blocked_extensions.extend([
            '.mp4', '.mp3', '.avi', '.mov', '.webm',  # Media files
            '.pdf', '.doc', '.docx', '.zip',  # Documents
        ])
        
        # Check if resource should be blocked
        should_block = False
        
        # Block by resource type
        if resource_type in blocked_types:
            should_block = True
            logger.debug(f"[RESOURCE_BLOCK] Blocking {resource_type}: {url}")
        
        # Block by domain
        elif any(domain in url.lower() for domain in blocked_domains):
            should_block = True
            logger.debug(f"[RESOURCE_BLOCK] Blocking domain: {url}")
        
        # Block by file extension
        elif any(url.lower().endswith(ext) for ext in blocked_extensions):
            should_block = True
            logger.debug(f"[RESOURCE_BLOCK] Blocking file extension: {url}")
        
        # Allow essential resources
        if should_block:
            # Still allow some critical CSS that might be needed for layout
            if resource_type == 'stylesheet' and any(essential in url.lower() for essential in ['bootstrap', 'main', 'style', 'app']):
                should_block = False
                logger.debug(f"[RESOURCE_ALLOW] Allowing essential CSS: {url}")
        
        if should_block:
            await route.abort()
        else:
            await route.continue_()
        
    async def initialize(self, use_session=False, skip_cooldown_check=False):
        """Initialize browser instance"""
        try:
            logger.info(f"[INIT] Instance #{self.instance_id} initializing...")
            
            # Check cooldown if not skipped
            if not skip_cooldown_check:
                can_initialize, remaining_minutes = self.check_last_vote_cooldown()
                if not can_initialize:
                    logger.info(f"[INIT] Instance #{self.instance_id} in cooldown: {remaining_minutes}m remaining")
                    return False
            
            # Acquire semaphore to ensure sequential browser launch
            if self.voter_manager and hasattr(self.voter_manager, 'browser_launch_semaphore'):
                async with self.voter_manager.browser_launch_semaphore:
                    logger.info(f"[INIT] Instance #{self.instance_id} acquired browser launch lock")
                    return await self._initialize_browser(use_session)
            else:
                # Fallback if no voter_manager
                return await self._initialize_browser(use_session)
            
        except Exception as e:
            logger.error(f"[INIT] Instance #{self.instance_id} initialization failed: {e}")
            self.status = "Error"
            return False
    
    async def _initialize_browser(self, use_session=False):
        """Internal method to initialize browser (called within semaphore)"""
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Browser launch arguments
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
            
            # Launch browser with proxy
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                proxy={
                    'server': self.proxy_config['server'],
                    'username': self.proxy_config['username'],
                    'password': self.proxy_config['password']
                },
                args=browser_args
            )
            
            # Create context
            if use_session and os.path.exists(os.path.join(self.session_dir, 'storage_state.json')):
                # Restore session
                storage_state_path = os.path.join(self.session_dir, 'storage_state.json')
                self.context = await self.browser.new_context(
                    storage_state=storage_state_path,
                    viewport={'width': 1920, 'height': 1080}
                )
                logger.info(f"[INIT] Instance #{self.instance_id} restored session")
            else:
                # New session
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080}
                )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Enable resource blocking if configured
            if self.enable_resource_blocking:
                await self.page.route("**/*", self._handle_resource_blocking)
                blocked_types = []
                if self.block_images: blocked_types.append("images")
                if self.block_stylesheets: blocked_types.append("CSS")
                if self.block_fonts: blocked_types.append("fonts")
                if self.block_tracking: blocked_types.append("tracking")
                blocked_types.append("media")  # Always blocked
                logger.info(f"[INIT] Instance #{self.instance_id} resource blocking enabled - blocking: {', '.join(blocked_types)}")
            
            self.status = "Ready"
            logger.info(f"[INIT] Instance #{self.instance_id} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[INIT] Instance #{self.instance_id} initialization failed: {e}")
            self.status = "Error"
            return False
    
    async def initialize_with_saved_session(self, storage_state_path: str):
        """Initialize browser instance with saved session"""
        try:
            logger.info(f"[INIT] Instance #{self.instance_id} initializing with saved session...")
            
            # Acquire semaphore to ensure sequential browser launch
            if self.voter_manager and hasattr(self.voter_manager, 'browser_launch_semaphore'):
                async with self.voter_manager.browser_launch_semaphore:
                    logger.info(f"[INIT] Instance #{self.instance_id} acquired browser launch lock")
                    return await self._initialize_browser_with_session(storage_state_path)
            else:
                # Fallback if no voter_manager
                return await self._initialize_browser_with_session(storage_state_path)
            
        except Exception as e:
            logger.error(f"[INIT] Instance #{self.instance_id} initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.status = "Error"
            return False
    
    async def _initialize_browser_with_session(self, storage_state_path: str):
        """Internal method to initialize browser with session (called within semaphore)"""
        try:
            # Start Playwright
            self.playwright = await async_playwright().start()
            
            # Browser launch arguments
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage'
            ]
            
            # Launch browser with proxy
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                proxy={
                    'server': self.proxy_config['server'],
                    'username': self.proxy_config['username'],
                    'password': self.proxy_config['password']
                },
                args=browser_args
            )
            
            # Create context with saved session
            self.context = await self.browser.new_context(
                storage_state=storage_state_path,
                viewport={'width': 1920, 'height': 1080}
            )
            logger.info(f"[INIT] Instance #{self.instance_id} restored session from {storage_state_path}")
            
            # Create page
            self.page = await self.context.new_page()
            
            # Enable resource blocking if configured
            if self.enable_resource_blocking:
                await self.page.route("**/*", self._handle_resource_blocking)
                blocked_types = []
                if self.block_images: blocked_types.append("images")
                if self.block_stylesheets: blocked_types.append("CSS")
                if self.block_fonts: blocked_types.append("fonts")
                if self.block_tracking: blocked_types.append("tracking")
                blocked_types.append("media")  # Always blocked
                logger.info(f"[INIT] Instance #{self.instance_id} resource blocking enabled - blocking: {', '.join(blocked_types)}")
            
            self.status = "Ready"
            logger.info(f"[INIT] Instance #{self.instance_id} initialized successfully with saved session")
            return True
            
        except Exception as e:
            logger.error(f"[INIT] Instance #{self.instance_id} initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.status = "Error"
            return False
    
    def check_last_vote_cooldown(self):
        """Check if instance is in cooldown period"""
        try:
            session_info_path = os.path.join(self.session_dir, 'session_info.json')
            
            if os.path.exists(session_info_path):
                with open(session_info_path, 'r') as f:
                    session_info = json.load(f)
                
                last_vote_time_str = session_info.get('last_vote_time')
                if last_vote_time_str:
                    last_vote_time = datetime.fromisoformat(last_vote_time_str)
                    # Server is IST, timestamps are IST, no conversion needed
                    current_time = datetime.now()  # Gets IST from server
                    time_since_vote = (current_time - last_vote_time).total_seconds() / 60
                    
                    if time_since_vote < 31:  # 31 minute cooldown
                        remaining_minutes = int(31 - time_since_vote)
                        return False, remaining_minutes
            
            return True, 0
            
        except Exception as e:
            logger.error(f"[COOLDOWN] Error checking cooldown: {e}")
            return True, 0
    
    async def navigate_to_voting_page(self):
        """Navigate to voting page"""
        try:
            if not self.page:
                return False
            
            logger.info(f"[NAV] Instance #{self.instance_id} navigating to {self.target_url}")
            # Use 'domcontentloaded' instead of 'networkidle' for faster, more reliable loading
            # 'networkidle' can timeout on pages with continuous network activity
            await self.page.goto(self.target_url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for page to stabilize
            await asyncio.sleep(3)
            
            logger.info(f"[NAV] Instance #{self.instance_id} navigation successful")
            return True
            
        except Exception as e:
            logger.error(f"[NAV] Instance #{self.instance_id} navigation failed: {e}")
            return False
    
    async def check_login_required(self):
        """Check if Google login is required"""
        try:
            if not self.page:
                return False
            
            # Check for Google login indicators
            login_selectors = [
                'a[href*="accounts.google.com"]',
                'button:has-text("Sign in with Google")',
                'div:has-text("Sign in")'
            ]
            
            for selector in login_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        logger.info(f"[LOGIN] Instance #{self.instance_id} requires login")
                        return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"[LOGIN] Error checking login: {e}")
            return False
    
    async def get_vote_count(self):
        """Get current vote count from page"""
        try:
            # Try multiple selectors for vote count
            count_selectors = [
                '.pc-image-info-box-votes',
                '[class*="vote"][class*="count"]',
                '[class*="votes"]',
                'span:has-text("votes")',
                'div:has-text("votes")',
                '.vote-count',
                '#vote-count'
            ]
            
            for selector in count_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        # Extract number from text like "1,234 votes" or "Votes: 1234"
                        import re
                        numbers = re.findall(r'\d+', text.replace(',', ''))
                        if numbers:
                            count = int(numbers[0])
                            logger.debug(f"[VOTE_COUNT] Found count {count} with selector: {selector}")
                            return count
                except:
                    continue
            
            logger.warning("[VOTE_COUNT] Could not find vote count on page")
            return None
            
        except Exception as e:
            logger.error(f"[VOTE_COUNT] Error getting vote count: {e}")
            return None
    
    async def clear_popups_enhanced(self):
        """Enhanced popup clearing with multiple phases"""
        try:
            logger.info(f"[POPUP] Instance #{self.instance_id} clearing popups...")
            
            # PHASE 1: Escape sequences to dismiss popups
            for i in range(4):
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(0.05)
            
            # PHASE 2: Specific popup close buttons (cutebabyvote.com specific)
            specific_selectors = [
                'button.pum-close.popmake-close[aria-label="Close"]',
                'button[type="button"].pum-close.popmake-close',
                '.pum-close.popmake-close',
                'button.pum-close',
                'button.popmake-close',
                '[class*="pum-close"][class*="popmake-close"]',
                'button[class*="pum-close"]',
                'button[class*="popmake-close"]'
            ]
            
            popup_closed = False
            for selector in specific_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        try:
                            if await element.is_visible():
                                await element.click(timeout=500)
                                logger.info(f"[POPUP] ✅ Closed specific popup: {selector}")
                                popup_closed = True
                                await asyncio.sleep(0.3)
                                break
                        except:
                            continue
                except:
                    continue
                
                if popup_closed:
                    break
            
            # PHASE 3: Generic close buttons
            generic_selectors = [
                '[aria-label="Close"]',
                'button[aria-label="Close"]',
                '.close',
                'button.close',
                'button:has-text("×")',
                'button:has-text("✕")',
                'button:has-text("Close")',
                '.modal-close',
                '.popup-close',
                '[class*="close"]',
                'div[role="dialog"] button'
            ]
            
            for selector in generic_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements[:2]:  # Check first 2 elements
                        try:
                            if await element.is_visible():
                                await element.click(timeout=500)
                                logger.info(f"[POPUP] Closed generic popup: {selector}")
                                await asyncio.sleep(0.1)
                                break
                        except:
                            continue
                except:
                    continue
            
            # PHASE 4: Final escape sequences
            for i in range(2):
                await self.page.keyboard.press('Escape')
                await asyncio.sleep(0.05)
            
            logger.info(f"[POPUP] Instance #{self.instance_id} popup clearing complete")
            return True
            
        except Exception as e:
            logger.warning(f"[POPUP] Popup clearing failed: {e}")
            return False
    
    async def attempt_vote(self):
        """Attempt to cast a vote with vote count verification"""
        # Initialize variables at the start so they're available in exception handler
        click_time = datetime.now()  # Server is IST
        initial_count = None
        click_attempts = 0
        button_clicked = False
        
        try:
            if not self.page:
                return False
            
            logger.info(f"[VOTE] Instance #{self.instance_id} attempting vote...")
            
            # STEP 1: Clear popups BEFORE voting
            try:
                await asyncio.wait_for(self.clear_popups_enhanced(), timeout=3.0)
            except asyncio.TimeoutError:
                logger.warning(f"[VOTE] Popup clearing timeout - proceeding anyway")
            except Exception as e:
                logger.warning(f"[VOTE] Popup clearing failed: {e} - proceeding anyway")
            
            # STEP 2: Get initial vote count
            initial_count = await self.get_vote_count()
            if initial_count is not None:
                logger.info(f"[VOTE] Initial vote count: {initial_count}")
            else:
                logger.warning(f"[VOTE] Could not get initial vote count - will use text detection fallback")
            
            # STEP 3: Find and click vote button
            # Record exact click time
            click_time = datetime.now()  # Server is IST
            vote_selectors = [
                # Most specific selectors first (exact match for cutebabyvote.com)
                'div.pc-image-info-box-button-btn-text.blink',
                '.pc-image-info-box-button-btn-text.blink',
                '.pc-image-info-box-button-btn-text',
                'div.pc-image-info-box-button-btn',
                '.blink',
                'input[type="submit"]',
                'button:has-text("Vote")'
            ]
            
            for selector in vote_selectors:
                try:
                    click_attempts += 1
                    button = await self.page.wait_for_selector(selector, timeout=2000)
                    if button and await button.is_visible():
                        await button.click()
                        logger.info(f"[VOTE] Instance #{self.instance_id} clicked vote button with selector: {selector}")
                        button_clicked = True
                        break
                except:
                    continue
            
            if not button_clicked:
                logger.error(f"[VOTE] Instance #{self.instance_id} could not find vote button")
                
                # Track last attempt (failed) and store reason
                self.last_attempted_vote = datetime.now()
                self.last_failure_reason = "Could not find vote button"
                self.last_failure_type = "technical"  # Technical failure
                
                # Log failed vote attempt
                self.vote_logger.log_vote_attempt(
                    instance_id=self.instance_id,
                    instance_name=f"Instance_{self.instance_id}",
                    time_of_click=click_time,
                    status="failed",
                    voting_url=self.target_url,
                    failure_type="technical",
                    failure_reason="Could not find vote button",
                    proxy_ip=self.proxy_ip,
                    session_id=self.session_id or "",
                    click_attempts=click_attempts,
                    browser_closed=False
                )
                return False
            
            # STEP 4: Wait for response
            await asyncio.sleep(3)
            
            # STEP 5: Get final vote count and VERIFY
            final_count = await self.get_vote_count()
            if final_count is not None:
                logger.info(f"[VOTE] Final vote count: {final_count}")
            
            # CRITICAL: Verify vote by comparing counts
            if initial_count is not None and final_count is not None:
                count_increase = final_count - initial_count
                
                if count_increase == 1:
                    # VERIFIED SUCCESS - Count increased by exactly 1
                    logger.info(f"[SUCCESS] ✅ Vote VERIFIED successful: {initial_count} -> {final_count} (+{count_increase})")
                    current_time = datetime.now()  # Server is IST
                    self.last_vote_time = current_time
                    self.last_successful_vote = current_time  # Track last successful vote
                    self.last_attempted_vote = current_time   # Track last attempt
                    self.last_failure_reason = None          # Clear failure reason on success
                    self.last_failure_type = None            # Clear failure type on success
                    self.vote_count += 1
                    
                    # Log successful vote to CSV with comprehensive data
                    self.vote_logger.log_vote_attempt(
                        instance_id=self.instance_id,
                        instance_name=f"Instance_{self.instance_id}",
                        time_of_click=click_time,
                        status="success",
                        voting_url=self.target_url,
                        cooldown_message="",
                        failure_type="",
                        failure_reason=f"Vote count verified: +{count_increase}",
                        initial_vote_count=initial_count,
                        final_vote_count=final_count,
                        proxy_ip=self.proxy_ip,
                        session_id=self.session_id or "",
                        click_attempts=click_attempts,
                        error_message="",
                        browser_closed=True
                    )
                    
                    await self.save_session_data()
                    
                    # Close browser after successful vote to free resources
                    logger.info(f"[CLEANUP] Closing browser after successful vote")
                    await self.close_browser()
                    
                    return True
                    
                elif count_increase > 1:
                    logger.warning(f"[SUSPICIOUS] Vote count increased by {count_increase} (expected 1): {initial_count} -> {final_count}")
                    logger.warning(f"[SUSPICIOUS] Possible parallel voting interference - not counting as successful")
                    return False
                    
                else:
                    # Count didn't increase - wait for page to fully load and check for error messages
                    logger.info(f"[FAILED] Vote count did not increase: {initial_count} -> {final_count}")
                    logger.info(f"[WAIT] Waiting for page to fully load and display error message...")
                    
                    # Wait additional time for error message to appear (page might still be loading)
                    await asyncio.sleep(5)
                    
                    page_content = await self.page.content()
                    cooldown_message = ""
                    
                    # Check for failure patterns from config
                    if any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
                        logger.warning(f"[VOTE] Instance #{self.instance_id} hit cooldown/limit")
                        
                        # Track last attempt (failed)
                        self.last_attempted_vote = datetime.now()
                        
                        # Try to extract the actual message from the page
                        try:
                            # Look for the message in button text or alert divs
                            if self.page:
                                # Try to find message in common elements
                                message_selectors = [
                                    '.pc-image-info-box-button-btn-text',
                                    '.pc-hiddenbutton .pc-image-info-box-button-btn-text',
                                    '.alert', '.message', '.notification',
                                    '[class*="message"]', '[class*="error"]'
                                ]
                                
                                for selector in message_selectors:
                                    try:
                                        element = await self.page.query_selector(selector)
                                        if element:
                                            text = await element.inner_text()
                                            if text and any(pattern in text.lower() for pattern in FAILURE_PATTERNS):
                                                # Clean up the message
                                                cooldown_message = text.strip()
                                                
                                                # Remove personalized names (e.g., "shivanshu pathak!")
                                                # Pattern: "You have voted already [NAME]! Please come back..."
                                                cooldown_message = re.sub(r'(voted already|already)\s+[^!]+!', r'\1!', cooldown_message, flags=re.IGNORECASE)
                                                
                                                # Remove extra whitespace
                                                cooldown_message = ' '.join(cooldown_message.split())
                                                
                                                # Limit length
                                                if len(cooldown_message) > 150:
                                                    cooldown_message = cooldown_message[:150] + "..."
                                                break
                                    except:
                                        continue
                        except Exception as e:
                            logger.debug(f"Could not extract message: {e}")
                        
                        # Fallback to generic messages if extraction failed
                        if not cooldown_message:
                            if 'please come back at your next voting time' in page_content.lower():
                                cooldown_message = "Already voted - Please come back at next voting time"
                            elif 'hourly limit' in page_content.lower():
                                cooldown_message = "Hourly voting limit reached"
                            elif 'already voted' in page_content.lower():
                                cooldown_message = "Already voted"
                            elif 'cooldown' in page_content.lower():
                                cooldown_message = "In cooldown period"
                            else:
                                cooldown_message = "Cooldown/limit detected"
                        
                        # Store failure reason and type
                        self.last_failure_reason = cooldown_message
                        self.last_failure_type = "ip_cooldown"  # IP cooldown/hourly limit
                        
                        # Check if this is a GLOBAL hourly limit or INSTANCE-SPECIFIC cooldown
                        is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)
                        is_instance_cooldown = any(pattern in page_content.lower() for pattern in INSTANCE_COOLDOWN_PATTERNS)
                        
                        if is_global_limit:
                            logger.warning(f"[GLOBAL_LIMIT] Instance #{self.instance_id} detected GLOBAL hourly limit - will pause ALL instances")
                        elif is_instance_cooldown:
                            logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} in instance-specific cooldown (30 min) - only this instance affected")
                        
                        # Log cooldown to CSV with comprehensive data
                        self.vote_logger.log_vote_attempt(
                            instance_id=self.instance_id,
                            instance_name=f"Instance_{self.instance_id}",
                            time_of_click=click_time,
                            status="failed",
                            voting_url=self.target_url,
                            cooldown_message=cooldown_message,
                            failure_type="ip_cooldown",
                            failure_reason="IP in cooldown period" if is_instance_cooldown else "Global hourly limit reached",
                            initial_vote_count=initial_count,
                            final_vote_count=final_count,
                            proxy_ip=self.proxy_ip,
                            session_id=self.session_id or "",
                            click_attempts=click_attempts,
                            error_message="",
                            browser_closed=True
                        )
                        
                        # Close browser before cooldown
                        logger.info(f"[CLEANUP] Closing browser after cooldown detection")
                        await self.close_browser()
                        
                        # ONLY trigger global hourly limit handling for GLOBAL patterns
                        if is_global_limit and self.voter_manager:
                            logger.warning(f"[GLOBAL_LIMIT] Triggering global hourly limit handler")
                            asyncio.create_task(self.voter_manager.handle_hourly_limit())
                        else:
                            logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} will wait individually, other instances continue")
                    else:
                        # No error message found - try to extract any visible text from button/page
                        logger.error(f"[FAILED] Vote failed - count unchanged and no known error pattern detected")
                        logger.info(f"[DIAGNOSTIC] Attempting to extract page status message...")
                        
                        # Try to extract any message from the page for diagnostics
                        diagnostic_message = "Vote count unchanged, no error message found"
                        try:
                            # Check button text
                            button_selectors = [
                                '.pc-image-info-box-button-btn-text',
                                '.pc-hiddenbutton',
                                'div.pc-image-info-box-button-btn',
                                '.blink'
                            ]
                            for selector in button_selectors:
                                try:
                                    element = await self.page.query_selector(selector)
                                    if element:
                                        text = await element.inner_text()
                                        if text and text.strip():
                                            diagnostic_message = f"Button text: {text.strip()[:100]}"
                                            logger.info(f"[DIAGNOSTIC] Found button text: {text.strip()[:100]}")
                                            break
                                except:
                                    continue
                        except Exception as e:
                            logger.debug(f"[DIAGNOSTIC] Could not extract diagnostic info: {e}")
                        
                        # Track last attempt (failed) and store reason
                        self.last_attempted_vote = datetime.now()
                        self.last_failure_reason = diagnostic_message
                        self.last_failure_type = "technical"  # Technical failure
                        
                        # Log failed vote with comprehensive data
                        self.vote_logger.log_vote_attempt(
                            instance_id=self.instance_id,
                            instance_name=f"Instance_{self.instance_id}",
                            time_of_click=click_time,
                            status="failed",
                            voting_url=self.target_url,
                            cooldown_message="",
                            failure_type="technical",
                            failure_reason=diagnostic_message,
                            initial_vote_count=initial_count,
                            final_vote_count=final_count,
                            proxy_ip=self.proxy_ip,
                            session_id=self.session_id or "",
                            click_attempts=click_attempts,
                            error_message="Count unchanged after 8 seconds wait",
                            browser_closed=True
                        )
                        
                        # Close browser after failed vote
                        logger.info(f"[CLEANUP] Closing browser after failed vote")
                        await self.close_browser()
                    
                    return False
            
            else:
                # Fallback to text detection if vote count unavailable
                logger.warning("[VOTE] Vote count verification unavailable - using text detection fallback")
                
                page_content = await self.page.content()
                
                if any(pattern in page_content.lower() for pattern in ['thank you', 'success', 'counted']):
                    logger.warning(f"[VOTE] Text detection shows success (UNVERIFIED)")
                    self.last_vote_time = datetime.now()  # Server is IST
                    self.vote_count += 1
                    
                    # Log with warning that it's unverified
                    self.vote_logger.log_vote_attempt(
                        instance_id=self.instance_id,
                        instance_name=f"Instance_{self.instance_id}",
                        time_of_click=click_time,
                        status="success",
                        voting_url=self.target_url,
                        cooldown_message="",
                        failure_type="",
                        failure_reason="Vote success (text detection - NOT verified by count)",
                        initial_vote_count=None,
                        final_vote_count=None,
                        proxy_ip=self.proxy_ip,
                        session_id=self.session_id or "",
                        click_attempts=click_attempts,
                        error_message="WARNING: Unverified vote",
                        browser_closed=False
                    )
                    
                    await self.save_session_data()
                    return True
                    
                elif any(pattern in page_content.lower() for pattern in FAILURE_PATTERNS):
                    logger.warning(f"[VOTE] Instance #{self.instance_id} hit cooldown/limit (fallback detection)")
                    
                    # Track last attempt (failed)
                    self.last_attempted_vote = datetime.now()
                    
                    # Try to extract actual message
                    cooldown_message = "Cooldown/limit detected (fallback)"
                    try:
                        if self.page:
                            message_selectors = [
                                '.pc-image-info-box-button-btn-text',
                                '.pc-hiddenbutton .pc-image-info-box-button-btn-text',
                                '.alert', '.message', '.notification'
                            ]
                            for selector in message_selectors:
                                try:
                                    element = await self.page.query_selector(selector)
                                    if element:
                                        text = await element.inner_text()
                                        if text and any(pattern in text.lower() for pattern in FAILURE_PATTERNS):
                                            cooldown_message = text.strip()
                                            
                                            # Remove personalized names
                                            cooldown_message = re.sub(r'(voted already|already)\s+[^!]+!', r'\1!', cooldown_message, flags=re.IGNORECASE)
                                            
                                            # Remove extra whitespace
                                            cooldown_message = ' '.join(cooldown_message.split())
                                            
                                            if len(cooldown_message) > 150:
                                                cooldown_message = cooldown_message[:150] + "..."
                                            break
                                except:
                                    continue
                    except:
                        pass
                    
                    # Store failure reason and type
                    self.last_failure_reason = cooldown_message
                    self.last_failure_type = "ip_cooldown"  # IP cooldown (fallback)
                    
                    # Check if this is a GLOBAL hourly limit or INSTANCE-SPECIFIC cooldown
                    is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)
                    is_instance_cooldown = any(pattern in page_content.lower() for pattern in INSTANCE_COOLDOWN_PATTERNS)
                    
                    if is_global_limit:
                        logger.warning(f"[GLOBAL_LIMIT] Instance #{self.instance_id} detected GLOBAL hourly limit (fallback) - will pause ALL instances")
                    elif is_instance_cooldown:
                        logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} in instance-specific cooldown (fallback) - only this instance affected")
                    
                    # Log cooldown to CSV with comprehensive data
                    self.vote_logger.log_vote_attempt(
                        instance_id=self.instance_id,
                        instance_name=f"Instance_{self.instance_id}",
                        time_of_click=click_time,
                        status="failed",
                        voting_url=self.target_url,
                        cooldown_message="Cooldown detected (fallback detection)",
                        failure_type="ip_cooldown",
                        failure_reason="IP in cooldown period" if is_instance_cooldown else "Global hourly limit reached",
                        initial_vote_count=None,
                        final_vote_count=None,
                        proxy_ip=self.proxy_ip,
                        session_id=self.session_id or "",
                        click_attempts=click_attempts,
                        error_message="",
                        browser_closed=True
                    )
                    
                    # Close browser before cooldown
                    logger.info(f"[CLEANUP] Closing browser after cooldown detection (fallback)")
                    await self.close_browser()
                    
                    # ONLY trigger global hourly limit handling for GLOBAL patterns
                    if is_global_limit and self.voter_manager:
                        logger.warning(f"[GLOBAL_LIMIT] Triggering global hourly limit handler (fallback)")
                        asyncio.create_task(self.voter_manager.handle_hourly_limit())
                    else:
                        logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} will wait individually (fallback), other instances continue")
                    
                    return False
                
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"[VOTE] Instance #{self.instance_id} vote failed: {e}")
            self.failed_attempts += 1
            
            # Track last attempt (failed) and store reason
            self.last_attempted_vote = datetime.now()
            self.last_failure_reason = f"Exception: {str(e)[:100]}"
            self.last_failure_type = "technical"  # Technical failure (exception)
            
            # Get final count if possible
            final_count = None
            try:
                if self.page:
                    final_count = await self.get_vote_count()
            except:
                pass
            
            # Log failed vote to CSV with comprehensive data
            self.vote_logger.log_vote_attempt(
                instance_id=self.instance_id,
                instance_name=f"Instance_{self.instance_id}",
                time_of_click=click_time if 'click_time' in locals() else datetime.now(),
                status="failed",
                voting_url=self.target_url,
                cooldown_message="",
                failure_type="technical",
                failure_reason=f"Exception during vote attempt: {str(e)[:200]}",
                initial_vote_count=initial_count if 'initial_count' in locals() else None,
                final_vote_count=final_count,
                proxy_ip=self.proxy_ip,
                session_id=self.session_id or "",
                click_attempts=click_attempts if 'click_attempts' in locals() else 0,
                error_message=str(e)[:200],
                browser_closed=True
            )
            
            # Close browser after error
            logger.info(f"[CLEANUP] Closing browser after vote error")
            await self.close_browser()
            
            return False
    
    async def save_session_data(self):
        """Save session data for persistence"""
        try:
            os.makedirs(self.session_dir, exist_ok=True)
            
            # Save storage state
            if self.context:
                storage_state_path = os.path.join(self.session_dir, 'storage_state.json')
                await self.context.storage_state(path=storage_state_path)
            
            # Save session info
            session_info = {
                'instance_id': self.instance_id,
                'proxy_ip': self.proxy_ip,
                'session_id': self.session_id,
                'last_vote_time': self.last_vote_time.isoformat() if self.last_vote_time else None,
                'vote_count': self.vote_count,
                'saved_at': datetime.now().isoformat()  # Server is IST
            }
            
            session_info_path = os.path.join(self.session_dir, 'session_info.json')
            with open(session_info_path, 'w') as f:
                json.dump(session_info, f, indent=2)
                f.flush()  # Ensure data is written immediately
                os.fsync(f.fileno())  # Force write to disk
            
            logger.info(f"[SESSION] Instance #{self.instance_id} session saved to {session_info_path}")
            logger.info(f"[SESSION] Last vote time: {session_info['last_vote_time']}, Vote count: {session_info['vote_count']}")
            
        except Exception as e:
            logger.error(f"[SESSION] Instance #{self.instance_id} failed to save session: {e}")
    
    async def run_voting_cycle(self):
        """Main voting cycle"""
        try:
            logger.info(f"[CYCLE] Instance #{self.instance_id} starting voting cycle")
            
            while True:
                # Check if paused, but also check if cooldown has expired
                if self.is_paused:
                    # Check if this instance should be auto-unpaused
                    time_info = self.get_time_until_next_vote()
                    seconds_remaining = time_info.get('seconds_remaining', 0)
                    
                    # If cooldown expired and instance is paused (but not waiting for login)
                    if seconds_remaining == 0 and not self.waiting_for_login:
                        # Check if this is NOT a global hourly limit pause
                        if not (self.voter_manager and self.voter_manager.global_hourly_limit):
                            logger.info(f"[AUTO-UNPAUSE] Instance #{self.instance_id} cooldown expired - auto-unpausing")
                            self.is_paused = False
                            self.pause_event.set()
                            self.status = "▶️ Resumed - Ready to Vote"
                
                # Wait if still paused
                await self.pause_event.wait()
                
                # Re-initialize browser if it was closed (e.g., after hourly limit)
                if not self.browser or not self.page:
                    logger.info(f"[CYCLE] Instance #{self.instance_id} browser not active, re-initializing...")
                    
                    # Check if we have a saved session to restore
                    storage_state_path = os.path.join(self.session_dir, 'storage_state.json')
                    if os.path.exists(storage_state_path):
                        init_success = await self.initialize_with_saved_session(storage_state_path)
                    else:
                        init_success = await self.initialize(skip_cooldown_check=True)
                    
                    if not init_success:
                        logger.error(f"[CYCLE] Instance #{self.instance_id} browser re-initialization failed, retrying...")
                        await asyncio.sleep(30)
                        continue
                
                # Navigate to voting page
                if not await self.navigate_to_voting_page():
                    logger.warning(f"[CYCLE] Instance #{self.instance_id} navigation failed, retrying...")
                    await asyncio.sleep(30)
                    continue
                
                # CRITICAL: Check for hourly limit AFTER navigation
                if await self.check_hourly_voting_limit():
                    logger.info(f"[LIMIT] Instance #{self.instance_id} limit detected - analyzing type...")
                    
                    # Get page content to determine if global or instance-specific
                    try:
                        page_content = await self.page.content()
                        
                        # Check if this is a GLOBAL hourly limit or INSTANCE-SPECIFIC cooldown
                        is_global_limit = any(pattern in page_content.lower() for pattern in GLOBAL_HOURLY_LIMIT_PATTERNS)
                        is_instance_cooldown = any(pattern in page_content.lower() for pattern in INSTANCE_COOLDOWN_PATTERNS)
                        
                        if is_global_limit:
                            logger.warning(f"[GLOBAL_LIMIT] Instance #{self.instance_id} detected GLOBAL hourly limit - will pause ALL instances")
                            await self.close_browser()
                            
                            # Trigger global hourly limit handling
                            if self.voter_manager:
                                asyncio.create_task(self.voter_manager.handle_hourly_limit())
                            
                            # Pause this instance
                            self.is_paused = True
                            self.pause_event.clear()
                            continue
                            
                        elif is_instance_cooldown:
                            logger.info(f"[INSTANCE_COOLDOWN] Instance #{self.instance_id} in instance-specific cooldown (pre-vote) - only this instance affected")
                            await self.close_browser()
                            
                            # Don't trigger global pause, just close browser and continue cycle
                            # The instance will wait in its normal voting cycle
                            continue
                        else:
                            # Unknown pattern - treat as instance-specific to be safe (don't pause all instances)
                            logger.warning(f"[LIMIT] Instance #{self.instance_id} detected unknown limit pattern - treating as instance-specific (safe default)")
                            await self.close_browser()
                            continue
                            
                    except Exception as e:
                        logger.error(f"[LIMIT] Error analyzing limit type: {e}")
                        # On error, don't trigger global pause (safe default)
                        await self.close_browser()
                        continue
                
                # Check if login required
                if await self.check_login_required():
                    logger.info(f"[CYCLE] Instance #{self.instance_id} requires login - pausing")
                    self.status = "🔑 Waiting for Login"
                    self.waiting_for_login = True
                    self.is_paused = True
                    self.pause_event.clear()
                    continue
                
                # Attempt vote
                success = await self.attempt_vote()
                
                if success:
                    self.status = "✅ Vote Successful"
                    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting {RETRY_DELAY_COOLDOWN} minutes...")
                    await asyncio.sleep(RETRY_DELAY_COOLDOWN * 60)
                else:
                    # Determine wait time based on failure type
                    if self.last_failure_type == "ip_cooldown":
                        # Hourly limit / cooldown - wait full cycle
                        wait_minutes = RETRY_DELAY_COOLDOWN
                        self.status = f"⏳ Cooldown ({wait_minutes} min)"
                        logger.info(f"[CYCLE] Instance #{self.instance_id} in cooldown, waiting {wait_minutes} minutes...")
                    else:
                        # Technical failure - retry sooner
                        wait_minutes = RETRY_DELAY_TECHNICAL
                        self.status = f"🔄 Retry in {wait_minutes} min"
                        logger.info(f"[CYCLE] Instance #{self.instance_id} technical failure, retrying in {wait_minutes} minutes...")
                    
                    await asyncio.sleep(wait_minutes * 60)
                
        except asyncio.CancelledError:
            logger.info(f"[CYCLE] Instance #{self.instance_id} voting cycle cancelled")
        except Exception as e:
            logger.error(f"[CYCLE] Instance #{self.instance_id} error in voting cycle: {e}")
            self.status = "Error"
    
    async def check_hourly_voting_limit(self) -> bool:
        """Check if hourly voting limit has been reached"""
        try:
            if not self.page:
                return False
            
            # Look for the hourly limit message
            limit_selectors = [
                'div.pc-hiddenbutton',
                'div.redb.pc-hiddenbutton',
                'div:has-text("hourly voting limit")',
                'div:has-text("voting button is temporarily disabled")',
                'div:has-text("will be reactivated at")'
            ]
            
            for selector in limit_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element and await element.is_visible():
                        # Extract the message text
                        message_text = await element.inner_text()
                        logger.info(f"[HOURLY_LIMIT] Instance #{self.instance_id} detected: {message_text[:100]}...")
                        return True
                except:
                    continue
            
            # Also check page content for hourly limit text
            try:
                page_content = await self.page.content()
                hourly_limit_patterns = [
                    'hourly voting limit',
                    'voting button is temporarily disabled',
                    'will be reactivated at',
                    'reached your hourly limit'
                ]
                
                for pattern in hourly_limit_patterns:
                    if pattern.lower() in page_content.lower():
                        logger.info(f"[HOURLY_LIMIT] Instance #{self.instance_id} detected pattern: {pattern}")
                        return True
            except:
                pass
            
            return False
            
        except Exception as e:
            logger.error(f"[HOURLY_LIMIT] Error checking hourly limit: {e}")
            return False
    
    async def close_browser(self):
        """Close browser and cleanup with forced timeouts"""
        try:
            # Force close with timeouts to prevent hanging
            if self.page:
                try:
                    await asyncio.wait_for(self.page.close(), timeout=5.0)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"[CLEANUP] Instance #{self.instance_id} page close timeout/error: {e}")
                finally:
                    self.page = None
            
            if self.context:
                try:
                    await asyncio.wait_for(self.context.close(), timeout=10.0)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"[CLEANUP] Instance #{self.instance_id} context close timeout/error: {e}")
                finally:
                    self.context = None
            
            if self.browser:
                try:
                    await asyncio.wait_for(self.browser.close(), timeout=10.0)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"[CLEANUP] Instance #{self.instance_id} browser close timeout/error: {e}")
                finally:
                    self.browser = None
            
            if self.playwright:
                try:
                    await asyncio.wait_for(self.playwright.stop(), timeout=5.0)
                except (asyncio.TimeoutError, Exception) as e:
                    logger.warning(f"[CLEANUP] Instance #{self.instance_id} playwright stop timeout/error: {e}")
                finally:
                    self.playwright = None
            
            self.status = "Cooldown - Browser Closed"
            logger.info(f"[CLEANUP] Instance #{self.instance_id} browser cleanup completed")
            
        except Exception as e:
            logger.error(f"[CLEANUP] Instance #{self.instance_id} browser close failed: {e}")
            # Force cleanup even on error
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

class MultiInstanceVoter:
    """Manager for multiple voting instances"""
    
    def __init__(self, username: str, password: str, target_url: str):
        self.username = username
        self.password = password
        self.target_url = target_url
        
        # Initialize proxy API
        self.proxy_api = BrightDataAPI(username, password)
        
        # Proxy configuration
        self.proxy_config = {
            'server': 'http://brd.superproxy.io:22225',
            'host': 'brd.superproxy.io',
            'port': 22225,
            'username': f"brd-customer-{username}-zone-datacenter_proxy1-country-in",
            'password': password
        }
        
        # Instance management
        self.active_instances = {}
        self.used_ips = set()
        
        # Hourly limit management
        self.global_hourly_limit = False
        self.global_reactivation_time = None
        self.hourly_limit_check_task = None
        
        # Browser monitoring
        self.browser_monitoring_task = None
        self.browser_monitoring_active = False
        
        # Auto-unpause monitoring (checks for expired cooldowns)
        self.auto_unpause_task = None
        self.auto_unpause_active = False
        
        # Sequential browser launch control (prevents memory overload on limited resources)
        self.browser_launch_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSER_LAUNCHES)
        self.browser_launch_delay = BROWSER_LAUNCH_DELAY  # Seconds to wait between browser launches
        self.sequential_resume_active = False
        
        # Circuit breaker for proxy 503 errors
        self.consecutive_503_errors = 0
        self.circuit_breaker_active = False
        self.circuit_breaker_reset_time = None
    
    async def get_proxy_ip(self, excluded_ips: Set[str] = None) -> Optional[tuple]:
        """Get unique IP from Bright Data proxy with retry logic and circuit breaker"""
        import urllib.request
        import urllib.error
        import json
        
        # Check circuit breaker
        if self.circuit_breaker_active:
            if datetime.now() < self.circuit_breaker_reset_time:
                remaining = (self.circuit_breaker_reset_time - datetime.now()).seconds
                logger.warning(f"[CIRCUIT_BREAKER] Proxy service paused, {remaining}s remaining")
                return None
            else:
                # Reset circuit breaker
                logger.info(f"[CIRCUIT_BREAKER] Resetting after pause")
                self.circuit_breaker_active = False
                self.consecutive_503_errors = 0
        
        # Retry logic with exponential backoff
        for attempt in range(PROXY_MAX_RETRIES):
            try:
                # Generate unique session ID
                session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                
                # Create proxy auth with session
                base_auth = f"brd-customer-{self.proxy_api.username}-zone-{self.proxy_api.zone}-country-in-session-{session_id}"
                proxy_auth = f"{base_auth}:{self.proxy_api.password}"
                
                proxy = f'http://{proxy_auth}@{self.proxy_api.proxy_host}:{self.proxy_api.proxy_port}'
                
                opener = urllib.request.build_opener(
                    urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
                )
                
                response = opener.open('https://httpbin.org/ip', timeout=10)
                result = response.read().decode()
                ip_data = json.loads(result)
                
                assigned_ip = ip_data.get('origin', '').split(',')[0].strip()
                
                if assigned_ip:
                    if excluded_ips and assigned_ip in excluded_ips:
                        logger.warning(f"[IP] IP {assigned_ip} already in use, retrying...")
                        return None
                    
                    # Success - reset circuit breaker counter
                    self.consecutive_503_errors = 0
                    logger.info(f"[IP] Assigned IP: {assigned_ip}")
                    return (assigned_ip, self.proxy_api.proxy_port)
                
                return None
                
            except urllib.error.HTTPError as e:
                if e.code == 503:
                    self.consecutive_503_errors += 1
                    logger.error(f"[IP] HTTP 503 error (attempt {attempt + 1}/{PROXY_MAX_RETRIES}, consecutive: {self.consecutive_503_errors})")
                    
                    # Check if circuit breaker should trip
                    if self.consecutive_503_errors >= PROXY_503_CIRCUIT_BREAKER_THRESHOLD:
                        self.circuit_breaker_active = True
                        self.circuit_breaker_reset_time = datetime.now() + timedelta(seconds=PROXY_503_PAUSE_DURATION)
                        logger.error(f"[CIRCUIT_BREAKER] 🚫 Proxy service unavailable after {self.consecutive_503_errors} consecutive 503s")
                        logger.error(f"[CIRCUIT_BREAKER] Pausing proxy requests for {PROXY_503_PAUSE_DURATION}s until {self.circuit_breaker_reset_time.strftime('%H:%M:%S')}")
                        return None
                    
                    # Exponential backoff
                    if attempt < PROXY_MAX_RETRIES - 1:
                        wait_time = PROXY_RETRY_DELAY ** (attempt + 1)
                        logger.warning(f"[IP] Retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                else:
                    logger.error(f"[IP] HTTP Error {e.code}: {e}")
                    return None
                    
            except Exception as e:
                logger.error(f"[IP] Error getting proxy IP (attempt {attempt + 1}/{PROXY_MAX_RETRIES}): {e}")
                if attempt < PROXY_MAX_RETRIES - 1:
                    wait_time = PROXY_RETRY_DELAY ** (attempt + 1)
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        logger.error(f"[IP] Failed to get proxy IP after {PROXY_MAX_RETRIES} attempts")
        return None
    
    async def launch_new_instance(self) -> bool:
        """Launch a new voting instance"""
        try:
            # Get unique IP
            excluded_ips = set(self.active_instances.keys()) | self.used_ips
            
            ip_result = await self.get_proxy_ip(excluded_ips)
            if not ip_result:
                logger.error("[ERROR] Could not get unique IP")
                return False
            
            proxy_ip, proxy_port = ip_result
            
            # Create session-specific proxy config
            session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            instance_proxy_config = {
                'server': self.proxy_config['server'],
                'host': self.proxy_config['host'],
                'port': self.proxy_config['port'],
                'username': f"brd-customer-{self.proxy_api.username}-zone-{self.proxy_api.zone}-country-in-session-{session_id}",
                'password': self.proxy_api.password
            }
            
            # Get next instance ID
            next_instance_id = len(self.active_instances) + 1
            
            # Create instance
            instance = VoterInstance(proxy_ip, instance_proxy_config, next_instance_id, self.target_url, self)
            instance.session_id = session_id
            
            # Initialize instance
            if await instance.initialize():
                self.active_instances[proxy_ip] = instance
                self.used_ips.add(proxy_ip)
                
                logger.info(f"[SUCCESS] Launched instance #{next_instance_id} with IP: {proxy_ip}")
                
                # Navigate and start voting cycle
                await instance.navigate_to_voting_page()
                
                if await instance.check_login_required():
                    logger.info(f"[LAUNCH] Instance #{next_instance_id} requires login")
                    instance.status = "🔑 Waiting for Login"
                    instance.waiting_for_login = True
                else:
                    logger.info(f"[LAUNCH] Instance #{next_instance_id} starting voting cycle")
                    asyncio.create_task(instance.run_voting_cycle())
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"[ERROR] Failed to launch instance: {e}")
            return False
    
    async def launch_instance_from_saved_session(self, instance_id: int, session_path: str) -> Optional['VoterInstance']:
        """Launch instance from saved session"""
        try:
            import os
            import json
            
            logger.info(f"[SESSION] Loading session for instance #{instance_id} from {session_path}")
            
            # Load session info
            session_info_path = os.path.join(session_path, "session_info.json")
            storage_state_path = os.path.join(session_path, "storage_state.json")
            
            if not os.path.exists(storage_state_path):
                logger.error(f"[SESSION] Storage state not found for instance #{instance_id}")
                return None
            
            # Load session metadata
            session_info = {}
            if os.path.exists(session_info_path):
                with open(session_info_path, 'r') as f:
                    session_info = json.load(f)
            
            saved_proxy_ip = session_info.get('proxy_ip')
            saved_session_id = session_info.get('session_id')
            
            # Check if instance is already running by instance ID
            for ip, existing_instance in self.active_instances.items():
                if existing_instance.instance_id == instance_id:
                    logger.warning(f"[SESSION] Instance #{instance_id} already running with IP {ip}")
                    return None
            
            # CRITICAL: Reuse saved proxy IP instead of requesting new one
            # This prevents 502 errors and maintains session consistency
            if saved_proxy_ip and saved_session_id:
                logger.info(f"[SESSION] Reusing saved proxy IP: {saved_proxy_ip} (session: {saved_session_id})")
                new_proxy_ip = saved_proxy_ip
                session_id = saved_session_id
                proxy_port = self.proxy_api.proxy_port
            else:
                # Fallback: Only request new IP if session doesn't have one saved
                logger.warning(f"[SESSION] No saved IP found, requesting new IP for instance #{instance_id}")
                excluded_ips = set(self.active_instances.keys()) | self.used_ips
                ip_result = await self.get_proxy_ip(excluded_ips)
                
                if not ip_result:
                    logger.error(f"[SESSION] Could not get unique IP for instance #{instance_id}")
                    return None
                
                new_proxy_ip, proxy_port = ip_result
                session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            
            # Create session-specific proxy config (using saved or new session_id)
            instance_proxy_config = {
                'server': self.proxy_config['server'],
                'host': self.proxy_config['host'],
                'port': self.proxy_config['port'],
                'username': f"brd-customer-{self.proxy_api.username}-zone-{self.proxy_api.zone}-country-in-session-{session_id}",
                'password': self.proxy_api.password
            }
            
            # Create instance
            instance = VoterInstance(new_proxy_ip, instance_proxy_config, instance_id, self.target_url, self)
            instance.session_id = session_id
            instance.session_path = session_path
            instance.storage_state_path = storage_state_path
            
            # Initialize instance with saved session
            if await instance.initialize_with_saved_session(storage_state_path):
                self.active_instances[new_proxy_ip] = instance
                self.used_ips.add(new_proxy_ip)
                
                logger.info(f"[SESSION] Restored instance #{instance_id} with IP: {new_proxy_ip}")
                
                # Navigate and start voting cycle
                nav_success = await instance.navigate_to_voting_page()
                
                if nav_success:
                    if await instance.check_login_required():
                        logger.info(f"[SESSION] Instance #{instance_id} requires login")
                        instance.status = "🔑 Waiting for Login"
                        instance.waiting_for_login = True
                    else:
                        logger.info(f"[SESSION] Instance #{instance_id} starting voting cycle")
                        asyncio.create_task(instance.run_voting_cycle())
                else:
                    logger.error(f"[SESSION] Instance #{instance_id} navigation failed, will retry")
                    instance.status = "⚠️ Navigation Failed"
                
                return instance
            
            return None
            
        except Exception as e:
            logger.error(f"[SESSION] Error launching instance #{instance_id} from session: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    async def handle_hourly_limit(self):
        """Handle hourly limit by pausing ALL instances"""
        try:
            if self.global_hourly_limit:
                return  # Already handling
            
            logger.info("[HOURLY_LIMIT] 🚫 HOURLY LIMIT DETECTED - Pausing ALL instances")
            
            # Set global limit flag
            self.global_hourly_limit = True
            
            # Calculate reactivation time (next hour)
            next_hour = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            self.global_reactivation_time = next_hour.isoformat()
            
            logger.info(f"[HOURLY_LIMIT] Will resume at {next_hour.strftime('%I:%M %p')}")
            
            # Pause ALL active instances
            paused_count = 0
            for ip, instance in self.active_instances.items():
                if not instance.is_paused:
                    instance.is_paused = True
                    instance.pause_event.clear()
                    instance.status = "⏸️ Paused - Hourly Limit"
                    paused_count += 1
                    logger.info(f"[HOURLY_LIMIT] Paused instance #{instance.instance_id}")
            
            logger.info(f"[HOURLY_LIMIT] Paused {paused_count} instances")
            
            # Start monitoring task to resume when limit clears
            if not self.hourly_limit_check_task:
                self.hourly_limit_check_task = asyncio.create_task(self._check_hourly_limit_expiry())
            
        except Exception as e:
            logger.error(f"[HOURLY_LIMIT] Error handling hourly limit: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _check_hourly_limit_expiry(self):
        """Monitor and resume instances when hourly limit expires"""
        try:
            while self.global_hourly_limit:
                if self.global_reactivation_time:
                    reactivation_dt = datetime.fromisoformat(self.global_reactivation_time)
                    current_time = datetime.now()  # Server is IST
                    
                    if current_time >= reactivation_dt:
                        logger.info(f"[HOURLY_LIMIT] ✅ Hourly limit expired - Resuming instances SEQUENTIALLY")
                        
                        # Clear global limit
                        self.global_hourly_limit = False
                        self.global_reactivation_time = None
                        
                        # Resume instances SEQUENTIALLY to prevent memory overload
                        self.sequential_resume_active = True
                        resumed_count = 0
                        
                        # Collect instances to resume
                        instances_to_resume = [
                            instance for ip, instance in self.active_instances.items()
                            if instance.is_paused and "Hourly Limit" in instance.status
                        ]
                        
                        logger.info(f"[HOURLY_LIMIT] Found {len(instances_to_resume)} instances to resume")
                        
                        # Resume instances one by one with delay
                        for instance in instances_to_resume:
                            try:
                                instance.is_paused = False
                                instance.pause_event.set()
                                instance.status = "▶️ Resumed - Initializing"
                                resumed_count += 1
                                logger.info(f"[HOURLY_LIMIT] Resumed instance #{instance.instance_id} ({resumed_count}/{len(instances_to_resume)})")
                                
                                # Wait before resuming next instance to prevent memory spike
                                if resumed_count < len(instances_to_resume):
                                    logger.info(f"[HOURLY_LIMIT] Waiting {self.browser_launch_delay}s before next resume...")
                                    await asyncio.sleep(self.browser_launch_delay)
                            except Exception as e:
                                logger.error(f"[HOURLY_LIMIT] Error resuming instance #{instance.instance_id}: {e}")
                        
                        self.sequential_resume_active = False
                        logger.info(f"[HOURLY_LIMIT] ✅ Sequential resume completed: {resumed_count} instances")
                        break
                    else:
                        # Log remaining time
                        remaining = (reactivation_dt - current_time).total_seconds() / 60
                        logger.info(f"[HOURLY_LIMIT] ⏰ {int(remaining)} minutes until resume")
                
                # Check every minute
                await asyncio.sleep(60)
            
            self.hourly_limit_check_task = None
            
        except asyncio.CancelledError:
            logger.info("[HOURLY_LIMIT] Limit check task cancelled")
        except Exception as e:
            logger.error(f"[HOURLY_LIMIT] Error in limit check: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def _auto_unpause_monitoring_loop(self):
        """Periodically check for paused instances with expired cooldowns and auto-unpause them"""
        try:
            logger.info("[AUTO-UNPAUSE] Monitoring service started")
            
            while self.auto_unpause_active:
                try:
                    # Check all paused instances
                    for ip, instance in list(self.active_instances.items()):
                        if instance.is_paused and not instance.waiting_for_login:
                            # Get time until next vote
                            time_info = instance.get_time_until_next_vote()
                            seconds_remaining = time_info.get('seconds_remaining', 0)
                            
                            # If cooldown expired and NOT in global hourly limit
                            if seconds_remaining == 0 and not self.global_hourly_limit:
                                logger.info(f"[AUTO-UNPAUSE] Instance #{instance.instance_id} cooldown expired - auto-unpausing")
                                instance.is_paused = False
                                instance.pause_event.set()
                                instance.status = "▶️ Resumed - Ready to Vote"
                    
                    # Check every 30 seconds
                    await asyncio.sleep(30)
                    
                except Exception as e:
                    logger.error(f"[AUTO-UNPAUSE] Error in monitoring loop: {e}")
                    await asyncio.sleep(30)
            
            logger.info("[AUTO-UNPAUSE] Monitoring service stopped")
            
        except asyncio.CancelledError:
            logger.info("[AUTO-UNPAUSE] Monitoring task cancelled")
        except Exception as e:
            logger.error(f"[AUTO-UNPAUSE] Fatal error: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    async def start_auto_unpause_monitoring(self):
        """Start auto-unpause monitoring service"""
        if self.auto_unpause_active:
            return
        
        self.auto_unpause_active = True
        self.auto_unpause_task = asyncio.create_task(self._auto_unpause_monitoring_loop())
        logger.info("[AUTO-UNPAUSE] Monitoring service initialized")
    
    async def stop_auto_unpause_monitoring(self):
        """Stop auto-unpause monitoring service"""
        self.auto_unpause_active = False
        
        if self.auto_unpause_task:
            self.auto_unpause_task.cancel()
            try:
                await self.auto_unpause_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[AUTO-UNPAUSE] Monitoring service stopped")
    
    async def start_browser_monitoring_service(self):
        """Start browser monitoring service"""
        if self.browser_monitoring_active:
            return
        
        self.browser_monitoring_active = True
        self.browser_monitoring_task = asyncio.create_task(self._browser_monitoring_loop())
        logger.info("[MONITOR] Browser monitoring service started")
    
    async def stop_browser_monitoring_service(self):
        """Stop browser monitoring service"""
        self.browser_monitoring_active = False
        
        if self.browser_monitoring_task:
            self.browser_monitoring_task.cancel()
            try:
                await self.browser_monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("[MONITOR] Browser monitoring service stopped")
    
    async def _browser_monitoring_loop(self):
        """Monitor browsers and close idle ones"""
        try:
            while self.browser_monitoring_active:
                # Check for idle browsers
                for ip, instance in list(self.active_instances.items()):
                    try:
                        # Only close browsers with Error status or hourly limit
                        # DO NOT close browsers in Cooldown - they need to vote again!
                        if instance.status == "Error":
                            if instance.browser:
                                await instance.close_browser()
                                logger.info(f"[MONITOR] Closed browser for instance #{instance.instance_id}: Error status")
                        elif self.global_hourly_limit and instance.browser:
                            # Close browsers during global hourly limit to save resources
                            await instance.close_browser()
                            logger.info(f"[MONITOR] Closed browser for instance #{instance.instance_id}: Global hourly limit")
                    except Exception as e:
                        logger.error(f"[MONITOR] Error monitoring instance #{instance.instance_id}: {e}")
                
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            logger.info("[MONITOR] Browser monitoring loop cancelled")
        except Exception as e:
            logger.error(f"[MONITOR] Browser monitoring error: {e}")
