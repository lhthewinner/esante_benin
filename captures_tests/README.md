# 📁 Dossier des Preuves et Captures de Tests — E-Santé Bénin

Ce dossier regroupe les **preuves de validation technique, de tests end-to-end et d'intégration** du système E-Santé Bénin connectées à la base de données réelle MySQL active sur WAMP.

---

## 📸 Liste des Captures Haute Résolution Disponibles

1. **[01_execution_tests_unitaires_complets.png](01_execution_tests_unitaires_complets.png)**
   - *Description* : Capture de l'exécution complète des 18 tests unitaires avec 100% de réussite.
   - *Composants testés* : Détection phonétique, protocoles de conversation, token de sécurité, calcul de charge hospitalière.

2. **[02_verification_bdd_mysql_active.png](02_verification_bdd_mysql_active.png)**
   - *Description* : Vérification en direct de la connexion MySQL sur WAMP (port 3306).
   - *Données vérifiées* : Intégrité des tables `consultations`, `sessions`, `alertes` et répartition géographique.

3. **[03_test_algorithme_repartition_flux.png](03_test_algorithme_repartition_flux.png)**
   - *Description* : Validation de l'algorithme de régulation hospitalière et génération automatique des liens Google Maps.
   - *Zones testées* : 4 hôpitaux d'Abomey-Calavi et 4 cliniques/hôpitaux de Godomey.

4. **[04_test_securite_hmac_authentification.png](04_test_securite_hmac_authentification.png)**
   - *Description* : Audit de sécurité prouvant le bon fonctionnement de l'authentification HMAC-SHA256 pour les médecins régulateurs et le rejet des tentatives d'usurpation.

5. **[05_discussion_complete_bot.png](05_discussion_complete_bot.png)**
   - *Description* : Consultation médicale réelle de bout en bout avec l'agent d'IA médicale.
   - *Éléments validés* :
     - Échange structuré en 11 messages avec le patient Koffi (28 ans, Godomey vers Togba).
     - Explication pédagogique des causes probables (syndrome grippal, paludisme, infection bactérienne).
     - Conseils de soulagement 100% naturels sans aucun médicament chimique (tisane gingembre/citron/miel avec précaution d'usage, hydratation, repos, compresse tiède).
     - Classification stricte en **Urgence ROUGE** (fièvre persistante > 48h, frissons violents).
     - Attribution automatique de l'hôpital le moins chargé (**Clinique Mahoulé de Godomey**) et lien Google Maps.

6. **[06_dashboard_medical_apres_consultation.png](06_dashboard_medical_apres_consultation.png)**
   - *Description* : Tableau de bord de régulation médicale après la consultation.
   - *Éléments validés* :
     - Consultation #21 immédiatement répertoriée dans le tableau des consultations récentes.
     - Déclenchement automatique d'une **Alerte ROUGE** prioritaire pour le patient Koffi avec bouton de prise en charge soignant.
     - Compteurs mis à jour en temps réel (Total consultations, Urgences Rouges, Alertes actives).

---

## 📊 Rapport de Test Interactif
- **[rapport_tests_officiel.html](rapport_tests_officiel.html)** : Rapport interactif complet généré par `pytest-html` (ouvrable dans n'importe quel navigateur Web).

---
*Date de mise à jour : 29/10/2026*
