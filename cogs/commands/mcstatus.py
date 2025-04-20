import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
logger = logging.getLogger('bot')

class MCStatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.STATUS_CHANNEL_ID = int(os.getenv('STATUS_CHANNEL_ID', 0))
    
    @commands.command(
        name="mcstat",
        help="Affiche le statut du serveur Minecraft",
        description="Vérifie si le serveur est en ligne et affiche les joueurs connectés",
        usage="!mcstat"
    )
    async def mcstat(self, ctx):
        """Commande pour afficher le statut du serveur manuellement"""
        # Récupérer le cog MCStatusTracker
        tracker_cog = self.bot.get_cog('MCStatusTracker')
        if not tracker_cog:
            await ctx.send("❌ Le système de suivi n'est pas disponible.")
            return
        
        loading_msg = await ctx.send("🔄 Vérification du statut du serveur...")
        is_online, embed, _, _ = await tracker_cog.get_status_embed()
        await loading_msg.edit(content=None, embed=embed)
        logger.info(f"✅ Commande mcstat exécutée par {ctx.author}")
    
    @commands.command(
        name="mcrefresh",
        help="Actualise le message de statut du serveur",
        description="Force l'actualisation du message de statut",
        usage="!mcrefresh"
    )
    @commands.has_permissions(administrator=True)
    async def mcrefresh(self, ctx):
        """Force l'actualisation du message de statut"""
        # Récupérer le cog MCStatusTracker
        tracker_cog = self.bot.get_cog('MCStatusTracker')
        if not tracker_cog:
            await ctx.send("❌ Le système de suivi n'est pas disponible.")
            return
        
        await ctx.send("🔄 Actualisation du statut du serveur...")
        is_online, embed, player_count, current_player_list = await tracker_cog.get_status_embed()
        
        channel = self.bot.get_channel(self.STATUS_CHANNEL_ID)
        if channel:
            # Nettoyer d'abord les anciens messages du bot dans le canal
            await tracker_cog.clean_status_messages(channel)
            
            # Créer un nouveau message de statut
            tracker_cog.status_message = await channel.send(embed=embed)
            
            # Mettre à jour les valeurs précédentes
            tracker_cog.previous_server_status = is_online
            tracker_cog.previous_player_count = player_count
            tracker_cog.previous_player_list = current_player_list
            
            await ctx.send("✅ Message de statut actualisé!")
        else:
            await ctx.send(f"❌ Canal de statut non trouvé (ID: {self.STATUS_CHANNEL_ID})")
    
async def setup(bot):
    await bot.add_cog(MCStatusCommands(bot))