import json
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle, Mention, MultiMention
from config import PREFIX
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AntiCardHandler:
    def __init__(self, client):
        self.client = client
        self.settings_card = "data/anticard_settings.json"
        self.enabled_groups = self.load_settings()
        self.card_violations = {}
        self.violation_window = 60  # thời gian tính vi phạm (giây)
        # Đã chỉnh sửa: Kick/Block sẽ xảy ra ở Lần 1
        self.kick_threshold = 1     # số lần vi phạm trước khi kick

    # ------------------------ QUẢN LÝ CÀI ĐẶT ------------------------
    def load_settings(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        try:
            with open(self.settings_card, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_settings(self):
        with open(self.settings_card, "w") as f:
            json.dump(self.enabled_groups, f, indent=4)

    def is_enabled(self, thread_id):
        return self.enabled_groups.get(str(thread_id), False)

    # ------------------------ HÀM TIỆN ÍCH ------------------------
    def get_user_name(self, uid):
        try:
            user_info = self.client.fetchUserInfo(uid)
            return user_info.changed_profiles.get(
                str(uid), {}).get(
                'zaloName', str(uid))
        except BaseException:
            return str(uid)

    # ------------------------ LỆNH ANTICARD ------------------------
    def handle_anticard_command(
            self,
            message_text,
            message_object,
            thread_id,
            thread_type,
            author_id):
        name = self.get_user_name(author_id)

        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Bạn không có quyền sử dụng lệnh này."
            msg = f"{name}\n➜ {rest_text}"
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="bold",
                        auto_format=False)])
            self.client.replyMessage(
                Message(
                    text=msg,
                    style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=60000)
            for r_icon in ["❌", "🚫", "🔐"]:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            return

        parts = message_text.lower().split()
        action = parts[1] if len(parts) > 1 else ""

        if action not in ["on", "off"]:
            current_status = "Bật ✅" if self.is_enabled(thread_id) else "Tắt ❌"
            rest_text = f"🚦Hướng dẫn: {PREFIX}anticard <on/off>\n➜ Trạng thái hiện tại: {current_status}"
            msg = f"{name}\n➜ {rest_text}"
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=0,
                        length=len(name),
                        style="bold",
                        auto_format=False)])
            self.client.replyMessage(
                Message(
                    text=msg,
                    style=styles),
                message_object,
                thread_id,
                thread_type,
                ttl=60000)
            for r_icon in ["👉", "📜", "ℹ️"]:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            return

        thread_id_str = str(thread_id)
        if action == "on":
            if self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Card đã được bật trước đó. 🔄"
                reactions = ["⚠️", "🛡️", "🪪"]
            else:
                self.enabled_groups[thread_id_str] = True
                self.save_settings()
                # Fix: sửa f-string bị lỗi trước đó
                rest_text = f"Đã bật chế độ Anti-Card. Gửi card {self.kick_threshold} lần/phút sẽ bị kick ngay lập tức. 🛡️"
                reactions = ["✅", "🛡️", "🪪"]
        else:
            if not self.is_enabled(thread_id_str):
                rest_text = "Chế độ Anti-Card đã được tắt trước đó. 🔄"
                reactions = ["⚠️", "🪪", "🔓"]
            else:
                if thread_id_str in self.enabled_groups:
                    del self.enabled_groups[thread_id_str]
                self.save_settings()
                rest_text = "Đã tắt chế độ Anti-Card. 🔓"
                reactions = ["🚫", "🪪", "🔓"]

        msg = f"{name}\n➜ {rest_text}"
        styles = MultiMsgStyle([MessageStyle(offset=0,
                                             length=len(name),
                                             style="color",
                                             color="#db342e",
                                             auto_format=False),
                                MessageStyle(offset=0,
                                             length=len(name),
                                             style="bold",
                                             auto_format=False)])
        self.client.replyMessage(
            Message(
                text=msg,
                style=styles),
            message_object,
            thread_id,
            thread_type,
            ttl=60000)
        for r_icon in reactions:
            try:
                self.client.sendReaction(
                    message_object,
                    r_icon,
                    thread_id,
                    thread_type,
                    reactionType=75)
            except BaseException:
                pass

    # ------------------------ XỬ LÝ CARD ------------------------
    def check_and_delete_card(
            self,
            message_object,
            thread_id,
            thread_type,
            author_id):
        """
        Hàm phát hiện và xóa tin nhắn dạng 'card' (chat.carduser, chat.cardgroup, v.v.)
        """
        if not self.is_enabled(thread_id):
            return False

        msg_type = message_object.get('msgType') or ""
        # Mở rộng kiểm tra kiểu tin nhắn chứa 'card' hoặc 'recommand' để phát hiện đa dạng hơn
        if not any(k in msg_type.lower() for k in ('card', 'recommand', 'recommended')):
            return False

        # Nếu tác giả là admin/thành viên whitelist -> bỏ qua
        try:
            if self.client.is_group_admin(thread_id, author_id):
                return False
        except Exception:
            # nếu không lấy được thông tin admin thì tiếp tục bước sau (bước phòng hộ)
            pass

        if str(thread_id) in getattr(self.client, "whitelist", {}) and str(
                author_id) in self.client.whitelist.get(str(thread_id), []):
            return False

        try:
            msg_id = message_object.get('msgId')
            cli_msg_id = message_object.get('cliMsgId')
            card_name = message_object.get(
                'content', {}).get(
                'displayName', 'Không rõ tên')
            if msg_id:
                self.client.deleteGroupMsg(
                    msg_id, author_id, cli_msg_id, thread_id)
        except Exception as e:
            logger.error(f"[AntiCard] Lỗi khi xóa card: {e}")
            return False

        now = time.time()
        if thread_id not in self.card_violations:
            self.card_violations[thread_id] = {}

        # Nếu là lần vi phạm đầu tiên hoặc vi phạm ngoài cửa sổ thời gian (60s), đặt lại count = 1
        user_violations = self.card_violations[thread_id].get(
            author_id, {'count': 0, 'first_violation_time': now})

        if now - user_violations['first_violation_time'] > self.violation_window:
            user_violations = {'count': 1, 'first_violation_time': now}
        else:
            user_violations['count'] += 1

        self.card_violations[thread_id][author_id] = user_violations
        current_violation_count = user_violations['count']
        user_name = self.get_user_name(author_id)
        tag_author = f"{user_name}"
        msg = ""

        if current_violation_count >= self.kick_threshold:
            # Lần 1: Xóa + Chặn khỏi nhóm (vì kick_threshold = 1)
            try:
                # Ghi log trước khi gọi block để dễ debug
                logger.info(f"[AntiCard] Thực hiện block user {author_id} trong group {thread_id}")
                resp = self.client.blockUsersInGroup(author_id, thread_id)
                logger.info(f"[AntiCard] blockUsersInGroup response: {resp}")
                del self.card_violations[thread_id][author_id]
                rest_text = f"📣 {tag_author} đã bị chặn khỏi nhóm do gửi card vi phạm lần đầu."
            except Exception as e:
                # Nếu block không thành công (thường do bot không có quyền admin), tạo fallback:
                logger.error(f"[AntiCard] Lỗi khi chặn user {author_id}: {e}")
                rest_text = f"⚠️ Đã cố gắng chặn {tag_author} nhưng thất bại do thiếu quyền. Đã báo cho admin xử lý."
                # Thông báo tới admins trong group (fallback)
                try:
                    self._alert_admins_for_manual_kick(thread_id, author_id, user_name, message_object)
                except Exception as ex2:
                    logger.error(f"[AntiCard] Lỗi khi báo admin: {ex2}")

            msg = f"➜ [ANTI-CARD]\n{tag_author}\n➜ {rest_text}"

        if msg:
            tag_offset = msg.find(tag_author)
            styles = MultiMsgStyle(
                [
                    MessageStyle(
                        offset=len("➜ "),
                        length=len("[ANTI-CARD]"),
                        style="color",
                        color="#db342e",
                        auto_format=False),
                    MessageStyle(
                        offset=len("➜ "),
                        length=len("[ANTI-CARD]"),
                        style="bold",
                        auto_format=False)])
            try:
                self.client.replyMessage(
                    Message(
                        text=msg,
                        mention=Mention(
                            author_id,
                            offset=tag_offset,
                            length=len(tag_author)),
                        style=styles),
                    message_object,
                    thread_id,
                    thread_type,
                    ttl=120000)
            except Exception as e:
                logger.error(f"[AntiCard] Lỗi khi gửi thông báo kết quả xử lý: {e}")
        return True

    # ------------------------ FALLBACK: BÁO ADMIN KHI BOT KHÔNG CÓ QUYỀN ------------------------
    def _alert_admins_for_manual_kick(self, thread_id, offender_id, offender_name, message_object):
        """
        Nếu bot không có quyền kick, gửi thông báo kèm mention tới admin/creator của nhóm
        và gửi riêng cho ADMIN chính (owner) 1 tin nhắn yêu cầu can thiệp.
        """
        try:
            info = self.client.fetchGroupInfo(thread_id)
            if not info:
                return
            # cố gắng lấy adminIds/creatorId từ response
            group_data = getattr(info, "gridInfoMap", {}) or {}
            group_entry = group_data.get(str(thread_id)) or next(iter(group_data.values()), {})
            admin_ids = group_entry.get("adminIds", []) if isinstance(group_entry, dict) else []
            creator_id = group_entry.get("creatorId") if isinstance(group_entry, dict) else None

            admin_ids = [str(x) for x in admin_ids if x]
            if creator_id:
                admin_ids.append(str(creator_id))
            admin_ids = list(dict.fromkeys(admin_ids))

            if not admin_ids:
                # gửi 1 tin trong group kèm offender mention để báo mọi người
                text = f"⚠️ Bot không có quyền chặn user. Vui lòng admin kiểm tra: @{offender_name}"
                self.client.send(Message(text=text), thread_id=thread_id, thread_type=ThreadType.GROUP)
                return

            # Tạo mentions cho tất cả admin
            text = f"⚠️ Yêu cầu hỗ trợ: Vui lòng xử lý {offender_name} (gửi card)."
            mentions = []
            offset = len(text) + 1
            # note: Mention constructor thứ tự (uid, length, offset) một số API khác nhau, dùng named args cho an toàn
            for aid in admin_ids:
                mentions.append(Mention(uid=aid, offset=offset, length=1, auto_format=False))
                text += " @"
                offset += 2

            try:
                self.client.send(Message(text=text, mention=MultiMention(mentions)),
                                 thread_id=thread_id, thread_type=ThreadType.GROUP)
            except Exception:
                # fallback: gửi text đơn giản
                self.client.send(Message(text=f"⚠️ Yêu cầu admin xử lý: {offender_name}"), thread_id=thread_id, thread_type=ThreadType.GROUP)

            # Gửi cảnh báo riêng cho admin chính (nếu cấu hình ADMIN tồn tại trong client)
            try:
                main_admin = getattr(self.client, "ADMIN", None) or None
                if main_admin:
                    self.client.send(Message(text=f"⚠️ Bot không thể chặn {offender_name} trong group {thread_id}. Vui lòng can thiệp."), main_admin, ThreadType.USER)
            except Exception as e:
                logger.error(f"[AntiCard] Không thể gửi cảnh báo cho ADMIN chính: {e}")

        except Exception as e:
            logger.error(f"[AntiCard] Lỗi khi lấy admin để báo: {e}")