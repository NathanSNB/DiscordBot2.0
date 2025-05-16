import discord
from discord.ext import commands
import logging
import config
from utils.rules_manager import RulesManager
from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

class RoleEvents(commands.Cog, name="RoleEvents"):
    def __init__(self, bot):
        self.bot = bot
        logger.info("✅ Module RoleEvents chargé")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gère l'arrivée d'un nouveau membre"""
        try:
            # Attribution du rôle par défaut
            default_role = await RulesManager.setup_default_role(member.guild)
            if default_role:
                await member.add_roles(default_role)
                logger.info(f"✅ Rôle par défaut attribué à {member.name}")

                # Vérifier si on doit envoyer un message privé
                if await RulesManager.should_send_welcome_dm(member):
                    # Envoyer le message de bienvenue en MP
                    rules_channel = member.guild.get_channel(config.get('rules_channel_id'))
                    if rules_channel:
                        embed = EmbedManager.create_welcome_dm(member, rules_channel)
                        await member.send(embed=embed)
                        logger.info(f"✅ Message de bienvenue envoyé à {member.name}")
            else:
                logger.error(f"❌ Impossible d'attribuer le rôle par défaut à {member.name}")

        except Exception as e:
            logger.error(f"❌ Erreur lors de l'attribution du rôle: {str(e)}")

async def setup(bot):
    await bot.add_cog(RoleEvents(bot))