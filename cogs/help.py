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
                discord.SelectOption(
                    label="Accueil",
                    emoji="🏠",
                    value="main",
                    description="Page principale d'aide",
                ),
                discord.SelectOption(
                    label="Administration",
                    emoji="🛡️",
                    value="admin",
                    description="Commandes d'administration et modération",
                ),
                discord.SelectOption(
                    label="Utilitaires",
                    emoji="🧰",
                    value="util",
                    description="Outils utiles pour votre serveur",
                ),
                discord.SelectOption(
                    label="Divertissement",
                    emoji="🎮",
                    value="fun",
                    description="Commandes de divertissement",
                ),
                discord.SelectOption(
                    label="Systèmes",
                    emoji="⚙️",
                    value="systems",
                    description="Systèmes automatisés du bot",
                ),
                discord.SelectOption(
                    label="Aide",
                    emoji="❓",
                    value="help",
                    description="Commandes d'aide et support",
                ),
            ],
        )
        self.category_select.callback = self.select_callback
        self.add_item(self.category_select)

        # Bouton pour fermer le menu
        self.close_button = Button(
            label="Fermer", emoji="🚫", style=discord.ButtonStyle.red
        )
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
            embed = create_category_embed(
                self.bot,
                "Administration",
                "🛡️",
                [
                    "Commandes_Moderations",
                    "Commandes_Urgence",
                    "RulesCommands",
                    "WhitelistCog",
                ],
            )
        elif selected == "util":
            embed = create_category_embed(
                self.bot,
                "Utilitaires",
                "🧰",
                [
                    "CommandesGénérales",
                    "Commandes_Webs",
                    "MCStatusCommands",
                    "YouTubeDownloader",
                    "ProfilePictureCog",
                    "WikiCommands",
                ],
            )
        elif selected == "fun":
            embed = create_category_embed(
                self.bot, "Divertissement", "🎮", ["Commandes_musicales"]
            )
        elif selected == "systems":
            embed = create_category_embed(
                self.bot,
                "Systèmes",
                "⚙️",
                [
                    "StatsCommands",
                    "BedtimeReminder",
                    "Commandes_Economie",
                    "RoleManager",
                    "private_voice",
                    "tickets",
                ],
            )
        elif selected == "help":
            embed = create_category_embed(self.bot, "Aide", "❓", ["HelpCog"])

        await interaction.response.edit_message(embed=embed, view=self)

    async def close_callback(self, interaction):
        await interaction.response.defer()
        await interaction.delete_original_response()


def create_main_help_embed(bot):
    """Crée l'embed principal d'aide avec un style professionnel"""
    fields = [
        {
            "name": f"{EmbedManager.EMOJIS['shield']} Administration",
            "value": "• Commandes_Moderations\n• Commandes_Urgence\n• RulesCommands\n• WhitelistCog",
            "inline": True,
        },
        {
            "name": f"{EmbedManager.EMOJIS['tools']} Utilitaires",
            "value": "• CommandesGénérales\n• Commandes_Webs\n• MCStatusCommands\n• YouTubeDownloader\n• ProfilePictureCog\n• WikiCommands",
            "inline": True,
        },
        {
            "name": f"{EmbedManager.EMOJIS['game']} Divertissement",
            "value": "• Commandes_musicales",
            "inline": True,
        },
        {
            "name": f"{EmbedManager.EMOJIS['settings']} Systèmes",
            "value": "• StatsCommands\n• BedtimeReminder\n• Commandes_Economie\n• RoleManager\n• private_voice",
            "inline": True,
        },
        {
            "name": f"{EmbedManager.EMOJIS['info']} Information",
            "value": f"**Préfixe:** `{bot.config.PREFIX}`\n**Sélectionnez une catégorie** dans le menu déroulant pour plus de détails",
            "inline": False,
        },
    ]

    embed = EmbedManager.create_professional_embed(
        title="Menu d'aide principal",
        description="Bienvenue dans le système d'aide de MathysieBot™\n\nUtilisez le menu déroulant ci-dessous pour explorer les différentes catégories de commandes.",
        embed_type="help",
        fields=fields,
        thumbnail=bot.user.display_avatar.url,
    )

    return embed

    embed.add_field(
        name="━━━ ⚙️ Systèmes ━━━",
        value="• StatsCommands\n• BedtimeReminder\n• Commandes_Economie\n• RoleManager\n• private_voice\n• tickets",
        inline=False,
    )

    embed.add_field(name="━━━ ❓ Aide ━━━", value="• HelpCog", inline=False)

    embed.set_thumbnail(url=bot.user.display_avatar.url)
    return embed


def create_category_embed(bot, category, emoji, modules_list):
    """Crée un embed professionnel pour une catégorie de commandes"""
    fields = []

    for module in modules_list:
        commands_list = []
        for command in bot.commands:
            cog_name = command.cog_name if command.cog else "Sans catégorie"
            if cog_name == module:
                usage = f"{bot.config.PREFIX}{command.name}"
                if command.usage:
                    usage += f" {command.usage}"
                commands_list.append(
                    f"• `{usage}`: {command.help or 'Aucune description'}"
                )

        # Si aucune commande n'est trouvée, afficher un message par défaut
        description = (
            "\n".join(commands_list[:5])  # Limiter à 5 commandes par module
            if commands_list
            else "*Module sans commandes ou non chargé*"
        )

        if commands_list and len(commands_list) > 5:
            description += f"\n*... et {len(commands_list) - 5} autres commandes*"

        fields.append(
            {
                "name": f"{EmbedManager.EMOJIS['folder']} {module}",
                "value": description,
                "inline": False,
            }
        )

    embed = EmbedManager.create_professional_embed(
        title=f"Commandes {category}",
        description=f"Voici les modules disponibles dans la catégorie {category}.\n"
        f"Utilisez `{bot.config.PREFIX}help [commande]` pour plus d'informations sur une commande spécifique.",
        embed_type="help",
        fields=fields,
        thumbnail=bot.user.display_avatar.url,
    )

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
                usage = f"{self.bot.config.PREFIX}{cmd.name}"
                if cmd.usage:
                    usage += f" {cmd.usage}"

                fields = [
                    {
                        "name": f"{EmbedManager.EMOJIS['page']} Utilisation",
                        "value": f"`{usage}`",
                        "inline": False,
                    },
                    {
                        "name": f"{EmbedManager.EMOJIS['info']} Description",
                        "value": cmd.help or "Aucune description disponible",
                        "inline": False,
                    },
                ]

                if cmd.aliases:
                    aliases = ", ".join([f"`{alias}`" for alias in cmd.aliases])
                    fields.append(
                        {
                            "name": f"{EmbedManager.EMOJIS['bookmark']} Alias",
                            "value": aliases,
                            "inline": False,
                        }
                    )

                embed = EmbedManager.create_command_embed(
                    command_name=cmd.name,
                    description=cmd.help or "Aucune description disponible",
                    usage=usage,
                    examples=[f"{usage}"] if cmd.usage else None,
                )

                await ctx.send(embed=embed)
            else:
                error_embed = EmbedManager.create_error_embed(
                    title="Commande introuvable",
                    description=f"La commande `{command}` n'existe pas.",
                )
                await ctx.send(embed=error_embed)
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
