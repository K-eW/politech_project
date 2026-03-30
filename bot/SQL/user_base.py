import aiosqlite
import logging
from _user import *
from typing import Optional, Dict
import sqlite3
import os
import asyncio

logging.basicConfig(level=logging.INFO)


user_cache: Dict[str, User] = {}
_db_connection: Optional[aiosqlite.Connection] = None

BOT_MESSAGE_TABLE = "user_states"
DB_NAME = "SQL/user_database.sql"


BACKUP_DIR = "backups"
MAX_CACHE_AGE_HOURS = 24
MAX_CACHE_SIZE = 10000




async def get_db() -> aiosqlite.Connection:
    global _db_connection
    if _db_connection is None:
        _db_connection = await aiosqlite.connect(DB_NAME)
        _db_connection.row_factory = aiosqlite.Row
        await _db_connection.execute("PRAGMA journal_mode = WAL")
        await _db_connection.execute("PRAGMA synchronous = NORMAL")
        await _db_connection.execute("PRAGMA cache_size = 10000")
        await _db_connection.execute("PRAGMA temp_store = MEMORY")
        await _db_connection.execute("PRAGMA foreign_keys = ON")

    assert _db_connection is not None, "Database connection failed"
    return _db_connection


async def close_db():
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None



# --- Инициализация БД ---
async def init_db():
    db = await get_db()
    try:
        await db.execute(f'''
            CREATE TABLE IF NOT EXISTS {BOT_MESSAGE_TABLE} (
                chat_id INTEGER PRIMARY KEY,
                mode STRING)
        ''')

        await db.commit()
        logging.info("✅ База данных инициализирована")
    except Exception as e:
        logging.error(f"❌ Ошибка при инициализации БД: {e}")

def get_user_from_db(chat_id: str) -> Optional[User]:
    try:
        with sqlite3.connect(DB_NAME, timeout=5) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute(f'''
                SELECT 
                    chat_id, mode
                FROM {BOT_MESSAGE_TABLE}
                WHERE chat_id = ?
            ''', (int(chat_id),))

            row = cursor.fetchone()
            if not row:
                return None

            user_data = {
                'mode': row[1] or 0,
            }
            user = User.from_dict({'user_id': int(chat_id), **user_data})
            subjects = [r[0] for r in cursor.fetchall()]
            user._selected_subjects = subjects
            return user
    except Exception as e:
        logging.error(f"❌ Ошибка при синхронной загрузке пользователя {chat_id} из БД: {e}")
        return None

def get_user_state(chat_id: int) -> User:
    chat_id_str = str(chat_id)

    if chat_id_str in user_cache:
        cached = user_cache[chat_id_str]
        if cached is not None:
            if isinstance(cached, User):
                return cached
        else:
            logging.warning(f"⚠️ None в user_cache для {chat_id}")
            del user_cache[chat_id_str]

    user = get_user_from_db(chat_id_str)
    if user:
        user_cache[chat_id_str] = user
    else:
        user = User(user_id=chat_id)
        user_cache[chat_id_str] = user

    return user


async def load_users_into_cache():
    global user_cache
    user_cache = {}
    db = await get_db()
    loaded_count = 0

    try:
        async with db.execute(f'''
            SELECT 
                chat_id, mode
            FROM {BOT_MESSAGE_TABLE}
            LIMIT ?
        ''', (MAX_CACHE_SIZE,)) as cursor:
            async for row in cursor:
                chat_id = str(row['chat_id'])
                user_data = {
                    'user_id': row['chat_id'],
                    'mode': row['mode'] or 0,
                }
                user = User.from_dict(user_data)
                user_cache[chat_id] = user
                loaded_count += 1



        logging.info(f"✅ Загружено {loaded_count} активных пользователей в кэш (лимит: {MAX_CACHE_SIZE})")
    except Exception as e:
        logging.error(f"❌ Ошибка при загрузке пользователей: {e}")


async def save_user_to_data(chat_id: int):
    user_id_str = str(chat_id)
    user = user_cache.get(user_id_str)
    if not user:
        return

    db = await get_db()
    try:
        await db.execute(f'DELETE FROM {BOT_MESSAGE_TABLE} WHERE chat_id = ?', (int(user_id_str),))

        db_data = user.to_dict()
        await db.execute(f'''
            INSERT INTO {BOT_MESSAGE_TABLE} 
            (chat_id, mode)
            VALUES (?, ?)
        ''', (
            db_data['user_id'],
            db_data['mode']
        ))


        await db.commit()
    except Exception as e:
        logging.error(f"❌ Ошибка при сохранении пользователя {chat_id}: {e}")




async def init_user_base():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    await init_db()
    await load_users_into_cache()
    logging.info("🔁 Фоновая очистка кэша запущена")