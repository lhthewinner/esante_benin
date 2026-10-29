import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch
from main import choisir_hopital_moins_charge, HOPITAUX_ABOMEY_CALAVI

class TestRepartitionHopitaux(unittest.TestCase):

    @patch("database.compter_orientations_recentes")
    def test_selection_hopital_moins_charge(self, mock_compter):
        """Vérifie que l'hôpital ayant le moins d'orientations récentes est systématiquement sélectionné."""
        # Simulation : le Centre de Santé Calavi Kpota (CS_KPOTA) a reçu 0 patient, les autres plus
        def fausse_charge(nom_hopital, heures=2):
            if "Kpota" in nom_hopital:
                return 0
            elif "CHIC" in nom_hopital:
                return 5
            elif "Zone" in nom_hopital:
                return 3
            return 2

        mock_compter.side_effect = fausse_charge

        hopital_choisi = choisir_hopital_moins_charge(HOPITAUX_ABOMEY_CALAVI)
        self.assertEqual(hopital_choisi["id"], "CS_KPOTA")

    @patch("database.compter_orientations_recentes")
    def test_repli_en_cas_d_erreur_bdd(self, mock_compter):
        """Vérifie qu'en cas d'erreur BDD, le système ne plante pas et retourne le premier hôpital."""
        mock_compter.side_effect = Exception("Erreur de connexion MySQL temporaire")

        hopital_choisi = choisir_hopital_moins_charge(HOPITAUX_ABOMEY_CALAVI)
        self.assertEqual(hopital_choisi, HOPITAUX_ABOMEY_CALAVI[0])


if __name__ == "__main__":
    unittest.main()
