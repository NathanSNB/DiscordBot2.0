import random
import asyncio
import discord
from discord.ext import commands

class CommandesGénérales(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def create_embed(self, title, description=None, color=discord.Color(0x2BA3B3)):
        """Crée un embed standard"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Bot Discord - Commandes Générales")
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Les arguments fournis sont invalides.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Il manque des arguments requis.")

    @commands.command(
        name="calc",
        help="Calculatrice simple",
        description="Effectue une opération mathématique entre deux nombres",
        usage="!calc <nombre1> <opérateur> <nombre2>"
    )
    async def calc(self, ctx, a: float, operation: str, b: float):
        try:
            if operation not in ['+', '-', '*', '/']:
                await ctx.send("❌ Opération invalide. Utilisez : +, -, *, /")
                return
                
            if operation == '/' and b == 0:
                await ctx.send("❌ Division par zéro impossible")
                return

            operations = {
                '+': lambda x, y: x + y,
                '-': lambda x, y: x - y,
                '*': lambda x, y: x * y,
                '/': lambda x, y: x / y
            }
            
            result = operations[operation](a, b)
            embed = self.create_embed(
                "🔢 Calculatrice",
                f"{a} {operation} {b} = {result:.2f}"
            )
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send("❌ Veuillez entrer des nombres valides")

    @commands.command(
        name="roll",
        help="Lance un dé",
        description="Génère un nombre aléatoire entre 1 et 10",
        usage="!roll"
    )
    async def roll(self, ctx):
        result = random.randint(1, 10)
        embed = self.create_embed(
            "🎲 Jet de dé",
            f"{ctx.author.mention} a obtenu : **{result}**"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="say",
        help="Répète un message",
        description="Répète un message dans un salon spécifique un certain nombre de fois",
        usage="!say <message> [#salon] [nombre]"
    )
    async def say(self, ctx, *, args):
        """Répète un message dans un salon"""
        try:
            # Extraction des arguments
            parts = args.split()
            
            # Vérification du salon
            if len(parts) >= 2 and parts[-2].startswith('<#') and parts[-2].endswith('>'):
                channel_id = int(parts[-2][2:-1])
                channel = ctx.guild.get_channel(channel_id)
                parts.pop(-2)
            else:
                channel = ctx.channel
            
            # Vérification du nombre
            try:
                count = int(parts[-1])
                if 0 < count <= 5:
                    parts.pop(-1)
                else:
                    count = 1
            except ValueError:
                count = 1
            
            # Message final
            message = ' '.join(parts)
            
            # Envoi des messages
            for _ in range(count):
                await channel.send(message)
                await asyncio.sleep(1)
            
            embed = self.create_embed(
                "📢 Message répété",
                f"Message envoyé {count} fois dans {channel.mention}"
            )
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas la permission d'envoyer des messages dans ce salon")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

async def setup(bot):
    await bot.add_cog(CommandesGénérales(bot))
