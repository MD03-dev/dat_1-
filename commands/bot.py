import json
import os
import tempfile
import requests
from io import BytesIO
import concurrent.futures
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from config import PREFIX
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import logging

logger = logging.getLogger(__name__)

try:
    FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
    EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
    if not os.path.exists(FONT_PATH) or not os.path.exists(EMOJI_FONT_PATH): FONT_PATH = None
except: FONT_PATH = None

BG_COLOR = (29, 32, 41)
CARD_COLOR = (44, 48, 61)
SHADOW_COLOR = (18, 20, 26, 128)
TEXT_COLOR = (230, 235, 240)
HEADER_COLOR = (130, 230, 255)
ID_COLOR = (150, 155, 170)
ICON_COLOR = (255, 255, 255)

def get_user_name(client, uid):
    try:
        user_info = client.fetchUserInfo(uid)
        author_info = user_info.changed_profiles.get(str(uid), {}) if user_info and user_info.changed_profiles else {}
        name = author_info.get('zaloName', 'Không xác định')
        return name
    except Exception as e:
        logger.error(f"[get_user_name] Failed to fetch name for user {uid}: {e}")
        return 'Không xác định'

def create_circular_avatar(img, size):
    img = img.resize(size, Image.Resampling.LANCZOS)
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0) + size, fill=255)
    output = Image.new('RGBA', size)
    output.paste(img, (0, 0), mask)
    return output

def fetch_and_process_avatar(group_info, avatar_size):
    group_id = group_info[0]
    avatar_url = group_info[2]
    
    try:
        if avatar_url:
            response = requests.get(avatar_url, timeout=5)
            response.raise_for_status()
            img = Image.open(BytesIO(response.content)).convert("RGB")
            return group_id, create_circular_avatar(img, (avatar_size, avatar_size))
    except Exception:
        pass
    
    placeholder = Image.new('RGB', (avatar_size, avatar_size), CARD_COLOR)
    if FONT_PATH:
        try:
            placeholder_font = ImageFont.truetype(EMOJI_FONT_PATH, int(avatar_size * 0.6))
            draw = ImageDraw.Draw(placeholder)
            icon = "👥"
            bbox = draw.textbbox((0, 0), icon, font=placeholder_font)
            draw.text(
                ((avatar_size - (bbox[2]-bbox[0])) / 2, (avatar_size - (bbox[3]-bbox[1])) / 2 - 10),
                icon, font=placeholder_font, fill=ICON_COLOR
            )
        except: pass
    return group_id, create_circular_avatar(placeholder, (avatar_size, avatar_size))

def create_group_list_image(group_list_info, page=1, items_per_page=10):
    paginated_list = group_list_info[(page - 1) * items_per_page : page * items_per_page]
    total_pages = (len(group_list_info) + items_per_page - 1) // items_per_page
    if not paginated_list: return None

    try:
        if FONT_PATH:
            header_font = ImageFont.truetype(FONT_PATH, 50)
            name_font = ImageFont.truetype(FONT_PATH, 38)
            id_font = ImageFont.truetype(FONT_PATH, 28)
            footer_font = ImageFont.truetype(FONT_PATH, 28)
        else: raise IOError()
    except:
        header_font, name_font, id_font, footer_font = (ImageFont.load_default(size=s) for s in [30, 20, 16, 16])

    avatar_size = 90
    avatars = {}
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_avatar = {executor.submit(fetch_and_process_avatar, group_info, avatar_size): group_info for group_info in paginated_list}
        for future in concurrent.futures.as_completed(future_to_avatar):
            group_id, avatar_img = future.result()
            avatars[group_id] = avatar_img

    img_width = 1280
    padding = 60
    header_height = 150
    card_height = 120
    card_spacing = 20
    footer_height = 90
    content_height = len(paginated_list) * (card_height + card_spacing)
    img_height = header_height + content_height + footer_height

    image = Image.new("RGB", (img_width, img_height), BG_COLOR)
    draw = ImageDraw.Draw(image, "RGBA")

    header_text = "BOT ĐANG HOẠT ĐỘNG TRONG CÁC NHÓM"
    bbox = draw.textbbox((0,0), header_text, font=header_font)
    draw.text(((img_width - (bbox[2]-bbox[0])) / 2, padding), header_text, font=header_font, fill=HEADER_COLOR)

    current_y = header_height
    for i, (group_id, group_name, avatar_url) in enumerate(paginated_list):
        draw.rounded_rectangle(
            (padding + 5, current_y + 5, img_width - padding + 5, current_y + card_height + 5),
            radius=20, honey=SHADOW_COLOR
        )
        draw.rounded_rectangle(
            (padding, current_y, img_width - padding, current_y + card_height),
            radius=20, fill=CARD_COLOR
        )
        
        avatar_img = avatars.get(group_id)
        if avatar_img:
            y_avatar = current_y + (card_height - avatar_size) // 2
            image.paste(avatar_img, (padding + 20, y_avatar), avatar_img)

        text_x = padding + avatar_size + 45
        max_name_width = img_width - text_x - padding - 20
        if draw.textlength(group_name, font=name_font) > max_name_width:
            while draw.textlength(group_name + "...", font=name_font) > max_name_width and len(group_name) > 0:
                group_name = group_name[:-1]
            group_name += "..."
        draw.text((text_x, current_y + 25), group_name, font=name_font, fill=TEXT_COLOR)
        draw.text((text_x, current_y + 75), f"ID: {group_id}", font=id_font, fill=ID_COLOR)
        
        current_y += card_height + card_spacing
        
    footer_text = f"Trang {page}/{total_pages}  •  Tổng cộng: {len(group_list_info)} nhóm"
    bbox = draw.textbbox((0,0), footer_text, font=footer_font)
    draw.text(((img_width - (bbox[2]-bbox[0])) / 2, img_height - footer_height + 30), footer_text, font=footer_font, fill=HEADER_COLOR)
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        image.save(tf.name, "JPEG", quality=95, optimize=True)
        return tf.name, image.width, image.height


class BotStatusHandler:
    def __init__(self, client):
        self.client = client
        self.settings_file = "data/bot_status.json"
        self.bot_enabled_groups = self.load_settings()

    def load_settings(self):
        if not os.path.exists("data"): os.makedirs("data")
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (FileNotFoundError, json.JSONDecodeError): return []

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            json.dump(self.bot_enabled_groups, f, indent=4)

    def is_bot_enabled(self, thread_id):
        return str(thread_id) in self.bot_enabled_groups

    def handle_bot_command(self, message_text, message_object, thread_id, thread_type, author_id):
        name = get_user_name(self.client, author_id)

        if str(author_id) not in self.client.ADMIN:
            rest_text = "⚠️ Chỉ chủ nhân của bot mới có quyền sử dụng lệnh này."
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "🔐", thread_id, thread_type, reactionType=75)
            return

        parts = message_text.lower().split()
        
        if len(parts) < 2 or parts[1] not in ["on", "off", "list"]:
            current_status = "Bật ✅" if self.is_bot_enabled(thread_id) else "Tắt ❌"
            rest_text = f"Hướng dẫn: {PREFIX}bot <on/off/list/on all/off all>\nTình trạng bot trong nhóm này: {current_status}"
            msg = f"{name}\n➜{rest_text}"
            styles = MultiMsgStyle([
                MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
            ])
            self.client.replyMessage(
                Message(text=msg, style=styles),
                message_object, thread_id, thread_type, ttl=60000
            )
            self.client.sendReaction(message_object, "👉", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "📜", thread_id, thread_type, reactionType=75)
            self.client.sendReaction(message_object, "ℹ️", thread_id, thread_type, reactionType=75)
            return

        action = parts[1]
        
        if action == 'list':
            page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            if not self.bot_enabled_groups:
                rest_text = "Hiện không có nhóm nào đang bật bot."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            self.client.replyMessage(
                Message(text="➜ Đang lấy thông tin và tạo danh sách, việc này có thể mất một lúc..."),
                message_object, thread_id, thread_type, ttl=15000
            )
            
            group_list_info = []
            for group_id in self.bot_enabled_groups:
                try:
                    info = self.client.fetchGroupInfo(group_id).gridInfoMap.get(group_id, {})
                    name = info.get('name', f"Nhóm không tên ({group_id})")
                    url = info.get('fullAvt') or info.get('avatar')
                    group_list_info.append((group_id, name, url))
                except Exception:
                    group_list_info.append((group_id, f"Lỗi khi lấy tên nhóm ({group_id})", None))
            
            group_list_info.sort(key=lambda x: x[1].lower())
            output_path = None
            try:
                image_result = create_group_list_image(group_list_info, page)
                if image_result:
                    output_path, width, height = image_result
                    self.client.sendLocalImage(
                        output_path, thread_id=thread_id, thread_type=thread_type, width=width, height=height, ttl=120000
                    )
                else:
                    rest_text = f"❌ Không có dữ liệu ở trang {page}."
                    msg = f"{name}\n➜{rest_text}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=60000
                    )
                    self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
            finally:
                if output_path and os.path.exists(output_path):
                    os.remove(output_path)
            return

        is_all_command = len(parts) > 2 and parts[2] == 'all'
        
        if is_all_command:
            if action == 'on':
                try:
                    all_group_ids = self.client.fetchAllGroups().gridVerMap.keys()
                    group_ids_str = [str(gid) for gid in all_group_ids]
                    enabled_set = set(self.bot_enabled_groups)
                    enabled_set.update(group_ids_str)
                    self.bot_enabled_groups = list(enabled_set)
                    self.save_settings()
                    rest_text = f"✅ Đã bật bot trong {len(group_ids_str)} nhóm."
                    msg = f"{name}\n➜{rest_text}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=60000
                    )
                    self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "🌐", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
                except Exception as e:
                    rest_text = f"❌ Đã xảy ra lỗi khi lấy danh sách nhóm: {e}"
                    msg = f"{name}\n➜{rest_text}"
                    styles = MultiMsgStyle([
                        MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                        MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                    ])
                    self.client.replyMessage(
                        Message(text=msg, style=styles),
                        message_object, thread_id, thread_type, ttl=60000
                    )
                    self.client.sendReaction(message_object, "❌", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                    self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)
                return

            elif action == 'off':
                self.bot_enabled_groups = []
                self.save_settings()
                rest_text = "🚫 Đã tắt bot trong tất cả các nhóm."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🌐", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
                return

        thread_id_str = str(thread_id)
        if action == "on":
            if self.is_bot_enabled(thread_id_str):
                rest_text = "✅ Bot đã được bật trong nhóm này rồi."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
            else:
                self.bot_enabled_groups.append(thread_id_str)
                self.save_settings()
                rest_text = "✅ Bot đã được bật trong nhóm này."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "✅", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🛡️", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
        
        elif action == "off":
            if not self.is_bot_enabled(thread_id_str):
                rest_text = "🚫 Bot đã được tắt trong nhóm này rồi."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🔄", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
            else:
                self.bot_enabled_groups.remove(thread_id_str)
                self.save_settings()
                rest_text = "🚫 Bot đã được tắt trong nhóm này."
                msg = f"{name}\n➜{rest_text}"
                styles = MultiMsgStyle([
                    MessageStyle(offset=0, length=len(name), style="color", color="#db342e", auto_format=False),
                    MessageStyle(offset=0, length=len(name), style="bold", auto_format=False),
                ])
                self.client.replyMessage(
                    Message(text=msg, style=styles),
                    message_object, thread_id, thread_type, ttl=60000
                )
                self.client.sendReaction(message_object, "🚫", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🤖", thread_id, thread_type, reactionType=75)
                self.client.sendReaction(message_object, "🔓", thread_id, thread_type, reactionType=75)