import time
import threading
import logging
import json
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType, Mention
from config import ADMIN, PREFIX, HEADER_STYLE

logger = logging.getLogger(__name__)

# Biến trạng thái toàn cục để kiểm soát vòng lặp
is_autotag_running = False

des = {
    'version': "1.5.1",
    'credits': "Van Chien & Gemini",
    'description': "Auto Tag - Treo tag thành viên liên tục với phân quyền nâng cao",
    'power': "Admin"
}

def check_admin_permissions(author_id, thread_id, thread_type, client):
    """Kiểm tra quyền admin từ client, seting.json và config.py"""
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

    if isinstance(ADMIN, list):
        if author_id in [str(uid) for uid in ADMIN]:
            return True
    elif author_id == str(ADMIN):
        return True
        
    return False

# --- Các hàm hỗ trợ Style chuẩn ---

def get_user_name(client, user_id):
    """Lấy tên người dùng chuẩn"""
    try:
        user_info = client.fetchUserInfo(user_id)
        if user_info and hasattr(user_info, 'changed_profiles'):
            profile = user_info.changed_profiles.get(str(user_id))
            if profile and profile.get('zaloName'):
                return profile['zaloName']
    except Exception:
        pass
    return "Bae"

def _send_styled_msg(client, text, message_object, thread_id, thread_type, author_id, ttl=120000):
    """Gửi tin nhắn phản hồi có style chuẩn"""
    name = get_user_name(client, author_id)
    tag_text = f"@{name}"
    
    if thread_type == ThreadType.USER:
        full_msg = f"{HEADER_STYLE}\n{text}"
        mention = None
        offset_header = 0
    else:
        full_msg = f"{tag_text}\n{HEADER_STYLE}\n{text}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))
        offset_header = len(tag_text) + 1

    styles = MultiMsgStyle([
        MessageStyle(offset=offset_header, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=offset_header, length=len(HEADER_STYLE), style="bold", auto_format=False),
        MessageStyle(offset=offset_header, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
    ])
    
    try:
        client.replyMessage(
            Message(text=full_msg, style=styles, mention=mention),
            message_object, thread_id, thread_type, ttl=ttl
        )
    except Exception as e:
        logger.error(f"[autotag] Lỗi gửi tin: {e}")

# --- Logic chính ---

def handle_autotag_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_autotag_running

    # 1. KIỂM TRA QUYỀN HẠN NÂNG CAO
    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        _send_styled_msg(client, "Quyền hạn của bạn không đủ để dùng lệnh này.\nYêu Cầu: Quản Trị Bot\n🚫🚫🚫", message_object, thread_id, thread_type, author_id, ttl=10000)
        return

    # 2. Chặn sử dụng trong chat riêng
    if thread_type != ThreadType.GROUP:
        _send_styled_msg(client, "Lệnh này chỉ có thể sử dụng trong nhóm chat!", message_object, thread_id, thread_type, author_id)
        return

    command_parts = message.split()
    
    # 3. Hướng dẫn cú pháp
    if len(command_parts) == 1:
        syntax = (
            f"Bật: {PREFIX}autotag on [giây] @user\n"
            f"Tắt: {PREFIX}autotag off"
        )
        _send_styled_msg(client, syntax, message_object, thread_id, thread_type, author_id, ttl=20000)
        return

    lowered_parts = [x.lower() for x in command_parts]

    # Xử lý lệnh Tắt
    if any(x in lowered_parts for x in ["off", "stop"]):
        if is_autotag_running:
            is_autotag_running = False
            _send_styled_msg(client, "Đã dừng quá trình Auto Tag!\n✅✅✅", message_object, thread_id, thread_type, author_id)
        else:
            _send_styled_msg(client, "Hiện không có quá trình tag nào đang chạy.", message_object, thread_id, thread_type, author_id, ttl=10000)
        return

    # Xử lý lệnh Bật
    if "on" in lowered_parts:
        if is_autotag_running:
            _send_styled_msg(client, "Hệ thống đang chạy một tiến trình tag khác rồi!", message_object, thread_id, thread_type, author_id, ttl=10000)
            return

        if not message_object.mentions:
            _send_styled_msg(client, "Vui lòng tag người bạn muốn 'gọi hồn'!", message_object, thread_id, thread_type, author_id, ttl=10000)
            return

        # Xác định delay
        delay = 2.0
        for part in command_parts:
            try:
                val = float(part)
                if val >= 0.5: delay = val
            except: continue

        tagged_user_id = message_object.mentions[0]['uid']
        tagged_name = get_user_name(client, tagged_user_id)
        
        is_autotag_running = True

        def autotag_loop():
            global is_autotag_running
            tag_text = f"@{tagged_name}"
            mention = Mention(uid=tagged_user_id, offset=0, length=len(tag_text))
            
            while is_autotag_running:
                try:
                    client.send(
                        Message(text=tag_text, mention=mention),
                        thread_id, thread_type, ttl=10000
                    )
                    time.sleep(delay)
                except Exception as e:
                    logger.error(f"[autotag] Lỗi vòng lặp: {e}")
                    is_autotag_running = False
                    break

        threading.Thread(target=autotag_loop, daemon=True).start()
        _send_styled_msg(client, f"Đã bắt đầu gọi hồn {tagged_name} với tốc độ {delay}s/lần!", message_object, thread_id, thread_type, author_id)

def PTA():
    return {'autotag': handle_autotag_command}