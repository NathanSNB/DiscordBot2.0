import discord
from discord.ext import commands
import logging
from ..commands.role import create_embed, RoleView

logger = logging.getLogger('bot')

class RoleEventsCog(commands.Cog, name="RoleEvents"):
    def __init__(self, bot):
        self.bot = bot
        self.default_channel_id = 1356659177870594130
        logger.info("✅ RoleEventsCog initialisé")

    async def simulate_refreshroles(self, channel):
        """Simule l'exécution de la commande !refreshroles"""
        try:
            # Récupérer le cog RoleManager
            role_cog = self.bot.get_cog("RoleManager")
            if role_cog:
                # Créer un contexte fictif
                message = await channel.history(limit=1).next()
                ctx = await self.bot.get_context(message)
                ctx.author.guild_permissions.administrator = True
                
                # Exécuter la commande refreshroles
                refresh_command = role_cog.refreshroles_command
                if refresh_command:
                    await refresh_command(ctx)
                    logger.info("✅ Commande refreshroles simulée avec succès")
                else:
                    logger.error("❌ Commande refreshroles non trouvée")
            else:
                logger.error("❌ RoleManager non trouvé")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la simulation de refreshroles: {str(e)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gère l'arrivée d'un nouveau membre"""
        try:
            # Récupérer le canal des rôles
            role_channel = self.bot.get_channel(self.default_channel_id)
            
            if role_channel:
                # Envoyer le MP de bienvenue
                welcome_embed = create_embed(
                    "Bienvenue sur le serveur !",
                    f"Bonjour {member.mention} ! 👋\n\n"
                    f"Pour personnaliser ton expérience sur le serveur, je t'invite à choisir tes rôles dans le salon {role_channel.mention}.\n\n"
                    "Tu pourras y sélectionner les rôles qui correspondent à tes intérêts !",
                    "success"
                )
                
                try:
                    await member.send(embed=welcome_embed)
                    logger.info(f"✅ MP de bienvenue envoyé à {member.name}")
                except discord.Forbidden:
                    logger.warning(f"❌ Impossible d'envoyer un MP à {member.name}")

                # Simuler la commande refreshroles
                await self.simulate_refreshroles(role_channel)
                logger.info(f"✅ Menu des rôles actualisé suite à l'arrivée de {member.name}")
                
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement du nouveau membre: {str(e)}")

async def setup(bot):
    await bot.add_cog(RoleEventsCog(bot))