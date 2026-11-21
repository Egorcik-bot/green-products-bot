import asyncio
import base64
import contextlib
import csv
import html
import io
import logging
import os
import re
from datetime import date
from typing import Any, Awaitable, Callable, Optional

from dotenv import load_dotenv
from aiogram import BaseMiddleware, Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    ReplyKeyboardMarkup,
    TelegramObject,
)
from openai import AsyncOpenAI

from analyzer import (
    analyze_image,
    analyze_inci_text,
    answer_product_question,
    build_system_prompt,
    compare_scans,
    evaluate,
    suggest_alternatives,
)
from database import (
    DAILY_SCAN_LIMIT,
    MODE_COLUMNS,
    REFERRAL_BONUS_SCANS,
    DatabaseManager,
)
from texts import TEXTS

# ---------------------------------------------------------
# Configuration & Setup
# ---------------------------------------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_MINI_MODEL = os.getenv("OPENAI_MINI_MODEL", "gpt-4o-mini")

# Admin identity: unlimited scans + access to /admin and /stats. Must be a numeric Telegram user ID.
_admin_raw = os.getenv("ADMIN_ID")
try:
    ADMIN_ID: Optional[int] = int(_admin_raw) if _admin_raw else None
except ValueError:
    raise ValueError("ADMIN_ID in the .env file must be an integer Telegram user ID.")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing from the .env file.")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing from the .env file.")
if ADMIN_ID is None:
    logging.getLogger(__name__).warning(
        "ADMIN_ID is not set - no admin features (/admin, /stats, unlimited scans) are available."
    )


def is_admin(user_id: int) -> bool:
    return ADMIN_ID is not None and user_id == ADMIN_ID


def today_str() -> str:
    """Current local date as YYYY-MM-DD (used for the daily limit reset)."""
    return date.today().isoformat()


# Initialize Router for aiogram 3.x
router = Router()

# Async OpenAI client (shared, reuses HTTP connections)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=60.0, max_retries=2)

TELEGRAM_MAX_LEN = 4096

# Instantiate the DB Manager globally so handlers can use it
db_manager = DatabaseManager()

# Tracks users created during the current update so /start can still detect brand-new users
# after the UserTrackingMiddleware runs.
_NEW_USERS_THIS_UPDATE: set[int] = set()
_CACHED_BOT_USERNAME: Optional[str] = None


class UserTrackingMiddleware(BaseMiddleware):
    """Keeps username, first_name and last_seen_date fresh in SQLite on every interaction."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user = getattr(event, "from_user", None)
        if tg_user is not None:
            try:
                is_new = await db_manager.touch_user(
                    tg_user.id, tg_user.username, tg_user.first_name, today_str()
                )
                if is_new:
                    _NEW_USERS_THIS_UPDATE.add(tg_user.id)
            except Exception:
                logging.debug("touch_user failed", exc_info=True)
        return await handler(event, data)


router.message.outer_middleware(UserTrackingMiddleware())
router.callback_query.outer_middleware(UserTrackingMiddleware())


async def get_bot_username(bot: Bot) -> str:
    global _CACHED_BOT_USERNAME
    if _CACHED_BOT_USERNAME:
        return _CACHED_BOT_USERNAME
    try:
        me = await bot.get_me()
        if me and me.username:
            _CACHED_BOT_USERNAME = me.username
            return _CACHED_BOT_USERNAME
    except Exception:
        logging.debug("get_me failed", exc_info=True)
    return "IngredientScannerBot"


# ---------------------------------------------------------
# Vision / Text LLM Wrappers & Report Formatting
# ---------------------------------------------------------
LIGHT_EMOJI = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

MAX_NAME_LEN = 80
MAX_NOTE_LEN = 220

# Telegram Stars packages: pack_key -> (scans_added, stars_amount)
STAR_PACKAGES: dict[str, tuple[int, int]] = {
    "pack_10": (10, 25),
    "pack_30": (30, 60),
}

# Heuristic for detecting pasted INCI ingredient lists vs casual chat
_INCI_KEYWORDS_RX = re.compile(
    r"\b(aqua|water|eau|glycerin|glycerine|parfum|fragrance|ingredients|ingrediente|состав|склад"
    r"|sodium|alcohol|acid|tocopherol|dimethicone|niacinamide|panthenol|cetearyl|caprylic"
    r"|phenoxyethanol|xanthan|citric|extract|oil|butter|peg-\d+|ci\s?\d{4,5})\b",
    re.IGNORECASE,
)


def looks_like_inci(text: str) -> bool:
    """Returns True when free text looks like a pasted INCI list rather than casual chat."""
    cleaned = (text or "").strip()
    if len(cleaned) < 25:
        return False
    return ("," in cleaned) or (";" in cleaned) or bool(_INCI_KEYWORDS_RX.search(cleaned))


async def analyze_image_with_llm(base64_image: str, lang: str = "en", allergies: str = "") -> dict:
    """Thin wrapper around analyzer.analyze_image (temperature=0, deterministic rubric)."""
    return await analyze_image(openai_client, OPENAI_MODEL, base64_image, lang, allergies)


async def analyze_text_with_llm(
    inci_text: str, lang: str = "en", allergies: str = "", user_modes: Optional[dict] = None
) -> dict:
    """Thin wrapper around analyzer.analyze_inci_text (gpt-4o-mini, temperature=0, seed=7)."""
    return await analyze_inci_text(
        inci_text, lang, allergies, user_modes, client=openai_client, model=OPENAI_MINI_MODEL
    )


async def ask_product_with_llm(
    report_text: str, question: str, lang: str, allergies: str, user_modes: Optional[dict] = None
) -> str:
    return await answer_product_question(
        openai_client, OPENAI_MINI_MODEL, report_text, question, lang, allergies, user_modes
    )


async def suggest_alternatives_with_llm(
    report_text: str, lang: str, allergies: str, user_modes: Optional[dict] = None
) -> list[dict]:
    return await suggest_alternatives(
        openai_client, OPENAI_MINI_MODEL, report_text, lang, allergies, user_modes
    )


async def compare_scans_with_llm(
    report1: str, report2: str, lang: str, allergies: str, user_modes: Optional[dict] = None
) -> dict:
    return await compare_scans(
        report1, report2, lang, allergies, user_modes, client=openai_client, model=OPENAI_MINI_MODEL
    )


def esc(value, limit: int = 0) -> str:
    """Truncates (optional) and HTML-escapes AI/user text so Telegram never fails to parse it."""
    text = " ".join(str(value or "").split())
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return html.escape(text, quote=False)


def score_bar(score: int, light: str) -> str:
    """10-segment progress bar (each dot = 10 points, matching the 0-100 score directly)."""
    filled = max(0, min(10, score // 10))
    return LIGHT_EMOJI[light] * filled + "⚪" * (10 - filled)


def _quote(title: str, rows: list[str]) -> list[str]:
    return ["", title, "<blockquote>" + "\n".join(rows) + "</blockquote>"]


def format_report(analysis: Optional[dict], lang: str = "en") -> tuple[str, int]:
    """
    Builds the localized HTML report card from an evaluated analysis dict.
    Returns (html_text, score 0-100). If analysis is None, returns the anti-hallucination prompt.
    """
    if analysis is None:
        return t(lang, "no_ingredients_found"), 0

    score = analysis["score"]
    light = analysis["traffic_light"]
    verdict = esc(analysis.get("verdict"), 400)

    items = analysis.get("items") or []
    # Both personal allergies AND pregnancy-mode Red triggers appear in the prominent blockquote alert box.
    alerts = [i for i in items if i.get("user_allergy") or i.get("mode_flag") == "pregnancy"]
    reds = [
        i for i in items
        if i["level"] == "red" and not (i.get("user_allergy") or i.get("mode_flag") == "pregnancy")
    ]
    yellows = [i for i in items if i["level"] == "yellow"]
    safe = [i for i in items if i["level"] == "green"]

    def build(safe_list: list[dict], omitted_safe: int = 0) -> str:
        lines = [
            f"🔬 <b>{t(lang, 'report_title')}</b>",
            "",
            f"{score_bar(score, light)}  <b>{score}/100</b>",
            f"{LIGHT_EMOJI[light]} <b>{t(lang, 'light_' + light)}</b>",
        ]
        if verdict:
            lines += ["", f"📝 {verdict}"]

        if alerts:
            lines += _quote(
                f"🚨 <b>{t(lang, 'lbl_alerts')}</b>",
                [
                    f"🔸 <b>{esc(i['name'], MAX_NAME_LEN)}</b> (-{i['penalty']}) — {esc(i['note'], MAX_NOTE_LEN)}"
                    for i in alerts
                ],
            )
        if reds:
            lines += ["", f"🔴 <b>{t(lang, 'lbl_red')} ({len(reds)})</b>"]
            lines += [
                f"• <b>{esc(i['name'], MAX_NAME_LEN)}</b> (-{i['penalty']}) — {esc(i['note'], MAX_NOTE_LEN)}"
                for i in reds
            ]
        if yellows:
            lines += ["", f"🟡 <b>{t(lang, 'lbl_yellow')} ({len(yellows)})</b>"]
            lines += [
                f"• <b>{esc(i['name'], MAX_NAME_LEN)}</b> (-{i['penalty']}) — {esc(i['note'], MAX_NOTE_LEN)}"
                for i in yellows
            ]
        if safe_list:
            names = ", ".join(esc(i["name"], MAX_NAME_LEN) for i in safe_list)
            if omitted_safe:
                names += f" (+{omitted_safe})"
            lines += ["", f"✅ <b>{t(lang, 'lbl_safe')} ({len(safe)})</b>", names]
        if not (alerts or reds or yellows or safe_list):
            lines += ["", t(lang, "no_details")]

        lines += ["", f"<i>{t(lang, 'disclaimer')}</i>"]
        return "\n".join(lines)

    shown_safe = list(safe)
    omitted_safe = 0
    text = build(shown_safe, omitted_safe)
    # Stay under Telegram's 4096-char limit by dropping whole items (never cutting an HTML tag).
    while len(text) > TELEGRAM_MAX_LEN:
        if shown_safe:
            shown_safe.pop()
            omitted_safe += 1
        elif yellows:
            yellows.pop()
        elif reds:
            reds.pop()
        elif alerts:
            alerts.pop()
        else:
            break
        text = build(shown_safe, omitted_safe)
    return text, score


# ---------------------------------------------------------
# FSM States & UI Helpers
# ---------------------------------------------------------
class Onboarding(StatesGroup):
    choosing_language = State()
    entering_allergies = State()


class ProductQA(StatesGroup):
    asking = State()


class AdminGiveScans(StatesGroup):
    waiting_input = State()
    waiting_amount = State()


class AdminBroadcast(StatesGroup):
    waiting_message = State()
    confirming = State()


LANGUAGES = {
    "en": "English 🇬🇧",
    "ro": "Română 🇷🇴",
    "ru": "Русский 🇷🇺",
    "uk": "Українська 🇺🇦",
}
DEFAULT_LANG = "en"
MAX_ALLERGIES_LEN = 500
NONE_WORDS = {
    "none", "no", "nothing", "n/a", "-", "nu", "nimic", "fara", "fără",
    "нет", "ничего", "немає", "нема", "ні", "нічого",
}


def t(lang: str, key: str, **kwargs) -> str:
    """Looks up a localized string (falls back to English)."""
    template = TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key) or TEXTS[DEFAULT_LANG][key]
    return template.format(**kwargs) if kwargs else template


def language_keyboard() -> InlineKeyboardMarkup:
    """2x2 grid of language buttons."""
    buttons = [
        InlineKeyboardButton(text=label, callback_data=f"lang:{code}")
        for code, label in LANGUAGES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


def format_active_modes(lang: str, modes: Optional[dict]) -> str:
    modes = modes or {}
    active = [t(lang, col) for col in MODE_COLUMNS if modes.get(col)]
    return ", ".join(active) if active else t(lang, "no_modes")


def settings_keyboard(lang: str, modes: Optional[dict] = None) -> InlineKeyboardMarkup:
    """Settings inline keyboard with Language, Allergies, and the 3 Safety Mode toggles."""
    modes = modes or {}
    rows = [
        [InlineKeyboardButton(text=t(lang, "btn_language"), callback_data="settings:language")],
        [InlineKeyboardButton(text=t(lang, "btn_allergies"), callback_data="settings:allergies")],
    ]
    for col in MODE_COLUMNS:
        icon = "✅" if modes.get(col) else "⬜"
        rows.append([
            InlineKeyboardButton(text=f"{icon} {t(lang, col)}", callback_data=f"mode:{col}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def buy_packages_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Inline buttons for purchasing non-expiring bonus scans with Telegram Stars."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_pack_10"), callback_data="buy:pack_10")],
        [InlineKeyboardButton(text=t(lang, "btn_pack_30"), callback_data="buy:pack_30")],
    ])


def report_actions_keyboard(lang: str, scan_id: int) -> InlineKeyboardMarkup:
    """Opt-in follow-up buttons attached beneath every scan report."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_ask"), callback_data=f"ask:{scan_id}")],
        [InlineKeyboardButton(text=t(lang, "btn_alternatives"), callback_data=f"alt:{scan_id}")],
    ])


def qa_cancel_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="qa:cancel")],
    ])


def admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Detailed Stats", callback_data="admin:stats"),
            InlineKeyboardButton(text="🕵️ Recent Scans", callback_data="admin:recent"),
        ],
        [
            InlineKeyboardButton(text="📥 Export DB (CSV)", callback_data="admin:export"),
            InlineKeyboardButton(text="🎁 Give Bonus Scans", callback_data="admin:give"),
        ],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast")],
    ])


def admin_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Cancel", callback_data="admin:cancel")],
    ])


async def get_lang(user_id: int) -> str:
    user = await db_manager.get_user(user_id)
    return user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG


def display_allergies(lang: str, allergies: str) -> str:
    return html.escape(allergies) if allergies else t(lang, "no_allergies")


# Reply-keyboard (persistent bottom menu) button -> translation key
MENU_KEYS = {
    "scan": "btn_scan",
    "compare": "btn_compare",
    "profile": "btn_profile",
    "history": "btn_history",
    "buy": "btn_buy",
    "settings": "btn_menu_settings",
}


def menu_texts(action: str) -> set[str]:
    """The label of one menu button in ALL languages (so taps are recognised after a language change)."""
    return {TEXTS[code][MENU_KEYS[action]] for code in TEXTS}


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Persistent 3x2 bottom keyboard, translated into the user's language."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_scan")), KeyboardButton(text=t(lang, "btn_compare"))],
            [KeyboardButton(text=t(lang, "btn_profile")), KeyboardButton(text=t(lang, "btn_history"))],
            [KeyboardButton(text=t(lang, "btn_buy")), KeyboardButton(text=t(lang, "btn_menu_settings"))],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


async def set_bot_commands(bot: Bot):
    """Registers the native Telegram command menu (default English + localized variants)."""
    for code in TEXTS:
        commands = [
            BotCommand(command="start", description=t(code, "cmd_start")),
            BotCommand(command="profile", description=t(code, "cmd_profile")),
            BotCommand(command="compare", description=t(code, "cmd_compare")),
            BotCommand(command="history", description=t(code, "cmd_history")),
            BotCommand(command="buy", description=t(code, "cmd_buy")),
            BotCommand(command="settings", description=t(code, "cmd_settings")),
        ]
        if code == DEFAULT_LANG:
            await bot.set_my_commands(commands)
        await bot.set_my_commands(commands, language_code=code)


def history_button_label(lang: str, row: dict) -> str:
    """e.g. '🟡 68/100 · 19.11 20:53' (never uses a guessed product name)."""
    ts = row.get("timestamp") or ""
    when = f"{ts[8:10]}.{ts[5:7]} {ts[11:16]}" if len(ts) >= 16 else ""
    light = row.get("traffic_light")
    if row.get("score") is not None and light in LIGHT_EMOJI:
        base = f"{LIGHT_EMOJI[light]} {row['score']}/100"
    else:
        base = f"🧴 {t(lang, 'scan_untitled')} #{row.get('id', '?')}"
    return f"{base} · {when}" if when else base


_TAG_RE = re.compile(r"<[^>]*>")


def html_to_plain(text: str) -> str:
    """Strips tags / entities from a report so it can be sent without any parse mode."""
    text = re.sub(r"</?blockquote[^>]*>", "\n", text)
    return html.unescape(_TAG_RE.sub("", text)).strip()


async def safe_delete(msg: Optional[Message]):
    """Deletes a (status) message; failures (already deleted, too old...) are ignored."""
    if msg is None:
        return
    try:
        await msg.delete()
    except TelegramBadRequest:
        logging.debug("Could not delete status message", exc_info=True)
    except Exception:
        logging.exception("Unexpected error while deleting status message")


async def send_report(message: Message, report: str, reply_markup=None):
    """
    Sends the report as a brand-new message (never edits anything).
    If Telegram rejects the HTML, falls back to plain text so the user always gets an answer.
    """
    try:
        await message.answer(report, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except TelegramBadRequest:
        logging.warning("HTML report rejected by Telegram, resending as plain text", exc_info=True)
        await message.answer(html_to_plain(report), parse_mode=None, reply_markup=reply_markup)


@contextlib.asynccontextmanager
async def chat_action(bot: Bot, chat_id: int, action: str = "typing"):
    """Keeps the 'typing...' indicator alive (Telegram clears it after ~5 s) while the body runs."""
    async def _send():
        try:
            await bot.send_chat_action(chat_id=chat_id, action=action)
        except Exception:
            logging.debug("send_chat_action failed", exc_info=True)

    async def _keep_alive():
        while True:
            await asyncio.sleep(4)
            await _send()

    await _send()
    task = asyncio.create_task(_keep_alive())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


async def _maybe_reward_referral(bot: Bot, message: Message, user_id: int, lang: str):
    """Triggers the delayed +5/+5 referral reward on the referee's first completed scan."""
    try:
        referrer_id = await db_manager.reward_referral_if_due(user_id)
        if referrer_id is None:
            return
        await message.answer(t(lang, "ref_reward_referee", n=REFERRAL_BONUS_SCANS))
        try:
            ref_lang = await get_lang(referrer_id)
            await bot.send_message(
                referrer_id, t(ref_lang, "ref_reward_referrer", n=REFERRAL_BONUS_SCANS)
            )
        except Exception:
            logging.debug("Could not notify referrer %s", referrer_id, exc_info=True)
    except Exception:
        logging.exception("Referral reward check failed")


# =========================================================
# 1. COMMANDS & PERSISTENT MENU BUTTON HANDLERS
#    (Registered before FSM states so commands/menu taps always win)
# =========================================================
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start / reset: parses optional ref_<id> deep link for brand-new users and begins onboarding."""
    await state.clear()
    user_id = message.from_user.id
    is_new = user_id in _NEW_USERS_THIS_UPDATE
    _NEW_USERS_THIS_UPDATE.discard(user_id)
    if not is_new:
        is_new = await db_manager.touch_user(
            user_id, message.from_user.username, message.from_user.first_name, today_str()
        )

    # Parse deep-link payload: /start ref_<referrer_id>
    parts = (message.text or "").split(maxsplit=1)
    if is_new and len(parts) == 2 and parts[1].startswith("ref_"):
        ref_str = parts[1][4:].strip()
        if ref_str.isdigit():
            referrer_id = int(ref_str)
            await db_manager.set_referrer(user_id, referrer_id)

    await db_manager.reset_user(user_id)
    await state.set_state(Onboarding.choosing_language)
    await state.update_data(flow="onboarding")
    await message.answer(
        "🌍 <b>Choose your language · Alege limba · Выберите язык · Оберіть мову</b>",
        reply_markup=language_keyboard(),
    )


@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Interactive admin dashboard (strictly restricted to ADMIN_ID)."""
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        "🛠️ <b>Admin Dashboard</b>\nSelect an action below:",
        reply_markup=admin_dashboard_keyboard(),
    )


async def _build_admin_stats_text() -> str:
    s = await db_manager.get_admin_stats(today_str())
    langs = ", ".join(f"{k.upper()}: <b>{v}</b>" for k, v in s["languages"].items()) or "—"
    return (
        "📊 <b>Detailed Bot Statistics</b>\n\n"
        f"👥 Registered users: <b>{s['users']}</b>\n"
        f"🆕 New users today: <b>{s['new_today']}</b>\n"
        f"🟢 Active users today: <b>{s['active_today']}</b>\n\n"
        f"📅 Scans today: <b>{s['scans_today']}</b>\n"
        f"🔢 Scans all-time: <b>{s['scans_total']}</b>\n\n"
        f"🌐 Languages: {langs}\n"
        f"🤝 Successful referrals: <b>{s['referrals']}</b>\n"
        f"⭐ Telegram Stars earned: <b>{s['stars']}</b>"
    )


@router.message(Command("stats"))
async def cmd_stats(message: Message, state: FSMContext):
    """Admin-only usage statistics (alias to Detailed Stats)."""
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(await _build_admin_stats_text(), reply_markup=admin_dashboard_keyboard())


@router.message(Command("settings"))
@router.message(F.text.in_(menu_texts("settings")))
async def cmd_settings(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    await db_manager.ensure_user(user_id)
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user["language"] in TEXTS else DEFAULT_LANG
    modes = user.get("modes") or {}
    await message.answer(
        t(
            lang,
            "settings",
            language=LANGUAGES.get(lang, lang),
            allergies=display_allergies(lang, user["allergies"]),
            modes=format_active_modes(lang, modes),
        ),
        reply_markup=settings_keyboard(lang, modes),
    )


@router.message(Command("help"))
@router.message(F.text.in_(menu_texts("scan")))
async def cmd_scan_help(message: Message, state: FSMContext):
    """'📸 Scan Product' button (and /help): explains both photo and pasted INCI text scanning."""
    await state.clear()
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "scan_intro"), reply_markup=main_menu_keyboard(lang))


@router.message(Command("profile"))
@router.message(F.text.in_(menu_texts("profile")))
async def cmd_profile(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    user_id = message.from_user.id
    profile = await db_manager.get_profile(user_id)
    lang = profile["language"] if profile["language"] in TEXTS else DEFAULT_LANG

    if is_admin(user_id):
        scans = "♾️"
    else:
        left = profile["daily_scans"] if profile["last_reset_date"] == today_str() else DAILY_SCAN_LIMIT
        scans = f"{left}/{DAILY_SCAN_LIMIT}"

    bot_username = await get_bot_username(bot)
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"

    await message.answer(
        t(
            lang,
            "profile",
            language=LANGUAGES.get(lang, lang),
            allergies=display_allergies(lang, profile["allergies"]),
            modes=format_active_modes(lang, profile.get("modes")),
            scans=scans,
            bonus=profile["bonus_scans"],
            total=profile["total_scans"],
            referrals=profile["referrals_count"],
            ref_link=ref_link,
        ),
        reply_markup=main_menu_keyboard(lang),
    )


@router.message(Command("history"))
@router.message(F.text.in_(menu_texts("history")))
async def cmd_history(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    rows = await db_manager.get_history(user_id, limit=8)
    if not rows:
        await message.answer(t(lang, "history_empty"), reply_markup=main_menu_keyboard(lang))
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=history_button_label(lang, row), callback_data=f"hist:{row['id']}")]
        for row in rows
    ])
    await message.answer(t(lang, "history_title"), reply_markup=keyboard)


@router.message(Command("compare"))
@router.message(F.text.in_(menu_texts("compare")))
async def cmd_compare(message: Message, state: FSMContext):
    """Step 1 of 2-product comparison: pick Product #1 from recent scans."""
    await state.clear()
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    rows = await db_manager.get_history(user_id, limit=8)
    if len(rows) < 2:
        await message.answer(t(lang, "cmp_need_two"), reply_markup=main_menu_keyboard(lang))
        return
    buttons = [
        [InlineKeyboardButton(text=history_button_label(lang, r), callback_data=f"cmp_pick1:{r['id']}")]
        for r in rows
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="cmp_cancel")])
    await message.answer(t(lang, "cmp_pick1"), reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


@router.message(Command("buy"))
@router.message(F.text.in_(menu_texts("buy")))
async def cmd_buy(message: Message, state: FSMContext):
    """Displays Telegram Stars packages for non-expiring bonus scans."""
    await state.clear()
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "buy_menu"), reply_markup=buy_packages_keyboard(lang))


# =========================================================
# 2. CALLBACK QUERIES (Settings, Modes, History, Compare, Buy, Admin, Q&A)
# =========================================================
@router.callback_query(F.data.startswith("hist:"))
async def cb_history_item(callback: CallbackQuery):
    """Re-opens a stored report from /history (only the owner can read it)."""
    lang = await get_lang(callback.from_user.id)
    try:
        scan_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return
    result = await db_manager.get_history_item(callback.from_user.id, scan_id)
    if not result:
        await callback.answer(t(lang, "history_missing"), show_alert=True)
        return
    await send_report(callback.message, result, report_actions_keyboard(lang, scan_id))
    await callback.answer()


@router.callback_query(F.data == "settings:language")
async def cb_settings_language(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Onboarding.choosing_language)
    await state.update_data(flow="settings")
    await callback.message.answer(
        "🌍 <b>Choose your language · Alege limba · Выберите язык · Оберіть мову</b>",
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:allergies")
async def cb_settings_allergies(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    await state.set_state(Onboarding.entering_allergies)
    await state.update_data(flow="settings")
    await callback.message.answer(t(lang, "ask_allergies").split("\n\n", 1)[1])
    await callback.answer()


@router.callback_query(F.data.startswith("mode:"))
async def cb_toggle_safety_mode(callback: CallbackQuery):
    """Flips one safety mode in SQLite and updates the inline keyboard in-place."""
    user_id = callback.from_user.id
    mode_col = callback.data.split(":", 1)[1]
    if mode_col not in MODE_COLUMNS:
        await callback.answer()
        return
    await db_manager.toggle_mode(user_id, mode_col)
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    modes = user.get("modes") if user else {}
    try:
        await callback.message.edit_reply_markup(reply_markup=settings_keyboard(lang, modes))
    except TelegramBadRequest:
        pass
    await callback.answer()


@router.callback_query(Onboarding.choosing_language, F.data.startswith("lang:"))
async def cb_language_chosen(callback: CallbackQuery, state: FSMContext):
    lang = callback.data.split(":", 1)[1]
    if lang not in TEXTS:
        await callback.answer()
        return

    await db_manager.set_language(callback.from_user.id, lang)
    data = await state.get_data()

    await callback.message.edit_text(f"✅ {LANGUAGES[lang]}", reply_markup=None)

    if data.get("flow") == "settings":
        await state.clear()
        await callback.message.answer(
            t(lang, "language_updated", language=LANGUAGES[lang]),
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await state.set_state(Onboarding.entering_allergies)
        await callback.message.answer(t(lang, "ask_allergies"), reply_markup=main_menu_keyboard(lang))
    await callback.answer()


# --- Product Comparison Callbacks -----------------------------------------
def format_comparison_report(cmp_data: dict, scan1: dict, scan2: dict, lang: str) -> str:
    l1 = history_button_label(lang, scan1)
    l2 = history_button_label(lang, scan2)
    winner_raw = str(cmp_data.get("winner") or "").strip().lower()
    if winner_raw == "1":
        winner_line = f"{t(lang, 'cmp_winner')} <b>{t(lang, 'cmp_p1')}</b> ({esc(l1)})"
    elif winner_raw == "2":
        winner_line = f"{t(lang, 'cmp_winner')} <b>{t(lang, 'cmp_p2')}</b> ({esc(l2)})"
    else:
        winner_line = t(lang, "cmp_tie")

    reason = esc(cmp_data.get("winner_reason"), 240)
    diffs = [
        f"• {esc(d, 220)}"
        for d in (cmp_data.get("differences") or [])
        if isinstance(d, str) and d.strip()
    ][:5]
    verdict = esc(cmp_data.get("verdict"), 600)

    lines = [
        t(lang, "cmp_title"),
        f"1️⃣ <b>{t(lang, 'cmp_p1')}:</b> {esc(l1)}",
        f"2️⃣ <b>{t(lang, 'cmp_p2')}:</b> {esc(l2)}",
        "",
        winner_line,
    ]
    if reason:
        lines.append(f"<i>{reason}</i>")
    if diffs:
        lines += ["", t(lang, "cmp_diffs"), *diffs]
    if verdict:
        lines += ["", t(lang, "cmp_verdict"), f"<blockquote>{verdict}</blockquote>"]
    lines += ["", f"<i>{t(lang, 'disclaimer')}</i>"]
    return "\n".join(lines)


@router.callback_query(F.data == "cmp_cancel")
async def cb_compare_cancel(callback: CallbackQuery):
    lang = await get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text(t(lang, "cmp_cancelled"), reply_markup=None)
    except TelegramBadRequest:
        await callback.message.answer(t(lang, "cmp_cancelled"))
    await callback.answer()


@router.callback_query(F.data.startswith("cmp_pick1:"))
async def cb_compare_pick1(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_lang(user_id)
    try:
        scan1_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return

    scan1 = await db_manager.get_scan(user_id, scan1_id)
    if not scan1:
        await callback.answer(t(lang, "history_missing"), show_alert=True)
        return

    rows = [r for r in await db_manager.get_history(user_id, limit=8) if r["id"] != scan1_id]
    if not rows:
        await callback.answer(t(lang, "cmp_need_two"), show_alert=True)
        return

    buttons = [
        [InlineKeyboardButton(
            text=history_button_label(lang, r),
            callback_data=f"cmp_pick2:{scan1_id}:{r['id']}",
        )]
        for r in rows
    ]
    buttons.append([InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="cmp_cancel")])
    text = t(lang, "cmp_pick2", p1=esc(history_button_label(lang, scan1)))
    try:
        await callback.message.edit_text(
            text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    except TelegramBadRequest:
        await callback.message.answer(
            text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("cmp_pick2:"))
async def cb_compare_pick2(callback: CallbackQuery, bot: Bot):
    """Step 3 of comparison: runs gpt-4o-mini comparison without deducting any scans."""
    user_id = callback.from_user.id
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    allergies = user["allergies"] if user else ""
    modes = user.get("modes") if user else {}

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    try:
        scan1_id, scan2_id = int(parts[1]), int(parts[2])
    except ValueError:
        await callback.answer()
        return
    if scan1_id == scan2_id:
        await callback.answer()
        return

    scan1 = await db_manager.get_scan(user_id, scan1_id)
    scan2 = await db_manager.get_scan(user_id, scan2_id)
    if not scan1 or not scan2:
        await callback.answer(t(lang, "history_missing"), show_alert=True)
        return

    await callback.answer(t(lang, "cmp_loading"))
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass

    try:
        async with chat_action(bot, callback.message.chat.id, "typing"):
            cmp_data = await compare_scans_with_llm(
                html_to_plain(scan1["ai_result"]),
                html_to_plain(scan2["ai_result"]),
                lang,
                allergies,
                modes,
            )
        card = format_comparison_report(cmp_data, scan1, scan2, lang)
        await send_report(callback.message, card)
    except Exception:
        logging.exception("Error comparing products")
        await callback.message.answer(t(lang, "cmp_error"))


# --- Telegram Stars Payments Callbacks & Handlers -------------------------
@router.callback_query(F.data.startswith("buy:"))
async def cb_buy_package(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = await get_lang(user_id)
    pack_key = callback.data.split(":", 1)[1]
    if pack_key not in STAR_PACKAGES:
        await callback.answer()
        return
    scans_added, stars_amount = STAR_PACKAGES[pack_key]
    title = t(lang, f"inv_title_{scans_added}")
    description = t(lang, f"inv_desc_{scans_added}")
    await callback.message.answer_invoice(
        title=title,
        description=description,
        payload=f"scans:{pack_key}:{user_id}",
        provider_token="",  # MUST be empty string for Telegram Stars (XTR)
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=stars_amount)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def handle_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    payload = pre_checkout_query.invoice_payload or ""
    parts = payload.split(":")
    if len(parts) == 3 and parts[0] == "scans" and parts[1] in STAR_PACKAGES:
        await pre_checkout_query.answer(ok=True)
    else:
        await pre_checkout_query.answer(ok=False, error_message="Invalid package payload.")


@router.message(F.successful_payment)
async def handle_successful_payment(message: Message):
    user_id = message.from_user.id
    lang = await get_lang(user_id)
    sp = message.successful_payment
    charge_id = sp.telegram_payment_charge_id
    payload = sp.invoice_payload or ""
    stars_amount = sp.total_amount

    parts = payload.split(":")
    pack_key = parts[1] if len(parts) >= 2 else "pack_10"
    scans_added = STAR_PACKAGES.get(pack_key, (10, stars_amount))[0]

    new_balance = await db_manager.record_payment(
        user_id=user_id,
        charge_id=charge_id,
        payload=payload,
        stars=stars_amount,
        scans=scans_added,
    )
    if new_balance is None:
        await message.answer(t(lang, "pay_duplicate"), reply_markup=main_menu_keyboard(lang))
        return
    await message.answer(
        t(lang, "pay_success", added=scans_added, balance=new_balance),
        reply_markup=main_menu_keyboard(lang),
    )


# --- Opt-in Product Q&A & Romanian Pharmacy Alternatives ------------------
@router.callback_query(F.data.startswith("ask:"))
async def cb_ask_product(callback: CallbackQuery, state: FSMContext):
    """Enters Q&A FSM state for a saved scan report (does NOT deduct daily_scans)."""
    user_id = callback.from_user.id
    lang = await get_lang(user_id)
    try:
        scan_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return

    report_text = await db_manager.get_history_item(user_id, scan_id)
    if not report_text:
        await callback.answer(t(lang, "history_missing"), show_alert=True)
        return

    await state.set_state(ProductQA.asking)
    await state.update_data(scan_id=scan_id, report_text=html_to_plain(report_text))
    await callback.message.answer(t(lang, "qa_prompt"), reply_markup=qa_cancel_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "qa:cancel")
async def cb_qa_cancel(callback: CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer(t(lang, "qa_cancelled"), reply_markup=main_menu_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data.startswith("alt:"))
async def cb_suggest_alternatives(callback: CallbackQuery, bot: Bot):
    """On-demand Romanian pharmacy alternatives via gpt-4o-mini (does NOT deduct daily_scans)."""
    user_id = callback.from_user.id
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    allergies = user["allergies"] if user else ""
    modes = user.get("modes") if user else {}

    try:
        scan_id = int(callback.data.split(":", 1)[1])
    except ValueError:
        await callback.answer()
        return

    report_text = await db_manager.get_history_item(user_id, scan_id)
    if not report_text:
        await callback.answer(t(lang, "history_missing"), show_alert=True)
        return

    await callback.answer(t(lang, "alt_loading"))
    try:
        async with chat_action(bot, callback.message.chat.id, "typing"):
            alts = await suggest_alternatives_with_llm(html_to_plain(report_text), lang, allergies, modes)
        if not alts:
            await callback.message.answer(t(lang, "alt_empty"))
            return
        rows = [
            f"💠 <b>{esc(a.get('name'), MAX_NAME_LEN)}</b> — {esc(a.get('reason') or a.get('note'), MAX_NOTE_LEN)}"
            for a in alts
        ]
        card = (
            f"💊 <b>{t(lang, 'lbl_alternatives')}</b>\n"
            f"<blockquote>" + "\n".join(rows) + "</blockquote>\n\n"
            f"<i>{t(lang, 'disclaimer')}</i>"
        )
        await send_report(callback.message, card)
    except Exception:
        logging.exception("Error generating pharmacy alternatives")
        await callback.message.answer(t(lang, "alt_error"))


# --- Admin Dashboard Callbacks --------------------------------------------
def _csv_bytes(columns: list[str], rows: list[tuple]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue().encode("utf-8-sig")


@router.callback_query(F.data == "admin:stats")
async def cb_admin_stats(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.message.answer(await _build_admin_stats_text(), reply_markup=admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:recent")
async def cb_admin_recent(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    rows = await db_manager.get_recent_scans(limit=5)
    if not rows:
        await callback.message.answer("🕵️ <b>Recent Scans</b>\nNo scans recorded yet.")
        await callback.answer()
        return
    blocks = ["🕵️ <b>Last 5 Scans</b>"]
    for r in rows:
        who = f"@{esc(r['username'])}" if r.get("username") else esc(r.get("first_name") or "User")
        light = LIGHT_EMOJI.get(r.get("traffic_light"), "🧴")
        score_str = f"{r['score']}/100" if r.get("score") is not None else "—"
        preview = esc(html_to_plain(r.get("ai_result") or ""), 150)
        blocks.append(
            f"\n<b>#{r['id']}</b> · {r.get('timestamp') or ''}\n"
            f"👤 {who} (<code>{r['user_id']}</code>) · {light} <b>{score_str}</b>\n"
            f"<blockquote>{preview}</blockquote>"
        )
    await callback.message.answer("\n".join(blocks), reply_markup=admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin:export")
async def cb_admin_export(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    await callback.answer("📥 Generating CSV files...")
    u_cols, u_rows = await db_manager.export_users()
    s_cols, s_rows = await db_manager.export_scans()
    users_file = BufferedInputFile(_csv_bytes(u_cols, u_rows), filename="users.csv")
    scans_file = BufferedInputFile(_csv_bytes(s_cols, s_rows), filename="scans.csv")
    await callback.message.answer_document(users_file, caption=f"👥 users.csv ({len(u_rows)} rows)")
    await callback.message.answer_document(scans_file, caption=f"🔬 scans.csv ({len(s_rows)} rows)")


@router.callback_query(F.data == "admin:give")
async def cb_admin_give(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminGiveScans.waiting_input)
    await callback.message.answer(
        "🎁 <b>Give Bonus Scans</b>\n\n"
        "Send the target <code>user_id</code> (or <code>@username</code>) and the amount separated by space "
        "(e.g. <code>123456789 10</code> or <code>@alice 15</code>), or send just the user identifier first:",
        reply_markup=admin_cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.set_state(AdminBroadcast.waiting_message)
    await callback.message.answer(
        "📢 <b>Broadcast Message</b>\n\nSend the text you want to broadcast to all registered users:",
        reply_markup=admin_cancel_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:cancel")
async def cb_admin_cancel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    await callback.message.answer("✅ Admin action cancelled.", reply_markup=admin_dashboard_keyboard())
    await callback.answer()


@router.callback_query(AdminBroadcast.confirming, F.data == "admin:bc_confirm")
async def cb_admin_broadcast_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not is_admin(callback.from_user.id):
        return
    data = await state.get_data()
    text = data.get("broadcast_text") or ""
    await state.clear()
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass
    if not text:
        await callback.answer()
        return

    await callback.answer("📢 Sending broadcast...")
    user_ids = await db_manager.get_all_user_ids()
    delivered, failed = 0, 0
    safe_text = html.escape(text, quote=False)
    for uid in user_ids:
        try:
            await bot.send_message(uid, safe_text)
            delivered += 1
        except (TelegramForbiddenError, TelegramBadRequest):
            failed += 1
        except Exception:
            logging.debug("Broadcast to %s failed", uid, exc_info=True)
            failed += 1
        await asyncio.sleep(0.05)

    await callback.message.answer(
        f"📢 <b>Broadcast Complete</b>\n✅ Delivered: <b>{delivered}</b>\n❌ Failed/Blocked: <b>{failed}</b>",
        reply_markup=admin_dashboard_keyboard(),
    )


@router.callback_query()
async def cb_stale(callback: CallbackQuery):
    """Stops the loading spinner for buttons from an expired flow (e.g. after a restart)."""
    await callback.answer()


# =========================================================
# 3. ACTIVE FSM STATE MESSAGE HANDLERS
# =========================================================
@router.message(Onboarding.entering_allergies, F.text)
async def msg_allergies(message: Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    raw = " ".join(message.text.split())

    if len(raw) > MAX_ALLERGIES_LEN:
        await message.answer(t(lang, "too_long", n=MAX_ALLERGIES_LEN))
        return

    allergies = "" if raw.lower().strip(".! ") in NONE_WORDS else raw
    await db_manager.set_allergies(message.from_user.id, allergies)
    data = await state.get_data()
    await state.clear()

    if data.get("flow") == "settings":
        await message.answer(
            t(lang, "allergies_updated", allergies=display_allergies(lang, allergies)),
            reply_markup=main_menu_keyboard(lang),
        )
    else:
        await message.answer(
            t(
                lang,
                "ready",
                language=LANGUAGES[lang],
                allergies=display_allergies(lang, allergies),
            ),
            reply_markup=main_menu_keyboard(lang),
        )


@router.message(Onboarding.entering_allergies)
async def msg_allergies_invalid(message: Message):
    """Non-text input (photo, sticker...) while waiting for the allergy text."""
    await message.answer(t(await get_lang(message.from_user.id), "send_text"))


@router.message(ProductQA.asking, F.text)
async def msg_qa_question(message: Message, state: FSMContext, bot: Bot):
    """Answers a follow-up question using gpt-4o-mini without deducting daily_scans."""
    user_id = message.from_user.id
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    allergies = user["allergies"] if user else ""
    modes = user.get("modes") if user else {}

    data = await state.get_data()
    report_text = data.get("report_text")
    if not report_text:
        await state.clear()
        await message.answer(t(lang, "history_missing"), reply_markup=main_menu_keyboard(lang))
        return

    try:
        async with chat_action(bot, message.chat.id, "typing"):
            answer = await ask_product_with_llm(report_text, message.text, lang, allergies, modes)
        safe_answer = html.escape(answer or t(lang, "qa_error"), quote=False)
        if len(safe_answer) > TELEGRAM_MAX_LEN - 50:
            safe_answer = safe_answer[: TELEGRAM_MAX_LEN - 60].rsplit("\n", 1)[0] + "\n…"
        await message.answer(f"💬 {safe_answer}", reply_markup=qa_cancel_keyboard(lang))
    except Exception:
        logging.exception("Error answering product Q&A")
        await message.answer(t(lang, "qa_error"), reply_markup=qa_cancel_keyboard(lang))


@router.message(ProductQA.asking, ~F.photo)
async def msg_qa_invalid(message: Message):
    """Non-text input (sticker, voice...) while in Q&A mode (photos fall through to handle_photo)."""
    lang = await get_lang(message.from_user.id)
    await message.answer(t(lang, "qa_send_text"), reply_markup=qa_cancel_keyboard(lang))


# --- Admin FSM Handlers ---------------------------------------------------
async def _execute_give_scans(message: Message, state: FSMContext, bot: Bot, target_user: dict, amount: int):
    await state.clear()
    target_id = target_user["user_id"]
    new_balance = await db_manager.add_bonus_scans(target_id, amount)
    who = f"@{esc(target_user['username'])}" if target_user.get("username") else f"<code>{target_id}</code>"
    await message.answer(
        f"✅ Added <b>+{amount}</b> bonus scans to {who} (<code>{target_id}</code>).\n"
        f"⭐ New bonus balance: <b>{new_balance}</b>",
        reply_markup=admin_dashboard_keyboard(),
    )
    try:
        t_lang = await get_lang(target_id)
        await bot.send_message(
            target_id, t(t_lang, "bonus_gift_notify", amount=amount, balance=new_balance)
        )
    except Exception:
        logging.debug("Could not notify gifted user %s", target_id, exc_info=True)


@router.message(AdminGiveScans.waiting_input, F.text)
async def msg_admin_give_input(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    parts = message.text.strip().split()
    if not parts:
        return
    target = await db_manager.find_user(parts[0])
    if not target:
        await message.answer(
            f"⚠️ User <code>{esc(parts[0])}</code> not found in the database. Try again or press Cancel:",
            reply_markup=admin_cancel_keyboard(),
        )
        return
    if len(parts) >= 2 and parts[1].lstrip("-").isdigit():
        await _execute_give_scans(message, state, bot, target, int(parts[1]))
        return
    await state.set_state(AdminGiveScans.waiting_amount)
    await state.update_data(target_user=target)
    await message.answer(
        f"👤 Target user: <code>{target['user_id']}</code>\nNow send the number of bonus scans to add (e.g. <code>10</code>):",
        reply_markup=admin_cancel_keyboard(),
    )


@router.message(AdminGiveScans.waiting_amount, F.text)
async def msg_admin_give_amount(message: Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    raw = message.text.strip()
    if not raw.lstrip("-").isdigit():
        await message.answer("⚠️ Please enter a valid integer amount:", reply_markup=admin_cancel_keyboard())
        return
    data = await state.get_data()
    target = data.get("target_user")
    if not target:
        await state.clear()
        return
    await _execute_give_scans(message, state, bot, target, int(raw))


@router.message(AdminBroadcast.waiting_message, F.text)
async def msg_admin_broadcast_preview(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return
    text = message.text.strip()
    user_ids = await db_manager.get_all_user_ids()
    await state.set_state(AdminBroadcast.confirming)
    await state.update_data(broadcast_text=text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Confirm & Send", callback_data="admin:bc_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="admin:cancel"),
        ]
    ])
    await message.answer(
        f"📢 <b>Broadcast Preview</b> (to <b>{len(user_ids)}</b> users):\n\n"
        f"<blockquote>{esc(text, 3500)}</blockquote>\n\nSend now?",
        reply_markup=kb,
    )


# =========================================================
# 4. PHOTO SCAN HANDLER
# =========================================================
@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    admin = is_admin(user_id)
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    allergies = user["allergies"] if user else ""
    modes = user.get("modes") if user else {}

    # Daily -> bonus -> blocked limit check
    allowed, source = await db_manager.consume_scan(user_id, is_admin=admin, today=today_str())
    if not allowed:
        await message.answer(
            t(lang, "limit_reached", n=DAILY_SCAN_LIMIT),
            reply_markup=buy_packages_keyboard(lang),
        )
        return

    status_msg = await message.answer(t(lang, "processing"), reply_markup=main_menu_keyboard(lang))
    analysis_done = False

    try:
        async with chat_action(bot, message.chat.id, "typing"):
            highest_res_photo = message.photo[-1]

            # 1. Download the image into memory only (nothing is written to disk)
            buffer = await bot.download(highest_res_photo.file_id, destination=io.BytesIO())
            if buffer is None:
                raise RuntimeError("Telegram download returned no data.")

            # 2. Encode to base64
            base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
            buffer.close()

            # 3. Single async Vision LLM call (OCR + classification), then deterministic rubric scoring
            raw_data = await analyze_image_with_llm(base64_image, lang, allergies)

        analysis = evaluate(raw_data, lang, allergies, modes)
        report, score = format_report(analysis, lang)
        analysis_done = True

        # 4. Log to the database (a logging failure must never hide the result from the user)
        scan_id: Optional[int] = None
        try:
            if analysis is not None:
                extracted = ", ".join(i["name"] for i in analysis["items"])
                await db_manager.log_scan(user_id, extracted, safety_score=score)
                scan_id = await db_manager.add_scan_history(
                    user_id, report, None, score, analysis["traffic_light"]
                )
            else:
                await db_manager.add_scan_history(user_id, report, None)
        except Exception:
            logging.exception("Failed to write scan history")

        # 5. Remove the temporary status message and send the report as a NEW message
        await safe_delete(status_msg)
        status_msg = None
        markup = (
            report_actions_keyboard(lang, scan_id)
            if (analysis is not None and scan_id is not None)
            else main_menu_keyboard(lang)
        )
        await send_report(message, report, markup)

        if analysis is not None:
            await _maybe_reward_referral(bot, message, user_id, lang)

    except Exception:
        logging.exception("Error processing photo")
        if not analysis_done:
            try:
                await db_manager.refund_scan(user_id, source)
            except Exception:
                logging.exception("Failed to refund scan")
        if status_msg is not None:
            await safe_delete(status_msg)
        try:
            await message.answer(t(lang, "error"), reply_markup=main_menu_keyboard(lang))
        except Exception:
            logging.exception("Failed to send error message")


# =========================================================
# 5. GENERAL TEXT INCI HANDLER (MUST BE LAST!)
# =========================================================
@router.message(F.text)
async def handle_text_inci(message: Message, bot: Bot):
    """
    If free text looks like a pasted INCI ingredient list, analyses it with gpt-4o-mini using the
    exact same deterministic rubric, limits, history logging and follow-up buttons as photo scans.
    Otherwise replies with a localized hint explaining how to scan by photo or paste an INCI list.
    """
    user_id = message.from_user.id
    user = await db_manager.get_user(user_id)
    lang = user["language"] if user and user["language"] in TEXTS else DEFAULT_LANG
    allergies = user["allergies"] if user else ""
    modes = user.get("modes") if user else {}

    text = (message.text or "").strip()
    if not looks_like_inci(text):
        await message.answer(t(lang, "scan_intro"), reply_markup=main_menu_keyboard(lang))
        return

    admin = is_admin(user_id)
    allowed, source = await db_manager.consume_scan(user_id, is_admin=admin, today=today_str())
    if not allowed:
        await message.answer(
            t(lang, "limit_reached", n=DAILY_SCAN_LIMIT),
            reply_markup=buy_packages_keyboard(lang),
        )
        return

    status_msg = await message.answer(t(lang, "processing_text"), reply_markup=main_menu_keyboard(lang))
    analysis_done = False

    try:
        async with chat_action(bot, message.chat.id, "typing"):
            raw_data = await analyze_text_with_llm(text, lang, allergies, modes)

        analysis = evaluate(raw_data, lang, allergies, modes)
        analysis_done = True

        # Anti-garbage check: if the pasted text wasn't an ingredient list, refund the scan!
        if analysis is None:
            await db_manager.refund_scan(user_id, source)
            await safe_delete(status_msg)
            status_msg = None
            await message.answer(t(lang, "no_ingredients_text"), reply_markup=main_menu_keyboard(lang))
            return

        report, score = format_report(analysis, lang)

        scan_id: Optional[int] = None
        try:
            extracted = ", ".join(i["name"] for i in analysis["items"])
            await db_manager.log_scan(user_id, extracted, safety_score=score)
            scan_id = await db_manager.add_scan_history(
                user_id, report, None, score, analysis["traffic_light"]
            )
        except Exception:
            logging.exception("Failed to write text scan history")

        await safe_delete(status_msg)
        status_msg = None
        markup = report_actions_keyboard(lang, scan_id) if scan_id is not None else main_menu_keyboard(lang)
        await send_report(message, report, markup)
        await _maybe_reward_referral(bot, message, user_id, lang)

    except Exception:
        logging.exception("Error processing INCI text")
        if not analysis_done:
            try:
                await db_manager.refund_scan(user_id, source)
            except Exception:
                logging.exception("Failed to refund scan")
        if status_msg is not None:
            await safe_delete(status_msg)
        try:
            await message.answer(t(lang, "error"), reply_markup=main_menu_keyboard(lang))
        except Exception:
            logging.exception("Failed to send error message")


# ---------------------------------------------------------
# Main Application Loop
# ---------------------------------------------------------
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    await db_manager.init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    await set_bot_commands(bot)
    dp.include_router(router)

    logging.info("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
