import os
import requests
import io
import tempfile
import random
import regex
from zlapi.models import Message, ThreadType, Mention, MessageStyle, MultiMsgStyle
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
# Import các biến từ config
from config import ADMIN, PREFIX, HEADER_STYLE

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

# ==============================
# HÀM HỖ TRỢ ĐỊNH DẠNG
# ==============================
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

def send_styled_reply(client, message_object, thread_id, thread_type, author_id, main_content):
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
            message_object,
            thread_id,
            thread_type,
            ttl=120000 
        )
    except Exception:
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

# ==============================
# XỬ LÝ ẢNH PIL
# ==============================
def load_image_from_url(url):
    resp = requests.get(url, timeout=10)
    return Image.open(BytesIO(resp.content)).convert("RGBA")

def get_font(size, is_emoji=False):
    font_file = EMOJI_FONT_PATH if is_emoji else FONT_PATH
    try:
        return ImageFont.truetype(font_file, size)
    except:
        return ImageFont.load_default()

def wrap_text(text, font, max_width):
    lines = []
    if not text: return lines
    for line in text.split("\n"):
        words = line.split(" ")
        current = ""
        for w in words:
            if font.getlength(current + w + " ") <= max_width:
                current += w + " "
            else:
                if current: lines.append(current.strip())
                current = w + " "
        if current: lines.append(current.strip())
    return lines

def get_random_background(width, height):
    bg_urls = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]
    try:
        url = random.choice(bg_urls)
        img = load_image_from_url(url).convert("RGBA")
        img = img.resize((width, height), Image.LANCZOS)
        return img
    except:
        return Image.new("RGBA", (width, height), (235, 240, 250))

icon_urls = [
    "https://files.catbox.moe/ijpxb5.jpg", "https://files.catbox.moe/1fd4ad.jpg",
    "https://files.catbox.moe/uy8o28.jpg", "https://files.catbox.moe/6pvn60.jpg",
    "https://files.catbox.moe/tiwpfk.jpg", "https://files.catbox.moe/e99aaq.jpg",
    "https://files.catbox.moe/br526z.jpg", "https://files.catbox.moe/pagrpt.jpg"
]

def draw_menu_image(commands_list, page=1):
    WIDTH, HEIGHT = 1080, 1440
    COLS, PADDING, HEADER_HEIGHT, FOOTER_HEIGHT = 2, 50, 220, 100
    CARD_PADDING, COL_SPACING, CARD_SPACING, ICON_SIZE = 30, 40, 30, 58
    CARD_WIDTH = (WIDTH - PADDING * 2 - COL_SPACING) // COLS

    font_header = get_font(72)
    font_cmd = get_font(30)
    font_desc = get_font(24)
    font_footer = get_font(22)

    all_card_heights = []
    for _, cmd, desc in commands_list:
        desc_lines = wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2)
        card_height = CARD_PADDING * 2 + ICON_SIZE + 10 + len(desc_lines) * 30
        all_card_heights.append(card_height)

    available_height = HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT
    temp_col_heights = [0] * COLS
    items_per_page = 0

    for h in all_card_heights:
        idx = temp_col_heights.index(min(temp_col_heights))
        if temp_col_heights[idx] + h <= available_height:
            temp_col_heights[idx] += h + CARD_SPACING
            items_per_page += 1
        else: break

    if items_per_page == 0: items_per_page = 1
    total_pages = (len(commands_list) + items_per_page - 1) // items_per_page
    start = (page - 1) * items_per_page
    end = min(len(commands_list), start + items_per_page)

    if start >= len(commands_list): return None

    bg_image = get_random_background(WIDTH, HEIGHT)
    canvas = bg_image.filter(ImageFilter.GaussianBlur(6))
    draw = ImageDraw.Draw(canvas, "RGBA")

    header_text = "MENU QUẢN LÝ ADMIN"
    hx = (WIDTH - font_header.getlength(header_text)) // 2
    draw.text((hx, 80), header_text, font=font_header, fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0, 120))

    col_heights = [HEADER_HEIGHT] * COLS
    col_cards = [[] for _ in range(COLS)]

    for i in range(start, end):
        idx = col_heights.index(min(col_heights))
        col_cards[idx].append(i)
        col_heights[idx] += all_card_heights[i] + CARD_SPACING

    for col_idx in range(COLS):
        current_y = HEADER_HEIGHT
        for card_idx in col_cards[col_idx]:
            icon, cmd, desc = commands_list[card_idx]
            card_h = all_card_heights[card_idx]
            card_x = PADDING + col_idx * (CARD_WIDTH + COL_SPACING)

            glass = bg_image.crop((card_x, current_y, card_x + CARD_WIDTH, current_y + card_h)).filter(ImageFilter.GaussianBlur(18))
            canvas.paste(glass, (card_x, current_y))
            draw.rounded_rectangle((card_x, current_y, card_x + CARD_WIDTH, current_y + card_h), radius=22, fill=(255, 255, 255, 55), outline=(255, 255, 255, 100), width=2)

            icon_url = icon_urls[card_idx % len(icon_urls)]
            try:
                icon_img = load_image_from_url(icon_url).resize((ICON_SIZE, ICON_SIZE), Image.LANCZOS)
                mask = Image.new("L", (ICON_SIZE, ICON_SIZE), 0)
                ImageDraw.Draw(mask).ellipse((0, 0, ICON_SIZE, ICON_SIZE), fill=255)
                rounded_icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0,0,0,0))
                rounded_icon.paste(icon_img, (0,0), mask)
                canvas.paste(rounded_icon, (card_x + CARD_PADDING, current_y + CARD_PADDING), rounded_icon)
            except: pass

            draw.text((card_x + CARD_PADDING + ICON_SIZE + 16, current_y + CARD_PADDING + 8), cmd, font=font_cmd, fill=(0, 110, 230))
            desc_y = current_y + CARD_PADDING + ICON_SIZE + 10
            for line in wrap_text(desc, font_desc, CARD_WIDTH - CARD_PADDING * 2):
                draw.text((card_x + CARD_PADDING, desc_y), line, font=font_desc, fill=(20, 30, 50))
                desc_y += 30
            current_y += card_h + CARD_SPACING

    footer_text = f"Trang {page}/{total_pages} • Developer Van Chien"
    fx = (WIDTH - font_footer.getlength(footer_text)) // 2
    draw.text((fx, HEIGHT - FOOTER_HEIGHT + 30), footer_text, font=font_footer, fill=(200, 210, 230), stroke_width=1, stroke_fill=(0, 0, 0, 120))

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tf:
        final = canvas.convert("RGB")
        final.save(tf.name, "JPEG", quality=95, optimize=True, subsampling=0, dpi=(150,150))
        return tf.name, final.width, final.height

class ManagerHandler:
    def __init__(self, client):
        self.client = client

    def handle_manager_command(self, message_text, message_object, thread_id, thread_type, author_id):
        # 1. KIỂM TRA QUYỀN ADMIN
        if author_id not in ADMIN:
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Bạn không có không có đủ quyền để sử dụng lệnh này\nYêu cầu quyền hạn: Quản Trị Viên Bot\n🚫🚫🚫")
            return

        # 2. KIỂM TRA PHẢI TRONG NHÓM KHÔNG
        if thread_type != ThreadType.GROUP:
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Lệnh này chỉ thực hiện được trong nhóm!\n❌❌❌")
            return

        parts = message_text.split()
        page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

        commands_list = [
            ("icon", f"{PREFIX}bot", "Quản lý trạng thái bot (on/off/list/all)."),
            ("icon", f"{PREFIX}aibot", "Chế độ AI tự động trả lời."),
            ("icon", f"{PREFIX}antisp", "Chống spam tin nhắn."),
            ("icon", f"{PREFIX}antiricon", "Chống spam reaction."),
            ("icon", f"{PREFIX}antiall", "Chống tag @all."),
            ("icon", f"{PREFIX}antilink", "Chống gửi link lạ."),
            ("icon", f"{PREFIX}antiphoto", "Chống gửi ảnh."),
            ("icon", f"{PREFIX}antivideo", "Chống gửi video."),
            ("icon", f"{PREFIX}antifile", "Chống gửi file."),
            ("icon", f"{PREFIX}antistk", "Chống gửi sticker."),
            ("icon", f"{PREFIX}cam", "Bộ lọc ngôn từ thô tục."),
            ("icon", f"{PREFIX}antiundo", "Chống thu hồi tin nhắn."),
            ("icon", f"{PREFIX}whitelist", "Danh sách miễn trừ."),
            ("icon", f"{PREFIX}autoapprv", "Tự động duyệt thành viên."),
            ("icon", f"{PREFIX}lbot", "Khoá bot chỉ cho admin."),
            ("icon", f"{PREFIX}unlbot", "Mở khoá bot."),
            ("icon", f"{PREFIX}bcmd", "Danh sách lệnh bị cấm."),
            ("icon", f"{PREFIX}svc",  "Quản lý voice.")
        ]

        output_path = None
        try:
            self.client.sendReaction(message_object, "/-ok", thread_id, thread_type, reactionType=75)
            render = draw_menu_image(commands_list, page)

            if not render:
                send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                                  f"❌ Trang {page} không có dữ liệu.")
                return

            output_path, w, h = render
            self.client.sendLocalImage(output_path, thread_id=thread_id, thread_type=thread_type, width=w, height=h, ttl=120000)
            
            # CHỈ GỬI LOGGER - ĐÃ XOÁ THÔNG BÁO TEXT TRONG CHAT
            print(f"[LOGGER] Đã gửi menu quản lý trang {page} cho ID: {author_id} thành công ✅")

        except Exception as e:
            print("Error:", e)
            send_styled_reply(self.client, message_object, thread_id, thread_type, author_id, 
                              "Đã xảy ra lỗi khi tạo menu.\n❌❌❌")
            self.client.sendReaction(message_object, "⚠️", thread_id, thread_type, reactionType=75)

        finally:
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

def PTA():
    return {"manager": ManagerHandler}