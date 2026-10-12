import json
import time
import threading
import os
import random
import requests
from zlapi.models import Message, Mention, MultiMsgStyle, MessageStyle, ThreadType
import logging
from config import PREFIX, ADMIN, HEADER_STYLE

logging.basicConfig(level=logging.DEBUG)

des = {
    'version': "1.0.0",
    'credits': "Hoang Khanh Prime",
    'description': "Treo Ảnh - Spam ảnh kèm text từ file, hỗ trợ tag, chọn file",
    'power': "Quản trị viên Bot"
}

is_treoanh_running = False

# ==========================
# ⚙️ HÀM TRỢ GIÚP
# ==========================

def get_username(client, user_id):
    try:
        info = client.fetchUserInfo(str(user_id))
        if info and hasattr(info, "changed_profiles"):
            user_data = info.changed_profiles.get(str(user_id))
            if user_data:
                return user_data.get('zaloName', 'Ê')
        return "Ê"
    except:
        return "Ê"

def check_admin_permissions(author_id, thread_id, thread_type, client):
    author_id = str(author_id)

    if hasattr(client, 'is_allowed_author') and client.is_allowed_author(author_id):
        return True

    try:
        if os.path.exists('seting.json'):
            with open('seting.json', 'r', encoding='utf-8') as f:
                current_settings = json.load(f)
            admin_id = str(current_settings.get('admin', ''))
            adm_list = [str(uid) for uid in current_settings.get('adm', [])]
            if author_id == admin_id or author_id in adm_list:
                return True
    except Exception:
        pass

    if author_id in ADMIN:
        return True

    return False

def send_styled_reply(client, message_object, thread_id, thread_type, author_id, main_content):
    header_text = str(HEADER_STYLE)
    header_len = len(header_text)

    if thread_type == ThreadType.GROUP:
        name = get_username(client, author_id)
        tag_text = f"@{name}"
        full_msg = f"{tag_text}\n{header_text}\n{main_content}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))
        header_offset = len(tag_text) + 1
    else:
        full_msg = f"{header_text}\n{main_content}"
        mention = None
        header_offset = 0

    style_list = [
        MessageStyle(offset=header_offset, length=header_len, style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=header_offset, length=header_len, style="bold", auto_format=False),
        MessageStyle(offset=header_offset, length=header_len, style="font", size=18, auto_format=False)
    ]
    styles = MultiMsgStyle(style_list)

    try:
        client.replyMessage(
            Message(text=full_msg, style=styles, mention=mention),
            message_object, thread_id, thread_type, ttl=120000
        )
    except Exception:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

# ==========================
# ⚙️ HÀM CHÍNH TREOANH
# ==========================

def handle_treoanh_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_treoanh_running
    command_parts = message.split()

    # 1. Kiểm tra quyền
    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          "Bạn không có quyền sử dụng lệnh này\nYêu Cầu: Quản Trị Viên Bot\n🚫🚫🚫")
        return

    # 2. Menu hướng dẫn
    if len(command_parts) == 1:
        menu_msg = (
            f"🖼️ HƯỚNG DẪN LỆNH TREOANH:\n"
            f"• {PREFIX}treoanh [url] : Spam ảnh với file text mặc định (1.txt)\n"
            f"• {PREFIX}treoanh [url] [số file] : Spam ảnh với file text chỉ định\n"
            f"• {PREFIX}treoanh [url] [số file] [tốc độ]ms : Spam có tốc độ\n"
            f"• {PREFIX}treoanh tha : Dừng spam\n\n"
            f"📌 Ví dụ:\n"
            f"- {PREFIX}treoanh https://i.imgur.com/abc.jpg\n"
            f"- {PREFIX}treoanh https://i.imgur.com/abc.jpg 2\n"
            f"- {PREFIX}treoanh https://i.imgur.com/abc.jpg 2 500ms"
        )
        send_styled_reply(client, message_object, thread_id, thread_type, author_id, menu_msg)
        return

    # 3. Lệnh dừng
    if command_parts[1].lower() in ["tha", "off", "stop"]:
        is_treoanh_running = False
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          "Đã dừng treo ảnh!\n✅✅✅")
        return

    # 4. Lấy URL ảnh (tham số đầu tiên)
    img_url = command_parts[1]
    if not img_url.startswith("http"):
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          "URL không hợp lệ! Phải bắt đầu bằng http/https\n❌❌❌")
        return

    # 5. Phân tích số file và tốc độ
    file_num = "1"
    delay_time = 1.5

    for part in command_parts[2:]:
        part_lower = part.lower()
        if part.isdigit():
            file_num = part
        elif part_lower.endswith("ms") and part_lower[:-2].isdigit():
            delay_time = int(part_lower[:-2]) / 1000.0
        elif part_lower.endswith("s") and part_lower[:-1].replace('.', '', 1).isdigit():
            delay_time = float(part_lower[:-1])

    delay_time = max(0.1, delay_time)

    # 6. Không tag user

    # 7. Đọc file text
    try:
        with open(f"spam/{file_num}.txt", "r", encoding="utf-8") as f:
            text_list = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          f"Không tìm thấy file: spam/{file_num}.txt\n❌❌❌")
        return

    if not text_list:
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          f"File {file_num}.txt rỗng!\n❌❌❌")
        return

    # 8. Tải ảnh về dạng bytes
    try:
        resp = requests.get(img_url, timeout=10)
        resp.raise_for_status()
        img_data = resp.content

        # Xác định đuôi file từ URL
        ext = "jpg"
        url_lower = img_url.lower().split("?")[0]
        for e in ["png", "gif", "webp", "jpeg", "jpg"]:
            if url_lower.endswith(e):
                ext = e
                break

        img_path = f"/tmp/treoanh_img.{ext}"
        with open(img_path, "wb") as f:
            f.write(img_data)
    except Exception as e:
        send_styled_reply(client, message_object, thread_id, thread_type, author_id,
                          f"Không tải được ảnh từ URL!\nLỗi: {e}\n❌❌❌")
        return

    # 9. Thông báo bắt đầu
    is_treoanh_running = True
    status_msg = (
        f"🖼️ Bắt đầu Treo Ảnh!\n"
        f"📁 File text: {file_num}.txt ({len(text_list)} câu)\n"
        f"⚡ Tốc độ: {delay_time}s\n"
        f"✅✅✅"
    )
    send_styled_reply(client, message_object, thread_id, thread_type, author_id, status_msg)

    # 10. Vòng lặp spam
    def treoanh_loop():
        global is_treoanh_running
        while is_treoanh_running:
            for noidung in text_list:
                if not is_treoanh_running:
                    break

                mentions_list = []
                caption = noidung
                c_offset = 0

                # Style cho text nội dung
                styles_list = [
                    MessageStyle(offset=c_offset, length=len(noidung), style="color", color="#DB342E", auto_format=False),
                    MessageStyle(offset=c_offset, length=len(noidung), style="bold", auto_format=False),
                    MessageStyle(offset=c_offset, length=len(noidung), style="font", size=18, auto_format=False),
                ]

                msg_kwargs = {
                    "text": caption,
                    "style": MultiMsgStyle(styles_list)
                }

                try:
                    client.sendLocalImage(
                        img_path,
                        thread_id=thread_id,
                        thread_type=thread_type,
                        message=Message(**msg_kwargs),
                        ttl=0
                    )
                except Exception as e:
                    logging.error(f"Lỗi gửi ảnh: {e}")

                time.sleep(delay_time)

    t = threading.Thread(target=treoanh_loop)
    t.daemon = True
    t.start()

def PTA():
    return {'treoanh': handle_treoanh_command}
