import discord
from discord.ext import commands
import asyncio

class Commandes_Moderations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        description="Permet de supprimer entre 1 et 100 messages dans le salon",
        usage="!clear <nombre>"
    )
    @commands.has_permissions(administrator=True)
    async def clear(self, ctx, limit: int):
        if not 0 < limit <= 100:
            await ctx.send("❌ Le nombre de messages doit être entre 1 et 100.")
            return
        try:
            deleted = await ctx.channel.purge(limit=limit)
            embed = self.create_embed(
                "Messages supprimés",
                f"✅ {len(deleted)} messages ont été supprimés.",
                discord.Color.orange()
            )
            await ctx.send(embed=embed, delete_after=5)
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission de supprimer les messages.")

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

async def setup(bot):
    await bot.add_cog(Commandes_Moderations(bot))