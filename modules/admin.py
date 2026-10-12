import json
import os
import time
import requests
from io import BytesIO
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config import PREFIX
from config import ADMIN
import random
FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"
CACHE_DIR = "modules/cache/admin_menu_temp"
os.makedirs(CACHE_DIR, exist_ok=True)

des = {
    'version': "1.1.5",
    'credits': "</> Hoàng Khánh Prime",
    'description': "Quản lý danh sách admin",
    'power': "Quản trị viên Bot"
}

import requests
from io import BytesIO

def load_image_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        return Image.open(BytesIO(resp.content)).convert("RGBA")
    except:
        return Image.new("RGBA", (500, 500), (30, 30, 30))


def get_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def get_emoji_font(size):
    return ImageFont.truetype(EMOJI_FONT_PATH, size)

def is_primary_admin(author_id):
    with open('seting.json', 'r') as f:
        data = json.load(f)
    return author_id == data.get('admin')

def is_secondary_admin(author_id):
    with open('seting.json', 'r') as f:
        data = json.load(f)
    return author_id in data.get('adm', [])

def is_admin(author_id):
    return is_primary_admin(author_id) or is_secondary_admin(author_id)

def fetch_avatar(url, size):
    try:
        if url:
            response = requests.get(url, timeout=3)
            img = Image.open(BytesIO(response.content)).convert("RGBA").resize((size, size))
        else:
            raise Exception("No avatar url")
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img
    except Exception:
        img = Image.new("RGBA", (size, size), (180, 150, 180, 255))
        mask = Image.new('L', (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        img.putalpha(mask)
        return img

def draw_center_text(draw, text, y, font, emoji_font, img_w, color, shadow=False, x_offset=0):
    import emoji as emoji_mod
    lines = text_wrap(text, font, emoji_font, img_w - 60)
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1]
    for line in lines:
        width = 0
        for c in line:
            if emoji_mod.emoji_count(c):
                width += emoji_font.getlength(c)
            else:
                width += font.getlength(c)
        x = (img_w - width) // 2 + x_offset
        cur_x = x
        for c in line:
            if emoji_mod.emoji_count(c):
                if shadow:
                    draw.text((cur_x+2, y+2), c, font=emoji_font, fill=(0,0,0,180))
                draw.text((cur_x, y), c, font=emoji_font, fill=color)
                cur_x += emoji_font.getlength(c)
            else:
                if shadow:
                    draw.text((cur_x+2, y+2), c, font=font, fill=(0,0,0,180))
                draw.text((cur_x, y), c, font=font, fill=color)
                cur_x += font.getlength(c)
        y += line_height + 6

def text_wrap(text, font, emoji_font, max_width):
    import emoji as emoji_mod
    lines = []
    line = ""
    for word in text.split():
        test_line = f"{line} {word}".strip()
        w = sum(emoji_font.getlength(ch) if emoji_mod.emoji_count(ch) else font.getlength(ch) for ch in test_line)
        if w > max_width and line:
            lines.append(line)
            line = word
        else:
            line = test_line
    if line:
        lines.append(line)
    return lines

def draw_card_box(draw, x, y, w, h, radius, fill, outline, outline_width):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=radius, fill=fill, outline=outline, width=outline_width)

def calc_card_height(lines, font, emoji_font, w):
    title_h = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 32
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 6
    content_h = 0
    for line in lines:
        wrapped = text_wrap(line, font, emoji_font, w - 38)
        content_h += len(wrapped) * line_height
    y_bot = 28
    return title_h + content_h + y_bot

def draw_menu_card(draw, x, y, w, title, lines, font, emoji_font, color):
    import emoji as emoji_mod
    title = title.strip()
    if title and (emoji_mod.emoji_count(title[0]) or ord(title[0]) > 10000):
        emoji_part = title[0]
        text_part = title[1:].strip()
    else:
        emoji_part = ""
        text_part = title

    card_h = calc_card_height(lines, font, emoji_font, w)
    draw_card_box(draw, x, y, w, card_h, 22, (60,70,120,230), color, 4)
    ty = y+18
    if emoji_part:
        draw.text((x+24, ty), emoji_part, font=emoji_font, fill=(255,230,120))
        draw.text((x+74, ty+5), text_part, font=font, fill=(255,240,180))
    else:
        draw.text((x+24, ty+5), text_part, font=font, fill=(255,240,180))
    content_x = x+38
    y_text = y + font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 42
    line_height = font.getbbox("Ay")[3] - font.getbbox("Ay")[1] + 6
    for line in lines:
        line_lines = text_wrap(line, font, emoji_font, w-38)
        for l in line_lines:
            cur_x = content_x
            for ch in l:
                if emoji_mod.emoji_count(ch):
                    draw.text((cur_x, y_text), ch, font=emoji_font, fill=(210,255,255))
                    cur_x += emoji_font.getlength(ch)
                else:
                    draw.text((cur_x, y_text), ch, font=font, fill=(210,255,255))
                    cur_x += font.getlength(ch)
            y_text += line_height
    draw.line((x+22, y+card_h-17, x+w-22, y+card_h-17), fill=(130,210,255), width=2)
    return card_h

def draw_admin_list_image(client):
    with open('seting.json', 'r') as f:
        data = json.load(f)
    qtv_bot = data.get('admin')
    qtv_c2 = data.get('adm', [])

    admin_users = []
    if qtv_bot:
        try:
            user_info = client.fetchUserInfo(qtv_bot)
            author_info = user_info.changed_profiles.get(qtv_bot, {}) if user_info and user_info.changed_profiles else {}
            name = author_info.get('zaloName', 'Không xác định')
            avatar = author_info.get('avatar', None)
        except Exception:
            name = "Không xác định"
            avatar = None
        admin_users.append(("👑 ĐẠI CA BOT", name, avatar, qtv_bot, "main"))

    for idx, uid in enumerate(qtv_c2, 1):
        try:
            user_info = client.fetchUserInfo(uid)
            author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
            name = author_info.get('zaloName', 'Không xác định')
            avatar = author_info.get('avatar', None)
        except Exception:
            name = "Không xác định"
            avatar = None
        admin_users.append((f"🛡️ ADMIN {idx}", name, avatar, uid, "sub"))

    row_h = 120
    box_w = 960
    margin_top = 90
    margin_left = 80
    extra = 150 if len(admin_users) else 230
    image_width = 1150
    image_height = margin_top + row_h * max(1, len(admin_users)) + extra
    bg = Image.new("RGBA", (image_width, image_height), (38, 30, 75, 255))
    draw = ImageDraw.Draw(bg)
    font = get_font(28)
    emoji_font = get_emoji_font(38)
    id_font = get_font(22)
    draw_center_text(draw, "🌈💠 DANH SÁCH ADMIN BOT 💠🌈", 32, get_font(38), emoji_font, image_width, (255,225,255), True, x_offset=0)
    if not admin_users:
        draw_center_text(draw, "Chưa có admin nào cả!", 200, font, emoji_font, image_width, (255,180,180), True)
    for i, (role, name, avatar_url, uid, typ) in enumerate(admin_users):
        y = margin_top + i * row_h
        av = fetch_avatar(avatar_url, 80)
        bg.alpha_composite(av, (margin_left, y + (row_h - 80)//2))
        if typ == "main":
            draw.ellipse([margin_left-5, y + (row_h-80)//2 - 5, margin_left + 80 + 5, y + (row_h-80)//2 + 80 + 5], outline=(250,220,90), width=4)
        import emoji as emoji_mod
        role_x = margin_left + 100
        role_y = y + 14
        if role and (emoji_mod.emoji_count(role[0]) or ord(role[0]) > 10000):
            draw.text((role_x, role_y), role[0], font=emoji_font, fill=(240,245,180))
            draw.text((role_x + 48, role_y + 5), role[1:], font=font, fill=(240,245,180))
        else:
            draw.text((role_x, role_y + 5), role, font=font, fill=(240,245,180))
        name_show = name if len(name) <= 18 else name[:17] + "…"
        name_y = role_y + 43
        draw.text((role_x, name_y), f"Tên: {name_show}", font=font, fill=(200,255,255))
        id_y = name_y + 34
        draw.text((role_x, id_y), f"ID: {uid}", font=id_font, fill=(180,220,255))
        divider_y = y + row_h - 2
        draw.line((margin_left+2, divider_y, margin_left+box_w-2, divider_y), fill=(159,108,255), width=2)
    draw_center_text(draw, "🛡️ Muốn vào admin? Đại ca chỉ định mới được nha! 🛡️", image_height-52, get_font(27), emoji_font, image_width, (255,210,255), True, x_offset=0)
    outname = os.path.join(CACHE_DIR, f"admin_list_{os.getpid()}_{int(time.time())}_{len(admin_users)}.jpg")
    bg = bg.convert("RGB")
    bg.save(outname, "JPEG", quality=100, optimize=True)
    return outname, image_width, image_height

def search_admin_commands(search_term):
    """Tìm kiếm subcommand admin dựa trên chuỗi nhập vào."""
    search_term = search_term.lower()
    commands = [
        ('add', f'📋 {PREFIX}admin add @user • Thêm {PREFIX}admin phụ'),
        ('remove', f'❌ {PREFIX}admin remove @user • Xóa {PREFIX}admin phụ'),
        ('list', f'✅ {PREFIX}admin list • Xem danh sách {PREFIX}admin bot'),
        ('reset', f'🧹 {PREFIX}admin reset • Reset toàn bộ danh sách {PREFIX}admin phụ')
    ]
    matched_commands = []
    for cmd, desc in commands:
        if search_term in cmd.lower():
            matched_commands.append((cmd, desc))
    return matched_commands

def show_menu_image(matched_commands=None):
    image_width, image_height = 1100, 850
    margin_x = 55

    # =============================
    # BACKGROUND (ảnh + blur nhẹ)
    # =============================
    BG_URLS = [
        "https://files.catbox.moe/y5fg9j.jpg",
        "https://files.catbox.moe/t31gfd.jpg",
        "https://files.catbox.moe/77c4by.jpg",
        "https://files.catbox.moe/d7p28q.jpg"
    ]

    bg = load_image_from_url(random.choice(BG_URLS)).convert("RGBA")
    bg = bg.resize((image_width, image_height), Image.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(6))  # blur nhẹ như menu.py
    draw = ImageDraw.Draw(bg)

    # =============================
    # HEADER (glass + text)
    # =============================
    draw.rounded_rectangle(
        [margin_x, 22, image_width - margin_x, 100],
        radius=30,
        fill=(28, 34, 48, 150),          # kính mờ
        outline=(180, 220, 255, 160),
        width=3
    )

    header_text = "🛡️ QUẢN LÝ ADMIN BOT 🛡️"
    draw_center_text(
        draw, header_text, 40,
        get_font(36), get_emoji_font(28),
        image_width, (255, 255, 255), True, x_offset=20
    )

    # =============================
    # DỮ LIỆU HIỂN THỊ
    # =============================
    font = get_font(25)
    emoji_font = get_emoji_font(28)

    if matched_commands is None:
        user_lines = [
            f"📋 {PREFIX}admin list • Xem danh sách admin bot",
            f"✅ {PREFIX}admin add @user • Thêm admin phụ",
            f"❌ {PREFIX}admin remove @user • Xóa admin phụ",
            f"🧹 {PREFIX}admin reset • Reset toàn bộ admin phụ"
        ]
    else:
        user_lines = [desc for _, desc in matched_commands]

    rule_lines = [
        "👑 Chỉ Đại ca (admin chính) mới thêm/xóa/reset admin phụ.",
        "⚠️ Tag đúng @user khi thao tác!",
        "🔐 Admin phụ không thể xóa admin chính."
    ]

    sys_lines = [
        f"🌐 Phiên bản: {des['version']}",
        f"👤 Tác giả: {des['credits']}",
        f"🔑 Quyền: {des['power']}"
    ]

    # =============================
    # RENDER CÁC CARD
    # =============================
    y = 120
    card_w = image_width - 2 * margin_x - 6

    # Áp dụng glass-card style giống menu.py
    def glass_card(y_pos, title, lines, color):
        card_h = draw_menu_card(
            draw,                 # sử dụng hàm có sẵn của bạn
            margin_x + 3,
            y_pos,
            card_w,
            title,
            lines,
            font,
            emoji_font,
            color
        )
        return card_h

    # CARD 1
    y += glass_card(y, "💠 CÁC LỆNH QUẢN LÝ", user_lines, (159,108,255)) + 10

    # CARD 2
    y += glass_card(y, "📜 LƯU Ý / QUY TẮC", rule_lines, (255,195,85)) + 10

    # CARD 3
    y += glass_card(y, "🔎 THÔNG TIN", sys_lines, (80,210,255))

    # =============================
    # FOOTER
    # =============================
    footer_text = (
        f"🌈 Xem danh sách admin bằng ảnh: {PREFIX}admin list\n⚡ Menu: {PREFIX}admin help"
        if matched_commands is None else
        f"⚡ Menu: {PREFIX}admin help"
    )
    draw_center_text(
        draw,
        footer_text,
        image_height - 48,
        font,
        emoji_font,
        image_width,
        (255, 225, 255),
        True
    )

    # =============================
    # SAVE FILE
    # =============================
    outname = os.path.join(
        CACHE_DIR,
        f"admin_menu_{os.getpid()}_{int(time.time())}.jpg"
    )
    bg.convert("RGB").save(outname, "JPEG", quality=100, optimize=True)

    return outname

def add_admin(uids, client):
    with open('seting.json', 'r') as f:
        data = json.load(f)
    added_users = []
    for idx, uid in enumerate(uids, 1):
        if uid not in data.get('adm', []):
            data.setdefault('adm', []).append(uid)
            try:
                user_info = client.fetchUserInfo(uid)
                author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
                name = author_info.get('zaloName', 'Không xác định')
                added_users.append(f"✅ {idx}. {name} (ID: {uid})")
            except (AttributeError, Exception):
                added_users.append(f"⚠️ {idx}. UID {uid} (Lỗi: Không lấy được thông tin)")
    with open('seting.json', 'w') as f:
        json.dump(data, f, indent=4)
    if added_users:
        return (
            "🎯 ĐÃ THÊM ADMIN 🎯\n"
            "━━━━━━━━━━━━━━━\n"
            + "\n".join(added_users) +
            "\n━━━━━━━━━━━━━━━"
        )
    else:
        return (
            "⚠️ Không có admin mới nào được thêm.\n"
            "Hãy kiểm tra lại danh sách @user hoặc thử lại!"
        )

def remove_admin(uids, client):
    with open('seting.json', 'r') as f:
        data = json.load(f)
    removed_users = []
    for idx, uid in enumerate(uids, 1):
        if uid in data.get('adm', []):
            data.get('adm', []).remove(uid)
            try:
                user_info = client.fetchUserInfo(uid)
                author_info = user_info.changed_profiles.get(uid, {}) if user_info and user_info.changed_profiles else {}
                name = author_info.get('zaloName', 'Không xác định')
                removed_users.append(f"❌ {idx}. {name} (ID: {uid})")
            except (AttributeError, Exception):
                removed_users.append(f"⚠️ {idx}. UID {uid} (Lỗi: Không lấy được thông tin)")
    with open('seting.json', 'w') as f:
        json.dump(data, f, indent=4)
    if removed_users:
        return (
            "🧹 ĐÃ XÓA ADMIN 🧹\n"
            "━━━━━━━━━━━━━━━\n"
            + "\n".join(removed_users) +
            "\n━━━━━━━━━━━━━━━"
        )
    else:
        return (
            "⚠️ Không có admin nào bị xóa.\n"
            "Hãy kiểm tra lại danh sách @user hoặc thử lại!"
        )

def handle_admin_command(message, message_object, thread_id, thread_type, author_id, client):
    if not is_admin(author_id):
        response_message = (
            "🚫 Đại ca ơi, chỉ Đại ca mới dùng được lệnh này 😤\n"
            "Hãy liên hệ Đại Ca để được cấp quyền!"
        )
        message_to_send = Message(text=response_message)
        client.replyMessage(message_to_send, message_object, thread_id, thread_type, ttl=60000)
        return

    try:
        if hasattr(message_object, 'text') and isinstance(message_object.text, str):
            message_text = message_object.text
        else:
            message_text = str(message) if message else ""
    except Exception as e:
        print(f"Error extracting message text: {e}")
        response_message = (
            "⚠️ Lỗi khi xử lý lệnh! 😓\n"
            "Hãy thử lại hoặc kiểm tra cú pháp."
        )
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        return

    text = message_text.split()
    if len(text) < 2 or text[1].lower() in ["help", "menu"]:
        img_path = show_menu_image()
        with Image.open(img_path) as img:
            width, height = img.size
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=120000
        )
        if os.path.exists(img_path):
            os.remove(img_path)
        return

    subcommand = text[1].lower()
    if subcommand == "add" and message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions]
        response_message = add_admin(uids, client)
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    elif subcommand == "remove" and message_object.mentions:
        uids = [mention['uid'] for mention in message_object.mentions]
        response_message = remove_admin(uids, client)
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    elif subcommand == "list":
        img_path, width, height = draw_admin_list_image(client)
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=width,
            height=height,
            ttl=120000
        )
        if os.path.exists(img_path):
            os.remove(img_path)
    elif subcommand == "reset":
        if not is_primary_admin(author_id):
            response_message = (
                "🚫 Chỉ Đại ca) mới có thể reset danh sách admin phụ! 😤"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
            return

        with open('seting.json', 'r') as f:
            data = json.load(f)
        data['adm'] = []
        with open('seting.json', 'w') as f:
            json.dump(data, f, indent=4)

        response_message = (
            "🧹 ĐÃ RESET DANH SÁCH ADMIN 🧹\n"
            "➜   ✅ Tất cả admin phụ đã bị xóa.\n"
            "➜   Danh sách admin phụ giờ đây rỗng!"
        )
        client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
    else:
        matched_commands = search_admin_commands(subcommand)
        if not matched_commands:
            response_message = (
                f"❌ Không tìm thấy lệnh nào khớp với '{subcommand}'! 😓\n"
                f"Hãy dùng đúng cú pháp: {PREFIX}admin [add|remove|list|reset]\n"
                f"Xem hướng dẫn: {PREFIX}admin help"
            )
            client.replyMessage(Message(text=response_message), message_object, thread_id, thread_type, ttl=60000)
        else:
            img_path = show_menu_image(matched_commands)
            with Image.open(img_path) as img:
                width, height = img.size
            client.sendLocalImage(
                img_path,
                thread_id=thread_id,
                thread_type=thread_type,
                width=width,
                height=height,
                ttl=120000
            )
            if os.path.exists(img_path):
                os.remove(img_path)

def PTA():
    return {
        'admin': handle_admin_command
    }