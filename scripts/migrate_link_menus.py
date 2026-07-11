"""
سكربت لمرة واحدة: يربط قائمتي (1966 <-> 3101) و(2017 <-> 3106) كقوائم توأم.
1) يفرّغ 3101 و3106 تماماً (حذف نهائي لكل ما بداخلهما).
2) ينسخ محتويات 1966 إلى 3101 ومحتويات 2017 إلى 3106، مع تسجيل "التوأمة"
   على مستوى كل زر/عنصر محتوى مقابل، بحيث تعمل المزامنة التلقائية
   (bot/data_access.py: add_btn/upd_btn_label/del_btn/add_item/... ) من الآن فصاعداً.
تشغيله مرة واحدة فقط.
"""
import sys
sys.path.insert(0, "/home/runner/workspace")

from bot.data_access import _col, _next_id, set_twin, set_item_twin, get_btn_any


def wipe_subtree(bid):
    """حذف نهائي (hard delete) لكل أبناء bid وكل بياناتهم، مع إبقاء bid نفسه."""
    children = list(_col("buttons").find({"parent_id": bid}))
    for child in children:
        wipe_btn_completely(child["id"])


def wipe_btn_completely(bid):
    for child in list(_col("buttons").find({"parent_id": bid})):
        wipe_btn_completely(child["id"])
    item_ids = [it["id"] for it in _col("content_items").find({"button_id": bid}, {"id": 1})]
    for iid in item_ids:
        _col("item_ratings").delete_many({"item_id": iid})
        _col("comments").delete_many({"target_type": "item", "target_id": iid})
    _col("content_items").delete_many({"button_id": bid})
    _col("quiz_questions").delete_many({"button_id": bid})
    _col("quiz_options").delete_many({"question_id": {"$in": [
        q["id"] for q in _col("quiz_questions").find({"button_id": bid}, {"id": 1})
    ]}})
    _col("exam_questions").delete_many({"button_id": bid})
    _col("button_ratings").delete_many({"button_id": bid})
    _col("comments").delete_many({"target_type": "btn", "target_id": bid})
    _col("buttons").delete_one({"id": bid})


def deep_clone_and_pair(source_bid, dest_pid):
    """ينسخ زر source_bid (وكل ما بداخله) ليصبح ابناً جديداً تحت dest_pid،
    ويسجل التوأمة (source <-> new) على مستوى كل زر وعنصر محتوى مطابق."""
    src = get_btn_any(source_bid)
    if not src:
        return None
    t = src["type"]

    ids = [b["id"] for b in _col("buttons").find({"parent_id": dest_pid}, {"id": 1}).sort([("ord", 1)])]
    new_id = _next_id("buttons")
    _col("buttons").insert_one({
        "id": new_id, "parent_id": dest_pid, "type": t, "label": src.get("label", ""),
        "ord": len(ids) + 1, "new_row": src.get("new_row", 1), "click_count": 0,
        "unified_rating": src.get("unified_rating", 1 if t == "content" else 0),
        "no_caption": src.get("no_caption", 0), "no_btn_caption": src.get("no_btn_caption", 0),
        "hidden": src.get("hidden", 0), "special_action": src.get("special_action"),
        "compound_text": src.get("compound_text"),
        "random_quiz": src.get("random_quiz", 0), "random_exam": src.get("random_exam", 0),
        "sort_by_year": src.get("sort_by_year", 0), "sort_alpha": src.get("sort_alpha", 0),
        "maintenance": src.get("maintenance", 0), "maintenance_msg": src.get("maintenance_msg"),
        "deleted": 0,
    })
    set_twin(source_bid, new_id)

    if t == "content":
        items = list(_col("content_items").find({"button_id": source_bid}).sort([("ord", 1), ("id", 1)]))
        for item in items:
            n_id = _next_id("content_items")
            _col("content_items").insert_one({
                "id": n_id, "button_id": new_id,
                "type": item.get("type"), "content": item.get("content"),
                "file_id": item.get("file_id"), "local_path": item.get("local_path"),
                "channel_msg_id": item.get("channel_msg_id"), "ord": item.get("ord", 1),
            })
            set_item_twin(item["id"], n_id)

    elif t == "quiz":
        questions = list(_col("quiz_questions").find({"button_id": source_bid}).sort([("ord", 1), ("id", 1)]))
        for q in questions:
            new_qid = _next_id("quiz_questions")
            _col("quiz_questions").insert_one({
                "id": new_qid, "button_id": new_id,
                "question": q.get("question"), "correct_option": q.get("correct_option", 0),
                "explanation": q.get("explanation", ""), "ord": q.get("ord", 1),
            })
            for opt in list(_col("quiz_options").find({"question_id": q["id"]}).sort([("ord", 1)])):
                new_oid = _next_id("quiz_options")
                _col("quiz_options").insert_one({
                    "id": new_oid, "question_id": new_qid,
                    "text": opt.get("text"), "ord": opt.get("ord", 1),
                })

    elif t == "exam":
        for eq in list(_col("exam_questions").find({"button_id": source_bid}).sort([("ord", 1), ("id", 1)])):
            new_eqid = _next_id("exam_questions")
            _col("exam_questions").insert_one({
                "id": new_eqid, "button_id": new_id,
                "q_type": eq.get("q_type", "text"), "q_text": eq.get("q_text"),
                "q_file_id": eq.get("q_file_id"), "q_channel_msg_id": eq.get("q_channel_msg_id"),
                "a_type": eq.get("a_type", "text"), "a_text": eq.get("a_text"),
                "a_file_id": eq.get("a_file_id"), "a_channel_msg_id": eq.get("a_channel_msg_id"),
                "ord": eq.get("ord", 1),
            })

    elif t == "compound":
        for child in list(_col("buttons").find({"parent_id": source_bid, "deleted": {"$ne": 1}}).sort([("ord", 1), ("id", 1)])):
            deep_clone_and_pair(child["id"], new_id)

    elif t in ("menu", "exam_group"):
        for child in list(_col("buttons").find({"parent_id": source_bid, "deleted": {"$ne": 1}}).sort([("ord", 1), ("id", 1)])):
            deep_clone_and_pair(child["id"], new_id)

    return new_id


def link_menus(source_menu_bid, dest_menu_bid):
    print(f"-- تفريغ {dest_menu_bid} بالكامل...")
    wipe_subtree(dest_menu_bid)
    src_children = list(_col("buttons").find(
        {"parent_id": source_menu_bid, "deleted": {"$ne": 1}}
    ).sort([("ord", 1), ("id", 1)]))
    print(f"-- نسخ {len(src_children)} عنصر من {source_menu_bid} إلى {dest_menu_bid}...")
    for child in src_children:
        deep_clone_and_pair(child["id"], dest_menu_bid)
    set_twin(source_menu_bid, dest_menu_bid)
    print(f"-- تمت التوأمة بين {source_menu_bid} و {dest_menu_bid}.")


if __name__ == "__main__":
    link_menus(1966, 3101)
    link_menus(2017, 3106)
    print("تم الانتهاء من ربط القوائم بنجاح.")
