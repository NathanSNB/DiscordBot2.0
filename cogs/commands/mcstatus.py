import discord
from discord.ext import commands
from mcstatus import JavaServer
import socket
import asyncio
import os
from dotenv import load_dotenv
import logging

# Chargement des variables d'environnement
load_dotenv()
logger = logging.getLogger('bot')

class MCStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.SERVER_IP = os.getenv('MINECRAFT_SERVER_IP', 'localhost')
        self.PORT = int(os.getenv('MINECRAFT_SERVER_PORT', 25565))
        logger.info(f"🎮 Module MCStatus chargé (Serveur: {self.SERVER_IP}:{self.PORT})")

    @commands.command(
        name="mcstat",
        help="Affiche le statut du serveur Minecraft",
        description="Vérifie si le serveur est en ligne et affiche les joueurs connectés",
        usage="!mcstat"
    )
    async def mcstat(self, ctx):
        loading_msg = await ctx.send("🔄 Vérification du statut du serveur...")

        try:
            # Test de résolution DNS
            try:
                ip = socket.gethostbyname(self.SERVER_IP)
                logger.info(f"✅ DNS résolu : {self.SERVER_IP} -> {ip}")
            except socket.gaierror:
                raise ConnectionError(f"❌ Impossible de résoudre l'adresse {self.SERVER_IP}")

            # Test de connexion au serveur
            server = JavaServer(ip, self.PORT)
            status = server.status()

            # Création de l'embed avec les infos
            embed = discord.Embed(
                title="🟢 Serveur Minecraft en ligne",
                color=discord.Color.green()
            )
            embed.add_field(
                name="🌐 Adresse", 
                value=f"`{self.SERVER_IP}`", 
                inline=True
            )
            embed.add_field(
                name="📊 Joueurs", 
                value=f"{status.players.online}/{status.players.max}", 
                inline=True
            )
            embed.add_field(
                name="📶 Latence", 
                value=f"{round(status.latency, 2)}ms", 
                inline=True
            )

            # Ajout des joueurs connectés si présents
            if status.players.online > 0 and hasattr(status.players, 'sample'):
                players = "\n".join(f"• {p.name}" for p in status.players.sample)
                embed.add_field(
                    name="👥 Joueurs en ligne",
                    value=players,
                    inline=False
                )

            await loading_msg.edit(content=None, embed=embed)
            logger.info(f"✅ Statut vérifié pour {self.SERVER_IP}")

        except Exception as e:
            logger.error(f"❌ Erreur MCStatus: {str(e)}")
            embed = discord.Embed(
                title="🔴 Serveur Minecraft hors ligne",
                description=f"Erreur: {str(e)}",
                color=discord.Color.red()
            )
            await loading_msg.edit(content=None, embed=embed)

async def setup(bot):
    await bot.add_cog(MCStatus(bot))
