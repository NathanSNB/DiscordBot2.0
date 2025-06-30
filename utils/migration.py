import json
import os
import logging
import aiosqlite
from typing import Dict, Any
from .database import db_manager

logger = logging.getLogger('bot')

class DataMigration:
    """Classe pour migrer les anciennes données vers les bases de données par serveur"""
    
    def __init__(self):
        self.old_data_dir = "data"
    
    async def migrate_all_data(self, guild_id: int):
        """Migre toutes les données d'un serveur vers sa DB dédiée"""
        logger.info(f"🔄 Migration des données pour le serveur {guild_id}")
        
        try:
            # S'assurer que la DB du serveur est initialisée
            await db_manager.init_guild_database(guild_id)
            
            await self.migrate_stats(guild_id)
            await self.migrate_warnings(guild_id)
            await self.migrate_ticket_config(guild_id)
            await self.migrate_roles_config(guild_id)
            await self.migrate_rules_config(guild_id)
            await self.migrate_user_preferences(guild_id)
            
            logger.info(f"✅ Migration terminée pour le serveur {guild_id}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la migration: {str(e)}")
    
    async def migrate_stats(self, guild_id: int):
        """Migre les statistiques utilisateurs vers la DB du serveur"""
        stats_file = os.path.join(self.old_data_dir, "stats.json")
        if not os.path.exists(stats_file):
            return
            
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)
        
        db_path = db_manager.get_db_path(guild_id)
        
        # Migrer les messages et temps vocal
        async with aiosqlite.connect(db_path) as db:
            for user_id, message_count in stats_data.get('messages', {}).items():
                voice_time = stats_data.get('voice_time', {}).get(user_id, 0)
                last_online = stats_data.get('last_online', {}).get(user_id, '')
                
                await db.execute('''
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, messages, voice_time, last_online)
                    VALUES (?, ?, ?, ?)
                ''', (int(user_id), message_count, voice_time, last_online))
            await db.commit()
        
        logger.info(f"✅ Statistiques migrées pour {len(stats_data.get('messages', {}))} utilisateurs")
    
    async def migrate_warnings(self, guild_id: int):
        """Migre les avertissements vers la DB du serveur"""
        warns_file = os.path.join(self.old_data_dir, "warns.json")
        if not os.path.exists(warns_file):
            return
            
        with open(warns_file, 'r', encoding='utf-8') as f:
            warns_data = json.load(f)
        
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            for user_id, warnings in warns_data.get('warnings', {}).items():
                for warning in warnings:
                    created_at = warning[0]  # datetime ISO format
                    reason = warning[1]
                    author_id = warning[2]
                    
                    await db.execute('''
                        INSERT INTO warnings 
                        (user_id, reason, author_id, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (int(user_id), reason, author_id, created_at))
            await db.commit()
        
        logger.info(f"✅ Avertissements migrés")
    
    async def migrate_ticket_config(self, guild_id: int):
        """Migre la configuration des tickets vers la DB du serveur"""
        ticket_file = os.path.join(self.old_data_dir, "ticket_config.json")
        if not os.path.exists(ticket_file):
            return
            
        with open(ticket_file, 'r', encoding='utf-8') as f:
            ticket_data = json.load(f)
        
        await db_manager.update_guild_config(
            guild_id,
            ticket_category_id=ticket_data.get('category_id'),
            ticket_create_channel_id=ticket_data.get('create_channel_id'),
            ticket_log_channel_id=ticket_data.get('log_channel_id'),
            extra_config={
                'ticket_message_id': ticket_data.get('ticket_message_id'),
                'archive_category_id': ticket_data.get('archive_category_id'),
                'ticket_reasons': ticket_data.get('ticket_reasons', [])
            }
        )
        
        logger.info("✅ Configuration des tickets migrée")
    
    async def migrate_roles_config(self, guild_id: int):
        """Migre la configuration des rôles vers la DB du serveur"""
        roles_file = os.path.join(self.old_data_dir, "roles_config.json")
        if not os.path.exists(roles_file):
            return
            
        with open(roles_file, 'r', encoding='utf-8') as f:
            roles_data = json.load(f)
        
        db_path = db_manager.get_db_path(guild_id)
        
        async with aiosqlite.connect(db_path) as db:
            for role_id, role_info in roles_data.items():
                await db.execute('''
                    INSERT OR REPLACE INTO role_config 
                    (role_id, role_name, description, emoji)
                    VALUES (?, ?, ?, ?)
                ''', (role_info['id'], role_info['name'], 
                      role_info.get('description', ''), role_info.get('emoji', '')))
            await db.commit()
        
        logger.info(f"✅ Configuration des rôles migrée ({len(roles_data)} rôles)")
    
    async def migrate_rules_config(self, guild_id: int):
        """Migre la configuration des règles vers la DB du serveur"""
        rules_config_file = os.path.join(self.old_data_dir, "rules_config.json")
        if os.path.exists(rules_config_file):
            with open(rules_config_file, 'r', encoding='utf-8') as f:
                rules_config = json.load(f)
            
            await db_manager.update_guild_config(
                guild_id,
                rules_channel_id=rules_config.get('rules_channel_id'),
                rules_message_id=rules_config.get('rules_message_id'),
                verified_role_id=rules_config.get('verified_role_id'),
                default_role_id=rules_config.get('default_role_id')
            )
        
        logger.info("✅ Configuration des règles migrée")
    
    async def migrate_user_preferences(self, guild_id: int):
        """Migre les préférences utilisateur (Minecraft, etc.)"""
        prefs_file = os.path.join(self.old_data_dir, "user_preferences.json")
        if not os.path.exists(prefs_file):
            return
            
        with open(prefs_file, 'r', encoding='utf-8') as f:
            prefs_data = json.load(f)
        
        mc_config = prefs_data.get('minecraft', {})
        if mc_config:
            server_config = mc_config.get('server', {})
            discord_config = mc_config.get('discord', {})
            
            await db_manager.update_guild_config(
                guild_id,
                mc_server_ip=server_config.get('ip'),
                mc_server_port=int(server_config.get('port', 25565)),
                mc_status_channel_id=int(discord_config.get('statusChannelId', 0)) or None,
                mc_notification_role_id=int(discord_config.get('notificationRoleId', 0)) or None
            )
        
        logger.info("✅ Préférences utilisateur migrées")

# Instance globale
migration_manager = DataMigration()
