import aiosqlite
from datetime import datetime, timedelta

DB_PATH = "finance_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                subscription_until TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()

async def create_user(user_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
            (user_id, username)
        )
        await db.commit()

async def is_subscribed(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user[2]:
        return False
    sub_until = datetime.fromisoformat(user[2])
    return sub_until > datetime.now()

async def activate_subscription(user_id: int, days: int = 30):
    now = datetime.now()
    user = await get_user(user_id)

    if user and user[2]:
        current_end = datetime.fromisoformat(user[2])
        if current_end > now:
            new_end = current_end + timedelta(days=days)
        else:
            new_end = now + timedelta(days=days)
    else:
        new_end = now + timedelta(days=days)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET subscription_until = ? WHERE user_id = ?",
            (new_end.isoformat(), user_id)
        )
        await db.commit()
    return new_end