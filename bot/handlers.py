import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus
from bot.moderation import get_reason, is_admin

log = logging.getLogger(__name__)

async def admin_required(update, context):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user or not update.effective_chat:
        return False
    try:
        member = await context.bot.get_chat_member(update.effective_chat.id, user.id)
        allowed = member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        allowed = False
    if not allowed:
        await msg.reply_text("Perintah ini hanya untuk admin grup.")
    return allowed

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Halo! Saya AntiGCastBot. Tambahkan saya ke grup dan jadikan admin "
        "dengan izin menghapus pesan serta membatasi anggota. Gunakan /help."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Perintah:\n"
        "/status - status proteksi\n"
        "/settings - pengaturan grup\n"
        "/antigcast on|off - deteksi flood, forward beruntun, pesan berulang\n"
        "/antispam on|off - deteksi tautan dan mention massal\n"
        "/setlimit 6 - batas pesan per jendela waktu\n"
        "/whitelist - whitelist anggota yang di-reply\n"
        "/unwhitelist - hapus whitelist anggota yang di-reply\n"
        "/warn - beri peringatan kepada anggota yang di-reply\n\n"
        "Catatan: bot hanya memoderasi grup tempat bot ditambahkan. "
        "Bot tidak mengirim broadcast massal dan tidak melewati pembatasan Telegram."
    )

def get_db_cfg(update, context):
    db, cfg = context.bot_data["db"], context.bot_data["config"]
    chat_id = update.effective_chat.id
    db.ensure_chat(chat_id, cfg)
    return db, db.settings(chat_id)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db, s = get_db_cfg(update, context)
    await update.effective_message.reply_text(
        f"Anti-GCast: {'ON' if s['gcast_enabled'] else 'OFF'}\n"
        f"Anti-Spam: {'ON' if s['spam_enabled'] else 'OFF'}\n"
        f"Batas pesan: {s['message_limit']} per {s['window_seconds']} detik"
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await status(update, context)

async def toggle(update, context, column, label):
    if update.effective_chat.type == "private":
        await update.effective_message.reply_text("Gunakan perintah ini di grup.")
        return
    if not await admin_required(update, context):
        return
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.effective_message.reply_text(f"Format: /{label.lower()} on atau off")
        return
    db, _ = get_db_cfg(update, context)
    enabled = context.args[0].lower() == "on"
    db.set_flag(update.effective_chat.id, column, enabled)
    await update.effective_message.reply_text(f"{label}: {'ON' if enabled else 'OFF'}")

async def toggle_gcast(update, context):
    await toggle(update, context, "gcast_enabled", "AntiGCast")

async def toggle_spam(update, context):
    await toggle(update, context, "spam_enabled", "AntiSpam")

async def set_limit(update, context):
    if not await admin_required(update, context):
        return
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Format: /setlimit 6 (rentang 3-30)")
        return
    limit = int(context.args[0])
    if not 3 <= limit <= 30:
        await update.effective_message.reply_text("Batas harus antara 3 dan 30.")
        return
    db, _ = get_db_cfg(update, context)
    db.set_limit(update.effective_chat.id, limit)
    await update.effective_message.reply_text(f"Batas pesan diperbarui menjadi {limit}.")

async def replied_user(update):
    msg = update.effective_message
    if not msg.reply_to_message or not msg.reply_to_message.from_user:
        await msg.reply_text("Balas pesan anggota yang dimaksud, lalu jalankan perintah.")
        return None
    return msg.reply_to_message.from_user

async def whitelist(update, context):
    if not await admin_required(update, context):
        return
    user = await replied_user(update)
    if user:
        db, _ = get_db_cfg(update, context)
        db.add_whitelist(update.effective_chat.id, user.id)
        await update.effective_message.reply_text(f"{user.full_name} masuk whitelist.")

async def unwhitelist(update, context):
    if not await admin_required(update, context):
        return
    user = await replied_user(update)
    if user:
        db, _ = get_db_cfg(update, context)
        removed = db.remove_whitelist(update.effective_chat.id, user.id)
        await update.effective_message.reply_text("Whitelist dihapus." if removed else "Anggota tidak ada di whitelist.")

async def warn_command(update, context):
    if not await admin_required(update, context):
        return
    user = await replied_user(update)
    if not user:
        return
    db, cfg = get_db_cfg(update, context)
    count = db.add_warning(update.effective_chat.id, user.id, "peringatan manual oleh admin")
    await update.effective_message.reply_text(f"Peringatan untuk {user.full_name}: {count}/{cfg.warn_limit}")
    if count >= cfg.warn_limit:
        until = datetime.now(timezone.utc) + timedelta(minutes=cfg.mute_minutes)
        try:
            await context.bot.restrict_chat_member(
                update.effective_chat.id, user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
            db.clear_warnings(update.effective_chat.id, user.id)
            await update.effective_message.reply_text(
                f"{user.full_name} dibatasi selama {cfg.mute_minutes} menit setelah mencapai batas warning."
            )
        except Exception as e:
            log.warning("Gagal membatasi anggota: %s", e)
            await update.effective_message.reply_text("Gagal membatasi anggota. Pastikan bot admin dengan izin Restrict Members.")

async def moderation_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not user or user.is_bot or chat.type == "private":
        return
    db, settings = get_db_cfg(update, context)
    if db.is_whitelisted(chat.id, user.id):
        return
    if await is_admin(context.bot, chat.id, user.id):
        return
    reason = get_reason(msg, settings)
    if not reason:
        return
    try:
        await msg.delete()
    except Exception as e:
        log.info("Tidak dapat menghapus pesan: %s", e)
    count = db.add_warning(chat.id, user.id, reason)
    cfg = context.bot_data["config"]
    try:
        await context.bot.send_message(
            chat.id, f"⚠️ {user.mention_html()} mendapat peringatan {count}/{cfg.warn_limit}.\nAlasan: {reason}",
            parse_mode="HTML",
        )
    except Exception:
        pass
    if count >= cfg.warn_limit:
        until = datetime.now(timezone.utc) + timedelta(minutes=cfg.mute_minutes)
        try:
            await context.bot.restrict_chat_member(
                chat.id, user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until,
            )
            db.clear_warnings(chat.id, user.id)
            await context.bot.send_message(chat.id, f"Anggota dibatasi selama {cfg.mute_minutes} menit.")
        except Exception as e:
            log.warning("Gagal menerapkan mute: %s", e)
