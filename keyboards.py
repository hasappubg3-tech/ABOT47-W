from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import get_buttons, get_button, get_all_admins
from config import TYPE_ICONS, BUTTON_TYPES


def user_menu_keyboard(parent_id=None):
    buttons = get_buttons(parent_id)
    keyboard = []
    for btn in buttons:
        icon = TYPE_ICONS.get(btn["type"], "")
        keyboard.append([
            InlineKeyboardButton(
                f"{icon} {btn['label']}",
                callback_data=f"view_{btn['id']}"
            )
        ])
    if parent_id is not None:
        btn_obj = get_button(parent_id)
        if btn_obj:
            back_parent = btn_obj.get("parent_id")
            if back_parent is None:
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="view_root")])
            else:
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"view_{back_parent}")])
    return InlineKeyboardMarkup(keyboard) if keyboard else None


def admin_main_keyboard():
    keyboard = [
        [InlineKeyboardButton("📋 إدارة الأزرار", callback_data="admin_manage_root")],
        [InlineKeyboardButton("👥 إدارة المشرفين", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("❌ إغلاق", callback_data="admin_close")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_buttons_keyboard(parent_id=None):
    buttons = get_buttons(parent_id)
    keyboard = []

    for btn in buttons:
        icon = TYPE_ICONS.get(btn["type"], "")
        keyboard.append([
            InlineKeyboardButton(f"{icon} {btn['label']}", callback_data=f"admin_edit_{btn['id']}"),
            InlineKeyboardButton("⬆️", callback_data=f"admin_move_up_{btn['id']}"),
            InlineKeyboardButton("⬇️", callback_data=f"admin_move_down_{btn['id']}"),
            InlineKeyboardButton("🗑", callback_data=f"admin_delete_{btn['id']}"),
        ])

    keyboard.append([InlineKeyboardButton("➕ إضافة زر جديد", callback_data=f"admin_add_{parent_id if parent_id else 'root'}")])

    if parent_id is not None:
        btn_obj = get_button(parent_id)
        if btn_obj:
            back_parent = btn_obj.get("parent_id")
            if back_parent is None:
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_manage_root")])
            else:
                keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_manage_{back_parent}")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="admin_main")])

    return InlineKeyboardMarkup(keyboard)


def admin_button_type_keyboard(parent_context):
    keyboard = []
    for type_key, type_label in BUTTON_TYPES.items():
        keyboard.append([
            InlineKeyboardButton(type_label, callback_data=f"admin_type_{type_key}_{parent_context}")
        ])
    keyboard.append([InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")])
    return InlineKeyboardMarkup(keyboard)


def admin_edit_button_keyboard(button_id):
    keyboard = [
        [InlineKeyboardButton("✏️ تعديل الاسم", callback_data=f"admin_editlabel_{button_id}")],
        [InlineKeyboardButton("✏️ تعديل المحتوى", callback_data=f"admin_editcontent_{button_id}")],
        [InlineKeyboardButton("🗑 حذف الزر", callback_data=f"admin_delete_{button_id}")],
    ]
    btn = get_button(button_id)
    if btn and btn["type"] == "menu":
        keyboard.insert(0, [
            InlineKeyboardButton("📂 فتح القائمة وإدارة محتواها", callback_data=f"admin_manage_{button_id}")
        ])

    parent_id = btn["parent_id"] if btn else None
    if parent_id is None:
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_manage_root")])
    else:
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=f"admin_manage_{parent_id}")])
    return InlineKeyboardMarkup(keyboard)


def admin_admins_keyboard():
    admins = get_all_admins()
    keyboard = []
    for admin in admins:
        name = admin.get("username") or str(admin["user_id"])
        keyboard.append([
            InlineKeyboardButton(f"👤 {name}", callback_data=f"admin_view_admin_{admin['user_id']}"),
            InlineKeyboardButton("🗑 إزالة", callback_data=f"admin_remove_admin_{admin['user_id']}"),
        ])
    keyboard.append([InlineKeyboardButton("➕ إضافة مشرف جديد", callback_data="admin_add_admin")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="admin_main")])
    return InlineKeyboardMarkup(keyboard)


def cancel_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("❌ إلغاء", callback_data="admin_cancel")]])
