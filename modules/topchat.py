# -*- coding: utf-8 -*-
import os, json, time, threading, io, requests
from zlapi.models import Message
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ================= CẤU HÌNH =================
DATA_FILE = "modules/data/topchat/topchat.json"
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
LOCK = threading.Lock()

FONT_PATH = "modules/cache/font/BeVietnamPro-Bold.ttf"
EMOJI_FONT_PATH = "modules/cache/font/NotoEmoji-Bold.ttf"

BG_TOP = (25, 30, 55)
BG_BOTTOM = (10, 15, 25)
CARD_COLOR = (25, 30, 50)
TEXT_COLOR = (255, 255, 255)

# ================= DỮ LIỆU =================
def load_data():
    """Đọc dữ liệu topchat, không reset."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}

def save_data(data):
    """Lưu dữ liệu an toàn, không ghi đè trống."""
    if not data:
        return  # Không ghi đè nếu rỗng (bảo toàn BXH)
    with LOCK:
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Không thể lưu TopChat: {e}")

# ================= AVATAR =================
def fetch_avatar_image(client, uid, size=55):
    try:
        info = client.fetchUserInfo(uid)
        avatar_url = None
        if info and getattr(info, "changed_profiles", None):
            profile = info.changed_profiles.get(uid, {})
            avatar_url = profile.get("avatar")
        if not avatar_url:
            avatar_url = getattr(info, "avatar", None)
        if avatar_url:
            r = requests.get(avatar_url, timeout=5)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGBA")
                img = img.resize((size, size))
                mask = Image.new("L", (size, size), 0)
                d = ImageDraw.Draw(mask)
                d.ellipse((0, 0, size, size), fill=255)
                img.putalpha(mask)
                return img
    except Exception:
        pass
    img = Image.new("RGBA", (size, size), (90, 90, 90, 255))
    d = ImageDraw.Draw(img)
    d.text((size//4, size//3), "👤", fill=(255, 255, 255))
    return img

# ================= RANK ICON =================
def get_rank_label(count):
    if count >= 1000:
        return ("SSS", "🏆", (255, 215, 0))
    elif count >= 700:
        return ("SS", "💎", (255, 165, 0))
    elif count >= 400:
        return ("S", "⭐", (0, 255, 255))
    elif count >= 200:
        return ("A", "⚡", (0, 200, 255))
    elif count >= 100:
        return ("B", "💬", (150, 200, 255))
    else:
        return ("C", "🌱", (180, 180, 200))

# ================= VẼ ẢNH =================
def draw_topchat_image(client, data, tid, top_n=5):
    if tid not in data or not data[tid]:
        return None

    try:
        group_info = client.fetchGroupInfo(tid)
        group_name = getattr(group_info, "name", "Nhóm chat")
    except:
        group_name = "Nhóm chat"

    sorted_users = sorted(data[tid].items(), key=lambda x: x[1]["count"], reverse=True)[:top_n]
    if not sorted_users:
        return None

    # Tính tổng tin nhắn để tính phần trăm
    total_count = sum(info.get("count", 0) for _, info in sorted_users)
    max_count = sorted_users[0][1].get("count", 1) if sorted_users else 1

    width = 750
    card_height = 95
    header_height = 140
    footer_height = 50
    spacing = 15
    height = header_height + (top_n * (card_height + spacing)) + footer_height
    
    # Tạo nền gradient hiện đại
    bg = Image.new("RGB", (width, height), (20, 25, 45))
    draw = ImageDraw.Draw(bg)
    
    # Gradient nền đẹp hơn
    for y_pos in range(height):
        blend = y_pos / height
        r = int(20 * (1 - blend) + 15 * blend)
        g = int(25 * (1 - blend) + 20 * blend)
        b = int(45 * (1 - blend) + 30 * blend)
        draw.line([(0, y_pos), (width, y_pos)], fill=(r, g, b))

    # Font setup
    font_title = ImageFont.truetype(FONT_PATH, 36)
    emoji_font = ImageFont.truetype(EMOJI_FONT_PATH, 36)
    font_name = ImageFont.truetype(FONT_PATH, 24)
    font_count = ImageFont.truetype(FONT_PATH, 20)
    font_small = ImageFont.truetype(FONT_PATH, 18)
    font_rank = ImageFont.truetype(FONT_PATH, 22)
    font_percent = ImageFont.truetype(FONT_PATH, 18)

    # Header với hiệu ứng đẹp
    center_x = width / 2
    title_text = "🏆 BXH TƯƠNG TÁC 🏆"
    text_bbox = draw.textbbox((0, 0), title_text, font=font_title)
    text_w = text_bbox[2] - text_bbox[0]
    
    # Vẽ shadow cho title
    for offset in [(2, 2), (1, 1)]:
        draw.text((center_x - text_w/2 + offset[0], 40 + offset[1]), title_text,
                  fill=(0, 0, 0, 150), font=font_title, anchor="lt")
    draw.text((center_x - text_w/2, 40), title_text,
              fill=(255, 215, 0), font=font_title, anchor="lt")
    
    draw.text((center_x, 90), f"💬 {group_name}",
              fill=(200, 230, 255), anchor="mm", font=font_small)

    # Danh sách top với design hiện đại
    y = header_height
    avatar_size = 70
    
    for i, (uid, info) in enumerate(sorted_users, 1):
        name = info.get("name", "Người dùng")
        count = info.get("count", 0)
        rank_label, rank_icon, color = get_rank_label(count)
        
        # Tính phần trăm
        percentage = (count / max_count * 100) if max_count > 0 else 0
        
        # Vẽ card với shadow và glow
        card_y = y
        card_w = width - 80
        card_x = 40
        
        # Shadow
        shadow_img = Image.new("RGBA", (card_w, card_height), (0, 0, 0, 60))
        bg.paste(shadow_img, (card_x + 3, card_y + 3), shadow_img)
        
        # Card background với gradient
        card = Image.new("RGBA", (card_w, card_height), (35, 40, 60, 240))
        card_draw = ImageDraw.Draw(card)
        card_draw.rounded_rectangle((0, 0, card_w, card_height), radius=20, 
                                    fill=(35, 40, 60, 240), outline=color, width=3)
        
        # Hiệu ứng glow
        glow_card = card.filter(ImageFilter.GaussianBlur(radius=8))
        bg.paste(glow_card, (card_x - 2, card_y - 2), glow_card)
        bg.paste(card, (card_x, card_y), card)
        
        # Vẽ số thứ tự
        rank_x = card_x + 20
        rank_y = card_y + card_height // 2
        medal_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
        if i <= 3:
            draw.text((rank_x - 8, rank_y), medal_icons[i], font=emoji_font, anchor="mm")
        else:
            draw.text((rank_x, rank_y - 15), f"#{i}", fill=color, font=font_rank, anchor="lt")
        
        # Avatar
        avatar = fetch_avatar_image(client, uid, size=avatar_size)
        avatar_x = card_x + 70
        avatar_y = card_y + (card_height - avatar_size) // 2
        
        # Avatar border với glow
        avatar_border = Image.new("RGBA", (avatar_size + 8, avatar_size + 8), (0, 0, 0, 0))
        avatar_border_draw = ImageDraw.Draw(avatar_border)
        avatar_border_draw.ellipse((0, 0, avatar_size + 8, avatar_size + 8), fill=color + (200,))
        bg.paste(avatar_border, (avatar_x - 4, avatar_y - 4), avatar_border)
        bg.paste(avatar, (avatar_x, avatar_y), avatar)
        
        # Tên người dùng
        name_x = avatar_x + avatar_size + 25
        name_y = card_y + 18
        name_display = name[:25] + "..." if len(name) > 25 else name
        draw.text((name_x, name_y), name_display, fill=(255, 255, 255), font=font_name)
        
        # Số tin nhắn
        count_y = name_y + 32
        draw.text((name_x, count_y), f"{count:,} tin nhắn", fill=(180, 200, 220), font=font_count)
        
        # Thanh phần trăm
        bar_x = name_x
        bar_y = count_y + 28
        bar_w = card_w - (name_x - card_x) - 30
        bar_h = 8
        bar_radius = 4
        
        # Background bar
        bar_bg = Image.new("RGBA", (int(bar_w), bar_h), (50, 50, 70, 200))
        bar_bg_draw = ImageDraw.Draw(bar_bg)
        bar_bg_draw.rounded_rectangle((0, 0, int(bar_w), bar_h), radius=bar_radius, fill=(50, 50, 70, 200))
        bg.paste(bar_bg, (int(bar_x), int(bar_y)), bar_bg)
        
        # Progress bar với gradient
        progress_w = int((percentage / 100) * bar_w)
        if progress_w > 0:
            bar_progress = Image.new("RGBA", (progress_w, bar_h), color + (255,))
            bar_progress_draw = ImageDraw.Draw(bar_progress)
            bar_progress_draw.rounded_rectangle((0, 0, progress_w, bar_h), radius=bar_radius, fill=color + (255,))
            bg.paste(bar_progress, (int(bar_x), int(bar_y)), bar_progress)
        
        # Phần trăm text
        percent_text = f"{percentage:.1f}%"
        percent_w = draw.textlength(percent_text, font=font_percent)
        draw.text((bar_x + bar_w - percent_w - 5, bar_y - 22), percent_text,
                  fill=color, font=font_percent)
        
        # Rank icon bên phải
        rank_icon_x = card_x + card_w - 50
        rank_icon_y = card_y + card_height // 2
        draw.text((rank_icon_x, rank_icon_y), f"{rank_label} {rank_icon}",
                  fill=color, anchor="mm", font=font_rank)
        
        y += card_height + spacing

    # Footer
    footer_text = time.strftime("🕓 %H:%M:%S • %d/%m/%Y")
    footer_bbox = draw.textbbox((0, 0), footer_text, font=font_small)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text((width - 30, height - 25), footer_text,
              fill=(140, 150, 170), anchor="rs", font=font_small)

    path = f"modules/cache/topchat_{tid}.png"
    bg.save(path)
    return path

# ================= GHI NHẬN TIN NHẮN =================
def on_message(author_id, author_name, thread_id):
    try:
        data = load_data()
        tid, uid = str(thread_id), str(author_id)

        if tid not in data:
            data[tid] = {}
        if uid not in data[tid]:
            data[tid][uid] = {"name": author_name or uid, "count": 0, "last": 0}

        data[tid][uid]["count"] += 1
        data[tid][uid]["name"] = author_name or data[tid][uid]["name"]
        data[tid][uid]["last"] = time.time()

        save_data(data)
    except Exception as e:
        print(f"⚠️ Lỗi ghi nhận TopChat: {e}")

# ================= LỆNH =================
def handle_topchat(message, msg_obj, tid, ttype, aid, client):
    args = message.split()
    top_n = 5
    if len(args) > 1 and args[1].isdigit():
        top_n = max(1, min(int(args[1]), 10))

    data = load_data()
    if tid not in data or not data[tid]:
        client.replyMessage(Message(text="⚠️ Chưa có dữ liệu chat nào được ghi nhận!"), msg_obj, tid, ttype)
        return

    img_path = draw_topchat_image(client, data, tid, top_n)
    if img_path and hasattr(client, "sendLocalImage"):
        client.sendLocalImage(img_path, tid, ttype, message=Message(text=f"🏆 BXH TƯƠNG TÁC TOP {top_n}"))
    else:
        client.replyMessage(Message(text="⚠️ Không thể tạo ảnh BXH!"), msg_obj, tid, ttype)

def PTA():
    return {"topchat": handle_topchat}

des = {
    "version": "3.8.2 — BXH Giữ Dữ Liệu",
    "credits": "Hoàng Khánh Prime",
    "description": "TopChat v3.8.2 — giữ nguyên BXH, không reset, ghi nhận chính xác.",
    "power": "Thành viên"
}
