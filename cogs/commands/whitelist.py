import discord
from discord.ext import commands
from utils.checks import require_permission

class WhitelistCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send("❌ Tu n'as pas la permission d'utiliser cette commande!")
            return
        raise error

    @commands.command(name="wl")
    @require_permission(5)  # Seul le niveau 5 peut gérer les permissions
    async def whitelist(self, ctx, user: discord.Member, level: int):
        """Ajoute un niveau de permission à un utilisateur"""
        if level not in [1, 2, 3, 5]:
            return await ctx.send("❌ Niveau invalide! Utilisez 1, 2, 3 ou 5")

        try:
            if self.bot.perm_manager.add_permission(user.id, level):
                embed = discord.Embed(
                    title="✅ Permission accordée",
                    description=f"{user.mention} a reçu le niveau {level}",
                    color=self.bot.config.COLOR_SUCCESS
                )
                embed.set_footer(text="MathysieBot™ • Système de permissions")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"ℹ️ {user.mention} a déjà le niveau {level}")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'ajout des permissions: {str(e)}")

    @commands.command(name="perms")
    async def check_perms(self, ctx, user: discord.Member = None):
        """Vérifie les permissions d'un utilisateur"""
        user = user or ctx.author
        try:
            perms = self.bot.perm_manager.get_user_permissions(user.id)
            perms_txt = ", ".join(map(str, sorted(perms))) if perms else "Aucune"
            
            embed = discord.Embed(
                title="🔍 Permissions",
                description=f"Permissions de {user.mention}:\n`{perms_txt}`",
                color=self.bot.config.COLOR_SUCCESS
            )
            embed.set_footer(text="MathysieBot™ • Permissions")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la vérification des permissions: {str(e)}")

async def setup(bot):
    await bot.add_cog(WhitelistCog(bot))