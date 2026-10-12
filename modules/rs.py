import sys
import os
import time
from zlapi.models import Message, ThreadType, MultiMsgStyle, MessageStyle
from config import ADMIN, HEADER_STYLE

# Khởi tạo danh sách Admin từ config
ADMIN_ID = ADMIN

des = {
    'version': "1.4.0",
    'credits': "Van Chien Dev",
    'description': "Restart bot - Chữ đỏ, không tag, có thời gian khởi động",
    'power': "Admin",
    'reaction': False
}

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

def send_styled_reply(client, message_object, thread_id, thread_type, main_content, is_reply=True):
    """
    Hàm gửi tin nhắn có tiêu đề đỏ, in đậm và kích thước lớn.
    Đã loại bỏ hoàn toàn chức năng tag người dùng.
    """
    header_text = str(HEADER_STYLE)
    header_len = len(header_text)
    
    # Nội dung tin nhắn chỉ bao gồm tiêu đề và nội dung chính
    full_msg = f"{header_text}\n{main_content}"
    
    # Định dạng Style cho tiêu đề (Màu đỏ #db342e, in đậm, cỡ chữ 18)
    style_list = [
        MessageStyle(offset=0, length=header_len, style="color", color="#db342e", auto_format=False),
        MessageStyle(offset=0, length=header_len, style="bold", auto_format=False),
        MessageStyle(offset=0, length=header_len, style="font", size=18, auto_format=False)
    ]
    styles = MultiMsgStyle(style_list)
    
    try:
        msg_payload = Message(text=full_msg, style=styles)
        
        if is_reply and message_object:
            # Sử dụng replyMessage để phản hồi tin nhắn bot
            client.replyMessage(msg_payload, message_object, thread_id, thread_type, ttl=120000)
        else:
            client.sendMessage(msg_payload, thread_id, thread_type, ttl=120000)
    except Exception as e:
        print(f"Lỗi gửi tin nhắn: {e}")
        client.sendMessage(Message(text=full_msg), thread_id, thread_type)

def handle_reset_command(message, message_object, thread_id, thread_type, author_id, client):

    if not check_admin_permissions(author_id, thread_id, thread_type, client):
        send_styled_reply(client, message_object, thread_id, thread_type, 
                          "Bạn không có quyền sử dụng lệnh này\nYêu Cầu: Quản Trị Viên Bot\n🚫🚫🚫")
        return

    try:
        # Thông báo bắt đầu khởi động (Sử dụng reply)
        send_styled_reply(client, message_object, thread_id, thread_type, 
                          "Đang tiến hành khởi động lại hệ thống...\nVui lòng chờ trong giây lát!\n✅✅✅")

        # Lưu thông tin khởi động vào cache
        start_time = time.time()
        with open("modules/cache/restart_info.txt", "w", encoding="utf-8") as f:
            f.write(f"{thread_id}\n{thread_type.name}\n{start_time}")

        # Lệnh khởi chạy lại hệ thống
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    except Exception as e:
        client.sendMessage(Message(text=f"• Đã xảy ra lỗi khi restart bot: {str(e)}"), thread_id, thread_type)

def send_reset_success_message(client):
    """
    Hàm thông báo khởi động thành công và tính thời gian bot đã khởi động lại là bao nhiêu giây.
    """
    cache_path = "modules/cache/restart_info.txt"
    if not os.path.exists(cache_path):
        return

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
            if len(lines) < 3: return
            
            thread_id = lines[0]
            type_str = lines[1]
            start_time = float(lines[2])
        
        thread_type = ThreadType.GROUP if type_str == "GROUP" else ThreadType.USER
        
        # Tính toán thời gian khởi động lại
        duration = round(time.time() - start_time, 2)
        content = f"Hệ thống bot đã hoạt động trở lại\nThời gian đã khởi động lại là: {duration} giây\n✅✅✅"
        
        # Gửi thông báo (is_reply=False vì tin nhắn cũ không còn trong phiên làm việc mới)
        send_styled_reply(client, None, thread_id, thread_type, content, is_reply=False)
        
        os.remove(cache_path)
    except Exception as e:
        print(f"Lỗi gửi xác nhận restart: {e}")

def PTA():
    return {
        'rs': handle_reset_command,
        'restart': handle_reset_command
    }