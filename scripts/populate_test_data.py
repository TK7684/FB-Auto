"""
Populate test data for dashboard verification.
Creates status files and activity log with realistic sample data.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.status_logger import get_status_logger

logger = get_status_logger()

# Simulate bot statuses
logger.update_bot_status(
    bot_type="comment",
    bot_name="Fast Responder",
    status="active",
    processed_count=142,
    reply_count=38,
    last_action="Scanning 3 posts"
)

logger.update_bot_status(
    bot_type="chat",
    bot_name="Chat Operator",
    status="active",
    processed_count=67,
    reply_count=21,
    last_action="Monitoring inbox"
)

logger.update_bot_status(
    bot_type="post",
    bot_name="FB Auto-Poster",
    status="offline",
    processed_count=0,
    reply_count=0,
    last_action="Idle"
)

# Simulate recent activity
activities = [
    ("Fast Responder", "comment_reply", "สมปอง ม.", "สนใจครีมลดจุดด่างดำ", "สวัสดีค่ะคุณสมปอง ลองดูตัวนี้นะคะ"),
    ("Fast Responder", "comment_reply", "นิดา ก.", "ราคาเท่าไรคะ", "ราคา 590 บาทค่ะ มีโปรโมชั่นอยู่นะคะ"),
    ("Chat Operator", "dm_reply", "ศรีสุดา พ.", "ส่งได้กี่วันคะ", "ส่งภายใน 1-2 วันทำการค่ะ"),
    ("Fast Responder", "comment_reply", "วรรณา อ.", "มีรีวิวมั้ยคะ", "มีค่ะ ลองดูรีวิวจากลูกค้าได้ที่ลิงก์นี้เลยค่ะ"),
    ("Fast Responder", "comment_reply", "ธนา ส.", "สั่ง 2 ชิ้นลดมั้ย", "สั่ง 2 ชิ้นลด 10% ค่ะ"),
]

for bot, action, user, msg, reply in activities:
    logger.log_activity(
        bot_name=bot,
        action=action,
        user_name=user,
        user_message=msg,
        bot_reply=reply,
        status="success"
    )

print("Test data populated successfully!")
print("- data/status_comment.json")
print("- data/status_chat.json")
print("- data/status_post.json")
print("- data/activity_log.json")
