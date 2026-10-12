import time
import threading
import os
from zlapi.models import Message

des = {
    "version": "1.2.1",
    "credits": "Duc Duy",
    "description": "Che do si tu file txt (gui lap den khi tat)",
    "power": "Thanh vien"
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_PATH = os.path.join(BASE_DIR, "cache", "tangai.txt")

RUNNING = False
THREAD = None


def load_lines():
    try:
        with open(TXT_PATH, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            print("[TANGAI] loaded:", len(lines))
            return lines
    except Exception as e:
        print("[TANGAI] load error:", e)
        return []


def loop_send(client, message_object, thread_id, thread_type, lines, tag_name):
    global RUNNING
    idx = 0
    total = len(lines)

    print("[TANGAI] loop start")

    while RUNNING and total > 0:
        base_text = lines[idx]
        full_text = base_text + "\n@" + tag_name

        print("[TANGAI] sending:", full_text)

        try:
            client.replyMessage(
                Message(text=full_text),
                message_object,
                thread_id,
                thread_type
            )
        except Exception as e:
            print("[TANGAI] send error:", e)

        idx = (idx + 1) % total
        time.sleep(1)


def handle_tangai(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING, THREAD

    if RUNNING:
        client.replyMessage(
            Message(text="⚠️ Dang si roi, dung /dungsi de tat"),
            message_object,
            thread_id,
            thread_type
        )
        return

    lines = load_lines()
    if not lines:
        client.replyMessage(
            Message(text="❌ File tangai.txt trong hoac loi"),
            message_object,
            thread_id,
            thread_type
        )
        return

    target_id = author_id
    if message_object.mentions:
        target_id = message_object.mentions[0]["uid"]

    user_info = client.fetchUserInfo(target_id)
    if hasattr(user_info, "changed_profiles") and str(target_id) in user_info.changed_profiles:
        tag_name = user_info.changed_profiles[str(target_id)].get("zaloName", "ban")
    else:
        tag_name = getattr(user_info, "name", "ban")

    RUNNING = True
    THREAD = threading.Thread(
        target=loop_send,
        args=(client, message_object, thread_id, thread_type, lines, tag_name),
        daemon=True
    )
    THREAD.start()

    client.replyMessage(
        Message(text="✅ Da bat dau si (dung /dungsi de dung)"),
        message_object,
        thread_id,
        thread_type
    )


def handle_dungsi(message, message_object, thread_id, thread_type, author_id, client):
    global RUNNING
    RUNNING = False
    client.replyMessage(
        Message(text="🛑 Da dung si"),
        message_object,
        thread_id,
        thread_type
    )


def PTA():
    return {
        "tangai": handle_tangai,
        "dungsi": handle_dungsi
    }