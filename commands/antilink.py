import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention
from config import PREFIX, HEADER_STYLE

class AntiLinkHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/antilink_settings.json"
        self.enabled_groups = self.load_settings()

        # Bộ đếm vi phạm
        self.link_violations = {}
        self.violation_window = 60       # thời gian reset (1 phút)
        self.kick_threshold = 3          # số lần vi phạm để kick
        self.warn_threshold = 2          # số lần cảnh báo

    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except:
            return {}

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(str(uid), {}).get('zaloName', str(uid))
        except:
            return str(uid)

    def _send_reply(self, text, message_object, thread_id, thread_type, author_id, use_header=True, tag_user=True):
        """Hàm tối ưu để xử lý riêng biệt chat nhóm / chat riêng, có tắt/bật tag và màu mè"""
        name = self.get_user_name(author_id)
        full_msg = ""
        mention = None
        styles = None
        msg_styles = []

        if use_header:
            if thread_type == ThreadType.USER:
                full_msg = f"{HEADER_STYLE}\n{text}"
                msg_styles = [
                    MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
                    MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
                ]
            else:
                if tag_user:
                    tag_text = f"@{name}"
                    full_msg = f"{tag_text}\n{HEADER_STYLE}\n{text}"
                    mention = Mention(uid=author_id, offset=0, length=len(tag_text))
                    offset_start = len(tag_text) + 1
                    msg_styles = [
                        MessageStyle(offset=offset_start, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=offset_start, length=len(HEADER_STYLE), style="bold", auto_format=False),
                        MessageStyle(offset=offset_start, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
                    ]
                else:
                    full_msg = f"{HEADER_STYLE}\n{text}"
                    msg_styles = [
                        MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
                        MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
                    ]
        else:
            # Tắt Header_Style — dùng cho thông báo cảnh báo có heart style + tag tên
            if thread_type == ThreadType.USER:
                full_msg = text
            else:
                if tag_user:
                    tag_text = f"@{name}"
                    full_msg = f"{tag_text}\n{text}"
                    mention = Mention(uid=author_id, offset=0, length=len(tag_text))

                    # ❤️ Heart style: tô màu hồng/đỏ cho tên trong phần cảnh báo
                    # Dòng tag: "@Tên\n" => offset 0..len(tag_text)
                    # Dòng nội dung bắt đầu tại: len(tag_text)+1
                    body_offset = len(tag_text) + 1
                    body_len = len(text)
                    msg_styles = [
                        # Tag @Tên: màu đỏ hồng, bold
                        MessageStyle(offset=0, length=len(tag_text), style="color", color="#e91e8c", auto_format=False),
                        MessageStyle(offset=0, length=len(tag_text), style="bold", auto_format=False),
                        # Nội dung cảnh báo: màu cam đỏ
                        MessageStyle(offset=body_offset, length=body_len, style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=body_offset, length=body_len, style="bold", auto_format=False),
                    ]
                else:
                    full_msg = text
                    msg_styles = [
                        MessageStyle(offset=0, length=len(text), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=0, length=len(text), style="bold", auto_format=False),
                    ]

        if msg_styles:
            styles = MultiMsgStyle(msg_styles)

        msg_to_send = Message(text=full_msg, style=styles, mention=mention)
        try:
            self.client.replyMessage(msg_to_send, message_object, thread_id, thread_type)
        except:
            self.client.replyMessage(Message(text=full_msg), message_object, thread_id, thread_type)

    # ===========================
    #  LỆNH BẬT / TẮT ANTILINK
    # ===========================
    def handle_antilink_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if str(author_id) not in self.client.ADMIN:
            self._send_reply("⚠️ Bạn không có quyền dùng lệnh này.", message_object, thread_id, thread_type, author_id, use_header=True, tag_user=True)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            msg = f"Dùng: {PREFIX}antilink <on/off>\nTrạng thái: {current}"
            self._send_reply(msg, message_object, thread_id, thread_type, author_id, use_header=True, tag_user=True)
            return

        if action == "on":
            self.enabled_groups[str(thread_id)] = True
            rest = "Đã bật AntiLink 🛡️"
        else:
            self.enabled_groups.pop(str(thread_id), None)
            rest = "Đã tắt AntiLink 🔕"

        self.save_settings()
        self._send_reply(f"{rest}", message_object, thread_id, thread_type, author_id, use_header=True, tag_user=True)

    # ====================================
    #  XỬ LÝ MỖI KHI USER GỬI LINK
    # ====================================
    def check_and_handle_link(self, message_object, thread_id, thread_type, author_id):
        if not self.is_enabled(thread_id):
            return False

        if not self.client.is_url_in_message(message_object):
            return False

        if self.client.is_group_admin(thread_id, author_id):
            return False

        # Xoá tin nhắn
        try:
            self.client.deleteGroupMsg(
                message_object.get("msgId"),
                author_id,
                message_object.get("cliMsgId"),
                thread_id
            )
        except:
            pass

        now = time.time()

        if thread_id not in self.link_violations:
            self.link_violations[thread_id] = {}

        user = self.link_violations[thread_id].get(author_id, {
            "count": 0,
            "first": now
        })

        if now - user["first"] > self.violation_window:
            user = {"count": 1, "first": now}
        else:
            user["count"] += 1

        self.link_violations[thread_id][author_id] = user
        count = user["count"]

        author_name = self.get_user_name(author_id)

        # =======================================
        #  XỬ LÝ CẢNH CÁO / KICK TRONG NHÓM
        # =======================================
        if count >= self.kick_threshold:
            try:
                self.client.blockUsersInGroup(author_id, thread_id)
                # Kick: thông báo không tag, in đậm đỏ
                reply_text = f"{author_name} đã bị kick khỏi nhóm do gửi link vi phạm 3 lần!"
                self._send_reply(reply_text, message_object, thread_id, thread_type, author_id, use_header=False, tag_user=False)
            except Exception as e:
                reply_text = f"Lỗi! Không thể kick {author_name}: {e}"
                self._send_reply(reply_text, message_object, thread_id, thread_type, author_id, use_header=False, tag_user=False)

        elif count == self.warn_threshold:
            # Cảnh báo lần 2: tag tên + heart style + nêu rõ tên trong nội dung
            reply_text = (
                f"⚠️ Cảnh báo {author_name}!\n"
                f"Ngừng send link, trước khi, mọi chuyện dần tồi tệ hơn!"
            )
            self._send_reply(reply_text, message_object, thread_id, thread_type, author_id, use_header=False, tag_user=True)

        else:
            # Cảnh báo lần 1: tag tên + heart style + nêu rõ tên trong nội dung
            reply_text = (
                f"⚠️ Cảnh báo {author_name}!\n"
                f"Ở đây không được phép gửi link này!"
            )
            self._send_reply(reply_text, message_object, thread_id, thread_type, author_id, use_header=False, tag_user=True)

        return True