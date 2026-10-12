import json
import time
import threading
import os
import random # Thêm thư viện random để chọn màu ngẫu nhiên
from zlapi.models import Message, Mention, MultiMsgStyle, MessageStyle, ThreadType
import logging
from config import PREFIX, ADMIN

logging.basicConfig(level=logging.DEBUG)

des = {
    'version': "1.5.0",
    'credits': "hi Dev",
    'description': "Var Red Style - Delay Config, Tag Support, Show Menu, List, Create, Color, Random",
    'power': "Quản trị viên Bot"
}

is_var_running = False

# --- THÊM CONFIG MÀU SẮC ---
ALL_COLORS = [
    "#DB342E",  # Đỏ
    "#15A85F",  # Xanh lá
    "#F27806",  # Cam
    "#F7B503"   # Vàng
]

COLOR_DICT = {
    "do": "#DB342E",
    "xanh": "#15A85F",
    "cam": "#F27806",
    "vang": "#F7B503"
}

current_color = "#DB342E" # Màu mặc định là Đỏ
is_random_color = False
# ---------------------------

def check_admin_permissions(author_id, thread_id, thread_type, client):
    author_id = str(author_id)
    
    if hasattr(client, 'is_allowed_author') and client.is_allowed_author(author_id):
        return True

    try:
        with open('seting.json', 'r', encoding='utf-8') as f:
            current_settings = json.load(f)
        admin_id = str(current_settings.get('admin', ''))
        adm_list = [str(uid) for uid in current_settings.get('adm', [])]
        
        if author_id == admin_id or author_id in adm_list:
            return True
    except Exception:
        pass

    if author_id in ADMIN:
        return True
        
    return False

def handle_var_command(message, message_object, thread_id, thread_type, author_id, client):
    global is_var_running, current_color, is_random_color
    command_parts = message.split()
    
    # Kiểm tra quyền hạn
    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        client.send(Message(text="🚦 Cút! Quyền hạn không đủ."), thread_id, thread_type, ttl=10000)
        return

    # Nếu chỉ gõ "var", sẽ hiển thị Menu hướng dẫn
    if len(command_parts) == 1:
        menu_msg = (
            f"🚦 HƯỚNG DẪN LỆNH VAR:\n"
            f"• {PREFIX}var [số file] : Chạy với tốc độ mặc định\n"
            f"• {PREFIX}var [số] [tốc độ]ms : Chạy var có tốc độ\n"
            f"• {PREFIX}var [số] [tốc độ]ms @tag : Var tốc độ kèm tag\n"
            f"• {PREFIX}var list : Xem danh sách file var\n"
            f"• {PREFIX}var create [số] [nội dung] : Tạo file var (dùng dấu | để xuống dòng)\n"
            f"• {PREFIX}var mau [do/xanh/cam/vang] : Chọn màu var\n"
            f"• {PREFIX}var random : Chạy var với màu ngẫu nhiên liên tục\n"
            f"• {PREFIX}var tha : Dừng var\n\n"
            f"📌 Ví dụ:\n"
            f"- {PREFIX}var 2\n"
            f"- {PREFIX}var mau xanh\n"
            f"- {PREFIX}var random\n"
            f"- {PREFIX}var create 5 múc nó | đấm nó"
        )
        client.send(Message(text=menu_msg), thread_id, thread_type)
        return

    # ---------------- CHỨC NĂNG MÀU SẮC MỚI ----------------

    # Lệnh chọn màu (var mau <màu>)
    if command_parts[1].lower() == "mau":
        if len(command_parts) < 3:
            client.send(Message(text="❌ Vui lòng chọn màu: do, xanh, cam, vang.\nVí dụ: var mau xanh"), thread_id, thread_type)
            return
            
        mau_chon = command_parts[2].lower()
        if mau_chon in COLOR_DICT:
            current_color = COLOR_DICT[mau_chon]
            is_random_color = False # Tắt chế độ random nếu đang bật
            client.send(Message(text=f"✅ Đã đổi màu var sang: {mau_chon.upper()}"), thread_id, thread_type)
        else:
            client.send(Message(text="❌ Màu không hợp lệ. Vui lòng chọn: do, xanh, cam, vang."), thread_id, thread_type)
        return

    # Lệnh random màu (var random)
    if command_parts[1].lower() == "random":
        is_random_color = True
        client.send(Message(text="✅ Đã bật chế độ Var màu ngẫu nhiên (7 sắc cầu vồng)!"), thread_id, thread_type)
        return

    # ---------------- CÁC CHỨC NĂNG CŨ ----------------

    # Lệnh xem danh sách file var (var list)
    if command_parts[1].lower() == "list":
        if not os.path.exists("spam"):
            client.send(Message(text="❌ Thư mục 'spam' chưa được tạo."), thread_id, thread_type)
            return
        
        files = [f for f in os.listdir("spam") if f.endswith(".txt")]
        if not files:
            client.send(Message(text="📁 Không có file var nào trong thư mục 'spam'."), thread_id, thread_type)
            return
            
        # Sắp xếp lại danh sách theo số/chữ cái cho đẹp
        files.sort()
        msg = "📁 DANH SÁCH FILE VAR HIỆN CÓ:\n"
        for f in files:
            msg += f"• {f.replace('.txt', '')}\n"
            
        client.send(Message(text=msg.strip()), thread_id, thread_type)
        return

    # Lệnh tạo file var mới (var create)
    if command_parts[1].lower() == "create":
        if len(command_parts) < 4:
            client.send(Message(text=f"❌ Sai cú pháp! Vui lòng dùng:\n{PREFIX}var create [tên file] [nội dung]\n💡 Mẹo: Dùng dấu | để phân tách các câu."), thread_id, thread_type)
            return
            
        file_name = command_parts[2]
        
        # Tách lấy toàn bộ phần nội dung phía sau tên file
        parts = message.split(maxsplit=3)
        content_str = parts[3]
        
        # Tạo thư mục spam nếu chưa có
        if not os.path.exists("spam"):
            os.makedirs("spam")
            
        file_path = f"spam/{file_name}.txt"
        
        # Cắt nội dung theo dấu '|' và loại bỏ khoảng trắng dư thừa
        lines = [line.strip() for line in content_str.split('|') if line.strip()]
        
        if not lines:
            client.send(Message(text="❌ Nội dung không hợp lệ."), thread_id, thread_type)
            return
            
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(line + "\n")
            client.send(Message(text=f"✅ Đã tạo file `{file_name}.txt` thành công với {len(lines)} câu chửi!"), thread_id, thread_type)
        except Exception as e:
            client.send(Message(text=f"❌ Lỗi khi lưu file: {e}"), thread_id, thread_type)
        return

    # Lệnh dừng (tha)
    if command_parts[1].lower() in ["tha", "off", "stop"]:
        is_var_running = False
        client.send(Message(text="✅ Đã tha! Cảm ơn đại ca tao đi."), thread_id, thread_type)
        return

    # Phân tích các thông số từ lệnh (Số file và Tốc độ)
    file_num = "1"
    delay_time = 1.5 # Mặc định là 1.5 giây nếu không nhập
    
    for part in command_parts[1:]:
        part_lower = part.lower()
        if part.isdigit():
            file_num = part # Nếu là số thuần thì gán làm số file
        elif part_lower.endswith("ms") and part_lower[:-2].isdigit():
            delay_time = int(part_lower[:-2]) / 1000.0 # Chuyển mili-giây sang giây
        elif part_lower.endswith("s") and part_lower[:-1].isdigit():
            delay_time = float(part_lower[:-1]) # Chuyển giây trực tiếp
            
    # Đặt mức chống lag tối thiểu
    if delay_time < 0.1:
        delay_time = 0.1

    # Xử lý Tag (Mention mục tiêu)
    target_mention = None
    prefix_tag = ""

    if hasattr(message_object, 'mentions') and message_object.mentions:
        mention = message_object.mentions[0]
        uid = mention.get('uid') if isinstance(mention, dict) else getattr(mention, 'uid', None)
        
        if uid:
            prefix_tag = "@Ê " 
            tag_len_for_mention = len(prefix_tag.strip())
            # Chỉ tag và để màu mặc định cho thẻ tag
            target_mention = Mention(uid=str(uid), offset=0, length=tag_len_for_mention)

    # Đọc file
    file_path = f"spam/{file_num}.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            ngon_list = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        client.send(Message(text=f"❌ Không tìm thấy file: {file_path}\nGõ {PREFIX}var để xem hướng dẫn"), thread_id, thread_type)
        return
    except Exception as e:
        client.send(Message(text=f"❌ Lỗi đọc file: {e}"), thread_id, thread_type)
        return

    if not ngon_list:
        client.send(Message(text=f"❌ File {file_num}.txt rỗng!"), thread_id, thread_type)
        return
    
    # Bắt đầu chạy Var
    is_var_running = True
    color_status = "Ngẫu nhiên" if is_random_color else current_color
    status_msg = f" /-li Bắt đầu Var file {file_num}.txt (Tốc độ: {delay_time}s) /-li \n🎨 Màu: {color_status}"
    if target_mention:
        status_msg += "\n🎯 Chế độ: Khóa mục tiêu (Tag)"
    
    client.send(Message(text=status_msg), thread_id, thread_type, ttl=10000)
    
    def var_loop():
        global is_var_running, current_color, is_random_color
        while is_var_running:
            for noidung in ngon_list:
                if not is_var_running:
                    break
                
                # Ghép tag vào phía trước tin nhắn
                final_content = prefix_tag + noidung
                
                tag_length = len(prefix_tag)
                content_length = len(noidung)
                
                # Quyết định màu sắc áp dụng cho tin nhắn hiện tại
                applied_color = random.choice(ALL_COLORS) if is_random_color else current_color
                
                styles = MultiMsgStyle([
                    MessageStyle(offset=tag_length, length=content_length, style="color", color=applied_color, auto_format=False),
                    MessageStyle(offset=tag_length, length=content_length, style="bold", auto_format=False),
                    MessageStyle(offset=tag_length, length=content_length, style="font", size="20", auto_format=False)
                ])
                
                msg = Message(text=final_content, style=styles)
                if target_mention:
                    msg.mention = target_mention
                
                try:
                    client.send(msg, thread_id, thread_type)
                except:
                    pass
                
                # Dừng gửi dựa trên số delay setup
                time.sleep(delay_time)

    thread = threading.Thread(target=var_loop)
    thread.daemon = True
    thread.start()

def PTA():
    return {'var': handle_var_command}
