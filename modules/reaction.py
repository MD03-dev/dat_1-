from zlapi.models import Message, MultiMsgStyle, MessageStyle
import time
import random
from config import ADMIN

# List of reactions
reaction_all = [

    "😀", "😃", "😄", "😁", "😆", "😅", "😂", "🤣", "😊", "😇", "🙂", "🙃", "😉", "😌", "😍", "🥰", "😘", "😗", "😙", "😚", "😋", "😛", "😜", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧", "😵", "🤯", "🤠", "🥳", "😎", "🤓", "🧐", "😕", "😟", "🙁", "😮", "😯", "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡", "😠", "🤬", "😈", "👿", "💀", "☠️", "💩", "🤡", "👹", "👺", "👻", "👽", "👾", "🤖",


    "👋", "🤚", "🖐", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞", "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍", "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏", "✍️", "💅", "🤳", "💪", "🦾", "🦵", "🦿", "🦶", "👂", "🦻", "👃", "👀", "👁️", "👅", "👄",

  
    "👶", "👧", "🧒", "👦", "👩", "🧑", "👨", "👩‍🦱", "👨‍🦱", "👩‍🦰", "👨‍🦰", "👱‍♀️", "👱‍♂️", "👩‍🦳", "👨‍🦳", "👩‍🦲", "👨‍🦲", "🧔", "👵", "👴", "👲", "👳‍♀️", "👳‍♂️", "🧕", "👮‍♀️", "👮‍♂️", "👷‍♀️", "👷‍♂️", "💂‍♀️", "💂‍♂️", "🕵️‍♀️", "🕵️‍♂️", "👩‍⚕️", "👨‍⚕️", "👩‍🌾", "👨‍🌾", "👩‍🍳", "👨‍🍳", "👩‍🎓", "👨‍🎓", "👩‍🎤", "👨‍🎤", "👩‍🏫", "👨‍🏫", "👩‍🏭", "👨‍🏭", "👩‍💻", "👨‍💻", "👩‍💼", "👨‍💼", "👩‍🔧", "👨‍🔧", "👩‍🔬", "👨‍🔬", "👩‍🎨", "👨‍🎨", "👩‍🚒", "👨‍🚒", "👩‍✈️", "👨‍✈️", "👩‍🚀", "👨‍🚀", "👩‍⚖️", "👨‍⚖️", "👰", "🤵", "👸", "🤴", "👼", "🤰", "🤱", "👩‍🍼", "👨‍🍼", "🙇‍♀️", "🙇‍♂️", "💁‍♀️", "💁‍♂️", "🙅‍♀️", "🙅‍♂️", "🙆‍♀️", "🙆‍♂️", "🙋‍♀️", "🙋‍♂️", "🧏‍♀️", "🧏‍♂️", "🙍‍♀️", "🙍‍♂️", "🙎‍♀️", "🙎‍♂️",

  
    "🐵", "🐒", "🦍", "🦧", "🐶", "🐕", "🦮", "🐕‍🦺", "🐩", "🐺", "🦊", "🦝", "🐱", "🐈", "🐈‍⬛", "🦁", "🐯", "🐅", "🐆", "🐴", "🐎", "🦄", "🦓", "🦌", "🐮", "🐂", "🐃", "🐄", "🐷", "🐖", "🐗", "🐽", "🐏", "🐑", "🐐", "🐪", "🐫", "🦙", "🦒", "🐘", "🦣", "🦏", "🦛", "🐭", "🐁", "🐀", "🐹", "🐰", "🐇", "🐿️", "🦫", "🦔", "🦇", "🐻", "🐻‍❄️", "🐨", "🐼", "🦥", "🦦", "🦨", "🦘", "🦡", "🐾", "🦃", "🐔", "🐓", "🐣", "🐤", "🐥", "🐦", "🐧", "🕊️", "🦅", "🦆", "🦢", "🦉", "🦤", "🪶", "🦩", "🦚", "🦜", "🐸", "🐊", "🐢", "🦎", "🐍", "🐲", "🐉", "🦕", "🦖", "🐳", "🐋", "🐬", "🦭", "🐟", "🐠", "🐡", "🦈", "🐙", "🐚", "🐌", "🦋", "🐛", "🐜", "🐝", "🪲", "🐞", "🦗", "🪳", "🕷️", "🕸️", "🦂", "🦟", "🪰", "🪱", "🦠",

   
    "🍇", "🍈", "🍉", "🍊", "🍋", "🍌", "🍍", "🥭", "🍎", "🍏", "🍐", "🍑", "🍒", "🍓", "🫐", "🥝", "🍅", "🍆", "🥑", "🥦", "🥬", "🥒", "🌶️", "🫑", "🌽", "🥕", "🫒", "🧄", "🧅", "🥔", "🍠", "🥐", "🥯", "🍞", "🥖", "🥨", "🧀", "🥚", "🍳", "🥓", "🥩", "🍗", "🍖", "🦴", "🌭", "🍔", "🍟", "🍕", "🌮", "🌯", "🥙", "🧆", "🥪", "🥫", "🍝", "🍜", "🍲", "🍛", "🍣", "🍤", "🍙", "🍚", "🍘", "🍥", "🥠", "🫓", "🥮", "🍢", "🍡", "🍧", "🍨", "🍦", "🥧", "🧁", "🍰", "🎂", "🍮", "🍭", "🍬", "🍫", "🍿", "🧂", "🥤", "🧃", "🧉", "🧊", "🍶", "🍺", "🍻", "🥂", "🍷", "🥃", "🍸", "🍹", "🧋", "🍾", "🍼", "🥛", "☕", "🍵", "🫖", "🧋", "🍶",

 
    "❤️", "🧡", "💛", "💚", "💙", "💜", "🤎", "🖤", "🤍", "💔", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️", "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐", "⛩️", "🕋", "🕌", "🛕", "🛳️", "⛴️", "🚢", "✈️", "🚀", "🛸", "🚁", "🚂", "🚆", "🚇", "🚊", "🚉", "🚖", "🚔", "🚍", "🚘", "🚛", "🚜", "🚲", "🛴", "🛵", "🏍️", "🛺", "🛹", "🛷", "⛷️", "🏂", "🏋️‍♀️", "🏋️‍♂️", "🏄‍♀️", "🏄‍♂️", "🏊‍♀️", "🏊‍♂️", "🤽‍♀️", "🤽‍♂️", "🚴‍♀️", "🚴‍♂️", "🚵‍♀️", "🚵‍♂️"
]


# Module description
des = {
    'version': "1.0.0",
    'credits': "Ha Huy Hoàng",
    'description': "Spam react",
    'power': "Quản trị viên bot"
}

# Dictionary to track spam status per thread
spam_active = {}

# Command handler for auto-spam random reactions with on/stop
def handle_react_command(message, message_object, thread_id, thread_type, author_id, client):

    if author_id not in ADMIN:
        client.replyMessage(
            Message(text="• Bạn không có quyền sử dụng lệnh này."),
            message_object, thread_id, thread_type, ttl=30000
        )
        return

    # Split the message to check for subcommands
    parts = message.lower().split()
    subcommand = parts[1] if len(parts) > 1 else ""

    if subcommand == "on":
        # Check if spam is already active in this thread
        if thread_id in spam_active and spam_active[thread_id]:
            client.replyMessage(Message(text="Spam react đang được bật!"), message_object, thread_id, thread_type)
            return

        # Mark spam as active for this thread
        spam_active[thread_id] = True

        # Infinite loop for auto-spam
        while spam_active.get(thread_id, False):
            action = random.choice(reaction_all)
            try:
                client.sendReaction(message_object, action, thread_id, thread_type, reactionType=75)
            except Exception as e:
                client.replyMessage(Message(text=f"Lỗi khi gửi phản ứng: {str(e)}. Đã dừng spam."), message_object, thread_id, thread_type)
                spam_active[thread_id] = False
                break

    elif subcommand == "stop":
        # Check if spam is active in this thread
        if thread_id in spam_active and spam_active[thread_id]:
            spam_active[thread_id] = False
        else:
            client.replyMessage(Message(text="Không có spam react nào đang chạy!"), message_object, thread_id, thread_type)

    else:
        # Default behavior or help message
        client.replyMessage(Message(text="Vui lòng sử dụng lệnh hợp lệ (vd: react on hoặc react stop)."), message_object, thread_id, thread_type)

# Module registration
def PTA():
    return {
        "react": handle_react_command
    }