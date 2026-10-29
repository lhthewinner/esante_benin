import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
import database

class TestBaseDeDonneesReelle(unittest.TestCase):

    def test_connexion_mysql_active(self):
        """Vérifie la connexion effective au serveur MySQL WAMP."""
        with database.connexion() as conn:
            self.assertIsNotNone(conn)
            with conn.cursor() as cursor:
                cursor.execute("SELECT DATABASE() as db, VERSION() as version")
                res = cursor.fetchone()
                self.assertIsNotNone(res)
                self.assertEqual(res["db"], "esante_benin")

    def test_tables_essentielles_presentes(self):
        """Vérifie la présence des tables consultations, sessions et alertes."""
        with database.connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES")
                tables = [list(r.values())[0] for r in cursor.fetchall()]
                self.assertIn("consultations", tables)
                self.assertIn("sessions", tables)
                self.assertIn("alertes", tables)

    def test_lecture_statistiques_reelles(self):
        """Vérifie l'agrégation des statistiques globales."""
        stats = database.get_stats()
        self.assertIn("total", stats)
        self.assertIn("alertes_non_traitees", stats)
        self.assertGreaterEqual(stats["total"], 0)

    def test_lecture_consultations_reelles(self):
        """Vérifie la récupération de l'historique des consultations."""
        consultations = database.get_consultations(limit=5)
        self.assertIsInstance(consultations, list)

    def test_lecture_alertes_reelles(self):
        """Vérifie la récupération de la liste des alertes."""
        alertes = database.get_alertes(non_traitees_seulement=True)
        self.assertIsInstance(alertes, list)

    def test_indexes_optimisation_presents(self):
        """Vérifie la présence effective des index de performance sur les tables."""
        database.creer_indexes_si_absents()
        with database.connexion() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name, index_name
                    FROM information_schema.statistics
                    WHERE table_schema = DATABASE()
                """)
                indices = [
                    (
                        r.get("table_name") or r.get("TABLE_NAME"),
                        r.get("index_name") or r.get("INDEX_NAME")
                    )
                    for r in cursor.fetchall()
                ]
                self.assertIn(("consultations", "idx_consultations_hopital_timestamp"), indices)
                self.assertIn(("consultations", "idx_consultations_urgence_timestamp"), indices)
                self.assertIn(("consultations", "idx_consultations_timestamp"), indices)
                self.assertIn(("alertes", "idx_alertes_traitee_timestamp"), indices)


if __name__ == "__main__":
    unittest.main()
