import os
from dotenv import load_dotenv

load_dotenv()

# Telegram API
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SESSION_NAME = os.getenv("SESSION_NAME", "tg_auto_bot")

# Owner & Log
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))

# Force Subscribe
FORCE_SUB_CHANNEL = os.getenv("FORCE_SUB_CHANNEL", "")
FORCE_SUB_CHANNEL_ID = int(os.getenv("FORCE_SUB_CHANNEL_ID", "0")) if os.getenv("FORCE_SUB_CHANNEL_ID") else 0

# Support
SUPPORT_CHANNEL = os.getenv("SUPPORT_CHANNEL", "@YourSupport")

# Auto React
AUTO_REACT_CHATS = [
    int(x.strip()) for x in os.getenv("AUTO_REACT_CHATS", "").split(",") if x.strip()
]
REACT_EMOJIS = os.getenv("REACT_EMOJIS", "👍 ❤️ 🔥 👏 😍").split()

# Clone target
DEFAULT_CLONE_TARGET = int(os.getenv("DEFAULT_CLONE_TARGET", "0")) if os.getenv("DEFAULT_CLONE_TARGET") else None

# Reaction Delay
REACT_DELAY_MIN = float(os.getenv("REACT_DELAY_MIN", "1.0"))
REACT_DELAY_MAX = float(os.getenv("REACT_DELAY_MAX", "3.5"))
