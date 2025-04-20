import discord
from discord.ext import commands
import os
import logging
import json
import asyncio

# Configuration du logger (si nécessaire)
logger = logging.getLogger('bot')

# Liste d'émojis pour l'embed (Unicode seulement pour éviter les erreurs)
EMBED_EMOJIS = {
    "title": ["🎭", "🎪", "🎯", "🎨", "🎮", "🌟", "✨", "🔰"],
    "field": ["📌", "📊", "📋", "📝", "📎", "📘", "📗", "📙"],
    "success": ["✅", "🟢", "🎉", "🎊"],
    "error": ["❌", "🔴", "⛔", "🚫"],
    "info": ["ℹ️", "📢", "🔔", "📣"],
    "update": ["🔄", "♻️", "📤", "🔃"]
}

def create_embed(title, description=None, embed_type="info"):
    """Crée un embed standard avec des émojis"""
    emoji_prefix = ""
    
    if embed_type in EMBED_EMOJIS:
        emoji_prefix = EMBED_EMOJIS[embed_type][0] + " "
    
    embed = discord.Embed(title=emoji_prefix + title, description=description, color=discord.Color(0x2BA3B3))
    embed.set_footer(text="Bot Discord - Système de Rôles")
    return embed

class RoleButton(discord.ui.Button):
    def __init__(self, role_id, role_name):
        super().__init__(style=discord.ButtonStyle.primary, label=role_name)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        role = guild.get_role(self.role_id)
        member = interaction.user

        if role in member.roles:
            await member.remove_roles(role)
            await interaction.response.send_message(f"{EMBED_EMOJIS['error'][0]} {role.name} retiré.", ephemeral=True)
            logger.info(f"Rôle {role.name} retiré de {member.name}")
        else:
            await member.add_roles(role)
            await interaction.response.send_message(f"{EMBED_EMOJIS['success'][0]} {role.name} ajouté.", ephemeral=True)
            logger.info(f"Rôle {role.name} ajouté à {member.name}")

class RoleView(discord.ui.View):
    def __init__(self, roles_data):
        super().__init__(timeout=None)
        for role_key, data in roles_data.items():
            self.add_item(RoleButton(role_id=data["id"], role_name=data["name"]))

class RolesManagementCog(commands.Cog, name="RoleManager"):
    def __init__(self, bot):
        self.bot = bot
        self.roles_data = {}
        self.default_channel_id = 1356659177870594130
        self.channel_config_file = 'data/channel_config.json'
        
        # Création des dossiers nécessaires
        os.makedirs('data', exist_ok=True)
        os.makedirs('logs', exist_ok=True)
        
        # Chargement des configurations
        self.load_roles()
        self.load_channel_config()
        
        logger.info("✅ RolesManagementCog initialisé")
        
    def load_roles(self):
        """Charge la configuration des rôles depuis le fichier JSON"""
        try:
            if os.path.exists('data/roles_config.json'):
                with open('data/roles_config.json', 'r', encoding='utf-8') as f:
                    self.roles_data = json.load(f)
            else:
                self.roles_data = {}
        except Exception as e:
            logger.error(f"❌ Erreur chargement rôles: {str(e)}")
            self.roles_data = {}

    def save_roles(self):
        """Sauvegarde la configuration des rôles"""
        with open('data/roles_config.json', 'w', encoding='utf-8') as f:
            json.dump(self.roles_data, f, indent=4)

    def load_channel_config(self):
        """Charge la configuration du canal"""
        try:
            if os.path.exists(self.channel_config_file):
                with open(self.channel_config_file, 'r') as f:
                    config = json.load(f)
                    self.default_channel_id = config.get('channel_id', self.default_channel_id)
                logger.info(f"📝 Configuration du canal chargée: {self.default_channel_id}")
        except Exception as e:
            logger.error(f"❌ Erreur chargement canal: {str(e)}")

    def save_channel_config(self):
        """Sauvegarde la configuration du canal"""
        with open(self.channel_config_file, 'w') as f:
            json.dump({'channel_id': self.default_channel_id}, f, indent=4)
            
    async def send_role_menu(self):
        """Envoie le menu des rôles dans le canal par défaut"""
        if not self.roles_data:
            logger.warning("⚠️ Aucun rôle configuré pour l'affichage initial")
            return
            
        try:
            channel = self.bot.get_channel(self.default_channel_id)
            if not channel:
                logger.error(f"❌ Canal avec ID {self.default_channel_id} non trouvé")
                return
                
            embed = create_embed(
                "Choisissez vos rôles !",
            )

            # Ajout des rôles dans l'embed avec les émojis configurés
            for role_key, data in self.roles_data.items():
                # Utiliser l'emoji configuré ou un émoji par défaut
                emoji = data.get('emoji', '🔹')
                embed.add_field(
                    name=f"{emoji} {data['name']}", 
                    value=data['description'] or "Pas de description",
                    inline=False
                )

            # Ajout d'informations d'utilisation en bas
            embed.add_field(
                name="💡 Utilisation",
                value="Cliquez sur un bouton pour ajouter/retirer un rôle.\nLes modifications sont instantanées !",
                inline=False
            )

            view = RoleView(self.roles_data)
            await channel.send(embed=embed, view=view)
            logger.info(f"✅ Menu rôles créé dans le canal {channel.name}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi menu rôles: {str(e)}")
        
    @commands.command(
        name="roles",
        help="Envoie le menu de sélection des rôles dans le canal actuel",
        description="Cette commande crée un menu interactif permettant aux utilisateurs de s'attribuer ou de retirer des rôles prédéfinis.",
        usage="!roles"
    )
    @commands.has_permissions(administrator=True)
    async def role_menu_command(self, ctx):
        """Envoie le menu de sélection des rôles dans le canal actuel"""
        logger.info(f"⚙️ Menu rôles demandé par {ctx.author}")
        try:
            if not self.roles_data:
                await ctx.send("❌ Aucun rôle configuré. Utilisez !configrole pour en ajouter.")
                return

            embed = create_embed(
                "Choisissez vos rôles !",
            )

            # Ajout des rôles dans l'embed avec les émojis configurés
            for role_key, data in self.roles_data.items():
                # Utiliser l'emoji configuré ou un émoji par défaut
                emoji = data.get('emoji', '🔹')
                embed.add_field(
                    name=f"{emoji} {data['name']}", 
                    value=data['description'] or "Pas de description",
                    inline=False
                )

            # Ajout d'informations d'utilisation en bas
            embed.add_field(
                name="💡 Utilisation",
                value="Cliquez sur un bouton pour ajouter/retirer un rôle.\nLes modifications sont instantanées !",
                inline=False
            )

            view = RoleView(self.roles_data)
            await ctx.send(embed=embed, view=view)
            logger.info("✅ Menu rôles créé")
        except Exception as e:
            logger.error(f"❌ Erreur menu rôles: {str(e)}")
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")

    @commands.command(
        name="refreshroles",
        help="Actualise le menu des rôles dans le canal par défaut",
        description="Supprime l'ancien menu des rôles et en crée un nouveau avec les rôles actuellement configurés.",
        usage="!refreshroles"
    )
    @commands.has_permissions(administrator=True)
    async def refreshroles_command(self, ctx):
        """Actualise le menu des rôles dans le canal par défaut"""
        try:
            # Vérifier si le canal par défaut existe
            channel = self.bot.get_channel(self.default_channel_id)
            if not channel:
                await ctx.send(f"❌ Canal avec ID {self.default_channel_id} non trouvé. Utilisez !setchannel pour configurer un canal valide.")
                return
                
            # Envoyer un message temporaire indiquant que l'actualisation est en cours
            temp_message = await ctx.send(embed=create_embed(
                "Actualisation en cours...",
                "Le menu des rôles est en cours d'actualisation.",
                "update"
            ))
            
            # Supprimer les 10 derniers messages du canal par défaut (pour chercher et supprimer l'ancien menu)
            try:
                async for message in channel.history(limit=10):
                    if message.author == self.bot.user and message.embeds and "Choisissez vos rôles" in message.embeds[0].title:
                        await message.delete()
                        logger.info(f"🗑️ Ancien menu supprimé")
                        break
            except Exception as e:
                logger.error(f"❌ Erreur suppression ancien menu: {str(e)}")
                
            # Envoyer le nouveau menu
            await self.send_role_menu()
            
            # Supprimer le message temporaire et envoyer une confirmation
            await temp_message.delete()
            await ctx.send(embed=create_embed(
                "Menu actualisé",
                f"Le menu des rôles a été actualisé dans {channel.mention}",
                "success"
            ))
            logger.info(f"🔄 Menu rôles actualisé par {ctx.author}")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de l'actualisation: {str(e)}")
            logger.error(f"❌ Erreur actualisation menu: {str(e)}")

    @commands.command(
        name="configrole",
        help="Configure un nouveau rôle pour le menu avec un emoji personnalisé",
        description="Ajoute un rôle au système de distribution automatique avec un emoji et une description personnalisée.",
        usage="!configrole @Role 🌟 Description du rôle"
    )
    @commands.has_permissions(administrator=True)
    async def configrole_command(self, ctx, role: discord.Role, emoji: str = "🔹", *, description: str = ""):
        """Configure un nouveau rôle pour le menu avec un emoji personnalisé
        
        Usage: !configrole @Role 🌟 Description du rôle
        """
        # Vérifier si l'emoji est valide (Unicode ou emoji Discord)
        if len(emoji) > 2 and not emoji.startswith('<'):
            await ctx.send(embed=create_embed(
                "Emoji invalide", 
                "Veuillez utiliser un emoji Unicode valide ou un emoji Discord.",
                "error"
            ))
            return
            
        # Utiliser l'ID du rôle comme clé
        role_key = str(role.id)
        
        self.roles_data[role_key] = {
            "id": role.id,
            "name": role.name,
            "description": description,
            "emoji": emoji
        }
        self.save_roles()
        
        embed = create_embed(
            "Rôle configuré",
            f"Le rôle {role.mention} a été ajouté au menu avec l'emoji {emoji}",
            "success"
        )
        await ctx.send(embed=embed)
        logger.info(f"✅ Rôle {role.name} configuré par {ctx.author} avec emoji {emoji}")

    @commands.command(
        name="delrole",
        help="Supprime un rôle de la configuration",
        description="Retire un rôle du système de distribution automatique.",
        usage="!delrole @Role"
    )
    @commands.has_permissions(administrator=True)
    async def delrole_command(self, ctx, role: discord.Role):
        """Supprime un rôle de la configuration"""
        role_key = None
        
        # Recherche du rôle par son ID
        for key, data in self.roles_data.items():
            if data["id"] == role.id:
                role_key = key
                break
        
        if role_key:
            del self.roles_data[role_key]
            self.save_roles()
            await ctx.send(embed=create_embed(
                "Rôle supprimé", 
                f"Le rôle {role.mention} a été retiré du menu",
                "success"
            ))
            logger.info(f"🗑️ Rôle {role.name} supprimé par {ctx.author}")
        else:
            await ctx.send(embed=create_embed(
                "Rôle non trouvé", 
                f"Le rôle {role.mention} n'est pas configuré dans le menu",
                "error"
            ))

    @commands.command(
        name="listroles",
        help="Affiche la liste des rôles configurés",
        description="Montre tous les rôles actuellement configurés dans le système avec leurs descriptions et emojis.",
        usage="!listroles"
    )
    @commands.has_permissions(administrator=True)
    async def listroles_command(self, ctx):
        """Affiche la liste des rôles configurés"""
        if not self.roles_data:
            await ctx.send(embed=create_embed(
                "Aucun rôle configuré", 
                "Utilisez !configrole pour ajouter des rôles",
                "error"
            ))
            return

        embed = create_embed("Rôles configurés", "", "info")
        
        count = 1
        for key, data in self.roles_data.items():
            role = ctx.guild.get_role(data["id"])
            if role:
                # Utiliser l'emoji configuré pour chaque rôle
                emoji = data.get('emoji', '🔹')
                embed.add_field(
                    name=f"{emoji} {data['name']}", 
                    value=data['description'] or "Pas de description",
                    inline=False
                )
                count += 1
                
        embed.set_footer(text=f"Total: {len(self.roles_data)} rôles • Bot Discord - Système de Rôles")
        await ctx.send(embed=embed)
        logger.info(f"📋 Liste des rôles affichée pour {ctx.author}")

    @commands.command(
        name="setchannel",
        help="Définit le canal par défaut pour l'affichage du menu des rôles",
        description="Configure le canal où sera affiché le menu des rôles lors de l'utilisation de !refreshroles.",
        usage="!setchannel #canal"
    )
    @commands.has_permissions(administrator=True)
    async def setchannel_command(self, ctx, channel: discord.TextChannel = None):
        """Définit le canal par défaut pour l'affichage du menu des rôles"""
        if channel is None:
            channel = ctx.channel
            
        self.default_channel_id = channel.id
        self.save_channel_config()
        
        await ctx.send(embed=create_embed(
            "Canal configuré", 
            f"Le canal {channel.mention} a été défini comme canal par défaut pour le menu des rôles",
            "success"
        ))
        logger.info(f"📝 Canal par défaut changé pour {channel.name} par {ctx.author}")

async def setup(bot):
    await bot.add_cog(RolesManagementCog(bot))