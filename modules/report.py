import random
import os
import json
from zlapi.models import Message, MessageStyle, MultiMsgStyle, Mention, ThreadType
from config import ADMIN, PREFIX, HEADER_STYLE

# ================= CONFIG =================
des = {
    "version": "1.1.2",
    "credits": "Van Chien & Gemini",
    "description": "Tố cáo người dùng - Chỉ lấy nội dung sau tag",
    "power": "Thành viên"
}

# ===== HÀM HỖ TRỢ GIAO DIỆN =====

def get_username(client, user_id):
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, "changed_profiles"):
            user_data = info.changed_profiles.get(str(user_id))
            if user_data:
                return user_data.get('zaloName', 'Người dùng')
        return "Người dùng"
    except:
        return "Người dùng"

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
        # Không tag người dùng ở chat riêng theo yêu cầu của Van Chien
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
            message_object,
            thread_id,
            thread_type,
            ttl=120000 
        )
    except:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

def react(client, icon, message_object, thread_id, thread_type):
    try:
        client.sendReaction(icon, message_object, thread_id, thread_type)
    except:
        pass

# ===== LOGIC GỬI REPORT =====

def execute_send_report(client, target_id, reason=0, content=None):
    params = {"zpw_ver": 645, "zpw_type": 30}
    payload_params = {
        "idTo": str(target_id),
        "objId": "person.profile"
    }
    
    if content:
        payload_params["content"] = str(content)
        payload_params["reason"] = str(reason if reason != 0 else 0)
    else:
        payload_params["reason"] = str(random.randint(1, 3))
    
    encoded_params = client._encode(payload_params)
    payload = {"params": encoded_params}
    
    response = client._post("https://tt-profile-wpa.chat.zalo.me/api/report/abuse-v2", params=params, data=payload)
    return response.json()

# ===== LỆNH CHÍNH =====

def handle_report_command(message, message_object, thread_id, thread_type, author_id, client, *args, **kwargs):
    try:
        target_id = None
        report_content = ""
        target_name = ""
        
        # 1. Xử lý trong nhóm (Lấy nội dung sau tag)
        if thread_type == ThreadType.GROUP:
            mentions = message_object.mentions
            if mentions:
                # Lấy UID của người được tag đầu tiên
                target_id = mentions[0].uid
                target_name = get_username(client, target_id)
                
                msg_text = message_object.content or ""
                
                # Tìm vị trí kết thúc của tag cuối cùng để cắt chuỗi chính xác
                last_mention_end = 0
                for m in mentions:
                    offset = m.offset if m.offset is not None else 0
                    length = m.length if m.length is not None else 0
                    end_pos = offset + length
                    if end_pos > last_mention_end:
                        last_mention_end = end_pos
                
                # Lấy phần văn bản CHỈ nằm sau các tag
                report_content = msg_text[last_mention_end:].strip()
            else:
                send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                                  "Trong nhóm, bạn phải @tag người cần tố cáo!")
                return
        
        # 2. Xử lý trong chat riêng
        else:
            target_id = thread_id
            target_name = get_username(client, target_id)
            report_content = " ".join(args) if args else ""

        if not target_id:
            return

        if str(target_id) == str(client.uid):
            send_styled_reply(client, message_style, thread_id, thread_type, author_id, "Bot không thể tự tố cáo chính mình!")
            return

        # Thực hiện gửi report
        react(client, "⏳", message_object, thread_id, thread_type)
        
        result = execute_send_report(client, target_id, content=report_content)
        
        if result.get("error_code") == 0:
            # Format nội dung phản hồi: Nội dung tố cáo {name} là: {nội dung}
            display_reason = report_content if report_content else "Không có lý do cụ thể"
            main_content = f"📝 Nội dung tố cáo {target_name} là: {display_reason}"
            
            # Đã loại bỏ react ✅/❌ theo chỉ thị trước đó của bạn
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, main_content)
        else:
            error_msg = result.get("error_message", "Lỗi hệ thống")
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, f"Thất bại!\nLỗi: {error_msg}")

    except Exception as e:
        print("❌ Lỗi report:", e)

def PTA():
    return {
        'report': handle_report_command,
        'tocao': handle_report_command
    }