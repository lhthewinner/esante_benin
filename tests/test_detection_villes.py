import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch
from main import normaliser_texte, detecter_hopital, HOPITAUX_ABOMEY_CALAVI, HOPITAUX_GODOMEY, HOPITAUX_AUTRES

@patch("database.compter_orientations_recentes", return_value=0)
class TestDetectionVilles(unittest.TestCase):

    def test_normalisation_accents_et_casse(self, mock_db):
        """Vérifie la suppression des accents et la mise en minuscules."""
        self.assertEqual(normaliser_texte("Godomé"), "godome")
        self.assertEqual(normaliser_texte("ÀBOMEY-CALAVI"), "abomey-calavi")
        self.assertEqual(normaliser_texte("Bêthésda"), "bethesda")

    def test_detection_abomey_calavi_variantes(self, mock_db):
        """Vérifie la reconnaissance d'Abomey-Calavi et de ses quartiers/variantes."""
        variantes = [
            ("J'habite à Abomey-Calavi", "Abomey-Calavi"),
            ("Je vis à Calavi Kpota", "Abomey-Calavi"),
            ("Mon quartier est Akassato", "Abomey-Calavi"),
            ("Bomekalavit", "Abomey-Calavi"),  # Transcription phonétique courante
            ("Je suis à Zinvié", "Abomey-Calavi"),
        ]
        ids_calavi = {h["id"] for h in HOPITAUX_ABOMEY_CALAVI}
        for texte, _ in variantes:
            hopital = detecter_hopital(texte, "")
            self.assertIsNotNone(hopital, f"Échec de détection pour: {texte}")
            self.assertIn(hopital["id"], ids_calavi, f"L'hôpital retourné n'appartient pas à Calavi: {hopital}")

    def test_detection_godomey_variantes(self, mock_db):
        """Vérifie la reconnaissance de Godomey et de ses variantes orales."""
        variantes = [
            ("Je suis à Godomey", "Godomey"),
            ("J'habite à Godomé", "Godomey"),  # Variante sans y et accent
            ("Je vis à Godomet", "Godomey"),
            ("Je réside à Togba", "Godomey"),
            ("Vers Maria-Gléta", "Godomey"),
            ("Quartier des Cocotiers", "Godomey"),
        ]
        ids_godomey = {h["id"] for h in HOPITAUX_GODOMEY}
        for texte, _ in variantes:
            hopital = detecter_hopital(texte, "")
            self.assertIsNotNone(hopital, f"Échec de détection pour: {texte}")
            self.assertIn(hopital["id"], ids_godomey, f"L'hôpital retourné n'appartient pas à Godomey: {hopital}")

    def test_detection_autres_villes(self, mock_db):
        """Vérifie la détection des autres grandes villes béninoises."""
        self.assertEqual(detecter_hopital("CNHU Cotonou")["nom"], HOPITAUX_AUTRES["CNHU"]["nom"])
        self.assertEqual(detecter_hopital("Porto-Novo")["nom"], HOPITAUX_AUTRES["Porto-Novo"]["nom"])
        self.assertEqual(detecter_hopital("Parakou")["nom"], HOPITAUX_AUTRES["Parakou"]["nom"])
        self.assertEqual(detecter_hopital("Bohicon")["nom"], HOPITAUX_AUTRES["Bohicon"]["nom"])

    def test_ville_inconnue(self, mock_db):
        """Vérifie qu'un texte sans ville reconnue renvoie None proprement."""
        self.assertIsNone(detecter_hopital("Je n'ai pas précisé mon adresse", ""))


if __name__ == "__main__":
    unittest.main()
