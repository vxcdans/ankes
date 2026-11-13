import re
import time
from collections import defaultdict, deque
from telegram.constants import ChatMemberStatus

# Per-process burst tracking. Persistent moderation history is stored in SQLite.
_activity = defaultdict(deque)
_last_text = {}

URL_RE = re.compile(r"(https?://|www\\.|t\\.me/)", re.I)

def get_reason(message, settings):
    text = message.text or message.caption or ""
    user_id = message.from_user.id if message.from_user else 0
    chat_id = message.chat_id
    now = time.monotonic()
    key = (chat_id, user_id)
    bucket = _activity[key]
    while bucket and now - bucket[0] > settings["window_seconds"]:
        bucket.popleft()
    bucket.append(now)

    if settings["gcast_enabled"]:
        if len(bucket) > settings["message_limit"]:
            return "broadcast/flood: terlalu banyak pesan dalam waktu singkat"
        if message.forward_origin is not None:
            return "pesan forward beruntun"
        normalized = re.sub(r"\\s+", " ", text).strip().lower()
        if normalized and _last_text.get(key) == normalized:
            return "pesan yang sama dikirim berulang"
        if normalized:
            _last_text[key] = normalized

    if settings["spam_enabled"]:
        entities = list(message.entities or []) + list(message.caption_entities or [])
        mentions = sum(1 for e in entities if e.type in ("mention", "text_mention"))
        if mentions >= 5:
            return "mention massal"
        if len(URL_RE.findall(text)) >= 3:
            return "spam tautan"
    return None

async def is_admin(bot, chat_id, user_id):
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False
