import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
DB_URI = os.environ.get("DB_URI", "")

ADMINS = list(map(int, os.environ.get("ADMINS", "7618349770 7336381823").split()))

#DUMP = int(os.environ.get("DUMP", "-1002867430238"))
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "Ankit")
SPLIT_SIZE = os.environ.get("SPLIT_SIZE", 2000 * 1024 * 1024)
DEFAULT_THUMB = os.environ.get("DEFAULT_THUMB", "")
