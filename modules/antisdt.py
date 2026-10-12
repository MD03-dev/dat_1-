import json
import os
import re
import time
import logging
from zlapi.models import Message, ThreadType, Mention, MessageStyle, MultiMsgStyle
from config import ADMIN, PREFIX, HEADER_STYLE

# Khởi tạo logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ANTISDT")

des = {
    'version': "2.4.0",
    'credits': "Van Chien",
    'description': "Chống gửi số điện thoại, cảnh báo chuẩn",
    'power': "Admin"
}

# ==========================
# ⚙️ HÀM TRỢ GIÚP (Đồng bộ từ adduser.py)
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
    """Kiểm tra quyền admin từ hệ thống realtime và file cấu hình"""
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
    except:
        pass
    if author_id in ADMIN:
        return True
    return False

def send_styled_reply(client, message_object, thread_id, thread_type, author_id, main_content):
    """Gửi phản hồi có Header đỏ chuẩn style Van Chien"""
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
    except:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

# ==========================
# 🛡️ XỬ LÝ ANTI-SDT
# ==========================

class AntiSdtHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antisdt_settings.json"
        self.whitelist_file = "data/phone_whitelist.json"
        
        self.enabled_groups = self.load_json(self.settings_file)
        self.phone_whitelist = self.load_json(self.whitelist_file)
        
        self.violations = {}
        self.violation_window = 86400 # 1 ngày
        self.kick_threshold = 3
        self.phone_regex = re.compile(r"0[\d.\s]{9,12}")

    def load_json(self, path):
        if not os.path.exists("data"): os.makedirs("data")
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}

    def save_json(self, path, data):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    def normalize_phone(self, phone):
        return re.sub(r"\D", "", phone)

    def is_group_admin(self, thread_id, author_id):
        """Kiểm tra quản trị viên của nhóm (để bỏ qua bắt sdt)"""
        try:
            group_info = self.client.getGroupInfo(thread_id)
            if group_info and hasattr(group_info, 'gridInfo'):
                admins = group_info.gridInfo.adminIds
                creator = group_info.gridInfo.creatorId
                return str(author_id) in admins or str(author_id) == str(creator)
        except: pass
        return False

    def handle_antisdt_command(self, message_text, message_object, thread_id, thread_type, author_id):
        # 1. Kiểm tra quyền hạn
        if not check_admin_permissions(author_id, thread_id, thread_type, self.client):
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Bạn không có quyền sử dụng lệnh này\nYêu Cầu: Quản Trị Viên Bot\n🚫🚫🚫")
            return

        # 2. Kiểm tra môi trường nhóm
        if thread_type != ThreadType.GROUP:
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Lệnh này chỉ thực hiện được trong nhóm!\n❌❌❌")
            return

        parts = message_text.split()
        action = parts[1].lower() if len(parts) > 1 else ""
        tid_str = str(thread_id)

        if action == "on":
            self.enabled_groups[tid_str] = True
            self.save_json(self.settings_file, self.enabled_groups)
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Đã bật chế độ Anti-SDT. Bảo vệ nhóm khỏi rác/spam số điện thoại. ✅✅✅")
            
        elif action == "off":
            if tid_str in self.enabled_groups: del self.enabled_groups[tid_str]
            self.save_json(self.settings_file, self.enabled_groups)
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Đã tắt chế độ Anti-SDT. ❌❌❌")

        elif action in ["white", "add"]:
            if len(parts) < 3:
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  f"Vui lòng nhập SDT: {PREFIX}antisdt white <số điện thoại>\n❌❌❌")
            else:
                phone = self.normalize_phone(parts[2])
                if len(phone) < 10:
                    send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                      "Số điện thoại không hợp lệ (phải từ 10 số).\n❌❌❌")
                else:
                    if tid_str not in self.phone_whitelist: self.phone_whitelist[tid_str] = []
                    if phone not in self.phone_whitelist[tid_str]:
                        self.phone_whitelist[tid_str].append(phone)
                        self.save_json(self.whitelist_file, self.phone_whitelist)
                        send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                          f"Đã thêm '{phone}' vào danh sách trắng của nhóm.\n✅✅✅")
                    else:
                        send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                          f"Số '{phone}' đã có trong danh sách trắng.\n❌❌❌")

        elif action == "remove":
            phone = self.normalize_phone(parts[2]) if len(parts) > 2 else ""
            if tid_str in self.phone_whitelist and phone in self.phone_whitelist[tid_str]:
                self.phone_whitelist[tid_str].remove(phone)
                self.save_json(self.whitelist_file, self.phone_whitelist)
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  f"Đã xóa số '{phone}' khỏi danh sách trắng.\n✅✅✅")
            else:
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  "Số điện thoại không tồn tại trong danh sách trắng.\n❌❌❌")

        elif action == "list":
            patterns = self.phone_whitelist.get(tid_str, [])
            if not patterns:
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  "Hiện tại nhóm không có số điện thoại nào trong danh sách trắng.\n❌❌❌")
            else:
                list_str = "\n".join([f"{i+1}. {p}" for i, p in enumerate(patterns)])
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  f"📋 Danh sách trắng SDT nhóm:\n{list_str}\n✅✅✅")

        else:
            status = "Đang Bật ✅" if self.is_enabled(thread_id) else "Đang Tắt ❌"
            msg = (f"Trạng thái: {status}\n"
                   f"➜ {PREFIX}antisdt on/off: Bật/Tắt\n"
                   f"➜ {PREFIX}antisdt white <sdt>: Thêm SDT ngoại lệ\n"
                   f"➜ {PREFIX}antisdt remove <sdt>: Xóa SDT ngoại lệ\n"
                   f"➜ {PREFIX}antisdt list: Xem danh sách trắng\nℹ️ℹ️ℹ️")
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, msg)

    def check_and_process(self, message_text, message_object, thread_id, thread_type, author_id):
        if not message_text or not isinstance(message_text, str) or thread_type != ThreadType.GROUP:
            return False

        if not self.is_enabled(thread_id):
            return False

        # Quản trị viên Bot và Quản trị viên nhóm được phép gửi SDT
        if check_admin_permissions(author_id, thread_id, thread_type, self.client) or self.is_group_admin(thread_id, author_id):
            return False

        matches = self.phone_regex.findall(message_text)
        if not matches: return False
        
        tid_str = str(thread_id)
        whitelist = self.phone_whitelist.get(tid_str, [])
        valid_violations = [m for m in matches if self.normalize_phone(m) not in whitelist]
        
        if not valid_violations: return False

        # Xóa tin nhắn
        try:
            msg_id = getattr(message_object, 'msgId', message_object.get('msgId') if isinstance(message_object, dict) else None)
            cli_msg_id = getattr(message_object, 'cliMsgId', message_object.get('cliMsgId') if isinstance(message_object, dict) else None)
            if msg_id:
                self.client.deleteGroupMsg(msg_id, str(author_id), cli_msg_id, thread_id)
        except: pass

        # Tính toán vi phạm
        now = time.time()
        author_id_str = str(author_id)
        if tid_str not in self.violations: self.violations[tid_str] = {}
        user_v = self.violations[tid_str].get(author_id_str, {'count': 0, 'time': now})
        
        if now - user_v['time'] > self.violation_window:
            user_v = {'count': 1, 'time': now}
        else:
            user_v['count'] += 1
            user_v['time'] = now 
            
        self.violations[tid_str][author_id_str] = user_v
        count = user_v['count']

        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                rest_text = f"🚫 Đã KICK thành công do gửi SDT vi phạm ({count}/{self.kick_threshold}). ✅✅✅"
                self.violations[tid_str][author_id_str] = {'count': 0, 'time': now}
            except:
                rest_text = f"⚠️ Vi phạm ({count}/{self.kick_threshold}) nhưng Bot không có quyền Quản trị viên để kick! ❌❌❌"
        elif count == 2:
            rest_text = f"⚠️ Cảnh báo lần 2\nNếu tái phạm lần nữa ({count+1}/{self.kick_threshold}), bạn sẽ bị kick ra khỏi nhóm! 🚫🚫🚫"
        else:
            rest_text = f"⚠️ Nhóm cấm gửi số điện thoại!\nTin nhắn đã bị thu hồi. Vi phạm ({count}/{self.kick_threshold}). ❌❌❌"

        send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, rest_text)
        return True

# ==========================
# ⚙️ KHỞI TẠO & EXPORT
# ==========================

_handler = None

def handle_antisdt_main(message, message_object, thread_id, thread_type, author_id, client):
    global _handler
    if _handler is None:
        _handler = AntiSdtHandler(client)
    
    # Nếu là lệnh thiết lập (bắt đầu bằng prefix + antisdt)
    if isinstance(message, str) and message.startswith(f"{PREFIX}antisdt"):
        _handler.handle_antisdt_command(message, message_object, thread_id, thread_type, author_id)
        return True
    
    # Hàm chạy ngầm quét SDT
    return _handler.check_and_process(message, message_object, thread_id, thread_type, author_id)

def PTA():
    return {
        'antisdt': handle_antisdt_main
    }