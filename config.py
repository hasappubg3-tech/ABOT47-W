import os

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

SUPER_ADMIN_IDS = []

BUTTON_TYPES = {
    "menu": "📂 قائمة",
    "text": "📝 نص",
    "photo": "🖼 صورة",
    "file": "📎 ملف",
    "video": "🎬 فيديو",
    "audio": "🎵 صوت",
}

TYPE_ICONS = {
    "menu": "📂",
    "text": "📝",
    "photo": "🖼",
    "file": "📎",
    "video": "🎬",
    "audio": "🎵",
}
