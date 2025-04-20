import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('bot')

# Chargement des variables d'environnement
load_dotenv()

class EventsCog(commands.Cog):
    def __init__(self, bot, config=None):
        self.bot = bot
        self.config = config
        logger.info("✅ EventsCog initialisé")
    
    def create_embed(self, title, description=None, type="info"):
        """Crée un embed standard avec le style du bot"""
        colors = {
            "info": discord.Color(0x2BA3B3),
            "success": discord.Color(0x57F287),
            "warning": discord.Color(0xFEE75C),
            "error": discord.Color(0xED4245)
        }
        color = colors.get(type, colors["info"])
        
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Bot Discord - Système de Rôles")
        return embed
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Exécuté quand le bot est prêt"""
        logger.info(f"🤖 Bot connecté en tant que {self.bot.user}")
        await self.bot.tree.sync()
        
        # Envoi du menu des rôles si la configuration existe
        if hasattr(self.config, 'send_role_menu'):
            await self.config.send_role_menu(self.bot)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self.create_embed(
                "Permission manquante", 
                "Vous n'avez pas la permission d'utiliser cette commande",
                "error"
            ))
            logger.warning(f"⚠️ Permission refusée pour {ctx.author} sur {ctx.command}")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self.create_embed(
                "Argument manquant", 
                "Il manque un argument requis pour cette commande",
                "error"
            ))
            logger.warning(f"⚠️ Argument manquant pour {ctx.author} sur {ctx.command}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=self.create_embed(
                "Argument invalide", 
                "Vérifiez les formats demandés (mention de rôle, etc.)",
                "error"
            ))
            logger.warning(f"⚠️ Argument invalide pour {ctx.author} sur {ctx.command}")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(embed=self.create_embed(
                "Salon introuvable", 
                "Le salon spécifié n'a pas été trouvé",
                "error"
            ))
        else:
            await ctx.send(embed=self.create_embed(
                "Erreur", 
                f"Une erreur est survenue: {str(error)}",
                "error"
            ))
            logger.error(f"❌ Erreur commande {ctx.command}: {str(error)}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Envoie un message de bienvenue en MP avec un lien vers le menu des rôles"""
        try:
            # On vérifie si la configuration existe
            if not hasattr(self.config, 'default_channel_id'):
                logger.warning(f"⚠️ Configuration default_channel_id manquante pour {member.name}")
                return
                
            channel = self.bot.get_channel(self.config.default_channel_id)
            if not channel:
                logger.warning(f"⚠️ Canal par défaut non trouvé pour message de bienvenue à {member.name}")
                return
                
            # Création de l'embed de bienvenue
            embed = discord.Embed(
                title="👋 Bienvenue sur le serveur !",
                description=f"Bonjour {member.mention}, bienvenue sur **{member.guild.name}** !\n\n"
                        f"N'oublie pas de choisir tes rôles dans le salon {channel.mention}.",
                color=discord.Color(0x2BA3B3)
            )
            embed.set_footer(text="Bot Discord - Système de Rôles")
            
            # Envoi du message privé
            await member.send(embed=embed)
            logger.info(f"👋 Message de bienvenue envoyé à {member.name}")
            
            # Envoi d'un log dans le canal de logs si configuré
            try:
                log_channel_id = int(os.getenv('LOG_CHANNEL_ID', '0'))
                if log_channel_id > 0:
                    log_channel = self.bot.get_channel(log_channel_id)
                    if log_channel:
                        log_embed = discord.Embed(
                            title="Nouveau membre",
                            description=f"👋 **{member}** a rejoint le serveur",
                            color=discord.Color(0x2BA3B3)
                        )
                        log_embed.set_footer(text="Système de Logs")
                        await log_channel.send(embed=log_embed)
            except Exception as e:
                logger.error(f"❌ Erreur envoi log pour nouveau membre: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ Erreur envoi message bienvenue à {member.name}: {str(e)}")

async def setup(bot):
    """Ajoute ce Cog au bot"""
    config = getattr(bot, 'config', None)
    await bot.add_cog(EventsCog(bot, config))