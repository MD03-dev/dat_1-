import json
import os
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
from config import PREFIX, ADMIN, HEADER_STYLE

des = {
    'version': "1.2.0",
    'credits': "Khánh Sang",
    'description': "Quản lý bật/tắt welcome cho nhóm (wlc list/remove all)",
    'power': "Quản trị viên Bot"
}

ALLOWED_GROUPS_FILE = "data/welcome_setting.json"
ADMIN_ID = ADMIN

def is_admin(author_id):
    return str(author_id) == str(ADMIN_ID)

def load_allowed_groups():
    try:
        if os.path.exists(ALLOWED_GROUPS_FILE):
            with open(ALLOWED_GROUPS_FILE, "r") as f:
                return json.load(f)
    except json.JSONDecodeError:
        return {"groups": []}
    return {"groups": []}

def save_allowed_groups(allowed_groups):
    try:
        os.makedirs("data", exist_ok=True)
        with open(ALLOWED_GROUPS_FILE, "w") as f:
            json.dump(allowed_groups, f, indent=4)
    except Exception as e:
        print(f"Error saving allowed groups: {e}")

def reply_msg(client, message_object, thread_id, thread_type, author_id, text_content, ttl=15000):
    """Gửi tin nhắn có HEADER_STYLE - giữ màu đỏ/đậm cho header, không áp style cho nội dung"""
    header = str(HEADER_STYLE) if HEADER_STYLE else ""

    if thread_type == ThreadType.USER:
        full_msg = f"{header}\n{text_content}" if header else text_content
        mention = None
        style_list = []

        if header:
            style_list.extend([
                MessageStyle(offset=0, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(header), style="font", size=18, auto_format=False)
            ])

        styles = MultiMsgStyle(style_list) if style_list else None
    else:
        user_info = client.fetchUserInfo(author_id)
        author_info = user_info.changed_profiles.get(str(author_id), {}) if user_info and hasattr(user_info, 'changed_profiles') else {}
        name = author_info.get('zaloName', 'Thành viên')

        tag_text = f"@{name}"
        full_msg = f"{tag_text}\n{header}\n{text_content}" if header else f"{tag_text}\n{text_content}"
        mention = Mention(uid=author_id, offset=0, length=len(tag_text))

        style_list = []
        offset_header = len(tag_text) + 1

        if header:
            style_list.extend([
                MessageStyle(offset=offset_header, length=len(header), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="bold", auto_format=False),
                MessageStyle(offset=offset_header, length=len(header), style="font", size=18, auto_format=False)
            ])

        styles = MultiMsgStyle(style_list) if style_list else None

    try:
        client.replyMessage(
            Message(text=full_msg, style=styles, mention=mention),
            message_object, thread_id=thread_id, thread_type=thread_type, ttl=ttl
        )
    except Exception:
        try:
            client.sendMessage(
                Message(text=full_msg, style=styles, mention=mention),
                thread_id, thread_type
            )
        except Exception:
            pass

def handle_welcome_settings_command(message, message_object, thread_id, thread_type, author_id, client):
    # Kiểm tra quyền admin
    if not is_admin(author_id):
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  "Bạn không đủ quyền hạn để sử dụng lệnh này! 🚫🚫🚫", ttl=5000)
        return

    command_parts = message.split()

    # Nếu chỉ gõ "welcome" hoặc "wlc" mà không có tham số
    if len(command_parts) < 2:
        rest_text = (
            f"Hướng dẫn sử dụng lệnh {PREFIX}welcome (hoặc {PREFIX}wlc):\n"
            f"• {PREFIX}wlc on: Bật welcome nhóm này.\n"
            f"• {PREFIX}wlc off: Tắt welcome nhóm này.\n"
            f"• {PREFIX}wlc list: Xem danh sách các nhóm đã bật.\n"
            f"• {PREFIX}wlc remove all: Tắt welcome tất cả các nhóm."
        )
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=30000)
        return

    action = command_parts[1].lower()
    allowed_groups_data = load_allowed_groups()
    allowed_groups = allowed_groups_data.get("groups", [])

    # Xử lý các hành động
    if action == "on":
        if thread_id not in allowed_groups:
            allowed_groups.append(thread_id)
            allowed_groups_data["groups"] = allowed_groups
            save_allowed_groups(allowed_groups_data)
            rest_text = "Đã bật thông báo sự kiện cho nhóm này! 🚦✅"
        else:
            rest_text = "Nhóm này đã được bật thông báo trước đó! 🔄"

    elif action == "off":
        if thread_id in allowed_groups:
            allowed_groups.remove(thread_id)
            allowed_groups_data["groups"] = allowed_groups
            save_allowed_groups(allowed_groups_data)
            rest_text = "Đã tắt thông báo sự kiện cho nhóm này! 🚨✅"
        else:
            rest_text = "Nhóm này chưa được bật thông báo! 🔄"

    elif action == "list":
        if not allowed_groups:
            rest_text = "Hiện chưa có nhóm nào bật thông báo sự kiện. 📝"
        else:
            list_groups = "\n".join([f"{i+1}. {gid}" for i, gid in enumerate(allowed_groups)])
            rest_text = f"Danh sách ID nhóm đang bật Thông báo sự kiện:\n{list_groups}"

    elif action == "remove" and len(command_parts) > 2 and command_parts[2].lower() == "all":
        allowed_groups_data["groups"] = []
        save_allowed_groups(allowed_groups_data)
        rest_text = "Đã xóa tất cả nhóm khỏi danh sách nhận thông báo sự kiện! 🧹✅"

    else:
        rest_text = f"Lệnh không hợp lệ. Sử dụng {PREFIX}wlc để xem hướng dẫn. ❌❌❌"

    reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=10000)

def PTA():
    return {
        'welcome': handle_welcome_settings_command,
        'wlc': handle_welcome_settings_command
    }
