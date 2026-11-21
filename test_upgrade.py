"""
Automated 48-assertion end-to-end test suite for the Ingredient Scanner Telegram Bot.
Mocks OpenAI and Telegram Bot API sessions so all tests run offline at zero token cost.

Run with:
    python test_upgrade.py
"""
import asyncio
import itertools
import os
import sqlite3
import tempfile
from datetime import datetime
from html.parser import HTMLParser

# Provide safe dummy credentials if .env is not present (e.g. in CI or fresh clone)
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key")
os.environ.setdefault("ADMIN_ID", "777")

import analyzer
import bot as app
from aiogram import Bot, Dispatcher
from aiogram.client.session.base import BaseSession
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Chat, File, InlineKeyboardMarkup, Message, User

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(tempfile.gettempdir(), f"scanner_upgrade_test_{os.getpid()}.db")
if os.path.exists(DB):
    os.remove(DB)
app.db_manager.db_path = DB


class Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.ok = True

    def handle_starttag(self, tag, attrs):
        self.stack.append(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            self.ok = False


def valid_html(text: str) -> bool:
    ch = Checker()
    ch.feed(text)
    return ch.ok and not ch.stack


def check(name: str, cond: bool):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        check.failed += 1


check.failed = 0


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.calls = []
        self._ids = itertools.count(100)
        self.blocked_users = set()

    async def close(self):
        pass

    async def stream_content(self, url, headers=None, timeout=30, chunk_size=65536, raise_for_status=True):
        yield b"\xff\xd8fakejpeg"

    async def make_request(self, bot, method, timeout=None):
        self.calls.append(method)
        name = type(method).__name__
        if name == "SendMessage" and getattr(method, "chat_id", None) in self.blocked_users:
            raise TelegramForbiddenError(method=method, message="Forbidden: bot was blocked by the user")
        if name in ("SendMessage", "EditMessageText", "SendInvoice", "SendDocument"):
            return Message(
                message_id=next(self._ids),
                date=datetime.now(),
                chat=Chat(id=getattr(method, "chat_id", 42) or 42, type="private"),
                text=getattr(method, "text", None)
                or getattr(method, "title", None)
                or getattr(method, "caption", ""),
            ).as_(bot)
        if name == "GetMe":
            return User(id=999999, is_bot=True, first_name="Scanner", username="TestScannerBot")
        if name == "GetFile":
            return File(file_id="f", file_unique_id="u", file_path="photos/x.jpg")
        return True

    def sent(self, kind="SendMessage"):
        return [m for m in self.calls if type(m).__name__ == kind]


_ids = itertools.count(1)


def msg_dict(text=None, photo=False, uid=42, username=None, first_name="Alice", payment=None):
    if username is None:
        username = "referee200" if uid == 200 else f"user{uid}"
    d = {
        "message_id": next(_ids),
        "date": int(datetime.now().timestamp()),
        "chat": {"id": uid, "type": "private"},
        "from": {"id": uid, "is_bot": False, "first_name": first_name, "username": username},
    }
    if text is not None:
        d["text"] = text
        if text.startswith("/"):
            d["entities"] = [{"type": "bot_command", "offset": 0, "length": len(text.split()[0])}]
    if photo:
        d["photo"] = [{"file_id": "p1", "file_unique_id": "pu", "width": 10, "height": 10}]
    if payment:
        d["successful_payment"] = payment
    return d


async def say(dp, bot, text=None, photo=False, uid=42, username=None, first_name="Alice", payment=None):
    await dp.feed_raw_update(
        bot, {"update_id": next(_ids), "message": msg_dict(text, photo, uid, username, first_name, payment)}
    )


async def tap(dp, bot, data, uid=42, username=None, first_name="Alice"):
    if username is None:
        username = "referee200" if uid == 200 else f"user{uid}"
    await dp.feed_raw_update(
        bot,
        {
            "update_id": next(_ids),
            "callback_query": {
                "id": str(next(_ids)),
                "from": {"id": uid, "is_bot": False, "first_name": first_name, "username": username},
                "chat_instance": "ci",
                "data": data,
                "message": msg_dict("x", uid=uid, username=username, first_name=first_name),
            },
        },
    )


async def pre_checkout(dp, bot, payload, uid=42):
    await dp.feed_raw_update(
        bot,
        {
            "update_id": next(_ids),
            "pre_checkout_query": {
                "id": str(next(_ids)),
                "from": {"id": uid, "is_bot": False, "first_name": "Alice"},
                "currency": "XTR",
                "total_amount": 25,
                "invoice_payload": payload,
            },
        },
    )


async def main():
    # 0. Verify repository structure & .gitignore hygiene
    gitignore_path = os.path.join(ROOT, ".gitignore")
    gitignore_text = open(gitignore_path, encoding="utf-8").read() if os.path.isfile(gitignore_path) else ""
    check(
        "Repository structure & .gitignore hygiene verified",
        all(os.path.isfile(os.path.join(ROOT, f)) for f in ("bot.py", "database.py", "analyzer.py", "texts.py", "requirements.txt"))
        and ".env" in gitignore_text
        and "*.db" in gitignore_text,
    )

    # 1. Translation parity across en, ro, ru, uk & distinct ReplyKeyboard button labels
    for lang in ("ro", "ru", "uk"):
        missing = set(app.TEXTS["en"]) - set(app.TEXTS[lang])
        extra = set(app.TEXTS[lang]) - set(app.TEXTS["en"])
        check(f"texts parity {lang}", not missing and not extra)
    for lang in ("en", "ro", "ru", "uk"):
        labels = [app.TEXTS[lang][k] for k in app.MENU_KEYS.values()]
        check(f"6 distinct menu button labels ({lang})", len(labels) == len(set(labels)) == 6)

    # 2. Safe DB migration from an old-schema SQLite DB
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, language TEXT NOT NULL DEFAULT 'en', allergies TEXT NOT NULL DEFAULT '')")
    c.execute("INSERT INTO users (user_id, language, allergies) VALUES (10, 'ro', 'fragrance')")
    c.execute("CREATE TABLE scans_history (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, ai_result TEXT)")
    c.execute("INSERT INTO scans_history (user_id, ai_result) VALUES (10, '<b>legacy report</b>')")
    c.commit()
    c.close()

    await app.db_manager.init_db()
    c = sqlite3.connect(DB)
    user_cols = {r[1] for r in c.execute("PRAGMA table_info(users)")}
    tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    legacy_row = c.execute("SELECT language, allergies, daily_scans, bonus_scans, created_at FROM users WHERE user_id=10").fetchone()
    c.close()
    check(
        "users table migrated with all new columns",
        {"mode_pregnancy", "mode_acne", "mode_hair_clean", "bonus_scans", "referred_by", "referral_rewarded", "referrals_count", "username", "first_name", "created_at"} <= user_cols,
    )
    check("payments table created", "payments" in tables)
    check("legacy user row preserved & created_at backfilled", legacy_row[:4] == ("ro", "fragrance", 3, 0) and legacy_row[4] is not None)

    # 3. Scan consumption priority (daily -> bonus -> blocked) & exact refunds
    await app.db_manager.add_bonus_scans(10, 2)
    sources = []
    for _ in range(6):
        ok, src = await app.db_manager.consume_scan(10, is_admin=False, today="2026-11-20")
        sources.append((ok, src))
    check(
        "consume order: 3 daily -> 2 bonus -> blocked",
        sources == [(True, "daily"), (True, "daily"), (True, "daily"), (True, "bonus"), (True, "bonus"), (False, "none")],
    )
    await app.db_manager.refund_scan(10, "bonus")
    p10 = await app.db_manager.get_profile(10)
    check("refund 'bonus' restores bonus_scans=1", p10["bonus_scans"] == 1 and p10["daily_scans"] == 0)
    await app.db_manager.refund_scan(10, "daily")
    p10 = await app.db_manager.get_profile(10)
    check("refund 'daily' restores daily_scans=1", p10["daily_scans"] == 1 and p10["bonus_scans"] == 1)
    ok_adm, src_adm = await app.db_manager.consume_scan(10, is_admin=True, today="2026-11-20")
    p10_after = await app.db_manager.get_profile(10)
    check("admin consume deducts nothing", ok_adm and src_adm == "admin" and p10_after["daily_scans"] == 1 and p10_after["bonus_scans"] == 1)

    # 4. Profile Safety Modes in analyzer.evaluate()
    preg_formula = {
        "no_ingredients_found": False,
        "verdict": "Retinol & Bakuchiol serum with chemical UV filters.",
        "ingredients": [
            {"name": "Aqua", "level": "green", "penalty": 0, "note": ""},
            {"name": "Bakuchiol", "level": "green", "penalty": 0, "note": ""},
            {"name": "Retinol", "level": "green", "penalty": 0, "note": ""},
            {"name": "Homosalate", "level": "green", "penalty": 0, "note": ""},
            {"name": "Octocrylene", "level": "green", "penalty": 0, "note": ""},
            {"name": "Parfum", "level": "green", "penalty": 0, "note": ""},
        ],
    }
    ev_no_preg = analyzer.evaluate(preg_formula, "en", "", {"mode_pregnancy": False})
    ev_preg = analyzer.evaluate(preg_formula, "en", "", {"mode_pregnancy": True})
    check("without pregnancy mode: 61 Yellow", ev_no_preg["score"] == 61 and ev_no_preg["traffic_light"] == "yellow")
    check("with pregnancy mode: Retinol -> Red (-25), score 36 Red (bypasses 55 floor)", ev_preg["score"] == 36 and ev_preg["traffic_light"] == "red")
    check("Bakuchiol stays green in pregnancy mode", next(i for i in ev_preg["items"] if i["name"] == "Bakuchiol")["level"] == "green")
    rep_preg, _ = app.format_report(ev_preg, "en")
    check("pregnancy Red trigger appears in blockquote alert box", "<blockquote>" in rep_preg and "Retinol" in rep_preg.split("</blockquote>")[0] and valid_html(rep_preg))

    acne_formula = {
        "no_ingredients_found": False,
        "verdict": "Rich cream.",
        "ingredients": [
            {"name": "Aqua", "level": "green", "penalty": 0, "note": ""},
            {"name": "Cocos Nucifera Oil", "level": "green", "penalty": 0, "note": ""},
            {"name": "Isopropyl Palmitate", "level": "green", "penalty": 0, "note": ""},
        ],
    }
    ev_acne = analyzer.evaluate(acne_formula, "ro", "", {"mode_acne": True})
    check("mode_acne flags Coconut Oil & Isopropyl Palmitate (-10 each -> 80)", ev_acne["score"] == 80 and all(i["level"] == "yellow" for i in ev_acne["items"][1:]))

    hair_formula = {
        "no_ingredients_found": False,
        "verdict": "Shampoo.",
        "ingredients": [
            {"name": "Aqua", "level": "green", "penalty": 0, "note": ""},
            {"name": "Sodium Laureth Sulfate", "level": "green", "penalty": 0, "note": ""},
            {"name": "Dimethicone", "level": "green", "penalty": 0, "note": ""},
        ],
    }
    ev_hair = analyzer.evaluate(hair_formula, "ru", "", {"mode_hair_clean": True})
    check("mode_hair_clean flags SLES & Dimethicone (-10 each -> 80)", ev_hair["score"] == 80 and all(i["level"] == "yellow" for i in ev_hair["items"][1:]))

    # 5. End-to-end Telegram Bot flows via Dispatcher
    sess = FakeSession()
    bot = Bot(token="123456:TEST", session=sess)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(app.router)

    sample_formula = {
        "no_ingredients_found": False,
        "verdict": "Clean moisturizing formula.",
        "ingredients": [
            {"name": "Aqua", "level": "green", "penalty": 0, "note": ""},
            {"name": "Glycerin", "level": "green", "penalty": 0, "note": ""},
            {"name": "Niacinamide", "level": "green", "penalty": 0, "note": ""},
            {"name": "Parfum", "level": "yellow", "penalty": 15, "note": "Fragrance"},
        ],
    }
    app.analyze_image_with_llm = lambda b64, lang="en", allergies="": asyncio.sleep(0, result=sample_formula)

    # 5a. Referral deep link & anti-abuse checks
    await say(dp, bot, "/start ref_50", uid=50, username="self50", first_name="Self")
    c = sqlite3.connect(DB)
    ref_50 = c.execute("SELECT referred_by FROM users WHERE user_id=50").fetchone()[0]
    c.close()
    check("self-referral blocked", ref_50 is None)

    await say(dp, bot, "/start ref_10", uid=50, username="self50", first_name="Self")
    c = sqlite3.connect(DB)
    ref_50_again = c.execute("SELECT referred_by FROM users WHERE user_id=50").fetchone()[0]
    c.close()
    check("existing user referral blocked", ref_50_again is None)

    await say(dp, bot, "/start ref_10", uid=200, username="referee200", first_name="Bob")
    await tap(dp, bot, "lang:en", uid=200, username="referee200", first_name="Bob")
    await say(dp, bot, "none", uid=200, username="referee200", first_name="Bob")
    p200_before = await app.db_manager.get_profile(200)
    p10_before = await app.db_manager.get_profile(10)
    check("no bonus awarded on /start before first scan", p200_before["bonus_scans"] == 0)

    await say(dp, bot, photo=True, uid=200, username="referee200", first_name="Bob")
    p200_after = await app.db_manager.get_profile(200)
    p10_after = await app.db_manager.get_profile(10)
    check(
        "delayed referral reward (+5/+5) on first scan",
        p200_after["bonus_scans"] == 5
        and p10_after["bonus_scans"] == p10_before["bonus_scans"] + 5
        and p10_after["referrals_count"] == p10_before["referrals_count"] + 1,
    )
    await say(dp, bot, photo=True, uid=200, username="referee200", first_name="Bob")
    check("second scan does not double-reward referral", (await app.db_manager.get_profile(200))["bonus_scans"] == 5)

    # 5b. Settings safety mode toggle in-place
    await say(dp, bot, "/settings", uid=200)
    edits_markup_before = [m for m in sess.calls if type(m).__name__ == "EditMessageReplyMarkup"]
    await tap(dp, bot, "mode:mode_pregnancy", uid=200)
    edits_markup_after = [m for m in sess.calls if type(m).__name__ == "EditMessageReplyMarkup"]
    u200 = await app.db_manager.get_user(200)
    check(
        "safety mode toggle flips DB boolean & calls edit_message_reply_markup",
        u200["modes"]["mode_pregnancy"] is True and len(edits_markup_after) == len(edits_markup_before) + 1,
    )

    # 5c. Text INCI analysis & garbage-text refund
    prof_before_chat = await app.db_manager.get_profile(200)
    await say(dp, bot, "hello there!", uid=200)
    prof_after_chat = await app.db_manager.get_profile(200)
    check("short casual chat shows scan intro without deducting scan", prof_before_chat["daily_scans"] == prof_after_chat["daily_scans"] and "Photo" in sess.sent()[-1].text)

    app.analyze_text_with_llm = lambda txt, lang="en", allergies="", modes=None: asyncio.sleep(0, result={"no_ingredients_found": True})
    prof_before_garbage = await app.db_manager.get_profile(200)
    await say(dp, bot, "Hello friend, how are you doing today, everything good with you?", uid=200)
    prof_after_garbage = await app.db_manager.get_profile(200)
    check(
        "garbage text rejected & scan refunded",
        prof_after_garbage["daily_scans"] == prof_before_garbage["daily_scans"]
        and "not deducted" in sess.sent()[-1].text,
    )

    app.analyze_text_with_llm = lambda txt, lang="en", allergies="", modes=None: asyncio.sleep(0, result=preg_formula)
    await say(dp, bot, "Ingredients: Aqua, Bakuchiol, Retinol, Homosalate, Octocrylene, Parfum", uid=200)
    last_msg = sess.sent()[-1]
    check(
        "valid INCI text scan produces report (with active pregnancy mode -> 36/100) + follow-up buttons",
        "36/100" in last_msg.text and isinstance(last_msg.reply_markup, InlineKeyboardMarkup),
    )

    # 5d. 2-Product Comparison flow
    await say(dp, bot, "/compare", uid=50)
    check("< 2 scans guard on /compare", "2" in sess.sent()[-1].text)

    prof_before_cmp = await app.db_manager.get_profile(200)
    await say(dp, bot, "⚖️ Compare", uid=200)
    step1_kb = sess.sent()[-1].reply_markup
    check("compare step 1 lists recent scans", isinstance(step1_kb, InlineKeyboardMarkup) and step1_kb.inline_keyboard[0][0].callback_data.startswith("cmp_pick1:"))
    pick1_cb = step1_kb.inline_keyboard[0][0].callback_data
    scan1_id = int(pick1_cb.split(":")[1])

    await tap(dp, bot, pick1_cb, uid=200)
    step2_msg = sess.sent("EditMessageText")[-1]
    step2_kb = step2_msg.reply_markup
    pick2_cbs = [r[0].callback_data for r in step2_kb.inline_keyboard if r[0].callback_data.startswith("cmp_pick2:")]
    check("compare step 2 excludes Product #1", all(not cb.endswith(f":{scan1_id}") for cb in pick2_cbs))

    app.compare_scans_with_llm = lambda r1, r2, lang, allergies, modes=None: asyncio.sleep(
        0,
        result={
            "winner": "1",
            "winner_reason": "Product 1 avoids Retinol during pregnancy.",
            "differences": ["Product 1 has 85/100 vs 36/100", "Product 2 contains Retinol"],
            "verdict": "Choose Product 1 while pregnant.",
        },
    )
    await tap(dp, bot, pick2_cbs[0], uid=200)
    cmp_card = sess.sent()[-1].text
    prof_after_cmp = await app.db_manager.get_profile(200)
    check(
        "compare step 3 sends HTML comparison card & deducts 0 scans",
        "🏆" in cmp_card and "🔍" in cmp_card and "<blockquote>" in cmp_card and valid_html(cmp_card)
        and prof_after_cmp["daily_scans"] == prof_before_cmp["daily_scans"]
        and prof_after_cmp["bonus_scans"] == prof_before_cmp["bonus_scans"],
    )

    # 5e. Telegram Stars Payments (/buy, invoice XTR, pre_checkout, idempotent successful_payment)
    await say(dp, bot, "⭐ Buy Scans", uid=200)
    buy_kb = sess.sent()[-1].reply_markup
    check("/buy shows 2 Star packages", isinstance(buy_kb, InlineKeyboardMarkup) and len(buy_kb.inline_keyboard) == 2)
    await tap(dp, bot, "buy:pack_10", uid=200)
    inv = sess.sent("SendInvoice")[-1]
    check(
        "SendInvoice uses currency=XTR, provider_token='', amount=25",
        inv.currency == "XTR" and inv.provider_token == "" and inv.prices[0].amount == 25,
    )
    await pre_checkout(dp, bot, inv.payload, uid=200)
    pcq_ans = sess.sent("AnswerPreCheckoutQuery")[-1]
    check("pre_checkout_query answered ok=True", pcq_ans.ok is True)

    payment_obj = {
        "currency": "XTR",
        "total_amount": 25,
        "invoice_payload": inv.payload,
        "telegram_payment_charge_id": "charge_unique_001",
        "provider_payment_charge_id": "prov_001",
    }
    bonus_before_pay = (await app.db_manager.get_profile(200))["bonus_scans"]
    await say(dp, bot, uid=200, payment=payment_obj)
    bonus_after_pay = (await app.db_manager.get_profile(200))["bonus_scans"]
    check("successful_payment adds +10 bonus_scans", bonus_after_pay == bonus_before_pay + 10)

    await say(dp, bot, uid=200, payment=payment_obj)
    bonus_after_dup = (await app.db_manager.get_profile(200))["bonus_scans"]
    check("duplicate telegram_payment_charge_id is idempotent (no double credit)", bonus_after_dup == bonus_after_pay)

    # 5f. Admin Panel (/admin): auth guard, stats, recent, CSV UTF-8-SIG export, Give Scans, Broadcast
    app.ADMIN_ID = 777
    sent_count = len(sess.sent())
    await say(dp, bot, "/admin", uid=200)
    await tap(dp, bot, "admin:stats", uid=200)
    await tap(dp, bot, "admin:export", uid=200)
    check("non-admin completely ignored on /admin and admin:* callbacks", len(sess.sent()) == sent_count and not sess.sent("SendDocument"))

    await say(dp, bot, "/admin", uid=777, username="boss", first_name="Admin")
    adm_kb = sess.sent()[-1].reply_markup
    check("admin gets 5-button dashboard", isinstance(adm_kb, InlineKeyboardMarkup) and sum(len(r) for r in adm_kb.inline_keyboard) == 5)

    await tap(dp, bot, "admin:stats", uid=777)
    stats_text = sess.sent()[-1].text
    check("admin Detailed Stats shows referrals & Stars earned (25)", "Stars earned: <b>25</b>" in stats_text and "Successful referrals: <b>1</b>" in stats_text)

    await tap(dp, bot, "admin:recent", uid=777)
    check("admin Recent Scans shows @referee200", "@referee200" in sess.sent()[-1].text)

    await tap(dp, bot, "admin:export", uid=777)
    docs = sess.sent("SendDocument")
    check(
        "admin Export DB sends users.csv & scans.csv with UTF-8-SIG BOM",
        len(docs) == 2
        and docs[0].document.filename == "users.csv"
        and docs[1].document.filename == "scans.csv"
        and docs[0].document.data.startswith(b"\xef\xbb\xbf")
        and docs[1].document.data.startswith(b"\xef\xbb\xbf"),
    )

    await tap(dp, bot, "admin:give", uid=777)
    await say(dp, bot, "@referee200 7", uid=777)
    check("admin Give Bonus Scans credits +7 by @username", (await app.db_manager.get_profile(200))["bonus_scans"] == bonus_after_pay + 7)

    sess.blocked_users.add(50)
    await tap(dp, bot, "admin:broadcast", uid=777)
    await say(dp, bot, "Hello everyone! <New feature>", uid=777)
    check("broadcast preview shown", "Broadcast Preview" in sess.sent()[-1].text)
    await tap(dp, bot, "admin:bc_confirm", uid=777)
    bc_report = sess.sent()[-1].text
    check(
        "broadcast completes cleanly with blocked user counted in Failed/Blocked",
        "Broadcast Complete" in bc_report and "Failed/Blocked: <b>1</b>" in bc_report,
    )

    await bot.session.close()
    print("FAILED:", check.failed)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        if os.path.exists(DB):
            os.remove(DB)
