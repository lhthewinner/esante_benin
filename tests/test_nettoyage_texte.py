import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from main import nettoyer_texte

class TestNettoyageTexte(unittest.TestCase):

    def test_suppression_markdown(self):
        """Vérifie que les balises markdown sont nettoyées pour la synthèse vocale."""
        texte_avec_markdown = "**Bonjour**, vous avez une *fièvre* et `#des maux` de tête. `Prenez du repos`."
        propre = nettoyer_texte(texte_avec_markdown)
        self.assertNotIn("**", propre)
        self.assertNotIn("`", propre)
        self.assertNotIn("#", propre)
        self.assertIn("Bonjour", propre)
        self.assertIn("fièvre", propre)

    def test_tronquage_fin_consultation(self):
        """Vérifie que le JSON et la balise [FIN_CONSULTATION] sont coupés pour ne pas être lus par la voix."""
        texte_complet = (
            "Prenez soin de vous.\n"
            "[FIN_CONSULTATION]\n"
            '{"prenom": "Jean", "age": 30, "niveau_urgence": "vert"}'
        )
        propre = nettoyer_texte(texte_complet)
        self.assertEqual(propre, "Prenez soin de vous.")
        self.assertNotIn("[FIN_CONSULTATION]", propre)
        self.assertNotIn('{"prenom"', propre)


if __name__ == "__main__":
    unittest.main()
