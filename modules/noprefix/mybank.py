from zlapi.models import Message
import os
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

des = {
    'version': "1.0.0",
    'credits': "</> Hoàng Khánh Prime",
    'description': "Lệnh gửi số tài khoản ngân hàng admin",
    'power': "Thành viên"
}

def handle_mybank_command(message, message_object, thread_id, thread_type, author_id, client):
    if message.strip().lower() != "mybank":
        client.sendMessage(
            Message(text="Sai cú pháp, sử dụng: mybank"),
            thread_id, thread_type, ttl=30000
        )
        return

    sent_message = None
    try:
        sent_message = client.sendMessage(
            Message(text="Đang lấy thông tin số tài khoản..."),
            thread_id, thread_type, ttl=30000
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi tin nhắn lấy thông tin tài khoản: {str(e)}")
        return

    if not sent_message:
        logger.error("Không nhận được phản hồi khi gửi tin nhắn lấy thông tin tài khoản.")
        return

    stats_message = """
========================
   ✨ 1056 001 193 🪪
========================
👤: Tên Tài Khoản Ngân Hàng
         </> Hoàng Khánh Prime
========================
📩: NỘI DUNG GIAO DỊCH
         Tên Zalo Bạn
========================
"""

    try:
        image_dir = "Image/bank"
        image_files = [f for f in os.listdir(image_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
        if image_files:
            random_image = random.choice(image_files)
            image_path = os.path.join(image_dir, random_image)
            client.sendLocalImage(
                imagePath=image_path,
                message=Message(text=stats_message),
                thread_id=thread_id,
                thread_type=thread_type,
                width=1080,
                height=1080,
                ttl=120000
            )
        else:
            logger.warning("Không có hình ảnh nào trong thư mục Image/bank.")
            client.sendMessage(
                Message(text=stats_message),
                thread_id, thread_type, ttl=60000
            )
    except Exception as e:
        logger.error(f"Lỗi khi gửi ảnh thống kê: {str(e)}")
        client.sendMessage(
            Message(text=stats_message),
            thread_id, thread_type, ttl=60000
        )

    icon_list = ["💵", "💴", "💶", "💳", "💵", "💴", "💶", "💳"]
    random_emojis = random.sample(icon_list, min(4, len(icon_list)))
    for emoji in random_emojis:
        try:
            client.sendReaction(
                message_object, emoji, thread_id, thread_type
            )
        except Exception as e:
            logger.error(f"Lỗi khi gửi phản ứng {emoji}: {str(e)}")

def PTA():
    return {
        'mybank': handle_mybank_command
    }