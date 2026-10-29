"""
telegram_bot.py
----------------
E-Santé Bénin — Bot Telegram vocal
Messages vocaux → Whisper → Gemini → gTTS → Réponse vocale

Lancement :
    python telegram_bot.py

Dépendances :
    pip install python-telegram-bot requests pydub
"""

import os
import uuid
import base64
import tempfile
import httpx
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.request import HTTPXRequest

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
API_URL        = os.getenv("API_URL", "http://localhost:8000")

# ─────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────
sessions = {}


def get_session_id(user_id: int) -> str:
    if user_id not in sessions:
        sessions[user_id] = str(uuid.uuid4())
    return sessions[user_id]


async def reset_session(user_id: int):
    if user_id in sessions:
        session_id = sessions[user_id]
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.delete(f"{API_URL}/session/{session_id}")
        except Exception:
            pass
        del sessions[user_id]


# ─────────────────────────────────────────────
# APPELS API
# ─────────────────────────────────────────────
async def envoyer_texte(session_id: str, message: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{API_URL}/chat/text",
                data={
                    "message": message,
                    "session_id": session_id,
                    "canal": "telegram"
                }
            )
        return res.json()
    except Exception as e:
        print(f"❌ Erreur API texte: {e}")
        return {}


async def envoyer_audio_api(session_id: str, chemin_wav: str) -> dict:
    try:
        with open(chemin_wav, "rb") as f:
            audio_content = f.read()

        files = {"audio": ("recording.wav", audio_content, "audio/wav")}
        data = {
            "session_id": session_id,
            "canal": "telegram"
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            res = await client.post(
                f"{API_URL}/chat/audio",
                files=files,
                data=data
            )
        return res.json()
    except Exception as e:
        print(f"❌ Erreur API audio: {e}")
        return {}


# ─────────────────────────────────────────────
# HELPERS TELEGRAM
# ─────────────────────────────────────────────
async def envoyer_vocal(update: Update, audio_b64: str):
    """Envoie une réponse vocale MP3 sur Telegram."""
    try:
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            chemin_mp3 = f.name
            f.write(audio_bytes)
        with open(chemin_mp3, "rb") as f:
            await update.message.reply_voice(voice=f)
        os.remove(chemin_mp3)
    except Exception as e:
        print(f"❌ Erreur envoi vocal: {e}")


async def envoyer_maps(update: Update, hopital_info: dict):
    """Envoie la localisation de l'hôpital recommandé."""
    if not hopital_info:
        return
    texte = (
        f"📍 *Hôpital recommandé :*\n\n"
        f"🏥 *{hopital_info['nom']}*\n"
        f"📌 {hopital_info['ville']}\n"
        f"📞 {hopital_info['tel']}\n\n"
        f"🗺️ [Voir sur Google Maps]({hopital_info['lien']})"
    )
    await update.message.reply_text(texte, parse_mode="Markdown")


async def envoyer_badge_urgence(update: Update, texte: str):
    """Envoie le badge d'urgence si détecté."""
    t = texte.lower()
    if "rouge" in t:
        await update.message.reply_text(
            "🔴 *Urgence rouge* — Consultez immédiatement !",
            parse_mode="Markdown"
        )
    elif "orange" in t:
        await update.message.reply_text(
            "🟠 *Urgence orange* — Consultation recommandée dans les 2 à 4 heures.",
            parse_mode="Markdown"
        )
    elif "vert" in t or "non urgent" in t:
        await update.message.reply_text(
            "🟢 *Situation non urgente* — Suivez les conseils donnés.",
            parse_mode="Markdown"
        )


# ─────────────────────────────────────────────
# HANDLERS
# ─────────────────────────────────────────────
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — Démarre une nouvelle consultation."""
    user_id = update.effective_user.id
    await reset_session(user_id)
    session_id = get_session_id(user_id)

    # Message d'accueil immédiat pendant que Gemini répond
    await update.message.reply_text(
        "👋 Bienvenue sur *E-Santé Bénin* !\n\nUn instant...",
        parse_mode="Markdown"
    )

    data = await envoyer_texte(session_id, "Bonjour")

    if data.get("audio"):
        await envoyer_vocal(update, data["audio"])
    else:
        await update.message.reply_text(
            "Envoyez un 🎤 message vocal pour commencer votre consultation.",
        )


async def handle_nouveau(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/nouveau — Nouvelle consultation."""
    user_id = update.effective_user.id
    await reset_session(user_id)
    await update.message.reply_text(
        "🔄 Session réinitialisée.\nEnvoyez /start pour démarrer une nouvelle consultation !"
    )


async def handle_vocal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les messages vocaux."""
    user_id    = update.effective_user.id
    session_id = get_session_id(user_id)

    chemin_ogg = None
    chemin_wav = None

    try:
        # 1. Télécharger OGG depuis Telegram
        tg_file = await context.bot.get_file(update.message.voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            chemin_ogg = f.name
        await tg_file.download_to_drive(chemin_ogg)

        # 2. Convertir OGG → WAV 16kHz mono
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_ogg(chemin_ogg)
            audio = audio.set_frame_rate(16000).set_channels(1)
            chemin_wav = chemin_ogg.replace(".ogg", ".wav")
            audio.export(chemin_wav, format="wav")
        except Exception as e:
            print(f"❌ Conversion audio: {e}")
            await update.message.reply_text(
                "❌ Erreur de conversion audio. "
                "Assurez-vous que pydub et ffmpeg sont installés."
            )
            return

        # 3. Envoyer à FastAPI
        data = await envoyer_audio_api(session_id, chemin_wav)

        if not data:
            await update.message.reply_text("❌ Erreur de connexion. Le serveur est-il démarré ?")
            return

        if data.get("error"):
            await update.message.reply_text(f"⚠️ {data['error']}")
            return

        # 4. Réponse vocale
        if data.get("audio"):
            await envoyer_vocal(update, data["audio"])

        # 5. Carte Maps
        if data.get("hopital_info"):
            await envoyer_maps(update, data["hopital_info"])

        # 6. Badge urgence
        if data.get("response"):
            await envoyer_badge_urgence(update, data["response"])

        # 7. Fin consultation
        if data.get("fin_consultation"):
            await update.message.reply_text(
                "✅ *Consultation enregistrée.*\n\n"
                "Vous pouvez continuer à poser des questions ou\n"
                "envoyer /nouveau pour une nouvelle consultation.",
                parse_mode="Markdown"
            )

    except Exception as e:
        print(f"❌ Erreur handle_vocal: {e}")
        await update.message.reply_text("❌ Une erreur s'est produite. Veuillez réessayer.")

    finally:
        for f in [chemin_ogg, chemin_wav]:
            if f and os.path.exists(f):
                os.remove(f)


async def handle_texte(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gère les messages texte."""
    user_id    = update.effective_user.id
    session_id = get_session_id(user_id)

    await update.message.reply_chat_action("typing")

    data = await envoyer_texte(session_id, update.message.text)

    if not data:
        await update.message.reply_text("❌ Erreur de connexion.")
        return

    if data.get("audio"):
        await envoyer_vocal(update, data["audio"])

    if data.get("hopital_info"):
        await envoyer_maps(update, data["hopital_info"])

    if data.get("response"):
        await envoyer_badge_urgence(update, data["response"])

    if data.get("fin_consultation"):
        await update.message.reply_text(
            "✅ *Consultation enregistrée.*\n\nEnvoyez /nouveau pour une nouvelle consultation.",
            parse_mode="Markdown"
        )


# ─────────────────────────────────────────────
# LANCEMENT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("🤖 Démarrage du bot Telegram E-Santé Bénin...")
    print(f"   API : {API_URL}")

    # Timeout élevé pour Telegram + Whisper + Gemini
    trequest = HTTPXRequest(
        connect_timeout=60,
        read_timeout=120,
        write_timeout=60,
        media_write_timeout=120
    )

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(trequest).build()

    app.add_handler(CommandHandler("start",   handle_start))
    app.add_handler(CommandHandler("nouveau", handle_nouveau))
    app.add_handler(MessageHandler(filters.VOICE, handle_vocal))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_texte))

    print("✅ Bot en attente de messages...")
    app.run_polling()