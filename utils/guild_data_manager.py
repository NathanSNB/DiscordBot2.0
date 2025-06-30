"""
Gestionnaire unifié pour l'accès aux données par serveur
Utilise les bases de données indépendantes par serveur
"""
import json
from typing import Dict, Any, Optional
from .database import db_manager
import aiosqlite

class GuildDataManager:
    """Gestionnaire unifié des données par serveur avec DB indépendantes"""
    
    @staticmethod
    async def get_guild_config(guild_id: int) -> Dict[str, Any]:
        """Récupère la configuration complète d'un serveur"""
        return await db_manager.get_guild_config(guild_id)
    
    @staticmethod
    async def update_guild_config(guild_id: int, **kwargs):
        """Met à jour la configuration d'un serveur"""
        await db_manager.update_guild_config(guild_id, **kwargs)
    
    @staticmethod
    async def get_user_stats(guild_id: int, user_id: int) -> Dict[str, Any]:
        """Récupère les statistiques d'un utilisateur pour un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute('''
                SELECT messages, voice_time, last_online 
                FROM user_stats 
                WHERE user_id = ?
            ''', (user_id,))
            row = await cursor.fetchone()
            
            if row:
                return {
                    'messages': row[0],
                    'voice_time': row[1], 
                    'last_online': row[2]
                }
            return {'messages': 0, 'voice_time': 0, 'last_online': ''}
    
    @staticmethod
    async def update_user_stats(guild_id: int, user_id: int, **kwargs):
        """Met à jour les statistiques d'un utilisateur pour un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            # Construire la requête dynamiquement
            if kwargs:
                set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
                
                await db.execute(f'''
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, {', '.join(kwargs.keys())})
                    VALUES (?, {', '.join(['?' for _ in kwargs])})
                    ON CONFLICT(user_id) DO UPDATE SET
                    {set_clause}, updated_at = CURRENT_TIMESTAMP
                ''', [user_id] + list(kwargs.values()) + list(kwargs.values()))
                await db.commit()
    
    @staticmethod
    async def get_warnings(guild_id: int, user_id: int) -> list:
        """Récupère les avertissements d'un utilisateur pour un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute('''
                SELECT reason, author_id, created_at 
                FROM warnings 
                WHERE user_id = ?
                ORDER BY created_at DESC
            ''', (user_id,))
            rows = await cursor.fetchall()
            return [(row[2], row[0], row[1]) for row in rows]  # Format: (datetime, reason, author_id)
    
    @staticmethod
    async def add_warning(guild_id: int, user_id: int, reason: str, author_id: int) -> int:
        """Ajoute un avertissement et retourne le nombre total pour ce serveur"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''
                INSERT INTO warnings (user_id, reason, author_id)
                VALUES (?, ?, ?)
            ''', (user_id, reason, author_id))
            
            # Compter le total pour ce serveur
            cursor = await db.execute('''
                SELECT COUNT(*) FROM warnings 
                WHERE user_id = ?
            ''', (user_id,))
            total = (await cursor.fetchone())[0]
            
            await db.commit()
            return total
    
    @staticmethod
    async def get_role_config(guild_id: int) -> Dict[str, Dict]:
        """Récupère la configuration des rôles d'un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute('''
                SELECT role_id, role_name, description, emoji 
                FROM role_config
            ''')
            rows = await cursor.fetchall()
            
            return {
                str(row[0]): {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'emoji': row[3]
                } for row in rows
            }
    
    @staticmethod
    async def add_role_config(guild_id: int, role_id: int, name: str, description: str = '', emoji: str = ''):
        """Ajoute une configuration de rôle pour un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''
                INSERT OR REPLACE INTO role_config 
                (role_id, role_name, description, emoji)
                VALUES (?, ?, ?, ?)
            ''', (role_id, name, description, emoji))
            await db.commit()
    
    @staticmethod
    async def remove_role_config(guild_id: int, role_id: int):
        """Supprime une configuration de rôle pour un serveur spécifique"""
        await db_manager.init_guild_database(guild_id)
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            await db.execute('''
                DELETE FROM role_config 
                WHERE role_id = ?
            ''', (role_id,))
            await db.commit()

# Instance globale
guild_data = GuildDataManager()
