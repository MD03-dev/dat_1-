import json, os, time, sys, random, re, unicodedata
from fbchat.models import Message, Mention
from datetime import datetime, timedelta
import threading
import logging
import urllib.parse
import queue
import math
from PIL import Image
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import ffmpeg
import pyfiglet
from colorama import Fore, Style, init
from zlapi import ZaloAPI
from zlapi.models import *
from core.bot_sys import *
from config import API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES, ADMIN, PREFIX
from PTA import CommandHandler
from logging_utils import Logging
from event.event import handleGroupEvent
from threading import Lock
from commands.antispam import AntiSpamHandler
from commands.anticard import AntiCardHandler
from commands.loctk import LocTKHandler
from commands.antiundo import UndoHandler
from commands.lockbot import LockBotHandler
from commands.whitelist import WhitelistHandler
from commands.menuwar import WarHandler
from commands.bcmd import BcmdHandler
from modules.game import GameHandler
from commands.antiphoto import AntiPhotoHandler
from modules.afk import AFKHandler
from modules.treo import handle_treo_command
from modules.autojoin import AutoJoinHandler
from modules.ff  import handle_ff_command
from modules.attack import handle_attack_command
from modules.autoreply import handle_autoreply_message
from commands.antiall import AntiAllHandler
from commands.antivideo import AntiVideoHandler
from commands.antiricon import AntiRiconHandler
from modules.msvc import MSVCHandler
from commands.bot import BotStatusHandler
from commands.antistk import AntiStickerHandler
from commands.antifile import AntiFileHandler
from modules.antilink import AntiLinkHandler
from concurrent.futures import ThreadPoolExecutor
from modules import autoreaction
import collections
from modules import scl 
from modules import yt

init(autoreset=True)
COLORS_HEX = [
    "FF9900", "FFFF33", "33FFFF", "FF99FF", "FF3366",
    "FFFF66", "FF00FF", "66FF99", "00CCFF", "FF0099",
    "FF0066", "0033FF", "FF9999", "00FF66", "00FFFF",
    "CCFFFF", "8F00FF", "FF00CC", "FF0000", "FF1100", "FF3300"
]

def hex_to_ansi(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'\033[38;2;{r};{g};{b}m'

print(hex_to_ansi("33FFFF") + pyfiglet.figlet_format("Van Chien"))

main_executor = ThreadPoolExecutor(max_workers=100)

AUTOREPLY_ENABLED = True

import re
import json
import threading
import time
import logging
import random
import requests
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor, as_completed
from zlapi.models import ThreadType, Message
from core.bot_sys import read_settings, write_settings
from zlapi import ZaloAPIException
from core.bot_sys import admin_cao  # ✅ Check quyền admin
from core.bot_sys import is_admin, read_settings, write_settings
from zlapi.models import Message, MultiMsgStyle, MessageStyle, ThreadType
# --- Logging config ---
logging.basicConfig(
    level=logging.INFO,  # Đổi DEBUG -> INFO cho nhẹ
    format='%(asctime)s - [AUTOJOIN] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
import logging
logging.disable(logging.CRITICAL)


file_handler = logging.FileHandler('autojoin.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - [AUTOJOIN] - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# --- Regex compile ---
ZALO_GROUP_LINK_REGEX = re.compile(r'https:\/\/(?:zalo\.me|chat\.zalo\.me)\/g\/[a-zA-Z0-9]+(?:\?[^ ]*)?')

# --- Shared vars ---
failed_links = set()
failed_lock = threading.Lock()

# --- Load failed_links ---
try:
    with open('failed_links.json', 'r') as f:
        content = f.read().strip()
        failed_links = set(json.loads(content)) if content else set()
    logger.info(f"Đã tải {len(failed_links)} link thất bại từ failed_links.json")
except Exception as e:
    logger.warning(f"Không thể load failed_links.json: {e}")
    failed_links = set()

# --- Save failed_links batch ---
def save_failed_links():
    with failed_lock:
        try:
            with open('failed_links.json', 'w') as f:
                json.dump(list(failed_links), f)
        except Exception as e:
            logger.error(f"Lỗi khi lưu failed_links.json: {e}")

# --- Shared requests session ---
_shared_session = requests.Session()
adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50)
_shared_session.mount("http://", adapter)
_shared_session.mount("https://", adapter)
_shared_session.headers.update({'User-Agent': 'ZaloWeb/1.0'})
requests.get = _shared_session.get
requests.post = _shared_session.post
requests.put = _shared_session.put
requests.delete = _shared_session.delete

# --- Helpers ---
def extract_links_from_message(message_object, text):
    links = []
    if text:
        links.extend(ZALO_GROUP_LINK_REGEX.findall(text))

    attachments = getattr(message_object, 'attachments', None) or []
    for att in attachments:
        if isinstance(att, dict):
            att_text = str(att.get('content', '') or att.get('url', '') or att.get('link', '') or att.get('href', ''))
            links.extend(ZALO_GROUP_LINK_REGEX.findall(att_text))

    return list(dict.fromkeys(links))  # unique giữ nguyên thứ tự


def try_autojoin_from_link(client, link):
    if link in failed_links:
        return False, "Bỏ qua link thất bại trước đó", None, None

    if not ZALO_GROUP_LINK_REGEX.match(link):
        return False, "Link nhóm không hợp lệ", None, None

    group_code = link.split("/")[-1].split("?")[0].lower()

    try:
        join_response = client.joinGroup(link)
        time.sleep(0.01)  # delay tối thiểu
        return True, f"Yêu cầu join đã gửi ({group_code})", join_response, None

    except ZaloAPIException as e:
        if "404" in str(e):
            with failed_lock:
                failed_links.add(link)
            return False, "Link không hợp lệ (404)", None, None
        return False, f"API lỗi: {str(e)}", None, None
    except Exception as e:
        with failed_lock:
            failed_links.add(link)
        return False, f"Lỗi không mong muốn: {str(e)}", None, None


import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_message_for_autojoin(client, message_object, thread_id, thread_type, author_id, message_text, mid, logger_ext=None):
    log = logger_ext or logger
    try:
        links = extract_links_from_message(message_object, message_text)
        if not links:
            return

        # --- Đọc config của bot ---
        settings = read_settings() or {}

        # ✅ Autojoin bật thì quét link từ MỌI nhóm, không giới hạn allowed_thread_ids
        if not settings.get("autojoin_enabled", False):
            return

        # ✅ Kiểm tra session
        if not client.isLoggedIn():
            log.error("Session không hợp lệ (isLoggedIn = False)")
            return

        results = []
        new_failed_links = set()

        # --- Dùng thread pool nhỏ để xử lý nhanh ---
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_link = {executor.submit(try_autojoin_from_link, client, link): link for link in links[:5]}
            for future in as_completed(future_to_link):
                link = future_to_link[future]
                try:
                    success, msg, response, group_info = future.result()
                    results.append((link, success, msg, group_info))
                    if not success and "404" in msg:
                        new_failed_links.add(link)

                    # ⬅ Delay sau khi join mỗi link
                    time.sleep(0.1)
                except Exception as e:
                    results.append((link, False, f"Lỗi xử lý: {e}", None))
                    new_failed_links.add(link)

        # --- Cập nhật danh sách failed_links ---
        if new_failed_links:
            with failed_lock:
                failed_links.update(new_failed_links)
            save_failed_links()

        # --- Gửi reaction thay cho tin nhắn ---
        for link, success, msg, group_info in results:
            try:
                if success:
                    # Chọn ngẫu nhiên icon khi join thành công
                    icon = random.choice(["🗿Banamcoder😗", "🐢nambárõ🤨", "💸thuêbot50k🐧","💸Nhận Rãi Thuê","🌟Cho Thuê Bót😹"])
                else:
                    icon = "Phải Chịu🐻"

                client.sendReaction(
                    message_object,
                    icon,
                    thread_id,
                    thread_type
                )
                time.sleep(0)
            except Exception as e:
                log.error(f"Lỗi khi gửi reaction cho {link}: {e}")

    except Exception as e:
        log.exception(f"Lỗi trong process_message_for_autojoin: {e}")


from zlapi.models import Message, MessageStyle, MultiMsgStyle
from core.bot_sys import admin_cao, get_user_name_by_id
import logging

logger = logging.getLogger(__name__)

def handle_autojoin_command(self, message_object, thread_id, thread_type, author_id, message_text, mid, logger_ext=None):
    log = logger_ext or logger

    # ⚙️ Bỏ kiểm tra quyền admin_cao, cho phép tất cả người dùng dùng lệnh
    args = message_text.split()
    if len(args) < 2:
        self.sendReaction(message_object, "❓", thread_id, thread_type)
        author_name = get_user_name_by_id(self, author_id) or str(author_id)
        msg = f"➜{author_name}\n/-li Fen Ơi, dùng {self.prefix}autojoin on|off nha"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1
        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])
        self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=60000)
        return

    action = args[1].lower()
    settings = read_settings() or {}
    author_name = get_user_name_by_id(self, author_id) or str(author_id)

    try:
        if action in ("on", "enable", "1", "true"):
            settings["autojoin_enabled"] = True
            write_settings(self.uid, settings)
            status_text = "on"
            icon = "💢"

        elif action in ("off", "disable", "0", "false"):
            settings["autojoin_enabled"] = False
            write_settings(self.uid, settings)
            status_text = "off"
            icon = "❌"

        else:
            self.sendReaction(message_object, "❓", thread_id, thread_type)
            msg = f"➜{author_name}\nFen Ơi, /-li dùng {self.prefix}autojoin on|off nha"
            name_offset = 0
            name_len = len(author_name)
            if any(ord(ch) > 127 for ch in author_name):
                name_len += 1
            styles = MultiMsgStyle([
                MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
                MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
            ])
            self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type, ttl=60000)
            return

        # --- Gửi reaction và báo cáo ---
        self.sendReaction(message_object, icon, thread_id, thread_type)
        msg = f"➜{author_name}\n/-li Fen Ơi, Autojoin {status_text} Gòi"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1

        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])

        self.send(
            Message(text=msg, style=styles),
            thread_id=thread_id,
            thread_type=thread_type,
            ttl=60000
        )

    except Exception as e:
        log.error(f"Lỗi không mong muốn khi xử lý lệnh /autojoin: {e}")
        self.sendReaction(message_object, "⚠️", thread_id, thread_type)
        msg = f"{author_name}\n⚠️ Lỗi không mong muốn khi xử lý lệnh"
        name_offset = 0
        name_len = len(author_name)
        if any(ord(ch) > 127 for ch in author_name):
            name_len += 1
        styles = MultiMsgStyle([
            MessageStyle(offset=name_offset, length=name_len, style="color", color="#DB342E", auto_format=False),
            MessageStyle(offset=name_offset, length=name_len, style="bold", size="15", auto_format=False),
        ])
        self.send(Message(text=msg, style=styles), thread_id=thread_id, thread_type=thread_type)

last_command_times = {}
spam_warnings = {}
warning_count = {}


import time
import threading

# Lưu trạng thái spam
last_command_times = {}
warning_count = {}
spam_warnings = {}

def anti_spam_prefix(bot, author_id, thread_id, thread_type, msgId, message_text, base_cooldown=2):
    """
    Kiểm tra spam prefix và gửi reaction cảnh báo ⏳, sau đó tự động undo reaction.
    
    Args:
        bot: instance ZaloAPI
        author_id (str|int): ID người gửi
        thread_id (str|int): ID nhóm hoặc user
        thread_type (ThreadType): ThreadType.USER hoặc ThreadType.GROUP
        msgId (str|int): ID tin nhắn gốc
        message_text (str): Nội dung tin nhắn
        base_cooldown (int): thời gian cooldown cơ bản (giây)
    """
    if admin_cao(bot, str(author_id)):
        return


        return False

    now = time.time()
    last_time = last_command_times.get(author_id, 0)
    diff = now - last_time

    count = warning_count.get(author_id, 0)
    cooldown = base_cooldown * max(1, count + 1)

    if diff < cooldown:
        warning_count[author_id] = min(count + 1, 3)

        if spam_warnings.get(author_id, 0) + 2 < now:
            spam_warnings[author_id] = now
            try:
                reaction_emoji = "⏳"
                # Gửi reaction cảnh báo
                bot.sendReaction(reaction_emoji, msgId, thread_id, thread_type)
                print(f"[ANTI-SPAM] Gửi reaction '{reaction_emoji}' cho {author_id} "
                      f"(còn {int(cooldown-diff)}s, mức {warning_count[author_id]})")
                print(f"[ANTI-SPAM] Tin nhắn ID: {msgId}, thread: {thread_id}, type: {thread_type}")

                # Thread undo reaction sau 1 giây
                def undo_reaction():
                    try:
                        time.sleep(1)
                        bot.sendReaction(
                            emoji=reaction_emoji,
                            msgId=msgId,
                            thread_id=thread_id,
                            thread_type=thread_type,
                            action=0  # action=0 để xóa reaction
                        )
                        print(f"[UNDO-REACTION] ✅ Reaction '{reaction_emoji}' đã được gỡ (msgId={msgId})")
                    except Exception as e:
                        print(f"[UNDO-REACTION] ❌ Lỗi khi gỡ reaction: {e}")

                threading.Thread(target=undo_reaction).start()

            except Exception as e:
                print(f"[ANTI-SPAM] ❌ Lỗi gửi reaction: {e}")
        else:
            print(f"[ANTI-SPAM] Không gửi reaction vì vừa gửi gần đây.")
        return True

    # Nếu hợp lệ -> ghi lại thời gian và giảm cấp phạt (nếu có)
    last_command_times[author_id] = now
    if warning_count.get(author_id, 0) > 0:
        warning_count[author_id] -= 1
    print(f"[ANTI-SPAM] {author_id} OK, cho phép chạy lệnh. "
          f"(Cấp còn lại: {warning_count.get(author_id,0)})")
    return False
    

def get_allowed_thread_ids(self=None):
    try:
        if os.path.exists("settings.json"):
            with open("settings.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("allowed_thread_ids", [])
    except Exception as e:
        print(f"[BOT_SYS] Lỗi đọc allowed_thread_ids: {e}")
    return []

def load_mute_data():
    if not os.path.exists("mute.json"):
        return {}
    with open("mute.json", "r", encoding="utf-8") as f:
        return json.load(f)

def read_settings():
    if not os.path.exists("setings.json"):
        return {}
    with open("setings.json", "r", encoding="utf-8") as f:
        return json.load(f)
        
class ResetBot:
    """
    ResetBot manages periodic restarts. For safety we disable auto-restart by default.
    If you want to enable it later, change disable_autorestart=False when creating the instance.
    """
    def __init__(self, reset_interval=900, disable_autorestart=True):
        self.reset_event = threading.Event()
        self.reset_interval = reset_interval
        # By default we keep autorestart disabled to avoid unexpected process respawns.
        self.autorestart = False
        if disable_autorestart:
            logger.info("Auto-restart is disabled by configuration (safe mode).")
        else:
            # If explicitly enabled, try to load persisted setting (legacy behavior).
            self.load_autorestart_setting()
            if self.autorestart:
                logger.info("Auto-restart is enabled; starting periodic reset thread.")
                threading.Thread(target=self.reset_code_periodically, daemon=True).start()

    def load_autorestart_setting(self):
        try:
            # Try to read common filenames to be tolerant with typos in repo
            candidates = ["seting.json", "seting.json", "setting.json", "settings.json"]
            settings = {}
            for fn in candidates:
                if os.path.exists(fn):
                    with open(fn, "r", encoding="utf-8") as f:
                        try:
                            settings = json.load(f)
                            break
                        except json.JSONDecodeError:
                            continue
            # Default to False if key missing or malformed
            self.autorestart = str(settings.get("autorestart", "False")) == "True"
        except Exception as e:
            logger.error(f"Lỗi khi tải cấu hình autorestart: {e}")
            self.autorestart = False

    def reset_code_periodically(self):
        while not self.reset_event.is_set():
            time.sleep(self.reset_interval)
            logger.info("Đang tiến hành khởi động lại bot theo lịch (chế độ autorestart).")
            self.restart_bot()

    def restart_bot(self):
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            gui_message = f"➜ Bot đã khởi động lại thành công vào lúc: {current_time}"
            logger.info(gui_message)
            # IMPORTANT: We do NOT perform os.execl here anymore to avoid automatic process respawn.
            # If you really need to restart the process, handle it externally (systemd / supervisor).
        except Exception as e:
            logger.error(f"Lỗi khi khởi động lại bot: {e}")

logger = Logging()

class Client(ZaloAPI):

    def __init__(self, api_key, secret_key, imei, session_cookies, reset_interval=900, auto_approve_interval=0):
        self.uid = None
        self._imei = imei
        
        super().__init__(api_key, secret_key, imei=imei, session_cookies=session_cookies)
        self.is_main_bot = True
        self.prefix = PREFIX  # ✅ thêm dòng này để fix lỗi
        self.scl_user_states = {} 
        self.settings = self.load_settings()
        self.ADMIN = str(self.settings.get("admin") or ADMIN)
        self.ADM = [str(uid) for uid in self.settings.get("adm", [])]
        
        if not self.uid:
            try:
                self.uid = self.fetchAccountInfo().profile.get("userId")
            except Exception as e:
                logger.error(f"Không thể fetch UID của bot sau khi login: {e}")
                sys.exit("Lỗi nghiêm trọng: Không xác định được UID của bot.")

        logger.info(f"Admin ID: {self.ADMIN}")
        logger.info(f"Additional Admins: {self.ADM}")
        logger.info(f"✅ Bot Main đã đăng nhập thành công với UID: {self.uid}")

        self.command_handler = CommandHandler(self)
        self.reset_bot = ResetBot(reset_interval)
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,  # Giảm retry để tăng tốc độ
            backoff_factor=0.5,  # Giảm backoff time
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=20,  # Tăng connection pool
            pool_maxsize=20  # Tăng max connections
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.response_time_limit = timedelta(seconds=0)

        self.group_info_cache = {}
        self.group_info_cache_timestamps = {}  # Thêm timestamp cho cache
        self.group_info_cache_ttl = 300  # Cache 5 phút
        self.user_info_cache = {}  # Cache cho user info
        self.user_info_cache_timestamps = {}
        self.user_info_cache_ttl = 600  # Cache 10 phút
        self.last_sms_times = {}
        self.temp_thread_storage = {}
        self.search_results = {}
        self.search_result_messages = {}
        self.search_result_ttl = 24
        self.scl_user_states = {}
        self.yt_user_states = {}
        self.spam_enabled = self.load_spam_settings()
        self.group_lock_status = {}
        self.bot_status_handler = BotStatusHandler(self)
        self.user_message_times = {}
        self.warned_users = {}
        self.spam_threshold = 5
        self.kick_threshold = 6
        self.spam_window = 7
        self.antiricon_handler = AntiRiconHandler(self)
        self.antifile_handler = AntiFileHandler(self)
        self.loctk_enabled = self.load_loctk_settings()
        self.banned_words = self.load_banned_words()
        self.banned_word_violations = {}
        self.FileNM = 'database/dataundo.json'
        self.locked_users_file = 'data/locked_users.json'
        self.locked_users = self.load_locked_users()
        self.antispam_handler = AntiSpamHandler(self)
        self.antisticker_handler = AntiStickerHandler(self)
        self.loctk_handler = LocTKHandler(self)
        self.undo_handler = UndoHandler(self)
        self.afk_handler = AFKHandler(self)
        self.lockbot_handler = LockBotHandler(self)
        self.antilink_handler = AntiLinkHandler(self)
        self.game_handler = GameHandler(self)
        self.menuwar_handler = WarHandler(self)
        self.anticard_handler = AntiCardHandler(self)
        self.whitelist_handler = WhitelistHandler(self)
        self.bcmd_handler = BcmdHandler(self)
        self.autojoin_handler = AutoJoinHandler(self)
        self.msvc_handler = MSVCHandler(self)
        self.antiall_handler = AntiAllHandler(self)
        self.antiphoto_handler = AntiPhotoHandler(self)
        self.antivideo_handler = AntiVideoHandler(self)
        self.auto_approve_enabled = self.load_auto_approve_settings()
        self.auto_approve_interval = auto_approve_interval
        self.last_auto_approve_check = datetime.min
        self.group_message_counts = {}
        self.duyetbox_data = self.load_duyetbox_data()
        self.whitelist = self.load_whitelist()
        self.whitelist_lock = Lock()
        self.sendtask_autosticker_file = "modules/cache/sendtask_autosticker.json"
        self.datasticker_file = "database/datasticker.json"
        threading.Thread(target=self.auto_approve_periodically, daemon=True).start()
        logger.info('EVENT GROUP: Tiến hành nhận sự kiện các nhóm...')
        self.load_sticker_data()
        
        if not os.path.exists("data/whitelist.json"):
            with open("data/whitelist.json", "w") as f:
                json.dump({}, f)

    def switch_to_ai_bot(self):
        logger.warning("🚀 Nhận lệnh chuyển đổi sang Bot AI...")
        
        session_cookies = self.getSession()
        imei = self._imei

        if not session_cookies or not imei:
            logger.error("Không thể lấy thông tin session. Hủy chuyển đổi.")
            self.sendMessage(Message(text="❌ Lỗi: Không thể lấy thông tin session để chuyển đổi."), self.ADMIN, ThreadType.USER)
            return

        session_data = {
            "cookies": session_cookies,
            "imei": imei
        }

        try:
            with open("session.json", "w") as f:
                json.dump(session_data, f, indent=4)
            logger.info("✅ Đã lưu session vào session.json")
        except Exception as e:
            logger.error(f"Lỗi khi lưu session: {e}")
            self.sendMessage(Message(text=f"❌ Lỗi khi lưu session: {e}"), self.ADMIN, ThreadType.USER)
            return

        python = sys.executable
        try:
            os.execl(python, python, 'botAI.py')
        except Exception as e:
            logger.error(f"Lỗi khi thực thi botAI.py: {e}")

    def load_whitelist(self):
        try:
            if not os.path.exists("data/whitelist.json"):
                logger.warning("Whitelist file not found, creating empty whitelist")
                with open("data/whitelist.json", "w") as f:
                    json.dump({}, f)
                return {}
            
            with open("data/whitelist.json", "r", encoding="utf-8") as f:
                whitelist = json.load(f)
                logger.info(f"Loaded whitelist: {whitelist}")
                return whitelist
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding whitelist.json: {e}. Initializing empty whitelist.")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading whitelist: {e}. Initializing empty whitelist.")
            return {}

    def save_whitelist(self):
        with self.whitelist_lock:
            try:
                with open("data/whitelist.json", "w", encoding="utf-8") as f:
                    json.dump(self.whitelist, f, indent=4, ensure_ascii=False)
                logger.info("Whitelist saved successfully")
            except Exception as e:
                logger.error(f"Error saving whitelist: {e}")

    def load_sticker_data(self):
        try:
            with open(self.datasticker_file, "r") as f:
                self.sticker_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.sticker_data = []
            self.save_sticker_data()

    def save_sticker_data(self):
        with open(self.datasticker_file, "w") as f:
            json.dump(self.sticker_data, f, indent=4)

    def load_allowed_groups(self):
        try:
            with open(self.sendtask_autosticker_file, "r") as f:
                return json.load(f).get("groups", [])
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_allowed_groups(self, allowed_groups):
        with open(self.sendtask_autosticker_file, "w") as f:
            json.dump({"groups": allowed_groups}, f, indent=4)

    def auto_approve_periodically(self):
        while True:
            self.check_and_handle_auto_approve()
            time.sleep(self.auto_approve_interval)

    def onEvent(self, event_data, event_type):
        if event_type == GroupEventType.LEAVE:
            try:
                data = event_data.get('value', {})
                leftUser = data.get('updateUid')
                groupId = data.get('groupId')
                
                if leftUser == self.uid:
                    remove_uid_on_leave(groupId)
                    # Dòng log hiển thị ra màn hình
                    logger.info(f" {Fore.YELLOW}[WELCOME]{Style.RESET_ALL} Đã xóa cấu hình nhóm {groupId} (Bot rời nhóm)")
            except Exception as e:
                logger.error(f" Lỗi xóa welcome_setting: {e}")
        
        # Tiếp tục xử lý các sự kiện khác
        handleGroupEvent(self, event_data, event_type)

    def send_request(self, url):
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Lỗi request: {e}")
            return None

    def load_auto_approve_settings(self):
        try:
            with open("data/auto_approve_settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error("Lỗi khi đọc file auto_approve_settings.json. Khởi tạo settings trống.")
            return {}

    def save_auto_approve_settings(self):
        try:
            with open("data/auto_approve_settings.json", "w") as f:
                json.dump(self.auto_approve_enabled, f, indent=4)
        except Exception as e:
            logger.error(f"Lỗi khi lưu cài đặt auto-approve: {e}")
    
    def reload_duyetbox_data(self):
        self.duyetbox_data = self.load_duyetbox_data()
        logger.info("[Duyệt Box] Đã tải lại dữ liệu duyệt box.")
        
    def handle_auto_approve_command(self, message_text, message_object, thread_id, thread_type, author_id):
        if str(author_id) != self.ADMIN and str(author_id) not in self.ADM:
            self.replyMessage(Message(text="➜ ⚠️ Bạn không có quyền sử dụng lệnh này. Chỉ quản trị viên mới có thể thực hiện."), message_object, thread_id, thread_type, ttl=60000)
            return

        parts = message_text.split()
        if len(parts) < 2:
            self.replyMessage(Message(text=f"➜ Hướng dẫn sử dụng: {PREFIX}autoapprv <on/off>\n➜ Ví dụ: {PREFIX}autoapprv on (Bật tự động duyệt thành viên mới)"), message_object, thread_id, thread_type, ttl=60000)
            return

        action = parts[1].lower()
        if action == "on":
            self.auto_approve_enabled[thread_id] = True
            self.save_auto_approve_settings()
            self.replyMessage(Message(text="➜ ✅ Đã bật chế độ tự động duyệt thành viên mới trong nhóm này."), message_object, thread_id, thread_type, ttl=60000)
        elif action == "off":
            self.auto_approve_enabled[thread_id] = False
            self.save_auto_approve_settings()
            self.replyMessage(Message(text="➜ 🚫 Đã tắt chế độ tự động duyệt thành viên mới trong nhóm này."), message_object, thread_id, thread_type, ttl=60000)
        else:
            self.replyMessage(Message(text=f"➜ ❗ Lệnh không hợp lệ. Vui lòng sử dụng '{PREFIX}autoapprv on' hoặc '{PREFIX}autoapprv off'."), message_object, thread_id, thread_type, ttl=60000)

    def load_spam_settings(self):
        try:
            with open("data/spam_settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error("Lỗi khi đọc file spam_settings.json. Khởi tạo settings trống.")
            return {}

    def save_spam_settings(self):
        try:
            with open("data/spam_settings.json", "w") as f:
                json.dump(self.spam_enabled, f, indent=4)
        except Exception as e:
            logger.error(f"Lỗi khi lưu cài đặt anti-spam: {e}")

    def load_loctk_settings(self):
        try:
            with open("data/loctk_settings.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error("Lỗi khi đọc file loctk_settings.json. Khởi tạo settings trống.")
            return {}

    def save_loctk_settings(self):
        try:
            with open("data/loctk_settings.json", "w") as f:
                json.dump(self.loctk_enabled, f, indent=4)
        except Exception as e:
            logger.error("Lỗi khi lưu cài đặt lọc từ: {e}")

    def load_banned_words(self):
        try:
            with open("data/banned_words.json", "r", encoding='utf-8') as f:
                data = json.load(f)
                return data.get("banned_words", {"words": []}).get("words", [])
        except FileNotFoundError:
            logger.error("File banned_words.json không tìm thấy.")
            return []
        except json.JSONDecodeError:
            logger.error("Lỗi khi đọc file banned_words.json.")
            return []

    def save_banned_words(self):
        try:
            with open("data/banned_words.json", "w", encoding='utf-8') as f:
                json.dump({"banned_words": {"words": self.banned_words}}, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Lỗi khi lưu danh sách từ cấm: {e}") 

    def send_sticker(self, id, catId, thread_id, thread_type, author_id, message_object):
        try:
            author_info_for_sticker = self.fetchUserInfo(author_id)
            if author_info_for_sticker and getattr(author_info_for_sticker, "changed_profiles", None):
                fetched_name = author_info_for_sticker.changed_profiles.get(author_id, {}).get('zaloName')
                author_display_name_sticker = fetched_name if fetched_name and fetched_name != 'không xác định' else str(author_id)
            else:
                author_display_name_sticker = str(author_id)

            text = f"➜ [UNDO STICKER] {author_display_name_sticker} vừa thu hồi một sticker."
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[UNDO STICKER]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[UNDO STICKER]"), style="bold", auto_format=False),
            ])
            offset = text.find(f"{author_display_name_sticker}")
            self.replyMessage(Message(text=text, mention=Mention(author_id, len(f"{author_display_name_sticker}"), offset), style=styles), message_object, thread_id, thread_type, ttl=120000)
            self.sendSticker(1, id, catId, thread_id, thread_type)
        except Exception as e:
            logger.error(f"Lỗi khi gửi sticker: {e}")

    def handle_lockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        self.lockbot_handler.handle_lockbot_command(message_text, message_object, thread_id, thread_type, author_id)

    def handle_unlockbot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        self.lockbot_handler.handle_unlockbot_command(message_text, message_object, thread_id, thread_type, author_id)

    def load_mute_list(self):
        mute_PTA = "data/khoamom.json"
        if os.path.exists(mute_PTA):
            with open(mute_PTA, 'r') as f:
                return json.load(f)
        return {}

    def is_user_muted(self, thread_id, author_id):
        mute_list = self.load_mute_list()
        if thread_id in mute_list:
            return str(author_id) in mute_list[thread_id]
        return False

    def hex_to_ansi(self, hex_color):
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'\033[38;2;{r};{g};{b}m'

    def is_group_admin(self, thread_id, user_id):
        try:
            if thread_id in self.group_info_cache:
                group_data = self.group_info_cache[thread_id]
            else:
                group_info = self.fetchGroupInfo(thread_id)
                if not group_info or not hasattr(group_info, 'gridInfoMap') or thread_id not in group_info.gridInfoMap:
                    logger.warning(f"Không tìm thấy thông tin nhóm hoặc gridInfoMap cho thread_id: {thread_id} để kiểm tra admin.")
                    return False
                group_data = group_info.gridInfoMap[thread_id]
                self.group_info_cache[thread_id] = group_data
            
            creator_id = group_data.get('creatorId')
            admin_ids = group_data.get('adminIds', [])
            
            user_id_str = str(user_id)
            
            if user_id_str == str(creator_id) or user_id_str in [str(admin_id) for admin_id in admin_ids]:
                return True
            return False
        except Exception as e:
            logger.error(f"Lỗi khi kiểm tra admin nhóm {thread_id} cho user {user_id}: {e}")
            return False

    def get_content_message(self, message_object):
        if message_object.msgType == 'chat.recommand':
            return ""

        texts = []

        if hasattr(message_object, 'text') and isinstance(message_object.text, str):
            texts.append(message_object.text)
        elif message_object.get('msg') and isinstance(message_object.get('msg'), str):
            texts.append(message_object.get('msg'))

        content = message_object.get('content')
        if isinstance(content, str):
            texts.append(content)
        elif isinstance(content, dict):
            if content.get('title') and isinstance(content['title'], str):
                texts.append(content['title'])
            if content.get('href') and isinstance(content['href'], str):
                texts.append(content['href'])
            if content.get('description') and isinstance(content['description'], str):
                texts.append(content['description'])
            
            if content.get('params') and isinstance(content['params'], str):
                try:
                    params_data = json.loads(content['params'])
                    if params_data.get('mediaTitle') and isinstance(params_data['mediaTitle'], str):
                        texts.append(params_data['mediaTitle'])
                    if params_data.get('href') and isinstance(params_data['href'], str):
                        texts.append(params_data['href'])
                    if params_data.get('url') and isinstance(params_data['url'], str):
                        texts.append(params_data['url'])
                except json.JSONDecodeError:
                    pass

        attach = message_object.get('attach')
        if isinstance(attach, dict):
            if attach.get('title') and isinstance(attach['title'], str):
                texts.append(attach['title'])
            if attach.get('href') and isinstance(attach['href'], str):
                texts.append(attach['href'])
            if attach.get('description') and isinstance(attach['description'], str):
                texts.append(attach['description'])
            
            if attach.get('params') and isinstance(attach['params'], str):
                try:
                    params_data = json.loads(attach['params'])
                    if params_data.get('mediaTitle') and isinstance(params_data['mediaTitle'], str):
                        texts.append(params_data['mediaTitle'])
                    if params_data.get('href') and isinstance(params_data['href'], str):
                        texts.append(params_data['href'])
                    if params_data.get('url') and isinstance(params_data['url'], str):
                        texts.append(params_data['url'])
                except json.JSONDecodeError:
                    pass
        
        return " ".join(filter(None, texts))

    def is_url_in_message(self, message_object):
        msg_type = message_object.get('msgType', '')

        absolutely_ignored_msg_types = [
            'share.file',
            'chat.sticker',
            'chat.voice',
            'chat.gif',
            'chat.location.new'
        ]
        if msg_type in absolutely_ignored_msg_types:
            return False

        url_regex = re.compile(
            r'(?:(?:https?://)|(?:www\.))[\w.-]+\.(?:[a-zA-Z]{2,})[\w\/?=&%.-]*|(?<!\w)[\w-]+\.(com|vn|net|org|info|xyz|me|link|top|site|io|tv|cc|biz|us|uk|au|ca)(?:\.[\w-]+)*[\w\/?=&%.-]*(?!\w)',
            re.IGNORECASE
        )

        if msg_type.startswith('chat.photo') or msg_type.startswith('chat.video'):
            title_to_check = []
            content = message_object.get('content', {})
            if isinstance(content, dict) and content.get('title'):
                title_to_check.append(content.get('title'))
            
            attach = message_object.get('attach', {})
            if isinstance(attach, dict) and attach.get('title'):
                title_to_check.append(attach.get('title'))
            
            if not title_to_check:
                return False
            
            text_from_title = " ".join(title_to_check)
            if url_regex.search(text_from_title):
                logger.info(f"ANTI-LINK: Phát hiện link trong mô tả của tin nhắn {msg_type}.")
                return True
            
            return False

        text_to_check = self.get_content_message(message_object)
        if not text_to_check:
            return False

        if url_regex.search(text_to_check):
            logger.info(f"ANTI-LINK: Phát hiện link trong tin nhắn loại '{msg_type}'.")
            return True

        return False

    def check_and_handle_auto_approve(self):
        now = datetime.now()
        if (now - self.last_auto_approve_check).total_seconds() >= self.auto_approve_interval:
            for thread_id, enabled in self.auto_approve_enabled.items():
                if enabled == True:
                    self.auto_approve_pending_members(thread_id)
            self.last_auto_approve_check = now

    def auto_approve_pending_members(self, thread_id):
        try:
            group_info = self.fetchGroupInfo(thread_id)
            if not group_info or not hasattr(group_info, 'gridInfoMap'):
                return False
            group_data = group_info.get('gridInfoMap', {}).get(thread_id)
            if not isinstance(group_data, dict):
                return False
            pending_members = group_data.get('pendingApprove', {}).get('uids', [])
            for member_id in pending_members:
                if hasattr(self, 'handleGroupPending'):
                    if thread_id in self.auto_approve_enabled:
                        self.handleGroupPending(member_id, thread_id)
            return True
        except Exception as e:
            return False

    def handle_auto_sticker(self, thread_id, thread_type, message_object):
        allowed_groups = self.load_allowed_groups()  
        if thread_type == ThreadType.GROUP and thread_id in allowed_groups:
            if message_object.msgType == "webchat":
                self.group_message_counts[thread_id] = self.group_message_counts.get(thread_id, 0) + 1
                if self.group_message_counts[thread_id] >= random.randint(10, 15):
                    if self.sticker_data:
                        sticker = random.choice(self.sticker_data)
                        self.sendSticker(1, sticker["id"], sticker["catId"], thread_id, thread_type)
                        self.group_message_counts[thread_id] = 0

    def load_settings(self):
        try:
            with open("seting.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("Không tìm thấy file seting.json")
            return {}
        except json.JSONDecodeError:
            logger.error("Lỗi giải mã JSON trong file seting.json")
            return {}

    def reload_admin_settings(self):
        """Cập nhật lại danh sách Admin từ file seting.json vào bộ nhớ"""
        try:
            self.settings = self.load_settings()
            if self.settings:
                self.ADMIN = str(self.settings.get("admin") or ADMIN)
                self.ADM = [str(uid) for uid in self.settings.get("adm", [])]
                logger.info(f"♻️ Đã cập nhật quyền Admin: {len(self.ADM)} admin phụ.")
                return True
        except Exception as e:
            logger.error(f"Lỗi khi reload settings: {e}")
        return False

    def load_duyetbox_data(self):
        try:
            with open("modules/cache/duyetboxdata.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning("Không tìm thấy file duyetboxdata.json")
            return []
        except json.JSONDecodeError:
            logger.error("Lỗi giải mã JSON trong file duyetboxdata.json")
            return []

    def is_allowed_author(self, author_id):
        return str(author_id) == self.ADMIN or str(author_id) in self.ADM

    def is_duyetbox_thread(self, thread_id):
        return str(thread_id) in self.duyetbox_data

    def check_spam(self, author_id, message_object, thread_id, thread_type):
        if message_object.get('msgType') == 'chat.reaction':
            return
            
        if self.is_allowed_author(author_id) or self.is_group_admin(thread_id, author_id):
            return
        
        if not self.spam_enabled.get(thread_id, False):
            return
        
        if self.whitelist[thread_id] and str(author_id) in self.whitelist[thread_id]:
            return


        now = time.time()
        if thread_id not in self.user_message_times:
            self.user_message_times[thread_id] = {}
        if author_id not in self.user_message_times[thread_id]:
            self.user_message_times[thread_id][author_id] = []
        
        user_messages = self.user_message_times[thread_id][author_id]
        user_messages.append(now)
        user_messages = [timestamp for timestamp in user_messages if now - timestamp <= self.spam_window]
        self.user_message_times[thread_id][author_id] = user_messages

        if len(user_messages) == self.spam_threshold:
            self.handle_spam_warn(author_id, message_object, thread_id, thread_type)

        elif len(user_messages) >= self.kick_threshold:
            self.handle_spam_violation(author_id, message_object, thread_id, thread_type)
            del self.user_message_times[thread_id][author_id]

    def check_banned_words(self, message, message_object, thread_id, thread_type, author_id):
        if self.is_allowed_author(author_id) or self.is_group_admin(thread_id, author_id):
            return

        if thread_id in self.whitelist and str(author_id) in self.whitelist[thread_id]:
            return
        if not self.loctk_enabled.get(thread_id, False):
            return

        normalized_message = unicodedata.normalize('NFKC', message).lower()
        
        found_banned_word = None
        for word in self.banned_words:
            normalized_word = unicodedata.normalize('NFKC', word).lower()
            if re.search(r'\b' + re.escape(normalized_word) + r'\b', normalized_message):
                found_banned_word = word
                break

        if found_banned_word:
            self.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
            self.record_banned_word_violation(author_id, thread_id, message_object, found_banned_word, message)
            return

    def handle_spam_warn(self, user_id, message_object, thread_id, thread_type):
        if message_object.get('msgType') == 'chat.reaction':
            return
            
        if self.is_allowed_author(user_id) or self.is_group_admin(thread_id, user_id):
            return

        user_info = self.fetchUserInfo(user_id)
        if user_info and getattr(user_info, "changed_profiles", None):
            fetched_name = user_info.changed_profiles.get(user_id, {}).get('zaloName')
            display_name = fetched_name if fetched_name and fetched_name != 'không xác định' else str(user_id)
        else:
            display_name = str(user_id)

        tag = f"{display_name}"
        msg = f"➜ [ANTI-SPAM]\n{tag}\n➜ Đang gửi tin nhắn quá nhanh.\n➜ Vui lòng giảm tốc độ để tránh bị hệ thống chặn khỏi nhóm!"
        styles = MultiMsgStyle([
            MessageStyle(offset=len("➜ "), length=len("[ANTI-SPAM]"), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=len("➜ "), length=len("[ANTI-SPAM]"), style="bold", auto_format=False),
        ])
        self.replyMessage(
            Message(
                text=msg,
                mention=Mention(user_id, length=len(tag), offset=msg.find(tag)),
                style=styles
            ),
            message_object,
            thread_id,
            thread_type,
            ttl=30000
        )
        if user_id not in self.warned_users:
            self.warned_users[user_id] = {}
        self.warned_users[user_id][thread_id] = True

    def handle_spam_violation(self, user_id, message_object, thread_id, thread_type):
        if self.is_allowed_author(user_id) or self.is_group_admin(thread_id, user_id):
            return

        user_info = self.fetchUserInfo(user_id)
        display_name = str(user_id)
        if user_info and getattr(user_info, "changed_profiles", None):
            fetched_name = user_info.changed_profiles.get(user_id, {}).get('zaloName')
            if fetched_name and fetched_name != 'không xác định':
                display_name = fetched_name
        
        group_info = self.fetchGroupInfo(thread_id)
        if not group_info or thread_id not in group_info.gridInfoMap: return
        group_data = group_info.gridInfoMap[thread_id]
        creator_id = group_data.get('creatorId')
        admin_ids = group_data.get('adminIds', [])
        if str(self.uid) not in [str(admin) for admin in admin_ids] and str(self.uid) != str(creator_id): return

        if user_id in self.warned_users and thread_id in self.warned_users[user_id]:
            del self.warned_users[user_id][thread_id]

        if self.group_lock_status.get(thread_id):
            try:
                self.blockUsersInGroup(user_id, thread_id)
                self._send_kick_notification(user_id, thread_id, display_name, message_object, is_secondary_kick=True)
            except:
                pass
            return

        threading.Thread(
            target=self._lock_kick_and_unlock,
            args=(user_id, thread_id, display_name, message_object)
        ).start()

    def _send_kick_notification(self, user_id, thread_id, display_name, message_object, is_secondary_kick=False):
        tag_user = f"{display_name}"
        
        if is_secondary_kick:
            initial_text = "➜ [ANTI-SPAM]\n"
        else:
            initial_text = "➜ [ANTI-SPAM]\n➜Hệ thống phát hiện vi phạm spam trong nhóm. Tạm khóa chat để xử lý.\n"

        msg_text = f"{initial_text}{tag_user}\n➜ Đã bị chặn khỏi nhóm.\nHệ thống sẽ sớm mở lại chat."
        
        styles = MultiMsgStyle([
            MessageStyle(offset=msg_text.find("[ANTI-SPAM]"), length=len("[ANTI-SPAM]"), style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=msg_text.find("[ANTI-SPAM]"), length=len("[ANTI-SPAM]"), style="bold", auto_format=False),
        ])
        
        self.replyMessage(
            Message(
                text=msg_text,
                mention=Mention(user_id, len(tag_user), offset=msg_text.find(tag_user)),
                style=styles
            ),
            message_object,
            thread_id,
            ThreadType.GROUP,
            ttl=120000
        )

    def _lock_kick_and_unlock(self, user_id, thread_id, display_name, message_object):
        self.group_lock_status[thread_id] = True
        
        try:
            self.changeGroupSetting(thread_id, lockSendMsg=1)
            time.sleep(0) 

            self.blockUsersInGroup(user_id, thread_id)
            self._send_kick_notification(user_id, thread_id, display_name, message_object)
            
            time.sleep(5)

        except Exception as e:
            pass

        finally:
            self.changeGroupSetting(thread_id, lockSendMsg=0)
            self.sendMessage(Message(text="🔓 Chat đã được mở lại. Mọi người vui lòng tuân thủ quy định nhóm."), thread_id, ThreadType.GROUP, ttl=15000)
            if thread_id in self.group_lock_status:
                del self.group_lock_status[thread_id]
                
    def record_banned_word_violation(self, user_id, thread_id, message_object, banned_word, original_message_text):
        if self.is_allowed_author(user_id) or self.is_group_admin(thread_id, user_id):
            return

        if thread_id not in self.banned_word_violations:
            self.banned_word_violations[thread_id] = {}
        if user_id not in self.banned_word_violations[thread_id]:
            self.banned_word_violations[thread_id][user_id] = 0
        self.banned_word_violations[thread_id][user_id] += 1
        violations = self.banned_word_violations[thread_id][user_id]
        
        user_info = self.fetchUserInfo(user_id)
        if user_info and hasattr(user_info, 'changed_profiles'):
            fetched_name = user_info.changed_profiles.get(user_id, {}).get('zaloName')
            display_name = fetched_name if fetched_name and fetched_name != 'không xác định' else str(user_id)
        else:
            display_name = str(user_id)
        
        tag_user = f"{display_name}"

        if violations == 3:
            msg = f"➜ [LỌC TC]\n{tag_user}\n➜ Đã vi phạm quy định về từ ngữ thô tục ({violations}/5 lần).\n➜ Vui lòng chú ý ngôn từ của bạn. Tiếp tục vi phạm sẽ dẫn đến việc bị chặn khỏi nhóm!"
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[LỌC TC]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[LỌC TC]"), style="bold", auto_format=False),
            ])
            self.replyMessage(
                Message(text=msg, mention=Mention(user_id, len(tag_user), offset=msg.find(tag_user)), style=styles),
                message_object, thread_id, ThreadType.GROUP, ttl=120000
            )
        elif violations >= 5:
            group_info = self.fetchGroupInfo(thread_id)
            if not group_info or thread_id not in group_info.gridInfoMap:
                return
            group_data = group_info.gridInfoMap[thread_id]
            creator_id = group_data.get('creatorId')
            admin_ids = group_data.get('adminIds', [])
            
            if self.uid not in admin_ids and self.uid != creator_id:
                return

            self.blockUsersInGroup(user_id, thread_id)
            msg = f"➜ [LỌC TC] {tag_user}\n➜ Đã bị chặn khỏi nhóm do vi phạm quy định về từ ngữ thô tục quá nhiều lần ({violations}/5 lần).\n➜ Nội dung vi phạm: '{original_message_text}'"
            styles = MultiMsgStyle([
                MessageStyle(offset=len("➜ "), length=len("[LỌC TC]"), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len("➜ "), length=len("[LỌC TC]"), style="bold", auto_format=False),
            ])
            self.replyMessage(
                Message(text=msg, mention=Mention(user_id, len(tag_user), offset=msg.find(tag_user)), style=styles),
                message_object, thread_id, ThreadType.GROUP, ttl=120000
            )

    def handle_bot_invited(self, message_object, thread_id, thread_type, author_id):
            return
      
    def autoreply_onmessage(self, thread_id, message_object, author_id):
        global AUTOREPLY_ENABLED
        if not AUTOREPLY_ENABLED:
            return

        try:
            import time
            import threading
            from zlapi.models import ThreadType, Message
            import json

            # ======== Cấu hình thời gian ========
            REPLY_COOLDOWN = 3600  # 1 tiếng
            REACTION_INTERVAL = 300  # 5 phút (300s) thả reaction 1 lần
            REACTION_ICON = "⏱️"  # Biểu tượng đồng hồ đếm ngược

            # ======== Biến lưu trạng thái ========
            if not hasattr(self, "last_reply_time"):
                self.last_reply_time = {}
            if not hasattr(self, "reaction_threads"):
                self.reaction_threads = {}

            # Không phản hồi chính bot
            if author_id == self.uid:
                return

            now = time.time()
            last_time = self.last_reply_time.get(author_id, 0)

            # Nếu chưa đủ 1 tiếng (3600 giây) thì không trả lời lại
            if now - last_time < REPLY_COOLDOWN:
                return

            # Cập nhật thời gian trả lời
            self.last_reply_time[author_id] = now

            # ======== Tin nhắn trả lời ==========
            reply_text = (
"\n"
"\n"
"\n"
"\n"
"\n"

"\n"
            )

            # ======== Style chia nhiều màu ==========
            p1 = ">Nhận rải link thuê 10ka/ngày\n>Thuê nhiều chỉ còn 5k/ngày\n[Tao Mượn Văn bớt í kiến]\n"
            p2 = "🔹 Quảng cáo tự động, rải link vào các group mở chat\n🎮 Tự động tham gia nhóm\n😺 Tự động gửi kết bạn\n"
            p3 = "🛡️ Tự động rời nhóm bị key vàng tắt chat\n⚡Tự động thông báo nhóm gây phiền\n✅ Đăng nhập bằng qr tiện lợi\n- thích hợp cho thuê, sử dụng nhiều clone\n🔥 Và nhiều tính năng HOT khác!\n"
            p4 = "💰 Giá bot siêu rẻ\n⚡ 40k/Tuần\n⚡ 70K/Tháng\nDịch vụ Rải Link / QC Giá Rẻ – Rải nhanh, ổn định\n"

            style_json = json.dumps({
                "styles": [
                    {"start": 0, "len": len(p1), "st": "b,c_DB342E,f_17"},     # Đỏ
                    {"start": len(p1), "len": len(p2), "st": "b,c_F27806,f_17"},  # Cam
                    {"start": len(p1) + len(p2), "len": len(p3), "st": "b,c_F7B503,f_17"},  # Vàng
                    {"start": len(p1) + len(p2) + len(p3), "len": len(p4), "st": "b,c_4287F5,f_17"},  # Xanh
                ],
                "ver": 0
            })

            # ======== Gửi tin nhắn văn bản ==========
            self.send(
                Message(text=reply_text, style=style_json),
                thread_id=thread_id,
                thread_type=ThreadType.USER,
                ttl=360000
            )

            # ======== Gửi Business Card ==========
            CARD_UID = ""  # UID admin hoặc liên hệ
            CARD_CONTENT = "thuê Bot Thì chờ  nHoàng Khánh Prime onl nhé💗"
            user_info = self.fetchUserInfo(CARD_UID).get(CARD_UID, {})
            avatar_url = user_info.get('avatar', '')

            self.sendBusinessCard(
                userId=CARD_UID,
                qrCodeUrl=avatar_url,
                phone=CARD_CONTENT,
                thread_id=thread_id,
                thread_type=ThreadType.USER,
                ttl=360000
            )


            # ======== Bắt đầu thread thả reaction đồng hồ ========
            def countdown_react():
                start_time = time.time()
                while time.time() - start_time < REPLY_COOLDOWN:
                    try:
                        self.sendReaction(message_object, REACTION_ICON, thread_id, ThreadType.USER)
                    except Exception as e:
                        print(f"[WARN] Reaction error: {e}")
                    time.sleep(REACTION_INTERVAL)  # chờ vài phút rồi thả lại

                print(f"[INFO] Countdown reaction stopped for {author_id}")

            # Dừng luồng cũ nếu có
            if author_id in self.reaction_threads:
                try:
                    self.reaction_threads[author_id].do_run = False
                except Exception:
                    pass

            # Tạo luồng mới
            t = threading.Thread(target=countdown_react)
            t.daemon = True
            self.reaction_threads[author_id] = t
            t.start()
  
        except Exception as e:
            print(f"[ERROR] Exception in autoreply_onmessage: {e}")

    def onMessage(self, mid, author_id, message, message_object, thread_id, thread_type):
        try:
            try:
                autoreaction.check_and_react(self, message_object, thread_id, thread_type)
            except Exception as e:
                pass

            if thread_type == ThreadType.USER:
                self.autoreply_onmessage(thread_id, message_object, author_id)

            settings = read_settings()
            allowed_thread_ids = settings.get('allowed_thread_ids', [])
            admin_bot = settings.get("admin_bot", [])
            banned_users = settings.get("banned_users", [])
            chat_user = (thread_type == ThreadType.USER)
            is_main_bot = self.is_main_bot
            prefix = self.prefix
            allowed_thread_ids = get_allowed_thread_ids(self)

            if author_id in banned_users:
                return

            message_text = message.text if isinstance(message, Message) else str(message)
            message_lower = message_text.lower()
            message_text = message.text if isinstance(message, Message) else str(message)
            message_text = message.text if isinstance(message, Message) else str(message)

        #    handle_autojoin_command(self, message_object, thread_id, thread_type, author_id, message_text, mid, logging.getLogger(__name__))
        
        except Exception as e:
            print(f"[onMessage] Lỗi: {e}")

        main_executor.submit(self._process_message_async, mid, author_id, message, message_object, thread_id, thread_type)

    def _process_message_async(self, mid, author_id, message, message_object, thread_id, thread_type):
        message_text = message.text if isinstance(message, Message) else str(message)
        if message_object.get('msgType') == 'chat.undo':
            if thread_type == ThreadType.GROUP:
                if self.undo_handler.is_undo_enabled(thread_id):
                    self.undo_handler.handle_undo_event(message_object, thread_id, thread_type, author_id)
        
        mute_data = load_mute_data()
        if str(thread_id) in mute_data and str(author_id) in mute_data[str(thread_id)]:
            settings = read_settings()
            msg_id_to_delete = settings.get('bot_message_ids', {}).get(str(thread_id), message_object.msgId)

            self.deleteGroupMsg(
                msg_id_to_delete,
                author_id,
                message_object.cliMsgId,
                thread_id
            )
            return
            
        if message_object.get('msgType') == 'chat.delete':
            return
        if self.is_allowed_author(author_id):
            pass
            
        elif thread_type == ThreadType.GROUP:
            if not self.bot_status_handler.is_bot_enabled(thread_id):
                return
    
            temp_message_text = ""
            if isinstance(message, Message) and hasattr(message, 'text'):
                temp_message_text = message.text
            elif isinstance(message, str):
                temp_message_text = message

            is_bot_command = temp_message_text.lower().strip().startswith(f"{PREFIX}bot")
    
            if is_bot_command:
                self.bot_status_handler.handle_bot_command(
                    temp_message_text, message, thread_id, thread_type, author_id
                )
                return

        try:
            if message_object.get("msgType") == "chat.reaction":
                reaction_author_id = str(author_id)
                if thread_type == ThreadType.GROUP:
                    if self.bot_status_handler.is_bot_enabled(thread_id) or self.is_allowed_author(author_id):
                        self.antiricon_handler.check_spam_reaction(reaction_author_id, message_object, thread_id, thread_type)
                return
                
            message_text = message.text if isinstance(message, Message) else str(message)
            
            if message_text.lower() == f"{PREFIX}aibot on":
                if self.is_allowed_author(author_id):
                    self.replyMessage(Message(text="🚀 Đã chuyển đổi bot sang chế độ Bot AI..."), message_object, thread_id, thread_type, ttl=120000)
                    self.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
                    self.switch_to_ai_bot()
                else:
                    self.replyMessage(Message(text="⚠️ Bạn không có quyền thực hiện lệnh này."), message_object, thread_id, thread_type, ttl=120000)
                    self.sendReaction(message_object, "🤬", thread_id, thread_type, reactionType=75)
                return
            
        # --- BẮT ĐẦU ĐOẠN LOG TIN NHẮN MỚI ---
            # 1. Kiểm tra quyền (Admin hoặc Nhóm cho phép)
            # Lưu ý: Đảm bảo biến admin_bot và allowed_thread_ids đã được định nghĩa trước đó trong code của bạn
            admin_bot = [str(self.ADMIN)] + [str(uid) for uid in getattr(self, 'ADM', [])]
            allowed_thread_ids = globals().get('allowed_thread_ids', []) # Hoặc biến tương ứng của bạn
            
            # Nếu không phải admin, không trong nhóm cho phép và không phải chat riêng thì bỏ qua log
            if not (str(author_id) in admin_bot or str(thread_id) in allowed_thread_ids or thread_type == ThreadType.USER):
                pass # Vẫn xử lý lệnh nhưng không in log rác ra màn hình
            else:
                # 2. Lấy tên người dùng (Có bọc try-except để không bao giờ lỗi)
                author_name = 'Không xác định'
                try:
                    info = self.fetchUserInfo(author_id).changed_profiles.get(author_id, {})
                    author_name = info.get('displayName') or info.get('zaloName') or 'Người dùng Zalo'
                except: pass

                # 3. Lấy tên nhóm
                group_name = 'Chat Riêng'
                if thread_type == ThreadType.GROUP:
                    try:
                        g_info = self.fetchGroupInfo(thread_id)
                        group_name = g_info.gridInfoMap.get(thread_id, {}).get('name', 'Nhóm không tên')
                    except: group_name = 'Lỗi lấy tên nhóm'

                # 4. Thiết lập thời gian và màu sắc
                current_time = time.strftime("%H:%M:%S - %d/%m/%Y", time.localtime())
                # Lấy màu từ danh sách COLORS_HEX (đảm bảo file config hoặc đầu bot.py có biến này)
                if 'COLORS_HEX' in globals():
                    colors_selected = random.sample(COLORS_HEX, 8)
                else:
                    # Màu dự phòng nếu bot không có danh sách màu
                    colors_selected = ["#FFFFFF"] * 8

                # 5. In log ra console với định dạng đẹp
                print(f"{self.hex_to_ansi(colors_selected[0])}┌──────────────────────────────────────────────────┐")
                print(f"{self.hex_to_ansi(colors_selected[7])}{Style.BRIGHT}│- Thời gian: {current_time}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[5])}{Style.BRIGHT}│- Tên Nhóm: {group_name}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[4])}{Style.BRIGHT}│- ID Nhóm: {thread_id}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[3])}{Style.BRIGHT}│- Tên User: {author_name}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[2])}{Style.BRIGHT}│- ID User: {author_id}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[6])}{Style.BRIGHT}│- Loại: {thread_type}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[1])}{Style.BRIGHT}│- Nội dung: {message_text}{Style.RESET_ALL}")
                print(f"{self.hex_to_ansi(colors_selected[0])}└──────────────────────────────────────────────────┘")
            
            if message_text.strip().isdigit():
                if author_id in self.scl_user_states:
                    scl_state = self.scl_user_states[author_id]
                    if time.time() - scl_state['time_of_search'] <= scl.SEARCH_TIMEOUT:
                        scl.handle_scl_command(f"{PREFIX}scl {message_text.strip()}", message_object, thread_id, thread_type, author_id, self)
                        return
                    else:
                        del self.scl_user_states[author_id]
                        self.replyMessage(Message(text=f"➜ {author_display_name}, kết quả tìm kiếm SoundCloud đã hết hạn ({scl.SEARCH_TIMEOUT}s), vui lòng tìm lại."), message_object, thread_id, thread_type, ttl=60000)
                        return
                        
            yt_selection_pattern = re.compile(r'^\d+(\s+(audio|mp3|low|360|360p|high|1080|1080p|max))?$', re.IGNORECASE)
            
            if yt_selection_pattern.match(message_text.strip()):
                if author_id in self.yt_user_states:
                    yt_state = self.yt_user_states[author_id]
                    if time.time() - yt_state['time_of_search'] <= yt.SEARCH_TIMEOUT:
                        fake_command = f"{PREFIX}yt {message_text.strip()}"
                        yt.handle_yt_command(fake_command, message_object, thread_id, thread_type, author_id, self)
                        return
                    else:
                        del self.yt_user_states[author_id]
                        self.replyMessage(Message(text=f"➜ {author_display_name}, kết quả tìm kiếm YouTube đã hết hạn ({yt.SEARCH_TIMEOUT}s), vui lòng tìm lại."), message_object, thread_id, thread_type, ttl=60000)
                        return

            if self.undo_handler.is_undo_enabled(thread_id):
                if message_object.msgType != 'chat.undo':
                    self.undo_handler.LuuNoiDungThuHoi(message_object, message_text)
            
            if self.antilink_handler.check_and_handle_link(message_object, thread_id, thread_type, author_id):
                return

            if self.anticard_handler.check_and_delete_card(message_object, thread_id, thread_type, author_id):
                return
                
            if self.antifile_handler.check_and_delete_file(message_object, thread_id, thread_type, author_id):
                return
                         
            if self.antiphoto_handler.check_antiphoto(message_object, thread_id, thread_type, author_id):
                return
            
            if self.antivideo_handler.check_antivideo(message_object, thread_id, thread_type, author_id):
                return
                
            if self.antisticker_handler.check_and_delete_sticker(message_object, thread_id, thread_type, author_id):
                return
                
            if self.is_user_muted(thread_id, author_id):
                if not self.is_allowed_author(author_id):
                    self.check_spam(author_id, message_object, thread_id, thread_type)
                self.deleteGroupMsg(message_object.msgId, author_id, message_object.cliMsgId, thread_id)
                return
                
            self.afk_handler.check_afk_return(author_id, thread_id, thread_type, message_object)
            self.afk_handler.check_afk_mention(message_object, thread_id, thread_type)
            self.antiall_handler.check_and_ban_if_all_hidden(message_object, thread_id, author_id)

            if author_id in self.locked_users:
                return

            if message_object.msgType == 'chat.sticker':
                allowed_groups = self.load_allowed_groups()  
                if thread_type == ThreadType.GROUP and thread_id in allowed_groups:
                    sticker_id = message_object.content.id
                    sticker_catId = message_object.content.catId
                    logger.info(f"Sticker ID: {sticker_id}, Sticker CatId: {sticker_catId}")
                    sticker_info = {"id": sticker_id, "catId": sticker_catId}
                    if sticker_info not in self.sticker_data:
                        self.sticker_data.append(sticker_info)
                        self.save_sticker_data()

            command_handlers = {
                f"{PREFIX}antisp": self.antispam_handler.handle_antispam_command,
                f"{PREFIX}cam": self.loctk_handler.handle_loctk_command,
                f"{PREFIX}thread": self.bot_status_handler.handle_bot_command,
                f"{PREFIX}antiundo": self.undo_handler.handle_undo_command,
                f"{PREFIX}lbot": self.lockbot_handler.handle_lockbot_command,
                f"{PREFIX}unlbot": self.lockbot_handler.handle_unlockbot_command,
                f"{PREFIX}listlb": self.lockbot_handler.handle_listlockbot_command,
                f"{PREFIX}antifile": self.antifile_handler.handle_antifile_command,
                f"{PREFIX}antivideo": self.antivideo_handler.handle_antivideo_command,
                f"{PREFIX}antilink": self.antilink_handler.handle_antilink_command,
                f"{PREFIX}anticard": self.anticard_handler.handle_anticard_command,
                f"{PREFIX}autoapprv": self.handle_auto_approve_command,
                f"{PREFIX}game": self.game_handler.handle_game_command,
                f"{PREFIX}menuwar": self.menuwar_handler.handle_war_command,
                f"{PREFIX}autojoin": self.autojoin_handler.handle_autojoin_command,
                f"{PREFIX}whitelist": self.whitelist_handler.handle_whitelist_command,
                f"{PREFIX}bcmd": self.bcmd_handler.handle_bcmd_command,
                f"{PREFIX}unbcmd": self.bcmd_handler.handle_unbcmd_command,
                f"{PREFIX}listbcmd": self.bcmd_handler.handle_listbcmd_command,
                f"{PREFIX}antiall": self.antiall_handler.handle_antiall_command,
                f"{PREFIX}antistk": self.antisticker_handler.handle_antistk_command,
                f"{PREFIX}antiphoto": self.antiphoto_handler.handle_antiphoto_command,
                f"{PREFIX}antiricon": self.antiricon_handler.handle_antiricon_command,
                f"{PREFIX}afk": self.afk_handler.handle_afk_command,
                f"{PREFIX}luuvc": self.msvc_handler.handle_luuvc_command,
                f"{PREFIX}svc": self.msvc_handler.handle_svc_command,
                f"{PREFIX}listvoice": self.msvc_handler.handle_listvoice_command,
                f"{PREFIX}delvc": self.msvc_handler.handle_delvc_command,
                f"{PREFIX}autoreact": lambda msg, msg_obj, tid, ttype, aid: autoreaction.handle_autoreact_command(msg, msg_obj, tid, ttype, aid, self)
            }

            for prefix_cmd, handler in command_handlers.items():
                if message_text.lower().startswith(prefix_cmd):
                    handler(message_text, message_object, thread_id, thread_type, author_id)
                    return

            if message_text.isdigit() and thread_id in self.search_results and author_id in self.search_results[thread_id]:
                self.handle_download_command(message_text, message_object, thread_id, thread_type, author_id)
                return

            self.command_handler.handle_command(message_text, author_id, message_object, thread_id, thread_type)
            self.handle_auto_sticker(thread_id, thread_type, message_object)
            self.autojoin_handler.check_and_join_group(message_text, message_object, thread_id, thread_type, author_id)

        except Exception as e:
            logger.error(f"Lỗi trong onMessage: {e}")
            if message and thread_type == ThreadType.USER:
                if author_id == self.uid:
                    return
                now = time.time()
                if author_id in self.temp_thread_storage:
                    last_message_time = self.temp_thread_storage[author_id]
                    if now - last_message_time < 360000:
                        return
                self.temp_thread_storage[author_id] = now
                msg = f"➜ Chào bạn, bot hiện đang hoạt động để hỗ trợ các tính năng trong nhóm. Nếu bạn có bất kỳ thắc mắc hoặc cần hỗ trợ về bot, vui lòng liên hệ trực tiếp với admin để được giải đáp.\n\n➜ "
                self.replyMessage(Message(text=msg), message_object, thread_id, thread_type, ttl=300000)
                self.sendBusinessCard(userId=787909765578004269, qrCodeUrl=self.fetchUserInfo(self.uid).changed_profiles[self.uid]['avatarUrl'], phone="TrumCungCapFile!", thread_id=thread_id, thread_type=thread_type, ttl=300000)

        if thread_type == ThreadType.GROUP:
            self.check_banned_words(message_text, message_object, thread_id, thread_type, author_id)
            self.check_spam(author_id, message_object, thread_id, thread_type)

    def load_locked_users(self):
        try:
            with open(self.locked_users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_locked_users(self):
        with open(self.locked_users_file, 'w') as f:
            json.dump(self.locked_users, f, indent=4)

    def handle_undo_command(self, message, message_object, thread_id, thread_type, author_id):
        self.undo_handler.handle_undo_command(message, message_object, thread_id, thread_type, author_id)

    def should_kick_user(self, user_id, thread_id):
        if thread_id in self.banned_word_violations and user_id in self.banned_word_violations[thread_id]:
            return self.banned_word_violations[thread_id][user_id] >= 5
        return False

    def handle_loctk_command(self, message, message_object, thread_id, thread_type, author_id):
        if self.loctk_handler:
            self.loctk_handler.handle_loctk_command(message, message_object, thread_id, thread_type, author_id)

    def handle_antispam_command(self, message, message_object, thread_id, thread_type, author_id):
        if self.antispam_handler:
            self.antispam_handler.handle_antispam_command(message, message_object, thread_id, thread_type, author_id)

    def is_admin(self, user_id, thread_id):
        return self.is_allowed_author(user_id) or self.is_group_admin(thread_id, user_id)

    def get_current_time(self):
        return time.time()

    def cleanup_expired_search_results(self):
        while True:
            time.sleep(60)
            now = self.get_current_time()
            
            for thread_id in list(self.search_result_messages):
                for author_id in list(self.search_result_messages[thread_id]):
                    search_result_info = self.search_result_messages[thread_id][author_id]
                    elapsed_time = now - search_result_info['time']
                    if elapsed_time > self.search_result_ttl:
                        self.cleanup_search_result(thread_id, author_id)

def run_bot(client):
    try:
        logger.info("🚀 Bot đang khởi động...")
        client.listen(run_forever=True, delay=0, thread=True)
    except Exception as e:
        logger.error(f"❌ Lỗi trong listen: {e}")

def check_network():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

def watchdog(bot_thread, client, timeout=180):
    logger.info("🧠 Watchdog Bot đang chạy...")

    last_network_ok = time.time()
    network_fail = 0
    freeze_count = 0

    while True:
        try:
            now = time.time()

            # 🧠 1. Check treo thông minh
            if client.last_message_time:
                idle = now - client.last_message_time

                if idle > timeout:
                    freeze_count += 1
                    logger.warning(f"⚠️ Bot có dấu hiệu treo ({freeze_count})")

                else:
                    freeze_count = 0

                # chỉ restart khi treo nhiều lần liên tiếp
                if freeze_count >= 5:
                    restart("Bot treo nhiều lần")

            # 🧵 2. Thread chết
            if not bot_thread.is_alive():
                restart("Thread chết")

            # 🌐 3. Check mạng nâng cao
            try:
                requests.get("https://1.1.1.1", timeout=3)
                last_network_ok = now
                network_fail = 0
            except:
                network_fail += 1
                logger.warning(f"🌐 Mạng lỗi ({network_fail})")

                if network_fail >= 15 and (now - last_network_ok > 180):
                    restart("Mất mạng lâu")

        except Exception as e:
            logger.error(f"Lỗi watchdog: {e}")

        time.sleep(8)

def run_bot(client):
    try:
        logger.info("🚀 Bot đang khởi động...")
        client.listen(run_forever=True, delay=0, thread=True)
    except Exception as e:
        logger.error(f"❌ Lỗi trong listen: {e}")

def check_network():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except:
        return False

def watchdog(bot_thread, client, timeout=180):
    logger.info("🧠 Watchdog Bot đang chạy...")

    last_network_ok = time.time()
    network_fail = 0
    freeze_count = 0

    while True:
        try:
            now = time.time()

            # 🧠 1. Check treo thông minh
            if client.last_message_time:
                idle = now - client.last_message_time

                if idle > timeout:
                    freeze_count += 1
                    logger.warning(f"⚠️ Bot có dấu hiệu treo ({freeze_count})")

                else:
                    freeze_count = 0

                # chỉ restart khi treo nhiều lần liên tiếp
                if freeze_count >= 5:
                    restart("Bot treo nhiều lần")

            # 🧵 2. Thread chết
            if not bot_thread.is_alive():
                restart("Thread chết")

            # 🌐 3. Check mạng nâng cao
            try:
                requests.get("https://1.1.1.1", timeout=3)
                last_network_ok = now
                network_fail = 0
            except:
                network_fail += 1
                logger.warning(f"🌐 Mạng lỗi ({network_fail})")

                if network_fail >= 15 and (now - last_network_ok > 180):
                    restart("Mất mạng lâu")

        except Exception as e:
            logger.error(f"Lỗi watchdog: {e}")

        time.sleep(8)

def safe_listen(client):
    retry = 2

    while True:
        try:
            logger.info("🔄 Kết nối bot...")
            client.listen(run_forever=True, delay=0, thread=True)

        except Exception as e:
            logger.error(f"❌ Disconnect: {e}")

            # log chi tiết
            traceback.print_exc()

            time.sleep(retry)

            # tăng delay dần (anti spam reconnect)
            retry = min(retry * 2, 60)

def safe_listen(client):
    retry = 2
    while True:
        try:
            logger.info("🔄 Bắt đầu lắng nghe sự kiện...")
            # Cập nhật nhịp đập ngay khi bắt đầu
            client.heartbeat = time.time()
            
            # Giả sử hàm listen của bạn có cơ chế callback hoặc lặp
            # Nếu listen() là hàm chặn (block) hoàn toàn, bạn cần cập nhật heartbeat 
            # bên trong các hàm on_message hoặc on_event của client.
            client.listen(run_forever=True, delay=0, thread=True)
            
        except Exception as e:
            logger.error(f"❌ Mất kết nối (Disconnect): {e}")
            time.sleep(retry)
            retry = min(retry * 2, 60)

def watchdog(bot_thread, client, timeout=300): # Tăng timeout lên 5 phút cho thoải mái
    logger.info("🧠 Watchdog đang chạy (Chế độ Heartbeat)...")
    last_network_ok = time.time()
    network_fail = 0
    freeze_count = 0

    while True:
        try:
            now = time.time()
            
            # 1. Kiểm tra "Nhịp đập" (Heartbeat) thay vì tin nhắn
            # Lấy thời gian hoạt động cuối cùng, nếu chưa có thì lấy thời gian hiện tại
            last_alive = getattr(client, 'heartbeat', now)
            idle = now - last_alive

            if idle > timeout:
                freeze_count += 1
                logger.warning(f"⚠️ Bot không có phản hồi nhịp đập ({freeze_count}/5)")
            else:
                freeze_count = 0
            
            if freeze_count >= 5:
                restart("Bot không cập nhật heartbeat (có thể đã treo loop)")

            # 2. Kiểm tra Thread sống/chết
            if not bot_thread.is_alive():
                restart("Thread lắng nghe đã chết")

            # 3. Kiểm tra mạng
            try:
                requests.get("https://1.1.1.1", timeout=5)
                last_network_ok = now
                network_fail = 0
            except:
                network_fail += 1
                logger.warning(f"🌐 Lỗi kết nối mạng lần {network_fail}")
                if network_fail >= 10 and (now - last_network_ok > 180):
                    restart("Mất mạng quá lâu")

        except Exception as e:
            logger.error(f"Lỗi watchdog: {e}")
            
        time.sleep(15) # Nghỉ 15s mỗi lần quét để tiết kiệm CPU

last_restart_time = 0
def restart(reason="Không rõ"):
    global last_restart_time
    now = time.time()
    # Chống loop restart liên tục (ít nhất 2 phút giữa mỗi lần restart)
    if now - last_restart_time < 120: 
        logger.warning("⏳ Vừa mới restart, đang đợi ổn định...")
        return
    
    last_restart_time = now
    try:
        logger.warning(f"🚀 Đang RESTART bot ngay lập tức | Lý do: {reason}")
        # Đóng kết nối nếu cần trước khi restart
        os.execv(sys.executable, ['python'] + sys.argv)
    except Exception as e:
        logger.error(f"❌ Lỗi Restart: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Khởi tạo Client
        client = Client(API_KEY, SECRET_KEY, IMEI, SESSION_COOKIES)
        
        # QUAN TRỌNG: Khởi tạo các thuộc tính để tránh lỗi 'AttributeError'
        client.heartbeat = time.time() 
        client.last_message_time = time.time()
  
        from modules.rs import send_reset_success_message
        send_reset_success_message(client)

        # Hàm này để cập nhật nhịp đập mỗi khi có tin nhắn (để bổ trợ thêm)
        # Bạn nên chèn client.heartbeat = time.time() vào các hàm xử lý sự kiện của mình.

        bot_thread = threading.Thread(target=safe_listen, args=(client,), daemon=True)
        bot_thread.start()

        # Chạy Watchdog
        watch_thread = threading.Thread(target=watchdog, args=(bot_thread, client, 300), daemon=True)
        watch_thread.start()

        while True:
            # Cập nhật heartbeat liên tục từ luồng chính nếu bot đang chạy ổn định
            if bot_thread.is_alive():
                client.heartbeat = time.time()
            time.sleep(30)

    except Exception as e:
        logger.error(f"❌ Lỗi khởi động: {e}")
        time.sleep(5)
        restart("Lỗi khởi tạo")
