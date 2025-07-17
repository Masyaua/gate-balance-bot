import asyncio
from aiogram import Bot, Dispatcher, types, executor
from gate_api import get_ledger_entries, get_total_balance
from dotenv import load_dotenv
import os
import json
import time

load_dotenv()

TG_TOKEN = os.getenv("TELEGRAM_TOKEN")
TG_USER_ID = int(os.getenv("TELEGRAM_USER_ID"))

bot = Bot(token=TG_TOKEN)
dp = Dispatcher(bot)

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {"last_ledger_id": 0, "last_balance": {}}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def format_ledger(entry):
    sign = "📥" if float(entry['amount']) > 0 else "📤"
    reason = entry['type'].replace("_", " ").title()
    return f"{sign} {reason}: {entry['amount']} {entry['currency']}"

def format_balance_change(new, old):
    diffs = []
    for currency in new:
        new_amt = float(new[currency])
        old_amt = float(old.get(currency, 0))
        diff = new_amt - old_amt
        if abs(diff) > 0.0001:
            emoji = "🟢" if diff > 0 else "🔴"
            diffs.append(f"{emoji} {currency}: {new_amt:.4f} ({diff:+.4f})")
    return diffs

async def check_ledger():
    state = load_state()
    entries = get_ledger_entries(limit=50)
    new_entries = [e for e in entries if e['id'] > state["last_ledger_id"]]
    new_entries.sort(key=lambda x: x['id'])
    for entry in new_entries:
        msg = format_ledger(entry)
        await bot.send_message(TG_USER_ID, msg)
        state["last_ledger_id"] = max(state["last_ledger_id"], entry['id'])
    save_state(state)

async def check_balance():
    state = load_state()
    new_balance = get_total_balance()
    changes = format_balance_change(new_balance, state.get("last_balance", {}))
    if changes:
        msg = "📊 Изменение баланса:\n" + "\n".join(changes)
        await bot.send_message(TG_USER_ID, msg)
    state["last_balance"] = new_balance
    save_state(state)

async def scheduler():
    while True:
        try:
            await check_ledger()
        except Exception as e:
            await bot.send_message(TG_USER_ID, f"⚠️ Ошибка в check_ledger: {e}")
        await asyncio.sleep(1800)
        try:
            await check_balance()
        except Exception as e:
            await bot.send_message(TG_USER_ID, f"⚠️ Ошибка в check_balance: {e}")

@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    await message.answer("🤖 Бот отслеживает баланс и движения на Gate.io")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler())
    executor.start_polling(dp)
