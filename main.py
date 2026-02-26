import asyncio
import json
import os
import time
import sys
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors

# ================= ENV VARIABLES =================
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not API_ID or not API_HASH or not BOT_TOKEN:
    print("❌ Missing environment variables!")
    sys.exit(1)

API_ID = int(API_ID)

# ================= TELEGRAM CLIENT =================
client = TelegramClient("/tmp/neet2", API_ID, API_HASH)
SESSION_FILE = "/tmp/neet_sessions.json"

IST = timezone(timedelta(hours=5, minutes=30))
TARGET = datetime(2026, 5, 3, 0, 0, 0, tzinfo=IST)

# ================= 50+ QUOTES =================
QUOTES = [ ... ]  # (poori list yahan paste karo)

# ================= SESSION HANDLING =================
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sessions(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

active_sessions = load_sessions()

# ================= RESUME ALL COUNTDOWNS ON START =================
async def resume_all_countdowns():
    for chat_id_str, data in list(active_sessions.items()):
        if not data.get("active"):
            continue
        chat_id = int(chat_id_str)
        message_id = data["message_id"]
        try:
            msg = await client.get_messages(chat_id, ids=message_id)
            if not msg:
                del active_sessions[chat_id_str]
                save_sessions(active_sessions)
                continue
        except Exception:
            del active_sessions[chat_id_str]
            save_sessions(active_sessions)
            continue

        asyncio.create_task(run_countdown(chat_id, message_id, resume=True))
        print(f"🔄 Resumed countdown in chat {chat_id}")

# ================= COUNTDOWN FUNCTION =================
async def run_countdown(chat_id, message_id, resume=False):
    if resume:
        # Resume hote hi last_quote track reset karo
        active_sessions[str(chat_id)]["last_quote"] = time.monotonic()
        active_sessions[str(chat_id)]["quote_index"] = 0
        save_sessions(active_sessions)

    while True:
        loop_start = time.monotonic()
        session = active_sessions.get(str(chat_id))
        if not session or not session.get("active"):
            break

        now = datetime.now(IST)
        remaining = TARGET - now

        if remaining.total_seconds() <= 0:
            await client.edit_message(
                chat_id,
                message_id,
                "🎉 **NEET 2026 – The Big Day is Here!**\n\nBest of luck future doctor! 🩺✨"
            )
            active_sessions.pop(str(chat_id), None)
            save_sessions(active_sessions)
            break

        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        # Quote rotate every 30 seconds
        if loop_start - session["last_quote"] >= 30:
            session["quote_index"] = (session["quote_index"] + 1) % len(QUOTES)
            session["last_quote"] = loop_start
            save_sessions(active_sessions)

        quote = QUOTES[session["quote_index"]]

        text = (
            f"🩺 **LIVE NEET 2026 COUNTDOWN**\n\n"
            f"🗓️ **3 May 2026**\n\n"
            f"{quote}\n\n"
            f"⏳ **Time Left:**\n"
            f"📅 {days} Days\n"
            f"⏰ {hours:02d}:{minutes:02d}:{seconds:02d}"
        )

        # Edit with retry & FloodWait handling
        retries = 3
        for attempt in range(retries):
            try:
                await client.edit_message(chat_id, message_id, text)
                break
            except errors.FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception as e:
                if attempt == retries - 1:
                    print(f"⚠️ Edit failed: {e}")
                    active_sessions.pop(str(chat_id), None)
                    save_sessions(active_sessions)
                    return
                await asyncio.sleep(1)

        elapsed = time.monotonic() - loop_start
        await asyncio.sleep(max(0, 1.0 - elapsed))  # 1 second update

    # Cleanup
    if str(chat_id) in active_sessions and not active_sessions[str(chat_id)]["active"]:
        del active_sessions[str(chat_id)]
        save_sessions(active_sessions)

# ================= COMMAND HANDLER =================
@client.on(events.NewMessage)
async def handler(event):
    if not event.raw_text:
        return

    text = event.raw_text.lower().strip()
    chat_id = event.chat_id

    if text == "/start":
        await event.respond(
            "👋 **Welcome to NEET 2026 Countdown Bot!**\n\n"
            "This bot shows a live countdown to NEET 2026 (3rd May) with motivational quotes.\n\n"
            "**Commands:**\n"
            "/neet - Start the countdown\n"
            "/stop - Stop the countdown\n\n"
            "Updates every second, quotes change every 30 seconds.\n"
            "Good luck with your preparation! 🩺✨\n\n"
            "💞 **Developer:** @ll_VIPIN_ll"
        )

    elif text == "/neet":
        if str(chat_id) in active_sessions and active_sessions[str(chat_id)]["active"]:
            await event.respond("⚠️ Countdown already running in this chat!")
            return

        try:
            msg = await client.send_message(chat_id, "🩺 **NEET 2026 COUNTDOWN**\n\nInitialising...")
        except Exception as e:
            await event.respond(f"❌ Failed to start: {e}")
            return

        active_sessions[str(chat_id)] = {
            "message_id": msg.id,
            "quote_index": 0,
            "last_quote": time.monotonic(),
            "active": True,
        }
        save_sessions(active_sessions)

        asyncio.create_task(run_countdown(chat_id, msg.id))
        print(f"✅ Countdown started in chat {chat_id}")

    elif text == "/stop":
        if str(chat_id) in active_sessions and active_sessions[str(chat_id)]["active"]:
            active_sessions[str(chat_id)]["active"] = False
            save_sessions(active_sessions)
            await event.respond("🛑 Countdown stopped.")
            print(f"🛑 Countdown stopped in chat {chat_id}")
        else:
            await event.respond("❌ No active countdown in this chat.")

# ================= MAIN =================
async def main():
    try:
        await client.start(bot_token=BOT_TOKEN)
        me = await client.get_me()
        print(f"✅ Bot logged in as: @{me.username}")
        print("🚀 Bot Active – Commands: /neet , /stop , /start")
        print("🔄 Resuming previous countdowns...")
        await resume_all_countdowns()
        await client.run_until_disconnected()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
