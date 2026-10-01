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
    return "YUKITERU V2 EN LIGNE - Paiement + Verif"

async def verify_payment(payment_id: str):
    url = f"https://api.moneroo.io/v1/payments/{payment_id}/verify"
    headers = {"Authorization": f"Bearer {MONEROO_SECRET}"}
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url, headers=headers) as r:
            data = await r.json()
            print(f"VERIFY {r.status}: {data}")
            return r.status, data

@dp.message(Command("start"))
async def start_cmd(m: types.Message):
    await m.answer(f"👑 YUKITERU V2\n\n/encaisser 2000 -> créer lien\n/verifier py_xxx -> vérifier paiement\n\nTape /encaisser 5000")

@dp.message(Command("encaisser"))
async def encaisser_cmd(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Utilise: /encaisser 2000")
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
            "return_url": f"https://t.me/{(await bot.get_me()).username}",
            "customer": {
                "email": f"{message.from_user.id}@yukiteru.bot",
                "first_name": message.from_user.first_name or "Client",
                "last_name": "Yukiteru"
            }
        }
        async with aiohttp.ClientSession() as sess:
            async with sess.post(url, json=payload, headers=headers) as r:
                data = await r.json()
                if r.status not in (200,201):
                    await message.answer(f"❌ Erreur {r.status}: {data}")
                    return
                d = data.get("data", data)
                link = d.get("checkout_url")
                pid = d.get("id")
                await message.answer(f"💸 LIEN {montant} XAF ✅\n{link}\n\nID: {pid}\n\nAprès paiement tape:\n/verifier {pid}")
    except Exception as e:
        await message.answer(f"Erreur: {e}")

@dp.message(Command("verifier"))
async def verifier_cmd(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.answer("Utilise: /verifier py_wtprtx...")
            return
        pid = parts[1].strip()
        await message.answer(f"⏳ Vérification {pid}...")
        status, data = await verify_payment(pid)

        d = data.get("data", data)
        pay_status = d.get("status") or data.get("status") or "inconnu"

        if pay_status.lower() in ["success", "successful", "paid", "completed"]:
            await message.answer(f"✅ PAIEMENT RÉUSSI!\n\nMontant: {d.get('amount')} {d.get('currency')}\nID: {pid}\nStatus: {pay_status}\n\nTu peux livrer! 💰")
        elif pay_status.lower() in ["pending", "initiated", "processing"]:
            await message.answer(f"⏳ En attente...\nStatus: {pay_status}\nLe client n'a pas encore payé ou c'est en cours.")
        else:
            await message.answer(f"❌ Pas payé / Échoué\nStatus: {pay_status}\nData: {data}")

    except Exception as e:
        await message.answer(f"Erreur verif: {e}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
