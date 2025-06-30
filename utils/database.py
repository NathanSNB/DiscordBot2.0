import sqlite3
import json
import logging
import os
from typing import Optional, Any, Dict, List
import asyncio
import aiosqlite

logger = logging.getLogger('bot')

class DatabaseManager:
    """Gestionnaire de base de données avec une DB par serveur"""
    
    def __init__(self, base_path: str = "data/databases"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self._initialized_guilds = set()  # Garde en mémoire les serveurs initialisés
        
    def get_db_path(self, guild_id: int) -> str:
        """Retourne le chemin de la base de données pour un serveur spécifique"""
        return os.path.join(self.base_path, f"guild_{guild_id}.db")
    
    async def init_guild_database(self, guild_id: int):
        """Initialise la base de données pour un serveur spécifique"""
        if guild_id in self._initialized_guilds:
            return  # Déjà initialisé
            
        db_path = self.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            # Table pour les statistiques des utilisateurs
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    messages INTEGER DEFAULT 0,
                    voice_time INTEGER DEFAULT 0,
                    last_online TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            ''')
            
            # Table pour les avertissements
            await db.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    reason TEXT,
                    author_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table pour les tickets
            await db.execute('''
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT,
                    owner_id INTEGER,
                    channel_id INTEGER,
                    status TEXT DEFAULT 'open',
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    closed_by INTEGER,
                    close_reason TEXT
                )
            ''')
            
            # Table pour les rôles configurés
            await db.execute('''
                CREATE TABLE IF NOT EXISTS role_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER,
                    role_name TEXT,
                    description TEXT,
                    emoji TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(role_id)
                )
            ''')
            
            # Table pour la configuration du serveur
            await db.execute('''
                CREATE TABLE IF NOT EXISTS guild_config (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    embed_color INTEGER DEFAULT 2827571,
                    rules_channel_id INTEGER,
                    rules_message_id INTEGER,
                    verified_role_id INTEGER,
                    default_role_id INTEGER,
                    ticket_category_id INTEGER,
                    ticket_create_channel_id INTEGER,
                    ticket_log_channel_id INTEGER,
                    mc_server_ip TEXT,
                    mc_server_port INTEGER DEFAULT 25565,
                    mc_status_channel_id INTEGER,
                    mc_notification_role_id INTEGER,
                    roles_channel_id INTEGER,
                    config_data TEXT, -- JSON pour configurations supplémentaires
                    CHECK (id = 1)
                )
            ''')
            
            # Insérer la configuration par défaut si elle n'existe pas
            await db.execute('''
                INSERT OR IGNORE INTO guild_config (id) VALUES (1)
            ''')
            
            # Table pour les whitelist/blacklist (au niveau global, pas par serveur)
            # Cette table sera dans une DB séparée pour la gestion globale
            
            # Table pour l'historique des messages (par heure)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS message_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    hour_timestamp TEXT, -- Format: YYYY-MM-DD HH:00
                    message_count INTEGER DEFAULT 0,
                    UNIQUE(user_id, hour_timestamp)
                )
            ''')
            
            # Table pour les jeux joués
            await db.execute('''
                CREATE TABLE IF NOT EXISTS games_played (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    game_name TEXT,
                    play_time INTEGER DEFAULT 0, -- en minutes
                    last_played TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, game_name)
                )
            ''')
            
            await db.commit()
            
        self._initialized_guilds.add(guild_id)
        logger.info(f"✅ Base de données initialisée pour le serveur {guild_id}")
    
    async def init_global_database(self):
        """Initialise la base de données globale pour les fonctions du bot"""
        global_db_path = os.path.join(self.base_path, "global.db")
        
        async with aiosqlite.connect(global_db_path) as db:
            # Table pour les whitelist/blacklist globales
            await db.execute('''
                CREATE TABLE IF NOT EXISTS access_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    list_type TEXT CHECK (list_type IN ('whitelist', 'blacklist')),
                    reason TEXT,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id, list_type)
                )
            ''')
            
            # Table pour les serveurs enregistrés
            await db.execute('''
                CREATE TABLE IF NOT EXISTS registered_guilds (
                    guild_id INTEGER PRIMARY KEY,
                    guild_name TEXT,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.commit()
            
        logger.info("✅ Base de données globale initialisée")
    
    async def register_guild(self, guild_id: int, guild_name: str):
        """Enregistre un nouveau serveur et initialise sa base de données"""
        # Initialiser la DB du serveur
        await self.init_guild_database(guild_id)
        
        # Enregistrer dans la DB globale
        global_db_path = os.path.join(self.base_path, "global.db")
        async with aiosqlite.connect(global_db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO registered_guilds (guild_id, guild_name, last_seen)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (guild_id, guild_name))
            await db.commit()
            
        logger.info(f"✅ Serveur {guild_name} ({guild_id}) enregistré avec sa propre base de données")
    
    async def is_guild_allowed(self, guild_id: int) -> bool:
        """Vérifie si un serveur est autorisé (utilise la DB globale)"""
        global_db_path = os.path.join(self.base_path, "global.db")
        async with aiosqlite.connect(global_db_path) as db:
            # Vérifier la blacklist
            cursor = await db.execute('''
                SELECT 1 FROM access_lists 
                WHERE guild_id = ? AND list_type = 'blacklist'
            ''', (guild_id,))
            if await cursor.fetchone():
                return False
            
            # Vérifier la whitelist (si elle existe)
            cursor = await db.execute('''
                SELECT COUNT(*) FROM access_lists 
                WHERE list_type = 'whitelist'
            ''')
            whitelist_count = (await cursor.fetchone())[0]
            
            if whitelist_count > 0:
                cursor = await db.execute('''
                    SELECT 1 FROM access_lists 
                    WHERE guild_id = ? AND list_type = 'whitelist'
                ''', (guild_id,))
                return await cursor.fetchone() is not None
            
            return True  # Aucune restriction si pas de whitelist
    
    async def add_to_access_list(self, guild_id: int, list_type: str, reason: str = None, added_by: int = None):
        """Ajoute un serveur à la whitelist ou blacklist (DB globale)"""
        global_db_path = os.path.join(self.base_path, "global.db")
        async with aiosqlite.connect(global_db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO access_lists 
                (guild_id, user_id, list_type, reason, added_by)
                VALUES (?, 0, ?, ?, ?)
            ''', (guild_id, list_type, reason, added_by))
            await db.commit()
    
    async def remove_from_access_list(self, guild_id: int, list_type: str):
        """Retire un serveur de la whitelist ou blacklist (DB globale)"""
        global_db_path = os.path.join(self.base_path, "global.db")
        async with aiosqlite.connect(global_db_path) as db:
            await db.execute('''
                DELETE FROM access_lists 
                WHERE guild_id = ? AND list_type = ?
            ''', (guild_id, list_type))
            await db.commit()

    async def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """Récupère la configuration d'un serveur depuis sa DB dédiée"""
        await self.init_guild_database(guild_id)  # S'assurer que la DB existe
        
        db_path = self.get_db_path(guild_id)
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute('''
                SELECT * FROM guild_config WHERE id = 1
            ''')
            row = await cursor.fetchone()
            
            if row:
                # Convertir le résultat en dictionnaire
                columns = [description[0] for description in cursor.description]
                config = dict(zip(columns, row))
                
                # Décoder les données JSON si présentes
                if config.get('config_data'):
                    try:
                        config['extra_config'] = json.loads(config['config_data'])
                    except:
                        config['extra_config'] = {}
                else:
                    config['extra_config'] = {}
                
                return config
            
            # Configuration par défaut si non trouvée
            return {
                'guild_id': guild_id,
                'embed_color': 2827571,
                'extra_config': {}
            }
    
    async def update_guild_config(self, guild_id: int, **kwargs):
        """Met à jour la configuration d'un serveur dans sa DB dédiée"""
        await self.init_guild_database(guild_id)  # S'assurer que la DB existe
        
        # Séparer les données JSON des colonnes directes
        extra_config = kwargs.pop('extra_config', {})
        
        if kwargs:
            # Construire la requête dynamiquement
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            
            db_path = self.get_db_path(guild_id)
            async with aiosqlite.connect(db_path) as db:
                await db.execute(f'''
                    UPDATE guild_config 
                    SET {set_clause}
                    WHERE id = 1
                ''', values)
                
                # Mettre à jour les données JSON si nécessaire
                if extra_config:
                    await db.execute('''
                        UPDATE guild_config 
                        SET config_data = ?
                        WHERE id = 1
                    ''', (json.dumps(extra_config),))
                
                await db.commit()

# Instance globale
db_manager = DatabaseManager()
