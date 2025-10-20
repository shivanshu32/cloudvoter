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
    "hourly limit",
    "already voted",
    "cooldown",
    "try again later",
    "someone has already voted out of this ip",
    "please come back at your next voting time",
    "wait before voting again"
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
MAX_CONCURRENT_BROWSER_LAUNCHES = 1  # Maximum number of browsers that can launch simultaneously

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
