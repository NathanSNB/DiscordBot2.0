"""
Script d'installation et de migration vers le système de base de données par serveur
"""
import asyncio
import os
import sys
import logging
from utils.database import db_manager
from utils.migration import migration_manager

async def setup_database():
    """Configure la base de données globale et explique le système par serveur"""
    print("🚀 Configuration du nouveau système de base de données...")
    
    # Initialiser la base de données globale
    await db_manager.init_global_database()
    print("✅ Base de données globale initialisée")
    
    print("\n📋 Informations importantes :")
    print("• Chaque serveur aura maintenant sa propre base de données")
    print("• Les DB se créent automatiquement quand le bot rejoint un serveur")
    print("• Les anciennes données seront migrées automatiquement")
    print("• Les accès globaux (whitelist/blacklist) restent centralisés")
    
    # Proposer de migrer pour un serveur spécifique si besoin
    guild_id = input("\n📝 ID d'un serveur spécifique pour test de migration (optionnel, appuyez sur Entrée pour ignorer): ")
    
    if guild_id and guild_id.isdigit():
        guild_id = int(guild_id)
        print(f"🔄 Test de migration pour le serveur {guild_id}...")
        await db_manager.init_guild_database(guild_id)
        await migration_manager.migrate_all_data(guild_id)
        print("✅ Test de migration terminé")
    
    print("\n🎉 Configuration terminée !")
    print("• Le bot créera automatiquement une DB pour chaque nouveau serveur")
    print("• Vous pouvez maintenant démarrer le bot en toute sécurité")

if __name__ == "__main__":
    asyncio.run(setup_database())
