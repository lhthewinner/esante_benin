import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from session_manager import GestionnaireSessions

class TestGestionnaireSessions(unittest.TestCase):

    def setUp(self):
        self.sm = GestionnaireSessions()
        self.session_id = "test-session-uuid-999"
        self.sm.supprimer_session(self.session_id)

    def tearDown(self):
        self.sm.supprimer_session(self.session_id)

    def test_stockage_et_recuperation_session(self):
        """Vérifie l'enregistrement et la lecture d'un historique de conversation."""
        historique = [
            {"role": "user", "parts": [{"text": "Bonjour, j'ai mal à la tête"}]},
            {"role": "model", "parts": [{"text": "Bonjour, depuis combien de temps ?"}]}
        ]
        self.sm.set_historique(self.session_id, historique)
        resultat = self.sm.get_historique(self.session_id)
        self.assertEqual(resultat, historique)

    def test_suppression_session(self):
        """Vérifie que la suppression d'une session vide son historique."""
        self.sm.set_historique(self.session_id, [{"role": "user", "parts": [{"text": "Test"}]}])
        self.sm.supprimer_session(self.session_id)
        self.assertEqual(self.sm.get_historique(self.session_id), [])

    def test_session_inexistante_retourne_vide(self):
        """Vérifie qu'un identifiant inconnu renvoie une liste vide sans erreur."""
        self.assertEqual(self.sm.get_historique("id-totalement-inconnu-000"), [])

    def test_fallback_transparent(self):
        """Vérifie que le statut de Redis est déterminé sans lever d'exception."""
        self.assertIn(self.sm.est_redis_actif, [True, False])


if __name__ == "__main__":
    unittest.main()
