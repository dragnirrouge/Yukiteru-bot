import asyncio, os, logging, sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
import aiohttp

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONEROO_KEY = os.getenv("MONEROO_SECRET_KEY")
MONEROO_API = "https://api.moneroo.io/checkout/v1/initialize"

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN or not MONEROO_KEY:
    sys.exit("Manque BOT_TOKEN ou MONEROO_SECRET_KEY")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(f"👑 Salut {message.from_user.first_name}!\n\nYUKITERU EN LIGNE\n\nTape /encaisser 5000 pour lien MTN/Airtel XAF")

@dp.message(Command("encaisser"))
async def encaisser(message: types.Message):
    try:
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            await message.answer("Utilise: /encaisser 5000")
            return
        montant = int(args[1])
        payload = {
            "amount": montant,
            "currency": "XAF",
            "description": f"Paiement {montant} XAF",
            "customer": {"email": f"{message.from_user.id}@bot.cg", "name": message.from_user.first_name},
            "success_url": "https://t.me/",
            "failed_url": "https://t.me/"
        }
        headers = {"Authorization": f"Bearer {MONEROO_KEY}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(MONEROO_API, json=payload, headers=headers) as resp:
                data = await resp.json()
                url = data.get("checkout_url") or data.get("data",{}).get("checkout_url")
                if url:
                    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="💸 Payer maintenant", url=url)]])
                    await message.answer(f"✅ Lien {montant} XAF:\n{url}", reply_markup=kb)
                else:
                    await message.answer(f"❌ Erreur: {data}")
    except Exception as e:
        await message.answer("Erreur, reessaie")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
