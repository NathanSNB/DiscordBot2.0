import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
import asyncio
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class RoleButton(Button):
    def __init__(self, emoji, role_id):
        super().__init__(style=discord.ButtonStyle.primary, emoji=emoji)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(self.role_id)
        member = interaction.user

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"❌ {role.name} retiré.", ephemeral=True)
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"✅ {role.name} ajouté.", ephemeral=True)

class RoleView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.load_roles()
        for emoji, data in self.roles.items():
            self.add_item(RoleButton(emoji=emoji, role_id=data["id"]))

    def load_roles(self):
        """Charge la configuration des rôles depuis le fichier JSON"""
        if os.path.exists('data/roles_config.json'):
            with open('data/roles_config.json', 'r', encoding='utf-8') as f:
                self.roles = json.load(f)
        else:
            self.roles = {}

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("🛠️ Module Admin chargé")
        os.makedirs('data', exist_ok=True)
        self.load_roles()

    def load_roles(self):
        """Charge la configuration des rôles"""
        try:
            if os.path.exists('data/roles_config.json'):
                with open('data/roles_config.json', 'r', encoding='utf-8') as f:
                    self.roles = json.load(f)
            else:
                self.roles = {}
            logger.info("👥 Configuration des rôles chargée")
        except Exception as e:
            logger.error(f"❌ Erreur chargement rôles: {str(e)}")
            self.roles = {}

    def save_roles(self):
        """Sauvegarde la configuration des rôles"""
        with open('data/roles_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.roles, f, indent=4)

    def create_embed(self, title, description=None):
        """Crée un embed standard"""
        embed = discord.Embed(title=title, description=description, color=discord.Color(0x2BA3B3))
        embed.set_footer(text="Bot Discord - Système de Rôles")
        return embed

    @commands.command(
        name="roles",
        help="Affiche le menu des rôles",
        description="Crée un message avec des boutons pour choisir les rôles",
        usage="!roles"
    )
    @commands.has_permissions(administrator=True)
    async def roles(self, ctx):
        """Envoie le menu de sélection des rôles"""
        logger.info(f"⚙️ Menu rôles demandé par {ctx.author}")
        try:
            if not self.roles:
                await ctx.send("❌ Aucun rôle configuré. Utilisez !configrole pour en ajouter.")
                return

            embed = self.create_embed(
                "🎭 Choisissez vos rôles !",
                "Cliquez sur les boutons pour obtenir ou retirer les rôles."
            )

            for emoji, data in self.roles.items():
                embed.add_field(
                    name=f"{emoji} {data['name']}", 
                    value=data['description'] or "Pas de description",
                    inline=False
                )

            view = RoleView()
            await ctx.send(embed=embed, view=view)
            logger.info("✅ Menu rôles créé")
        except Exception as e:
            logger.error(f"❌ Erreur menu rôles: {str(e)}")

    @commands.command(
        name="configrole",
        help="Configure un rôle",
        description="Ajoute ou modifie un rôle dans le menu de sélection",
        usage="!configrole <emoji> <@role> [description]"
    )
    @commands.has_permissions(administrator=True)
    async def configrole(self, ctx, emoji: str, role: discord.Role, *, description: str = ""):
        """Configure un nouveau rôle pour le menu"""
        self.roles[emoji] = {
            "id": role.id,
            "name": role.name,
            "description": description
        }
        self.save_roles()
        
        embed = self.create_embed(
            "✅ Rôle configuré",
            f"Le rôle {role.name} a été configuré avec l'emoji {emoji}"
        )
        await ctx.send(embed=embed)

    @commands.command(
        name="delrole",
        help="Supprime un rôle",
        description="Retire un rôle du menu de sélection",
        usage="!delrole <emoji>"
    )
    @commands.has_permissions(administrator=True)
    async def delrole(self, ctx, emoji: str):
        """Supprime un rôle de la configuration"""
        if emoji in self.roles:
            role_name = self.roles[emoji]["name"]
            del self.roles[emoji]
            self.save_roles()
            await ctx.send(embed=self.create_embed("✅ Rôle supprimé", f"Le rôle {role_name} a été retiré du menu"))
        else:
            await ctx.send("❌ Emoji non trouvé dans la configuration")

    @commands.command(
        name="listroles",
        help="Liste les rôles",
        description="Affiche la liste des rôles configurés",
        usage="!listroles"
    )
    @commands.has_permissions(administrator=True)
    async def listroles(self, ctx):
        """Affiche la liste des rôles configurés"""
        if not self.roles:
            await ctx.send("❌ Aucun rôle configuré")
            return

        embed = self.create_embed("📋 Rôles configurés")
        for emoji, data in self.roles.items():
            embed.add_field(
                name=f"{emoji} {data['name']}", 
                value=data['description'] or "Pas de description",
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas la permission d'utiliser cette commande")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Il manque un argument requis")
        else:
            await ctx.send(f"❌ Une erreur est survenue: {str(error)}")

async def setup(bot):
    await bot.add_cog(Admin(bot))
