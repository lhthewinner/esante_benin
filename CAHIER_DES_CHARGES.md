# 📘 Cahier des Charges & Spécifications Techniques — E-Santé Bénin

**Projet :** E-Santé Bénin — Assistant Médical Vocal & Régulation Hospitalière Intelligente  
**Auteurs :**  
- **Lucien HAIKOU** (@Lucien) — Chef de Projet & Développeur Fullstack Lead (Backend / IA)  
- **Grâce ADJAFON** (@Grace) — Co-développeuse & Responsable Interface Utilisateur (UI/UX) & Design  
**Périmètre pilote :** Communes d'Abomey-Calavi et de Godomey (Département de l'Atlantique, République du Bénin)  
**Statut du document :** Version Finale Validée Post-Soutenance  
**Dernière mise à jour :** 30 octobre 2026  

---

## 1. Contexte & Objectifs du Projet

### 1.1. Problématique Sanitaire
Au Bénin, et particulièrement dans la conurbation dense d'Abomey-Calavi et de Godomey, les services d'urgence et centres de santé subissent de fortes tensions :
- Engorgement régulier des salles d'attente par des cas bénins ne relevant pas de l'urgence hospitalière immédiate.
- Retard de prise en charge pour les urgences vitales par manque d'orientation préalable.
- Difficulté d'accès à une information médicale fiable pour les populations éloignées ou ayant des difficultés avec l'écrit.
- Répartition inégale des flux de patients entre les centres hospitaliers voisins (certaines structures saturées pendant que d'autres disposent de capacités d'accueil).

### 1.2. Solution Apportée par E-Santé Bénin
**E-Santé Bénin** est une plateforme de télérégulation sanitaire intégrant l'Intelligence Artificielle générative et la reconnaissance vocale :
1. **Écoute et Triage Vocal :** Permet à un patient d'exprimer librement et oralement ses symptômes en langage naturel (français).
2. **Démarche Médicale Pédagogique :** Explique les causes probables des maux sans jamais poser de diagnostic définitif.
3. **Conseils Naturels Sans Médicament Chimique :** Dispense uniquement des conseils hygiéno-diététiques et remèdes naturels locaux avec alertes d'interactions médicamenteuses.
4. **Orientation Géolocalisée Équilibrée :** Calcule en temps réel la charge des établissements de santé et oriente le patient vers l'hôpital le moins sollicité de sa zone géographique, avec itinéraire GPS Google Maps et contact téléphonique direct.
5. **Supervision Médicale Temps Réel :** Un tableau de bord réservé aux soignants permet de suivre les flux sanitaires et de traiter en priorité les alertes graves.

### 1.3. Équipe de Réalisation & Répartition des Rôles

Le projet est le fruit d'une collaboration technique complémentaire :

- **Lucien HAIKOU — Chef de Projet & Développeur Fullstack Lead (Backend / IA)**
  - **Pilotage & Architecture :** Conception générale de la solution, rédaction des spécifications et coordination technique.
  - **Moteur IA & Triage Vocal :** Pipeline vocal asynchrone (Groq Whisper, LLM Llama, synthèse gTTS) et protocole médical conversationnel.
  - **Régulation Hospitalière :** Modélisation de l'algorithme d'orientation et intégration de la cartographie sanitaire (Calavi & Godomey).
  - **Données & Infrastructure :** Conception de la base relationnelle MySQL (index de performance) et gestionnaire de session hybride Redis.
  - **Sécurité :** Authentification soignant de bout en bout (signature HMAC-SHA256 côté API et interface de connexion sécurisée).
  - **Qualité logicielle :** Suite complète des 23 tests automatisés et canal Telegram.

- **Grâce ADJAFON — Co-développeuse & Responsable Interface Utilisateur (UI/UX) & Design**
  - **Direction Artistique & Branding :** Création des logos officiels du projet (`esblogo.jpeg`) et de la charte visuelle (déclinée sur le Web, le Dashboard et le Bot).
  - **Développement Frontend :** Conception et intégration de l'application React moderne (React 19, Vite, Tailwind CSS).
  - **Supervision Médicale :** Mise en page des indicateurs cliniques, du tableau des flux de consultations et du module de gestion des alertes d'urgence.
  - **Expérience Utilisateur :** Ergonomie générale, accessibilité et évolutions futures des interfaces web.

---

## 2. Architecture Générale du Système

Le système est découpé en **cinq couches interdépendantes et modulaires** :

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          CANAUX D'ACCÈS PATIENTS                       │
│    Interface Web Vocale (index.html)   │    Bot Telegram (@esante_bot) │
└───────────────────┬────────────────────┴───────────────────┬──────────┘
                    │ Multipart / JSON                       │ Audio OGG / Polling
                    ▼                                        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   COUCHE 1 : BACKEND API (FastAPI)                     │
│  - Endpoint /chat/audio (Transcription ASR Groq Whisper)               │
│  - Moteur d'inférence LLM (Llama 3.3 / Qwen) avec System Prompt        │
│  - Synthèse vocale gTTS (Audio MP3 base64)                             │
│  - Algorithme de régulation hospitalière dynamique                    │
│  - Contrôle d'accès soignant par signature HMAC-SHA256                │
└──────────────┬───────────────────────────────┬─────────────────────────┘
               │ Lecture / Écriture             │ Gestion des sessions (TTL 2h)
               ▼                               ▼
┌───────────────────────────────┐   ┌────────────────────────────────────┐
│ COUCHE 2 : BASE DE DONNÉES    │   │ COUCHE 3 : GESTION DES SESSIONS    │
│ MySQL (WAMP / Port 3306)      │   │ - Moteur Redis (distribué)         │
│ - 6 Index de performance      │   │ - Fallback transparent mémoire vive│
│ - Tables : consultations,     │   │ - Restauration automatique MySQL   │
│   sessions, alertes           │   └────────────────────────────────────┘
└──────────────┬────────────────┘
               │ Données temps réel & alertes
               ▼
┌────────────────────────────────────────────────────────────────────────┐
│               COUCHE 4 : DASHBOARD DE SUPERVISION SOIGNANT             │
│  Application React 19 + Tailwind CSS + Vite (Port 5173)                │
│  - Authentification sécurisée des médecins régulateurs                 │
│  - Suivi des consultations récentes et statistiques sanitaires         │
│  - Prise en charge en 1 clic des alertes d'urgence rouge & orange      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Stack Technique & Technologies Retenues

| Composant | Technologie | Version / Détail | Rôle |
| :--- | :--- | :--- | :--- |
| **Langage Backend** | Python | 3.10+ | Moteur d'exécution principal |
| **Framework Web API** | FastAPI | 0.115+ (ASGI Uvicorn) | API REST asynchrone haute performance |
| **ASR (Voix vers Texte)** | Groq Whisper Cloud | `whisper-large-v3` | Transcription audio quasi-instantanée (< 1s) |
| **ASR Fallback** | OpenAI Whisper Local | Modèle `small` | Secours hors-ligne si panne réseau |
| **Moteur LLM Médical** | Groq API / Llama / Qwen | Modèles haute précision | Raisonnement clinique et dialogue empathique |
| **LLM Fallback** | Google Gemini API | `gemini-flash` | Relais transparent en cas de dépassement de quota |
| **Synthèse Vocale (TTS)**| gTTS / Google TTS | MP3 français | Restitution vocale pour les patients |
| **Conversion Audio** | pydub + FFmpeg | WebM / OGG $\rightarrow$ WAV mono | Standardisation des flux micro et Telegram |
| **Base de Données** | MySQL (WAMP / Cloud) | 8.0+, charset `utf8mb4` | Stockage relationnel et traçabilité médicale |
| **Gestion des Sessions** | Redis + Cache Local | Redis 5.0+ / Python Memory | Gestion des TTL (120 min) et reprise sur panne |
| **Frontend Patient** | HTML5 / CSS3 / Vanilla JS | `templates/index.html` | Interface vocale légère compatible tout navigateur |
| **Dashboard Soignant** | React + Tailwind CSS | React 19, Vite 8 | Interface médicale interactive temps réel |
| **Bot Messagerie** | python-telegram-bot | 21+ (mode asynchrone httpx)| Canal mobile accessible sans installation tierce |
| **Tests Automatisés** | pytest + pytest-html | 23 tests automatisés | Assurance qualité et non-régression |

---

## 4. Protocole Médical Conversationnel (System Prompt)

L'interaction avec le patient est encadrée par un prompt système rigoureux interdisant toute dérive diagnostique ou médicamenteuse :

### 4.1. Les 6 Étapes Structurées
- **Étape 0 — Accueil & Identification :** Salutation unique au premier contact, collecte bienveillante du prénom, de l'âge et du sexe.
- **Étape 1 — Symptômes Principaux :** Écoute attentive des maux décrits par le patient et questions d'approfondissement.
- **Étape 1.5 — Douleurs Associées :** Recherche méthodique de signes annexes (nausées, vertiges, courbatures, perte d'appétit).
- **Étape 2 — Durée d'Évolution :** Précision du temps d'apparition (heures, jours, semaines), déterminant critique de la gravité.
- **Étape 2.5 — Analyse des Causes Probables :** Explication pédagogique de 2 à 3 hypothèses médicales fréquentes dans la sous-région (ex : syndrome grippal, paludisme d'endémie, gastro-entérite) avec avertissement clair qu'il ne s'agit pas d'un diagnostic certifié.
- **Étape 3 — Conseils Naturels & Précautions :** Conseils d'hygiène, d'hydratation, d'alimentation légère et tisanes traditionnelles locales (citron, gingembre, miel, neem). **Interdiction formelle de prescrire le moindre médicament chimique** (même paracétamol). Avertissement systématique sur les interactions avec les traitements médicaux en cours.
- **Étape 4 — Triage & Orientation Géolocalisée :** Évaluation stricte de l'urgence selon les signes de gravité, recueil de la localisation et affectation de l'hôpital le moins chargé.
- **Étape 5 — Clôture & Transmission :** Message de bienveillance, balise technique `[FIN_CONSULTATION]` et payload JSON pour la base de données.

### 4.2. Règles d'Urgence Tricolore
- **🔴 ROUGE (Urgence Absolue — Prise en charge immédiate) :**  
  *Critères :* Détresse respiratoire, douleur thoracique oppressante, fièvre $> 39^\circ\text{C}$ persistante avec frissons violents, convulsions, confusion mentale, coma, saignements inexpliqués.
- **🟠 ORANGE (Consultation sous 2 à 4 heures) :**  
  *Critères :* Fièvre modérée évoluant depuis plus de 48 heures, vomissements répétés avec début de déshydratation, douleurs abdominales aiguës, toute situation chez le nourrisson ou la personne âgée sans détresse vitale.
- **🟢 VERT (Non Urgent — Surveillance 24 à 48 heures) :**  
  *Critères :* Symptômes légers et récents (rhume débutant, fatigue passagère, courbatures légères sans fièvre), soulageables par le repos et les mesures naturelles.

---

## 5. Réseau Hospitalier & Algorithme de Régulation

### 5.1. Cartographie des Établissements Pilotes
Conformément au **plan national de numérotation de l'ARCEP Bénin à 10 chiffres** :

#### Communes d'Abomey-Calavi :
1. **CHIC — Centre Hospitalier International de Calavi** : Standard `+229 01 21 40 01 00` / RDV `+229 01 21 40 01 11` (Face Tribunal)
2. **Hôpital de Zone Abomey-Calavi / Sô-Ava (CHUZ-AS)** : Standard `+229 01 21 36 01 50` / `+229 01 65 06 43 65` (Kansounkpa)
3. **Clinique Centrale de Calavi** : Ligne d'urgence 24/7 `+229 01 99 47 68 27` (Quartier Adjakè, RNIE2)
4. **Centre de Santé Calavi Kpota (CSA)** : `+229 01 67 04 35 47` (Carrefour Kpota)

#### Commune de Godomey :
1. **Clinique Mahoulé de Godomey** : `+229 01 91 91 93 43` (Dekoungbé)
2. **Hôpital Saint Jean Maria-Gléta** : `+229 01 69 27 91 10` / `+229 01 95 52 77 72` (Maria-Gléta / Togba)
3. **Clinique La Grâce de Vie** : `+229 01 50 89 05 25` (Hlacomey)
4. **Centre de Santé Eau-Vive (Clinique ADC)** : `+229 01 21 36 01 50` (Orientation zone sanitaire / SAMU 112)

#### Couverture Régionale (Autres Villes du Bénin) :
- Cotonou (CNHU-HKM) : `+229 01 21 30 06 56`
- Porto-Novo (CHUD Ouémé-Plateau) : `+229 01 20 21 35 90`
- Parakou (CHUD Borgou) : `+229 01 23 61 07 17`
- Bohicon, Natitingou, Lokossa, Kandi, Djougou.

### 5.2. Algorithme de Répartition des Flux
Lorsqu'une ville est identifiée (avec normalisation des accents et variantes phonétiques telles que *Bomekalavit* ou *Godomé*), le système exécute :
$$\text{Hôpital Sélectionné} = \arg\min_{h \in \mathcal{H}_{\text{ville}}} \left( \sum \text{Orientations}(h, t \ge \text{maintenant} - 2\text{ heures}) \right)$$
L'hôpital ayant orienté le moins de patients dans la tranche des deux dernières heures est priorisé afin d'éviter la saturation des services d'urgence.

---

## 6. Modèle de Données & Optimisation MySQL

La base de données relationnelle `esante_benin` s'articule autour de trois tables pourvues d'index de performance B-Tree :

### 6.1. Table `consultations`
Enregistre chaque interaction médicale terminée :
- `id` (INT PK AI) : Identifiant unique de la consultation
- `patient_id` (VARCHAR 50, Indexé) : Identifiant anonymisé du patient
- `prenom` (VARCHAR 100), `age` (INT), `sexe` (VARCHAR 20)
- `timestamp` (DATETIME, Indexé) : Date et heure de la consultation
- `symptomes` (TEXT), `duree` (VARCHAR 100), `localisation` (VARCHAR 100)
- `niveau_urgence` (VARCHAR 20) : vert / orange / rouge
- `hopital` (VARCHAR 200) : Nom de l'établissement recommandé
- `conseils` (TEXT) : Résumé des remèdes et conseils hygiéno-diététiques
- `conversation` (LONGTEXT) : Historique complet des tours de parole au format JSON
- `canal` (VARCHAR 20) : web ou telegram
- `alerte_traitee` (BOOLEAN) : Statut de prise en charge par le personnel soignant
- **Index composites :** `idx_consultations_hopital_timestamp` et `idx_consultations_urgence_timestamp`

### 6.2. Table `alertes`
File active des situations nécessitant une intervention soignante :
- `id` (INT PK AI)
- `consultation_id` (INT FK consultations.id)
- `patient_id` (VARCHAR 50), `prenom` (VARCHAR 100), `localisation` (VARCHAR 100)
- `niveau_urgence` (VARCHAR 20) : orange ou rouge
- `symptomes` (TEXT), `hopital` (VARCHAR 200), `timestamp` (DATETIME)
- `traitee` (BOOLEAN) : Indicateur d'acquittement
- `notes_medecin` (TEXT) : Compte-rendu d'intervention médicale
- **Index composite :** `idx_alertes_traitee_timestamp`

### 6.3. Table `sessions`
Persistance secondaire pour les reprises de sessions :
- `session_id` (VARCHAR 100 UNIQUE) : UUID de session
- `patient_id` (VARCHAR 50), `prenom`, `age`, `sexe`
- `historique` (LONGTEXT) : Messages au format JSON
- `created_at` (DATETIME), `updated_at` (DATETIME, Indexé)

---

## 7. Inventaire des Endpoints API

Toutes les routes d'administration et de consultation des données patients sont protégées par le protocole d'authentification soignant :

| Méthode | Route | Protection | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Publique | Page d'accueil web patient (`index.html`) |
| `GET` | `/health` | Publique | Diagnostic de disponibilité du serveur |
| `POST`| `/auth/login` | Publique | Connexion médecin régulateur $\rightarrow$ délivre un Bearer Token |
| `GET` | `/auth/verify`| Bearer Token | Validation de validité du jeton de session |
| `POST`| `/chat/text` | Publique | Échange patient textuel $\rightarrow$ réponse texte + audio MP3 |
| `POST`| `/chat/audio`| Publique | Envoi fichier audio $\rightarrow$ ASR Whisper + LLM + audio MP3 |
| `GET` | `/consultations` | Bearer Token | Liste paginée et filtrable des consultations |
| `GET` | `/consultation/{id}` | Bearer Token | Dossier clinique complet d'une consultation |
| `GET` | `/alertes` | Bearer Token | Liste des alertes prioritaires non traitées |
| `PATCH`| `/alertes/{id}/traiter` | Bearer Token | Acquittement d'une alerte par le médecin régulateur |
| `GET` | `/stats` | Bearer Token | Statistiques consolidées et répartition des flux |
| `DELETE`| `/session/{id}` | Publique | Clôture manuelle d'une session de discussion |

---

## 8. Sécurité, Confidentialité & Résilience

1. **Authentification HMAC-SHA256 :**  
   Les jetons délivrés aux soignants sont signés cryptographiquement contre une clé secrète (`DASHBOARD_SECRET_KEY`) avec horodatage d'expiration (24 heures). Toute falsification de payload entraîne un rejet immédiat (`HTTP 401`).
2. **Isolation Stricte des Secrets :**  
   Aucune clé API, mot de passe de base de données ou secret de signature n'est présent dans le code source. Toutes les variables sensibles sont confinées dans `.env` exclu du versionnement par `.gitignore`.
3. **Protection contre l'Injection de Prompts (Prompt Shielding) :**  
   Le modèle est explicitement verrouillé pour refuser les sujets extra-médicaux et ne jamais divulguer sa configuration interne, ses clés ou l'architecture de ses serveurs.
4. **Nettoyage et Cycle de Vie Audio :**  
   Tous les fichiers audios temporaires (`.webm`, `.ogg`, `.wav`, `.mp3`) créés pour les besoins de conversion de pydub ou ffmpeg sont supprimés dès la fin de la requête dans un bloc `finally`.
5. **Résilience Multi-Workers :**  
   Grâce au gestionnaire de sessions hybride (`session_manager.py`), plusieurs instances de l'API FastAPI peuvent être exécutées en parallèle derrière un répartiteur de charge sans perte d'état de conversation.

---

## 9. Validation & Résultats des Tests

Le système est couvert par une suite de **23 tests automatisés** exécutés via `pytest` et `unittest` :
- **4 tests de sécurité & authentification** : Validation des signatures valides, rejet des jetons altérés, protection contre les usurpations d'identité et les payloads corrompus.
- **6 tests de base de données réelle** : Connexion effective MySQL, présence des tables, intégrité des 6 index d'optimisation et interrogation des données réelles.
- **5 tests de normalisation linguistique** : Détection des communes (Abomey-Calavi, Godomey), suppression des accents, insensibilité à la casse et reconnaissance des transcriptions phonétiques.
- **2 tests de nettoyage de texte** : Filtrage du balisage markdown et tronquage propre des métadonnées JSON de fin de consultation.
- **2 tests de régulation hospitalière** : Élection systématique de l'hôpital le moins chargé et bascule sécurisée en cas d'indisponibilité momentanée de la base de données.
- **4 tests du gestionnaire de sessions** : Stockage, lecture, suppression et bascule transparente en cas de panne Redis.

*Taux de succès constaté : **100% (23/23 tests passés)**. Preuves visuelles et rapport interactif archivés dans `captures_tests/`.*

---

## 10. Bilan des Travaux Réalisés & Perspectives

### ✅ Travaux Réalisés et Validés
- [x] Correction de l'erreur de temporisation du badge orange Telegram (aligné sur 2 à 4 heures).
- [x] Remplacement du dashboard HTML statique par une application React 19 interactive.
- [x] Détection phonétique avancée des toponymes béninois (Calavi, Godomey, Togba, Kpota, Cocotiers).
- [x] Intégration des numéros hospitaliers officiels au plan 10 chiffres ARCEP Bénin et liens GPS.
- [x] Authentification soignant robuste (HMAC-SHA256) protégeant les dossiers patients.
- [x] Asynchronisme complet des communications réseau (`httpx`).
- [x] Gestionnaire de session hybride (Redis avec TTL + persistance MySQL).
- [x] Indexation complète des tables MySQL WAMP (accélération $O(\log N)$).
- [x] Harmonisation graphique (logo circulaire officiel partagé sur le Web et le Dashboard).

### 🔮 Perspectives d'Évolution Future
1. **Connecteur WhatsApp Business Cloud API :** Intégration du canal WhatsApp pour toucher directement la majorité des foyers béninois.
2. **Support des Langues Locales :** Expérimentation d'un module de transcription et synthèse en langue **Fongbé** pour les personnes non francophones.
3. **Voix de Synthèse Empathique :** Transition de gTTS vers un modèle vocal neural ouest-africain plus chaleureux.
4. **Déploiement Conteneurisé :** Orchestration Docker Compose (FastAPI + React + MySQL + Redis + Nginx) pour hébergement sur serveur dédié au Bénin.
