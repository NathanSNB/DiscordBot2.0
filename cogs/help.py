import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View, Select
import typing
import datetime

from utils.embed_manager import EmbedManager

class HelpView(View):
    def __init__(self, bot, author, timeout=60):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.author = author
        self.current_page = "main"
        
        # Création du menu déroulant pour les catégories
        self.category_select = Select(
            placeholder="Sélectionnez une catégorie...",
            options=[
                discord.SelectOption(label="Accueil", emoji="🏠", value="main", description="Page principale d'aide"),
                discord.SelectOption(label="Administration", emoji="🛡️", value="admin", description="Commandes d'administration et modération"),
                discord.SelectOption(label="Utilitaires", emoji="🧰", value="util", description="Outils utiles pour votre serveur"),
                discord.SelectOption(label="Divertissement", emoji="🎮", value="fun", description="Commandes de divertissement"),
                discord.SelectOption(label="Systèmes", emoji="⚙️", value="systems", description="Systèmes automatisés du bot"),
                discord.SelectOption(label="Aide", emoji="❓", value="help", description="Commandes d'aide et support")
            ]
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)
        
        # Bouton pour fermer le menu
        self.close_button = Button(label="Fermer", emoji="🚫", style=discord.ButtonStyle.red)
        self.close_button.callback = self.close_callback
        self.add_item(self.close_button)
        
    async def interaction_check(self, interaction):
        # S'assurer que seul l'utilisateur qui a demandé l'aide peut interagir
        return interaction.user.id == self.author.id
    
    async def select_callback(self, interaction):
        selected = self.category_select.values[0]
        self.current_page = selected
        
        if selected == "main":
            embed = create_main_help_embed(self.bot)
        elif selected == "admin":
            embed = create_category_embed(self.bot, "Administration", "🛡️", [
                "Commandes_Moderations", "Commandes_Urgence", "RulesCommands", "WhitelistCog"
            ])
        elif selected == "util":
            embed = create_category_embed(self.bot, "Utilitaires", "🧰", [
                "CommandesGénérales", "Commandes_Webs", "MCStatusCommands", 
                "YouTubeDownloader", "ProfilePictureCog", "WikiCommands"
            ])
        elif selected == "fun":
            embed = create_category_embed(self.bot, "Divertissement", "🎮", [
                "Commandes_musicales"
            ])
        elif selected == "systems":
            embed = create_category_embed(self.bot, "Systèmes", "⚙️", [
                "StatsCommands", "BedtimeReminder", "Commandes_Economie", 
                "RoleManager", "private_voice", "tickets"
            ])
        elif selected == "help":
            embed = create_category_embed(self.bot, "Aide", "❓", [
                "HelpCog"
            ])
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    async def close_callback(self, interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()

def create_main_help_embed(bot):
    embed = EmbedManager.create_embed(
        title="📚 Menu d'aide de MathysieBot™",
        description=f"Bienvenue dans le système d'aide de MathysieBot™\n\n"
                f"Utilisez le menu déroulant ci-dessous pour explorer les différentes catégories de commandes.\n\n"
                f"**Préfixe des commandes:** `{bot.config.PREFIX}`",
        timestamp=datetime.datetime.now()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    # Ajout des catégories principales avec séparateurs
    embed.add_field(name="━━━ 🛡️ Administration ━━━", 
                    value="• Commandes_Moderations\n• Commandes_Urgence\n• RulesCommands\n• WhitelistCog", 
                    inline=False)
    
    embed.add_field(name="━━━ 🧰 Utilitaires ━━━", 
                    value="• CommandesGénérales\n• Commandes_Webs\n• MCStatusCommands\n• YouTubeDownloader\n• ProfilePictureCog\n• WikiCommands", 
                    inline=False)
    
    embed.add_field(name="━━━ 🎮 Divertissement ━━━", 
                    value="• Commandes_musicales", 
                    inline=False)
    
    embed.add_field(name="━━━ ⚙️ Systèmes ━━━", 
                    value="• StatsCommands\n• BedtimeReminder\n• Commandes_Economie\n• RoleManager\n• private_voice\n• tickets", 
                    inline=False)
    
    embed.add_field(name="━━━ ❓ Aide ━━━", 
                    value="• HelpCog", 
                    inline=False)
    
    embed.set_footer(text=f"Développé avec ❤️ par l'équipe Mathysie • {bot.config.PREFIX}help [commande] pour plus de détails")
    return embed

def create_category_embed(bot, category, emoji, modules_list):
    embed = discord.Embed(
        title=f"{emoji} Commandes {category}",
        description=f"Voici les modules disponibles dans la catégorie {category}.\n"
                    f"Utilisez `{bot.config.PREFIX}help [commande]` pour plus d'informations sur une commande spécifique.",
        color=0x7289DA,
        timestamp=datetime.datetime.now()
    )
    
    embed.add_field(name=f"━━━ Modules {emoji} ━━━", value="\u200b", inline=False)
    
    for module in modules_list:
        commands_list = []
        for command in bot.commands:
            cog_name = command.cog_name if command.cog else "Sans catégorie"
            if cog_name == module:
                usage = f"{bot.config.PREFIX}{command.name}"
                if command.usage:
                    usage += f" {command.usage}"
                commands_list.append(f"• `{usage}`: {command.help or 'Aucune description'}")
        
        # Si aucune commande n'est trouvée, afficher un message par défaut
        description = "\n".join(commands_list) if commands_list else "*Module sans commandes ou non chargé*"
        embed.add_field(name=f"📌 {module}", value=description, inline=False)
            
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text="Utilisez le menu déroulant pour naviguer entre les catégories")
    return embed

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="help", aliases=["aide", "h"])
    async def help_command(self, ctx, command: typing.Optional[str] = None):
        """Affiche ce message d'aide"""
        
        if command:
            # Afficher l'aide pour une commande spécifique
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(
                    title=f"📖 Aide pour {cmd.name}",
                    color=0x7289DA
                )
                
                usage = f"{self.bot.config.PREFIX}{cmd.name}"
                if cmd.usage:
                    usage += f" {cmd.usage}"
                
                embed.add_field(name="Utilisation", value=f"`{usage}`", inline=False)
                
                if cmd.help:
                    embed.add_field(name="Description", value=cmd.help, inline=False)
                else:
                    embed.add_field(name="Description", value="Aucune description disponible", inline=False)
                
                if cmd.aliases:
                    aliases = ", ".join([f"`{alias}`" for alias in cmd.aliases])
                    embed.add_field(name="Alias", value=aliases, inline=False)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ La commande `{command}` n'existe pas.")
        else:
            # Afficher le menu d'aide principal
            embed = create_main_help_embed(self.bot)
            view = HelpView(self.bot, ctx.author)
            await ctx.send(embed=embed, view=view)
    
    @app_commands.command(name="help", description="Affiche l'aide du bot")
    async def help_slash(self, interaction: discord.Interaction):
        """Affiche le menu d'aide (version slash command)"""
        embed = create_main_help_embed(self.bot)
        view = HelpView(self.bot, interaction.user)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))