"""
Core Voting Engine for CloudVoter
Adapted from brightdatavoter.py for web-based deployment
"""

import asyncio
import json
import logging
import os
import random
import string
import time
from datetime import datetime, timedelta
from typing import Dict, Set, Optional
from playwright.async_api import async_playwright
from vote_logger import VoteLogger
from config import (
    ENABLE_RESOURCE_BLOCKING, BLOCK_IMAGES, BLOCK_STYLESHEETS, 
    BLOCK_FONTS, BLOCK_TRACKING
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
                    self.last_vote_time = datetime.now()  # Server is IST
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
                    # Count didn't increase - check for hourly limit message
                    logger.info(f"[FAILED] Vote count did not increase: {initial_count} -> {final_count}")
                    
                    page_content = await self.page.content()
                    cooldown_message = ""
                    if any(pattern in page_content.lower() for pattern in ['hourly limit', 'already voted', 'cooldown']):
                        logger.warning(f"[VOTE] Instance #{self.instance_id} hit hourly limit")
                        
                        # Extract cooldown message
                        try:
                            if 'hourly limit' in page_content.lower():
                                cooldown_message = "Hourly voting limit reached"
                            elif 'already voted' in page_content.lower():
                                cooldown_message = "Already voted"
                            elif 'cooldown' in page_content.lower():
                                cooldown_message = "In cooldown period"
                        except:
                            cooldown_message = "Hourly limit detected"
                        
                        # Log hourly limit to CSV with comprehensive data
                        self.vote_logger.log_vote_attempt(
                            instance_id=self.instance_id,
                            instance_name=f"Instance_{self.instance_id}",
                            time_of_click=click_time,
                            status="failed",
                            voting_url=self.target_url,
                            cooldown_message=cooldown_message,
                            failure_type="ip_cooldown",
                            failure_reason="IP in cooldown period - hourly limit reached",
                            initial_vote_count=initial_count,
                            final_vote_count=final_count,
                            proxy_ip=self.proxy_ip,
                            session_id=self.session_id or "",
                            click_attempts=click_attempts,
                            error_message="",
                            browser_closed=True
                        )
                        
                        # Close browser before cooldown
                        logger.info(f"[CLEANUP] Closing browser after hourly limit detection")
                        await self.close_browser()
                        
                        # Trigger global hourly limit handling
                        if self.voter_manager:
                            asyncio.create_task(self.voter_manager.handle_hourly_limit())
                    else:
                        logger.error(f"[FAILED] Vote failed - count unchanged and no error message")
                        
                        # Log failed vote with comprehensive data
                        self.vote_logger.log_vote_attempt(
                            instance_id=self.instance_id,
                            instance_name=f"Instance_{self.instance_id}",
                            time_of_click=click_time,
                            status="failed",
                            voting_url=self.target_url,
                            cooldown_message="",
                            failure_type="technical",
                            failure_reason="Vote count did not increase",
                            initial_vote_count=initial_count,
                            final_vote_count=final_count,
                            proxy_ip=self.proxy_ip,
                            session_id=self.session_id or "",
                            click_attempts=click_attempts,
                            error_message="",
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
                    
                elif any(pattern in page_content.lower() for pattern in ['hourly limit', 'already voted', 'cooldown']):
                    logger.warning(f"[VOTE] Instance #{self.instance_id} hit hourly limit")
                    
                    # Log hourly limit to CSV with comprehensive data
                    self.vote_logger.log_vote_attempt(
                        instance_id=self.instance_id,
                        instance_name=f"Instance_{self.instance_id}",
                        time_of_click=click_time,
                        status="failed",
                        voting_url=self.target_url,
                        cooldown_message="Hourly voting limit reached (fallback detection)",
                        failure_type="ip_cooldown",
                        failure_reason="IP in cooldown period - hourly limit reached",
                        initial_vote_count=None,
                        final_vote_count=None,
                        proxy_ip=self.proxy_ip,
                        session_id=self.session_id or "",
                        click_attempts=click_attempts,
                        error_message="",
                        browser_closed=True
                    )
                    
                    # Close browser before cooldown
                    logger.info(f"[CLEANUP] Closing browser after hourly limit detection (fallback)")
                    await self.close_browser()
                    
                    # Trigger global hourly limit handling
                    if self.voter_manager:
                        asyncio.create_task(self.voter_manager.handle_hourly_limit())
                    
                    return False
                
                return False
            
            return False
            
        except Exception as e:
            logger.error(f"[VOTE] Instance #{self.instance_id} vote failed: {e}")
            self.failed_attempts += 1
            
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
                # Check if paused
                await self.pause_event.wait()
                
                # Navigate to voting page
                if not await self.navigate_to_voting_page():
                    logger.warning(f"[CYCLE] Instance #{self.instance_id} navigation failed, retrying...")
                    await asyncio.sleep(30)
                    continue
                
                # CRITICAL: Check for hourly limit AFTER navigation
                if await self.check_hourly_voting_limit():
                    logger.info(f"[LIMIT] Instance #{self.instance_id} hourly voting limit detected - closing browser")
                    await self.close_browser()
                    
                    # Trigger global hourly limit handling
                    if self.voter_manager:
                        asyncio.create_task(self.voter_manager.handle_hourly_limit())
                    
                    # Pause this instance
                    self.is_paused = True
                    self.pause_event.clear()
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
                    logger.info(f"[CYCLE] Instance #{self.instance_id} waiting 31 minutes...")
                    await asyncio.sleep(31 * 60)  # 31 minute wait
                else:
                    self.status = "⏳ Cooldown"
                    logger.info(f"[CYCLE] Instance #{self.instance_id} in cooldown, waiting...")
                    await asyncio.sleep(31 * 60)
                
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
    
    async def get_proxy_ip(self, excluded_ips: Set[str] = None) -> Optional[tuple]:
        """Get unique IP from Bright Data proxy"""
        try:
            import urllib.request
            import json
            
            # Generate unique session ID
            session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
            
            # Create proxy auth with session
            base_auth = f"brd-customer-{self.proxy_api.username}-zone-{self.proxy_api.zone}-country-in-session-{session_id}"
            proxy_auth = f"{base_auth}:{self.proxy_api.password}"
            
            proxy = f'http://{proxy_auth}@{self.proxy_api.proxy_host}:{self.proxy_api.proxy_port}'
            
            opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({'https': proxy, 'http': proxy})
            )
            
            response = opener.open('https://httpbin.org/ip')
            result = response.read().decode()
            ip_data = json.loads(result)
            
            assigned_ip = ip_data.get('origin', '').split(',')[0].strip()
            
            if assigned_ip:
                if excluded_ips and assigned_ip in excluded_ips:
                    logger.warning(f"[IP] IP {assigned_ip} already in use, retrying...")
                    return None
                
                logger.info(f"[IP] Assigned IP: {assigned_ip}")
                return (assigned_ip, self.proxy_api.proxy_port)
            
            return None
            
        except Exception as e:
            logger.error(f"[IP] Error getting proxy IP: {e}")
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
            
            proxy_ip = session_info.get('proxy_ip', f'session_{instance_id}')
            
            # Check if instance is already running by instance ID
            for ip, existing_instance in self.active_instances.items():
                if existing_instance.instance_id == instance_id:
                    logger.warning(f"[SESSION] Instance #{instance_id} already running with IP {ip}")
                    return None
            
            # Get unique IP from Bright Data
            excluded_ips = set(self.active_instances.keys()) | self.used_ips
            ip_result = await self.get_proxy_ip(excluded_ips)
            
            if not ip_result:
                logger.error(f"[SESSION] Could not get unique IP for instance #{instance_id}")
                return None
            
            new_proxy_ip, proxy_port = ip_result
            
            # Create session-specific proxy config
            session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
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
                        logger.info(f"[HOURLY_LIMIT] ✅ Hourly limit expired - Resuming instances")
                        
                        # Clear global limit
                        self.global_hourly_limit = False
                        self.global_reactivation_time = None
                        
                        # Resume all paused instances
                        resumed_count = 0
                        for ip, instance in self.active_instances.items():
                            if instance.is_paused and "Hourly Limit" in instance.status:
                                instance.is_paused = False
                                instance.pause_event.set()
                                instance.status = "▶️ Resumed"
                                resumed_count += 1
                                logger.info(f"[HOURLY_LIMIT] Resumed instance #{instance.instance_id}")
                        
                        logger.info(f"[HOURLY_LIMIT] Resumed {resumed_count} instances")
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
