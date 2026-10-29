"""
database.py
------------
E-Santé Bénin — Module base de données MySQL (WAMP)
Gestion des consultations, sessions et alertes
"""

import sys
import os

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pymysql
import json
from datetime import datetime
from contextlib import contextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─────────────────────────────────────────────
# CONFIGURATION MYSQL
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":        os.getenv("DB_HOST", "localhost"),
    "port":        int(os.getenv("DB_PORT", 3306)),
    "user":        os.getenv("DB_USER", "root"),
    "password":    os.getenv("DB_PASSWORD", ""),
    "database":        os.getenv("DB_NAME", "esante_benin"),
    "charset":         "utf8mb4",
    "cursorclass":     pymysql.cursors.DictCursor,
    "connect_timeout": 3
}


# ─────────────────────────────────────────────
# CONNEXION
# ─────────────────────────────────────────────
def get_conn():
    """Retourne une connexion MySQL."""
    return pymysql.connect(**DB_CONFIG)


@contextmanager
def connexion():
    """
    Context manager — ferme toujours la connexion,
    même en cas d'exception.
    Usage : with connexion() as conn: ...
    """
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def creer_indexes_si_absents():
    """Crée les index de performance MySQL s'ils n'existent pas encore."""
    indexes = [
        ("consultations", "idx_consultations_hopital_timestamp", "(`hopital`, `timestamp`)"),
        ("consultations", "idx_consultations_urgence_timestamp", "(`niveau_urgence`, `timestamp`)"),
        ("consultations", "idx_consultations_timestamp", "(`timestamp`)"),
        ("consultations", "idx_consultations_patient_id", "(`patient_id`)"),
        ("alertes", "idx_alertes_traitee_timestamp", "(`traitee`, `timestamp`)"),
        ("sessions", "idx_sessions_updated_at", "(`updated_at`)"),
    ]
    try:
        with connexion() as conn:
            with conn.cursor() as cur:
                for table, nom_idx, colonnes in indexes:
                    cur.execute("""
                        SELECT COUNT(1) AS count
                        FROM information_schema.statistics
                        WHERE table_schema = DATABASE()
                          AND table_name = %s
                          AND index_name = %s
                    """, (table, nom_idx))
                    res = cur.fetchone()
                    if not (res and res["count"] > 0):
                        cur.execute(f"CREATE INDEX {nom_idx} ON {table} {colonnes}")
                        print(f"⚡ Index créé : {table}.{nom_idx}")
    except Exception as e:
        print(f"⚠️ Vérification des index MySQL : {e}")


def init_db():
    """Vérifie la connexion à la base de données et optimise les index."""
    try:
        with connexion():
            pass
        creer_indexes_si_absents()
        print("✅ Connexion MySQL et index optimisés !")
    except Exception as e:
        print(f"❌ Erreur connexion MySQL : {e}")


# ─────────────────────────────────────────────
# SESSIONS
# ─────────────────────────────────────────────
def get_session(session_id: str) -> dict:
    """Récupère une session existante."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM sessions WHERE session_id = %s", (session_id,))
                result = cursor.fetchone()
        return result or {}
    except Exception as e:
        print(f"❌ Erreur get_session: {e}")
        return {}


def sauvegarder_session(
    session_id: str,
    patient_id: str,
    prenom: str,
    age: int,
    sexe: str,
    historique: list
) -> bool:
    """Crée ou met à jour une session."""
    try:
        historique_json = json.dumps(historique, ensure_ascii=False)
        existing = get_session(session_id)

        with connexion() as conn:
            with conn.cursor() as cursor:
                if existing:
                    cursor.execute("""
                        UPDATE sessions
                        SET patient_id=%s, prenom=%s, age=%s, sexe=%s,
                            historique=%s, updated_at=%s
                        WHERE session_id=%s
                    """, (patient_id, prenom, age, sexe,
                          historique_json, datetime.now(), session_id))
                else:
                    cursor.execute("""
                        INSERT INTO sessions
                        (session_id, patient_id, prenom, age, sexe, historique)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (session_id, patient_id, prenom, age, sexe, historique_json))
        return True
    except Exception as e:
        print(f"❌ Erreur sauvegarder_session: {e}")
        return False


def get_historique(session_id: str) -> list:
    """Récupère l'historique de conversation."""
    session = get_session(session_id)
    if session and session.get("historique"):
        try:
            return json.loads(session["historique"])
        except Exception:
            return []
    return []


# ─────────────────────────────────────────────
# CONSULTATIONS
# ─────────────────────────────────────────────
def sauvegarder_consultation(
    patient_id: str,
    prenom: str,
    age: int,
    sexe: str,
    symptomes: str,
    duree: str,
    localisation: str,
    niveau_urgence: str,
    hopital: str,
    conseils: str,
    conversation: str,
    canal: str = "web"
) -> int:
    """Sauvegarde une consultation complète."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO consultations
                    (patient_id, prenom, age, sexe, symptomes, duree, localisation,
                     niveau_urgence, hopital, conseils, conversation, canal, alerte_traitee)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (patient_id, prenom, age, sexe, symptomes, duree, localisation,
                      niveau_urgence, hopital, conseils, conversation, canal, False))
                consultation_id = cursor.lastrowid

        print(f"✅ Consultation #{consultation_id} sauvegardée — {prenom}, Urgence: {niveau_urgence}")

        # Créer alerte si Orange ou Rouge
        if niveau_urgence in ["orange", "rouge"]:
            creer_alerte(
                consultation_id=consultation_id,
                patient_id=patient_id,
                prenom=prenom,
                niveau_urgence=niveau_urgence,
                symptomes=symptomes,
                localisation=localisation,
                hopital=hopital
            )

        return consultation_id

    except Exception as e:
        print(f"❌ Erreur sauvegarder_consultation: {e}")
        return 0


def get_consultations(limit: int = 50) -> list:
    """Retourne les dernières consultations."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id, patient_id, prenom, age, sexe, timestamp,
                           symptomes, duree, localisation, niveau_urgence,
                           hopital, conseils, canal, alerte_traitee
                    FROM consultations
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (limit,))
                results = cursor.fetchall()

        # Convertir datetime en string
        for r in results:
            if r.get("timestamp"):
                r["timestamp"] = r["timestamp"].isoformat()
            r["alerte_traitee"] = bool(r["alerte_traitee"])

        return results
    except Exception as e:
        print(f"❌ Erreur get_consultations: {e}")
        return []


def get_consultation_by_id(consultation_id: int) -> dict:
    """Retourne une consultation par son ID."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM consultations WHERE id = %s", (consultation_id,))
                result = cursor.fetchone()
        if result and result.get("timestamp"):
            result["timestamp"] = result["timestamp"].isoformat()
        return result or {}
    except Exception as e:
        print(f"❌ Erreur get_consultation_by_id: {e}")
        return {}


def marquer_consultation_traitee(consultation_id: int):
    """Marque une consultation comme traitée."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE consultations SET alerte_traitee = TRUE WHERE id = %s",
                    (consultation_id,)
                )
        print(f"✅ Consultation #{consultation_id} marquée comme traitée.")
    except Exception as e:
        print(f"❌ Erreur marquer_consultation_traitee: {e}")


# ─────────────────────────────────────────────
# ALERTES
# ─────────────────────────────────────────────
def creer_alerte(
    consultation_id: int,
    patient_id: str,
    prenom: str,
    niveau_urgence: str,
    symptomes: str,
    localisation: str,
    hopital: str
) -> int:
    """Crée une alerte pour le dashboard médical."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO alertes
                    (consultation_id, patient_id, prenom, niveau_urgence,
                     symptomes, localisation, hopital, traitee)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (consultation_id, patient_id, prenom, niveau_urgence,
                      symptomes, localisation, hopital, False))
                alerte_id = cursor.lastrowid
        print(f"🚨 Alerte {niveau_urgence.upper()} créée pour {prenom} !")
        return alerte_id
    except Exception as e:
        print(f"❌ Erreur creer_alerte: {e}")
        return 0


def get_alertes(non_traitees_seulement: bool = False) -> list:
    """Retourne les alertes."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                if non_traitees_seulement:
                    cursor.execute("""
                        SELECT * FROM alertes
                        WHERE traitee = FALSE
                        ORDER BY timestamp DESC LIMIT 50
                    """)
                else:
                    cursor.execute("""
                        SELECT * FROM alertes
                        ORDER BY timestamp DESC LIMIT 50
                    """)
                results = cursor.fetchall()

        for r in results:
            if r.get("timestamp"):
                r["timestamp"] = r["timestamp"].isoformat()
            r["traitee"] = bool(r["traitee"])

        return results
    except Exception as e:
        print(f"❌ Erreur get_alertes: {e}")
        return []


def marquer_alerte_traitee(alerte_id: int, notes: str = ""):
    """Marque une alerte comme traitée."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    UPDATE alertes
                    SET traitee = TRUE, notes_medecin = %s
                    WHERE id = %s
                """, (notes, alerte_id))
        print(f"✅ Alerte #{alerte_id} traitée.")
    except Exception as e:
        print(f"❌ Erreur marquer_alerte_traitee: {e}")


# ─────────────────────────────────────────────
# RÉPARTITION INTELLIGENTE
# ─────────────────────────────────────────────
def compter_orientations_recentes(nom_hopital: str, heures: int = 2) -> int:
    """Compte le nombre de patients orientés vers un hôpital dans les X dernières heures."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) as total FROM consultations
                    WHERE hopital = %s
                    AND timestamp >= NOW() - INTERVAL %s HOUR
                """, (nom_hopital, heures))
                result = cursor.fetchone()
        return result["total"] if result else 0
    except Exception as e:
        print(f"❌ Erreur compter_orientations_recentes: {e}")
        return 0


# ─────────────────────────────────────────────
# STATISTIQUES
# ─────────────────────────────────────────────
def get_stats() -> dict:
    """Retourne les statistiques globales."""
    try:
        with connexion() as conn:
            with conn.cursor() as cursor:

                # Total
                cursor.execute("SELECT COUNT(*) as total FROM consultations")
                total = cursor.fetchone()["total"]

                # Aujourd'hui
                cursor.execute("""
                    SELECT COUNT(*) as total FROM consultations
                    WHERE DATE(timestamp) = CURDATE()
                """)
                aujourd_hui = cursor.fetchone()["total"]

                # Par urgence
                cursor.execute("""
                    SELECT niveau_urgence, COUNT(*) as count
                    FROM consultations GROUP BY niveau_urgence
                """)
                urgences = {r["niveau_urgence"]: r["count"] for r in cursor.fetchall()}

                # Alertes non traitées
                cursor.execute("SELECT COUNT(*) as total FROM alertes WHERE traitee = FALSE")
                alertes_non_traitees = cursor.fetchone()["total"]

                # Par ville
                cursor.execute("""
                    SELECT localisation as ville, COUNT(*) as count
                    FROM consultations
                    WHERE localisation != ''
                    GROUP BY localisation
                    ORDER BY count DESC LIMIT 5
                """)
                par_ville = cursor.fetchall()

        return {
            "total": total,
            "aujourd_hui": aujourd_hui,
            "vert":   urgences.get("vert", 0),
            "orange": urgences.get("orange", 0),
            "rouge":  urgences.get("rouge", 0),
            "alertes_non_traitees": alertes_non_traitees,
            "par_ville": par_ville
        }

    except Exception as e:
        print(f"❌ Erreur get_stats: {e}")
        return {
            "total": 0, "aujourd_hui": 0,
            "vert": 0, "orange": 0, "rouge": 0,
            "alertes_non_traitees": 0, "par_ville": []
        }