import os
import logging
from config import Config

logger = logging.getLogger("bot")

async def load_cogs(bot):
    """Charge tous les Cogs automatiquement"""
    for extension in Config.EXTENSIONS:
        try:
            await bot.load_extension(f"cogs.{extension}")
            logger.info(f"✅ Cog chargé : {extension}")
        except Exception as e:
            logger.error(f"❌ Erreur de chargement {extension}: {e}")