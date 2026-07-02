import os

# ---------- BOT CREDENTIALS ----------
API_ID = int(os.environ.get("API_ID", "34422904"))
API_HASH = os.environ.get("API_HASH", "7e0002469784f47fc08a6b3d93d7ebed")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")

# ---------- OWNER / ADMIN ----------
OWNER_ID = int(os.environ.get("OWNER_ID", "5349573682"))
ADMINS = [int(x) for x in os.environ.get("ADMINS", "5349573682").split()]

# ---------- DATABASE ----------
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://your_mongo_url")
DATABASE_NAME = os.environ.get("DATABASE_NAME", "ugdev_db")

# ---------- DEFAULT CREDIT ----------
CREDIT = os.environ.get("CREDIT", "✩°𓏲 кяιѕнηα ⋆🌿")

# ---------- API EXTRACTORS (from ram.py) ----------
API_BASE = os.environ.get("API_BASE", "https://backend.multistreaming.site/api")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# CW (ClassPlus) APIs
CW_ALL_BATCHES = os.environ.get("CW_ALL_BATCHES", "https://cw-ut-apis-e37c22944d2f.herokuapp.com/api/batches")
CW_BATCH_API = os.environ.get("CW_BATCH_API", "https://cw-api-website.vercel.app/batch/{}")
CW_TOPIC_API = os.environ.get("CW_TOPIC_API", "https://cw-api-website.vercel.app/batch?batchid={}&topicid={}")
CW_VIDEO_API = os.environ.get("CW_VIDEO_API", "https://cw-vid-virid.vercel.app/get_video_details?name={}")

# Careerwill
CAREERWILL_BUILD_ID = os.environ.get("CAREERWILL_BUILD_ID", "")
CAREERWILL_COOKIE = os.environ.get("CAREERWILL_COOKIE", "")
CAREERWILL_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://web.careerwill.com/live-classes",
    "Accept": "application/json",
}
if CAREERWILL_COOKIE:
    CAREERWILL_HEADERS["Cookie"] = CAREERWILL_COOKIE

# ---------- AUTH MESSAGES ----------
AUTH_MESSAGES = {
    "subscription_active": """<b>🎉 Subscription Activated!</b>\n\nYour subscription will expire on {expiry_date}.""",
    "user_added": """✅ User Added!\nName: {name}\nID: {user_id}\nExpiry: {expiry_date}""",
    "not_admin": "⚠️ Not authorized.",
    "access_denied": "❌ Access Denied. Contact admin.",
}
