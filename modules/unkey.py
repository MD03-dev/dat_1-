import os
import json
from zlapi.models import *
from config import ADMIN, PREFIX, HEADER_STYLE

des = {
    'version': "2.5.4",
    'credits': "Van Chien",
    'description': "Xóa quyền phó nhóm",
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
            message_object,
            thread_id,
            thread_type,
            ttl=120000 
        )
    except Exception:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

# ==========================
# ⚙️ HÀM CHÍNH
# ==========================

def handle_delkeysilver_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        # 1. Kiểm tra quyền của người dùng lệnh
        if not check_admin_permissions(author_id, thread_id, thread_type, client):
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                              "Bạn không có đủ quyền để sử dụng lệnh này\nYêu cầu quyền hạn: Quản Trị Bot\n🚫🚫🚫")
            return

        if thread_type != ThreadType.GROUP:
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                              "Lệnh này chỉ thực hiện được trong nhóm!\n❌❌❌")
            return

        # 2. KIỂM TRA BOT CÓ PHẢI TRƯỞNG NHÓM (CREATOR) KHÔNG
        # Đồng bộ logic giống kick.py
        try:
            group_info = client.fetchGroupInfo(thread_id)
            group_data = group_info.gridInfoMap[thread_id]
            
            # Lấy ID Trưởng nhóm từ dữ liệu nhóm
            creator_id = str(group_data.creatorId)
            bot_id = str(client.uid)

            # Chỉ Trưởng nhóm mới có quyền hạ cấp Phó nhóm
            if bot_id != creator_id:
                send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                                  ":d Đưa Key Vàng 🔑 em xoá Key bạc cho đại ca!")
                return
        except Exception as e:
            # Nếu không lấy được info nhóm, có thể bot chưa vào nhóm hoặc lỗi API
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                              "Không thể kiểm tra quyền hạn của Bot trong nhóm này!\n❌❌❌")
            return

        # 3. Kiểm tra xem có tag ai không
        if not message_object.mentions:
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                              "Vui lòng đề cập người cần xóa key bạc\n❌❌❌")
            return

        uids = []
        user_names = []
        
        for m in message_object.mentions:
            uid = getattr(m, 'uid', None)
            if not uid and isinstance(m, dict):
                uid = m.get('uid')
            
            if uid:
                uid_str = str(uid)
                uids.append(uid_str)
                name = get_username(client, uid_str)
                user_names.append(name)

        if not uids:
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, 
                              "Không tìm thấy UID từ người được tag!\n❌❌❌")
            return

        # 4. THỰC THI XÓA PHÓ NHÓM
        try:
            # Chức năng remove phó nhóm của Zlapi
            client.removeGroupAdmins(uids, thread_id)
            
            names_str = ", ".join(user_names)
            result_text = f"Đã xoá key của {names_str}\n✅✅✅"
            
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, result_text)
        except Exception as e:
            error_msg = f"Lỗi: {str(e)}\n(Hãy đảm bảo Bot vẫn là Trưởng Nhóm)\n❌❌❌"
            send_styled_reply(client, message_object, thread_id, thread_type, author_id, error_msg)

    except Exception as e:
        client.sendMessage(Message(text=f"Lỗi hệ thống: {str(e)}\n❌❌❌"), thread_id, thread_type)

def PTA():
    return {
        'unkey': handle_delkeysilver_command
    }
