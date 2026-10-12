from config import PREFIX, HEADER_STYLE
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
import json
import time
import threading
import traceback
from concurrent.futures import ThreadPoolExecutor

_pool = ThreadPoolExecutor(8)

class VisualCooldownManager:
    """Quản lý cooldown + visual countdown bằng reaction thả/thu hồi."""

    def __init__(self, bot):
        self.bot = bot
        self._lock = threading.Lock()
        self._last = {}
        self._waiting = {}
        self._waiting_lock = threading.Lock()
        
        # Cấu hình icon
        self.icon_cooldown = "🕐"
        self.icon_done = "/-ok"

    def _build_rMsg(self, message_object):
        """Tạo rMsg dict cho reaction API."""
        try:
            from zlapi._util import getClientMessageType
            msg_type = getClientMessageType(message_object.msgType)
        except Exception:
            msg_type = 1
        return {
            "gMsgID": int(message_object.msgId),
            "cMsgID": int(message_object.cliMsgId),
            "msgType": msg_type,
        }

    def _add_multi_react(self, mo, count, tid, tt):
        """Thả N reaction đồng hồ cùng lúc (reactionType=75)."""
        try:
            if count <= 0: return
            r = self._build_rMsg(mo)
            rMsg_list = [r.copy() for _ in range(count)]
            self.bot.sendMultiReaction(
                reactionObj=rMsg_list,
                reactionIcon=self.icon_cooldown,
                thread_id=tid,
                thread_type=tt,
                reactionType=75,
            )
        except Exception as e:
            pass

    def _remove_react(self, mo, tid, tt):
        """Thu hồi bớt 1 reaction (reactionType=-1)."""
        try:
            r = self._build_rMsg(mo)
            self.bot.sendMultiReaction(
                reactionObj=[r],
                reactionIcon=self.icon_cooldown,
                thread_id=tid,
                thread_type=tt,
                reactionType=-1,
            )
        except Exception as e:
            pass

    def _add_single_react(self, mo, icon, tid, tt):
        """Thả 1 reaction hoàn thành."""
        try:
            self.bot.sendReaction(
                messageObject=mo,
                reactionIcon=icon,
                thread_id=tid,
                thread_type=tt,
            )
        except Exception as e:
            pass

    def check(self, name, uid, tid, cd_seconds):
        """Kiểm tra thời gian cooldown còn lại."""
        if cd_seconds <= 0:
            return None

        key = f"{name}:{uid}:{tid}"
        with self._lock:
            now = time.time()
            last = self._last.get(key, 0)
            if now - last < cd_seconds:
                return cd_seconds - (now - last)
            self._last[key] = now
            return None

    def mark(self, name, uid, tid):
        """Lưu timestamp khi sử dụng lệnh thành công."""
        key = f"{name}:{uid}:{tid}"
        with self._lock:
            self._last[key] = time.time()

    def countdown_then_run(self, remain, name, fn, msg, mo, tid, tt, uid, run_handler_fn):
        """
        Flow thực thi:
        - Thả số lượng 🕐 tương ứng số giây.
        - Mỗi 1 giây: Thu hồi 1 cái -> Thả lại số lượng (còn lại - 1).
        - Xong cooldown: Thả /-ok và chạy lệnh.
        """
        cd_key = f"{name}:{uid}:{tid}"

        with self._waiting_lock:
            if self._waiting.get(cd_key):
                return
            self._waiting[cd_key] = True

        def _run():
            try:
                # Giới hạn max 30s để tránh dội API Zalo
                secs = max(1, min(int(remain) + 1, 30))

                # Bước 1: Thả N icon đồng hồ ban đầu
                self._add_multi_react(mo, secs, tid, tt)

                # Bước 2: Vòng lặp đếm ngược, thu hồi và thả lại
                for i in range(secs):
                    time.sleep(1)
                    remaining = secs - (i + 1)

                    # Thu hồi bớt reaction
                    self._remove_react(mo, tid, tt)

                    # Thả lại số lượng tương ứng số giây còn lại
                    if remaining > 0:
                        time.sleep(0.01)  # Chống nghẽn API
                        self._add_multi_react(mo, remaining, tid, tt)

                # Bước 3: Đánh dấu đã hết cooldown
                self.mark(name, uid, tid)

                # Bước 4: Thả reaction hoàn thành và chạy hàm
                self._add_single_react(mo, self.icon_done, tid, tt)
                run_handler_fn(fn, name, msg, mo, tid, tt, uid)

            except Exception:
                traceback.print_exc()
            finally:
                with self._waiting_lock:
                    self._waiting.pop(cd_key, None)

        _pool.submit(_run)

# --- PHẦN THÔNG TIN VÀ CẤU HÌNH LỆNH ---

des = {
    'version': "1.0.5",
    'credits': "</> Hoàng Khánh Premiun",
    'description': "check prefix",
    'power': "Thành viên",
    'reaction': False
}

COOLDOWN_TIME = 30
_cd_manager = None

def get_cd_manager(client):
    """Khởi tạo hoặc trả về instance toàn cục của VisualCooldownManager."""
    global _cd_manager
    if _cd_manager is None:
        _cd_manager = VisualCooldownManager(client)
    else:
        # Cập nhật lại client phòng trường hợp bot bị restart/đổi object client
        _cd_manager.bot = client 
    return _cd_manager

def prf():
    with open('seting.json', 'r') as f:
        return json.load(f).get('prefix')

def get_username(client, user_id):
    """Hàm lấy tên người dùng để tag."""
    try:
        info = client.fetchUserInfo(user_id)
        if info and hasattr(info, "changed_profiles"):
            return info.changed_profiles.get(str(user_id), {}).get('zaloName', 'Người dùng')
        return "Người dùng"
    except Exception:
        return "Người dùng"

def checkprefix(message, message_object, thread_id, thread_type, author_id, client):
    cd_manager = get_cd_manager(client)
    
    bot_uid = client.uid
    bot_name = get_username(client, bot_uid) # Đã sửa thành get_username
    current_prefix = prf()
    content = f"Prefix hiện tại của bot {bot_name} là: {current_prefix}\n✅✅✅"
    
    # Hàm thực thi chính của lệnh
    def execute_logic(msg, mo, tid, tt, uid, cli):
        # Lấy thông tin Bot và prefix theo đoạn code bạn cung cấp
        bot_uid = cli.uid
        bot_name = get_username(cli, bot_uid)
        current_prefix = prf()
        
        if tt == ThreadType.USER:
            # Xử lý khi nhắn ở chat riêng (không tag)
            content_msg = f"Prefix hiện tại của bot {bot_name} là: {current_prefix}\n✅✅✅"
            full_msg = f"{HEADER_STYLE}\n{content_msg}"
            mention = None
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False) 
            ])
        else:
            # Xử lý khi nhắn ở nhóm (có tag chuẩn)
            name = get_username(cli, uid)
            tag_text = f"@{name}"
            content_msg = f"Prefix hiện tại của bot {bot_name} là: {current_prefix}\n✅✅✅"
            full_msg = f"{tag_text}\n{HEADER_STYLE}\n{content_msg}"
            mention = Mention(uid=uid, offset=0, length=len(tag_text))
            styles = MultiMsgStyle([
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
            ])

        gui = Message(text=full_msg, style=styles, mention=mention)
        cli.replyMessage(gui, mo, tid, tt, ttl=20000)

    # Kiểm tra thời gian hồi chiêu
    remain = cd_manager.check('prefix', author_id, thread_id, COOLDOWN_TIME)
    
    if remain:
        # Trình bao bọc để chạy lệnh sau khi kết thúc đếm ngược
        def run_handler(fn, name, msg, mo, tid, tt, uid):
            fn(msg, mo, tid, tt, uid, client)
            
        # Gọi hiệu ứng chờ cooldown và sau đó chạy lệnh
        cd_manager.countdown_then_run(
            remain=remain,
            name='prefix',
            fn=execute_logic,
            msg=message,
            mo=message_object,
            tid=thread_id,
            tt=thread_type,
            uid=author_id,
            run_handler_fn=run_handler
        )
    else:
        # Nếu không dính cooldown thì thực thi ngay và lưu lại mốc thời gian
        execute_logic(message, message_object, thread_id, thread_type, author_id, client)
        cd_manager.mark('prefix', author_id, thread_id)

def PTA():
    return {
        'prefix': checkprefix
    }