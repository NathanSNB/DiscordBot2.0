import discord
from discord.ext import commands
import json
import os
from dotenv import load_dotenv
import logging

# Configuration
load_dotenv()
AUTHORIZED_USERS_CC = list(map(int, os.getenv("AUTHORIZED_USERS_CC", "").split(","))) if os.getenv("AUTHORIZED_USERS_CC") else []
ECONOMY_FILE = 'data/economy.json'

logger = logging.getLogger("bot")

class Commandes_Economie(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(ECONOMY_FILE):
            self.save_economy({})
        logger.info("💰 Module Économie chargé")

    def load_economy(self):
        try:
            if os.path.exists(ECONOMY_FILE):
                with open(ECONOMY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except json.JSONDecodeError:
            logger.error("❌ Erreur de lecture du fichier economy.json")
            return {}

    def save_economy(self, data):
        with open(ECONOMY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    def is_authorized(self, ctx):
        return ctx.author.id in AUTHORIZED_USERS_CC

    def create_embed(self, title, description=None):
        return discord.Embed(
            title=title,
            description=description,
            color=discord.Color(0x2BA3B3)
        ).set_footer(text="Système de Crédits Sociaux")

    @commands.command(name="cc")
    async def check_coins(self, ctx):
        """Affiche les crédits de tous les utilisateurs"""
        if not self.is_authorized(ctx):
            return await ctx.send("❌ Accès refusé")
            
        economy = self.load_economy()
        if not economy:
            return await ctx.send("❌ Aucun utilisateur enregistré")

        embed = self.create_embed("💰 Crédits Sociaux")
        for user, credits in economy.items():
            emoji = "🔴" if credits < 0 else "🟢" if credits > 0 else "⚪"
            embed.add_field(
                name=f"{emoji} {user}",
                value=f"{credits} cc",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="add")
    async def add_coins(self, ctx, user: str, amount: int):
        """Ajoute des crédits à un utilisateur"""
        if not self.is_authorized(ctx):
            return await ctx.send("❌ Accès refusé")

        economy = self.load_economy()
        if user not in economy:
            return await ctx.send(f"❌ Utilisateur {user} inexistant")

        economy[user] += amount
        self.save_economy(economy)
        await ctx.send(f"✅ {amount} cc ajoutés à {user}. Nouveau solde: {economy[user]} cc")

    @commands.command(name="remove")
    async def remove_coins(self, ctx, user_name: str, amount: int):
        if not self.is_authorized(ctx):
            await ctx.send("❌ Accès refusé")
            return

        economy = self.load_economy()
        if user_name not in economy:
            await ctx.send(f"❌ Utilisateur {user_name} inexistant")
            return

        economy[user_name] -= amount
        self.save_economy(economy)
        embed = self.create_embed(
            "✅ Crédits retirés",
            f"{amount} cc retirés à {user_name}\nNouveau solde: {economy[user_name]} cc"
        )
        await ctx.send(embed=embed)

    @commands.command(name="create")
    async def create_user(self, ctx, user: str):
        """Crée un nouvel utilisateur"""
        if not self.is_authorized(ctx):
            return await ctx.send("❌ Accès refusé")

        economy = self.load_economy()
        if user in economy:
            return await ctx.send(f"❌ {user} existe déjà")

        economy[user] = 0
        self.save_economy(economy)
        await ctx.send(f"✅ {user} créé avec 0 cc")

    @commands.command(
        name="rename",
        help="Renomme un utilisateur",
        description="Change le nom d'un utilisateur existant",
        usage="!rename <ancien_nom> <nouveau_nom>"
    )
    async def rename_user(self, ctx, old_name: str, new_name: str):
        if not self.is_authorized(ctx):
            await ctx.send("❌ Accès refusé")
            return

        economy = self.load_economy()
        if old_name not in economy:
            await ctx.send(f"❌ Utilisateur {old_name} inexistant")
            return
        if new_name in economy:
            await ctx.send(f"❌ Utilisateur {new_name} déjà existant")
            return

        economy[new_name] = economy.pop(old_name)
        self.save_economy(economy)
        embed = self.create_embed(
            "✅ Utilisateur renommé",
            f"{old_name} renommé en {new_name}"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="authorize",
        help="Autorise un utilisateur",
        description="Ajoute un utilisateur à la liste des utilisateurs autorisés",
        usage="!authorize <user_id>"
    )
    @commands.has_permissions(administrator=True)
    async def authorize_user(self, ctx, user_id: int):
        if user_id in AUTHORIZED_USERS_CC:
            await ctx.send("❌ Utilisateur déjà autorisé")
            return

        AUTHORIZED_USERS_CC.append(user_id)
        os.environ["AUTHORIZED_USERS_CC"] = json.dumps(AUTHORIZED_USERS_CC)
        embed = self.create_embed(
            "✅ Utilisateur autorisé",
            f"ID {user_id} ajouté aux utilisateurs autorisés"
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Commandes_Economie(bot))
