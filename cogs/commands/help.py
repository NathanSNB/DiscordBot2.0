import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View, Select
import datetime
import typing
from utils.embed_manager import EmbedManager  # Importer l'EmbedManager

class HelpCategorySelect(discord.ui.Select):
    def __init__(self, cog_embeds: dict):
        self.cog_embeds = cog_embeds
        
        # Dictionnaire de correspondance entre les noms de cogs et des noms plus descriptifs avec émojis
        self.category_display_names = {
            # Commandes d'administration et modération
            "Commandes_Moderations": "🛡️ Modération",
            "Commandes_Urgence": "🚨 Urgence & Sécurité",
            "RulesCommands": "📜 Règlement",
            "WhitelistCog": "🔑 Permissions",
            
            # Utilitaires
            "Commandes_Webs": "🌐 Outils Web",
            "MCStatusCommands": "🎮 Status Minecraft",
            "YouTubeDownloader": "📥 YouTube",
            "ProfilePictureCog": "🖼️ Images de profil",
            "WikiCommands": "📚 Recherche Wiki",
            "CommandesGénérales": "🧰 Outils généraux",
            
            # Divertissement et médias
            "Commandes_musicales": "🎵 Musique",
            
            # Systèmes
            "RoleManager": "🏷️ Gestion des rôles",
            "StatsCommands": "📊 Statistiques",
            "tickets": "🎫 Système de tickets",
            "private_voice": "🔊 Salons vocaux privés",
            "BedtimeReminder": "⏰ Rappels",
            "Commandes_Economie": "💰 Économie",
            "ColorCommands": "🎨 Apparence du bot",
            "compteur_membres": "👥 Compteur de Membres",            
            
            # Aide
            "HelpCog": "❓ Aide & Support",
        }
        
        # Organiser les catégories par groupes pour une meilleure lisibilité
        category_groups = {
            "Administration": ["Commandes_Moderations", "Commandes_Urgence", "RulesCommands", "WhitelistCog"],
            "Utilitaires": ["CommandesGénérales", "Commandes_Webs", "MCStatusCommands", "YouTubeDownloader", "ProfilePictureCog", "WikiCommands"],
            "Divertissement": ["Commandes_musicales"],
            "Systèmes": ["StatsCommands", "Commandes_Economie", "RoleManager", "private_voice", "tickets", "BedtimeReminder", "ColorCommands", "compteur_membres"],  # Ajout du compteur_membres
            "Assistance": ["HelpCog"]
        }
        
        options = []
        # Ajouter l'option "Vue d'ensemble" (Accueil)
        options.append(
            discord.SelectOption(
                label="📋 Vue d'ensemble",
                description="Afficher toutes les catégories disponibles",
                value="overview"
            )
        )
        
        # Ajouter les options par groupe
        for group_name, cog_names in category_groups.items():
            for cog_name in cog_names:
                if cog_name in self.cog_embeds:
                    display_name = self.category_display_names.get(cog_name, f"📁 {cog_name}")
                    options.append(
                        discord.SelectOption(
                            label=display_name,
                            description=f"Commandes {group_name.lower()}",
                            value=cog_name
                        )
                    )
        
        super().__init__(placeholder="📋 Choisir une catégorie...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Récupérer l'embed correspondant à la catégorie sélectionnée
        selected_value = self.values[0]
        
        if selected_value == "overview":
            # Créer une vue d'ensemble
            await self.show_overview(interaction)
            return
            
        # Récupérer et afficher l'embed de la catégorie
        embed = self.cog_embeds[selected_value]
        
        # Mettre à jour le titre de l'embed avec le nom amélioré
        display_name = self.category_display_names.get(selected_value, f"📁 {selected_value}")
        embed.title = f"📘 {display_name}"
        
        await interaction.response.edit_message(embed=embed)
        
    async def show_overview(self, interaction: discord.Interaction):
        # Créer un embed pour la vue d'ensemble
        embed = discord.Embed(
            title="📚 Menu d'aide de MathysieBot™",
            description=(
                "Bienvenue dans le système d'aide de MathysieBot™\n\n"
                "Utilisez le menu déroulant ci-dessous pour explorer les différentes catégories de commandes."
            ),
            color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
            timestamp=datetime.datetime.now()
        )
        
        # Grouper les catégories pour l'affichage
        category_groups = {
            "🛡️ Administration": [],
            "🧰 Utilitaires": [],
            "🎮 Divertissement": [],
            "⚙️ Systèmes": [],
            "❓ Aide": []
        }
        
        # Répartir les cogs dans les groupes
        for cog_name in self.cog_embeds.keys():
            display_name = self.category_display_names.get(cog_name, f"📁 {cog_name}")
            
            if cog_name in ["Commandes_Moderations", "Commandes_Urgence", "RulesCommands", "WhitelistCog"]:
                category_groups["🛡️ Administration"].append(display_name)
            elif cog_name in ["CommandesGénérales", "Commandes_Webs", "MCStatusCommands", "YouTubeDownloader", "ProfilePictureCog", "WikiCommands"]:
                category_groups["🧰 Utilitaires"].append(display_name)
            elif cog_name in ["Commandes_musicales"]:
                category_groups["🎮 Divertissement"].append(display_name)
            elif cog_name in ["StatsCommands", "Commandes_Economie", "RoleManager", "private_voice", "tickets", "BedtimeReminder", "ColorCommands", "compteur_membres"]:
                category_groups["⚙️ Systèmes"].append(display_name)
            else:
                # Log pour identifier les cogs non classés
                print(f"Cog non classé: {cog_name}")
                category_groups["❓ Aide"].append(display_name)
        
        # Ajouter chaque groupe à l'embed
        for group_name, categories in category_groups.items():
            if categories:
                categories_text = "\n".join(f"• {category}" for category in categories)
                embed.add_field(
                    name=f"━━━ {group_name} ━━━",
                    value=categories_text,
                    inline=False
                )
        
        embed.set_footer(
            text="MathysieBot™ • Utilisez le menu déroulant pour plus de détails",
            icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
        )
        
        await interaction.response.edit_message(embed=embed)

class HelpMenu(discord.ui.View):
    def __init__(self, cog_embeds: dict, author: discord.User):
        super().__init__(timeout=60)
        self.cog_embeds = cog_embeds
        self.author = author
        self.message = None
        
        # Ajouter le sélecteur de catégories
        self.add_item(HelpCategorySelect(cog_embeds))
        
        # Ajouter un bouton pour fermer le menu
        self.close_button = Button(label="Fermer", emoji="🚫", style=discord.ButtonStyle.red)
        self.close_button.callback = self.close_callback
        self.add_item(self.close_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Vérifier que c'est l'utilisateur ayant demandé l'aide qui utilise le menu
        if interaction.user != self.author:
            await interaction.response.send_message("Tu ne peux pas utiliser ce menu d'aide.", ephemeral=True)
            return False
        return True
    
    async def close_callback(self, interaction: discord.Interaction):
        # Supprimer le message d'aide
        await interaction.message.delete()
        
    async def on_timeout(self):
        # Désactiver les items quand le timeout est atteint
        for child in self.children:
            child.disabled = True
            
        if self.message:
            try:
                await self.message.edit(view=self)
            except:
                pass

class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Descriptions personnalisées pour certaines catégories
        self.category_descriptions = {
            "ColorCommands": (
                "Personnalisez l'apparence de votre bot en modifiant la couleur des embeds et du rôle décoratif.\n\n"
                "• Changez les couleurs par code hexadécimal ou nom\n"
                "• Gérez le rôle décoratif du bot\n"
                "• Synchronisez la couleur des menus avec le thème choisi"
            ),
            # Vous pouvez ajouter d'autres descriptions personnalisées ici
        }

    def get_command_signature(self, command):
        """Obtenir la signature formatée d'une commande"""
        if not command.usage:
            return f"{self.bot.config.PREFIX}{command.qualified_name} {command.signature}"
        return f"{self.bot.config.PREFIX}{command.qualified_name} {command.usage}"

    @commands.command(name='help', aliases=['aide', 'h'])
    async def help_command(self, ctx, command_name: typing.Optional[str] = None):
        """Affiche les commandes disponibles et leur description"""
        if command_name:
            # Aide spécifique à une commande
            command = self.bot.get_command(command_name)
            if command:
                # Vérifier que l'utilisateur a les permissions pour cette commande
                user_perms = self.bot.perm_manager.get_user_permissions(ctx.author.id)
                cmd_level = getattr(command, 'permission_level', None)
                if cmd_level is not None and cmd_level not in user_perms and 5 not in user_perms:
                    await ctx.send("❌ Vous n'avez pas accès à cette commande.")
                    return
                
                # Créer un embed pour cette commande
                embed = discord.Embed(
                    title=f"📖 Aide pour {command.name}",
                    description=command.help or "Aucune description disponible.",
                    color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(name="Utilisation", value=f"`{self.get_command_signature(command)}`", inline=False)
                
                if command.aliases:
                    aliases = ", ".join([f"`{alias}`" for alias in command.aliases])
                    embed.add_field(name="Alias", value=aliases, inline=False)
                
                if hasattr(command, 'permission_level') and command.permission_level is not None:
                    embed.add_field(name="Niveau de permission", value=f"{command.permission_level}/5", inline=False)
                
                embed.set_footer(
                    text=f"MathysieBot™ • {self.bot.config.PREFIX}help pour voir toutes les commandes",
                    icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
                )
                
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ La commande `{command_name}` n'existe pas.")
            return
            
        # Menu d'aide général
        user_perms = self.bot.perm_manager.get_user_permissions(ctx.author.id)
        cog_embeds = {}  # Dictionnaire pour stocker les embeds par catégorie

        # Debug - Afficher tous les cogs chargés
        print("Cogs actuellement chargés:")
        for cog_name in self.bot.cogs:
            print(f" - {cog_name}")

        # Préparer les embeds pour chaque catégorie
        for cog_name, cog in self.bot.cogs.items():
            available_commands = []
            for cmd in cog.get_commands():
                cmd_level = getattr(cmd, 'permission_level', None)
                if cmd_level is None or cmd_level in user_perms or 5 in user_perms:
                    available_commands.append(cmd)

            if not available_commands:
                continue

            # Utiliser une description personnalisée si elle existe, sinon utiliser une description générique
            custom_description = getattr(self, 'category_descriptions', {}).get(cog_name, "Liste des commandes disponibles dans cette catégorie")
            
            embed = discord.Embed(
                title=f"📘 {cog_name}",
                description=custom_description,
                color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
                timestamp=datetime.datetime.now()
            )

            total_commands = len([cmd for cmd in self.bot.commands])
            available_count = len(available_commands)
            
            stats = (
                "```yaml\n"
                "# Informations #\n"
                f"Commandes disponibles : {available_count}/{total_commands}\n"
                f"Niveau d'accès : {max(user_perms) if user_perms else 0}/5\n"
                "```"
            )
            
            embed.add_field(name="", value=stats, inline=False)
            embed.add_field(name="", value="━━━━━━━━━ Commandes ━━━━━━━━━", inline=False)

            for command in available_commands:
                level_txt = ""
                if hasattr(command, 'permission_level'):
                    level = getattr(command, 'permission_level')
                    if level is not None:
                        level_txt = f"[Niveau {level}] "

                help_text = command.help or 'Pas de description.'
                signature = self.get_command_signature(command)
                
                name = f"`{signature}`"
                value = f"{level_txt}{help_text}"

                embed.add_field(name=name, value=value, inline=False)

            embed.set_footer(
                text="MathysieBot™",
                icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
            )

            cog_embeds[cog_name] = embed

        if not cog_embeds:
            return await ctx.send("Aucune commande trouvée.")

        # Créer un embed pour la vue d'ensemble
        menu_embed = discord.Embed(
            title="📚 Menu d'aide de MathysieBot™",
            description=(
                "Bienvenue dans le système d'aide de MathysieBot™\n\n"
                "Utilisez le menu déroulant ci-dessous pour explorer les différentes catégories de commandes."
            ),
            color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
            timestamp=datetime.datetime.now()
        )
        
        category_display_names = {
            "Commandes_Moderations": "🛡️ Modération",
            "Commandes_Urgence": "🚨 Urgence & Sécurité",
            "RulesCommands": "📜 Règlement",
            "WhitelistCog": "🔑 Permissions",
            "Commandes_Webs": "🌐 Outils Web",
            "MCStatusCommands": "🎮 Status Minecraft",
            "YouTubeDownloader": "📥 YouTube",
            "ProfilePictureCog": "🖼️ Images de profil",
            "WikiCommands": "📚 Recherche Wiki",
            "CommandesGénérales": "🧰 Outils généraux",
            "Commandes_musicales": "🎵 Musique",
            "RoleManager": "🏷️ Gestion des rôles",
            "StatsCommands": "📊 Statistiques",
            "tickets": "🎫 Système de tickets",
            "private_voice": "🔊 Salons vocaux privés",
            "BedtimeReminder": "⏰ Rappels",
            "Commandes_Economie": "💰 Économie",
            "ColorCommands": "🎨 Apparence du bot",  # Modifié pour mieux refléter le rôle
            "HelpCog": "❓ Aide & Support",
        }
        
        # Grouper les catégories 
        category_groups = {
            "🛡️ Administration": [],
            "🧰 Utilitaires": [],
            "🎮 Divertissement": [],
            "⚙️ Systèmes": [],
            "❓ Aide": []
        }
        
        # Répartir les cogs dans les groupes
        for cog_name in cog_embeds.keys():
            display_name = category_display_names.get(cog_name, f"📁 {cog_name}")
            
            if cog_name in ["Commandes_Moderations", "Commandes_Urgence", "RulesCommands", "WhitelistCog"]:
                category_groups["🛡️ Administration"].append(display_name)
            elif cog_name in ["CommandesGénérales", "Commandes_Webs", "MCStatusCommands", "YouTubeDownloader", "ProfilePictureCog", "WikiCommands"]:
                category_groups["🧰 Utilitaires"].append(display_name)
            elif cog_name in ["Commandes_musicales"]:
                category_groups["🎮 Divertissement"].append(display_name)
            elif cog_name in ["StatsCommands", "Commandes_Economie", "RoleManager", "private_voice", "tickets", "BedtimeReminder", "ColorCommands", "compteur_membres"]:
                category_groups["⚙️ Systèmes"].append(display_name)
            else:
                # Log pour identifier les cogs non classés
                print(f"Cog non classé: {cog_name}")
                category_groups["❓ Aide"].append(display_name)
        
        # Ajouter chaque groupe à l'embed
        for group_name, categories in category_groups.items():
            if categories:
                categories_text = "\n".join(f"• {category}" for category in categories)
                menu_embed.add_field(
                    name=f"━━━ {group_name} ━━━",
                    value=categories_text,
                    inline=False
                )
        
        menu_embed.set_thumbnail(url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None)
        menu_embed.set_footer(
            text="MathysieBot™ • Utilisez le menu déroulant pour plus de détails",
            icon_url=ctx.bot.user.avatar.url if ctx.bot.user.avatar else None
        )

        # Créer la vue avec le menu déroulant
        view = HelpMenu(cog_embeds, ctx.author)
        message = await ctx.send(embed=menu_embed, view=view)
        view.message = message  # Pour pouvoir désactiver les boutons après timeout

    @app_commands.command(name="help", description="Affiche l'aide du bot")
    async def help_slash(self, interaction: discord.Interaction, commande: str = None):
        """Affiche le menu d'aide (version slash command)"""
        if commande:
            # Aide spécifique à une commande
            command = self.bot.get_command(commande)
            if command:
                # Vérifier que l'utilisateur a les permissions pour cette commande
                user_perms = self.bot.perm_manager.get_user_permissions(interaction.user.id)
                cmd_level = getattr(command, 'permission_level', None)
                if cmd_level is not None and cmd_level not in user_perms and 5 not in user_perms:
                    await interaction.response.send_message("❌ Vous n'avez pas accès à cette commande.", ephemeral=True)
                    return
                
                # Créer un embed pour cette commande
                embed = discord.Embed(
                    title=f"📖 Aide pour {command.name}",
                    description=command.help or "Aucune description disponible.",
                    color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
                    timestamp=datetime.datetime.now()
                )
                
                embed.add_field(name="Utilisation", value=f"`{self.get_command_signature(command)}`", inline=False)
                
                if command.aliases:
                    aliases = ", ".join([f"`{alias}`" for alias in command.aliases])
                    embed.add_field(name="Alias", value=aliases, inline=False)
                
                if hasattr(command, 'permission_level') and command.permission_level is not None:
                    embed.add_field(name="Niveau de permission", value=f"{command.permission_level}/5", inline=False)
                
                embed.set_footer(
                    text=f"MathysieBot™ • /help pour voir toutes les commandes",
                    icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
                )
                
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ La commande `{commande}` n'existe pas.", ephemeral=True)
            return
            
        # Menu d'aide général (identique à la version commande classique)
        user_perms = self.bot.perm_manager.get_user_permissions(interaction.user.id)
        cog_embeds = {}  # Dictionnaire pour stocker les embeds par catégorie

        # Même logique que dans help_command pour générer les embeds
        # Code similaire mais adapté pour app_commands
        for cog_name, cog in self.bot.cogs.items():
            available_commands = []
            for cmd in cog.get_commands():
                cmd_level = getattr(cmd, 'permission_level', None)
                if cmd_level is None or cmd_level in user_perms or 5 in user_perms:
                    available_commands.append(cmd)

            if not available_commands:
                continue

            # Utiliser une description personnalisée si elle existe, sinon utiliser une description générique
            custom_description = getattr(self, 'category_descriptions', {}).get(cog_name, "Liste des commandes disponibles dans cette catégorie")
            
            embed = discord.Embed(
                title=f"📘 {cog_name}",
                description=custom_description,
                color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
                timestamp=datetime.datetime.now()
            )

            total_commands = len([cmd for cmd in self.bot.commands])
            available_count = len(available_commands)
            
            stats = (
                "```yaml\n"
                "# Informations #\n"
                f"Commandes disponibles : {available_count}/{total_commands}\n"
                f"Niveau d'accès : {max(user_perms) if user_perms else 0}/5\n"
                "```"
            )
            
            embed.add_field(name="", value=stats, inline=False)
            embed.add_field(name="", value="━━━━━━━━━ Commandes ━━━━━━━━━", inline=False)

            for command in available_commands:
                level_txt = ""
                if hasattr(command, 'permission_level'):
                    level = getattr(command, 'permission_level')
                    if level is not None:
                        level_txt = f"[Niveau {level}] "

                help_text = command.help or 'Pas de description.'
                signature = self.get_command_signature(command)
                
                name = f"`{signature}`"
                value = f"{level_txt}{help_text}"

                embed.add_field(name=name, value=value, inline=False)

            embed.set_footer(
                text="MathysieBot™",
                icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
            )

            cog_embeds[cog_name] = embed
            
        if not cog_embeds:
            await interaction.response.send_message("Aucune commande trouvée.", ephemeral=True)
            return

        # Créer un embed pour la vue d'ensemble identique à celui de la commande classique
        menu_embed = discord.Embed(
            title="📚 Menu d'aide de MathysieBot™",
            description=(
                "Bienvenue dans le système d'aide de MathysieBot™\n\n"
                "Utilisez le menu déroulant ci-dessous pour explorer les différentes catégories de commandes."
            ),
            color=EmbedManager.get_default_color(),  # Utiliser la couleur définie
            timestamp=datetime.datetime.now()
        )
        
        category_display_names = {
            "Commandes_Moderations": "🛡️ Modération",
            "Commandes_Urgence": "🚨 Urgence & Sécurité",
            "RulesCommands": "📜 Règlement",
            "WhitelistCog": "🔑 Permissions",
            "Commandes_Webs": "🌐 Outils Web",
            "MCStatusCommands": "🎮 Status Minecraft",
            "YouTubeDownloader": "📥 YouTube",
            "ProfilePictureCog": "🖼️ Images de profil",
            "WikiCommands": "📚 Recherche Wiki",
            "CommandesGénérales": "🧰 Outils généraux",
            "Commandes_musicales": "🎵 Musique",
            "RoleManager": "🏷️ Gestion des rôles",
            "StatsCommands": "📊 Statistiques",
            "tickets": "🎫 Système de tickets",
            "private_voice": "🔊 Salons vocaux privés",
            "BedtimeReminder": "⏰ Rappels",
            "Commandes_Economie": "💰 Économie",
            "ColorCommands": "🎨 Apparence du bot",  # Modifié pour mieux refléter le rôle
            "HelpCog": "❓ Aide & Support",
        }
        
        # Grouper les catégories 
        category_groups = {
            "🛡️ Administration": [],
            "🧰 Utilitaires": [],
            "🎮 Divertissement": [],
            "⚙️ Systèmes": [],
            "❓ Aide": []
        }
        
        # Répartir les cogs
        for cog_name in cog_embeds.keys():
            display_name = category_display_names.get(cog_name, f"📁 {cog_name}")
            
            if cog_name in ["Commandes_Moderations", "Commandes_Urgence", "RulesCommands", "WhitelistCog"]:
                category_groups["🛡️ Administration"].append(display_name)
            elif cog_name in ["CommandesGénérales", "Commandes_Webs", "MCStatusCommands", "YouTubeDownloader", "ProfilePictureCog", "WikiCommands"]:
                category_groups["🧰 Utilitaires"].append(display_name)
            elif cog_name in ["Commandes_musicales"]:
                category_groups["🎮 Divertissement"].append(display_name)
            elif cog_name in ["StatsCommands", "Commandes_Economie", "RoleManager", "private_voice", "tickets", "BedtimeReminder", "ColorCommands", "compteur_membres"]:
                category_groups["⚙️ Systèmes"].append(display_name)
            else:
                # Log pour identifier les cogs non classés
                print(f"Cog non classé: {cog_name}")
                category_groups["❓ Aide"].append(display_name)
        
        # Ajouter chaque groupe à l'embed
        for group_name, categories in category_groups.items():
            if categories:
                categories_text = "\n".join(f"• {category}" for category in categories)
                menu_embed.add_field(
                    name=f"━━━ {group_name} ━━━",
                    value=categories_text,
                    inline=False
                )
        
        menu_embed.set_thumbnail(url=interaction.client.user.avatar.url if interaction.client.user.avatar else None)
        menu_embed.set_footer(
            text="MathysieBot™ • Utilisez le menu déroulant pour plus de détails",
            icon_url=interaction.client.user.avatar.url if interaction.client.user.avatar else None
        )

        # Créer la vue avec le menu déroulant
        view = HelpMenu(cog_embeds, interaction.user)
        await interaction.response.send_message(embed=menu_embed, view=view, ephemeral=True)
        # On ne peut pas récupérer le message après interaction.response.send_message avec ephemeral=True

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    # Supprimer l'ancienne cog d'aide si elle existe
    old_cog_path = "cogs.help"
    try:
        await bot.unload_extension(old_cog_path)
        print("🔄 Ancienne cog d'aide déchargée")
    except:
        pass
    print("✅ Module d'aide chargé avec succès")
