import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters
)
from database import init_db, add_admin, is_admin
from config import BOT_TOKEN
from handlers.user_handler import start, button_callback
from handlers.admin_handler import (
    admin_command, admin_callback,
    wait_button_label, wait_button_content,
    wait_new_admin_id, wait_edit_label, wait_edit_content
)
from states import (
    ADMIN_MENU, WAIT_NEW_ADMIN_ID, WAIT_BUTTON_LABEL,
    WAIT_BUTTON_TYPE, WAIT_BUTTON_CONTENT, WAIT_EDIT_LABEL, WAIT_EDIT_CONTENT
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def myid_command(update: Update, context):
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 معرّفك: `{user.id}`\n"
        f"الاسم: {user.first_name}",
        parse_mode="Markdown"
    )


async def post_init(application):
    super_admin_env = os.environ.get("SUPER_ADMIN_ID", "")
    if super_admin_env:
        try:
            admin_id = int(super_admin_env.strip())
            if not is_admin(admin_id):
                add_admin(admin_id)
                logger.info(f"Super admin {admin_id} added from environment.")
        except ValueError:
            pass


def main():
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN غير موجود!")
        return

    init_db()

    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    admin_conv = ConversationHandler(
        entry_points=[
            CommandHandler("admin", admin_command),
            CallbackQueryHandler(admin_callback, pattern="^admin_"),
        ],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_callback, pattern="^admin_"),
            ],
            WAIT_BUTTON_TYPE: [
                CallbackQueryHandler(admin_callback, pattern="^admin_type_"),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
            WAIT_BUTTON_LABEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, wait_button_label),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
            WAIT_BUTTON_CONTENT: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.Document.ALL |
                     filters.VIDEO | filters.AUDIO | filters.VOICE) & ~filters.COMMAND,
                    wait_button_content
                ),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
            WAIT_NEW_ADMIN_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, wait_new_admin_id),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
            WAIT_EDIT_LABEL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, wait_edit_label),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
            WAIT_EDIT_CONTENT: [
                MessageHandler(
                    (filters.TEXT | filters.PHOTO | filters.Document.ALL |
                     filters.VIDEO | filters.AUDIO | filters.VOICE) & ~filters.COMMAND,
                    wait_edit_content
                ),
                CallbackQueryHandler(admin_callback, pattern="^admin_cancel"),
            ],
        },
        fallbacks=[
            CommandHandler("admin", admin_command),
        ],
        per_message=False,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myid", myid_command))
    app.add_handler(admin_conv)
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^view_"))

    logger.info("البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
