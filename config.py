import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7401297240:AAHdIQPEuPOvyo3LlG2-EXT-8A5grFXJ_6c")
API_ID = int(os.environ.get("API_ID", "22287041"))
API_HASH = os.environ.get("API_HASH", "c149386dcd58a40fa9fe60e632e161d4")
DB_URI = os.environ.get("DB_URI", "mongodb+srv://mongo920:LAZkTQrPibzZDArm@cluster0.wbyyv.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMINS = list(map(int, os.environ.get("ADMINS", "7597122443 891959176").split()))
DUMP = int(os.environ.get("DUMP", "-1002201376693"))
WATERMARK_TEXT = os.environ.get("WATERMARK_TEXT", "@NaughtyX111 (TG)")
SPLIT_SIZE = os.environ.get("SPLIT_SIZE", 2000 * 1024 * 1024)
DEFAULT_THUMB = os.environ.get("DEFAULT_THUMB", "https://envs.sh/No1.jpg")
