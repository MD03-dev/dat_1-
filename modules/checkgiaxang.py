import requests
from bs4 import BeautifulSoup
from zlapi.models import Message
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import re

des = {
    'version': "4.0.0",
    'credits': "HoangHoàng Khánh Prime x Gemini",
    'description': "Xem giá xăng dầu, dầu thế giới + vẽ biểu đồ",
    'power': "Thành viên"
}

URL = "https://webgia.com/gia-xang-dau/petrolimex/"

# ====== CACHE PATH ======
CACHE_PATH = "modules/cache"
FONT_DIR = os.path.join(CACHE_PATH, "font")
FONT_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Bold.ttf")
FONT_REGULAR_PATH = os.path.join(FONT_DIR, "BeVietnamPro-Regular.ttf")

# ================== TẠO THƯ MỤC ==================
def ensure_dirs():
    os.makedirs(CACHE_PATH, exist_ok=True)
    os.makedirs(FONT_DIR, exist_ok=True)

# ================== LOAD FONT ==================
def load_font(size, bold=True):
    try:
        path = FONT_PATH if bold else FONT_REGULAR_PATH
        if not os.path.exists(path):
            path = FONT_PATH
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

# ================== LẤY GIÁ XĂNG ==================
def get_gas_price():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        domestic_data = []
        world_data = []
        
        tables = soup.find_all("table")
        if not tables:
            raise Exception("Không tìm thấy bảng giá!")

        # 1. Bảng Xăng Dầu Trong Nước
        domestic_rows = tables[0].find_all("tr")
        for row in domestic_rows:
            cols = [col.text.strip() for col in row.find_all(["td", "th"])]
            if len(cols) >= 3 and "Sản phẩm" not in cols[0] and "Loại" not in cols[0]:
                name = cols[0]
                price_v1 = cols[1]
                price_v2 = cols[2]
                if name and re.search(r'\d', price_v1):
                    domestic_data.append({"name": name, "v1": price_v1, "v2": price_v2})

        # 2. Bảng Giá Dầu Thế Giới
        for table in tables[1:]:
            header = table.find("th")
            if header and ("Dầu thô" in table.text or "WTI" in table.text or "Brent" in table.text):
                world_rows = table.find_all("tr")
                for row in world_rows:
                    cols = [col.text.strip() for col in row.find_all(["td", "th"])]
                    if len(cols) >= 4 and "Sản phẩm" not in cols[0]:
                        world_data.append({
                            "name": cols[0],
                            "price": cols[1],
                            "change": cols[2],
                            "percent": cols[3]
                        })
                break
                
        return domestic_data[:9], world_data[:2]
    except Exception as e:
        print(f"Lỗi Crawl Data: {e}")
        return [], []

# ================== HÀM PHỤ ĐO KÍCH THƯỚC CHỮ ==================
def get_text_width(draw, text, font):
    # Support backward compatibility cho các bản PIL cũ
    try:
        return draw.textlength(text, font=font)
    except AttributeError:
        return draw.textsize(text, font=font)[0]

# ================== VẼ ẢNH CANVAS (COMPACT MODE) ==================
def draw_image(domestic_data, world_data):
    ensure_dirs()
    
    WIDTH = 800
    HEIGHT = 1200 # Set height tạm thời, sẽ crop ở cuối
    BG_COLOR = "#F4F9F4"
    MAIN_GREEN = "#3B8840"
    LIGHT_GREEN = "#A7D7A9"
    TEXT_DARK = "#333333"
    TEXT_WHITE = "#FFFFFF"
    
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Giảm size font xuống một chút để nén dòng tốt hơn
    font_title = load_font(34, bold=True)
    font_section = load_font(24, bold=True)
    font_th = load_font(18, bold=True)
    font_td = load_font(18, bold=True)
    font_chart = load_font(12, bold=False)
    font_footer = load_font(16, bold=True)

    y_offset = 20 # Giảm lề trên

    # ===== 1. TIÊU ĐỀ CHÍNH =====
    title = "⛽ GIÁ XĂNG DẦU HÔM NAY"
    w = get_text_width(draw, title, font_title)
    draw.text(((WIDTH - w) / 2, y_offset), title, fill=MAIN_GREEN, font=font_title)
    y_offset += 50

    # ===== 2. BẢNG XĂNG DẦU TRONG NƯỚC =====
    table_margin = 15 # Ép margin nhỏ lại để chiều ngang chứa được nhiều chữ hơn
    table_width = WIDTH - (table_margin * 2)
    row_height = 36 # Rút ngắn chiều cao dòng
    
    draw.rounded_rectangle((table_margin, y_offset, WIDTH - table_margin, y_offset + row_height + 5), radius=8, fill=MAIN_GREEN)
    
    # Bỏ \n để viết ngang, giúp tiết kiệm height
    headers_1 = [("Sản Phẩm (Petrolimex)", table_margin + 20), 
                 ("Vùng 1 (VNĐ/lít)", table_margin + 380), 
                 ("Vùng 2 (VNĐ/lít)", table_margin + 580)]
    
    for text, x in headers_1:
        draw.text((x, y_offset + 8), text, fill=TEXT_WHITE, font=font_th)
    
    y_offset += row_height + 10
    
    draw.rounded_rectangle((table_margin, y_offset - 5, WIDTH - table_margin, y_offset + (len(domestic_data)*row_height) + 5), 
                           radius=8, outline=MAIN_GREEN, width=2)
    
    for i, item in enumerate(domestic_data):
        if i % 2 == 1:
            draw.rectangle((table_margin + 2, y_offset, WIDTH - table_margin - 2, y_offset + row_height), fill="#EAF3EA")
            
        draw.text((table_margin + 20, y_offset + 8), item['name'], fill=TEXT_DARK, font=font_td)
        draw.text((table_margin + 400, y_offset + 8), item['v1'], fill=MAIN_GREEN, font=font_td)
        draw.text((table_margin + 600, y_offset + 8), item['v2'], fill=MAIN_GREEN, font=font_td)
        y_offset += row_height
        
        if i < len(domestic_data) - 1:
            draw.line((table_margin, y_offset, WIDTH - table_margin, y_offset), fill="#D1E5D2", width=1)

    y_offset += 25

    # ===== 3. BẢNG GIÁ DẦU THẾ GIỚI =====
    if world_data:
        title_2 = "🌍 Giá Dầu Thế Giới"
        w2 = get_text_width(draw, title_2, font_section)
        draw.text(((WIDTH - w2) / 2, y_offset), title_2, fill=MAIN_GREEN, font=font_section)
        y_offset += 35
        
        draw.rounded_rectangle((table_margin, y_offset, WIDTH - table_margin, y_offset + row_height), radius=8, fill=MAIN_GREEN)
        headers_2 = [("Sản Phẩm", table_margin + 80), ("Giá (USD/Thùng)", table_margin + 260), 
                     ("Thay Đổi", table_margin + 480), ("%", table_margin + 620)]
        for text, x in headers_2:
            draw.text((x, y_offset + 8), text, fill=TEXT_WHITE, font=font_th)
        
        y_offset += row_height
        
        draw.rounded_rectangle((table_margin, y_offset - 5, WIDTH - table_margin, y_offset + (len(world_data)*row_height)), 
                               radius=8, outline=MAIN_GREEN, width=2)
        for i, item in enumerate(world_data):
            draw.text((table_margin + 40, y_offset + 8), item['name'], fill=TEXT_DARK, font=font_td)
            draw.text((table_margin + 290, y_offset + 8), item['price'], fill=TEXT_DARK, font=font_td)
            
            color_change = MAIN_GREEN if "+" in item['change'] or "↑" in item['change'] else "#D32F2F"
            draw.text((table_margin + 490, y_offset + 8), item['change'], fill=color_change, font=font_td)
            draw.text((table_margin + 610, y_offset + 8), item['percent'], fill=color_change, font=font_td)
            y_offset += row_height
    
    y_offset += 25

    # ===== 4. BIỂU ĐỒ BAR CHART =====
    chart_title = "Biểu đồ Giá Xăng Dầu (Nghìn VNĐ/Lít)"
    w3 = get_text_width(draw, chart_title, font_section)
    draw.text(((WIDTH - w3) / 2, y_offset), chart_title, fill="#666666", font=font_section)
    y_offset += 35
    
    # Rút gọn chú thích và xếp sát nhau
    draw.rectangle((220, y_offset+5, 240, y_offset+17), fill=MAIN_GREEN)
    draw.text((250, y_offset+2), "Vùng 1 (Nghìn VNĐ/Lít)", fill=TEXT_DARK, font=font_chart)
    draw.rectangle((430, y_offset+5, 450, y_offset+17), fill=LIGHT_GREEN)
    draw.text((460, y_offset+2), "Vùng 2 (Nghìn VNĐ/Lít)", fill=TEXT_DARK, font=font_chart)
    y_offset += 30

    chart_x_start = 60
    chart_y_start = y_offset
    chart_width = 700
    chart_height = 140 # Giảm chiều cao biểu đồ từ 200 -> 140
    
    try:
        max_price_val = max([float(item['v2'].replace('.', '').replace(',', '.')) for item in domestic_data]) / 1000
    except:
        max_price_val = 30

    y_max_grid = int(max_price_val) + 2
    y_min_grid = 18
    grid_steps = y_max_grid - y_min_grid
    
    for step in range(grid_steps + 1):
        grid_y = chart_y_start + chart_height - (step * (chart_height / grid_steps))
        draw.line((chart_x_start, grid_y, chart_x_start + chart_width, grid_y), fill="#E0E0E0", width=1)
        # Bớt mật độ số ở trục Y cho khỏi rối mắt khi đã thu nhỏ biểu đồ
        if (y_min_grid + step) % 2 == 0:
            draw.text((chart_x_start - 25, grid_y - 8), str(y_min_grid + step), fill="#888888", font=font_chart)

    bar_group_width = chart_width / len(domestic_data)
    bar_width = 16 
    
    for i, item in enumerate(domestic_data):
        try:
            val1 = float(item['v1'].replace('.', '').replace(',', '.')) / 1000
            val2 = float(item['v2'].replace('.', '').replace(',', '.')) / 1000
        except:
            continue
            
        x_center = chart_x_start + (i * bar_group_width) + (bar_group_width / 2)
        
        h1 = ((val1 - y_min_grid) / grid_steps) * chart_height
        y1 = chart_y_start + chart_height - h1
        draw.rectangle((x_center - bar_width - 1, y1, x_center - 1, chart_y_start + chart_height), fill=MAIN_GREEN)
        
        h2 = ((val2 - y_min_grid) / grid_steps) * chart_height
        y2 = chart_y_start + chart_height - h2
        draw.rectangle((x_center + 1, y2, x_center + bar_width + 1, chart_y_start + chart_height), fill=LIGHT_GREEN)
        
        short_name = item['name'].replace("RON ", "").replace("DO ", "").split("-")[0]
        draw.text((x_center - 20, chart_y_start + chart_height + 5), short_name, fill="#555555", font=font_chart)

    y_offset = chart_y_start + chart_height + 35

    # ===== 5. FOOTER =====
    now = datetime.now()
    days = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    date_text = f"Cập nhật: {days[now.weekday()]}, {now.strftime('%d/%m/%Y - %H:%M')}"
    
    w4 = get_text_width(draw, date_text, font_footer)
    draw.text(((WIDTH - w4) / 2, y_offset), date_text, fill="#555555", font=font_footer)

    y_offset += 30

    # ===== CẮT ẢNH CHO CHUẨN TỶ LỆ TRÁNH CROP TRÊN ZALO =====
    path = os.path.join(CACHE_PATH, "giaxang_full.png")
    final_img = img.crop((0, 0, WIDTH, int(y_offset)))
    
    # Tùy chọn: Dùng tính năng Resize mượt của PIL để ảnh sắc nét nhưng dung lượng nhỏ
    try:
        final_img = final_img.resize((WIDTH, int(y_offset)), Image.Resampling.LANCZOS)
    except:
        final_img = final_img.resize((WIDTH, int(y_offset)), Image.ANTIALIAS)
        
    final_img.save(path, "PNG")

    return path

# ================== HANDLE COMMAND ==================
def handle_check_gas_command(message, message_object, thread_id, thread_type, author_id, client):
    try:
        ensure_dirs()

        domestic_data, world_data = get_gas_price()

        if not domestic_data:
            raise Exception("Không thể parse dữ liệu từ webgia. Có thể cấu trúc web đã thay đổi!")

        img_path = draw_image(domestic_data, world_data)
        # ====== GỬI ẢNH ======
        client.sendLocalImage(
            img_path,
            thread_id=thread_id,
            thread_type=thread_type
        )

    except Exception as e:
        client.sendMessage(
            Message(text=f"❌ Lỗi khi lấy giá xăng:\n{str(e)}"),
            thread_id,
            thread_type
        )
# ================== REGISTER ==================
def PTA():
    return {
        'giaxang': handle_check_gas_command,
        'checkxang': handle_check_gas_command
    }

