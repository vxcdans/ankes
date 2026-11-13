import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bot.config import load_config
from bot.database import Database
from bot.handlers import (
    start, help_command, status, settings_command, toggle_gcast,
    toggle_spam, set_limit, whitelist, unwhitelist, warn_command,
    moderation_message,
)

def main():
    cfg = load_config()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    db = Database(cfg.db_path)
    db.initialize()

    app = Application.builder().token(cfg.bot_token).build()
    app.bot_data["config"] = cfg
    app.bot_data["db"] = db

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("antigcast", toggle_gcast))
    app.add_handler(CommandHandler("antispam", toggle_spam))
    app.add_handler(CommandHandler("setlimit", set_limit))
    app.add_handler(CommandHandler("whitelist", whitelist))
    app.add_handler(CommandHandler("unwhitelist", unwhitelist))
    app.add_handler(CommandHandler("warn", warn_command))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL, moderation_message))

    logging.info("AntiGCastBot started")
    app.run_polling(allowed_updates=["message", "chat_member"])

if __name__ == "__main__":
    main()
