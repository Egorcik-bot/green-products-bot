import logging
import os
import sqlite3
from datetime import date
from typing import Optional

import aiosqlite

DAILY_SCAN_LIMIT = 3
REFERRAL_BONUS_SCANS = 5

# Safety-mode DB columns (the keys of the `user_modes` dict used by the analyzer).
MODE_COLUMNS = ("mode_pregnancy", "mode_acne", "mode_hair_clean")

# Columns that must exist on the `users` table. Used by the lightweight migration so an
# existing ingredients.db is upgraded in place (never deleted). Note: SQLite cannot add a column
# with a non-constant default, so `created_at` is added without one and backfilled afterwards.
USER_COLUMNS = {
    "language": "TEXT NOT NULL DEFAULT 'en'",
    "allergies": "TEXT NOT NULL DEFAULT ''",
    "daily_scans": f"INTEGER NOT NULL DEFAULT {DAILY_SCAN_LIMIT}",
    "last_reset_date": "TEXT NOT NULL DEFAULT ''",  # YYYY-MM-DD
    "mode_pregnancy": "INTEGER NOT NULL DEFAULT 0",
    "mode_acne": "INTEGER NOT NULL DEFAULT 0",
    "mode_hair_clean": "INTEGER NOT NULL DEFAULT 0",
    "bonus_scans": "INTEGER NOT NULL DEFAULT 0",  # never reset at midnight
    "referred_by": "INTEGER DEFAULT NULL",
    "referral_rewarded": "INTEGER NOT NULL DEFAULT 0",  # 0 = pending, 1 = rewarded
    "referrals_count": "INTEGER NOT NULL DEFAULT 0",
    "username": "TEXT DEFAULT NULL",
    "first_name": "TEXT DEFAULT NULL",
    "last_seen_date": "TEXT NOT NULL DEFAULT ''",  # YYYY-MM-DD, drives "active users today"
    "created_at": "DATETIME",
}

# Extra `scans_history` columns (used to render the /history list without parsing the report).
HISTORY_COLUMNS = {
    "product_name": "TEXT",
    "score": "INTEGER",
    "traffic_light": "TEXT",
}


def _today() -> str:
    return date.today().isoformat()


class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        # Cloud deployments point DB_PATH at a persistent volume (e.g. /data/ingredients.db).
        self.db_path = db_path or os.getenv("DB_PATH") or "ingredients.db"

    # -----------------------------------------------------
    # Schema & migrations
    # -----------------------------------------------------
    async def init_db(self):
        """Creates tables if missing and migrates existing ones in place."""
        parent = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(parent, exist_ok=True)  # e.g. a freshly mounted /data volume
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scanned_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    product_text TEXT,
                    safety_score INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL DEFAULT 'en',
                    allergies TEXT NOT NULL DEFAULT '',
                    daily_scans INTEGER NOT NULL DEFAULT 3,
                    last_reset_date TEXT NOT NULL DEFAULT '',
                    mode_pregnancy INTEGER NOT NULL DEFAULT 0,
                    mode_acne INTEGER NOT NULL DEFAULT 0,
                    mode_hair_clean INTEGER NOT NULL DEFAULT 0,
                    bonus_scans INTEGER NOT NULL DEFAULT 0,
                    referred_by INTEGER DEFAULT NULL,
                    referral_rewarded INTEGER NOT NULL DEFAULT 0,
                    referrals_count INTEGER NOT NULL DEFAULT 0,
                    username TEXT DEFAULT NULL,
                    first_name TEXT DEFAULT NULL,
                    last_seen_date TEXT NOT NULL DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS scans_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ai_result TEXT,
                    product_name TEXT,
                    score INTEGER,
                    traffic_light TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    telegram_payment_charge_id TEXT UNIQUE NOT NULL,
                    payload TEXT NOT NULL,
                    stars_amount INTEGER NOT NULL,
                    scans_added INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_scans_history_user ON scans_history (user_id)"
            )
            await self._migrate_table(db, "users", USER_COLUMNS)
            await self._migrate_table(db, "scans_history", HISTORY_COLUMNS)
            await db.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
            await db.commit()
            logging.info("Database initialized successfully.")

    @staticmethod
    async def _migrate_table(db: aiosqlite.Connection, table: str, columns: dict):
        """ALTER TABLE ... ADD COLUMN for any missing columns (upgrades an existing DB in place)."""
        async with db.execute(f"PRAGMA table_info({table})") as cursor:
            existing = {row[1] async for row in cursor}
        for column, definition in columns.items():
            if column not in existing:
                await db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
                logging.info("Migration: added column %s.%s", table, column)

    # -----------------------------------------------------
    # Users
    # -----------------------------------------------------
    async def touch_user(
        self, user_id: int, username: Optional[str], first_name: Optional[str], today: Optional[str] = None
    ) -> bool:
        """
        Creates the user if needed and keeps username / first_name / last_seen_date fresh without
        touching settings or limits. Returns True if the user was created by this call (brand new).
        """
        today = today or _today()
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, last_seen_date) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, today),
            )
            is_new = cursor.rowcount > 0
            if not is_new:
                await db.execute(
                    "UPDATE users SET username = ?, first_name = ?, last_seen_date = ? "
                    "WHERE user_id = ? AND (username IS NOT ? OR first_name IS NOT ? OR last_seen_date != ?)",
                    (username, first_name, today, user_id, username, first_name, today),
                )
            await db.commit()
            return is_new

    async def ensure_user(self, user_id: int):
        """Creates the user row with defaults if it does not exist yet."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.commit()

    async def reset_user(self, user_id: int):
        """Resets language / allergies to defaults (used by /start). Limits and balances are kept."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (user_id, language, allergies) VALUES (?, 'en', '') "
                "ON CONFLICT(user_id) DO UPDATE SET language = 'en', allergies = ''",
                (user_id,),
            )
            await db.commit()

    async def set_language(self, user_id: int, language: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (user_id, language) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET language = excluded.language",
                (user_id, language),
            )
            await db.commit()

    async def set_allergies(self, user_id: int, allergies: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO users (user_id, allergies) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET allergies = excluded.allergies",
                (user_id, allergies),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[dict]:
        """Language, allergies and the safety-mode flags ({'mode_pregnancy': bool, ...})."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT language, allergies, {', '.join(MODE_COLUMNS)} FROM users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
        if row is None:
            return None
        return {
            "language": row[0],
            "allergies": row[1],
            "modes": {col: bool(row[2 + i]) for i, col in enumerate(MODE_COLUMNS)},
        }

    async def toggle_mode(self, user_id: int, mode: str) -> bool:
        """Flips one safety mode and returns its new state. `mode` must be a known column."""
        if mode not in MODE_COLUMNS:
            raise ValueError(f"Unknown safety mode: {mode}")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.execute(f"UPDATE users SET {mode} = 1 - {mode} WHERE user_id = ?", (user_id,))
            async with db.execute(f"SELECT {mode} FROM users WHERE user_id = ?", (user_id,)) as cursor:
                new_state = bool((await cursor.fetchone())[0])
            await db.commit()
            return new_state

    # -----------------------------------------------------
    # Scan allowance (daily -> bonus -> blocked) & refunds
    # -----------------------------------------------------
    async def consume_scan(
        self, user_id: int, is_admin: bool = False, today: Optional[str] = None
    ) -> tuple[bool, str]:
        """
        Spends one scan. Returns (allowed, source) where source is 'admin', 'daily', 'bonus' or 'none'.
        1. daily_scans is reset to the limit when last_reset_date != today.
        2. Admins are always allowed and nothing is deducted.
        3. Otherwise daily_scans is used first, then bonus_scans (which never reset at midnight).
        Every write is a single atomic UPDATE, so concurrent requests can't overspend.
        """
        today = today or _today()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            await db.execute(
                "UPDATE users SET daily_scans = ?, last_reset_date = ? "
                "WHERE user_id = ? AND last_reset_date != ?",
                (DAILY_SCAN_LIMIT, today, user_id, today),
            )
            if is_admin:
                await db.commit()
                return True, "admin"
            cursor = await db.execute(
                "UPDATE users SET daily_scans = daily_scans - 1 WHERE user_id = ? AND daily_scans > 0",
                (user_id,),
            )
            if cursor.rowcount > 0:
                await db.commit()
                return True, "daily"
            cursor = await db.execute(
                "UPDATE users SET bonus_scans = bonus_scans - 1 WHERE user_id = ? AND bonus_scans > 0",
                (user_id,),
            )
            allowed = cursor.rowcount > 0
            await db.commit()
            return (True, "bonus") if allowed else (False, "none")

    async def refund_scan(self, user_id: int, source: str):
        """Gives back the scan to where it came from ('daily' is capped at the limit, 'admin' is a no-op)."""
        if source not in ("daily", "bonus"):
            return
        async with aiosqlite.connect(self.db_path) as db:
            if source == "daily":
                await db.execute(
                    "UPDATE users SET daily_scans = MIN(daily_scans + 1, ?) WHERE user_id = ?",
                    (DAILY_SCAN_LIMIT, user_id),
                )
            else:
                await db.execute(
                    "UPDATE users SET bonus_scans = bonus_scans + 1 WHERE user_id = ?", (user_id,)
                )
            await db.commit()

    async def add_bonus_scans(self, user_id: int, amount: int) -> Optional[int]:
        """Adds bonus scans; returns the new balance, or None if the user does not exist."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE users SET bonus_scans = bonus_scans + ? WHERE user_id = ?", (amount, user_id)
            )
            if cursor.rowcount == 0:
                return None
            async with db.execute("SELECT bonus_scans FROM users WHERE user_id = ?", (user_id,)) as cur:
                balance = (await cur.fetchone())[0]
            await db.commit()
            return balance

    # -----------------------------------------------------
    # Referrals
    # -----------------------------------------------------
    async def set_referrer(self, user_id: int, referrer_id: int) -> bool:
        """
        Attaches a referrer. Refused for self-referral, unknown referrers and users that already have
        one. (The caller only invokes this for brand-new users.)
        """
        if referrer_id == user_id:
            return False
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE users SET referred_by = ? WHERE user_id = ? AND referred_by IS NULL "
                "AND EXISTS (SELECT 1 FROM users WHERE user_id = ?)",
                (referrer_id, user_id, referrer_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def reward_referral_if_due(self, user_id: int) -> Optional[int]:
        """
        Called after a user's successful scan. If they were referred and the reward is still pending,
        atomically marks it rewarded and gives +REFERRAL_BONUS_SCANS to both sides.
        Returns the referrer's id when a reward was paid, otherwise None.
        """
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE users SET referral_rewarded = 1, bonus_scans = bonus_scans + ? "
                "WHERE user_id = ? AND referred_by IS NOT NULL AND referral_rewarded = 0",
                (REFERRAL_BONUS_SCANS, user_id),
            )
            if cursor.rowcount == 0:
                await db.commit()
                return None
            async with db.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,)) as cur:
                referrer_id = (await cur.fetchone())[0]
            await db.execute(
                "UPDATE users SET bonus_scans = bonus_scans + ?, referrals_count = referrals_count + 1 "
                "WHERE user_id = ?",
                (REFERRAL_BONUS_SCANS, referrer_id),
            )
            await db.commit()
            return referrer_id

    # -----------------------------------------------------
    # Profile
    # -----------------------------------------------------
    async def get_profile(self, user_id: int) -> dict:
        """Preferences, balances, referral stats and the all-time scan count for /profile."""
        await self.ensure_user(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT language, allergies, daily_scans, last_reset_date, bonus_scans, referrals_count, "
                f"{', '.join(MODE_COLUMNS)} FROM users WHERE user_id = ?",
                (user_id,),
            ) as cursor:
                row = await cursor.fetchone()
            async with db.execute(
                "SELECT COUNT(*) FROM scans_history WHERE user_id = ?", (user_id,)
            ) as cursor:
                total = (await cursor.fetchone())[0]
        return {
            "language": row[0],
            "allergies": row[1],
            "daily_scans": row[2],
            "last_reset_date": row[3],
            "bonus_scans": row[4],
            "referrals_count": row[5],
            "modes": {col: bool(row[6 + i]) for i, col in enumerate(MODE_COLUMNS)},
            "total_scans": total,
        }

    # -----------------------------------------------------
    # Payments (Telegram Stars)
    # -----------------------------------------------------
    async def record_payment(
        self, user_id: int, charge_id: str, payload: str, stars: int, scans: int
    ) -> Optional[int]:
        """
        Idempotently records a payment and credits the bonus scans. Returns the new bonus balance, or
        None when this telegram_payment_charge_id was already processed (nothing is credited twice).
        """
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
            try:
                await db.execute(
                    "INSERT INTO payments (user_id, telegram_payment_charge_id, payload, stars_amount, scans_added) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (user_id, charge_id, payload, stars, scans),
                )
            except sqlite3.IntegrityError:
                await db.rollback()
                return None
            await db.execute(
                "UPDATE users SET bonus_scans = bonus_scans + ? WHERE user_id = ?", (scans, user_id)
            )
            async with db.execute("SELECT bonus_scans FROM users WHERE user_id = ?", (user_id,)) as cur:
                balance = (await cur.fetchone())[0]
            await db.commit()
            return balance

    # -----------------------------------------------------
    # Scan history
    # -----------------------------------------------------
    async def log_scan(self, user_id: int, product_text: str, safety_score: int):
        """Legacy per-scan log (ingredient names + score)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO scanned_products (user_id, product_text, safety_score) VALUES (?, ?, ?)",
                (user_id, product_text, safety_score),
            )
            await db.commit()

    async def add_scan_history(
        self,
        user_id: int,
        ai_result: str,
        product_name: Optional[str] = None,
        score: Optional[int] = None,
        traffic_light: Optional[str] = None,
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "INSERT INTO scans_history (user_id, ai_result, product_name, score, traffic_light) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, ai_result, product_name, score, traffic_light),
            )
            await db.commit()
            return cursor.lastrowid

    async def get_history(self, user_id: int, limit: int = 8, scored_only: bool = False) -> list[dict]:
        """Latest scans of a user (newest first); timestamps converted to local time."""
        where = "user_id = ?" + (" AND score IS NOT NULL" if scored_only else "")
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, datetime(timestamp, 'localtime'), product_name, score, traffic_light "
                f"FROM scans_history WHERE {where} ORDER BY id DESC LIMIT ?",
                (user_id, limit),
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            {"id": r[0], "timestamp": r[1], "product_name": r[2], "score": r[3], "traffic_light": r[4]}
            for r in rows
        ]

    async def get_scan(self, user_id: int, scan_id: int) -> Optional[dict]:
        """One scan including its stored report; only returned to the user who owns it."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, datetime(timestamp, 'localtime'), product_name, score, traffic_light, ai_result "
                "FROM scans_history WHERE id = ? AND user_id = ?",
                (scan_id, user_id),
            ) as cursor:
                r = await cursor.fetchone()
        if r is None:
            return None
        return {
            "id": r[0], "timestamp": r[1], "product_name": r[2], "score": r[3],
            "traffic_light": r[4], "ai_result": r[5],
        }

    async def get_history_item(self, user_id: int, scan_id: int) -> Optional[str]:
        """Stored report text of one scan; only returned to the user who owns it."""
        scan = await self.get_scan(user_id, scan_id)
        return scan["ai_result"] if scan else None

    # -----------------------------------------------------
    # Admin: stats, lookups, exports
    # -----------------------------------------------------
    async def get_admin_stats(self, today: Optional[str] = None) -> dict:
        today = today or _today()
        async with aiosqlite.connect(self.db_path) as db:
            async def scalar(sql: str, params: tuple = ()) -> int:
                async with db.execute(sql, params) as cursor:
                    return (await cursor.fetchone())[0]

            users = await scalar("SELECT COUNT(*) FROM users")
            new_today = await scalar(
                "SELECT COUNT(*) FROM users WHERE date(created_at, 'localtime') = ?", (today,)
            )
            active_today = await scalar("SELECT COUNT(*) FROM users WHERE last_seen_date = ?", (today,))
            scans_today = await scalar(
                "SELECT COUNT(*) FROM scans_history WHERE date(timestamp, 'localtime') = ?", (today,)
            )
            scans_total = await scalar("SELECT COUNT(*) FROM scans_history")
            referrals = await scalar("SELECT COUNT(*) FROM users WHERE referral_rewarded = 1")
            stars = await scalar("SELECT COALESCE(SUM(stars_amount), 0) FROM payments")
            async with db.execute(
                "SELECT language, COUNT(*) FROM users GROUP BY language ORDER BY COUNT(*) DESC"
            ) as cursor:
                languages = {row[0]: row[1] async for row in cursor}
        return {
            "users": users, "new_today": new_today, "active_today": active_today,
            "scans_today": scans_today, "scans_total": scans_total, "languages": languages,
            "referrals": referrals, "stars": stars,
        }

    async def get_recent_scans(self, limit: int = 5) -> list[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT h.id, h.user_id, u.username, u.first_name, datetime(h.timestamp, 'localtime'), "
                "h.score, h.traffic_light, h.ai_result "
                "FROM scans_history h LEFT JOIN users u ON u.user_id = h.user_id "
                "ORDER BY h.id DESC LIMIT ?",
                (limit,),
            ) as cursor:
                rows = await cursor.fetchall()
        return [
            {"id": r[0], "user_id": r[1], "username": r[2], "first_name": r[3], "timestamp": r[4],
             "score": r[5], "traffic_light": r[6], "ai_result": r[7]}
            for r in rows
        ]

    async def export_users(self) -> tuple[list[str], list[tuple]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT * FROM users ORDER BY user_id") as cursor:
                columns = [d[0] for d in cursor.description]
                rows = await cursor.fetchall()
        return columns, rows

    async def export_scans(self) -> tuple[list[str], list[tuple]]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT h.id AS scan_id, h.user_id, u.username, datetime(h.timestamp, 'localtime') AS timestamp, "
                "h.score, h.traffic_light, h.ai_result "
                "FROM scans_history h LEFT JOIN users u ON u.user_id = h.user_id ORDER BY h.id"
            ) as cursor:
                columns = [d[0] for d in cursor.description]
                rows = await cursor.fetchall()
        return columns, rows

    async def get_all_user_ids(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT user_id FROM users ORDER BY user_id") as cursor:
                return [row[0] async for row in cursor]

    async def find_user(self, identifier: str) -> Optional[dict]:
        """Looks a user up by numeric id or by @username (case-insensitive)."""
        identifier = identifier.strip()
        async with aiosqlite.connect(self.db_path) as db:
            if identifier.lstrip("-").isdigit():
                sql, param = "SELECT user_id, username, first_name FROM users WHERE user_id = ?", int(identifier)
            else:
                sql = "SELECT user_id, username, first_name FROM users WHERE lower(username) = lower(?)"
                param = identifier.lstrip("@")
            async with db.execute(sql, (param,)) as cursor:
                row = await cursor.fetchone()
        return {"user_id": row[0], "username": row[1], "first_name": row[2]} if row else None
