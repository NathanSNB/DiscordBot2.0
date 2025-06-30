import discord
from discord.ext import commands
import asyncio
from config import Config
from loader import load_cogs  # Import du nouveau chargeur
from utils.logger import setup_logger
from utils.permission_manager import PermissionManager
from utils.rules_manager import RulesManager
from utils.warns_manager import WarnsManager
from utils.database import db_manager
from utils.migration import migration_manager
from utils.access_manager import AccessManager
import logging
import os

logger = setup_logger()

class MathysieBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=Config.PREFIX,
            intents=discord.Intents.all(),
            help_command=None  # Utiliser notre propre système d'aide
        )
        self.config = Config
        self.perm_manager = PermissionManager("data/permissions.json")
        self.warns_manager = WarnsManager("data/warns.json")
        self.database_ready = False

    async def setup_hook(self):
        logger.info("🔄 Démarrage du bot...")
        
        # Initialiser la base de données globale
        await db_manager.init_global_database()
        self.database_ready = True
        logger.info("✅ Base de données globale initialisée")
        
        self.warns_manager.set_bot(self)
        # Utiliser le nouveau système de chargement des cogs
        await load_cogs(self)

    async def on_guild_join(self, guild):
        """Gestion de l'ajout à un nouveau serveur avec initialisation passive de la DB"""
        logger.info(f"📥 Invité sur le serveur: {guild.name} ({guild.id})")
        
        # Vérifier les permissions d'accès
        if not await AccessManager.check_guild_access(guild):
            logger.warning(f"🚫 Serveur {guild.name} ({guild.id}) non autorisé - Départ automatique")
            try:
                owner = guild.owner
                if owner:
                    embed = discord.Embed(
                        title="🚫 Accès refusé",
                        description="Ce serveur n'est pas autorisé à utiliser ce bot.",
                        color=discord.Color.red()
                    )
                    embed.add_field(
                        name="Pour demander l'accès",
                        value="Contactez les développeurs du bot",
                        inline=False
                    )
                    await owner.send(embed=embed)
            except:
                pass
            
            await guild.leave()
            return
        
        # Initialisation passive : enregistrer le serveur et créer sa DB automatiquement
        await db_manager.register_guild(guild.id, guild.name)
        
        # Migrer les anciennes données si elles existent
        await migration_manager.migrate_all_data(guild.id)
        
        logger.info(f"✅ Serveur {guild.name} enregistré avec sa base de données dédiée")

    async def on_guild_remove(self, guild):
        """Gestion du retrait d'un serveur"""
        logger.info(f"📤 Retiré du serveur: {guild.name} ({guild.id})")
        # Note: On garde la DB du serveur au cas où le bot reviendrait

    async def refresh_ticket_system(self):
        """Actualise le système de tickets pour appliquer la couleur actuelle des embeds"""
        try:
            ticket_cog = self.get_cog('tickets')
            if not ticket_cog:
                logger.warning("⚠️ Module de tickets non chargé")
                return False

            # Mettre à jour la couleur du ticket_cog depuis EmbedManager
            if hasattr(ticket_cog, 'color'):
                from utils.embed_manager import EmbedManager
                ticket_cog.color = EmbedManager.get_default_color()
                # Correction ici: utiliser .value pour accéder à la valeur de la couleur
                logger.info(f"✅ Couleur du cog tickets mise à jour: #{ticket_cog.color.value:06X}")

            # Utiliser la méthode refresh_ticket_message_on_startup si elle existe
            if hasattr(ticket_cog, 'refresh_ticket_message_on_startup'):
                result = await ticket_cog.refresh_ticket_message_on_startup()
                if result:
                    logger.info("✅ Message du système de tickets rafraîchi avec succès")
                    return True
                else:
                    logger.warning("⚠️ Échec du rafraîchissement du message de tickets")
                    return False

            # Approche manuelle si la méthode ci-dessus n'existe pas
            channel_id = getattr(ticket_cog, 'create_channel_id', None)
            if not channel_id:
                logger.warning("⚠️ ID du canal de tickets non configuré")
                return False

            channel = self.get_channel(channel_id)
            if not channel:
                logger.warning(f"⚠️ Canal de tickets introuvable (ID: {channel_id})")
                return False

            # Purger les anciens messages pour éviter les duplications
            await channel.purge(limit=5)

            # Créer un nouveau message avec le menu de création de tickets
            if hasattr(ticket_cog, 'create_ticket_embed') and hasattr(ticket_cog, 'TicketCreationView'):
                ticket_embed = ticket_cog.create_ticket_embed()
                # Vérifier qu'un constructeur de vue est disponible et l'instancier
                if ticket_cog.TicketCreationView.__module__ == 'cogs.events.ticket_system':
                    ticket_view = ticket_cog.TicketCreationView(ticket_cog)
                    ticket_message = await channel.send(embed=ticket_embed, view=ticket_view)
                else:
                    # Fallback si la classe n'est pas correctement importée
                    ticket_message = await channel.send(embed=ticket_embed)
                    logger.warning("⚠️ Vue des tickets non instanciée (classe non trouvée)")

                # Mettre à jour l'ID du message dans la configuration
                ticket_cog.ticket_message_id = ticket_message.id
                if hasattr(ticket_cog, 'save_config'):
                    ticket_cog.save_config()
                    logger.info(f"✅ Nouveau message de tickets créé et configuré (ID: {ticket_message.id})")
                    return True
                else:
                    logger.warning("⚠️ Méthode save_config non trouvée dans le cog des tickets")
                    return False
            else:
                logger.warning("⚠️ Méthodes nécessaires non trouvées dans le cog des tickets")
                return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'actualisation du système de tickets: {str(e)}")
            return False

    async def refresh_rules_system(self):
        """Actualise le système de règlement pour appliquer la couleur actuelle des embeds"""
        try:
            # Utiliser la méthode RulesManager existante
            result = await RulesManager.refresh_rules(self)
            
            # Actualiser également les règles pour chaque serveur
            rules_cog = self.get_cog('RulesCommands')
            if rules_cog:
                for guild in self.guilds:
                    await rules_cog.update_rules(guild)
                logger.info("✅ Règlement actualisé avec succès")
                return True
            else:
                logger.warning("⚠️ Module de règlement non chargé")
                return False if not result else True
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'actualisation du règlement: {str(e)}")
            return False

    async def refresh_roles_system(self):
        """Actualise le système de rôles pour appliquer la couleur actuelle des embeds"""
        try:
            roles_cog = self.get_cog('RoleManager')
            if not roles_cog:
                logger.warning("⚠️ Module de gestion des rôles non chargé")
                return False
                
            # Vérifier si le canal par défaut existe
            channel_id = getattr(roles_cog, 'default_channel_id', None)
            if not channel_id:
                logger.warning("⚠️ ID du canal des rôles non configuré")
                return False
                
            channel = self.get_channel(channel_id)
            if not channel:
                logger.warning(f"⚠️ Canal des rôles introuvable (ID: {channel_id})")
                return False
                
            # Supprimer les anciens messages de rôle
            try:
                async for message in channel.history(limit=10):
                    if message.author == self.user and message.embeds and "Choisissez vos rôles" in message.embeds[0].title:
                        await message.delete()
                        logger.info(f"🗑️ Ancien menu de rôles supprimé")
                        break
            except Exception as e:
                logger.error(f"❌ Erreur lors de la suppression de l'ancien menu de rôles: {str(e)}")
            
            # Envoyer un nouveau menu
            await roles_cog.send_role_menu()
            logger.info("✅ Menu des rôles actualisé avec succès")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'actualisation du système de rôles: {str(e)}")
            return False

    async def on_ready(self):
        # Définir le statut une fois que le bot est prêt
        await self.change_presence(activity=discord.Game(name="Vive la mathysie ! 🔈 URaaa"))
        
        # Initialize colors from saved settings
        Config.initialize_colors()
        print(f"🎨 Loaded embed color: #{Config.DEFAULT_COLOR:06X}")
        
        # Initialisation passive : enregistrer tous les serveurs actuels avec leurs DB
        logger.info(f"🔄 Initialisation passive des bases de données pour {len(self.guilds)} serveurs")
        for guild in self.guilds:
            await db_manager.register_guild(guild.id, guild.name)
            # Migrer les données existantes pour chaque serveur
            await migration_manager.migrate_all_data(guild.id)
        
        logger.info(f"✅ Toutes les bases de données serveur sont prêtes")
        
        # Vérifier que le module ColorAnalyzer est chargé
        color_cog = self.get_cog('ColorAnalyzer')
        if color_cog:
            logger.info("🎨 Module d'analyse de couleurs chargé avec succès")
        else:
            logger.warning("⚠️ Module d'analyse de couleurs non chargé")

        # Rafraîchir le message des règles au démarrage
        try:
            await RulesManager.refresh_rules(self)
            rules_cog = self.get_cog('RulesCommands')
            if rules_cog:
                for guild in self.guilds:
                    await rules_cog.update_rules(guild)
            logger.info("📜 Messages des règles rafraîchis")
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement des règles: {str(e)}")
        
        # Rafraîchir le message du système de tickets au démarrage
        try:
            ticket_cog = self.get_cog('tickets')
            if ticket_cog and hasattr(ticket_cog, 'refresh_ticket_message_on_startup'):
                await ticket_cog.refresh_ticket_message_on_startup()
                logger.info("🎫 Message du système de tickets rafraîchi")
            elif ticket_cog:
                # Méthode alternative si refresh_ticket_message_on_startup n'existe pas
                channel_id = getattr(ticket_cog, 'create_channel_id', None)
                message_id = getattr(ticket_cog, 'ticket_message_id', None)
                
                if channel_id and message_id:
                    channel = self.get_channel(channel_id)
                    if channel:
                        try:
                            # Tenter de récupérer et mettre à jour le message existant
                            message = await channel.fetch_message(message_id)
                            if hasattr(ticket_cog, 'create_ticket_embed') and hasattr(ticket_cog, 'TicketCreationView'):
                                await message.edit(
                                    embed=ticket_cog.create_ticket_embed(),
                                    view=ticket_cog.TicketCreationView(ticket_cog)
                                )
                                logger.info("🎫 Message du système de tickets mis à jour")
                            else:
                                logger.warning("⚠️ Fonctions nécessaires non trouvées dans le cog des tickets")
                        except discord.NotFound:
                            # Message non trouvé, en créer un nouveau
                            logger.warning("⚠️ Message de tickets non trouvé, création d'un nouveau message")
                            if hasattr(ticket_cog, 'setup_tickets'):
                                # Utiliser la méthode de configuration directement
                                ticket_channel = self.get_channel(channel_id)
                                if ticket_channel:
                                    async for message in ticket_channel.history(limit=10):
                                        if message.author == self.user:
                                            await message.delete()
                                            await asyncio.sleep(0.5)
                                    
                                    if hasattr(ticket_cog, 'create_ticket_embed') and hasattr(ticket_cog, 'TicketCreationView'):
                                        new_message = await ticket_channel.send(
                                            embed=ticket_cog.create_ticket_embed(),
                                            view=ticket_cog.TicketCreationView(ticket_cog)
                                        )
                                        ticket_cog.ticket_message_id = new_message.id
                                        ticket_cog.save_config()
                                        logger.info(f"🎫 Nouveau message de tickets créé (ID: {new_message.id})")
                            else:
                                logger.warning("⚠️ Méthode setup_tickets non trouvée")
                    else:
                        logger.warning(f"⚠️ Canal de tickets non trouvé (ID: {channel_id})")
                else:
                    logger.warning("⚠️ IDs du canal ou du message de tickets non configurés")
            else:
                logger.warning("⚠️ Module de tickets non chargé")
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement du message de tickets: {str(e)}")
        
        logger.info(f"🟢 Connecté en tant que {self.user}")
        logger.info(f"🔗 Connecté sur {len(self.guilds)} serveurs avec bases indépendantes")

    async def on_command(self, ctx):
        logger.info(f"📜 Commande '{ctx.command}' utilisée par {ctx.author}")

    async def on_command_error(self, ctx, error):
        logger.error(f"❌ Erreur commande '{ctx.command}': {str(error)}")

    async def on_disconnect(self):
        logger.warning("🔴 Bot déconnecté")

if __name__ == "__main__":
    try:
        # Vérifier que les dossiers nécessaires existent
        os.makedirs("cogs/commands", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Vérification plus robuste du token
        if not Config.TOKEN or not Config.TOKEN.strip():
            logger.critical("❌ Le token Discord n'est pas configuré dans le fichier .env")
            print("ERREUR: Aucun token Discord trouvé. Veuillez créer un fichier .env avec DISCORD_BOT_TOKEN=votre_token")
            exit(1)
            
        # Vérification de format basique
        if not (Config.TOKEN.startswith(('MT', 'NT', 'OT')) and len(Config.TOKEN) > 50):
            logger.warning("⚠️ Le format du token Discord semble incorrect - vérifiez votre token")
        
        # Vérifier que le fichier mcstarter.py existe
        mcstarter_path = "cogs/commands/mcstarter.py"
        if not os.path.exists(mcstarter_path):
            logger.warning(f"Le fichier {mcstarter_path} n'existe pas. Utilisez la commande 'mcstarter' pour activer le démarrage automatique.")
        
        try:
            # Lancer la vérification de configuration avant de démarrer
            Config.check_config()
            
            bot = MathysieBot()
            bot.run(Config.TOKEN)
        except ValueError as config_error:
            logger.critical(f"❌ Erreur de configuration: {str(config_error)}")
            print(f"ERREUR DE CONFIGURATION: {str(config_error)}")
            exit(1)
        except discord.errors.LoginFailure as login_error:
            logger.critical(f"❌ Échec d'authentification Discord: {str(login_error)}")
            print("ERREUR D'AUTHENTIFICATION: Votre token Discord est invalide ou a été révoqué.")
            print("Veuillez vérifier votre token ou en générer un nouveau sur le portail développeur Discord.")
            exit(1)
    except AttributeError:
        logger.critical("❌ La variable TOKEN n'existe pas dans config.py")
        exit(1)
    except Exception as e:
        logger.critical(f"❌ Erreur inattendue: {str(e)}")
        import traceback
        traceback.print_exc()  # Afficher la stack trace complète pour un meilleur débogage
        exit(1)