import os
import json
import importlib
import sys
import time
import threading
import re
import random
import difflib
import traceback
from concurrent.futures import ThreadPoolExecutor
from zlapi.models import Message, MultiMsgStyle, MessageStyle, Mention, ThreadType
from logging_utils import Logging
from colorama import Fore
from config import HEADER_STYLE

sys.path.extend([
    os.path.dirname(os.path.abspath(__file__)),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules/auto'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules/noprefix')
])
logger = Logging()

CACHE_DIR = 'modules/cache'
SETTINGS_FILE = 'seting.json'
DUYETBOX_FILE = os.path.join(CACHE_DIR, 'duyetboxdata.json')
DISABLED_THREADS_FILE = os.path.join(CACHE_DIR, 'disabled_threads.json')
COOLDOWN_FILE = os.path.join(CACHE_DIR, 'cooldown_settings.json')
STW_CMDS_FILE = os.path.join(CACHE_DIR, 'list_cmd_stw.json') 
MODULES_DIR = 'modules'
NOPREFIX_MODULES_DIR = 'modules/noprefix'
AUTO_MODULES_DIR = 'modules/auto'

def load_json(file_path, default=None):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {} if file_path.endswith(".json") else []

def save_json(file_path, data):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def load_duyetbox_data():
    return load_json(DUYETBOX_FILE, [])

def load_disabled_threads():
    return load_json(DISABLED_THREADS_FILE, [])

def save_disabled_threads(disabled_threads):
    save_json(DISABLED_THREADS_FILE, disabled_threads)

def load_stw_commands():
    return load_json(STW_CMDS_FILE, {}).get('commands', [])

def save_stw_commands(commands):
    save_json(STW_CMDS_FILE, {'commands': commands})

def update_any_string(old_string, new_string):
    replaced_count = 0
    files_changed = 0
    pattern = re.compile(re.escape(old_string), re.IGNORECASE)
    for root, dirs, files in os.walk('.'):
        for filename in files:
            if filename.endswith('.py'):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    new_code, n = pattern.subn(new_string, code)
                    if n > 0:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_code)
                        replaced_count += n
                        files_changed += 1
                except Exception as e:
                    logger.error(f"Lỗi khi xử lý {file_path}: {e}")
    return replaced_count, files_changed

class ThreadSafeDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.RLock()
    def __getitem__(self, key):
        with self.lock:
            return super().__getitem__(key)
    def __setitem__(self, key, value):
        with self.lock:
            super().__setitem__(key, value)
    def get(self, key, default=None):
        with self.lock:
            return super().get(key, default)
    def update(self, *args, **kwargs):
        with self.lock:
            super().update(*args, **kwargs)
    def pop(self, key, default=None):
        with self.lock:
            return super().pop(key, default)
    def __contains__(self, item):
        with self.lock:
            return super().__contains__(item)
    def keys(self):
        with self.lock:
            return list(super().keys())
    def values(self):
        with self.lock:
            return list(super().values())
    def items(self):
        with self.lock:
            return list(super().items())

executor = ThreadPoolExecutor(max_workers=10)

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
        """Thả N reaction đồng hồ cùng lúc."""
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
        """Thu hồi bớt 1 reaction."""
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
        """Flow thực thi visual cooldown (Đã xóa thả icon done)."""
        cd_key = f"{name}:{uid}:{tid}"

        with self._waiting_lock:
            if self._waiting.get(cd_key):
                return
            self._waiting[cd_key] = True

        def _run():
            try:
                secs = max(1, min(int(remain) + 1, 120))

                self._add_multi_react(mo, secs, tid, tt)

                for i in range(secs):
                    time.sleep(1)
                    remaining = secs - (i + 1)

                    self._remove_react(mo, tid, tt)

                    if remaining > 0:
                        time.sleep(0.01)  # Chống nghẽn API
                        self._add_multi_react(mo, remaining, tid, tt)

                self.mark(name, uid, tid)
                # Dòng self._add_single_react(mo, self.icon_done, tid, tt) đã được xóa bỏ
                run_handler_fn(fn, name, msg, mo, tid, tt, uid)

            except Exception:
                traceback.print_exc()
            finally:
                with self._waiting_lock:
                    self._waiting.pop(cd_key, None)

        executor.submit(_run)

class CommandHandler:
    def __init__(self, client):
        self.client = client
        self.PTA = ThreadSafeDict(self._load_modules(MODULES_DIR, 'PTA', ['version', 'credits', 'description', 'power']))
        self.noprefix_PTA = ThreadSafeDict(self._load_modules(NOPREFIX_MODULES_DIR, 'PTA', ['version', 'credits', 'description']))
        self.auto_PTA = ThreadSafeDict(self._load_auto_modules())
        self.disabled_threads = ThreadSafeDict({t: True for t in load_disabled_threads()})

        self._admin_id = [self.client.ADMIN] + self.client.ADM
        self.current_prefix = self.client.settings.get("prefix") or ""

        self.cooldown_settings = load_json(COOLDOWN_FILE, {})
        self.stw_commands = load_stw_commands() 
        
        # Khởi tạo VisualCooldownManager
        self.cd_manager = VisualCooldownManager(self.client)
        
        logger.prefixcmd(f"🛡 Prefix hiện tại của bot là '{self.current_prefix}'" 
                         if self.current_prefix else "❌️ Prefix hiện tại của bot là 'no prefix'")
        self._log_commands("start with", self.stw_commands) 
        self.prefix_handlers = self._create_prefix_handlers()

        self.reaction_icons = {
            'normal': ['/-flag'],
            'admin': ['/-flag'],
            'stw': ['/-flag'] 
        }

    def _create_prefix_handlers(self):
        return sorted([(self.current_prefix + command, handler)
                       for command, handler in self.PTA.items() if self.current_prefix],
                      key=lambda item: len(item[0]), reverse=True)

    def _update_prefix(self):
        new_prefix = self.client.settings.get("prefix") or ""
        if new_prefix != self.current_prefix:
            self.current_prefix = new_prefix
            logger.prefixcmd(f"🕹 Prefix đã được cập nhật thành '{self.current_prefix}'" 
                             if self.current_prefix else "🎑 Prefix đã được cập nhật thành 'no prefix'")
            self.prefix_handlers = self._create_prefix_handlers()

    def _log_commands(self, command_type, commands):
        if isinstance(commands, dict):
            if commands:
                logger.success(f"Đã load thành công các {command_type}")
            else:
                logger.success(f"Không có {command_type} nào.")
        elif isinstance(commands, list):
            if commands:
                logger.success(f"Đã load thành công các lệnh {command_type}")
            else:
                logger.success(f"Không có lệnh {command_type} nào.")

    def get_username(self, user_id):
        try:
            info = self.client.fetchUserInfo(user_id)
            if info and hasattr(info, "changed_profiles"):
                return info.changed_profiles.get(str(user_id), {}).get('zaloName', 'Không xác định')
            return "Không xác định"
        except Exception:
            return "Không xác định"

    def send_message_async(self, error_message, thread_id, thread_type, author_id):
        executor.submit(self._send_message_blocking, error_message, thread_id, thread_type, author_id)

    def reply_message_async(self, error_message, message_object, thread_id, thread_type, author_id):
        executor.submit(self._reply_message_blocking, error_message, message_object, thread_id, thread_type, author_id)

    def _send_message_blocking(self, error_message, thread_id, thread_type, author_id):
        
        if thread_type == ThreadType.USER:
            full_msg = f"{HEADER_STYLE}\n{error_message}"
            mention = None
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False) 
            ])
        else:
            name = self.get_username(author_id)
            tag_text = f"@{name}"
            full_msg = f"{tag_text}\n{HEADER_STYLE}\n{error_message}"
            mention = Mention(uid=author_id, offset=0, length=len(tag_text))
            styles = MultiMsgStyle([
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
            ])
        
        self.client.send(Message(text=full_msg, style=styles, mention=mention), thread_id, thread_type, ttl=12000)

    def _reply_message_blocking(self, error_message, message_object, thread_id, thread_type, author_id):
        
        if thread_type == ThreadType.USER:
            full_msg = f"{HEADER_STYLE}\n{error_message}"
            mention = None
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=0, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
            ])
        else:
            name = self.get_username(author_id)
            tag_text = f"@{name}"
            full_msg = f"{tag_text}\n{HEADER_STYLE}\n{error_message}"
            mention = Mention(uid=author_id, offset=0, length=len(tag_text))
            styles = MultiMsgStyle([
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="bold", auto_format=False),
                MessageStyle(offset=len(tag_text) + 1, length=len(HEADER_STYLE), style="font", size=18, auto_format=False)
            ])
        
        self.client.replyMessage(Message(text=full_msg, style=styles, mention=mention),
                                   message_object, thread_id=thread_id, thread_type=thread_type, ttl=12000)

    def _send_multiple_reactions(self, message_object, command_type, thread_id, thread_type):
        executor.submit(self._send_multiple_reactions_blocking, message_object, command_type, thread_id, thread_type)

    def _send_multiple_reactions_blocking(self, message_object, command_type, thread_id, thread_type):
        icons = random.sample(self.reaction_icons.get(command_type, ['✅']), 1)
        for icon in icons:
            try:
                self.client.sendReaction(messageObject=message_object, reactionIcon=icon,
                                         thread_id=thread_id, thread_type=thread_type)
            except Exception as e:
                logger.error(f"Lỗi khi gửi reaction '{icon}': {e}")

    def _load_modules(self, module_path, attribute_name, required_keys):
        modules, success_modules, failed_modules = {}, [], []
        for filename in os.listdir(module_path):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'{module_path.replace("/",".")}.{module_name}')
                    if (hasattr(module, attribute_name) and hasattr(module, 'des') and
                        all(key in module.des for key in required_keys)):
                        modules.update(getattr(module, attribute_name)())
                        success_modules.append(module_name)
                    else:
                        failed_modules.append(module_name)
                except Exception as e:
                    logger.error(f"Không thể load được lệnh '{module_name}' trong {module_path}: {e}")
                    failed_modules.append(module_name)
        if success_modules:
            logger.success(f"Đã load thành công {len(success_modules)} lệnh trong {module_path}")
        if failed_modules:
            logger.warning(f"Không thể load được {len(failed_modules)} lệnh trong {module_path}: {', '.join(failed_modules)}")
        return modules

    def _load_auto_modules(self):
        auto_modules, success_auto, failed_auto = {}, [], []
        for filename in os.listdir(AUTO_MODULES_DIR):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                try:
                    module = importlib.import_module(f'modules.auto.{module_name}')
                    if hasattr(module, 'start_auto'):
                        auto_modules[module_name] = module
                        success_auto.append(module_name)
                    else:
                        failed_auto.append(module_name)
                except Exception as e:
                    logger.error(f"Không thể load được lệnh auto '{module_name}': {e}")
                    failed_auto.append(module_name)
        if success_auto:
            logger.success(f"Đã load thành công {len(success_auto)} lệnh auto")
            for module in success_auto:
                executor.submit(auto_modules[module].start_auto, self.client)
        if failed_auto:
            logger.warning(f"Không thể load {len(failed_auto)} lệnh auto: {', '.join(failed_auto)}")
        return auto_modules

    def predict_command(self, wrong_command):
        if not wrong_command:
            return []
            
        possible_commands = list(self.PTA.keys())
        matches = [cmd for cmd in possible_commands if cmd.lower().startswith(wrong_command.lower())]
        return sorted(matches)[:5]

    def _get_command_role(self, cmd_name):
        try:
            if not hasattr(self, 'PTA') or not self.PTA:
                return "[Tất cả thành viên]"

            handler = self.PTA.get(cmd_name)
            if not handler:
                return "[Tất cả thành viên]"

            mod_name = getattr(handler, '__module__', None)
            if not mod_name:
                return "[Tất cả thành viên]"

            mod = sys.modules.get(mod_name)
            if not mod:
                return "[Tất cả thành viên]"
            
            des = getattr(mod, 'des', None)
            if isinstance(des, dict):
                power_val = des.get('power', 0)
                if isinstance(power_val, str):
                    p_lower = power_val.lower()
                    if any(x in p_lower for x in ["admin", "quản trị", "manager"]):
                        return "[Quản trị viên Bot]"
                    if any(x in p_lower for x in ["thành viên", "người dùng", "member", "tất cả", "all"]):
                        return "[Tất cả thành viên]"
                try:
                    if int(power_val) > 0:
                        return "[Quản trị viên Bot]"
                except (ValueError, TypeError):
                    pass 

        except Exception as e:
            if 'logger' in globals():
                logger.error(f"Lỗi check quyền lệnh '{cmd_name}': {e}", exc_info=True)
            
        return "[Tất cả thành viên]"

    def _handle_cooldown(self, message, message_object, thread_id, thread_type, author_id):
        if author_id not in self._admin_id:
            self.reply_message_async("Bạn không có quyền quản lý cooldown.",
                               message_object, thread_id, thread_type, author_id)
            return

        parts = message.split(self.current_prefix + 'cooldown', 1)
        
        # Tin nhắn hướng dẫn chi tiết
        help_message = (
            f"🛠 Hướng dẫn sử dụng lệnh Cooldown:\n"
            f"• {self.current_prefix}cooldown set <lệnh> <thời gian>: Đặt cooldown cho 1 lệnh (VD: 5s, 1m).\n"
            f"• {self.current_prefix}cooldown setall [thời gian]: Đặt cooldown cho TẤT CẢ lệnh. (Mặc định 5s nếu không ghi).\n"
            f"• {self.current_prefix}cooldown remove <lệnh>: Xóa cooldown của 1 lệnh.\n"
            f"• {self.current_prefix}cooldown remove all: Xóa toàn bộ cooldown của tất cả các lệnh.\n"
            f"• {self.current_prefix}cooldown list: Xem danh sách các lệnh đang có cooldown."
        )

        if len(parts) < 2 or not parts[1].strip():
            self.reply_message_async(help_message, message_object, thread_id, thread_type, author_id)
            return

        command_part = parts[1].strip().lower()
        args = command_part.split()
        if not args:
            self.reply_message_async(help_message, message_object, thread_id, thread_type, author_id)
            return

        action = args[0]

        # CHỨC NĂNG: SET ALL
        if action == 'setall':
            default_cd = 5.0
            if len(args) >= 2:
                try:
                    time_str = args[1]
                    if time_str.endswith('s'): default_cd = float(time_str[:-1])
                    elif time_str.endswith('m'): default_cd = float(time_str[:-1]) * 60
                    else: default_cd = float(time_str)
                except ValueError:
                    pass
            
            # Duyệt qua toàn bộ lệnh trong PTA và STW
            all_cmds = list(self.PTA.keys()) + self.stw_commands
            for cmd in set(all_cmds): # dùng set để tránh trùng lặp
                self.cooldown_settings[cmd] = default_cd
            
            save_json(COOLDOWN_FILE, self.cooldown_settings)
            self.reply_message_async(f"🚀 Đã đặt cooldown {default_cd}s cho TẤT CẢ các lệnh ({len(self.cooldown_settings)} lệnh).",
                                   message_object, thread_id, thread_type, author_id)
            return

        # CHỨC NĂNG: SET
        elif action == 'set':
            if len(args) < 3:
                self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}cooldown set <command> <time>",
                                   message_object, thread_id, thread_type, author_id)
                return
            command, time_str = args[1], args[2]
            is_valid_command = command in self.PTA or command in self.stw_commands
            if not is_valid_command:
                self.reply_message_async(f"Lệnh {command} không tồn tại.",
                                   message_object, thread_id, thread_type, author_id)
                return
            try:
                if time_str.endswith('s'):
                    cooldown_time = float(time_str[:-1])
                elif time_str.endswith('m'):
                    cooldown_time = float(time_str[:-1]) * 60
                else:
                    cooldown_time = float(time_str)
            except ValueError:
                self.reply_message_async("Thời gian không hợp lệ.",
                                   message_object, thread_id, thread_type, author_id)
                return
            self.cooldown_settings[command] = cooldown_time
            save_json(COOLDOWN_FILE, self.cooldown_settings)
            self.reply_message_async(f"Đã đặt cooldown {cooldown_time} giây cho lệnh {command}.",
                                   message_object, thread_id, thread_type, author_id)
        
        # CHỨC NĂNG: REMOVE
        elif action == 'remove':
            if len(args) < 2: return
            command = args[1]
            if command == 'all': 
                self.cooldown_settings = {}
                save_json(COOLDOWN_FILE, self.cooldown_settings)
                self.reply_message_async("Đã xóa toàn bộ cooldown của tất cả các lệnh.", message_object, thread_id, thread_type, author_id)
                return
            if command not in self.cooldown_settings:
                self.reply_message_async(f"Lệnh {command} không có cooldown.",
                                   message_object, thread_id, thread_type, author_id)
                return
            del self.cooldown_settings[command]
            save_json(COOLDOWN_FILE, self.cooldown_settings)
            self.reply_message_async(f"Đã xóa cooldown của lệnh {command}.",
                                   message_object, thread_id, thread_type, author_id)
        
        # CHỨC NĂNG: LIST VÀ CHIA NHỎ VĂN BẢN
        elif action == 'list':
            if self.cooldown_settings:
                def send_list_worker():
                    messages_to_send = []
                    current_msg = "📋 Danh sách lệnh có cooldown:\n"
                    
                    for command, cooldown_time in self.cooldown_settings.items():
                        line = f"⏱ {command}: {cooldown_time} giây\n"
                        # Giới hạn độ dài để tránh bị lỗi Zalo (khoảng 1800 ký tự)
                        if len(current_msg) + len(line) > 1800:
                            messages_to_send.append(current_msg.strip())
                            current_msg = "📋 Danh sách lệnh có cooldown (tiếp):\n"
                        current_msg += line
                        
                    if current_msg.strip():
                        messages_to_send.append(current_msg.strip())
                        
                    # Gửi tuần tự với khoảng nghỉ để tránh spam
                    for msg in messages_to_send:
                        self._reply_message_blocking(msg, message_object, thread_id, thread_type, author_id)
                        time.sleep(0.5)

                # Chạy luồng gửi tin nhắn chia nhỏ
                executor.submit(send_list_worker)
            else:
                self.reply_message_async("Không có lệnh nào được đặt cooldown.",
                                   message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(help_message, message_object, thread_id, thread_type, author_id)

    def _handle_credit(self, message, message_object, thread_id, thread_type, author_id):
        if author_id not in self._admin_id:
            self.reply_message_async("Bạn không có quyền sử dụng lệnh credit.",
                               message_object, thread_id, thread_type, author_id)
            return
        parts = message.split(self.current_prefix + 'credit', 1)
        if len(parts) < 2 or not parts[1].strip():
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>",
                               message_object, thread_id, thread_type, author_id)
            return
        args = parts[1].strip().split('-', 1)
        if len(args) < 2:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>",
                               message_object, thread_id, thread_type, author_id)
            return
        old_string = args[0].strip()
        new_string = args[1].strip()
        if not old_string or not new_string:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}credit <chuỗi cũ> - <chuỗi mới>",
                               message_object, thread_id, thread_type, author_id)
            return
        replaced_count, files_changed = update_any_string(old_string, new_string)
        if files_changed > 0:
            self.reply_message_async(
                f"Đã thay thế tất cả '{old_string}' thành '{new_string}' trong {files_changed} file, tổng {replaced_count} lần thay thế.",
                message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"Không tìm thấy chuỗi '{old_string}' trong mã nguồn.",
                               message_object, thread_id, thread_type, author_id)

    def _handle_stw(self, message, message_object, thread_id, thread_type, author_id):
        if author_id not in self._admin_id:
            self.reply_message_async("Bạn không có quyền quản lý lệnh startwith (stw).",
                               message_object, thread_id, thread_type, author_id)
            return
        
        parts = message.split(self.current_prefix + 'stw', 1)
        if len(parts) < 2:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}stw [add|del|list] [command]",
                               message_object, thread_id, thread_type, author_id)
            return
        command_part = parts[1].strip().lower()
        action, *target_parts = command_part.split(' ', 1)
        target = target_parts[0].strip() if target_parts else None

        if action == 'add':
            if not target:
                self.reply_message_async(f"Vui lòng cung cấp tên lệnh để thêm vào danh sách stw.",
                                   message_object, thread_id, thread_type, author_id)
                return
            if target not in self.PTA:
                self.reply_message_async(f"Lệnh '{target}' không tồn tại trong danh sách lệnh chính.",
                                   message_object, thread_id, thread_type, author_id)
                return
            if target not in self.stw_commands:
                self.stw_commands.append(target)
                save_stw_commands(self.stw_commands)
                self._log_commands("start with", self.stw_commands)
                self.reply_message_async(f"Đã thêm lệnh '{target}' vào danh sách start with.",
                                   message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async(f"Lệnh '{target}' đã có trong danh sách start with.",
                                   message_object, thread_id, thread_type, author_id)
        elif action == 'del':
            if not target:
                self.reply_message_async(f"Vui lòng cung cấp tên lệnh để xóa khỏi danh sách stw.",
                                   message_object, thread_id, thread_type, author_id)
                return
            if target in self.stw_commands:
                self.stw_commands.remove(target)
                save_stw_commands(self.stw_commands)
                self._log_commands("start with", self.stw_commands)
                self.reply_message_async(f"Đã xóa lệnh '{target}' khỏi danh sách start with.",
                                   message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async(f"Không tìm thấy lệnh '{target}' trong danh sách start with.",
                                   message_object, thread_id, thread_type, author_id)
        elif action == 'list':
            if self.stw_commands:
                self.reply_message_async(f"Các lệnh start with: {', '.join(self.stw_commands)}",
                                   message_object, thread_id, thread_type, author_id)
            else:
                self.reply_message_async("Không có lệnh start with nào.",
                                   message_object, thread_id, thread_type, author_id)
        else:
            self.reply_message_async(f"Vui lòng sử dụng: {self.current_prefix}stw [add|del|list] [command]",
                               message_object, thread_id, thread_type, author_id)

    def _get_content_message(self, message_object):
        if message_object.msgType == 'chat.sticker':
            return ""
        content = message_object.content
        if isinstance(content, dict) and 'title' in content:
            return content['title']
        elif isinstance(content, str):
            return content
        elif isinstance(content, dict) and 'href' in content:
            return content['href']
        else:
            return ""

    def _execute_command(self, command_handler, message_text, message_object, thread_id, thread_type, author_id, command_name, command_type_reaction):
        try:
            # Lấy số giây cooldown từ cài đặt
            cd_seconds = self.cooldown_settings.get(command_name, 0)
            
            # Logic kiểm tra cấu hình thả reaction từ module của lệnh
            mod_name = getattr(command_handler, '__module__', None)
            mod = sys.modules.get(mod_name)
            should_react = True # Mặc định là cho phép thả reaction
            
            if mod and hasattr(mod, 'des'):
                des_config = getattr(mod, 'des')
                if isinstance(des_config, dict):
                    should_react = des_config.get('reaction', True)

            # Hàm bọc để chạy lệnh chính
            def execute_logic(msg, mo, tid, tt, uid, cli):
                # Chỉ thả reaction /-ok khi thỏa mãn cả 2 điều kiện và lúc lệnh thực sự được chạy
                if command_type_reaction and should_react:
                    self._send_multiple_reactions(mo, command_type_reaction, tid, tt)
                # Thực thi hàm xử lý lệnh
                command_handler(msg, mo, tid, tt, uid, cli)

            # Kiểm tra thời gian hồi chiêu với VisualCooldownManager
            remain = self.cd_manager.check(command_name, author_id, thread_id, cd_seconds)
            
            if remain:
                # Trình bao bọc để chạy lệnh sau khi kết thúc đếm ngược
                def run_handler(fn, name, msg, mo, tid, tt, uid):
                    fn(msg, mo, tid, tt, uid, self.client)
                    
                # Gọi hiệu ứng chờ cooldown thả đồng hồ và sau đó chạy lệnh
                self.cd_manager.countdown_then_run(
                    remain=remain,
                    name=command_name,
                    fn=execute_logic,
                    msg=message_text,
                    mo=message_object,
                    tid=thread_id,
                    tt=thread_type,
                    uid=author_id,
                    run_handler_fn=run_handler
                )
            else:
                # Nếu không dính cooldown thì thực thi ngay và lưu lại mốc thời gian
                execute_logic(message_text, message_object, thread_id, thread_type, author_id, self.client)
                self.cd_manager.mark(command_name, author_id, thread_id)
            
        except Exception as e:
            logger.error(f"Lỗi khi thực thi lệnh '{command_name}': {e}")

    def handle_command(self, message, author_id, message_object, thread_id, thread_type):
        self._update_prefix()
        message_text = self._get_content_message(message_object)
        if not message_text:
            return

        if thread_type != ThreadType.USER:
            # Thêm \s+ và \S để bắt buộc prefix phải đứng sau khoảng trắng và trước một ký tự lệnh, tránh bắt nhầm dấu câu kết thúc.
            message_text = re.sub(rf'^@.*?\s+(?={re.escape(self.current_prefix)}\S)', '', message_text).strip()

        duyetbox_data = self.client.duyetbox_data
        admins_list = [self.client.ADMIN] + self.client.ADM
        is_admin = (author_id in admins_list)
        is_duyetbox_thread = (thread_id in duyetbox_data)

        noprefix_handler = self.noprefix_PTA.get(message_text.lower())
        if noprefix_handler:
            executor.submit(self._execute_command, noprefix_handler, message_text, message_object, thread_id, thread_type, author_id, message_text.lower(), 'normal')
            return

        if not is_duyetbox_thread and not is_admin:
            if message_text.startswith(self.current_prefix):
                return
            admin_cmd_prefixes = [self.current_prefix + cmd for cmd in ['cooldown', 'credit', 'stw']]
            if any(message_text.startswith(p) for p in admin_cmd_prefixes):
                return
            return
            
        special_admin_commands = {
            self.current_prefix + 'cooldown': self._handle_cooldown,
            self.current_prefix + 'credit': self._handle_credit,
            self.current_prefix + 'stw': self._handle_stw
        }

        for cmd_prefix_full, handler_func in special_admin_commands.items():
            if message_text.startswith(cmd_prefix_full):
                if re.match(rf"^{re.escape(cmd_prefix_full)}(\s|$)", message_text, re.IGNORECASE):
                    self._send_multiple_reactions(message_object, 'admin', thread_id, thread_type)
                    executor.submit(handler_func, message_text, message_object, thread_id, thread_type, author_id)
                    return
        
        found_cmd_name = None
        message_for_execution = message_text
        command_type_reaction = None

        if message_text.startswith(self.current_prefix):
            command_part_after_prefix = message_text[len(self.current_prefix):].strip()
            if command_part_after_prefix:
                found_cmd_name = None
                sorted_pta_cmds = sorted(self.PTA.keys(), key=len, reverse=True)
                
                for cmd_name in sorted_pta_cmds:
                    pattern = rf"^{re.escape(cmd_name)}(\s|$)"
                    if re.match(pattern, command_part_after_prefix, re.IGNORECASE):
                        found_cmd_name = cmd_name
                        break

                if found_cmd_name:
                    if self.client.bcmd_handler.is_command_blocked(found_cmd_name, author_id, thread_id):
                        self._send_multiple_reactions(message_object, 'error', thread_id, thread_type)
                        self.reply_message_async("Bạn đã bị cấm sử dụng lệnh này.", message_object, thread_id, thread_type, author_id)
                        return
                    
                    command_type_reaction = 'normal'

        if not found_cmd_name and self.stw_commands:
            sorted_valid_stw_cmds = sorted([cmd for cmd in self.stw_commands if cmd in self.PTA], key=len, reverse=True)
            if sorted_valid_stw_cmds:
                stw_command_pattern_str = '|'.join([re.escape(cmd) for cmd in sorted_valid_stw_cmds])
                if stw_command_pattern_str:
                    prefix_escaped = re.escape(self.current_prefix)
                    stw_regex = re.compile(rf"{prefix_escaped}\s*({stw_command_pattern_str})(?:\s|$)", re.IGNORECASE)
                    match = stw_regex.search(message_text)
                    if match:
                        found_cmd_name = match.group(1).lower()
                        command_type_reaction = 'stw'

        if found_cmd_name:
            if self.client.bcmd_handler.is_command_blocked(found_cmd_name, author_id, thread_id):
                self._send_multiple_reactions(message_object, 'error', thread_id, thread_type)
                self.reply_message_async("Bạn đã bị cấm sử dụng lệnh này.", message_object, thread_id, thread_type, author_id)
                return

            command_handler = self.PTA.get(found_cmd_name)
            if command_handler:
                executor.submit(self._execute_command, command_handler, message_for_execution, message_object, thread_id, thread_type, author_id, found_cmd_name, command_type_reaction)
            return

        if message_text.startswith(self.current_prefix):
            command_part_after_prefix = message_text[len(self.current_prefix):].strip()
            wrong_cmd = command_part_after_prefix.split()[0].lower() if command_part_after_prefix else ""
            
            predicted = []
            if wrong_cmd:
                search_prefix = wrong_cmd[:min(len(wrong_cmd), 4)]
                if hasattr(self, 'PTA') and isinstance(self.PTA, dict):
                    for cmd_name in self.PTA.keys():
                        if cmd_name.startswith(search_prefix) and cmd_name != wrong_cmd:
                            predicted.append(cmd_name)
                        if len(predicted) >= 5:
                            break
                            
                if not predicted:
                    close_matches = difflib.get_close_matches(wrong_cmd, self.PTA.keys(), n=5, cutoff=0.5)
                    predicted = close_matches
            
            if predicted:
                help_message = f"Không tìm thấy lệnh \"{wrong_cmd}\"\nCó phải mày muốn dùng:\n"
                for cmd in predicted:
                    role = self._get_command_role(cmd) if hasattr(self, '_get_command_role') else ""
                    help_message += f"{self.current_prefix}{cmd} {role}\n"
            else:
                help_message = (
                    f"Nếu Bạn Thắc Mắc Tôi Có Những Lệnh Gì, Hãy:..                                                                                                                      \n"
                    f"{self.current_prefix}help - Xem hướng dẫn sử dụng\n"
                    f"{self.current_prefix}game - Xem hướng dẫn chơi game\n"
                    f"{self.current_prefix}command - Xem toàn bộ danh sách lệnh có sẵn."
                )
            
            self.reply_message_async(help_message.strip(), message_object, thread_id, thread_type, author_id)
            return