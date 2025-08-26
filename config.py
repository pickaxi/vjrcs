import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7726282640:AAGSWtdGlOoRAlVDDMx_fJhX20BZAtfguD8")
API_ID = int(os.environ.get("API_ID", "28735699"))
API_HASH = os.environ.get("API_HASH", "2e19c326d8cb322df7c15d7b7e84d1f3")
DB_URI = os.environ.get("DB_URI", "mongodb+srv://ridhatlog:RcZ4EVi6hzwSaarZ@cluster0.dxj0ntg.mongodb.net/?retryWrites=true&w=majority")

ADMINS = list(map(int, os.environ.get("ADMINS", "6573328336 7794867502").split()))
#DUMP = int(os.environ.get("DUMP", "-1002867430238"))
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "Ankit")
SPLIT_SIZE = os.environ.get("SPLIT_SIZE", 2000 * 1024 * 1024)
DEFAULT_THUMB = os.environ.get("DEFAULT_THUMB", "")
