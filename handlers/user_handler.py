from telegram import Update
from telegram.ext import ContextTypes
from database import get_button, get_buttons
from keyboards import user_menu_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = get_buttons(None)
    keyboard = user_menu_keyboard(None)
    text = "👋 أهلاً بك! اختر من القائمة أدناه:"
    if not buttons:
        text = "👋 أهلاً بك!\nلا توجد أزرار متاحة حالياً. يرجى التواصل مع المشرف."
        await update.message.reply_text(text)
        return
    await update.message.reply_text(text, reply_markup=keyboard)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "view_root":
        buttons = get_buttons(None)
        keyboard = user_menu_keyboard(None)
        if not buttons:
            await query.edit_message_text("لا توجد أزرار متاحة حالياً.")
            return
        await query.edit_message_text("👋 القائمة الرئيسية:", reply_markup=keyboard)
        return

    if data.startswith("view_"):
        button_id = int(data[5:])
        btn = get_button(button_id)
        if not btn:
            await query.edit_message_text("❌ الزر غير موجود.")
            return

        btn_type = btn["type"]

        if btn_type == "menu":
            sub_buttons = get_buttons(button_id)
            keyboard = user_menu_keyboard(button_id)
            if not sub_buttons:
                await query.edit_message_text(
                    f"📂 *{btn['label']}*\n\nهذه القائمة فارغة حالياً.",
                    parse_mode="Markdown",
                    reply_markup=user_menu_keyboard(button_id)
                )
            else:
                await query.edit_message_text(
                    f"📂 *{btn['label']}*\n\nاختر من القائمة:",
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )

        elif btn_type == "text":
            content = btn.get("content") or "لا يوجد محتوى."
            parent_id = btn.get("parent_id")
            if parent_id is None:
                keyboard = user_menu_keyboard(None)
                back_text = "🔙 رجوع للقائمة الرئيسية"
            else:
                keyboard = user_menu_keyboard(parent_id)
                back_text = "🔙 رجوع"

            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            back_data = "view_root" if parent_id is None else f"view_{parent_id}"
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton(back_text, callback_data=back_data)]])

            await query.edit_message_text(
                f"📝 *{btn['label']}*\n\n{content}",
                parse_mode="Markdown",
                reply_markup=back_keyboard
            )

        elif btn_type == "photo":
            parent_id = btn.get("parent_id")
            back_data = "view_root" if parent_id is None else f"view_{parent_id}"
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]])
            caption = btn.get("content") or btn["label"]
            file_id = btn.get("file_id")
            if file_id:
                await query.message.reply_photo(
                    photo=file_id,
                    caption=f"🖼 *{btn['label']}*\n\n{caption}" if btn.get("content") else f"🖼 *{btn['label']}*",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard
                )
                await query.delete_message()
            else:
                await query.edit_message_text("❌ لا توجد صورة مرفقة.", reply_markup=back_keyboard)

        elif btn_type == "file":
            parent_id = btn.get("parent_id")
            back_data = "view_root" if parent_id is None else f"view_{parent_id}"
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]])
            file_id = btn.get("file_id")
            if file_id:
                caption = btn.get("content") or btn["label"]
                await query.message.reply_document(
                    document=file_id,
                    caption=f"📎 *{btn['label']}*\n\n{caption}" if btn.get("content") else f"📎 *{btn['label']}*",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard
                )
                await query.delete_message()
            else:
                await query.edit_message_text("❌ لا يوجد ملف مرفق.", reply_markup=back_keyboard)

        elif btn_type == "video":
            parent_id = btn.get("parent_id")
            back_data = "view_root" if parent_id is None else f"view_{parent_id}"
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]])
            file_id = btn.get("file_id")
            if file_id:
                caption = btn.get("content") or btn["label"]
                await query.message.reply_video(
                    video=file_id,
                    caption=f"🎬 *{btn['label']}*\n\n{caption}" if btn.get("content") else f"🎬 *{btn['label']}*",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard
                )
                await query.delete_message()
            else:
                await query.edit_message_text("❌ لا يوجد فيديو مرفق.", reply_markup=back_keyboard)

        elif btn_type == "audio":
            parent_id = btn.get("parent_id")
            back_data = "view_root" if parent_id is None else f"view_{parent_id}"
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 رجوع", callback_data=back_data)]])
            file_id = btn.get("file_id")
            if file_id:
                caption = btn.get("content") or btn["label"]
                await query.message.reply_audio(
                    audio=file_id,
                    caption=f"🎵 *{btn['label']}*\n\n{caption}" if btn.get("content") else f"🎵 *{btn['label']}*",
                    parse_mode="Markdown",
                    reply_markup=back_keyboard
                )
                await query.delete_message()
            else:
                await query.edit_message_text("❌ لا يوجد صوت مرفق.", reply_markup=back_keyboard)
