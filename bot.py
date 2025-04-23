import discord
from discord.ext import commands
import asyncio
from config import Config
from loader import load_cogs
from utils.logger import setup_logger
from utils.permission_manager import PermissionManager  # Assurez-vous que ce module existe
import logging

logger = setup_logger()

class MathysieBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=discord.Intents.all(),
            help_command=None
        )
        self.config = Config
        self.perm_manager = PermissionManager("data/permissions.json")  # Ajout de l'initialisation

    async def setup_hook(self):
        logger.info("🔄 Démarrage du bot...")
        await load_cogs(self)
        logger.info("✅ Configuration terminée")

    async def on_ready(self):
        # Définir le statut une fois que le bot est prêt
        await self.change_presence(activity=discord.Game(name="Vive la mathysie ! 🔈 URaaa"))
        logger.info(f"🟢 Connecté en tant que {self.user}")
        logger.info(f"🔗 Connecté sur {len(self.guilds)} serveurs")

    async def on_command(self, ctx):
        logger.info(f"📜 Commande '{ctx.command}' utilisée par {ctx.author}")

    async def on_command_error(self, ctx, error):
        logger.error(f"❌ Erreur commande '{ctx.command}': {str(error)}")

    async def on_disconnect(self):
        logger.warning("🔴 Bot déconnecté")

if __name__ == "__main__":
    bot = MathysieBot()
    bot.run(Config.TOKEN)
