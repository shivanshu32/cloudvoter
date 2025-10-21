"""
Configuration file for CloudVoter
"""

# Bright Data Proxy Credentials
# Update these when credentials change
BRIGHT_DATA_USERNAME = "hl_47ba96ab"
BRIGHT_DATA_PASSWORD = "tcupn0cw7pbz"

# Target voting URLs
TARGET_URLS = [
    "https://www.cutebabyvote.com/october-2025/?contest=photo-detail&photo_id=463146"
]

# Legacy single URL support
TARGET_URL = TARGET_URLS[0]

# Timing configuration (in seconds)
NORMAL_CYCLE_WAIT = 31 * 60  # 31 minutes between voting cycles
VOTE_RESPONSE_WAIT = 3       # Wait time after clicking vote button

# Browser configuration
HEADLESS_MODE = True
BROWSER_WIDTH = 1920
BROWSER_HEIGHT = 1080

# Resource blocking configuration (reduces page load size by 60-80%)
ENABLE_RESOURCE_BLOCKING = True  # Block images, CSS, fonts, tracking scripts
BLOCK_IMAGES = True              # Block all images (jpg, png, gif, svg, etc.)
BLOCK_STYLESHEETS = True         # Block CSS files (may affect page appearance)
BLOCK_FONTS = True               # Block font files
BLOCK_TRACKING = True            # Block analytics and tracking scripts

# Vote button selectors
VOTE_BUTTON_SELECTORS = [
    ".photo_vote",
    "[data-item]",
    ".vote-button", 
    "button[class*='vote']",
    "input[type='button'][value*='VOTE']",
    ".pc-image-info-box-button-btn",
    "#vote-btn",
    "[onclick*='vote']"
]

# Message detection selectors
MESSAGE_SELECTORS = [
    ".alert",
    ".message", 
    ".notification",
    ".pc-image-info-box-button-btn-text",
    "[class*='message']",
    "[class*='alert']",
    ".status-message",
    ".vote-status"
]

# Success message patterns (case-insensitive)
SUCCESS_PATTERNS = [
    "thank you for vote",
    "vote successful", 
    "your vote has been recorded",
    "vote counted",
    "thanks for voting"
]

# Failure/cooldown message patterns (case-insensitive)
FAILURE_PATTERNS = [
    "hourly voting limit",  # Current message format (has "voting" in between)
    "hourly limit",         # Legacy format (keep for compatibility)
    "already voted",
    "cooldown",
    "try again later",
    "someone has already voted out of this ip",
    "please come back at your next voting time",
    "wait before voting again"
]

# Global hourly limit patterns (these affect ALL instances, not just one)
# Only these patterns should trigger global pause of all instances
GLOBAL_HOURLY_LIMIT_PATTERNS = [
    "hourly voting limit",  # Current message format
    "hourly limit"          # Legacy format
]

# Instance-specific cooldown patterns (only affect the specific instance)
# These should NOT trigger global pause
INSTANCE_COOLDOWN_PATTERNS = [
    "please come back at your next voting time",  # 30-minute cooldown
    "already voted",  # Instance-specific
    "wait before voting again",  # Instance-specific
    "someone has already voted out of this ip"  # Proxy assigned different IP that already voted
]

# Browser monitoring configuration
ENABLE_BROWSER_MONITORING = True
BROWSER_IDLE_TIMEOUT = 3
BROWSER_LOGIN_TIMEOUT = 5
BROWSER_PAUSED_TIMEOUT = 5
BROWSER_ERROR_TIMEOUT = 2
MONITORING_CHECK_INTERVAL = 60

# Sequential browser launch configuration (prevents memory overload)
BROWSER_LAUNCH_DELAY = 5  # Seconds to wait between browser launches
MAX_CONCURRENT_BROWSER_LAUNCHES = 3  # Maximum number of browsers that can launch simultaneously (increased from 1 to prevent deadlock)

# Retry configuration (minutes to wait before retrying after failure)
RETRY_DELAY_TECHNICAL = 5   # Technical failures (button not found, exception, etc.)
RETRY_DELAY_COOLDOWN = 31   # IP cooldown / hourly limit (respect voting restrictions)

# Proxy retry configuration
PROXY_MAX_RETRIES = 3       # Maximum retries for getting proxy IP
PROXY_RETRY_DELAY = 2       # Base delay in seconds (exponential backoff)
PROXY_503_CIRCUIT_BREAKER_THRESHOLD = 3  # Consecutive 503s before pausing
PROXY_503_PAUSE_DURATION = 60  # Seconds to pause after circuit breaker trips

# Session scanning configuration
SESSION_SCAN_INTERVAL = 60  # Seconds between saved session scans (reduced from ~38s)

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
