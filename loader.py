# utils/loader.py
import os
import logging
import traceback
import asyncio
from pathlib import Path

from config import Config

logger = logging.getLogger("bot")

async def load_cogs(bot):
    """
    Charge tous les cogs du bot depuis les dossiers 'cogs/commands' et 'cogs/events'
    """
    # Liste de tous les cogs à charger (avec leur chemin relatif)
    cog_folders = ["cogs/commands", "cogs/events"]
    
    logger.info(f"🔄 Chargement des modules...")
    loaded = 0
    failed = 0

    # Charger les cogs restants
    for folder in cog_folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            logger.info(f"📁 Dossier {folder} créé")
        
        for filename in os.listdir(folder):
            if filename.endswith(".py"):
                module_path = f"{folder}/{filename}".replace("/", ".").replace(".py", "")
                try:
                    await bot.load_extension(module_path)
                    logger.info(f"✅ Module chargé: {module_path}")
                    loaded += 1
                except Exception as e:
                    logger.error(f"❌ Erreur lors du chargement du module {module_path}: {str(e)}")
                    logger.error(traceback.format_exc())
                    failed += 1
    
    # Afficher un résumé du chargement des modules
    logger.info(f"📊 Résultat du chargement des modules: {loaded} réussis, {failed} échoués")
    
    # Vérification spécifique pour le module ColorCommands
    has_color_commands = False
    for cog_name, cog in bot.cogs.items():
        if cog_name == "ColorCommands":
            has_color_commands = True
            logger.info("✅ Module ColorCommands correctement chargé")
            break
    
    # Si ColorCommands n'est pas chargé, essayer de le charger spécifiquement
    if not has_color_commands:
        try:
            # Tenter de charger directement depuis couleur.py
            await bot.load_extension("cogs.commands.couleur")
            logger.info("✅ Module ColorCommands chargé avec succès depuis cogs.commands.couleur")
            has_color_commands = True
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de ColorCommands depuis couleur.py: {str(e)}")
            try:
                # Tenter avec color.py comme backup
                await bot.load_extension("cogs.commands.color")
                logger.info("✅ Module ColorCommands chargé avec succès depuis cogs.commands.color")
                has_color_commands = True
            except Exception as e2:
                logger.error(f"❌ Erreur lors du chargement de ColorCommands depuis color.py: {str(e2)}")
                logger.warning("⚠️ Module ColorCommands non chargé! Vérifiez les fichiers couleur.py et color.py")
    
    return loaded, failed

async def reload_cogs(bot):
    """Recharge tous les cogs actifs du bot"""
    cogs_list = list(bot.extensions.keys())
    success_count = 0
    
    for cog in cogs_list:
        try:
            await bot.reload_extension(cog)
            success_count += 1
            logger.info(f"🔄 Cog rechargé : {cog}")
        except Exception as e:
            logger.error(f"❌ Erreur lors du rechargement de {cog}: {str(e)}")
    
    logger.info(f"✅ {success_count}/{len(cogs_list)} cogs rechargés avec succès")
    return success_count, len(cogs_list)

async def get_cogs_status(bot):
    """Retourne l'état de tous les cogs configurés"""
    cogs_status = {}
    
    # Vérifier les cogs des extensions
    if hasattr(Config, 'EXTENSIONS') and Config.EXTENSIONS:
        for extension in Config.EXTENSIONS:
            cog_path = f"cogs.{extension}"
            cogs_status[cog_path] = cog_path in bot.extensions
    
    # Vérifier les cogs principaux
    for cog in bot.cogs:
        cogs_status[cog] = True
        
    return cogs_status