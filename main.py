"""
main.py
--------
E-Santé Bénin — Backend FastAPI
Whisper (ASR) + Gemini (IA) + gTTS (TTS) + MySQL (DB)

Fonctionnalités :
- Répartition intelligente des patients sur 8 hôpitaux
  (Abomey-Calavi et Godomey) selon la charge en temps réel

Lancement :
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import sys
import os

# Forcer l'encodage UTF-8 sur Windows (support des logs et emojis sans crash charmap)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import re
import json
import uuid
import base64
import asyncio
import tempfile
import unicodedata
import hmac
import hashlib
import time
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form, Request, Depends, HTTPException, Header, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
whisper = None  # Chargement paresseux (lazy loading) pour optimiser le démarrage
import httpx
from gtts import gTTS
import database

# ─────────────────────────────────────────────
# CONFIGURATION (Variables d'environnement / .env)
# ─────────────────────────────────────────────
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL     = os.getenv(
    "GEMINI_URL",
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"
)
WHISPER_MODEL  = os.getenv("WHISPER_MODEL", "small")

# ─────────────────────────────────────────────
# GROQ — Chat (Llama 3.3 70B)
# ─────────────────────────────────────────────
GROQ_CHAT_URL   = os.getenv("GROQ_CHAT_URL", "https://api.groq.com/openai/v1/chat/completions")
GROQ_CHAT_MODEL = os.getenv("GROQ_CHAT_MODEL", "qwen/qwen3.8-27b")
UTILISER_GROQ_CHAT = os.getenv("UTILISER_GROQ_CHAT", "True").lower() in ("true", "1", "yes")

# ─────────────────────────────────────────────
# GROQ — Transcription audio (Whisper hébergé)
# ─────────────────────────────────────────────
GROQ_API_KEY    = os.getenv("GROQ_API_KEY", "")
GROQ_AUDIO_URL  = os.getenv("GROQ_AUDIO_URL", "https://api.groq.com/openai/v1/audio/transcriptions")
GROQ_MODEL      = os.getenv("GROQ_MODEL", "whisper-large-v3")
UTILISER_GROQ_WHISPER = os.getenv("UTILISER_GROQ_WHISPER", "True").lower() in ("true", "1", "yes")

# Durée d'inactivité avant expiration d'une session (en minutes)
SESSION_EXPIRATION_MINUTES = int(os.getenv("SESSION_EXPIRATION_MINUTES", "120"))

# ─────────────────────────────────────────────
# AUTHENTIFICATION PERSONNEL SOIGNANT (DASHBOARD)
# ─────────────────────────────────────────────
DASHBOARD_USERNAME   = os.getenv("DASHBOARD_USERNAME", "admin")
DASHBOARD_PASSWORD   = os.getenv("DASHBOARD_PASSWORD", "esante_benin_2026")
DASHBOARD_SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY", "esante_benin_secret_key_2026_super_secure")


class LoginRequest(BaseModel):
    username: str
    password: str


def generer_token(username: str) -> str:
    timestamp = int(time.time())
    payload = f"{username}:{timestamp}"
    signature = hmac.new(
        DASHBOARD_SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode()).decode()


def valider_token(token: str) -> bool:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        parts = decoded.split(":")
        if len(parts) != 3:
            return False
        username, timestamp_str, sig = parts
        timestamp = int(timestamp_str)
        # Expiration 24 heures (86400 secondes)
        if time.time() - timestamp > 86400:
            return False
        payload = f"{username}:{timestamp}"
        expected_sig = hmac.new(
            DASHBOARD_SECRET_KEY.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected_sig) and username == DASHBOARD_USERNAME
    except Exception:
        return False


async def verifier_authentification_soignant(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification requise pour accéder aux dossiers médicaux.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization
    if authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    if not valider_token(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide ou expirée. Veuillez vous reconnecter.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

# ─────────────────────────────────────────────
# BASE HÔPITAUX — ABOMEY-CALAVI ET GODOMEY
# ─────────────────────────────────────────────
HOPITAUX_ABOMEY_CALAVI = [
    {
        "id": "CHIC",
        "nom": "CHIC — Centre Hospitalier International de Calavi",
        "ville": "Abomey-Calavi",
        "lien": "https://www.google.com/maps/search/?api=1&query=Centre+Hospitalier+International+de+Calavi",
        "tel": "+229 01 21 40 01 00"  # Standard (+229 01 21 40 01 11 pour RDV)
    },
    {
        "id": "HZ_CALAVI",
        "nom": "Hôpital de Zone Abomey-Calavi / Sô-Ava",
        "ville": "Abomey-Calavi",
        "lien": "https://www.google.com/maps/search/?api=1&query=Hopital+de+Zone+Abomey+Calavi+So+Ava",
        "tel": "+229 01 21 36 01 50"  # Ligne standard CHUZ-AS (+229 01 65 06 43 65)
    },
    {
        "id": "CLINIQUE_CALAVI",
        "nom": "Clinique Centrale de Calavi",
        "ville": "Abomey-Calavi",
        "lien": "https://www.google.com/maps/search/?api=1&query=Clinique+Centrale+de+Calavi",
        "tel": "+229 01 99 47 68 27"  # Urgences 24h/24 (+229 01 21 36 37 44)
    },
    {
        "id": "CS_KPOTA",
        "nom": "Centre de Santé Calavi Kpota",
        "ville": "Abomey-Calavi",
        "lien": "https://www.google.com/maps/search/?api=1&query=Centre+de+Sante+Calavi+Kpota",
        "tel": "+229 01 67 04 35 47"
    },
]

HOPITAUX_GODOMEY = [
    {
        "id": "MAHOULE",
        "nom": "Clinique Mahoulé de Godomey",
        "ville": "Godomey",
        "lien": "https://www.google.com/maps/search/?api=1&query=Clinique+Mahoule+de+Godomey",
        "tel": "+229 01 91 91 93 43"  # Dekoungbé, Godomey
    },
    {
        "id": "ST_JEAN",
        "nom": "Hôpital Saint Jean Maria-Gléta",
        "ville": "Godomey",
        "lien": "https://www.google.com/maps/search/?api=1&query=Hopital+Saint+Jean+Maria+Gleta",
        "tel": "+229 01 69 27 91 10"  # Maria-Gléta / Togba (+229 01 95 52 77 72)
    },
    {
        "id": "GRACE_VIE",
        "nom": "Clinique La Grâce de Vie Godomey",
        "ville": "Godomey",
        "lien": "https://www.google.com/maps/search/?api=1&query=Clinique+La+Grace+de+Vie+Godomey",
        "tel": "+229 01 50 89 05 25"  # Hlacomey, Godomey
    },
    {
        "id": "ADC",
        "nom": "Centre de Santé Eau-Vive (Clinique ADC)",
        "ville": "Godomey",
        "lien": "https://www.google.com/maps/search/?api=1&query=Centre+de+Sante+Eau+Vive+Godomey",
        "tel": "+229 01 21 36 01 50"  # Régulation zone Calavi/Godomey (SAMU : 112)
    },
]

# Autres villes (format national ARCEP 10 chiffres + coordonnées GPS)
HOPITAUX_AUTRES = {
    "CNHU": {
        "nom": "CNHU-HKM — Centre National Hospitalier Universitaire",
        "ville": "Cotonou",
        "lien": "https://maps.google.com/?q=6.3654,2.4183",
        "tel": "+229 01 21 30 06 56"
    },
    "Porto-Novo": {
        "nom": "CHUD Ouémé-Plateau",
        "ville": "Porto-Novo",
        "lien": "https://maps.google.com/?q=6.4739,2.6131",
        "tel": "+229 01 20 21 35 90"
    },
    "Parakou": {
        "nom": "CHUD Borgou",
        "ville": "Parakou",
        "lien": "https://maps.google.com/?q=9.3358,2.6364",
        "tel": "+229 01 23 61 07 17"
    },
    "Bohicon": {
        "nom": "Hôpital de Zone de Bohicon",
        "ville": "Bohicon",
        "lien": "https://maps.google.com/?q=7.1791,2.0670",
        "tel": "+229 01 22 51 02 00"
    },
    "Natitingou": {
        "nom": "Centre Hospitalier Départemental de l'Atacora",
        "ville": "Natitingou",
        "lien": "https://maps.google.com/?q=10.3067,1.3806",
        "tel": "+229 01 94 99 83 92"
    },
    "Lokossa": {
        "nom": "CHD Mono/Couffo (Lokossa)",
        "ville": "Lokossa",
        "lien": "https://maps.google.com/?q=6.6333,1.7167",
        "tel": "+229 01 22 41 15 90"
    },
    "Kandi": {
        "nom": "Hôpital de Zone de Kandi",
        "ville": "Kandi",
        "lien": "https://maps.google.com/?q=11.1333,2.9333",
        "tel": "+229 01 23 63 00 85"
    },
    "Djougou": {
        "nom": "CHD Donga (Djougou)",
        "ville": "Djougou",
        "lien": "https://maps.google.com/?q=9.7080,1.6659",
        "tel": "+229 01 23 80 01 40"
    },
}


# ─────────────────────────────────────────────
# RÉPARTITION INTELLIGENTE DES PATIENTS
# ─────────────────────────────────────────────
def choisir_hopital_moins_charge(hopitaux: list) -> dict:
    """
    Vérifie dans MySQL le nombre de patients orientés vers chaque hôpital
    dans les 2 dernières heures et retourne le moins chargé.
    """
    try:
        charges = {}
        for h in hopitaux:
            count = database.compter_orientations_recentes(h["nom"], heures=2)
            charges[h["id"]] = count
            print(f"   📊 {h['nom']} : {count} patient(s) orienté(s) (2h)")

        id_moins_charge = min(charges, key=charges.get)
        hopital_choisi = next(h for h in hopitaux if h["id"] == id_moins_charge)
        charge_min = charges[id_moins_charge]
        print(f"   ✅ Hôpital recommandé : {hopital_choisi['nom']} ({charge_min} patient(s))")
        return hopital_choisi

    except Exception as e:
        print(f"⚠️ Erreur répartition : {e} → retour au premier hôpital")
        return hopitaux[0]


def normaliser_texte(texte: str) -> str:
    """Supprime les accents, la ponctuation superflue et met en minuscules."""
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(c for c in texte if unicodedata.category(c) != 'Mn')
    return texte.lower()


def detecter_hopital(texte_hopital: str, localisation: str = "") -> dict | None:
    texte = normaliser_texte(texte_hopital + " " + localisation)

    variantes_calavi = ["abomey", "calavi", "bome", "akassato", "kpota", "zinvi"]
    variantes_godomey = ["godome", "godomet", "godomei", "togba", "maria-gleta", "cocotier"]

    if any(v in texte for v in variantes_calavi):
        print("📍 Ville détectée : Abomey-Calavi → Répartition intelligente")
        return choisir_hopital_moins_charge(HOPITAUX_ABOMEY_CALAVI)
    elif any(v in texte for v in variantes_godomey):
        print("📍 Ville détectée : Godomey → Répartition intelligente")
        return choisir_hopital_moins_charge(HOPITAUX_GODOMEY)
    elif "cotonou" in texte or "cnhu" in texte:
        return HOPITAUX_AUTRES["CNHU"]
    elif "porto" in texte:
        return HOPITAUX_AUTRES["Porto-Novo"]
    elif "parakou" in texte:
        return HOPITAUX_AUTRES["Parakou"]
    elif "bohicon" in texte:
        return HOPITAUX_AUTRES["Bohicon"]
    elif "natitingou" in texte:
        return HOPITAUX_AUTRES["Natitingou"]
    elif "lokossa" in texte:
        return HOPITAUX_AUTRES["Lokossa"]
    elif "kandi" in texte:
        return HOPITAUX_AUTRES["Kandi"]
    elif "djougou" in texte:
        return HOPITAUX_AUTRES["Djougou"]
    return None


# ─────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────
app = FastAPI(title="E-Santé Bénin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

if UTILISER_GROQ_WHISPER:
    print("☁️ Transcription via Groq Whisper (cloud) — Whisper local non chargé")
    whisper_model = None
else:
    print("⏳ Chargement de Whisper local...")
    import whisper
    whisper_model = whisper.load_model(WHISPER_MODEL)
    print("✅ Whisper local prêt !")

from session_manager import session_manager


# ─────────────────────────────────────────────
# GESTION DES SESSIONS (REDIS + FALLBACK MÉMOIRE & MYSQL)
# ─────────────────────────────────────────────
def purger_sessions_expirees():
    """Supprime les sessions inactives depuis SESSION_EXPIRATION_MINUTES."""
    session_manager.purger_expirees()


def get_historique_memoire(session_id: str) -> list:
    """Retourne l'historique de la session (depuis Redis ou mémoire)."""
    return session_manager.get_historique(session_id)


def set_historique_memoire(session_id: str, historique: list):
    """Met à jour ou crée l'entrée de session avec TTL."""
    session_manager.set_historique(session_id, historique)


# ─────────────────────────────────────────────
# SYSTEM PROMPT GEMINI
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """
Tu es l'assistant médical conversationnel de "E-Santé Bénin".

RÔLE
- Tu aides les patients à décrire leurs symptômes.
- Tu expliques les causes probables de leurs maux.
- Tu fournis des conseils naturels pour soulager les maux mineurs.
- Tu évalues le niveau d'urgence.
- Tu orientes vers l'hôpital le plus proche et le moins chargé.
- Tu ne remplaces jamais un médecin.

PROTOCOLE DE CONVERSATION STRICT

ÉTAPE 0 — ACCUEIL ET IDENTIFICATION
- Salue chaleureusement le patient UNE SEULE FOIS, uniquement au tout premier message.
- Ne répète JAMAIS les salutations dans les échanges suivants de la conversation.
- Demande uniquement : prénom, âge et sexe.
- Attends que le patient réponde avec son prénom, âge et sexe avant de poser une autre question.
- Une fois les infos reçues, appelle le patient par son prénom uniquement, sans le resaluer.
- Demande : "Quels sont les maux dont vous souffrez ?"
- Attends la réponse du patient avant de continuer.

ÉTAPE 1 — COLLECTE DES SYMPTÔMES PRINCIPAUX
- Écoute attentivement les symptômes décrits.
- Pose des questions de précision si nécessaire.
- Après avoir compris les symptômes principaux, demande :
  "Avez-vous d'autres douleurs ou gênes associées à ces maux ?"
- Attends la réponse du patient avant de continuer.

ÉTAPE 1.5 — COLLECTE DES DOULEURS ASSOCIÉES
- Écoute les douleurs associées mentionnées.
- Note tous les symptômes secondaires.
- Ensuite demande : "Depuis combien de temps ressentez-vous ces symptômes ?"
- Attends la réponse du patient avant de continuer.

ÉTAPE 2 — COLLECTE DE LA DURÉE
- Attends la durée.
- Si pas claire, reformule la question.

ÉTAPE 2.5 — CAUSES PROBABLES
- Explique clairement et de façon pédagogique les causes probables des maux.
- Prends en compte TOUS les symptômes principaux et associés ainsi que l'âge et le sexe.
- Donne 2 à 3 causes probables pertinentes et bien expliquées.
- Utilise des formulations comme :
  "Ces symptômes pourraient être causés par..."
  "Il est possible que vous souffriez de... car..."
  "Cela pourrait être lié à... qui se manifeste souvent par..."
- Sois pédagogique et rassurant.
- Ne pose JAMAIS de diagnostic définitif.

ÉTAPE 3 — CONSEILS NATURELS POUR SOULAGER
- Propose des conseils UNIQUEMENT naturels et sans médicaments.
- Conseils autorisés :
  * Hydratation : boire beaucoup d'eau, tisanes, eau citronnée
  * Repos : se reposer, éviter les efforts
  * Alimentation : alimentation légère, fruits, légumes
  * Remèdes naturels : gingembre, citron, miel, feuilles de neem, décoctions locales
  * Compresses : froide ou chaude selon le cas
  * Hygiène : lavage des mains, propreté
- INTERDIT ABSOLUMENT : Ne prescris AUCUN médicament chimique, même le paracétamol ou l'ibuprofène.
- Avant de conseiller une tisane ou un remède naturel, précise toujours que le patient doit s'assurer qu'il ne suit pas un traitement médical en cours qui pourrait interagir avec ce remède.
- Si les maux sont graves, dis clairement qu'une consultation médicale urgente est nécessaire.

ÉTAPE 4 — ORIENTATION ET LOCALISATION

- Avant de déterminer le niveau d'urgence, relis attentivement TOUS les symptômes principaux, les douleurs associées, la durée d'évolution, l'âge et le sexe du patient mentionnés depuis le début de la conversation.
- Prends en compte que des symptômes en apparence légers peuvent devenir préoccupants selon leur durée d'évolution (par exemple une fièvre qui persiste plusieurs jours) ou selon l'âge du patient (les enfants en bas âge et les personnes âgées nécessitent une vigilance accrue).
- Détermine le niveau d'urgence selon ces critères STRICTS et EXCLUSIFS, dans cet ordre de priorité :

  ROUGE — urgence absolue, si AU MOINS UN de ces signes est présent :
    * Difficulté à respirer ou essoufflement
    * Douleur thoracique ou oppression dans la poitrine
    * Forte fièvre supérieure à 39 degrés persistante
    * Convulsions ou tremblements incontrôlables
    * Perte de connaissance ou confusion mentale
    * Saignement important
    * Douleur intense et soudaine
    * Paralysie ou perte de sensation
  → Message au patient : "Votre situation est une urgence médicale. Rendez-vous IMMÉDIATEMENT à l'hôpital sans attendre."

  ORANGE — situation sérieuse nécessitant une consultation rapide, si aucun signe rouge mais :
    * Fièvre entre 38 et 39 degrés
    * Douleurs modérées persistantes depuis plus de 24h
    * Vomissements ou diarrhée répétés
    * Symptômes qui s'aggravent progressivement
    * Doute sur la gravité de la situation
  → Message au patient : "Votre situation nécessite une consultation médicale dans les 2 à 4 heures qui suivent. Ne tardez pas à vous rendre à l'hôpital."

  VERT — situation non urgente, si aucun signe rouge ni orange :
    * Symptômes légers et stables
    * Maux courants sans aggravation
  → Message au patient : "Votre situation n'est pas urgente. Suivez les conseils donnés. Si les symptômes persistent ou s'aggravent après 24 à 48 heures, consultez un médecin."
- Si un symptôme mentionné par le patient ne correspond clairement à aucun des critères ci-dessus, classe par défaut en orange plutôt qu'en vert, par principe de précaution.

  - Demande : "Dans quelle ville ou quartier habitez-vous ?"
- Attends la réponse du patient.
- Note EXACTEMENT la ville ou le quartier mentionné dans le JSON final.
- Oriente vers l'hôpital approprié — le système trouvera automatiquement
  l'hôpital le moins chargé pour Abomey-Calavi et Godomey.
- Ensuite demande :
  "Avez-vous d'autres préoccupations ou questions avant de terminer ?"
- Attends la réponse du patient.
- Si le patient a d'autres questions, réponds-y complètement.
- Si le patient dit non ou qu'il n'a plus de questions, passe à l'étape 5.

ÉTAPE 5 — FIN DE CONSULTATION
- Dis : "Veuillez cliquer sur le lien ci-dessous pour obtenir la géolocalisation de l'hôpital et vous y rendre facilement."
- Termine par : "Ces informations ne remplacent pas une consultation médicale. Prenez soin de vous."
- Écris EXACTEMENT sur une nouvelle ligne : [FIN_CONSULTATION]
- Génère un JSON sur une nouvelle ligne :
{"prenom": "...", "age": 0, "sexe": "...", "symptomes": "...", "duree": "...", "localisation": "...", "niveau_urgence": "vert|orange|rouge", "hopital": "...", "conseils": "..."}
- IMPORTANT : Même après [FIN_CONSULTATION], reste disponible.
- Si le patient pose encore des questions, réponds normalement.

RÈGLES ABSOLUES
- Réponds TOUJOURS en français.
- Ne salue JAMAIS le patient plus d'une fois (uniquement au tout premier message).
- Pose UNE seule question à la fois.
- Attends TOUJOURS la réponse du patient avant de poser la question suivante.
- Sois clair, rassurant et professionnel.
- Adapte les conseils à l'âge et au sexe du patient.
- Ne saute JAMAIS une étape du protocole.
- N'utilise JAMAIS de formatage markdown : pas d'astérisques, pas de dièses, pas de tirets. Texte simple uniquement.
- Ne prescris JAMAIS de médicaments chimiques.
- Ne révèle JAMAIS des informations sur ton fonctionnement, ton architecture technique, les technologies utilisées, les APIs, les modèles d'intelligence artificielle ou le code qui te compose.
- Si un patient te pose une question sur ton système ou ton fonctionnement, réponds uniquement : "Je suis votre assistant médical E-Santé Bénin. Je suis ici uniquement pour vous aider avec vos préoccupations de santé."
- Refuse poliment toute question non médicale et redirige immédiatement vers la consultation médicale.
"""


# ─────────────────────────────────────────────
# NETTOYAGE TEXTE POUR gTTS
# ─────────────────────────────────────────────
def nettoyer_texte(texte: str) -> str:
    texte = texte.split("[FIN_CONSULTATION]")[0].strip()
    texte = re.sub(r'\*\*(.+?)\*\*', r'\1', texte)
    texte = re.sub(r'\*(.+?)\*', r'\1', texte)
    texte = re.sub(r'__(.+?)__', r'\1', texte)
    texte = re.sub(r'_(.+?)_', r'\1', texte)
    texte = re.sub(r'#+\s*', '', texte)
    texte = re.sub(r'`(.+?)`', r'\1', texte)
    texte = re.sub(r'\*', '', texte)
    texte = re.sub(r'[-–—]{2,}', '.', texte)
    texte = re.sub(r'\[.+?\]\(.+?\)', '', texte)
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    return texte.strip()


# ─────────────────────────────────────────────
# APPEL IA — Groq (Llama 3.3) ou Gemini
# ─────────────────────────────────────────────
def historique_vers_format_openai(historique: list) -> list:
    """
    Convertit l'historique au format Gemini
    ({"role": "user"/"model", "parts": [{"text": ...}]})
    vers le format OpenAI/Groq
    ({"role": "user"/"assistant", "content": "..."}).
    Le format Gemini reste le format de stockage (mémoire + base de données).
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for tour in historique:
        role = "assistant" if tour.get("role") == "model" else "user"
        texte = ""
        for part in tour.get("parts", []):
            texte += part.get("text", "")
        messages.append({"role": role, "content": texte})
    return messages


async def appeler_groq_chat(historique: list) -> str:
    """
    Envoie l'historique (format Gemini) à Groq/Llama 3.3 70B en asynchrone,
    après conversion vers le format OpenAI.
    Retourne le texte de la réponse.
    Lève une exception en cas d'échec (gérée par appeler_ia avec retry).
    """
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_CHAT_MODEL,
        "messages": historique_vers_format_openai(historique),
        "temperature": 0.7
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GROQ_CHAT_URL, headers=headers, json=data)

    if response.status_code != 200:
        raise Exception(f"Groq {response.status_code}: {response.text}")

    response_json = response.json()
    return response_json["choices"][0]["message"]["content"]


async def appeler_gemini_chat(historique: list) -> str:
    """
    Envoie l'historique (format Gemini natif) à l'API Gemini en asynchrone.
    Retourne le texte de la réponse.
    Lève une exception en cas d'échec (gérée par appeler_ia avec retry).
    """
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }
    data = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": historique
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(GEMINI_URL, headers=headers, json=data)

    if response.status_code != 200 or "candidates" not in response.json():
        raise Exception(f"Gemini {response.status_code}: {response.text}")

    response_json = response.json()
    return response_json["candidates"][0]["content"]["parts"][0]["text"]


async def appeler_ia(session_id: str, message: str) -> str:
    """
    Fonction principale asynchrone appelée par les routes /chat/text et /chat/audio.
    Utilise Groq (Llama 3.3 70B) ou Gemini selon UTILISER_GROQ_CHAT,
    avec retry asynchrone en cas d'erreur temporaire (503/429/timeout).
    L'historique est toujours stocké au format Gemini (mémoire + base de données).
    """
    # Charger depuis la mémoire ou depuis la DB si première fois
    historique = get_historique_memoire(session_id)
    if not historique:
        historique = database.get_historique(session_id) or []

    historique.append({
        "role": "user",
        "parts": [{"text": message}]
    })

    MAX_TENTATIVES = 3
    DELAI_RETRY    = 5  # secondes entre chaque tentative

    for tentative in range(1, MAX_TENTATIVES + 1):
        try:
            if UTILISER_GROQ_CHAT:
                bot_response = await appeler_groq_chat(historique)
            else:
                bot_response = await appeler_gemini_chat(historique)

            historique.append({
                "role": "model",
                "parts": [{"text": bot_response}]
            })
            set_historique_memoire(session_id, historique)
            return bot_response

        except Exception as e:
            erreur_str = str(e)
            est_temporaire = (
                "503" in erreur_str or "429" in erreur_str
                or "timeout" in erreur_str.lower() or "timed out" in erreur_str.lower()
            )

            if est_temporaire:
                print(f"⚠️ IA indisponible (tentative {tentative}/{MAX_TENTATIVES}): {erreur_str}")
                if tentative < MAX_TENTATIVES:
                    await asyncio.sleep(DELAI_RETRY)
                    continue
                else:
                    print(f"❌ IA indisponible après {MAX_TENTATIVES} tentatives.")
                    return "Je rencontre une difficulté technique. Veuillez réessayer dans un instant."
            else:
                print(f"❌ Erreur IA: {erreur_str}")
                return "Désolé, une erreur technique s'est produite."

    return "Je rencontre une difficulté technique. Veuillez réessayer."

# Alias pour compatibilité
appeler_gemini = appeler_ia


# ─────────────────────────────────────────────
# TRAITEMENT FIN DE CONSULTATION
# ─────────────────────────────────────────────
def traiter_fin_consultation(session_id: str, bot_response: str, canal: str = "web") -> dict | None:
    if "[FIN_CONSULTATION]" not in bot_response:
        return None

    try:
        lines = bot_response.split("\n")
        json_data = None
        for line in lines:
            line = line.strip()
            if line.startswith("{") and "niveau_urgence" in line:
                json_data = json.loads(line)
                break

        if not json_data:
            return None

        patient_id   = f"{canal.upper()}_{session_id[:8].upper()}"
        localisation = json_data.get("localisation", "")
        hopital_text = json_data.get("hopital", "")

        # Répartition intelligente pour Abomey-Calavi et Godomey
        hopital_info = detecter_hopital(hopital_text, localisation)
        hopital_nom  = hopital_info["nom"] if hopital_info else hopital_text

        historique = get_historique_memoire(session_id)

        database.sauvegarder_consultation(
            patient_id=patient_id,
            prenom=json_data.get("prenom", "Patient"),
            age=json_data.get("age", 0),
            sexe=json_data.get("sexe", ""),
            symptomes=json_data.get("symptomes", ""),
            duree=json_data.get("duree", ""),
            localisation=localisation,
            niveau_urgence=json_data.get("niveau_urgence", "vert"),
            hopital=hopital_nom,
            conseils=json_data.get("conseils", ""),
            conversation=json.dumps(historique, ensure_ascii=False),
            canal=canal
        )

        database.sauvegarder_session(
            session_id=session_id,
            patient_id=patient_id,
            prenom=json_data.get("prenom", ""),
            age=json_data.get("age", 0),
            sexe=json_data.get("sexe", ""),
            historique=historique
        )

        return hopital_info

    except Exception as e:
        print(f"Erreur fin consultation: {e}")
        return None


# ─────────────────────────────────────────────
# SYNTHÈSE VOCALE
# ─────────────────────────────────────────────
def generer_audio(texte: str) -> str:
    try:
        texte_propre = nettoyer_texte(texte)
        if not texte_propre:
            return ""

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            chemin_mp3 = f.name

        tts = gTTS(text=texte_propre, lang="fr", slow=False)
        tts.save(chemin_mp3)

        with open(chemin_mp3, "rb") as f:
            audio_base64 = base64.b64encode(f.read()).decode("utf-8")

        os.remove(chemin_mp3)
        return audio_base64

    except Exception as e:
        print(f"Erreur TTS: {e}")
        return ""


# ─────────────────────────────────────────────
# TRANSCRIPTION AUDIO — Groq Whisper (cloud) ou Whisper local
# ─────────────────────────────────────────────
async def transcrire_avec_groq(chemin_audio: str) -> str:
    """
    Transcrit un fichier audio via l'API Groq (whisper-large-v3) en asynchrone.
    Retourne le texte transcrit, ou lève une exception en cas d'échec.
    """
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}

    with open(chemin_audio, "rb") as f:
        audio_bytes = f.read()

    files = {"file": (os.path.basename(chemin_audio), audio_bytes, "audio/wav")}
    data = {
        "model": GROQ_MODEL,
        "language": "fr",
        "response_format": "json",
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            GROQ_AUDIO_URL,
            headers=headers,
            files=files,
            data=data
        )

    if response.status_code != 200:
        raise Exception(f"Groq {response.status_code}: {response.text}")

    result = response.json()
    return result.get("text", "").strip()


async def transcrire_audio(chemin_audio: str) -> str:
    """
    Transcrit un fichier audio de manière asynchrone.
    Utilise Groq Whisper si activé, avec repli automatique sur Whisper local
    en cas d'échec (réseau, quota, etc.).
    """
    if UTILISER_GROQ_WHISPER:
        try:
            texte = await transcrire_avec_groq(chemin_audio)
            print("☁️ Transcription via Groq Whisper")
            return texte
        except Exception as e:
            print(f"⚠️ Groq Whisper indisponible ({e}) → repli sur Whisper local")
            # Charger Whisper local à la volée si pas déjà chargé
            global whisper, whisper_model
            if whisper is None:
                import whisper
            if whisper_model is None:
                print("⏳ Chargement de Whisper local (repli)...")
                whisper_model = whisper.load_model(WHISPER_MODEL)
                print("✅ Whisper local prêt !")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: whisper_model.transcribe(chemin_audio, language="fr", fp16=False)
            )
            return result["text"].strip()
    else:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: whisper_model.transcribe(chemin_audio, language="fr", fp16=False)
        )
        return result["text"].strip()


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/dashboard")
async def dashboard():
    return RedirectResponse(url="http://localhost:5173", status_code=307)


@app.post("/chat/text")
async def chat_text(
    message: str = Form(...),
    session_id: str = Form(default=""),
    canal: str = Form(default="web")
):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Purger les sessions expirées à chaque appel
    purger_sessions_expirees()

    bot_response = await appeler_ia(session_id, message)
    hopital_info = traiter_fin_consultation(session_id, bot_response, canal)
    texte_propre = nettoyer_texte(bot_response)
    audio_base64 = generer_audio(texte_propre)

    return JSONResponse({
        "session_id": session_id,
        "response": texte_propre,
        "audio": audio_base64,
        "fin_consultation": "[FIN_CONSULTATION]" in bot_response,
        "hopital_info": hopital_info
    })


@app.post("/chat/audio")
async def chat_audio(
    audio: UploadFile = File(...),
    session_id: str = Form(default=""),
    canal: str = Form(default="web")
):
    if not session_id:
        session_id = str(uuid.uuid4())

    # Purger les sessions expirées à chaque appel
    purger_sessions_expirees()

    # Sauvegarder le fichier brut envoyé par le navigateur
    # Extension .webm : c'est le format produit par MediaRecorder du navigateur,
    # nécessaire pour que pydub/ffmpeg détectent correctement le format
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
        chemin_raw = f.name
        f.write(await audio.read())

    chemin_wav = chemin_raw.replace(".webm", ".wav")

    try:
        # Conversion pydub → WAV 16kHz mono propre pour Whisper
        # Le MediaRecorder du navigateur produit parfois un format non standard
        # Si le fichier est déjà un WAV valide (ex: envoyé par Telegram), on le garde tel quel
        try:
            from pydub import AudioSegment
            import wave
            # Vérifier si c'est déjà un WAV valide
            wav_valide = False
            try:
                with wave.open(chemin_raw, 'rb') as wf:
                    wav_valide = wf.getnframes() > 0
            except Exception:
                wav_valide = False

            if wav_valide:
                print("✅ Fichier WAV valide reçu, pas de reconversion nécessaire")
                chemin_wav = chemin_raw
            else:
                audio_seg = AudioSegment.from_file(chemin_raw)
                audio_seg = audio_seg.set_frame_rate(16000).set_channels(1)
                audio_seg.export(chemin_wav, format="wav")
                print("✅ Conversion audio réussie")
        except Exception as conv_err:
            print(f"⚠️ Conversion pydub échouée ({conv_err}), utilisation du fichier brut")
            chemin_wav = chemin_raw

        # Transcription via Groq Whisper (cloud, rapide) avec repli local si échec
        texte_transcrit = await transcrire_audio(chemin_wav)
        texte_transcrit = texte_transcrit.strip()

        if not texte_transcrit:
            return JSONResponse({"error": "Transcription vide. Parlez plus fort."}, status_code=400)

        print(f"🎤 Transcription : {texte_transcrit}")

        bot_response = await appeler_ia(session_id, texte_transcrit)
        hopital_info = traiter_fin_consultation(session_id, bot_response, canal)
        texte_propre = nettoyer_texte(bot_response)
        audio_base64 = generer_audio(texte_propre)

        return JSONResponse({
            "session_id": session_id,
            "transcription": texte_transcrit,
            "response": texte_propre,
            "audio": audio_base64,
            "fin_consultation": "[FIN_CONSULTATION]" in bot_response,
            "hopital_info": hopital_info
        })

    finally:
        for f in [chemin_raw, chemin_wav]:
            if f and f != chemin_raw and os.path.exists(f):
                os.remove(f)
        if os.path.exists(chemin_raw):
            os.remove(chemin_raw)


# ─────────────────────────────────────────────
# ROUTES AUTHENTIFICATION (DASHBOARD SOIGNANT)
# ─────────────────────────────────────────────

@app.post("/auth/login")
async def login(credentials: LoginRequest):
    if credentials.username == DASHBOARD_USERNAME and credentials.password == DASHBOARD_PASSWORD:
        token = generer_token(credentials.username)
        print(f"🔐 Connexion réussie au dashboard : {credentials.username}")
        return JSONResponse({
            "success": True,
            "token": token,
            "user": {
                "username": credentials.username,
                "role": "Personnel Médical",
                "nom": "Médecin Régulateur"
            }
        })
    print(f"⚠️ Échec de connexion dashboard : {credentials.username}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants incorrects. Veuillez vérifier le nom d'utilisateur et le mot de passe."
    )


@app.get("/auth/verify", dependencies=[Depends(verifier_authentification_soignant)])
async def verify_auth():
    return JSONResponse({"valid": True, "user": {"username": DASHBOARD_USERNAME, "role": "Personnel Médical"}})


# ─────────────────────────────────────────────
# ROUTES PROTÉGÉES (DONNÉES MÉDICALES)
# ─────────────────────────────────────────────

@app.get("/consultations", dependencies=[Depends(verifier_authentification_soignant)])
async def get_consultations():
    return JSONResponse({"consultations": database.get_consultations()})


@app.get("/alertes", dependencies=[Depends(verifier_authentification_soignant)])
async def get_alertes(non_traitees: bool = False):
    return JSONResponse({"alertes": database.get_alertes(non_traitees_seulement=non_traitees)})


@app.patch("/alertes/{alerte_id}/traiter", dependencies=[Depends(verifier_authentification_soignant)])
async def traiter_alerte(alerte_id: int, notes: str = ""):
    database.marquer_alerte_traitee(alerte_id, notes)
    return JSONResponse({"message": f"Alerte #{alerte_id} traitée."})


@app.get("/stats", dependencies=[Depends(verifier_authentification_soignant)])
async def get_stats():
    return JSONResponse(database.get_stats())


@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    session_manager.supprimer_session(session_id)
    return JSONResponse({"message": "Session réinitialisée."})


if __name__ == "__main__":
    database.init_db()
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)