from zlapi.models import Message, ZaloAPIException, MultiMsgStyle, MessageStyle
import os
import importlib
import json

des = {
    'version': "1.0.5",
    'credits': "Hoàng Khánh Prime",
    'description': "Hiển thị toàn bộ danh sách lệnh bot và chi tiết các lệnh cụ thể",
    'power': "Thành viên",
    'syntax': ",command [số trang]",
    'countdown': "5 Giây"
}

def get_utf16_length(s):
    """
    Tính toán độ dài chuỗi theo chuẩn UTF-16 code units của Zalo.
    Bắt buộc để căn chỉnh tọa độ màu chính xác 100% không bị lệch khi có Emoji.
    """
    return len(s.encode('utf-16-le')) // 2

def get_icon_for_description(description):
    """
    Hàm tự động quét từ khóa trong mô tả và trả về icon phù hợp.
    Được nâng cấp với hơn 100+ từ khóa để nhận diện chuẩn xác nhất.
    """
    desc_lower = description.lower()
    
    # Danh sách từ khóa và icon được chia theo từng nhóm chủ đề
    icon_mapping = {
        # 1. Nền tảng / Mạng xã hội / Ứng dụng (Ưu tiên quét trước)
        'tiktok': '🎵', 'youtube': '▶️', 'facebook': '📘', 'instagram': '📸',
        'pinterest': '🔴', 'spotify': '🟢', 'soundcloud': '☁️', 'capcut': '✂️',
        'google': '🌐', 'chatgpt': '🧠', 'gemini': '✨', 'simsimi': '🐥',
        'wikipedia': '🏛️', 'github': '🐙', 'shopee': '🛍️',
        
        # 2. AI / Trò chuyện / Xử lý ngôn ngữ
        'ai ': '🤖', 'bot ': '🤖', 'chat': '💬', 'trò chuyện': '💬',
        'hỏi đáp': '🙋', 'ngôn ngữ tự nhiên': '🗣️', 'văn bản': '📝',
        
        # 3. Quản trị / Box / Hệ thống
        'admin': '👑', 'quản trị': '🛡️', 'hệ thống': '⚙️', 'cài đặt': '🛠️',
        'khởi động': '🔄', 'bảo trì': '🚧', 'cập nhật': '🆙', 'update': '🔄',
        'ping': '📶', 'uptime': '⏱️', 'tốc độ': '⚡', 'cấm': '🚫', 'ban ': '🔨',
        'kick': '👢', 'cảnh cáo': '⚠️', 'duyệt': '✅', 'nhóm': '👥', 'box': '📦',
        
        # 4. Giải trí / Game / Cá cược
        'tài xỉu': '🎲', 'bầu cua': '🦀', 'oẳn tù tì': '✌️', 'cờ caro': '⭕',
        'đoán': '🤔', 'bắt chữ': '🅰️', 'blackjack': '🃏', 'poker': '♠️',
        'casino': '🎰', 'quay số': '🎡', 'gacha': '🌠', 'lô đề': '🎫',
        'trò chơi': '🎮', 'game': '🎮', 'giải trí': '🎪', 'thử thách': '🎯',
        
        # 5. Hệ thống Lệnh / Hướng dẫn / Thông tin
        'hướng dẫn': '📚', 'menu': '📑', 'danh sách': '📋', 'thông tin': 'ℹ️',
        'chi tiết': '📖', 'lệnh': '⌨️', 'help': '🆘', 'trợ giúp': '🤝',
        'luật': '⚖️', 'quy định': '📜',
        
        # 6. Media (Âm nhạc, Video, Hình ảnh)
        'bài hát': '🎤', 'nhạc': '🎵', 'mp3': '🎧', 'âm thanh': '🔊',
        'lyric': '🎶', 'lời bài hát': '🎼',
        'video': '🎥', 'mp4': '🎬', 'phim': '🍿', 'anime': '🌸',
        'ảnh': '🖼️', 'hình': '📸', 'avatar': '👤', 'logo': '🎨',
        'background': '🌄', 'wallpaper': '📱', 'cosplay': '👗',
        
        # 7. Tải xuống / Tiện ích URL
        'tải': '📥', 'download': '⬇️', 'convert': '🔄', 'chuyển đổi': '🔀',
        'rút gọn': '🔗', 'link': '📎', 'qr ': '🔲', 'mã vạch': '🦓',
        
        # 8. Kinh tế / Tiền tệ / Ngân hàng
        'tiền': '💰', 'xu ': '🪙', 'tài khoản': '💳', 'bank': '🏦',
        'ngân hàng': '🏛️', 'chuyển khoản': '💸', 'pay': '📱',
        'điểm danh': '📝', 'daily': '📅', 'nhận thưởng': '🎁',
        'shop': '🛒', 'mua sắm': '🛍️', 'chứng khoán': '📈', 'crypto': '🪙',
        
        # 9. Công cụ / Đời sống / Tiện ích khác
        'thời tiết': '⛅', 'nhiệt độ': '🌡️',
        'dịch': '🌐', 'translate': '🎌', 'ngôn ngữ': '🗣️', 'từ điển': '📖',
        'tìm kiếm': '🔍', 'search': '🔎',
        'thời gian': '⏰', 'ngày': '📅', 'tháng': '🗓️', 'năm': '🎆',
        'toán': '🧮', 'tính': '🔢', 'máy tính': '📟',
        'bói': '🔮', 'tử vi': '☯️', 'cung hoàng đạo': '♈', 'tarot': '🃏',
        
        # 10. Tương tác / Cảm xúc / Xã hội
        'tình yêu': '❤️', 'vợ': '👰', 'chồng': '🤵', 'thả thính': '🎣',
        'ghép đôi': '💑', 'hug': '🫂', 'ôm': '🫂', 'kiss': '😘', 'hôn': '💋',
        'đấm': '👊', 'tát': '🖐️', 'chửi': '🤬', 'cà khịa': '😏', 'khen': '👍',
        
        # 11. Nhạy cảm (Dành cho các lệnh giới hạn độ tuổi nếu có)
        '18+': '🔞', 'nsfw': '🔞', 'hentai': '🍑'
    }
    
    for keyword, icon in icon_mapping.items():
        if keyword in desc_lower:
            return icon
            
    # Trả về icon mặc định nếu không khớp từ khóa nào
    return '📌' 

def get_all_commands_info():
    all_commands = {}
    module_dir = 'modules'
    if not os.path.exists(module_dir):
        return all_commands

    for module_name in os.listdir(module_dir):
        if module_name.endswith('.py') and module_name != '__init__.py':
            module_path = f'modules.{module_name[:-3]}'
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, 'PTA') and hasattr(module, 'des'):
                    module_des = getattr(module, 'des')
                    pta_funcs = module.PTA() 
                    
                    description = module_des.get('description', 'Không có mô tả')
                    power = module_des.get('power', 'Thành viên')
                    countdown = module_des.get('countdown', '5 Giây')
                    
                    for cmd_trigger in pta_funcs.keys():
                        # Tự động ghép dấu phẩy + tên lệnh nếu dev quên set syntax (Fix lỗi "Chưa cập nhật")
                        syntax = module_des.get('syntax')
                        if not syntax or syntax == 'Chưa cập nhật':
                            syntax = f",{cmd_trigger}"
                            
                        all_commands[cmd_trigger] = {
                            'description': description,
                            'power': power,
                            'syntax': syntax,
                            'countdown': countdown
                        }
            except Exception:
                continue
    return all_commands

def handle_menu_command(message, message_object, thread_id, thread_type, author_id, client):
    commands_dict = get_all_commands_info()
    args = message.split()
    items_per_page = 10
    current_page = 1
    
    if len(args) > 1:
        try:
            current_page = int(args[1])
            if current_page < 1: current_page = 1
        except:
            current_page = 1
    
    all_cmd_keys = sorted(list(commands_dict.keys()))
    total_cmds = len(all_cmd_keys)
    if total_cmds == 0:
        client.replyMessage(Message(text="Chưa có lệnh nào."), message_object, thread_id, thread_type)
        return

    total_pages = (total_cmds + items_per_page - 1) // items_per_page
    if current_page > total_pages: current_page = total_pages

    start_index = (current_page - 1) * items_per_page
    end_index = start_index + items_per_page
    page_commands = all_cmd_keys[start_index:end_index]

    final_text = "📜 Danh sách lệnh:\n\n"
    styles = []

    for i, cmd_name in enumerate(page_commands):
        info = commands_dict[cmd_name]
        
        # Sinh icon động dựa vào mô tả
        dynamic_icon = get_icon_for_description(info['description'])
        
        # 1. Các thành phần text của 1 lệnh
        prefix = f"{start_index + i + 1}. ⭐ Lệnh: "
        desc_line = f"📝 Mô Tả: {dynamic_icon} {info['description']}\n"
        syntax_line = f"💡 Cú pháp: {info['syntax']}\n"
        countdown_line = f"⏱️ Countdown: {info['countdown']}\n\n"
        
        # 2. Tính toán toạ độ (Offset) dựa vào độ dài text hiện tại TRƯỚC KHI cộng dồn lệnh mới
        cmd_start_offset = get_utf16_length(final_text) + get_utf16_length(prefix)
        cmd_length = get_utf16_length(cmd_name)
        
        # 3. Add Style Màu Xanh & In Đậm cho tên lệnh (Đã fix lỗi cú pháp zlapi)
        styles.append(MessageStyle(
            offset=cmd_start_offset,
            length=cmd_length,
            style="color",
            color="#15a85f", # Xanh ngọc bích cực đẹp
            auto_format=False
        ))
        
        styles.append(MessageStyle(
            offset=cmd_start_offset,
            length=cmd_length,
            style="bold", # Cách set in đậm chuẩn của zlapi
            auto_format=False
        ))
        
        # 4. Cộng dồn nội dung vào final_text sau khi đã chốt toạ độ offset
        final_text += f"{prefix}{cmd_name}\n{desc_line}{syntax_line}{countdown_line}"

    if total_pages > 1:
        footer = f"Trang {current_page}/{total_pages}. Dùng ,command [số trang]"
        final_text += footer

    client.replyMessage(
        Message(text=final_text.strip(), style=MultiMsgStyle(styles)),
        message_object, thread_id, thread_type, ttl=60000
    )

def PTA():
    return {
        'command': handle_menu_command,
        'cmd': handle_menu_command 
    }