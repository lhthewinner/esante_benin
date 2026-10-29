"""
session_manager.py
------------------
E-Santé Bénin — Gestionnaire Hybride de Sessions (Redis + Fallback Mémoire + MySQL)
Assure la persistance des conversations patients avec expiration automatique (TTL).
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Assurer l'encodage UTF-8 sous Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import database

# Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_EXPIRATION_MINUTES = int(os.getenv("SESSION_EXPIRATION_MINUTES", "120"))
TTL_SECONDS = SESSION_EXPIRATION_MINUTES * 60

class GestionnaireSessions:
    """
    Gestionnaire hybride de sessions :
    1. Tente d'utiliser Redis pour le stockage distribué haute performance avec TTL natif.
    2. Si Redis n'est pas disponible (ex: environnement local Windows sans conteneur),
       bascule de façon transparente sur un cache en mémoire avec persistance MySQL automatique.
    """

    def __init__(self):
        self._redis = None
        self._redis_actif = False
        self._memoire_locale = {}
        self._initialiser_connexion()

    def _initialiser_connexion(self):
        try:
            import redis
            client = redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=1.5)
            client.ping()
            self._redis = client
            self._redis_actif = True
            print(f"🚀 [Sessions] Connecté avec succès au serveur Redis : {REDIS_URL} (TTL: {SESSION_EXPIRATION_MINUTES} min)")
        except Exception as e:
            self._redis = None
            self._redis_actif = False
            print(f"ℹ️ [Sessions] Redis non joignable ({e}) — Utilisation du gestionnaire hybride (Mémoire vive + Restauration MySQL).")

    @property
    def est_redis_actif(self) -> bool:
        """Indique si Redis est actuellement connecté et opérationnel."""
        return self._redis_actif

    def get_historique(self, session_id: str) -> list:
        """
        Récupère l'historique d'une session.
        Si la session n'est pas en RAM/Redis (ex: après un redémarrage serveur),
        tente de la restaurer directement depuis la table MySQL `sessions`.
        """
        if not session_id:
            return []

        # 1. Tentative via Redis
        if self._redis_actif and self._redis:
            try:
                cle = f"esante:session:{session_id}"
                data = self._redis.get(cle)
                if data:
                    # Renouveler le TTL à chaque accès actif
                    self._redis.expire(cle, TTL_SECONDS)
                    return json.loads(data)
            except Exception as e:
                print(f"⚠️ Erreur lecture Redis: {e} -> bascule vers le cache mémoire")

        # 2. Tentative via Cache Mémoire
        self.purger_expirees()
        if session_id in self._memoire_locale:
            self._memoire_locale[session_id]["last_access"] = datetime.now()
            return self._memoire_locale[session_id]["historique"]

        # 3. Restauration depuis MySQL (si le serveur a été redémarré en cours de conversation)
        try:
            historique_bdd = database.get_historique(session_id)
            if historique_bdd:
                print(f"🔄 Session {session_id[:8]} restaurée depuis MySQL !")
                self.set_historique(session_id, historique_bdd)
                return historique_bdd
        except Exception as e:
            print(f"⚠️ Erreur restauration session MySQL: {e}")

        return []

    def set_historique(self, session_id: str, historique: list):
        """Enregistre ou met à jour l'historique d'une session avec son TTL."""
        if not session_id:
            return

        # 1. Sauvegarde Redis si disponible
        if self._redis_actif and self._redis:
            try:
                cle = f"esante:session:{session_id}"
                json_data = json.dumps(historique, ensure_ascii=False)
                self._redis.setex(cle, TTL_SECONDS, json_data)
            except Exception as e:
                print(f"⚠️ Erreur écriture Redis: {e}")

        # 2. Toujours maintenir dans le cache local
        self._memoire_locale[session_id] = {
            "historique": historique,
            "last_access": datetime.now()
        }

    def supprimer_session(self, session_id: str):
        """Supprime une session (déconnexion ou réinitialisation)."""
        if not session_id:
            return

        if self._redis_actif and self._redis:
            try:
                self._redis.delete(f"esante:session:{session_id}")
            except Exception:
                pass

        if session_id in self._memoire_locale:
            del self._memoire_locale[session_id]

    def purger_expirees(self):
        """Nettoie les sessions expirées dans le cache mémoire local."""
        maintenant = datetime.now()
        delai_expiration = timedelta(minutes=SESSION_EXPIRATION_MINUTES)
        expirees = [
            sid for sid, item in self._memoire_locale.items()
            if maintenant - item["last_access"] > delai_expiration
        ]
        for sid in expirees:
            del self._memoire_locale[sid]


# Instance globale partagée
session_manager = GestionnaireSessions()
