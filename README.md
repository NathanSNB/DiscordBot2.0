# 🤖 DiscordBot 2.0

> Un bot avancé développé avec `discord.py`, regroupant modération, statistiques, économie, musique et bien plus encore.

---

## 📝 Description

**DiscordBot 2.0** est un bot Discord complet, conçu pour les serveurs souhaitant une solution tout-en-un. Il propose des outils puissants pour la **modération**, des **statistiques détaillées**, une **économie virtuelle**, une **intégration musicale**, ainsi qu'un système de **suivi Minecraft**.

Le bot utilise un **système de base de données par serveur**, permettant une isolation complète des données entre différents serveurs Discord.

---

## ⚙️ Installation

### 🧰 Prérequis

- Python **3.8+**
- FFmpeg (requis pour la musique)
- Git

### 🛠️ Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone https://github.com/NathanSNB/DiscordBot2.0.git
   cd DiscordBot2.0
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

5. **🆕 Configurer les bases de données**
   ```bash
   python setup_database.py
   ```
   > Ce script initialise le système de base de données et explique le fonctionnement par serveur.

6. **Lancer le bot**
   ```bash
   python bot.py
   ```

---

## 🎮 Fonctionnalités

### 🛡️ Modération
- `!kick`, `!ban` — Sanctions utilisateurs  
- `!clear` — Suppression de messages  
- `!heresie` — Verrouillage d'urgence  
- `!mute`, `!unmute` — Gestion des mutes  

### 💰 Économie
- `!cc` — Afficher les crédits sociaux  
- `!add`, `!remove` — Ajouter/retirer des crédits  
- `!create` — Créer un compte utilisateur  

### 📊 Statistiques
- `!stats` — Statistiques personnelles  
- `!serverstats` — Données globales du serveur  
- `!top` — Classements top utilisateurs  
- `!activity` — Graphiques d'activité (matplotlib)  
- `!gamestats` - Classements des utilisateurs par jeux

### 🎵 Musique
- `!play` — Lire une musique (YouTube, etc.)  
- `!stop` — Stop la lecture  

### ⛏️ Minecraft
- `!mcstat` — Vérifier l'état d'un serveur Minecraft  

---

## 📁 Structure du Projet

```
📦 discordbot/
├── cogs/                  # Modules/fonctionnalités du bot
├── data/                  # Fichiers JSON de données (anciennes données)
│   └── databases/         # 🆕 Bases de données par serveur
│       ├── global.db      # Base de données globale (whitelist/blacklist)
│       ├── guild_123.db   # Base de données du serveur 123
│       └── guild_456.db   # Base de données du serveur 456
├── logs/                  # Logs d'activité et erreurs
├── utils/                 # Scripts utilitaires du bot 
│   ├── database.py        # 🆕 Gestionnaire de base de données
│   ├── migration.py       # 🆕 Migration des anciennes données
│   └── logger.py          # Système de logs
├── .env                   # Variables d'environnement - **à configurer**
├── bot.py                 # Script principal
├── setup_database.py      # 🆕 Configuration initiale des bases de données
├── loader.py              # Chargement des COG's
├── config.py              # Configuration du bot - liée au .env
├── README.md              # Ce que vous voyez
└── requirements.txt       # Dépendances Python - **à installer**
```

---

## 🆕 Système de Base de Données

### 🔄 Base de Données par Serveur
- **Chaque serveur Discord** a sa propre base de données SQLite
- **Isolation complète** des données entre serveurs
- **Migration automatique** des anciennes données JSON
- **Performance optimisée** pour les gros serveurs

### 🌐 Base de Données Globale
- Gestion des **whitelist/blacklist** de serveurs
- **Enregistrement** des serveurs utilisant le bot
- **Statistiques globales** d'utilisation

### 📊 Tables par Serveur
- `user_stats` — Statistiques des utilisateurs (messages, temps vocal)
- `warnings` — Système d'avertissements
- `tickets` — Gestion des tickets de support
- `role_config` — Configuration des rôles
- `guild_config` — Configuration générale du serveur
- `message_history` — Historique des messages par heure
- `games_played` — Jeux joués par les utilisateurs

---

## 🚀 Ordre de Lancement

### ⚠️ Première Installation
1. **Configuration des bases de données**
   ```bash
   python setup_database.py
   ```

2. **Lancement du bot**
   ```bash
   python bot.py
   ```

### 🔄 Utilisation Normale
Après la première configuration, lancez simplement :
```bash
python bot.py
```

Le bot créera automatiquement une base de données pour chaque nouveau serveur qu'il rejoint.

---

## 📦 Dépendances principales

- `discord.py[voice]` — Framework principal
- `python-dotenv` — Chargement des variables d'environnement
- `matplotlib` — Graphiques d'activité
- `yt-dlp` — Lecture audio depuis YouTube
- `mcstatus` — Vérification des serveurs Minecraft
- `coloredlogs` — Logs colorés
- `aiosqlite` — 🆕 Base de données SQLite asynchrone

---

## 🛠️ Maintenance

### 🗂️ Logs

Tous les logs sont disponibles dans le dossier `logs/` :

- Erreurs système
- Utilisation des commandes
- Événements importants
- 🆕 Opérations de base de données

### 💾 Données

Les données sont maintenant stockées dans des bases de données SQLite :

#### 🆕 Nouvelles Données (SQLite)
- `data/databases/global.db` — Données globales du bot
- `data/databases/guild_*.db` — Données spécifiques à chaque serveur

#### 📁 Anciennes Données (JSON - Migration automatique)
- `data/economy.json` — Crédits sociaux (migré)
- `data/stats.json` — Statistiques des utilisateurs (migré)
- `data/reminders.json` — Configuration des rappels
- `data/roles_config.json` — Configuration du !roles (migré)

---

## 🔧 Migration des Données

Le système migre automatiquement vos anciennes données JSON vers les nouvelles bases de données SQLite :

- ✅ **Statistiques utilisateurs** (messages, temps vocal)
- ✅ **Avertissements** avec historique complet
- ✅ **Configuration des tickets**
- ✅ **Configuration des rôles**
- ✅ **Règles du serveur**
- ✅ **Préférences Minecraft**

La migration se fait **une seule fois** lors de la première utilisation sur un serveur.

---

## 📫 Support

Besoin d'aide ou d'un retour ?

- 🧵 Discord : _mrNathan
- 📧 Email : natSNB68@gmail.com

---

## 📄 Licence

Projet sous licence **GPL 3.0**.

Développé avec ❤️ par **Nathan** et **Gitex**

![Python](https://img.shields.io/badge/python-3.8-blue)
![License](https://img.shields.io/badge/license-GPLv3-blue)
![Dependencies](https://img.shields.io/badge/dependencies-up%20to%20date-brightgreen)
![Project Status](https://img.shields.io/badge/status-en%20développement-yellow)
![Langue](https://img.shields.io/badge/langue-français-blue)
![Database](https://img.shields.io/badge/database-SQLite-green)

