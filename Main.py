import os, asyncio, threading
from flask import Flask
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import aiohttp

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONEROO_SECRET = os.getenv("MONEROO_SECRET_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

@app.route('/')
def home():
    return "YUKITERU EN LIGNE"

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(f"👑 Salut {message.from_user.first_name}!\n\nYUKITERU EN LIGNE ✅\n\nTape /encaisser 5000")

@dp.message(Command("encaisser"))
async def encaisser_cmd(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Utilise: /encaisser 5000")
            return
        montant = int(parts[1])

        url = "https://api.moneroo.io/v1/payments/initialize"
        headers = {
            "Authorization": f"Bearer {MONEROO_SECRET}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "amount": montant,
            "currency": "XAF",
            "description": f"Paiement {montant} XAF",
            "return_url": "https://t.me/YukiAnimeBot",
            "customer": {
                "email": f"{message.from_user.id}@yukiteru.bot",
                "first_name": message.from_user.first_name or "Client",
                "last_name": "Yukiteru"
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                print(f"MONEROO {resp.status}: {data}")
                if resp.status not in [200, 201]:
                    await message.answer(f"❌ Erreur Moneroo {resp.status}:\n{data}")
                    return
                d = data.get("data", data)
                link = d.get("checkout_url") or d.get("checkoutUrl")
                await message.answer(f"💸 Lien {montant} XAF:\n{link}\nID: {d.get('id')}")

    except Exception as e:
        print(f"ERREUR: {e}")
        await message.answer(f"Erreur debug: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
