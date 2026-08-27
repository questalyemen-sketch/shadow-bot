import os

# =========================================================
# Shadow Bot - Configuration
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ضع Telegram ID الخاص بك في Railway
# مثال:
# ADMIN_ID=123456789
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

BOT_NAME = "Shadow"
OWNER_NAME = "صالح الخليفي"

# اسم قاعدة البيانات
DATABASE_NAME = "shadow.db"

# عدد النتائج التي نبحث فيها
MAX_SEARCH_RESULTS = 5