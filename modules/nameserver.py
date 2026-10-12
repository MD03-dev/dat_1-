from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
import json
import os
import logging
from config import ADMIN, PREFIX

logger = logging.getLogger("NameServerModule")

if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

des = {
    'version': "2.0.0",
    'credits': "Van Chien",
    'description': "Quản lý danh sách HEADER_STYLE - thêm/chọn/xóa theo số",
    'power': "Admin"
}

CONFIG_FILE = "config.py"
NS_DATA_FILE = "data/nameserver_list.json"


# ==================== KIỂM TRA ADMIN ====================
def check_admin_permissions(author_id, client):
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
    except Exception as e:
        logger.error(f"[NAMESERVER] Lỗi đọc seting.json: {e}")

    if isinstance(ADMIN, list):
        if author_id in [str(uid) for uid in ADMIN]:
            return True
    elif author_id == str(ADMIN):
        return True

    return False


# ==================== QUẢN LÝ DANH SÁCH ====================
def load_ns_list():
    try:
        if os.path.exists(NS_DATA_FILE):
            with open(NS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
    except Exception as e:
        logger.error(f"[NAMESERVER] Lỗi đọc danh sách: {e}")
    return []


def save_ns_list(ns_list):
    try:
        os.makedirs("data", exist_ok=True)
        with open(NS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(ns_list, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"[NAMESERVER] Lỗi lưu danh sách: {e}")
        return False


def get_current_header():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('HEADER_STYLE'):
                    val = line.split('=', 1)[1].strip()
                    if (val.startswith('"') and val.endswith('"')) or \
                       (val.startswith("'") and val.endswith("'")):
                        return val[1:-1]
                    if val in ('None', '""', "''", ''):
                        return None
                    return val
    except Exception as e:
        logger.error(f"[NAMESERVER] Lỗi đọc config.py: {e}")
    return None


def set_header_in_config(new_value):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        found = False
        for line in lines:
            if line.strip().startswith('HEADER_STYLE'):
                if new_value is None:
                    new_lines.append('HEADER_STYLE = None\n')
                else:
                    new_lines.append(f'HEADER_STYLE = "{new_value}"\n')
                found = True
            else:
                new_lines.append(line)

        if not found:
            if new_value is None:
                new_lines.append('\nHEADER_STYLE = None\n')
            else:
                new_lines.append(f'\nHEADER_STYLE = "{new_value}"\n')

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    except Exception as e:
        logger.error(f"[NAMESERVER] Lỗi ghi config.py: {e}")
        return False


# ==================== HÀM REPLY_MSG ====================
def reply_msg(client, message_object, thread_id, thread_type, author_id, text_content, ttl=15000):
    try:
        from config import HEADER_STYLE
        header = str(HEADER_STYLE) if HEADER_STYLE else ""
    except Exception:
        header = ""

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


# ==================== LỆNH CHÍNH ====================
def handle_nameserver(message, message_object, thread_id, thread_type, author_id, client):

    if not check_admin_permissions(author_id, client):
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  "Bạn không đủ quyền hạn để sử dụng lệnh này!\nYêu Cầu: Quản Trị Bot\n🚫🚫🚫", ttl=5000)
        return

    parts = message.split(maxsplit=2)
    ns_list = load_ns_list()
    current = get_current_header()
    current_display = f'"{current}"' if current else "Không có (None)"

    # ---- KHÔNG CÓ THAM SỐ → HƯỚNG DẪN ----
    if len(parts) < 2:
        rest_text = (
            f"📋 Hướng dẫn lệnh NameServer:\n"
            f"• {PREFIX}ns <tên mới> : Thêm nameserver mới vào danh sách\n"
            f"• {PREFIX}ns list : Xem danh sách nameserver\n"
            f"• {PREFIX}ns set <số> : Chọn nameserver theo số để dùng\n"
            f"• {PREFIX}ns remove <số> : Xóa nameserver theo số\n"
            f"• {PREFIX}ns remove all : Xóa toàn bộ danh sách\n\n"
            f"🔖 nameserver đang dùng: {current_display}"
        )
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=30000)
        return

    action = parts[1].lower()
    raw_arg = parts[1]  # Giữ nguyên chữ hoa/thường cho tên header

    # ---- NS LIST → XEM DANH SÁCH ----
    if action == "list":
        if not ns_list:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"📭 Danh sách nameserver trống!\nDùng {PREFIX}ns <tên mới> để thêm.", ttl=15000)
            return

        text = f"📋 Danh sách nameserver ({len(ns_list)} nameserver):\n\n"
        for i, item in enumerate(ns_list, 1):
            is_active = "✅ " if item == current else "    "
            text += f"{is_active}{i}. {item}\n"
        text += f"\n🔖 Đang dùng: {current_display}"
        text += f"\n💡 Dùng {PREFIX}ns set <số> để chọn"
        reply_msg(client, message_object, thread_id, thread_type, author_id, text, ttl=20000)

    # ---- NS SET <SỐ> → CHỌN HEADER THEO SỐ ----
    elif action == "set":
        if len(parts) < 3 or not parts[2].strip():
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Thiếu số thứ tự!\nCú pháp: {PREFIX}ns set <số>", ttl=10000)
            return

        target = parts[2].strip()
        if not target.isdigit():
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Phải nhập số thứ tự!\nCú pháp: {PREFIX}ns set <số>\n💡 Dùng {PREFIX}ns list để xem danh sách", ttl=10000)
            return

        if not ns_list:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"📭 Danh sách header trống!\nDùng {PREFIX}ns <tên mới> để thêm.", ttl=10000)
            return

        idx = int(target) - 1
        if idx < 0 or idx >= len(ns_list):
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Số {target} không tồn tại! Danh sách có {len(ns_list)} nameserver.\n❌❌❌", ttl=10000)
            return

        chosen = ns_list[idx]
        if set_header_in_config(chosen):
            logger.info(f"[NAMESERVER] Admin {author_id} chọn header số {target}: {chosen}")
            rest_text = (
                f"✅ Đã set nameserver số {target}:\n"
                f"{chosen}\n\n✅✅✅"
            )
        else:
            rest_text = "❌ Lỗi khi ghi vào config.py!\n❌❌❌"
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)

    # ---- NS REMOVE <SỐ/ALL> → XÓA HEADER ----
    elif action == "remove":
        if len(parts) < 3:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Thiếu tham số!\nCú pháp: {PREFIX}ns remove <số> hoặc {PREFIX}ns remove all", ttl=10000)
            return

        target = parts[2].strip().lower()

        if target == "all":
            save_ns_list([])
            set_header_in_config(None)
            logger.info(f"[NAMESERVER] Admin {author_id} xóa toàn bộ danh sách.")
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      "🗑️ Đã xóa toàn bộ danh sách nameserver!\n✅✅✅", ttl=15000)
            return

        if not target.isdigit():
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      "❌ Tham số không hợp lệ! Nhập số thứ tự hoặc 'all'.\n❌❌❌", ttl=10000)
            return

        idx = int(target) - 1
        if idx < 0 or idx >= len(ns_list):
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Số {target} không tồn tại! Danh sách có {len(ns_list)} nameserver.\n❌❌❌", ttl=10000)
            return

        removed = ns_list.pop(idx)
        save_ns_list(ns_list)

        if removed == current:
            set_header_in_config(None)
            extra = "\n⚠️ nameserver đang dùng đã bị xóa, reset về None."
        else:
            extra = ""

        logger.info(f"[NAMESERVER] Admin {author_id} xóa header số {target}: {removed}")
        reply_msg(client, message_object, thread_id, thread_type, author_id,
                  f"🗑️ Đã xóa nameserver số {target}:\n{removed}{extra}\n✅✅✅", ttl=15000)

    # ---- NS <TÊN MỚI> → THÊM HEADER MỚI ----
    else:
        # Lấy toàn bộ phần sau "ns " làm tên header (giữ nguyên chữ hoa/thường, khoảng trắng)
        new_name = message.split(maxsplit=1)[1].strip() if len(message.split(maxsplit=1)) > 1 else ""

        if not new_name:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"❌ Lệnh không hợp lệ! Dùng {PREFIX}ns để xem hướng dẫn.\n❌❌❌", ttl=10000)
            return

        if new_name in ns_list:
            reply_msg(client, message_object, thread_id, thread_type, author_id,
                      f"⚠️ nameserver này đã có trong danh sách rồi!\n⚠️⚠️⚠️", ttl=10000)
            return

        ns_list.append(new_name)
        if save_ns_list(ns_list):
            logger.info(f"[NAMESERVER] Admin {author_id} thêm nameserver: {new_name}")
            rest_text = (
                f"✅ Đã thêm nameserver mới:\n"
                f"{new_name}\n\n"
                f"📌 Số thứ tự: {len(ns_list)}\n"
                f"💡 Dùng {PREFIX}ns set {len(ns_list)} để chọn dùng\n✅✅✅"
            )
        else:
            rest_text = "❌ Lỗi khi lưu danh sách!\n❌❌❌"
        reply_msg(client, message_object, thread_id, thread_type, author_id, rest_text, ttl=15000)


def PTA():
    return {
        'nameserver': handle_nameserver,
        'ns': handle_nameserver
    }
