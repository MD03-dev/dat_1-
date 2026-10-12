from zlapi.models import *
import time
import random
import threading
import os
from config import PREFIX, ADMIN, HEADER_STYLE

is_war_running = False
WAR_SETTINGS = {}
DEFAULT_DELAY = 0.5

des = {
    'version': "2.1.0",
    'credits': "</> Hoàng Khánh Prime",
    'description': "War liên tục cho đến khi tắt ⚔️",
    'power': "Admin"
}

WAR_MENU = (
    f"╔════════════════════════╗\n"
    f"⚔️  MENU WAR BOT </> Hoàng Khánh Prime ⚔️\n"
    f"╚════════════════════════╝\n\n"
    f"➤ 🎯 Bắt đầu war: {PREFIX}war [reo/spam/poll/todo/random] @tag\n"
    f"➤ ⚙️ Cài delay: {PREFIX}war [reo/spam/poll/todo] delay [số]\n"
    f"➤ 📝 Đặt file: {PREFIX}war [reo/spam/poll/todo] set [file]\n"
    f"➤ ⭕️ Tắt war: {PREFIX}war off\n\n"
    f"💡 Ví dụ:\n"
    f"  • {PREFIX}war spam @duy\n"
    f"  • {PREFIX}war spam delay 1\n"
    f"  • {PREFIX}war spam set data/war.txt\n"
    f"  • {PREFIX}war off"
)

DEFAULT_MESSAGES = [
    "con đĩ ngu bị cha chửi k ngốc đầu lên đc🤣",
    "sao m cay t vậy tr🤣🤖",
    "thg óc đú m sủa lẹ đê",
    "cay đến nỗi phải bỏ cha vô hạn chế à:))?",
    "sủa lẹ đi🤣🤣",
    "thg culi ô xin mà đòi đú à",
    "lên bem cha đê🤣🤔",
    "sủa đê🤣",
    "mẹ m bị t đụ kìa🤤🤣",
    "cay k con",
    "mày hài v tr",
    "thg ngu đú bị cha chửi cho ko ngốc đầu lên đc🤣🤣",
    "lần sau gặp cha vhn thì xin tha đi🤣",
    "lên chửi nhau với cha phát:))?🤣",
    "cha lên giết cha mẹ m nè con🤣",
    "mày sợ à con 🐕",
    "thg bất hiếu ám sát cha mẹ",
    "mày bại t rõ mà",
    "còn cố gì nx tr🤣🙃",
    "thg ngu loạn luân với mẹ mà còn chối🤤🤣",
    "t cân cả dòng họ m mà:))",
    "Mày đang mếu vì bị cha chửi đúng ko🤣",
    "bú cứt cha đi cha tha cho m nè con🤣",
    "thg bê đê bị cha chửi cay phải tự tử bớt sủa dơ đi nha e eiii",
    "tao đã cho m câm chưa hả thg ngu đòi bem cha và cái kết...🤣",
    "mày cảm thấy bất lực khi bị t bem đúng k",
    "thg ngu đú war kiểu🤣",
    "mới có xíu m đã bại t mẹ r",
    "yếu rồi còn sĩ",
    "m còn gì khác để làm tao cay không hay là chỉ biết ăn hôi🤣"
    "đúng là thg tật mồ côi🤣",
    "sài adr 2m đòi khè ai v tr 😜😜",
    "thg tật bẩm sinh🤣",
    "đáy của xã hội😜😜👍",
    "bốc cứt ăn qua ngày🤣",
    "tưởng mình hay",
    "mà trong khi mình ngu hơn 1 con dog",
    "mày bại tao all sàn mxh với real mà còn cãi đc k🤣"
]


# ==================== HÀM REPLY_MSG ====================
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


# ==================== HÀM HỖ TRỢ ====================
def load_messages_from_file(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except Exception:
        return None


def stop_war(client, message_object, thread_id, thread_type, author_id):
    global is_war_running
    if not is_war_running:
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  "❌ Không có war nào đang chạy.", ttl=6000)
        return
    is_war_running = False
    reply_msg(client, message_object, thread_id, thread_type, author_id,
              "⛔️ Đã dừng WAR thành công!", ttl=6000)


def start_war(client, message_object, thread_id, thread_type, author_id, mode, delay, messages, tagged_user):
    global is_war_running
    is_war_running = True

    def war_loop():
        global is_war_running
        while is_war_running:
            msg = random.choice(messages)
            try:
                if tagged_user:
                    mention = Mention(tagged_user, length=0, offset=0)
                    client.send(Message(text=msg, mention=mention), thread_id, thread_type, ttl=6000)
                else:
                    client.send(Message(text=msg), thread_id, thread_type, ttl=6000)
            except Exception as e:
                reply_msg(client, message_object, thread_id, thread_type, author_id,
                          f"Lỗi gửi tin: {e}", ttl=6000)
            time.sleep(delay)
        is_war_running = False

    t = threading.Thread(target=war_loop)
    t.start()
    reply_msg(client, message_object, thread_id, thread_type, author_id,
              f"🚀 Bắt đầu WAR mode `{mode}` (liên tục đến khi off)\nDelay: {delay}s", ttl=6000)


# ==================== LỆNH CHÍNH ====================
def war(message, message_object, thread_id, thread_type, author_id, client):
    global is_war_running, WAR_SETTINGS

    # Chỉ admin mới được war
    if author_id not in ADMIN:
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  "🚫 Bạn không có quyền dùng lệnh WAR.", ttl=6000)
        return

    parts = message.split()
    if len(parts) == 1 or (len(parts) > 1 and parts[1].lower() in ["help", "?", "menu"]):
        reply_msg(client, message_object, thread_id, thread_type, author_id, WAR_MENU, ttl=6000)
        return

    if "off" in parts:
        stop_war(client, message_object, thread_id, thread_type, author_id)
        return

    mode = parts[1].lower()
    if mode not in ["reo", "spam", "poll", "todo", "random"]:
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  f"❌ Mode không hợp lệ.\n\n{WAR_MENU}", ttl=6000)
        return

    if "delay" in parts:
        try:
            idx = parts.index("delay")
            val = float(parts[idx + 1])
            WAR_SETTINGS["delay"] = val
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"✅ Delay cho mode `{mode}` đặt thành {val}s", ttl=6000)
        except Exception:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      "⚠️ Sai cú pháp. Ví dụ: war spam delay 1", ttl=6000)
        return

    if "set" in parts:
        try:
            idx = parts.index("set")
            path = parts[idx + 1]
            msgs = load_messages_from_file(path)
            if not msgs:
                reply_msg(client, message_object, thread_id, thread_type, author_id,
                          "❌ Không đọc được file hoặc file trống.", ttl=6000)
                return
            WAR_SETTINGS["messages"] = msgs
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"✅ Đã nạp file `{path}` ({len(msgs)} dòng).", ttl=6000)
        except Exception:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      "⚠️ Sai cú pháp. Ví dụ: war spam set data/spam.txt", ttl=6000)
        return

    delay = WAR_SETTINGS.get("delay", DEFAULT_DELAY)
    messages = WAR_SETTINGS.get("messages", DEFAULT_MESSAGES)
    tagged_user = message_object.mentions[0]["uid"] if message_object.mentions else None

    start_war(client, message_object, thread_id, thread_type, author_id, mode, delay, messages, tagged_user)


def PTA():
    return {
        'war': war
    }
