import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from main import generer_token, valider_token, DASHBOARD_USERNAME

class TestAuthSecurite(unittest.TestCase):

    def test_token_valide(self):
        """Vérifie qu'un jeton correctement généré est validé avec succès."""
        token = generer_token(DASHBOARD_USERNAME)
        self.assertTrue(valider_token(token))

    def test_token_altere_rejete(self):
        """Vérifie qu'un jeton dont la signature ou le contenu est altéré est rejeté."""
        token = generer_token(DASHBOARD_USERNAME)
        token_falsifie = token[:-4] + "ABCD"
        self.assertFalse(valider_token(token_falsifie))

    def test_token_mauvais_utilisateur(self):
        """Vérifie qu'un token émis pour un autre utilisateur est rejeté."""
        token_imposteur = generer_token("hacker_user")
        self.assertFalse(valider_token(token_imposteur))

    def test_token_chaine_corrompue(self):
        """Vérifie la résistance aux chaînes de caractères invalides."""
        self.assertFalse(valider_token(""))
        self.assertFalse(valider_token("invalid_base64_string!"))
        self.assertFalse(valider_token("abc:def"))


if __name__ == "__main__":
    unittest.main()
