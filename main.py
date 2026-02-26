import asyncio
import json
import os
import time
from datetime import datetime, timezone, timedelta
from telethon import TelegramClient, events, errors

# Environment variables se credentials lena (Railway/Koyeb par set karein)
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

client = TelegramClient("neet2", API_ID, API_HASH)

SESSION_FILE = "neet_sessions.json"

IST = timezone(timedelta(hours=5, minutes=30))
TARGET = datetime(2026, 5, 3, 0, 0, 0, tzinfo=IST)

# 50+ MOTIVATIONAL QUOTES
QUOTES = [
    "✨ Dreams don't work unless you do.",
    "🩺 A doctor's biggest miracle is perseverance.",
    "📚 One step at a time – NEET is just a milestone.",
    "💪 Your future patients are waiting for you.",
    "🌟 Consistency beats intensity.",
    "🧠 Train your mind like you train your muscles.",
    "🎯 Focus on the goal, not the obstacles.",
    "💊 Every page you read brings you closer.",
    "⚡ Success is the sum of small efforts, repeated.",
    "🎓 The white coat is waiting for you.",
    "🕯️ Be the light in someone's life – study on.",
    "🌅 Today's hard work is tomorrow's reward.",
    "🩻 A NEET rank is just a number; knowledge is forever.",
    "📖 Read like your life depends on it – because someone's will.",
    "🏥 The world needs more dedicated doctors. Be one.",
    "⏳ Time is precious – use every second wisely.",
    "💧 Little strokes fell great oaks.",
    "🌱 Plant the seeds of knowledge now, harvest success later.",
    "🚀 You are closer than you think.",
    "💡 Every mistake is a lesson in disguise.",
    "🛡️ Protect your study time like a treasure.",
    "💞 Believe in yourself as much as we believe in you.",
    "🔬 Science is magic that works – master it.",
    "⚕️ Heal the world, starting with your own determination.",
    "🌠 Shoot for the moon; even if you miss, you'll land among stars.",
    "🧘 Calm mind, focused study, bright future.",
    "📅 Days are numbered – make each one count.",
    "🏆 Rank is temporary, knowledge is permanent.",
    "💎 You are a diamond in the making.",
    "🌻 Stay positive, work hard, make it happen.",
    "🕊️ Let your dreams fly higher than the marks.",
    "💪 No pressure, no diamond.",
    "⚡ Wake up with determination, go to bed with satisfaction.",
    "🩺 Future doctor: your journey inspires us all.",
    "🧪 Every experiment begins with a single step.",
    "📝 Your notes today are your patient's history tomorrow.",
    "🫀 A doctor's heart beats for others.",
    "🧬 DNA of success: Dedication, Never giving up, Action.",
    "🏅 You're not just preparing for an exam, you're preparing for a calling.",
    "🌙 Late nights now will save lives later.",
    "☕ Chai aur NCERT – perfect combination!",
    "👨‍⚕️👩‍⚕️ Future MBBS student: that's you!",
    "📖 Every chapter mastered is a life saved.",
    "💉 Stay sharp, stay focused.",
    "🏥 From NEET to OPD – you'll get there.",
    "🧘‍♂️ Breathe, believe, achieve.",
    "🎯 Your target: 720/720. Your weapon: hard work.",
    "🛤️ The road is long, but the destination is worth it.",
    "🌟 Shine bright like a topper.",
    "📚 Books are your best friends right now.",
    "💤 Sleep is important, but so is your dream.",
    "🔥 Burn the midnight oil, but don't burn out.",
    "🎉 Celebrate small victories – every topic mastered is a win.",
    "🤝 You're not alone – millions are on this journey with you.",
    "🌈 After the rain comes the rainbow – after NEET comes MBBS.",
    "⏰ Every second counts, every mark matters.",
    "💯 Be the 1% who never gives up.",
]

# ---------- Session Load/Save ----------
def load_sessions():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sessions(data):
    with open(SESSION_FILE, "w") as f:
        json.dump(data, f, indent=2)

active_sessions = load_sessions()

# ---------- Resume All Countdowns on Start ----------
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

# ---------- Countdown Task ----------
async def run_countdown(chat_id, message_id, resume=False):
    if resume:
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
                "🎉 **NEET 2026 – The Big Day is Here!**\n\nBest of luck future doctors! 🩺✨"
            )
            active_sessions.pop(str(chat_id), None)
            save_sessions(active_sessions)
            break

        days = remaining.days
        hours, rem = divmod(remaining.seconds, 3600)
        minutes, seconds = divmod(rem, 60)

        # Change quote every 30 seconds
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
                wait = e.seconds
                print(f"⏳ Flood wait in chat {chat_id}: {wait} seconds")
                await asyncio.sleep(wait)
            except Exception as e:
                if attempt == retries - 1:
                    print(f"⚠️ Permanent edit failed in chat {chat_id}: {e}")
                    active_sessions.pop(str(chat_id), None)
                    save_sessions(active_sessions)
                    return
                await asyncio.sleep(1)

        elapsed = time.monotonic() - loop_start
        sleep_time = max(0, 5.0 - elapsed)  # 5 seconds interval
        await asyncio.sleep(sleep_time)

    # Clean up if loop ended
    if str(chat_id) in active_sessions and not active_sessions[str(chat_id)]["active"]:
        del active_sessions[str(chat_id)]
        save_sessions(active_sessions)

# ---------- Command Handler ----------
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
            "/neet - Start the countdown in this chat\n"
            "/stop - Stop the countdown in this chat\n\n"
            "The countdown updates every 5 seconds and changes quotes every 30 seconds.\n"
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

# ---------- Main ----------
async def main():
    await client.start(bot_token=BOT_TOKEN)
    me = await client.get_me()
    print(f"✅ Bot logged in as: @{me.username}")
    print("🚀 Bot Active – Commands: /neet , /stop , /start")
    print("🔄 Resuming previous countdowns...")
    await resume_all_countdowns()
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
