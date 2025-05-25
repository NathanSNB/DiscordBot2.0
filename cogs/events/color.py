"""
Module de redirection pour les commandes de couleur.
Ce module permet de charger les commandes de couleur depuis 'couleur.py'.
"""

import logging
import discord
from discord.ext import commands

# Initialiser le logger correctement
logger = logging.getLogger('bot')

# Tenter d'importer depuis le fichier couleur.py
try:
    from ..commands.couleur import ColorCommands
    
    # Ajouter une indication que le module a été importé correctement
    logger.info("✅ Module ColorCommands importé avec succès depuis couleur.py")
except ImportError as e:
    # En cas d'échec, créer une version simplifiée de la classe
    logger.error(f"❌ Erreur d'importation de ColorCommands: {e}")
    
    class ColorCommands(commands.Cog, name="ColorCommands"):
        """Commandes pour personnaliser les couleurs du bot et son apparence"""
        
        def __init__(self, bot):
            self.bot = bot
            logger.warning("⚠️ Version de secours de ColorCommands initialisée")

# Fonction setup nécessaire pour le chargement du cog
async def setup(bot):
    await bot.add_cog(ColorCommands(bot))
    logger.info("✅ Module ColorCommands chargé depuis color.py")
