import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from dotenv import load_dotenv
import logging
from utils.embed_manager import EmbedManager
from utils.error import ErrorHandler

# Charger les variables d'environnement
load_dotenv()
AUTHORIZED_USERS_HERESIE = [int(user_id) for user_id in os.getenv("AUTHORIZED_USERS_HERESIE", "").split(",") if user_id.strip().isdigit()]

# Initialisation du logger
logging.basicConfig(level=logging.INFO)

class Commandes_Urgence(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.saved_roles = {}  # Sauvegarde des rôles des membres
        self.locked_channels = []  # Sauvegarde des salons verrouillés
        self.community_announcement_channel_id = 1290378403060383776  # ID du salon d'annonces

    # Gestion des erreurs globale
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        await ErrorHandler.handle_command_error(ctx, error)

    def create_embed(self, title, description=None, color=None):
        """Crée un embed standard pour les réponses"""
        if color is None:
            color = EmbedManager.get_default_color()
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Système d'Urgence - Hérésie")
        return embed

    def is_authorized(self, ctx):
        """Vérifie si l'utilisateur est autorisé"""
        return ctx.author.id in AUTHORIZED_USERS_HERESIE

    async def get_or_create_heresie_role(self, guild):
        """Vérifie l'existence du rôle 'Hérésie' et le crée si nécessaire"""
        role_name = "Hérésie"

        # Vérifier si le rôle existe déjà
        heresie_role = discord.utils.get(guild.roles, name=role_name)
        if heresie_role:
            logging.info(f"Le rôle '{role_name}' existe déjà.")
            return heresie_role

        # Création du rôle si inexistant
        try:
            heresie_role = await guild.create_role(
                name=role_name,
                permissions=discord.Permissions(send_messages=False, speak=False),  # Désactive parole & messages
                color=discord.Color.dark_red()
            )
            logging.info(f"Rôle '{role_name}' créé avec succès.")
            return heresie_role
        except discord.Forbidden:
            logging.error("Permissions insuffisantes pour créer le rôle 'Hérésie'.")
        except Exception as e:
            logging.error(f"Erreur lors de la création du rôle 'Hérésie' : {e}")

        return None

    @commands.command(
        name="heresie",
        help="Lance une hérésie",
        description="Verrouille tous les salons et modifie les rôles des membres non autorisés",
        usage="!heresie"
    )
    @commands.has_permissions(administrator=True)
    async def heresie(self, ctx):
        if not self.is_authorized(ctx):
            await ctx.send("❌ Accès refusé")
            return

        guild = ctx.guild
        heresie_role = await self.get_or_create_heresie_role(guild)

        if not heresie_role:
            await ctx.send("❌ Impossible de créer le rôle Hérésie")
            return

        try:
            # Sauvegarde et modification des rôles
            for member in guild.members:
                if not member.bot and member.id not in AUTHORIZED_USERS_HERESIE:  # Ne modifie pas les rôles des utilisateurs autorisés
                    self.saved_roles[member.id] = [role.id for role in member.roles if role != guild.default_role]
                    await member.edit(roles=[heresie_role])
                    logging.info(f"Rôles retirés pour {member.name}")
                elif member.id in AUTHORIZED_USERS_HERESIE:
                    logging.info(f"Rôles préservés pour {member.name} (utilisateur autorisé)")

            # Verrouillage des salons
            self.locked_channels.clear()
            for channel in guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                    self.locked_channels.append((channel, channel.overwrites))
                    overwrites = {
                        guild.default_role: discord.PermissionOverwrite(
                            view_channel=False,
                            send_messages=False,
                            speak=False
                        ),
                        # Permet aux utilisateurs autorisés de toujours voir et utiliser les salons
                        heresie_role: discord.PermissionOverwrite(
                            view_channel=False,
                            send_messages=False,
                            speak=False
                        )
                    }
                    # Ajoute des permissions spéciales pour les utilisateurs autorisés
                    for user_id in AUTHORIZED_USERS_HERESIE:
                        member = guild.get_member(user_id)
                        if member:
                            overwrites[member] = discord.PermissionOverwrite(
                                view_channel=True,
                                send_messages=True,
                                speak=True
                            )
                    await channel.edit(overwrites=overwrites)

            embed = self.create_embed(
                "🚨 Hérésie activée", 
                "Tous les salons sont verrouillés.\nLes administrateurs autorisés conservent leurs accès."
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur hérésie : {e}")
            await ctx.send(f"❌ Une erreur est survenue : {e}")

    @commands.command(
        name="orthodoxie",
        help="Restaure l'ordre",
        description="Déverrouille les salons et restaure les rôles d'origine",
        usage="!orthodoxie"
    )
    @commands.has_permissions(administrator=True)
    async def orthodoxie(self, ctx):
        if not self.is_authorized(ctx):
            await ctx.send("❌ Accès refusé")
            return

        guild = ctx.guild
        try:
            # Restauration des rôles
            for member_id, roles_ids in self.saved_roles.items():
                member = guild.get_member(member_id)
                if member:
                    roles = [guild.get_role(role_id) for role_id in roles_ids if guild.get_role(role_id)]
                    await member.edit(roles=roles)
            self.saved_roles.clear()

            # Restauration des salons
            for channel, overwrites in self.locked_channels:
                await channel.edit(overwrites=overwrites)
            self.locked_channels.clear()

            embed = self.create_embed("✨ Orthodoxie restaurée", "L'ordre est rétabli.")
            await ctx.send(embed=embed)

        except Exception as e:
            logging.error(f"Erreur orthodoxie : {e}")
            await ctx.send(f"❌ Une erreur est survenue : {e}")

async def setup(bot):
    await bot.add_cog(Commandes_Urgence(bot))
