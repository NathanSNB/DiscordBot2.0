import discord
from discord.ext import commands
from discord import ui
from mcstatus import JavaServer
import socket
import asyncio
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import pytz  # Pour gérer les fuseaux horaires
import re
import json
from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

# Bouton de rafraîchissement personnalisé
class RefreshButton(ui.Button):
    def __init__(self, tracker):
        super().__init__(style=discord.ButtonStyle.primary, emoji="🔄", label="Actualiser")
        self.tracker = tracker
    
    async def callback(self, interaction):
        # Indiquer que le bot traite la demande
        await interaction.response.defer()
        
        # Obtenir le nouvel embed de statut
        current_status, embed, player_count, current_player_list = await self.tracker.get_status_embed()
        
        # Mettre à jour le message avec le nouvel embed et le bouton
        view = ui.View()
        view.add_item(RefreshButton(self.tracker))
        view.timeout = None  # Le bouton ne disparaît pas
        
        await interaction.followup.edit_message(
            message_id=interaction.message.id,
            embed=embed,
            view=view
        )

class MCStatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Centraliser la configuration
        self.load_config()
        self.status_message = None
        self.previous_player_count = 0
        self.previous_player_list = []
        self.previous_server_status = None
        self.error_messages = []
        self.player_notify_messages = []
        self.previous_latency = 0  
        self.high_latency_threshold = 200
        self.critical_latency_threshold = 500
        
        # Ajout d'un compteur pour les mises à jour horaires
        self.hourly_update_counter = 0
        
        # Créer une tâche asynchrone pour le suivi du serveur
        self.server_tracker = None
        bot.loop.create_task(self.initialize_status_message())
        
    def load_config(self):
        """Charge la configuration depuis le JSON"""
        try:
            with open('data/user_preferences.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                mc_config = config.get('minecraft', {})
                self.SERVER_IP = mc_config.get('server', {}).get('ip', 'localhost')
                self.PORT = int(mc_config.get('server', {}).get('port', '25565'))
                self.STATUS_CHANNEL_ID = int(mc_config.get('discord', {}).get('statusChannelId', '0'))
                self.NOTIFICATION_ROLE_ID = int(mc_config.get('discord', {}).get('notificationRoleId', '0'))
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de la configuration: {e}")
            self.SERVER_IP = 'localhost'
            self.PORT = 25565
            self.STATUS_CHANNEL_ID = 0 
            self.NOTIFICATION_ROLE_ID = 0
            
    def reload_config(self):
        """Recharge la configuration et replace le message de statut dans le bon salon si besoin"""
        old_channel_id = self.STATUS_CHANNEL_ID
        self.load_config()
        # Si le salon a changé, réinitialiser le message de statut dans le bon salon
        if old_channel_id != self.STATUS_CHANNEL_ID:
            self.status_message = None
            self.bot.loop.create_task(self.find_or_create_status_message())
        else:
            # Toujours s'assurer que le message est dans le bon salon
            self.bot.loop.create_task(self.find_or_create_status_message())
    
    def get_paris_time(self):
        """Renvoie l'heure actuelle dans le fuseau horaire de Paris, arrondie à la minute"""
        paris_tz = pytz.timezone('Europe/Paris')
        paris_time = datetime.now(paris_tz)
        # Supprimer les secondes et microsecondes pour arrondir à la minute
        paris_time = paris_time.replace(second=0, microsecond=0)
        return paris_time.strftime('%d/%m/%Y %H:%M')  # Format amélioré avec l'année
    
    async def initialize_status_message(self):
        """Initialise le message de statut au démarrage du bot"""
        await self.bot.wait_until_ready()
        await self.find_or_create_status_message()
        self.server_tracker = self.bot.loop.create_task(self.track_server_status())
    
    async def find_or_create_status_message(self):
        """Cherche un message de statut existant ou en crée un nouveau dans le salon configuré"""
        # Toujours recharger la config pour être sûr d'avoir le bon salon
        self.load_config()
        channel = self.bot.get_channel(self.STATUS_CHANNEL_ID)
        if not channel:
            logger.error(f"❌ Canal de statut introuvable (ID: {self.STATUS_CHANNEL_ID})")
            return

        # Nettoyer tous les anciens messages de statut dans tous les salons où le bot a accès
        # (pour éviter d'avoir plusieurs messages de statut dans plusieurs salons)
        for guild in self.bot.guilds:
            for ch in guild.text_channels:
                try:
                    async for message in ch.history(limit=50):
                        if message.author == self.bot.user and message.embeds and message.embeds[0].title.startswith("📊 Statut du serveur Minecraft"):
                            if ch.id != self.STATUS_CHANNEL_ID or self.status_message is None:
                                try:
                                    await message.delete()
                                    await asyncio.sleep(0.2)
                                except Exception:
                                    pass
                            else:
                                self.status_message = message
                except Exception:
                    continue

        # Chercher les messages du bot dans le salon cible
        bot_messages = []
        async for message in channel.history(limit=50):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title.startswith("📊 Statut du serveur Minecraft"):
                bot_messages.append(message)

        # Supprimer tous les messages du bot dans le canal sauf le plus récent
        if bot_messages:
            for i, message in enumerate(bot_messages):
                if i > 0:  # Garder le premier message (le plus récent)
                    try:
                        await message.delete()
                        await asyncio.sleep(0.2)
                    except Exception as e:
                        logger.error(f"Erreur lors de la suppression d'un message: {e}")

            # Utiliser le message le plus récent comme message de statut
            self.status_message = bot_messages[0]
            logger.info(f"✅ Message de statut existant trouvé (ID: {self.status_message.id}) dans le salon {channel.id}")

            # Ajouter le bouton de rafraîchissement
            view = ui.View()
            view.add_item(RefreshButton(self))
            view.timeout = None

            # Mise à jour initiale
            current_status, embed, player_count, current_player_list = await self.get_status_embed()
            await self.status_message.edit(embed=embed, view=view)
        else:
            # Créer un nouveau message si aucun n'existe
            embed = EmbedManager.create_embed(
                title="📊 Statut du serveur Minecraft",
                description="🔄 **Initialisation du statut...**\nVeuillez patienter pendant que je vérifie le serveur.",
                color=discord.Color.blue()  # Couleur spécifique pour le statut
            )

            # Ajouter le bouton de rafraîchissement
            view = ui.View()
            view.add_item(RefreshButton(self))
            view.timeout = None

            self.status_message = await channel.send(embed=embed, view=view)
            logger.info(f"✅ Nouveau message de statut créé (ID: {self.status_message.id}) dans le salon {channel.id}")
    
    async def track_server_status(self):
        """Suit le statut du serveur en continu"""
        try:
            channel = self.bot.get_channel(self.STATUS_CHANNEL_ID)
            if not channel:
                logger.error(f"❌ Canal de statut introuvable (ID: {self.STATUS_CHANNEL_ID})")
                return
                
            # Vérifier que le message de statut existe
            if not self.status_message:
                await self.find_or_create_status_message()
            
            # Première vérification pour initialiser l'état
            current_status, embed, player_count, current_player_list = await self.get_status_embed()
            
            # Ajouter le bouton de rafraîchissement
            view = ui.View()
            view.add_item(RefreshButton(self))
            view.timeout = None
            
            await self.status_message.edit(embed=embed, view=view)
            self.previous_server_status = current_status
            self.previous_player_count = player_count
            self.previous_player_list = current_player_list
            
            while not self.bot.is_closed():
                current_status, embed, player_count, current_player_list = await self.get_status_embed()
                
                # Déterminer s'il faut mettre à jour le message
                state_changed = current_status != self.previous_server_status
                new_players = self.detect_new_players(current_player_list)
                left_players = self.detect_left_players(current_player_list)
                players_changed = len(current_player_list) != len(self.previous_player_list)
                
                # Mettre à jour le compteur pour les mises à jour horaires (60 itérations * 60 secondes = 1 heure)
                self.hourly_update_counter += 1
                hourly_update = self.hourly_update_counter >= 60
                if hourly_update:
                    self.hourly_update_counter = 0
                
                # Vérification de latence
                latency_spike = False
                current_latency = 0
                
                if hasattr(embed, 'fields'):
                    for field in embed.fields:
                        if field.name == "📶 Latence":
                            # Extraire la valeur de latence de la chaîne
                            match = re.search(r'(\d+(\.\d+)?)', field.value)
                            if match:
                                current_latency = float(match.group(1))
                                # Détecter si c'est un pic de latence ou changement significatif
                                if self.previous_latency > 0:
                                    latency_change = abs(current_latency - self.previous_latency)
                                    
                                    # Critères de déclenchement de mise à jour pour la latence:
                                    latency_spike = (
                                        (latency_change > 100) or 
                                        (self.previous_latency > 100 and latency_change / self.previous_latency > 0.3) or
                                        (current_latency > self.critical_latency_threshold)
                                    )
                                    
                                    if latency_spike:
                                        logger.warning(f"⚠️ Changement de latence important: {self.previous_latency}ms → {current_latency}ms")
                                
                                # Mettre à jour la latence précédente
                                self.previous_latency = current_latency
                
                # Mettre à jour le message si :
                # - l'état du serveur a changé
                # - un joueur a rejoint ou quitté
                # - il y a un pic de latence
                # - c'est l'heure de la mise à jour périodique (toutes les heures)
                player_activity = new_players or left_players or players_changed
                update_needed = state_changed or player_activity or latency_spike or hourly_update
                
                if update_needed:
                    # Notifier des changements d'état
                    if state_changed:
                        await self.notify_status_change(channel, current_status)
                    
                    # Notifier des nouveaux joueurs avec des popups éphémères
                    if new_players and current_status:
                        await self.notify_new_players(channel, new_players, player_count)
                        logger.info(f"👋 Joueurs connectés: {', '.join(new_players)} - Mise à jour du statut")
                        
                    # Notifier des joueurs déconnectés avec des popups éphémères
                    if left_players and current_status:
                        await self.notify_left_players(channel, left_players, player_count)
                        logger.info(f"👋 Joueurs déconnectés: {', '.join(left_players)} - Mise à jour du statut")
                    
                    # Garantir que le message de statut principal est toujours à jour
                    try:
                        # Ajouter le bouton de rafraîchissement
                        view = ui.View()
                        view.add_item(RefreshButton(self))
                        view.timeout = None
                        
                        # Mettre à jour l'embed pour refléter les nouveaux joueurs et ceux qui sont partis
                        if player_activity:
                            # Mettre à jour l'embed pour refléter le changement de joueurs
                            current_status, embed, player_count, current_player_list = await self.get_status_embed()
                        
                        # Essayer de mettre à jour le message existant
                        await self.status_message.edit(embed=embed, view=view)
                        
                        # Journalisation des mises à jour
                        if player_activity:
                            logger.info("✅ Message de statut mis à jour avec les changements de joueurs")
                        elif hourly_update:
                            logger.info("⏱️ Mise à jour horaire du statut effectuée")
                            
                    except discord.NotFound:
                        # Le message a été supprimé, en créer un nouveau
                        logger.warning("⚠️ Message de statut non trouvé, création d'un nouveau message")
                        view = ui.View()
                        view.add_item(RefreshButton(self))
                        view.timeout = None
                        self.status_message = await channel.send(embed=embed, view=view)
                    except Exception as e:
                        # Autre erreur, créer un nouveau message
                        logger.error(f"❌ Erreur lors de la mise à jour du message: {str(e)}")
                        try:
                            view = ui.View()
                            view.add_item(RefreshButton(self))
                            view.timeout = None
                            self.status_message = await channel.send(embed=embed, view=view)
                        except Exception as e2:
                            logger.error(f"❌ Erreur lors de la création d'un nouveau message: {str(e2)}")
                    
                    # Supprimer les messages d'erreur si le serveur est en ligne après une déconnexion
                    if current_status and self.previous_server_status is False and self.error_messages:
                        await self.clean_error_messages(channel)
                
                # Mettre à jour les valeurs précédentes
                self.previous_server_status = current_status
                self.previous_player_count = player_count
                self.previous_player_list = current_player_list
                
                # Réduire l'intervalle de vérification si joueurs changent fréquemment
                check_interval = 15 if player_activity else (30 if latency_spike else 60)
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"❌ Erreur dans le tracker: {str(e)}")
            if self.server_tracker:
                self.server_tracker.cancel()
            # Redémarrer le tracker après une erreur
            await asyncio.sleep(30)
            self.server_tracker = self.bot.loop.create_task(self.track_server_status())
    
    def detect_new_players(self, current_player_list):
        """Détecte les nouveaux joueurs qui se sont connectés"""
        new_players = []
        for player in current_player_list:
            if player not in self.previous_player_list:
                new_players.append(player)
        return new_players
    
    def detect_left_players(self, current_player_list):
        """Détecte les joueurs qui se sont déconnectés"""
        left_players = []
        for player in self.previous_player_list:
            if player not in current_player_list:
                left_players.append(player)
        return left_players
    
    async def notify_new_players(self, channel, new_players, total_players):
        """Notifie lorsque de nouveaux joueurs rejoignent le serveur"""
        if new_players:
            # Création d'un embed pour l'annonce des nouveaux joueurs
            embed = discord.Embed(
                title="🎮 Nouveaux joueurs connectés!",
                description=f"De nouveaux joueurs ont rejoint le serveur Minecraft.",
                color=discord.Color.gold()
            )
            
            # Listing des nouveaux joueurs
            players_text = ", ".join(f"**{player}**" for player in new_players)
            embed.add_field(
                name="🧙‍♂️ Qui a rejoint",
                value=players_text,
                inline=False
            )
            
            # Information sur le nombre total de joueurs
            embed.add_field(
                name="👥 Total de joueurs",
                value=f"**{total_players}** joueurs en ligne actuellement",
                inline=False
            )
            
            # Ajouter l'heure de connexion
            embed.set_footer(text=f"Connecté(s) à {self.get_paris_time()} (heure de Paris)")
            
            # Envoyer l'annonce
            msg = await channel.send(embed=embed)
            self.player_notify_messages.append(msg.id)
            
            # Programmer la suppression du message après 2 minutes
            await asyncio.sleep(60)  # 1 minutes
            try:
                await msg.delete()
                # Supprimer l'ID du message de la liste des messages à nettoyer
                if msg.id in self.player_notify_messages:
                    self.player_notify_messages.remove(msg.id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass  # Ignorer si le message a déjà été supprimé ou si on n'a pas les permissions

    async def notify_left_players(self, channel, left_players, total_players):
        """Notifie lorsque des joueurs quittent le serveur"""
        if left_players:
            # Création d'un embed pour l'annonce des joueurs déconnectés
            embed = discord.Embed(
                title="👋 Joueurs déconnectés",
                description=f"Des joueurs ont quitté le serveur Minecraft.",
                color=discord.Color.orange()
            )
            
            # Listing des joueurs déconnectés
            players_text = ", ".join(f"**{player}**" for player in left_players)
            embed.add_field(
                name="🚶‍♂️ Qui a quitté",
                value=players_text,
                inline=False
            )
            
            # Information sur le nombre total de joueurs
            embed.add_field(
                name="👥 Total de joueurs",
                value=f"**{total_players}** joueurs en ligne actuellement",
                inline=False
            )
            
            # Ajouter l'heure de déconnexion
            embed.set_footer(text=f"Déconnecté(s) à {self.get_paris_time()} (heure de Paris)")
            
            # Envoyer l'annonce
            msg = await channel.send(embed=embed)
            self.player_notify_messages.append(msg.id)
            
            # Programmer la suppression du message après 2 minutes
            await asyncio.sleep(120)  # 2 minutes
            try:
                await msg.delete()
                # Supprimer l'ID du message de la liste des messages à nettoyer
                if msg.id in self.player_notify_messages:
                    self.player_notify_messages.remove(msg.id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass  # Ignorer si le message a déjà été supprimé ou si on n'a pas les permissions

    async def clean_error_messages(self, channel):
        """Supprime les messages d'erreur précédents"""
        try:
            for msg_id in self.error_messages:
                try:
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                except discord.NotFound:
                    pass  # Message déjà supprimé
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression du message: {e}")
            
            self.error_messages = []  # Réinitialiser la liste des messages d'erreur
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des messages: {e}")

    async def clean_player_notify_messages(self, channel):
        """Supprime les messages de notification de nouveaux joueurs"""
        try:
            for msg_id in self.player_notify_messages:
                try:
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                except discord.NotFound:
                    pass
                except Exception as e:
                    logger.error(f"Erreur lors de la suppression d'une notif joueur: {e}")
            self.player_notify_messages = []
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des notifs joueurs: {e}")

    async def notify_status_change(self, channel, current_status):
        """Notifie les changements d'état du serveur"""
        if self.previous_server_status is None:
            # Premier état détecté, juste enregistrer
            self.previous_server_status = current_status
            return
        
        # Vérifier si l'état a changé
        if current_status != self.previous_server_status:
            # S'assurer que le rôle est mentionné correctement
            role_mention = f"<@&{self.NOTIFICATION_ROLE_ID}>"
            
            if current_status:
                # Le serveur est revenu en ligne - créer un embed
                embed = discord.Embed(
                    title="🟢 Serveur Minecraft EN LIGNE!",
                    description=f"Le serveur est à nouveau accessible!\n\n**Adresse:** `{self.SERVER_IP}`",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Serveur en ligne depuis {self.get_paris_time()} (heure de Paris)")
                
                # Envoyer la notification avec le rôle mentionné
                status_msg = await channel.send(content=role_mention, embed=embed)
                self.error_messages.append(status_msg.id)  # Pour pouvoir le supprimer plus tard si besoin
                
                # Ne pas supprimer les notifications d'état en ligne
            else:
                # Le serveur est tombé hors ligne - créer un embed
                embed = discord.Embed(
                    title="🔴 Serveur Minecraft HORS LIGNE!",
                    description="Le serveur n'est plus accessible. Une notification sera envoyée dès que le serveur sera de nouveau en ligne.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Hors ligne depuis {self.get_paris_time()} (heure de Paris)")
                
                # Envoyer la notification avec le rôle mentionné
                status_msg = await channel.send(content=role_mention, embed=embed)
                self.error_messages.append(status_msg.id)
                
                # Ne pas supprimer les notifications de hors ligne

    def detect_server_type(self, version_name, motd=None):
        """Détecte le type de serveur à partir de la version et du motd"""
        # Détection basée sur le nom de version
        version_lower = version_name.lower() if version_name else ""
        
        # Détection des types de serveur courants
        version_lower = version_lower.lower()  # Assure que c'est en minuscule

        if "fabric"or "Fabric" in version_lower:
            return "🧵 Fabric"
        elif "quilt"or "Quilt" in version_lower:
            return "🪡 Quilt (fork de Fabric)"
        elif "forge" or "Forge"in version_lower or "fml" in version_lower:
            return "🔨 Forge"
        elif "neoforge"or "Neoforge" in version_lower:
            return "🧱 NeoForge (fork de Forge)"
        elif "paper"or "Paper" in version_lower:
            return "📝 Paper"
        elif "purpur"or "Purpur" in version_lower:
            return "🟣 Purpur (fork de Paper)"
        elif "pufferfish"or "Pufferfish" in version_lower:
            return "🐡 Pufferfish (optimisé Paper)"
        elif "airplane"or "Airplane" in version_lower:
            return "✈️ Airplane (fork de Paper)"
        elif "spigot" or "Spigot" in version_lower:
            return "🔌 Spigot"
        elif "taco" or "Taco"in version_lower:
            return "🌮 TacoSpigot (optimisé Spigot)"
        elif "bukkit" or "Bukkit"in version_lower:
            return "🪣 Bukkit"
        elif "sponge"or "Sponge" in version_lower:
            return "🧽 Sponge"
        elif "mohist"or "Mohist" in version_lower:
            return "⚙️ Mohist (Forge + Bukkit)"
        elif "catserver" or "Catserver" in version_lower:
            return "🐱 CatServer (Forge + Bukkit)"
        elif "arclight"or "Arclight" in version_lower:
            return "💡 Arclight (Forge + Bukkit)"
        elif "magma"or "Magma" in version_lower:
            return "🔥 Magma (Forge + Bukkit)"
        elif "vanilla"or "Vanilla" in version_lower:
            return "🍦 Vanilla"
        elif "cuberite"or "Cuberite" in version_lower:
            return "🧊 Cuberite (C++ vanilla-like)"
        elif "velocity"or "Velocity" in version_lower:
            return "⚡ Velocity (proxy)"
        elif "waterfall"or "Waterfall" in version_lower:
            return "💧 Waterfall (proxy)"
        elif "travertine"or "Travertine" in version_lower:
            return "⛲ Travertine (proxy)"
        elif "bungeecord"or "Bungeecord"  in version_lower or "bungee"or "Bungee"  in version_lower:
            return "🔀 BungeeCord (proxy)"
        elif "modded" in version_lower or "mod"or "Mod"or "Modded" in version_lower:
            return "🔧 Modded"
        else:
            return "❔ Inconnu ou Vanilla"

    async def get_status_embed(self):
        """Obtient l'embed de statut actuel et retourne également l'état du serveur"""
        try:
            # Test de résolution DNS
            try:
                ip = socket.gethostbyname(self.SERVER_IP)
            except socket.gaierror:
                raise ConnectionError("Serveur hors ligne")

            # Test de connexion au serveur
            server = JavaServer(ip, self.PORT)
            status = server.status()
            
            # Liste des joueurs connectés
            current_player_list = []
            if status.players.online > 0 and hasattr(status.players, 'sample'):
                current_player_list = [p.name for p in status.players.sample]

            # Détection du type de serveur
            server_type = self.detect_server_type(status.version.name, 
                                                 getattr(status, 'description', None))
            
            # Création de l'embed avec les infos
            embed = discord.Embed(
                title="📊 Statut du serveur Minecraft",
                description=f"**🟢 EN LIGNE**",
                color=EmbedManager.get_default_color()
            )
            
            # Informations sur la version avec le type de serveur
            embed.add_field(
                name="🛠️ Version",
                value=f"{server_type}\n{status.version.name}",
                inline=False
            )
            
            # Informations principales dans les champs
            embed.add_field(
                name="📡 Adresse",
                value=f"`{self.SERVER_IP}:{self.PORT}`",
                inline=True
            )
            
            # Affichage des joueurs avec émoji
            player_status = f"**{status.players.online}** / **{status.players.max}**"
            embed.add_field(
                name="👥 Joueurs",
                value=player_status,
                inline=True
            )
            
            # Affichage de la latence avec code couleur
            latency = round(status.latency, 2)
            if latency < 100:
                latency_emoji = "🟢"  # Bon
                latency_status = "Excellente"
            elif latency < 200:
                latency_emoji = "🟡"  # Moyen
                latency_status = "Bonne"
            elif latency < 500:
                latency_emoji = "🟠"  # Élevé
                latency_status = "Élevée"
            else:
                latency_emoji = "🔴"  # Critique
                latency_status = "Critique"
                
            embed.add_field(
                name="📶 Latence",
                value=f"{latency_emoji} **{latency}** ms ({latency_status})",
                inline=True
            )

            # Ajout des joueurs connectés si présents
            if status.players.online > 0 and hasattr(status.players, 'sample'):
                # Trier les joueurs par ordre alphabétique
                sorted_players = sorted([p.name for p in status.players.sample])
                
                # Afficher les joueurs avec un style plus élégant
                if len(sorted_players) <= 10:  # Si moins de 10 joueurs, afficher avec des emoji
                    players_display = "\n".join(f"🎮 **{p}**" for p in sorted_players)
                else:  # Si plus de 10 joueurs, afficher en colonnes
                    players_display = ", ".join(f"**{p}**" for p in sorted_players)
                    
                embed.add_field(
                    name=f"🎲 Joueurs en ligne ({status.players.online})",
                    value=players_display or "Aucun joueur",
                    inline=False
                )
            
            # Ajouter une date de mise à jour avec l'heure de Paris
            paris_time = self.get_paris_time()
            embed.set_footer(
                text=f"Dernière mise à jour: {paris_time}"
            )
            
            return True, embed, status.players.online, current_player_list  # True = serveur en ligne

        except Exception as e:
            # Enregistrer l'erreur dans les logs, mais ne pas l'afficher à l'utilisateur
            logger.error(f"❌ Erreur MCStatus: {str(e)}")
            
            # Créer un embed pour serveur hors ligne
            embed = discord.Embed(
                title="📊 Statut du serveur Minecraft",
                description="**🔴 HORS LIGNE**\n\nLe serveur n'est pas accessible actuellement.",
                color=discord.Color.red()  # Garder une couleur spécifique pour l'état hors ligne
            )
            
            # Ajouter l'adresse du serveur
            embed.add_field(
                name="📡 Adresse",
                value=f"`{self.SERVER_IP}`",
                inline=True
            )
            
            # Tentative de reconnexion
            embed.add_field(
                name="⏱️ Prochaine vérification",
                value="Dans 1 minute",
                inline=True
            )
            
            # Ajouter une date de mise à jour avec l'heure de Paris
            paris_time = self.get_paris_time()
            embed.set_footer(
                text=f"Dernière vérification: {paris_time}"
            )
            
            return False, embed, 0, []  # False = serveur hors ligne

    async def clean_status_messages(self, channel):
        """Nettoie les messages de statut précédents du bot dans le canal"""
        try:
            # Chercher les messages du bot dans les 100 derniers messages
            async for message in channel.history(limit=100):
                if message.author == self.bot.user:
                    # Vérifier si c'est un message de statut (avec embed)
                    if message.embeds and (
                        "Statut du serveur Minecraft" in message.embeds[0].title
                    ):
                        try:
                            await message.delete()
                            await asyncio.sleep(0.5)  # Éviter le rate limiting
                        except Exception as e:
                            logger.error(f"Erreur lors de la suppression d'un message de statut: {e}")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des messages de statut: {e}")

async def setup(bot):
    await bot.add_cog(MCStatusTracker(bot))