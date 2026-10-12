import requests
from bs4 import BeautifulSoup
from zlapi.models import Message
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import re

des = {
    'version': "4.0.0",
    'credits': "Hoàng Khánh Prime",
    'description': "Xem giá vàng trong nước, thế giới + vẽ biểu đồ",
    'power': "Thành viên"
}

# Sử dụng một trang web phổ biến để lấy giá vàng
URL = "https://webgia.com/gia-vang/"

# ====== CACHE PATH ======
CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")
EMOJI_FONT_PATH = os.path.join(FONT_DIR, "NotoEmoji-Bold.ttf")

# ================== TẠO THƯ MỤC ==================
def ensure_dirs():
    os.makedirs(CACHE_PATH, exist_ok=True)
    os.makedirs(FONT_DIR, exist_ok=True)

# ================== LOAD FONT ==================
def load_font(size, bold=True, is_emoji=False):
    try:
        if is_emoji:
            try:
                # Bật embedded_color để hỗ trợ render Emoji sắc nét hơn
                return ImageFont.truetype(EMOJI_FONT_PATH, size, embedded_color=True)
            except Exception:
                pass
        
        path = FONT_PATH if bold else FONT_REGULAR_PATH
        if not os.path.exists(path):
            path = FONT_PATH
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# ================== LẤY GIÁ VÀNG ==================
def get_gold_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    domestic_data = []
    world_data = []
    
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        tables = soup.find_all("table")
        
        # 1. Bảng Giá Vàng Trong Nước (Thường là bảng đầu tiên)
        if len(tables) > 0:
            domestic_rows = tables[0].find_all("tr")
            for row in domestic_rows:
                cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                if len(cols) >= 3 and "Loại" not in cols[0] and "Mua" not in cols[1]:
                    name = cols[0]
                    buy_price = cols[1]
                    sell_price = cols[2]
                    if name and re.search(r'\d', buy_price):
                        domestic_data.append({"name": name, "buy": buy_price, "sell": sell_price})

        # 2. Bảng Giá Vàng Thế Giới (Tìm bảng có chữ XAU hoặc Thế giới)
        for table in tables:
            if "thế giới" in table.text.lower() or "xau" in table.text.lower():
                world_rows = table.find_all("tr")
                for row in world_rows:
                    cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                    if len(cols) >= 4 and "Loại" not in cols[0]:
                        world_data.append({
                            "name": cols[0],
                            "price": cols[1],
                            "change": cols[2],
                            "percent": cols[3]
                        })
                break
                
    except Exception as e:
        print(f"Lỗi Crawl Data Giá Vàng: {e}")
        
    # --- DỮ LIỆU DỰ PHÒNG (Fallback) ---
    if not domestic_data:
        domestic_data = [
            {"name": "SJC 1L, 10L", "buy": "82.500.000", "sell": "84.500.000"},
            {"name": "DOJI HN", "buy": "82.500.000", "sell": "84.500.000"},
            {"name": "DOJI SG", "buy": "82.500.000", "sell": "84.500.000"},
            {"name": "Vàng nhẫn 9999", "buy": "74.500.000", "sell": "76.000.000"},
            {"name": "PNJ", "buy": "74.600.000", "sell": "76.200.000"}
        ]
    if not world_data:
        world_data = [
            {"name": "Vàng Thế Giới (XAU/USD)", "price": "2,350.50", "change": "+15.20", "percent": "+0.65%"}
        ]

    # Cắt bớt danh sách nếu quá dài để ảnh không bị tràn
    return domestic_data[:8], world_data[:2]

# ================== HÀM PHỤ ĐO KÍCH THƯỚC CHỮ ==================
def get_text_width(draw, text, font):
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return draw.textsize(text, font=font)[0]

# ================== VẼ ẢNH CANVAS (COMPACT MODE) ==================
def draw_image(domestic_data, world_data):
    ensure_dirs()
    
    WIDTH = 800
    HEIGHT = 1300 
    BG_COLOR = "#FFFDF5" # Nền hơi vàng nhạt
    MAIN_GOLD = "#B8860B" # Vàng đậm sang trọng
    LIGHT_GOLD = "#F3E5AB" # Vàng nhạt cho cột mua
    TEXT_DARK = "#333333"
    TEXT_WHITE = "#FFFFFF"
    
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    font_title = load_font(36, bold=True)
    font_title_emoji = load_font(36, is_emoji=True)
    
    font_section = load_font(24, bold=True)
    font_section_emoji = load_font(24, is_emoji=True)
    
    font_th = load_font(18, bold=True)
    font_td = load_font(18, bold=True)
    font_chart = load_font(12, bold=False)
    font_footer = load_font(16, bold=True)

    y_offset = 20

    # ===== 1. TIÊU ĐỀ CHÍNH =====
    emoji_1 = "🏆"
    text_1 = " BẢNG GIÁ VÀNG HÔM NAY"
    
    w_emoji_1 = get_text_width(draw, emoji_1, font_title_emoji)
    w_text_1 = get_text_width(draw, text_1, font_title)
    
    start_x_1 = (WIDTH - (w_emoji_1 + w_text_1)) / 2
    
    draw.text((start_x_1, y_offset), emoji_1, font=font_title_emoji)
    draw.text((start_x_1 + w_emoji_1, y_offset), text_1, fill=MAIN_GOLD, font=font_title)
    y_offset += 55

    # ===== 2. BẢNG GIÁ VÀNG TRONG NƯỚC =====
    table_margin = 15
    row_height = 36
    
    draw.rounded_rectangle((table_margin, y_offset, WIDTH - table_margin, y_offset + row_height + 5), radius=8, fill=MAIN_GOLD)
    
    headers_1 = [("Thương Hiệu", table_margin + 20), 
                 ("Mua Vào (VNĐ/Lượng)", table_margin + 360), 
                 ("Bán Ra (VNĐ/Lượng)", table_margin + 580)]
    
    for text, x in headers_1:
        draw.text((x, y_offset + 8), text, fill=TEXT_WHITE, font=font_th)
    
    y_offset += row_height + 10
    
    draw.rounded_rectangle((table_margin, y_offset - 5, WIDTH - table_margin, y_offset + (len(domestic_data)*row_height) + 5), 
                           radius=8, outline=MAIN_GOLD, width=2)
    
    for i, item in enumerate(domestic_data):
        if i % 2 == 1:
            draw.rectangle((table_margin + 2, y_offset, WIDTH - table_margin - 2, y_offset + row_height), fill="#FEFAED")
            
        short_name = item['name'][:30] + "..." if len(item['name']) > 30 else item['name']
            
        draw.text((table_margin + 20, y_offset + 8), short_name, fill=TEXT_DARK, font=font_td)
        draw.text((table_margin + 370, y_offset + 8), item['buy'], fill="#228B22", font=font_td) 
        draw.text((table_margin + 590, y_offset + 8), item['sell'], fill="#D32F2F", font=font_td) 
        y_offset += row_height
        
        if i < len(domestic_data) - 1:
            draw.line((table_margin, y_offset, WIDTH - table_margin, y_offset), fill="#E8D8A6", width=1)

    y_offset += 30

    # ===== 3. BẢNG GIÁ VÀNG THẾ GIỚI =====
    if world_data:
        emoji_2 = "🌍"
        text_2 = " Giá Vàng Thế Giới"
        
        w_emoji_2 = get_text_width(draw, emoji_2, font_section_emoji)
        w_text_2 = get_text_width(draw, text_2, font_section)
        
        start_x_2 = (WIDTH - (w_emoji_2 + w_text_2)) / 2
        
        draw.text((start_x_2, y_offset), emoji_2, font=font_section_emoji)
        draw.text((start_x_2 + w_emoji_2, y_offset), text_2, fill=MAIN_GOLD, font=font_section)
        y_offset += 35
        
        draw.rounded_rectangle((table_margin, y_offset, WIDTH - table_margin, y_offset + row_height), radius=8, fill=MAIN_GOLD)
        headers_2 = [("Sản Phẩm", table_margin + 60), ("Giá (USD/oz)", table_margin + 300), 
                     ("Thay Đổi", table_margin + 480), ("%", table_margin + 640)]
        for text, x in headers_2:
            draw.text((x, y_offset + 8), text, fill=TEXT_WHITE, font=font_th)
        
        y_offset += row_height
        
        draw.rounded_rectangle((table_margin, y_offset - 5, WIDTH - table_margin, y_offset + (len(world_data)*row_height)), 
                               radius=8, outline=MAIN_GOLD, width=2)
        for i, item in enumerate(world_data):
            draw.text((table_margin + 40, y_offset + 8), item['name'], fill=TEXT_DARK, font=font_td)
            draw.text((table_margin + 290, y_offset + 8), item['price'], fill=TEXT_DARK, font=font_td)
            
            color_change = "#228B22" if "+" in item['change'] or "↑" in item['change'] else "#D32F2F"
            draw.text((table_margin + 490, y_offset + 8), item['change'], fill=color_change, font=font_td)
            draw.text((table_margin + 630, y_offset + 8), item['percent'], fill=color_change, font=font_td)
            y_offset += row_height
    
    y_offset += 35

    # ===== 4. BIỂU ĐỒ BAR CHART =====
    chart_title = "Biểu đồ Mức Giá Mua - Bán (Triệu VNĐ/Lượng)"
    w3 = get_text_width(draw, chart_title, font_section)
    draw.text(((WIDTH - w3) / 2, y_offset), chart_title, fill="#666666", font=font_section)
    y_offset += 35
    
    draw.rectangle((260, y_offset+5, 280, y_offset+17), fill=LIGHT_GOLD)
    draw.text((290, y_offset+2), "Mua Vào", fill=TEXT_DARK, font=font_chart)
    draw.rectangle((430, y_offset+5, 450, y_offset+17), fill=MAIN_GOLD)
    draw.text((460, y_offset+2), "Bán Ra", fill=TEXT_DARK, font=font_chart)
    y_offset += 35

    chart_x_start = 60
    chart_y_start = y_offset
    chart_width = 700
    chart_height = 150 
    
    all_prices = []
    for item in domestic_data:
        try:
            b = float(re.sub(r'[^\d]', '', item['buy'])) / 1000000
            s = float(re.sub(r'[^\d]', '', item['sell'])) / 1000000
            all_prices.extend([b, s])
        except:
            pass

    if all_prices:
        y_max_grid = int(max(all_prices)) + 2
        y_min_grid = int(min(all_prices)) - 2
        if y_min_grid < 0: y_min_grid = 0
    else:
        y_max_grid = 90
        y_min_grid = 60

    grid_steps = y_max_grid - y_min_grid
    if grid_steps <= 0: grid_steps = 10
    
    for step in range(grid_steps + 1):
        grid_y = chart_y_start + chart_height - (step * (chart_height / grid_steps))
        draw.line((chart_x_start, grid_y, chart_x_start + chart_width, grid_y), fill="#EAEAEA", width=1)
        if (y_min_grid + step) % 2 == 0:  
            draw.text((chart_x_start - 25, grid_y - 8), str(y_min_grid + step), fill="#888888", font=font_chart)

    bar_group_width = chart_width / len(domestic_data)
    bar_width = 18
    
    for i, item in enumerate(domestic_data):
        try:
            val_buy = float(re.sub(r'[^\d]', '', item['buy'])) / 1000000
            val_sell = float(re.sub(r'[^\d]', '', item['sell'])) / 1000000
        except:
            continue
            
        x_center = chart_x_start + (i * bar_group_width) + (bar_group_width / 2)
        
        # Cột Mua 
        h1 = ((val_buy - y_min_grid) / grid_steps) * chart_height
        y1 = chart_y_start + chart_height - h1
        draw.rectangle((x_center - bar_width - 1, y1, x_center - 1, chart_y_start + chart_height), fill=LIGHT_GOLD)
        
        # Cột Bán
        h2 = ((val_sell - y_min_grid) / grid_steps) * chart_height
        y2 = chart_y_start + chart_height - h2
        draw.rectangle((x_center + 1, y2, x_center + bar_width + 1, chart_y_start + chart_height), fill=MAIN_GOLD)
        
        short_name = item['name'].replace("Vàng nhẫn", "Nhẫn").split(" ")[0][:8]
        draw.text((x_center - 15, chart_y_start + chart_height + 8), short_name, fill="#555555", font=font_chart)

    y_offset = chart_y_start + chart_height + 40

    # ===== 5. FOOTER =====
    now = datetime.now()
    days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    date_text = f"Cập nhật: {days[now.weekday()]}, {now.strftime('%d/%m/%Y - %H:%M')}"
    
    w4 = get_text_width(draw, date_text, font_footer)
    draw.text(((WIDTH - w4) / 2, y_offset), date_text, fill="#888888", font=font_footer)

    y_offset += 30

    # ===== CẮT ẢNH VÀ TRẢ VỀ CẢ KÍCH THƯỚC =====
    final_height = int(y_offset)
    path = os.path.join(CACHE_PATH, "giavang_full.png")
    final_img = img.crop((0, 0, WIDTH, final_height))
    
    try:
        final_img = final_img.resize((WIDTH, final_height), Image.Resampling.LANCZOS)
    except:
        final_img = final_img.resize((WIDTH, final_height), Image.ANTIALIAS)
        
    final_img.save(path, "PNG")

    return path, WIDTH, final_height

# ================== HANDLE COMMAND ==================
def handle_check_gold_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        ensure_dirs()
        domestic_data, world_data = get_gold_price()

        # Nhận thêm width và height từ hàm vẽ ảnh
        img_path, w, h = draw_image(domestic_data, world_data)
        
        # ====== GỬI ẢNH (Truyền thêm width, height để tránh crop) ======
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type,
            width=w,
            height=h
        )

    except Exception as e:
        client.sendMessage(
            Message(text=f"❌ Lỗi khi xử lý giá vàng:\n{str(e)}"),
            thread_id,
            thread_type
        )

# ================== REGISTER ==================
def PTA():
    return {
        'giavang': handle_check_gold_command,
        'checkvang': handle_check_gold_command
    }
