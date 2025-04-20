# utils/loader.py
import os
import logging
import importlib.util
from config import Config

logger = logging.getLogger('bot')

async def load_cogs(bot):
    """
    Charge tous les Cogs du bot en utilisant deux méthodes:
    1. Les extensions configurées dans Config.EXTENSIONS
    2. Certains cogs principaux importés directement
    """
    # Méthode 1: Chargement depuis Config.EXTENSIONS
    if hasattr(Config, 'EXTENSIONS') and Config.EXTENSIONS:
        for extension in Config.EXTENSIONS:
            try:
                await bot.load_extension(f"cogs.{extension}")
                logger.info(f"✅ Cog chargé : {extension}")
            except Exception as e:
                logger.error(f"❌ Erreur de chargement {extension}: {e}")
    
    # Méthode 2: Chargement direct des cogs principaux
    try:
        # Importations directes si les modules existent
        modules_to_import = ["commands_cog", "events_cog"]
        loaded_modules = 0
        
        for module_name in modules_to_import:
            try:
                # Vérifier si le module existe avant de l'importer
                spec = importlib.util.find_spec(module_name)
                if spec:
                    module = importlib.import_module(module_name)
                    cog_class_name = ''.join(word.capitalize() for word in module_name.split('_'))
                    if hasattr(module, cog_class_name):
                        cog_class = getattr(module, cog_class_name)
                        await bot.add_cog(cog_class(bot))
                        loaded_modules += 1
                        logger.info(f"✅ Cog principal chargé : {module_name}")
            except Exception as e:
                logger.error(f"❌ Erreur de chargement du cog principal {module_name}: {str(e)}")
        
        if loaded_modules > 0:
            logger.info(f"🧩 {loaded_modules} cogs principaux chargés avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur générale de chargement des cogs principaux : {str(e)}")

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