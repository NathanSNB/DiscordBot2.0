# 🤖 DiscordBot 2.0

> Un bot avancé développé avec `discord.py`, regroupant modération, statistiques, économie, musique et bien plus encore.

---

## 📝 Description

**DiscordBot 2.0** est un bot Discord complet, conçu pour les serveurs souhaitant une solution tout-en-un. Il propose des outils puissants pour la **modération**, des **statistiques détaillées**, une **économie virtuelle**, une **intégration musicale**, ainsi qu’un système de **suivi Minecraft**.

---

## ⚙️ Installation

### 🧰 Prérequis

- Python **3.8+**
- FFmpeg (requis pour la musique)
- Git

### 🛠️ Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone https://github.com/votre-utilisateur/discordbot.git
   cd discordbot
   ```

2. **Créer un environnement virtuel**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer le fichier `.env`**
   > Ajoutez vos tokens et clés API dans un fichier `.env` à la racine du projet.

---

## 🎮 Fonctionnalités

### 🛡️ Modération
- `!kick`, `!ban` — Sanctions utilisateurs  
- `!clear` — Suppression de messages  
- `!heresie` — Verrouillage d’urgence  
- `!mute`, `!unmute` — Gestion des mutes  

### 💰 Économie
- `!cc` — Afficher les crédits sociaux  
- `!add`, `!remove` — Ajouter/retirer des crédits  
- `!create` — Créer un compte utilisateur  

### 📊 Statistiques
- `!stats` — Statistiques personnelles  
- `!serverstats` — Données globales du serveur  
- `!top` — Classements top utilisateurs  
- `!activity` — Graphiques d’activité (matplotlib)  
- `!gamestats` - Classements des utilisateurs par jeux

### 🎵 Musique
- `!play` — Lire une musique (YouTube, etc.)  
- `!stop` — Stop la lecture  

### ⛏️ Minecraft
- `!mcstat` — Vérifier l’état d’un serveur Minecraft  

---

## 📁 Structure Importante du Projet

```
📦 discordbot/
├── cogs/              # Modules/fonctionnalités du bot
├── data/              # Fichiers JSON de données (économie, stats...)
├── logs/              # Logs d’activité et erreurs
├── utils/             # Scrpits utilitaires du bot 
├── .env               # Variables d’environnement - **à configurer**
├── bot.py             # Script principal
├── loader.py          # Chargement des COG's
├── config.py          # Configuration du bot - liée au .env
├── README.md          # Ce que vous voyez
└── requirements.txt   # Dépendances Python - **à installer**
```

---

## 🚀 Lancement du Bot

1. **Activer l’environnement virtuel**
2. **Importer l'ensemble des dépendances**
   ```
      pip install -r requirements.txt
   ```
3. **Configurer les fichiers**
- .env - sous exemple env.txt
- reminders.json - possible via commandes 
- roles_config.json - possible via commandes 

4. **Lancer le bot**
   ```bash
   python bot.py


---

## 📦 Dépendances principales

- `discord.py[voice]` — Framework principal
- `python-dotenv` — Chargement des variables d’environnement
- `matplotlib` — Graphiques d’activité
- `yt-dlp` — Lecture audio depuis YouTube
- `mcstatus` — Vérification des serveurs Minecraft
- `coloredlogs` — Logs colorés

---

## 🛠️ Maintenance

### 🗂️ Logs

Tous les logs sont disponibles dans le dossier `logs/` :

- Erreurs système
- Utilisation des commandes
- Événements importants

### 💾 Données

Les données persistantes sont stockées dans `data/` :

- `economy.json` — Crédits sociaux
- `stats.json` — Statistiques des utilisateurs
- `reminders.json` — Configuration des rappels
- `roles_config.json`— Configuration du !roles 

---

## 📫 Support

Besoin d’aide ou d’un retour ?

- 🧵 Discord : _mrNathan
- 📧 Email : natSNB68@gmail.com

---

## 📄 Licence

Projet sous licence **MIT**.

Développé avec ❤️ par **Nathan**