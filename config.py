import os

# Telegram API
TG_API_ID = int(os.environ.get("TG_API_ID", "0"))
TG_API_HASH = os.environ.get("TG_API_HASH", "")
TG_SESSION_STRING = os.environ.get("TG_SESSION_STRING", "")
TG_CHANNEL_ID = int(os.environ.get("TG_CHANNEL_ID", "0"))

# Site
SITE_USER = os.environ.get("SITE_USER", "")
SITE_PASS = os.environ.get("SITE_PASS", "")
SITE_BASE_URL = "https://6lotteryapi.com"
SITE_ORIGIN = "https://6windk5.com"

# Behavior
DRY_RUN = os.environ.get("DRY_RUN", "true").lower() == "true"
MIN_BET = 100
MAX_BET = 100000

# Signal Regex
SIGNAL_REGEX = (
    r'Period\s+(\d+)\s*'
    r'.*?SIGNAL\s*→\s*(BIG|SMALL)'
    r'.*?Bet:\s*([\d,]+)'
    r'.*?Bot\s*Step:\s*(\d+)x'
)
