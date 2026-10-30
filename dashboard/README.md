# 🖥️ E-Santé Bénin — Dashboard Soignant (Application React)

Application web de supervision médicale et de régulation hospitalière en temps réel pour le personnel soignant des communes d'Abomey-Calavi et de Godomey.

**Responsable Conception & Développement Frontend :** Grâce ADJAFON ([@Grace](https://github.com/graceadjafon) - `graceadjafon@gmail.com`)  
**Stack :** React 19, Vite, Tailwind CSS v4, Lucide Icons, Fetch API

---

## 🎯 Fonctionnalités Développées

1. **Tableau de Bord Clinique & Indicateurs Clés :**
   - Volume total des consultations en temps réel.
   - Compteur d'alertes prioritaires nécessitant une intervention soignante.
   - Métriques de charge et d'orientation des hôpitaux partenaires (CHIC Calavi, CHUZ-AS, Clinique Mahoulé, Saint Jean Maria-Gléta, etc.).

2. **File Active des Alertes d'Urgence :**
   - Visualisation immédiate des cas 🔴 **Rouge** (urgence vitale) et 🟠 **Orange** (consultation 2-4h).
   - Accès aux symptômes déclarés par le patient et à l'hôpital de destination.
   - Bouton d'acquittement en 1 clic avec confirmation et saisie des notes médicales.

3. **Historique des Consultations Patients :**
   - Filtrage dynamique par niveau d'urgence, canal (Web / Telegram) et établissement.
   - Vue détaillée du dialogue complet patient-IA, des remèdes naturels recommandés et des données géographiques.

4. **Identité Visuelle & Ergonomie Médicale :**
   - Intégration du logo officiel E-Santé Bénin (`esblogo.jpeg`).
   - Thème sombre médical moderne (Dark Mode) facilitant la lisibilité en salle de régulation.
   - Composants réactifs et animations fluides (Tailwind CSS).

---

## 🏗️ Structure des Composants

```text
dashboard/src/
├── assets/                  # Assets visuels, hero images, SVG
├── components/
│   ├── Alertes.jsx          # File active des alertes d'urgence et acquittement
│   ├── Consultations.jsx    # Table filtrable et tiroir de consultation détaillée
│   ├── Stats.jsx            # Indicateurs consolidés et fréquentation hospitalière
│   └── Login.jsx            # Écran de connexion soignant (Module Sécurité)
├── App.jsx                  # Navigation par onglets, layout et gestion d'état globale
├── main.jsx                 # Point d'entrée React 19
└── index.css                # Configuration Tailwind CSS v4
```

---

## 🚀 Démarrage Rapide

```bash
# Installation des dépendances
npm install

# Lancement du serveur de développement Vite
npm run dev
```

Accès à l'application : **`http://localhost:5173`**  
API Backend requise : **`http://localhost:8000`**
