from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from database import (
    is_admin, add_admin, remove_admin, get_button, get_buttons,
    add_button, update_button, delete_button, move_button
)
from keyboards import (
    admin_main_keyboard, admin_buttons_keyboard, admin_button_type_keyboard,
    admin_edit_button_keyboard, admin_admins_keyboard, cancel_keyboard
)
from states import (
    ADMIN_MENU, WAIT_NEW_ADMIN_ID, WAIT_BUTTON_LABEL,
    WAIT_BUTTON_TYPE, WAIT_BUTTON_CONTENT, WAIT_EDIT_LABEL, WAIT_EDIT_CONTENT
)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("❌ ليس لديك صلاحية الوصول لهذا الأمر.")
        return ConversationHandler.END

    await update.message.reply_text(
        f"👑 لوحة التحكم للمشرفين\n\nمرحباً {user.first_name}!",
        reply_markup=admin_main_keyboard()
    )
    return ADMIN_MENU


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data

    if not is_admin(user.id):
        await query.edit_message_text("❌ ليس لديك صلاحية.")
        return ConversationHandler.END

    if data == "admin_main":
        await query.edit_message_text(
            f"👑 لوحة التحكم للمشرفين\n\nمرحباً {user.first_name}!",
            reply_markup=admin_main_keyboard()
        )
        return ADMIN_MENU

    if data == "admin_close":
        await query.delete_message()
        return ConversationHandler.END

    if data == "admin_cancel":
        context.user_data.clear()
        await query.edit_message_text(
            "✅ تم الإلغاء.",
            reply_markup=admin_main_keyboard()
        )
        return ADMIN_MENU

    if data == "admin_manage_root":
        await query.edit_message_text(
            "📋 إدارة الأزرار - القائمة الرئيسية:",
            reply_markup=admin_buttons_keyboard(None)
        )
        return ADMIN_MENU

    if data.startswith("admin_manage_"):
        try:
            parent_id = int(data[len("admin_manage_"):])
        except ValueError:
            await query.edit_message_text("❌ خطأ.")
            return ADMIN_MENU
        btn = get_button(parent_id)
        if not btn:
            await query.edit_message_text("❌ الزر غير موجود.")
            return ADMIN_MENU
        await query.edit_message_text(
            f"📂 إدارة قائمة: *{btn['label']}*",
            parse_mode="Markdown",
            reply_markup=admin_buttons_keyboard(parent_id)
        )
        return ADMIN_MENU

    if data.startswith("admin_edit_"):
        button_id = int(data[len("admin_edit_"):])
        btn = get_button(button_id)
        if not btn:
            await query.edit_message_text("❌ الزر غير موجود.")
            return ADMIN_MENU
        from config import TYPE_ICONS
        icon = TYPE_ICONS.get(btn["type"], "")
        text = (
            f"*تعديل الزر*\n\n"
            f"الاسم: {btn['label']}\n"
            f"النوع: {icon} {btn['type']}\n"
        )
        if btn.get("content"):
            text += f"المحتوى: {btn['content'][:100]}\n"
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=admin_edit_button_keyboard(button_id)
        )
        return ADMIN_MENU

    if data.startswith("admin_move_up_") or data.startswith("admin_move_down_"):
        if "up" in data:
            button_id = int(data[len("admin_move_up_"):])
            direction = "up"
        else:
            button_id = int(data[len("admin_move_down_"):])
            direction = "down"
        move_button(button_id, direction)
        btn = get_button(button_id)
        parent_id = btn["parent_id"] if btn else None
        await query.edit_message_reply_markup(
            reply_markup=admin_buttons_keyboard(parent_id)
        )
        return ADMIN_MENU

    if data.startswith("admin_delete_"):
        button_id = int(data[len("admin_delete_"):])
        btn = get_button(button_id)
        parent_id = btn["parent_id"] if btn else None
        delete_button(button_id)
        await query.edit_message_text(
            "🗑 تم حذف الزر بنجاح.",
            reply_markup=admin_buttons_keyboard(parent_id)
        )
        return ADMIN_MENU

    if data.startswith("admin_add_"):
        parent_context = data[len("admin_add_"):]
        await query.edit_message_text(
            "➕ اختر نوع الزر الجديد:",
            reply_markup=admin_button_type_keyboard(parent_context)
        )
        return WAIT_BUTTON_TYPE

    if data == "admin_manage_admins":
        admins = get_all_admins()
        text = f"👥 قائمة المشرفين ({len(admins)}):"
        await query.edit_message_text(text, reply_markup=admin_admins_keyboard())
        return ADMIN_MENU

    if data == "admin_add_admin":
        context.user_data["action"] = "add_admin"
        await query.edit_message_text(
            "👤 أرسل معرّف المشرف الجديد (User ID):\n\n"
            "للحصول على الـ ID، يمكن للمستخدم إرسال /myid للبوت.",
            reply_markup=cancel_keyboard()
        )
        return WAIT_NEW_ADMIN_ID

    if data.startswith("admin_remove_admin_"):
        admin_id = int(data[len("admin_remove_admin_"):])
        if admin_id == user.id:
            await query.answer("❌ لا يمكنك إزالة نفسك!", show_alert=True)
            return ADMIN_MENU
        remove_admin(admin_id)
        admins = get_all_admins()
        await query.edit_message_text(
            f"✅ تم إزالة المشرف.\n\n👥 قائمة المشرفين ({len(admins)}):",
            reply_markup=admin_admins_keyboard()
        )
        return ADMIN_MENU

    if data.startswith("admin_editlabel_"):
        button_id = int(data[len("admin_editlabel_"):])
        context.user_data["action"] = "edit_label"
        context.user_data["button_id"] = button_id
        btn = get_button(button_id)
        await query.edit_message_text(
            f"✏️ أرسل الاسم الجديد للزر:\n\nالاسم الحالي: *{btn['label']}*",
            parse_mode="Markdown",
            reply_markup=cancel_keyboard()
        )
        return WAIT_EDIT_LABEL

    if data.startswith("admin_editcontent_"):
        button_id = int(data[len("admin_editcontent_"):])
        btn = get_button(button_id)
        if btn["type"] == "menu":
            await query.answer("📂 قوائم المحتوى لا تحتوي على محتوى مباشر.", show_alert=True)
            return ADMIN_MENU
        context.user_data["action"] = "edit_content"
        context.user_data["button_id"] = button_id
        context.user_data["button_type"] = btn["type"]
        if btn["type"] == "text":
            await query.edit_message_text(
                "✏️ أرسل النص الجديد:",
                reply_markup=cancel_keyboard()
            )
        else:
            await query.edit_message_text(
                f"✏️ أرسل {_type_hint(btn['type'])} الجديد/ة:",
                reply_markup=cancel_keyboard()
            )
        return WAIT_EDIT_CONTENT

    if data.startswith("admin_type_"):
        parts = data[len("admin_type_"):].split("_", 1)
        if len(parts) != 2:
            return ADMIN_MENU
        btn_type, parent_context = parts[0], parts[1]
        context.user_data["new_btn_type"] = btn_type
        context.user_data["new_btn_parent"] = parent_context
        await query.edit_message_text(
            f"✏️ أرسل اسم/عنوان الزر الجديد:",
            reply_markup=cancel_keyboard()
        )
        return WAIT_BUTTON_LABEL

    return ADMIN_MENU


def _type_hint(btn_type):
    hints = {
        "photo": "الصورة",
        "file": "الملف",
        "video": "الفيديو",
        "audio": "الصوت",
    }
    return hints.get(btn_type, "المحتوى")


async def wait_button_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    label = update.message.text.strip()
    if not label:
        await update.message.reply_text("❌ الاسم لا يمكن أن يكون فارغاً.", reply_markup=cancel_keyboard())
        return WAIT_BUTTON_LABEL

    context.user_data["new_btn_label"] = label
    btn_type = context.user_data.get("new_btn_type")
    parent_context = context.user_data.get("new_btn_parent")

    if btn_type == "menu":
        parent_id = None if parent_context == "root" else int(parent_context)
        add_button(parent_id, "menu", label, created_by=user.id)
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ تم إنشاء القائمة *{label}* بنجاح!",
            parse_mode="Markdown",
            reply_markup=admin_buttons_keyboard(parent_id)
        )
        return ADMIN_MENU

    if btn_type == "text":
        await update.message.reply_text(
            "📝 الآن أرسل محتوى النص:",
            reply_markup=cancel_keyboard()
        )
        return WAIT_BUTTON_CONTENT

    await update.message.reply_text(
        f"📎 الآن أرسل {_type_hint(btn_type)} المطلوب/ة:",
        reply_markup=cancel_keyboard()
    )
    return WAIT_BUTTON_CONTENT


async def wait_button_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    btn_type = context.user_data.get("new_btn_type")
    label = context.user_data.get("new_btn_label")
    parent_context = context.user_data.get("new_btn_parent")
    parent_id = None if parent_context == "root" else int(parent_context)

    content = None
    file_id = None

    if btn_type == "text":
        if not update.message.text:
            await update.message.reply_text("❌ أرسل نصاً.", reply_markup=cancel_keyboard())
            return WAIT_BUTTON_CONTENT
        content = update.message.text.strip()

    elif btn_type == "photo":
        if not update.message.photo:
            await update.message.reply_text("❌ أرسل صورة.", reply_markup=cancel_keyboard())
            return WAIT_BUTTON_CONTENT
        file_id = update.message.photo[-1].file_id
        content = update.message.caption

    elif btn_type == "file":
        if not update.message.document:
            await update.message.reply_text("❌ أرسل ملفاً.", reply_markup=cancel_keyboard())
            return WAIT_BUTTON_CONTENT
        file_id = update.message.document.file_id
        content = update.message.caption

    elif btn_type == "video":
        if not update.message.video:
            await update.message.reply_text("❌ أرسل فيديو.", reply_markup=cancel_keyboard())
            return WAIT_BUTTON_CONTENT
        file_id = update.message.video.file_id
        content = update.message.caption

    elif btn_type == "audio":
        if not (update.message.audio or update.message.voice):
            await update.message.reply_text("❌ أرسل ملف صوتي.", reply_markup=cancel_keyboard())
            return WAIT_BUTTON_CONTENT
        file_id = (update.message.audio or update.message.voice).file_id
        content = update.message.caption

    add_button(parent_id, btn_type, label, content=content, file_id=file_id, created_by=user.id)
    context.user_data.clear()
    await update.message.reply_text(
        f"✅ تم إضافة الزر *{label}* بنجاح!",
        parse_mode="Markdown",
        reply_markup=admin_buttons_keyboard(parent_id)
    )
    return ADMIN_MENU


async def wait_new_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    text = update.message.text.strip()
    try:
        new_admin_id = int(text)
    except ValueError:
        await update.message.reply_text("❌ الرجاء إرسال معرّف رقمي صحيح.", reply_markup=cancel_keyboard())
        return WAIT_NEW_ADMIN_ID

    add_admin(new_admin_id, username=None)
    context.user_data.clear()
    await update.message.reply_text(
        f"✅ تمت إضافة المشرف {new_admin_id} بنجاح!",
        reply_markup=admin_admins_keyboard()
    )
    return ADMIN_MENU


async def wait_edit_label(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    new_label = update.message.text.strip()
    button_id = context.user_data.get("button_id")
    update_button(button_id, label=new_label)
    btn = get_button(button_id)
    parent_id = btn["parent_id"] if btn else None
    context.user_data.clear()
    await update.message.reply_text(
        f"✅ تم تحديث الاسم إلى *{new_label}*.",
        parse_mode="Markdown",
        reply_markup=admin_buttons_keyboard(parent_id)
    )
    return ADMIN_MENU


async def wait_edit_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    button_id = context.user_data.get("button_id")
    btn_type = context.user_data.get("button_type")
    btn = get_button(button_id)
    parent_id = btn["parent_id"] if btn else None

    content = None
    file_id = None

    if btn_type == "text":
        if not update.message.text:
            await update.message.reply_text("❌ أرسل نصاً.", reply_markup=cancel_keyboard())
            return WAIT_EDIT_CONTENT
        content = update.message.text.strip()

    elif btn_type == "photo":
        if not update.message.photo:
            await update.message.reply_text("❌ أرسل صورة.", reply_markup=cancel_keyboard())
            return WAIT_EDIT_CONTENT
        file_id = update.message.photo[-1].file_id
        content = update.message.caption

    elif btn_type == "file":
        if not update.message.document:
            await update.message.reply_text("❌ أرسل ملفاً.", reply_markup=cancel_keyboard())
            return WAIT_EDIT_CONTENT
        file_id = update.message.document.file_id
        content = update.message.caption

    elif btn_type == "video":
        if not update.message.video:
            await update.message.reply_text("❌ أرسل فيديو.", reply_markup=cancel_keyboard())
            return WAIT_EDIT_CONTENT
        file_id = update.message.video.file_id
        content = update.message.caption

    elif btn_type == "audio":
        if not (update.message.audio or update.message.voice):
            await update.message.reply_text("❌ أرسل ملف صوتي.", reply_markup=cancel_keyboard())
            return WAIT_EDIT_CONTENT
        file_id = (update.message.audio or update.message.voice).file_id
        content = update.message.caption

    update_button(button_id, content=content, file_id=file_id)
    context.user_data.clear()
    await update.message.reply_text(
        "✅ تم تحديث المحتوى بنجاح!",
        reply_markup=admin_buttons_keyboard(parent_id)
    )
    return ADMIN_MENU
