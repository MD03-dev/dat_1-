from zlapi.models import Message, ZaloAPIException, MultiMsgStyle, MessageStyle
from config import ADMIN, IMEI
import time

des = {
    'version': "1.4.0",
    'credits': "Hoàng Khánh Prime",
    'description': "Lệnh rời nhóm + reaction tin nhắn",
    'power': "Admin"
}

ADMIN_ID = ADMIN

def is_admin(author_id):
    return author_id == ADMIN_ID

def handle_leave_command(message, message_object, thread_id, thread_type, author_id, client):

    # Kiểm tra quyền admin
    if not is_admin(author_id):
        msg = "❌ Bạn không có quyền sử dụng lệnh này!"
        client.replyMessage(
            Message(text=msg),
            message_object,
            thread_id,
            thread_type
        )
        return

    try:

        # ⭐ Thả reaction vào tin nhắn ra lệnh
        try:
            client.reactMessage(
                "👋",
                message_object,
                thread_id,
                thread_type
            )
        except:
            pass

        # Style thông báo
        leave_styles = MultiMsgStyle([
            MessageStyle(offset=0, length=10000, style="color", color="#db342e", auto_format=False),
            MessageStyle(offset=0, length=10000, style="bold", size="100000", auto_format=False)
        ])

        goodbye = Message(
            text=" /-flag Bai mấy em guộc xin phép rời nhóm.Chúc AE ở lại vui vẻ!",
            style=leave_styles
        )

        client.sendMessage(
            goodbye,
            thread_id,
            thread_type,
            ttl=20000
        )

        # Delay để mọi người đọc
        time.sleep(2)

        # Bot rời nhóm
        client.leaveGroup(thread_id, imei=IMEI)

    except ZaloAPIException as e:
        client.replyMessage(
            Message(text=f"⚠️ ZaloAPI Error: {str(e)}"),
            message_object,
            thread_id,
            thread_type
        )

    except Exception as e:
        client.replyMessage(
            Message(text=f"⚠️ Error: {str(e)}"),
            message_object,
            thread_id,
            thread_type
        )

def PTA():
    return {
        'leave': handle_leave_command,
        'bai': handle_leave_command
    }