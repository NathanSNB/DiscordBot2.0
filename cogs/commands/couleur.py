import discord
from discord.ext import commands
import json
import os
import re
import asyncio
import logging
from utils.logger import setup_logger
from utils.embed_manager import EmbedManager

# Initialiser le logger correctement
logger = logging.getLogger('bot')

# Définir une variable qui permet de détecter que ce module est le "color.py" recherché
__color_module__ = True  

class ColorCommands(commands.Cog, name="ColorCommands"):
    """Commandes pour personnaliser les couleurs du bot et son apparence
    
    Ce module permet de:
    • Changer la couleur des embeds par nom ou code hexadécimal
    • Gérer automatiquement le rôle décoratif du bot
    • Synchroniser la couleur du rôle du bot avec les embeds
    • Actualiser les menus avec la nouvelle couleur choisie
    """

    # Dictionnaire des couleurs nommées (formats HTML)
    NAMED_COLORS = {
        "rouge": 0xFF0000,
        "bleu": 0x0000FF,
        "vert": 0x00FF00,
        "jaune": 0xFFFF00,
        "orange": 0xFFA500,
        "violet": 0x800080,
        "rose": 0xFF69B4,
        "cyan": 0x00FFFF,
        "noir": 0x000000,
        "blanc": 0xFFFFFF,
        "gris": 0x808080,
        "marron": 0x8B4513,
        "turquoise": 0x40E0D0,
        "lavande": 0xE6E6FA,
        "indigo": 0x4B0082,
        "or": 0xFFD700,
        "argent": 0xC0C0C0,
        "bronze": 0xCD7F32,
        "corail": 0xFF7F50,
    }

    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/bot_settings.json'
        # Créer le dossier data si nécessaire pour éviter les erreurs
        os.makedirs('data', exist_ok=True)
        
        # Charger les paramètres existants ou créer des paramètres par défaut
        self.settings = self.load_settings()
        
        # Synchroniser avec Config pour éviter les conflits
        if hasattr(self.bot, 'config') and hasattr(self.bot.config, 'DEFAULT_COLOR'):
            self.bot.config.DEFAULT_COLOR = self.settings.get("embed_color", 0x2BA3B3)
            
        # Planifier la vérification des rôles après que le bot soit prêt
        self.bot.loop.create_task(self.setup_roles_when_ready())
        logger.info("✅ Initialisation du système de couleur et rôle décoratif")

    def load_settings(self):
        """Charge les paramètres du bot depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    logger.info(f"✅ Fichier de configuration des couleurs chargé: {self.config_file}")
                    return json.load(f)
            else:
                # Créer le fichier avec des paramètres par défaut
                default_settings = {
                    "embed_color": 0x2BA3B3,  # Couleur par défaut
                    "last_modified": "N/A"
                }
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    json.dump(default_settings, f, indent=4)
                logger.info(f"✅ Fichier de configuration des couleurs créé: {self.config_file}")
                return default_settings
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des paramètres: {str(e)}")
            return {"embed_color": 0x2BA3B3}

    def save_settings(self):
        """Sauvegarde les paramètres dans le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des paramètres: {e}")

    def color_hex_to_int(self, color_hex):
        """Convertit un code couleur hexadécimal en entier"""
        # Supprimer le # si présent
        if color_hex.startswith('#'):
            color_hex = color_hex[1:]
        
        # S'assurer que le format est valide
        if not re.match(r'^[0-9A-Fa-f]{6}$', color_hex):
            raise ValueError("Format de couleur hexadécimal invalide")
        
        # Convertir en entier
        return int(color_hex, 16)

    async def ensure_bot_role(self, guild):
        """Vérifie que le bot a un rôle décoratif avec son nom, et le crée ou le met à jour si nécessaire"""
        try:
            bot_member = guild.get_member(self.bot.user.id)
            if not bot_member:
                return False, "Je ne peux pas me trouver dans ce serveur"
                
            color_value = self.settings.get("embed_color", 0x2BA3B3)
            new_color = discord.Color(color_value)
            
            # Rechercher un rôle avec le nom exact du bot
            bot_role = discord.utils.get(guild.roles, name=self.bot.user.name)
            
            # Si le rôle n'existe pas, le créer
            if not bot_role:
                # Vérifier les permissions
                if not guild.me.guild_permissions.manage_roles:
                    return False, "Je n'ai pas la permission de gérer les rôles"
                
                # Créer un nouveau rôle
                bot_role = await guild.create_role(
                    name=self.bot.user.name,
                    color=new_color,
                    reason="Rôle décoratif pour le bot"
                )
                
                # Positionner le rôle juste en dessous du rôle le plus haut du bot
                highest_role = guild.me.top_role
                if highest_role.name != "@everyone":
                    try:
                        await bot_role.edit(position=highest_role.position - 1)
                    except discord.HTTPException:
                        # Si on ne peut pas modifier la position, ce n'est pas grave
                        pass
                
                # Attribuer le rôle au bot
                await bot_member.add_roles(bot_role, reason="Attribution du rôle décoratif")
                return True, f"Rôle {bot_role.name} créé et attribué"
            else:
                # Le rôle existe, mettre à jour sa couleur
                await bot_role.edit(color=new_color, reason="Mise à jour de la couleur du rôle")
                
                # Vérifier si le bot a ce rôle, sinon l'ajouter
                if bot_role not in bot_member.roles:
                    await bot_member.add_roles(bot_role, reason="Attribution du rôle décoratif")
                    return True, f"Rôle {bot_role.name} attribué et mis à jour"
                return True, f"Rôle {bot_role.name} mis à jour"
                
        except discord.Forbidden:
            return False, "Je n'ai pas la permission nécessaire pour gérer les rôles"
        except Exception as e:
            logger.error(f"Erreur lors de la gestion du rôle du bot: {str(e)}")
            return False, f"Une erreur est survenue: {str(e)}"

    async def setup_roles_when_ready(self):
        """Attend que le bot soit prêt puis configure les rôles dans tous les serveurs"""
        try:
            await self.bot.wait_until_ready()
            logger.info(f"Bot prêt! Configuration des rôles décoratifs pour {len(self.bot.guilds)} serveurs...")
            
            # Mise à jour dans chaque serveur
            success_count = 0
            fail_count = 0
            
            for guild in self.bot.guilds:
                try:
                    # Vérifier si le bot a déjà le rôle dans ce serveur
                    bot_member = guild.get_member(self.bot.user.id)
                    if not bot_member:
                        logger.warning(f"Impossible de trouver le bot dans le serveur {guild.name}")
                        continue
                        
                    # Vérifier si un rôle avec le nom du bot existe déjà
                    existing_role = discord.utils.get(guild.roles, name=self.bot.user.name)
                    
                    if existing_role and existing_role in bot_member.roles:
                        # Le bot a déjà le rôle, juste mettre à jour la couleur
                        logger.info(f"Serveur {guild.name}: Le bot a déjà le rôle, mise à jour de la couleur")
                    else:
                        # Le bot n'a pas le rôle ou le rôle n'existe pas
                        logger.info(f"Serveur {guild.name}: Création/attribution du rôle décoratif")
                    
                    # Appliquer ou mettre à jour le rôle
                    success, message = await self.ensure_bot_role(guild)
                    if success:
                        success_count += 1
                        logger.info(f"✅ Serveur {guild.name}: {message}")
                    else:
                        fail_count += 1
                        logger.warning(f"⚠️ Serveur {guild.name}: {message}")
                        
                except Exception as e:
                    fail_count += 1
                    logger.error(f"❌ Erreur lors de la configuration du rôle dans {guild.name}: {str(e)}")
            
            # Log final avec statistiques
            logger.info(f"Configuration des rôles terminée: ✅ {success_count} réussis, ❌ {fail_count} échoués")
        except Exception as e:
            logger.error(f"❌ Erreur globale dans setup_roles_when_ready: {str(e)}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Se déclenche quand le bot rejoint un nouveau serveur"""
        try:
            logger.info(f"Bot ajouté au serveur: {guild.name}")
            await self.ensure_bot_role(guild)
        except Exception as e:
            logger.error(f"Erreur lors de la création du rôle sur le nouveau serveur {guild.name}: {str(e)}")

    @commands.command(
        name="setcolor", 
        aliases=["couleur", "color"],
        help="Change la couleur des embeds et du rôle du bot",
        description="Modifie la couleur utilisée pour les embeds et le rôle du bot. Accepte un code hexadécimal ou un nom de couleur.",
        usage="<nom_couleur | #code_hex>"
    )
    @commands.has_permissions(administrator=True)
    async def set_color(self, ctx, *, color_input: str):
        """Change la couleur par défaut des embeds et du rôle du bot"""
        try:
            # Vérifier si c'est un nom de couleur
            color_input = color_input.lower().strip()
            
            if color_input in self.NAMED_COLORS:
                color_value = self.NAMED_COLORS[color_input]
                color_name = color_input
                color_hex = f"#{color_value:06X}"
            else:
                # Essayer de traiter comme code hexadécimal
                try:
                    color_hex = color_input
                    color_value = self.color_hex_to_int(color_input)
                    color_name = "personnalisée"
                except ValueError:
                    await ctx.send(f"❌ Couleur invalide. Utilisez un nom de couleur connu ou un code hexadécimal valide (ex: #2BA3B3).")
                    return
            
            # Mettre à jour les paramètres
            old_color = self.settings.get("embed_color", 0x2BA3B3)
            self.settings["embed_color"] = color_value
            self.settings["last_modified"] = f"{ctx.author.name} ({ctx.author.id})"
            self.save_settings()
            
            # Mettre à jour les couleurs dans la configuration du bot
            self.bot.config.DEFAULT_COLOR = color_value
            self.bot.config.initialize_colors()
            
            # Force EmbedManager to reload the color
            EmbedManager.reload_color()
            
            # Mettre à jour la couleur du rôle du bot
            role_updated, role_message = await self.ensure_bot_role(ctx.guild)
            
            # Créer un embed de confirmation
            embed = EmbedManager.create_embed(
                title="✅ Couleur modifiée",
                description=f"La couleur des embeds a été changée en **{color_name}** ({color_hex}).\n\n"
                            f"{'✅' if role_updated else '❌'} {role_message}\n\n"
                            f"**Note:** Tous les nouveaux embeds utiliseront désormais cette couleur.",
                color=discord.Color(color_value)  # Utiliser la nouvelle couleur pour l'embed
            )
            
            # Ajouter un exemple visuel de l'ancienne et de la nouvelle couleur
            embed.add_field(
                name="Ancienne couleur",
                value=f"#{old_color:06X}",
                inline=True
            )
            
            embed.add_field(
                name="Nouvelle couleur",
                value=f"{color_hex}",
                inline=True
            )
            
            await ctx.send(embed=embed)
            
        except discord.Forbidden:
            await ctx.send("❌ Je n'ai pas les permissions nécessaires pour modifier les rôles.")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")
            logger.error(f"Erreur dans setcolor: {str(e)}")

    @commands.command(
        name="listcolors",
        aliases=["couleurs", "colors"],
        help="Affiche la liste des couleurs disponibles",
        description="Affiche toutes les couleurs nommées disponibles avec leurs codes hexadécimaux.",
        usage=""
    )
    async def list_colors(self, ctx):
        """Affiche la liste des couleurs disponibles"""
        embed = EmbedManager.create_embed(
            title="🎨 Couleurs disponibles",
            description="Liste des couleurs nommées que vous pouvez utiliser avec la commande `!setcolor`:",
        )
        
        # Organiser les couleurs par groupes pour l'affichage
        colors_per_field = 5
        sorted_colors = sorted(self.NAMED_COLORS.items())
        
        for i in range(0, len(sorted_colors), colors_per_field):
            chunk = sorted_colors[i:i+colors_per_field]
            field_value = "\n".join([f"**{name}**: `#{value:06X}`" for name, value in chunk])
            embed.add_field(name=f"Groupe {i//colors_per_field + 1}", value=field_value, inline=True)
        
        embed.add_field(
            name="💡 Utilisation personnalisée",
            value="Vous pouvez également utiliser un code hexadécimal directement:\n`!setcolor #2BA3B3`",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(
        name="currentcolor",
        aliases=["couleuractuelle", "getcolor"],
        help="Affiche la couleur actuelle des embeds",
        description="Montre la couleur actuellement utilisée pour les embeds du bot.",
        usage=""
    )
    async def current_color(self, ctx):
        """Affiche la couleur actuelle des embeds"""
        color_value = self.settings.get("embed_color", 0x2BA3B3)
        color_hex = f"#{color_value:06X}"
        
        # Trouver le nom de la couleur si c'est une couleur nommée
        color_name = "personnalisée"
        for name, value in self.NAMED_COLORS.items():
            if value == color_value:
                color_name = name
                break
        
        embed = EmbedManager.create_embed(
            title="🎨 Couleur actuelle",
            description=f"La couleur actuelle des embeds est **{color_name}** ({color_hex}).",
            color=discord.Color(color_value)
        )
        
        embed.add_field(
            name="Dernière modification",
            value=self.settings.get("last_modified", "N/A"),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    @commands.command(
        name="updatebotrole",
        aliases=["majrole", "botrole"],
        help="Crée ou met à jour le rôle décoratif du bot",
        description="Vérifie que le bot a un rôle à son nom avec la couleur des embeds, le crée si nécessaire.",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def update_bot_role(self, ctx):
        """Crée ou met à jour le rôle décoratif du bot"""
        try:
            success, message = await self.ensure_bot_role(ctx.guild)
            
            color_value = self.settings.get("embed_color", 0x2BA3B3)
            embed = EmbedManager.create_embed(
                title="🤖 Rôle du bot" if success else "❌ Erreur",
                description=message,
                color=discord.Color(color_value)
            )
            
            # Si succès, ajouter des informations sur le rôle
            if success:
                bot_role = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
                if bot_role:
                    embed.add_field(
                        name="Détails du rôle",
                        value=f"**Nom**: {bot_role.name}\n"
                            f"**ID**: {bot_role.id}\n"
                            f"**Couleur**: #{bot_role.color.value:06X}\n"
                            f"**Position**: {bot_role.position}",
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")

    @commands.command(
        name="refreshmenus",
        aliases=["actualisermenus", "updatemenus"],
        help="Actualise tous les menus du bot avec la couleur actuelle",
        description="Met à jour les différents menus du bot pour utiliser la couleur d'embed actuelle.",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def refresh_menus(self, ctx):
        """Actualise tous les menus pour appliquer la couleur actuelle des embeds"""
        try:
            # Message de démarrage
            loading_msg = await ctx.send("🔄 Actualisation des menus en cours...")
            
            # Compteurs pour le suivi des mises à jour
            updated = 0
            failed = 0
            skipped = 0
            menus_updated = []
            
            # Forcer le rechargement de la couleur dans EmbedManager
            EmbedManager.reload_color()
            
            # Actualiser aussi le rôle décoratif du bot
            try:
                success, _ = await self.ensure_bot_role(ctx.guild)
                if success:
                    updated += 1
                    menus_updated.append("Rôle décoratif du bot")
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'actualisation du rôle décoratif: {str(e)}")
                failed += 1
            
            # 1. Actualiser le système de tickets
            try:
                # S'assurer que le cog tickets a bien la dernière couleur
                ticket_cog = self.bot.get_cog('tickets')
                if ticket_cog and hasattr(ticket_cog, 'color'):
                    ticket_cog.color = EmbedManager.get_default_color()
                    
                # Appeler la méthode de rafraîchissement du système de tickets si elle existe
                if hasattr(self.bot, 'refresh_ticket_system'):
                    success = await self.bot.refresh_ticket_system()
                    if success:
                        updated += 1
                        menus_updated.append("Menu des tickets")
                    else:
                        failed += 1
                else:
                    skipped += 1
                    logger.info("⏭️ Système de tickets ignoré: méthode non disponible")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'actualisation du menu tickets: {str(e)}")
                failed += 1
            
            # 2. Actualiser le système de règlement
            try:
                if hasattr(self.bot, 'refresh_rules_system'):
                    success = await self.bot.refresh_rules_system()
                    if success:
                        updated += 1
                        menus_updated.append("Règlement du serveur")
                    else:
                        failed += 1
                else:
                    skipped += 1
                    logger.info("⏭️ Système de règlement ignoré: méthode non disponible")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'actualisation du règlement: {str(e)}")
                failed += 1
            
            # 3. Actualiser le système de rôles
            try:
                if hasattr(self.bot, 'refresh_roles_system'):
                    success = await self.bot.refresh_roles_system()
                    if success:
                        updated += 1
                        menus_updated.append("Menu des rôles")
                    else:
                        failed += 1
                else:
                    skipped += 1
                    logger.info("⏭️ Système de rôles ignoré: méthode non disponible")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'actualisation du menu des rôles: {str(e)}")
                failed += 1
            
            # Créer un embed de résultat
            color_value = self.settings.get("embed_color", 0x2BA3B3)
            embed = discord.Embed(
                title="♻️ Actualisation des menus",
                description=f"Les menus ont été actualisés pour utiliser la couleur actuelle.",
                color=discord.Color(color_value)
            )
            
            # Ajouter les résultats détaillés
            if menus_updated:
                embed.add_field(
                    name="✅ Menus actualisés",
                    value="\n".join([f"• {menu}" for menu in menus_updated]),
                    inline=False
                )
            else:
                embed.add_field(
                    name="⚠️ Aucun menu actualisé",
                    value="Aucun menu n'a pu être actualisé",
                    inline=False
                )
            
            # Ajouter les statistiques
            embed.add_field(
                name="📊 Résultats",
                value=f"✅ Réussis: **{updated}**\n❌ Échoués: **{failed}**\n⏭️ Ignorés: **{skipped}**",
                inline=False
            )
            
            # Ajouter la couleur actuelle pour référence
            color_hex = f"#{color_value:06X}"
            embed.add_field(
                name="🎨 Couleur appliquée",
                value=f"Code: `{color_hex}`",
                inline=True
            )
            
            # Ajouter des conseils
            embed.set_footer(text="Commande exécutée avec succès • Bot Discord")
            
            # Remplacer le message de chargement
            await loading_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")

    @commands.command(
        name="createbotrole",
        aliases=["creerole", "newrole"],
        help="Crée un nouveau rôle décoratif pour le bot",
        description="Supprime l'ancien rôle décoratif du bot s'il existe et en crée un nouveau avec la couleur actuelle des embeds.",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def create_bot_role(self, ctx):
        """Crée un nouveau rôle décoratif pour le bot, en supprimant l'ancien s'il existe"""
        try:
            # Message de chargement
            loading_msg = await ctx.send("🔄 Création du rôle en cours...")
            
            # Obtenir la couleur actuelle
            color_value = self.settings.get("embed_color", 0x2BA3B3)
            new_color = discord.Color(color_value)
            
            # Trouver le rôle existant du bot
            old_role = discord.utils.get(ctx.guild.roles, name=self.bot.user.name)
            
            # Supprimer l'ancien rôle s'il existe
            if old_role:
                try:
                    await old_role.delete(reason="Recréation du rôle décoratif")
                    await asyncio.sleep(1)  # Attendre un peu pour éviter les problèmes de Discord rate limits
                    role_deleted = True
                except discord.Forbidden:
                    role_deleted = False
                    await loading_msg.edit(content="⚠️ Je n'ai pas la permission de supprimer mon ancien rôle.")
                    return
                except Exception as e:
                    role_deleted = False
                    logger.error(f"Erreur lors de la suppression de l'ancien rôle: {str(e)}")
            else:
                role_deleted = False
            
            # Créer un nouveau rôle
            try:
                new_role = await ctx.guild.create_role(
                    name=self.bot.user.name,
                    color=new_color,
                    reason="Création d'un rôle décoratif pour le bot"
                )
                
                # Positionner le rôle juste en dessous du rôle le plus haut du bot
                highest_role = ctx.guild.me.top_role
                if highest_role.name != "@everyone":
                    try:
                        await new_role.edit(position=highest_role.position - 1)
                    except discord.HTTPException:
                        # Si on ne peut pas modifier la position, ce n'est pas grave
                        pass
                
                # Attribuer le rôle au bot
                await ctx.guild.me.add_roles(new_role, reason="Attribution du nouveau rôle décoratif")
                
                # Créer un embed de confirmation
                embed = EmbedManager.create_embed(
                    title="✅ Rôle décoratif créé",
                    description=f"Un nouveau rôle décoratif a été créé et attribué au bot."
                )
                
                embed.add_field(
                    name="Détails",
                    value=f"**Nom**: {new_role.name}\n"
                        f"**ID**: {new_role.id}\n"
                        f"**Couleur**: #{new_role.color.value:06X}\n"
                        f"**Position**: {new_role.position}\n"
                        f"**Ancien rôle supprimé**: {'Oui' if role_deleted else 'Non/Inexistant'}",
                    inline=False
                )
                
                await loading_msg.edit(content=None, embed=embed)
                
            except discord.Forbidden:
                await loading_msg.edit(content="❌ Je n'ai pas les permissions nécessaires pour créer un rôle.")
            except Exception as e:
                await loading_msg.edit(content=f"❌ Une erreur est survenue: {str(e)}")
                logger.error(f"Erreur lors de la création du nouveau rôle: {str(e)}")
                
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")

# Fonction setup d'origine
async def setup(bot):
    await bot.add_cog(ColorCommands(bot))

# Fonction supplémentaire pour permettre l'importation depuis "color.py" 
# (alias pour éviter l'erreur de chargement)
def get_class():
    return ColorCommands