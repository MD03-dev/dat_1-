import json
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType, Mention
from logging_utils import Logging
from config import PREFIX, HEADER_STYLE

logger = Logging()

class LockBotHandler:
    def __init__(self, client):
        self.client = client
        self.client.locked_users = self.load_locked_users()

    def load_locked_users(self):
        try:
            with open('locked_users.json', 'r') as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading locked_users.json: {e}")
            return []

    def save_locked_users(self):
        try:
            with open('locked_users.json', 'w') as file:
                json.dump(self.client.locked_users, file, indent=4)
        except Exception as e:
            logger.error(f"Error saving locked_users.json: {e}")

    def get_username(self, user_id):
        try:
            info = self.client.fetchUserInfo(user_id)
            if info and hasattr(info, "changed_profiles"):
                user_data = info.changed_profiles.get(str(user_id))
                if user_data:
                    return user_data.get('zaloName', 'Không xác định')
            return "Không xác định"
        except:
            return "Không xác định"

    def send_styled_reply(self, message_object, thread_id, thread_type, author_id, main_content, is_success=None):
        """
        Hàm gửi phản hồi fix lỗi tag và màu đỏ chuẩn PTA cho Group/Chat riêng
        """
        # Thêm icon logic
        if is_success is True:
            main_content += "\n✅✅✅"
        elif is_success is False:
            main_content += "\n❌❌❌"

        header_text = str(HEADER_STYLE)
        header_len = len(header_text)
        
        if thread_type == ThreadType.GROUP:
            name = self.get_username(author_id)
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
            self.client.replyMessage(
                Message(text=full_msg, style=styles, mention=mention),
                message_object,
                thread_id,
                thread_type,
                ttl=120000 
            )
        except Exception as e:
            self.client.sendMessage(Message(text=full_msg), thread_id, thread_type)

    def check_preconditions(self, message_object, thread_id, thread_type, author_id):
        """
        Hàm kiểm tra điều kiện chung: Ở trong nhóm và Cấp quyền Admin
        """
        if thread_type != ThreadType.GROUP:
            self.send_styled_reply(message_object, thread_id, thread_type, author_id, "Lệnh này chỉ thực hiện được trong nhóm!", is_success=False)
            return False
            
        if str(author_id) != str(self.client.ADMIN):
            self.send_styled_reply(message_object, thread_id, thread_type, author_id, "Bạn không có quyền sử dụng lệnh này\nYêu Cầu: Quản Trị Viên Bot\n🚫🚫🚫")
            return False
            
        return True

    def handle_lockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self.check_preconditions(message_object, thread_id, thread_type, author_id):
            return

        args = message_text.split()
        
        # Xử lý thêm cho tính năng lbot del <số> và lbot delall
        if len(args) > 1:
            sub_cmd = args[1].lower()
            if sub_cmd == "delall":
                if not self.client.locked_users:
                    self.send_styled_reply(message_object, thread_id, thread_type, author_id, "Danh sách đang trống, không có ai để xoá cả! 😎", is_success=True)
                    return
                    
                self.client.locked_users.clear()
                self.save_locked_users()
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, "Đã xoá toàn bộ danh sách người bị khoá! 🗑️🔓", is_success=True)
                logger.warning("Admin đã dọn dẹp sạch sẽ danh sách lockbot (delall).")
                return

            elif sub_cmd == "del":
                if len(args) > 2 and args[2].isdigit():
                    index = int(args[2]) - 1
                    if 0 <= index < len(self.client.locked_users):
                        removed_id = self.client.locked_users.pop(index)
                        self.save_locked_users()
                        user_name = self.get_username(removed_id)
                        
                        rest_text = f"Đã thả xích thành công theo số thứ tự! 🔓\n{user_name} ({removed_id})"
                        self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=True)
                        logger.warning(f"Đã unlock {user_name} - {removed_id} qua lệnh lbot del.")
                    else:
                        self.send_styled_reply(message_object, thread_id, thread_type, author_id, "Số thứ tự không hợp lệ! Vui lòng dùng lệnh list để xem lại.", is_success=False)
                else:
                    self.send_styled_reply(message_object, thread_id, thread_type, author_id, f"Sai cú pháp! Dùng: {PREFIX}lbot del <số thứ tự>", is_success=False)
                return

        # Logic cũ của lockbot (Thêm người vào danh sách)
        user_ids_to_lock = []

        if message_object.mentions:
            user_ids_to_lock.extend([mention['uid'] for mention in message_object.mentions])
        else:
            try:
                potential_user_id = message_text.split()[-1]
                if potential_user_id.isdigit():
                    user_ids_to_lock.append(potential_user_id)
            except:
                rest_text = f"Cú pháp sai lè rồi! Dùng: {PREFIX}lbot @tag hoặc {PREFIX}lbot <user_id>"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                return

        if not user_ids_to_lock:
            rest_text = "Tag người hoặc nhập ID người cần lock đi chứ! 🤨"
            self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
            return

        for user_id_to_lock in user_ids_to_lock:
            user_name = self.get_username(user_id_to_lock)
            
            if user_name == "Không xác định":
                rest_text = f"Ủa? Không tìm thấy user ID {user_id_to_lock} này luôn á! 🤷‍♂️"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                continue

            if str(user_id_to_lock) == str(self.client.ADMIN):
                rest_text = "Ê nhóc! Định khóa mõm cả Admin hả? To gan! 😠"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                continue

            if user_id_to_lock not in self.client.locked_users:
                self.client.locked_users.append(user_id_to_lock)
                self.save_locked_users()
                
                rest_text = f"Đã khóa thành công! 🔒\n{user_name}"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=True)
                logger.warning(f"Đã lock {user_name} - {user_id_to_lock}")
            else:
                rest_text = f"User này đã bị khóa trước đó! 😴\n{user_name}"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)

    def handle_unlockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self.check_preconditions(message_object, thread_id, thread_type, author_id):
            return

        user_ids_to_unlock = []

        if message_object.mentions:
            user_ids_to_unlock.extend([mention['uid'] for mention in message_object.mentions])
        else:
            try:
                potential_user_id = message_text.split()[-1]
                if potential_user_id.isdigit():
                    user_ids_to_unlock.append(potential_user_id)
            except:
                rest_text = f"Sai cú pháp unlock rồi! Dùng: {PREFIX}unlbot @tag hoặc {PREFIX}unlbot <user_id>"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                return

        if not user_ids_to_unlock:
            rest_text = "Tag người hoặc nhập ID người cần thả ra đi chứ! 🤨"
            self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
            return

        for user_id_to_unlock in user_ids_to_unlock:
            user_name = self.get_username(user_id_to_unlock)

            if user_name == "Không xác định":
                rest_text = f"Hình như không thấy user ID {user_id_to_unlock} này á! 🤷‍♂️"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)
                continue

            if user_id_to_unlock in self.client.locked_users:
                self.client.locked_users.remove(user_id_to_unlock)
                self.save_locked_users()
                
                rest_text = f"Đã thả xích thành công! 🔓\n{user_name}"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=True)
                logger.warning(f"Đã unlock {user_name} - {user_id_to_unlock}")
            else:
                rest_text = f"User này có bị nhốt đâu mà đòi thả hả Đại Ka? 🤔\n{user_name}"
                self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=False)

    def handle_listlockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if not self.check_preconditions(message_object, thread_id, thread_type, author_id):
            return

        if not self.client.locked_users:
            rest_text = "Danh sách trong sạch, chưa có ai bị giam cầm cả! 😎"
            self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=True)
            return

        locked_users_info = []
        # Thêm số thứ tự index vào hiển thị để dễ dùng lệnh lbot del <số>
        for index, user_id in enumerate(self.client.locked_users, start=1):
            user_name = self.get_username(user_id)
            locked_users_info.append(f"{index}. {user_name} ({user_id})")

        list_message = "\n".join(locked_users_info)
        rest_text = f"Danh sách con sen đang bị xích nè:\n\n{list_message}"
        
        self.send_styled_reply(message_object, thread_id, thread_type, author_id, rest_text, is_success=True)
        logger.info(f"Displayed locked users list:\n{list_message}")
