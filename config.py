import os
from typing import List, Union
from dotenv import load_dotenv

load_dotenv()

API_ID_RAW = os.getenv("API_ID", "")
try:
    API_ID = int(API_ID_RAW) if API_ID_RAW.strip() else None
except ValueError:
    API_ID = None

API_HASH = os.getenv("API_HASH", "").strip()
SESSION_NAME = os.getenv("SESSION_NAME", "telegram_userbot").strip()
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "").strip() or None
STRING_SESSION = os.getenv("STRING_SESSION", "").strip()

# Parse target chats
raw_chats = os.getenv("TARGET_CHATS", "").strip()
TARGET_CHATS: List[Union[int, str]] = []
if raw_chats:
    for item in raw_chats.split(","):
        cleaned = item.strip()
        if not cleaned:
            continue
        try:
            # Jika integer ID (e.g. -100123456789 atau 12345678)
            TARGET_CHATS.append(int(cleaned))
        except ValueError:
            # Jika username string (e.g. @grupname atau grupname)
            TARGET_CHATS.append(cleaned)

# Parse filter keywords
raw_keywords = os.getenv("FILTER_KEYWORDS", "").strip()
FILTER_KEYWORDS: List[str] = []
if raw_keywords:
    FILTER_KEYWORDS = [k.strip().lower() for k in raw_keywords.split(",") if k.strip()]

# Output options
OUTPUT_FORMAT = os.getenv("OUTPUT_FORMAT", "both").strip().lower()
OUTPUT_FILE_JSON = os.getenv("OUTPUT_FILE_JSON", "extracted_links.json").strip()
OUTPUT_FILE_TXT = os.getenv("OUTPUT_FILE_TXT", "extracted_links.txt").strip()
ALLOW_DUPLICATES = os.getenv("ALLOW_DUPLICATES", "false").strip().lower() in ("true", "1", "yes")
