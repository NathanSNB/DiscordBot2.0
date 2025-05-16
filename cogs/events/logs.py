import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from utils.error import ErrorHandler

# Configuration du logging
logging.basicConfig(level=logging.INFO)
load_dotenv()

# Récupération du salon de logs depuis les variables d'environnement
LOG_CHANNEL_ID = int(os.getenv('LOG_CHANNEL_ID', '0'))

class Commandes_Logs(commands.Cog):
    """Cog pour surveiller les logs du serveur"""

    def __init__(self, bot):
        self.bot = bot
        if LOG_CHANNEL_ID == 0:
            logging.error("LOG_CHANNEL_ID non configuré dans le .env")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        await ErrorHandler.handle_command_error(ctx, error)

    def create_embed(self, title, description=None, color=discord.Color(0x2BA3B3)):
        """Crée un embed standard pour les logs"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Système de Logs")
        return embed

    async def send_log_message(self, message, title="Log"):
        """Envoie un message formaté dans le salon de logs"""
        try:
            channel = self.bot.get_channel(LOG_CHANNEL_ID)
            if channel:
                embed = self.create_embed(title, message)
                await channel.send(embed=embed)
            else:
                logging.error(f"Salon de log introuvable (ID: {LOG_CHANNEL_ID})")
        except Exception as e:
            logging.error(f"Erreur lors de l'envoi du log : {e}")

    async def get_admin_action(self, member, action_type):
        """Récupère l'admin ayant effectué une action spécifique"""
        guild = member.guild
        async for entry in guild.audit_logs(limit=1, action=action_type):
            return entry.user if entry else None
        return None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Surveille les changements de salons vocaux"""
        log_message = ""

        if before.channel is None and after.channel is not None:
            log_message = f"🎧 **{member}** a rejoint **{after.channel.name}**"
            title = "Rejoint un salon vocal"
        elif before.channel is not None and after.channel is None:
            log_message = f"🚪 **{member}** a quitté **{before.channel.name}**"
            title = "Quitte un salon vocal"
        elif before.self_mute != after.self_mute:
            log_message = f"🔇 **{member}** {'s’est mis en mute' if after.self_mute else 's’est enlevé de mute'} dans **{after.channel.name}**"
            title = "Mute/Unmute dans un salon vocal"
        elif before.mute != after.mute:
            admin = await self.get_admin_action(member, discord.AuditLogAction.member_update)
            log_message = f"🚫 **{member}** a été {'mute' if after.mute else 'unmute'} dans **{after.channel.name}** par {admin}"
            title = "Mute/Unmute par un administrateur"
        elif before.channel != after.channel:
            log_message = f"🔄 **{member}** a été déplacé de **{before.channel.name}** vers **{after.channel.name}**"
            title = "Déplacement dans un salon vocal"

        if log_message:
            await self.send_log_message(log_message, title)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Surveille les départs des membres et détecte les kicks"""
        admin = await self.get_admin_action(member, discord.AuditLogAction.kick)
        log_message = f"👢 **{member}** a été kické par **{admin}**" if admin else f"👢 **{member}** a été kické"
        await self.send_log_message(log_message, "Membre Kické")

    @commands.Cog.listener()
    async def on_ready(self):
        """Affiche un message quand le bot est prêt"""
        logging.info(f"{self.bot.user} est en ligne !")
        await self.bot.tree.sync()

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Surveille la création d'un salon"""
        log_message = f"🆕 Un nouveau salon a été créé : **{channel.name}**"
        await self.send_log_message(log_message, "Création de salon")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Surveille la suppression d'un salon"""
        log_message = f"🗑 Le salon **{channel.name}** a été supprimé"
        await self.send_log_message(log_message, "Suppression de salon")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """Surveille les modifications de salons"""
        if before.name != after.name:
            log_message = f"🔧 Le salon **{before.name}** a été renommé en **{after.name}**"
            await self.send_log_message(log_message, "Modification de salon")

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """Surveille les changements de paramètres du serveur"""
        if before.name != after.name:
            log_message = f"📝 Le nom du serveur a été modifié de **{before.name}** à **{after.name}**"
            await self.send_log_message(log_message, "Modification du serveur")
        if before.icon != after.icon:
            log_message = "🔄 L'icône du serveur a été modifiée"
            await self.send_log_message(log_message, "Modification de l'icône")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Surveille l'ajout de réactions"""
        log_message = f"👍 **{user}** a réagi au message avec **{reaction.emoji}**"
        await self.send_log_message(log_message, "Réaction ajoutée")

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Surveille la suppression de réactions"""
        log_message = f"👎 **{user}** a retiré sa réaction **{reaction.emoji}**"
        await self.send_log_message(log_message, "Réaction retirée")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Surveille les messages supprimés"""
        log_message = f"🗑 **{message.author}** a supprimé un message : {message.content}"
        await self.send_log_message(log_message, "Message supprimé")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        """Surveille les modifications de messages"""
        if before.content != after.content:
            log_message = f"✏ **{before.author}** a modifié un message : \nAvant : {before.content} \nAprès : {after.content}"
            await self.send_log_message(log_message, "Message modifié")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Surveille les bannissements de membres"""
        admin = await self.get_admin_action(user, discord.AuditLogAction.ban)
        log_message = f"⛔ **{user}** a été banni par **{admin}**"
        await self.send_log_message(log_message, "Membre Banni")

    @commands.Cog.listener()
    async def on_warning_add(self, member: discord.Member, reason: str, admin: discord.Member, warn_count: int):
        """Surveille l'ajout d'avertissements"""
        log_message = (
            f"⚠️ **{member}** a reçu un avertissement\n"
            f"**Par:** {admin.mention}\n"
            f"**Raison:** {reason or 'Aucune raison'}\n"
            f"**Total:** {warn_count}/3"
        )
        await self.send_log_message(log_message, "Avertissement Ajouté")

    @commands.Cog.listener()
    async def on_warning_remove(self, member: discord.Member, admin: discord.Member, warn_num: int):
        """Surveille la suppression d'avertissements"""
        log_message = (
            f"🗑️ **{member}** a eu son avertissement #{warn_num} supprimé\n"
            f"**Par:** {admin.mention}"
        )
        await self.send_log_message(log_message, "Avertissement Supprimé")

    @commands.Cog.listener()
    async def on_warning_expire(self, member: discord.Member):
        """Surveille l'expiration des avertissements"""
        log_message = f"⌛ Les avertissements de **{member}** ont expiré"
        await self.send_log_message(log_message, "Avertissements Expirés")

    @commands.Cog.listener()
    async def on_warning_auto_mute(self, member: discord.Member):
        """Surveille les mutes automatiques après 3 avertissements"""
        log_message = (
            f"🔇 **{member}** a été mute automatiquement\n"
            f"**Raison:** 3 avertissements en moins de 20 minutes"
        )
        await self.send_log_message(log_message, "Mute Automatique")

async def setup(bot):
    """Ajoute ce Cog au bot"""
    await bot.add_cog(Commandes_Logs(bot))
