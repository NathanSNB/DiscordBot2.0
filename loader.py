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
    
    # Fichiers à ignorer pour éviter les conflits
    ignored_files = ["color.py"]  # Fichier qui cause des conflits avec ColorCommands
    
    logger.info(f"🔄 Chargement des modules...")
    loaded = 0
    failed = 0

    # Charger les cogs restants
    for folder in cog_folders:
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            logger.info(f"📁 Dossier {folder} créé")
        
        for filename in os.listdir(folder):
            # Ignorer les fichiers qui ne sont pas des modules Python valides
            if (filename.endswith(".py") and 
                filename != "__init__.py" and 
                not filename.startswith("_") and 
                not filename.startswith(".") and
                filename not in ignored_files):
                
                module_path = f"{folder}/{filename}".replace("/", ".").replace(".py", "")
                
                # Vérifier si le cog n'est pas déjà chargé
                try:
                    # Vérifier les noms de cogs potentiels pour éviter les doublons
                    cog_names_to_check = []
                    if "color" in filename.lower():
                        cog_names_to_check.append("ColorCommands")
                    
                    skip_loading = False
                    for cog_name in cog_names_to_check:
                        if cog_name in bot.cogs:
                            logger.info(f"⚠️ Cog {cog_name} déjà chargé, ignore {module_path}")
                            skip_loading = True
                            break
                    
                    if skip_loading:
                        continue
                    
                    await bot.load_extension(module_path)
                    logger.info(f"✅ Module chargé: {module_path}")
                    loaded += 1
                except Exception as e:
                    logger.error(f"❌ Erreur lors du chargement du module {module_path}: {str(e)}")
                    logger.error(traceback.format_exc())
                    failed += 1
    
    # Afficher un résumé du chargement des modules
    logger.info(f"📊 Résultat du chargement des modules: {loaded} réussis, {failed} échoués")
    
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