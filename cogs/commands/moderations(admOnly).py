import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta

from utils import logger

class Commandes_Moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}  # Format: {user_id: [(timestamp, reason, author_id)]}

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
        elif isinstance(error, commands.MemberNotFound):
            await ctx.send("❌ Membre non trouvé.")
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("❌ Salon non trouvé.")

    def create_embed(self, title, description=None, color=discord.Color(0x2BA3B3)):
        """Crée un embed standard"""
        return discord.Embed(title=title, description=description, color=color)

    @commands.command(
        name="kick",
        help="Exclure un membre du serveur",
        description="Permet d'exclure un membre du serveur avec une raison (optionnelle)",
        usage="!kick <@membre> [raison]"
    )
    @commands.has_permissions(administrator=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """Exclure un membre du serveur."""
        await member.kick(reason=reason)
        response_message = f"✅ {member.name} a été exclu(e)" + (f" pour : {reason}" if reason else ".")
        embed = self.create_embed("Exclusion", response_message, discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(
        name="ban",
        help="Bannir un membre du serveur",
        description="Permet de bannir définitivement un membre du serveur avec une raison optionnelle",
        usage="!ban <@membre> [raison]"
    )
    @commands.has_permissions(administrator=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        response_message = f"✅ {member.name} a été banni(e)" + (f" pour : {reason}" if reason else ".")
        embed = self.create_embed("Bannissement", response_message, discord.Color.red())
        await ctx.send(embed=embed)

    @commands.command(
        name="unban",
        help="Débannir un utilisateur",
        description="Permet de débannir un utilisateur via son ID Discord",
        usage="!unban <ID>"
    )
    @commands.has_permissions(administrator=True)
    async def unban(self, ctx, user_id: int):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user)
            embed = self.create_embed("Débannissement", f"✅ {user.name} a été débanni.", discord.Color.green())
            await ctx.send(embed=embed)
        except discord.NotFound:
            await ctx.send("❌ Utilisateur non trouvé.")
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de débannir.")

    @commands.command(
        name="clear",
        help="Supprimer des messages",
        description="Permet de supprimer un nombre spécifique de messages ou tous les messages du salon",
        usage="!clear <nombre|all>"
    )
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, amount):
        try:
            if amount.lower() == "all":
                deleted = await ctx.channel.purge(limit=None)
            else:
                limit = int(amount)
                if not 0 < limit <= 100:
                    await ctx.send("❌ Le nombre de messages doit être entre 1 et 100.")
                    return
                deleted = await ctx.channel.purge(limit=limit)
            
            embed = self.create_embed(
                "Messages supprimés",
                f"✅ {len(deleted)} messages ont été supprimés.",
                discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de supprimer les messages.")
        except ValueError:
            await ctx.send("❌ Veuillez spécifier un nombre valide ou 'all'.")

    @commands.command(
        name="move",
        help="Déplacer un membre",
        description="Permet de déplacer un membre d'un salon vocal vers un autre",
        usage="!move <@membre> <#salon>"
    )
    @commands.has_permissions(administrator=True)
    async def move(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        if not member.voice:
            await ctx.send(f"❌ {member.name} n'est pas dans un salon vocal.")
            return
            
        await member.move_to(channel)
        embed = self.create_embed(
            "Déplacement",
            f"✅ {member.name} a été déplacé vers {channel.name}",
            discord.Color.blue()
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="mute",
        help="Rendre muet un membre",
        description="Empêche un membre de parler dans tous les salons avec une durée optionnelle en minutes",
        usage="!mute <@membre> [durée_en_minutes]"
    )
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, duration: int = None):
        """Rend muet un membre avec option de durée en minutes"""
        try:
            # Création ou récupération du rôle Mute
            mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
            if mute_role is None:
                mute_role = await ctx.guild.create_role(name="Mute")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)

            # Application du rôle
            await member.add_roles(mute_role)
            
            embed = self.create_embed(
                "🔇 Membre rendu muet",
                f"{member.mention} a été rendu muet" + 
                (f" pour {duration} minutes." if duration else ".")
            )
            await ctx.send(embed=embed)

            # Retrait automatique du mute si durée spécifiée
            if duration:
                await asyncio.sleep(duration * 60)  # Convertir minutes en secondes
                if mute_role in member.roles:
                    await member.remove_roles(mute_role)
                    embed = self.create_embed(
                        "🔊 Membre réactivé",
                        f"{member.mention} n'est plus muet."
                    )
                    await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de gérer les rôles.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="unmute",
        help="Réactiver un membre muet",
        description="Permet à un membre de parler à nouveau dans tous les salons",
        usage="!unmute <@membre>"
    )
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx, member: discord.Member):
        """Retire le statut muet d'un membre"""
        try:
            mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
            if not mute_role:
                await ctx.send("❌ Le rôle Mute n'existe pas.")
                return

            if mute_role not in member.roles:
                await ctx.send(f"❌ {member.mention} n'est pas muet.")
                return

            await member.remove_roles(mute_role)
            embed = self.create_embed(
                "🔊 Membre réactivé",
                f"{member.mention} n'est plus muet."
            )
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de gérer les rôles.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="warn",
        help="Avertir un membre",
        description="Donne un avertissement à un membre. 3 avertissements en 20 minutes = mute 1h",
        usage="!warn <@membre> [raison]"
    )
    @commands.has_permissions(administrator=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        try:
            # Ajouter l'avertissement via le gestionnaire
            nb_warns = await self.bot.warns_manager.add_warning(member.id, reason, ctx.author.id)

            # Envoyer un MP à l'utilisateur averti
            try:
                warn_mp = self.create_embed(
                    "⚠️ Avertissement",
                    f"Vous avez reçu un avertissement sur {ctx.guild.name}\n" +
                    f"Raison: {reason or 'Aucune raison'}\n" +
                    f"Avertissements actifs: {nb_warns}/3\n" +
                    "Note: Les avertissements expirent après 20 minutes si aucun autre n'est reçu pendant 24h.",
                    discord.Color.yellow()
                )
                await member.send(embed=warn_mp)
            except discord.Forbidden:
                pass  # L'utilisateur a peut-être bloqué les MPs

            # Créer l'embed de réponse pour le salon
            response_message = f"⚠️ {member.name} a reçu un avertissement" + (f" pour : {reason}" if reason else ".")
            embed = self.create_embed(
                "Avertissement",
                f"{response_message}\nAvertissements actifs : {nb_warns}/3",
                discord.Color.yellow()
            )
            await ctx.send(embed=embed)

            # Vérifier pour le mute automatique
            if nb_warns >= 3:
                await self._auto_mute(ctx, member)

        except Exception as e:
            print(f"Erreur lors de l'ajout d'un avertissement: {str(e)}")
            await ctx.send("❌ Une erreur est survenue lors de l'ajout de l'avertissement.")
            raise

    async def _auto_mute(self, ctx, member: discord.Member):
        try:
            # Code existant pour le mute automatique...
            mute_role = discord.utils.get(ctx.guild.roles, name="Mute")
            if mute_role is None:
                mute_role = await ctx.guild.create_role(name="Mute")
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, speak=False)

            await member.add_roles(mute_role)
            embed = self.create_embed(
                "🔇 Mute Automatique",
                f"{member.mention} a été rendu muet pour 1 heure suite à 3 avertissements.",
                discord.Color.red()
            )
            await ctx.send(embed=embed)

            # Attendre 1 heure puis unmute
            await asyncio.sleep(3600)  # 3600 secondes = 1 heure
            if mute_role in member.roles:
                await member.remove_roles(mute_role)
                embed = self.create_embed(
                    "🔊 Membre réactivé",
                    f"{member.mention} n'est plus muet."
                )
                await ctx.send(embed=embed)

            # Réinitialiser les avertissements après le mute
            self.bot.warns_manager.warnings[member.id] = []
            self.bot.warns_manager._save_warns()

            # Ajouter l'événement de mute automatique
            self.bot.dispatch('warning_auto_mute', member)

        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de gérer les rôles.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

    @commands.command(
        name="warnings",
        help="Voir les avertissements d'un membre",
        description="Affiche la liste des avertissements actifs d'un membre",
        usage="!warnings <@membre>"
    )
    @commands.has_permissions(administrator=True)
    async def warnings(self, ctx, member: discord.Member):
        """Affiche les avertissements actifs d'un membre"""
        active_warnings = self.bot.warns_manager.get_warnings(member.id)
        
        if not active_warnings:
            await ctx.send(f"✅ {member.name} n'a aucun avertissement actif.")
            return

        embed = self.create_embed(
            f"Avertissements de {member.name}",
            f"Total: {len(active_warnings)}/3",
            discord.Color.yellow()
        )

        current_time = datetime.now()
        for i, (timestamp, reason, author_id) in enumerate(active_warnings, 1):
            author = ctx.guild.get_member(author_id) or "Utilisateur inconnu"
            time_ago = current_time - timestamp
            minutes_ago = int(time_ago.total_seconds() / 60)
            
            embed.add_field(
                name=f"Warn #{i} (il y a {minutes_ago} minutes)",
                value=f"Par: {author.mention if isinstance(author, discord.Member) else author}\nRaison: {reason or 'Aucune raison'}",
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(
        name="delwarn",
        help="Supprimer un avertissement",
        description="Permet de supprimer un avertissement d'un membre",
        usage="!delwarn <@membre> <numéro_warn>"
    )
    @commands.has_permissions(administrator=True)
    async def delwarn(self, ctx, member: discord.Member, warn_num: int):
        """Supprime un avertissement d'un membre."""
        try:
            # Le numéro d'avertissement est donné en commençant par 1, donc on soustrait 1
            warn_index = warn_num - 1
            
            # Utiliser l'ID de l'auteur de la commande
            success = await self.bot.warns_manager.remove_warning(member.id, warn_index, ctx.author.id)
            
            if success:
                embed = self.create_embed(
                    "Avertissement Supprimé",
                    f"✅ L'avertissement #{warn_num} de {member.mention} a été supprimé.",
                    discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Impossible de trouver l'avertissement #{warn_num} pour {member.name}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la suppression d'un avertissement: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la suppression de l'avertissement.")

async def setup(bot):
    await bot.add_cog(Commandes_Moderations(bot))