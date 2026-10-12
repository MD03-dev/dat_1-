import os
import json
from zlapi.models import *
from config import ADMIN, PREFIX, HEADER_STYLE

des = {
    'version': "2.1.5",
    'credits': "Văn Chiến",
    'description': "Phong chủ nhóm (Key Vàng)",
    'power': "Quản Trị Viên Bot"
}

# ==========================
# ⚙️ HÀM TRỢ GIÚP
# ==========================

def get_username(client, user_id):
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, "changed_profiles"):
            user_data = info.changed_profiles.get(str(user_id))
            if user_data:
                return user_data.get('zaloName', 'Thành viên')
        return "Thành viên"
    except:
        return "Thành viên"

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

    styles = MultiMsgStyle([
        MessageStyle(offset=header_offset, length=len(header_text), style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=header_offset, length=len(header_text), style="bold", auto_format=False),
        MessageStyle(offset=header_offset, length=len(header_text), style="font", size=18, auto_format=False)
    ])
    
    try:
        client.replyMessage(Message(text=full_msg, style=styles, mention=mention), message_object, thread_id, thread_type, ttl=120000)
    except:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

def handle_keygold_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        if not check_admin_permissions(author_id, thread_id, thread_type, client):
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, "Bạn không có đủ quyền để sử dụng lệnh này\nYêu cầu quyền hạn: Quản Trị Bot\n🚫🚫🚫")
            return

        if thread_type != ThreadType.GROUP:
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, "Lệnh này chỉ dùng trong nhóm! ❌")
            return

        try:
            group_info = client.fetchGroupInfo(thread_id)
            group_data = group_info.gridInfoMap[thread_id]
            if str(client.uid) != str(group_data.creatorId):
                send_styled_reply(client, message_object, thread_id, thread_type, author_id, ":d Cần có key 🔑 mới phong được Key Vàng!")
                return
        except:
            pass

        if not message_object.mentions:
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, "Vui lòng tag người cần phong chủ nhóm! ❌")
            return

        uids_str = []
        uids_int = []
        user_names = []
        
        for m in message_object.mentions:
            uid = getattr(m, 'uid', None) or (m.get('uid') if isinstance(m, dict) else None)
            if uid:
                uids_str.append(str(uid))
                uids_int.append(int(uid))
                user_names.append(get_username(client, str(uid)))

        try:
            client.changeGroupOwner(uids_str[0], thread_id)
            names_str = ", ".join(user_names)
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, f"Đã trao Key Vàng (Chủ Nhóm) cho: {names_str}\n👑✅✅✅")
            
        except Exception as e:
            try:
                client.changeGroupOwner(uids_int[0], thread_id)
                send_styled_reply(client, message_object, thread_id, thread_type, author_id, f"Đã trao Key Vàng (Chủ Nhóm) cho: {', '.join(user_names)}\n👑✅✅✅")
            except:
                send_styled_reply(client, message_object, thread_id, thread_type, author_id, f"Lỗi: {str(e)}\nKhông thể thực hiện trên Zalo! ❌")

    except Exception as e:
        client.sendMessage(Message(text=f"Lỗi hệ thống: {str(e)}"), thread_id, thread_type)

def PTA():
    return {
        'keygold': handle_keygold_command
    }