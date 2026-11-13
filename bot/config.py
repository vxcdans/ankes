import os
from dataclasses import dataclass
from dotenv import load_dotenv

@dataclass(frozen=True)
class Config:
    bot_token: str
    db_path: str
    owner_id: int
    log_level: str
    default_window: int
    default_limit: int
    warn_limit: int
    mute_minutes: int

def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN belum diisi. Salin .env.example menjadi .env.")
    return Config(
        bot_token=token,
        db_path=os.getenv("DB_PATH", "data/antigcast.sqlite3"),
        owner_id=int(os.getenv("OWNER_ID", "0")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        default_window=int(os.getenv("DEFAULT_WINDOW_SECONDS", "10")),
        default_limit=int(os.getenv("DEFAULT_MESSAGE_LIMIT", "6")),
        warn_limit=int(os.getenv("WARN_LIMIT", "3")),
        mute_minutes=int(os.getenv("MUTE_MINUTES", "10")),
    )
