import discord
from discord.ext import commands
import logging
import asyncio
import json
import os
from datetime import datetime

from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

# Classe pour le menu déroulant de création de ticket
class TicketCreationView(discord.ui.View):
    def __init__(self, ticket_cog):
        super().__init__(timeout=None)
        self.ticket_cog = ticket_cog
        self.add_item(TicketReasonSelect(self.ticket_cog))

class TicketReasonSelect(discord.ui.Select):
    def __init__(self, ticket_cog):
        self.ticket_cog = ticket_cog
        options = []
        
        # Ajouter l'option "choisir" par défaut qui n'ouvre pas de ticket
        options.append(
            discord.SelectOption(
                label="Choisir", 
                value="no_action",
                description="Sélectionnez une option pour créer un ticket",
                default=True
            )
        )
        
        # Utiliser les raisons configurées ou des raisons par défaut si aucune n'est configurée
        reasons = ticket_cog.ticket_reasons if ticket_cog.ticket_reasons else [
            {"label": "Assistance générale", "emoji": "❓", "description": "Demande d'aide générale"},
            {"label": "Signalement", "emoji": "🚨", "description": "Signaler un problème"},
            {"label": "Suggestion", "emoji": "💡", "description": "Proposer une idée ou suggestion"},
            {"label": "Autre", "emoji": "📝", "description": "Autre demande"}
        ]
        
        for reason in reasons:
            options.append(
                discord.SelectOption(
                    label=reason["label"], 
                    emoji=reason.get("emoji"), 
                    description=reason.get("description", "")[:100]
                )
            )
        
        super().__init__(
            placeholder="Sélectionnez la raison de votre ticket...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_reason_select"
        )
    
    async def callback(self, interaction: discord.Interaction):
        try:
            # Vérifier si l'option sélectionnée est l'option "choisir"
            if self.values[0] == "no_action":
                # Ne rien faire, juste accuser réception de l'interaction
                await interaction.response.defer()
                return
                
            # Obtenir la raison sélectionnée
            reason = self.values[0]
            # Créer le ticket avec cette raison
            await self.ticket_cog.handle_ticket_creation_with_reason(interaction, reason)
            
            # Après traitement, réinitialiser le menu pour les futures interactions
            # Récupérer le canal et le message original
            channel = self.ticket_cog.bot.get_channel(self.ticket_cog.create_channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(self.ticket_cog.ticket_message_id)
                    # Recréer la vue avec le menu réinitialisé
                    new_view = TicketCreationView(self.ticket_cog)
                    await message.edit(view=new_view)
                except discord.NotFound:
                    logger.warning("⚠️ Message de tickets non trouvé lors de la réinitialisation du menu.")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la réinitialisation du menu: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Erreur dans le callback du menu de tickets: {str(e)}")

# Ajouter cette classe pour les boutons d'interaction dans les logs
class TicketLogView(discord.ui.View):
    def __init__(self, ticket_cog, ticket_id):
        super().__init__(timeout=None)  # Vue persistante
        self.ticket_cog = ticket_cog
        self.ticket_id = ticket_id
        
    @discord.ui.button(label="Voir le contenu", style=discord.ButtonStyle.primary, emoji="📝", custom_id="view_ticket_content")
    async def view_content_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Permet de voir le contenu d'un ticket archivé directement depuis les logs"""
        # Vérifier que l'utilisateur est administrateur
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Vous n'avez pas la permission de voir le contenu des tickets archivés.", ephemeral=True)
            return
            
        if self.ticket_id not in self.ticket_cog.archived_tickets:
            await interaction.response.send_message("❌ Ce ticket n'existe plus dans les archives.", ephemeral=True)
            return
            
        ticket_data = self.ticket_cog.archived_tickets[self.ticket_id]
        
        # Afficher les informations du ticket dans un embed
        embed = EmbedManager.create_embed(
            title=f"📁 Contenu du ticket: {self.ticket_id}",
            description=f"Nom original: {ticket_data['name']}\nSujet: {ticket_data.get('topic', 'Non défini')}"
        )
        
        # Ajouter les métadonnées
        archived_at = datetime.fromisoformat(ticket_data["archived_at"])
        owner_id = ticket_data["owner"]
        archived_by_id = ticket_data["archived_by"]
        close_reason = ticket_data.get("close_reason", "Non spécifiée")
        
        owner = interaction.guild.get_member(owner_id) or f"Utilisateur (ID: {owner_id})"
        archived_by = interaction.guild.get_member(archived_by_id) or f"Administrateur (ID: {archived_by_id})"
        
        embed.add_field(name="Créé par", value=str(owner), inline=True)
        embed.add_field(name="Archivé par", value=str(archived_by), inline=True)
        embed.add_field(name="Archivé le", value=archived_at.strftime("%d/%m/%Y à %H:%M"), inline=True)
        embed.add_field(name="Raison de fermeture", value=close_reason, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Envoyer les messages en privé pour éviter de polluer le canal
        messages = ticket_data.get("messages", [])
        if not messages:
            await interaction.followup.send("❌ Aucun message trouvé dans ce ticket.", ephemeral=True)
            return
            
        # Diviser les messages en groupes pour respecter les limites
        message_chunks = []
        current_chunk = "```\n"
        
        for msg in messages:
            timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%d/%m %H:%M")
            line = f"[{timestamp}] {msg['author']}: {msg['content'][:100]}"
            if len(msg['content']) > 100:
                line += "..."
            line += "\n"
            
            # Si ajouter cette ligne dépasse la limite, commencer un nouveau chunk
            if len(current_chunk) + len(line) > 1900:  # Limite de Discord moins une marge
                current_chunk += "```"
                message_chunks.append(current_chunk)
                current_chunk = "```\n"
                
            current_chunk += line
        
        # Ajouter le dernier chunk s'il n'est pas vide
        if current_chunk != "```\n":
            current_chunk += "```"
            message_chunks.append(current_chunk)
        
        # Envoyer les chunks
        for chunk in message_chunks:
            await interaction.followup.send(chunk, ephemeral=True)

class TicketSystem(commands.Cog, name="tickets"):
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}  # {channel_id: {"owner": user_id, "config_message": message_id}}
        self.archived_tickets = {}  # {ticket_id: {"owner": user_id, "archived_by": user_id, "archived_at": datetime, "messages": [...], "close_reason": str}}
        self.config_file = 'data/ticket_config.json'
        self.archive_file = 'data/archived_tickets.json'
        self.ticket_reasons = []  # Liste des raisons configurables pour les tickets
        self.color = EmbedManager.get_default_color()  # Utiliser la couleur par défaut du gestionnaire d'embeds
        self.load_config()
        self.load_archived_tickets()
        
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.ticket_category_id = config.get('category_id')
                    self.create_channel_id = config.get('create_channel_id')
                    self.log_channel_id = config.get('log_channel_id')
                    self.ticket_message_id = config.get('ticket_message_id')
                    self.archive_category_id = config.get('archive_category_id')
                    self.active_tickets = config.get('active_tickets', {})
                    self.ticket_reasons = config.get('ticket_reasons', [])
                    logger.info("✅ Configuration des tickets chargée")
            else:
                self.ticket_category_id = None
                self.create_channel_id = None
                self.log_channel_id = None
                self.ticket_message_id = None
                self.archive_category_id = None
                self.active_tickets = {}
                self.ticket_reasons = []
                logger.info("⚠️ Aucune configuration de tickets trouvée")
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de la configuration des tickets: {str(e)}")
            self.ticket_category_id = None
            self.create_channel_id = None
            self.log_channel_id = None
            self.ticket_message_id = None
            self.archive_category_id = None
            self.active_tickets = {}
            self.ticket_reasons = []
    
    def load_archived_tickets(self):
        """Charge les tickets archivés depuis le fichier JSON"""
        try:
            if os.path.exists(self.archive_file):
                with open(self.archive_file, 'r', encoding='utf-8') as f:
                    self.archived_tickets = json.load(f)
                    logger.info(f"✅ {len(self.archived_tickets)} tickets archivés chargés")
            else:
                self.archived_tickets = {}
                logger.info("⚠️ Aucun ticket archivé trouvé")
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des tickets archivés: {str(e)}")
            self.archived_tickets = {}
    
    def save_config(self):
        """Sauvegarde la configuration dans le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'category_id': self.ticket_category_id,
                    'create_channel_id': self.create_channel_id,
                    'log_channel_id': self.log_channel_id,
                    'ticket_message_id': self.ticket_message_id,
                    'archive_category_id': self.archive_category_id,
                    'active_tickets': self.active_tickets,
                    'ticket_reasons': self.ticket_reasons
                }, f, indent=4)
            logger.info("✅ Configuration des tickets sauvegardée")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la configuration des tickets: {str(e)}")

    def save_archived_tickets(self):
        """Sauvegarde les tickets archivés dans un fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.archive_file), exist_ok=True)
            with open(self.archive_file, 'w', encoding='utf-8') as f:
                json.dump(self.archived_tickets, f, indent=4)
            logger.info("✅ Tickets archivés sauvegardés")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des tickets archivés: {str(e)}")

    async def refresh_ticket_message_on_startup(self):
        """Rafraîchit le message de ticket au démarrage du bot"""
        try:
            # Vérifier si le canal et le message sont configurés
            if not self.create_channel_id or not hasattr(self, 'create_channel_id'):
                logger.warning("⚠️ Canal de tickets non configuré")
                return False
                
            channel = self.bot.get_channel(self.create_channel_id)
            if not channel:
                logger.warning(f"⚠️ Canal de tickets introuvable (ID: {self.create_channel_id})")
                return False
                
            # S'assurer que la couleur est à jour avec celle de l'EmbedManager
            self.color = EmbedManager.get_default_color()
            # Convertir la couleur en entier si ce n'est pas déjà fait
            if isinstance(self.color, discord.Color):
                self.color = self.color.value
            logger.info(f"✅ Couleur du système de tickets mise à jour: {hex(self.color)}")
                
            # Purger les anciens messages pour éviter les duplications
            await channel.purge(limit=5)
            
            # Créer un nouveau message avec le menu de création de tickets
            ticket_embed = self.create_ticket_embed()
            ticket_view = TicketCreationView(self)
            ticket_message = await channel.send(embed=ticket_embed, view=ticket_view)
            
            # Mettre à jour l'ID du message dans la configuration
            self.ticket_message_id = ticket_message.id
            self.save_config()
            
            logger.info(f"✅ Message des tickets rafraîchi (ID: {ticket_message.id})")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement du message des tickets: {str(e)}")
            return False

    def create_ticket_embed(self):
        """Crée l'embed pour la création de tickets"""
        embed = discord.Embed(
            title="🎫 Système de Tickets",
            description=(
                "Besoin d'aide ? Une question ? Un problème ?\n"
                "Créez un ticket en sélectionnant une raison dans le menu ci-dessous."
            ),
            color=self.color
        )
        
        embed.add_field(
            name="📜 Instructions",
            value=(
                "1. Sélectionnez la raison de votre ticket dans le menu\n"
                "2. Décrivez votre problème dans le salon créé\n"
                "3. Un membre du staff vous répondra dès que possible"
            ),
            inline=False
        )
        
        embed.set_footer(text="Support · Utilisez le menu déroulant pour ouvrir un ticket")
        return embed

    @commands.command(
        name="ticketsetup",
        help="Configure le système de tickets",
        description="Crée la catégorie et les salons nécessaires pour le système de tickets",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def setup_tickets(self, ctx):
        """Crée la catégorie et les salons pour le système de tickets"""
        try:
            # Créer la catégorie de tickets si elle n'existe pas
            guild = ctx.guild
            category_name = "Tickets"
            category = discord.utils.get(guild.categories, name=category_name)
            if not category:
                category = await guild.create_category(category_name)
                self.ticket_category_id = category.id
            else:
                self.ticket_category_id = category.id
            
            # Créer le canal de création de tickets si nécessaire
            create_channel_name = "créer-un-ticket"
            create_channel = discord.utils.get(guild.text_channels, name=create_channel_name)
            if not create_channel:
                create_channel = await guild.create_text_channel(create_channel_name, category=category)
                self.create_channel_id = create_channel.id
            else:
                self.create_channel_id = create_channel.id
            
            # Créer le canal de logs de tickets dans la même catégorie
            logs_channel_name = "ticket-logs"
            logs_channel = discord.utils.get(guild.text_channels, name=logs_channel_name, category=category)
            if not logs_channel:
                # Permissions spéciales pour le canal de logs (visible uniquement par les admins)
                logs_overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
                }
                # Ajouter les permissions pour les administrateurs
                for role in guild.roles:
                    if role.permissions.administrator:
                        logs_overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
                
                # Créer le canal
                logs_channel = await guild.create_text_channel(
                    logs_channel_name, 
                    category=category,
                    overwrites=logs_overwrites,
                    topic="Logs des actions sur les tickets"
                )
                self.log_channel_id = logs_channel.id
                await ctx.send(f"📋 Canal de logs de tickets créé: {logs_channel.mention}")
            else:
                self.log_channel_id = logs_channel.id
            
            # Envoyer le message d'instruction avec le menu déroulant
            await create_channel.purge(limit=10)  # Nettoyer les anciens messages
            ticket_embed = self.create_ticket_embed()
            ticket_message = await create_channel.send(embed=ticket_embed, view=TicketCreationView(self))
            
            # Sauvegarder l'ID du message
            self.ticket_message_id = ticket_message.id
            self.save_config()
            
            # Annoncer la configuration
            embed = discord.Embed(
                title="✅ Système de tickets configuré",
                description="Le système de tickets a été mis en place avec succès!",
                color=self.color
            )
            
            embed.add_field(name="Catégorie", value=f"**{category.name}**", inline=True)
            embed.add_field(name="Canal de création", value=f"{create_channel.mention}", inline=True)
            embed.add_field(name="Canal de logs", value=f"{logs_channel.mention}", inline=True)
            embed.set_footer(text="Utilisez !ticketreasons pour configurer les raisons des tickets")
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration des tickets: {str(e)}")
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")
    
    @commands.command(
        name="ticketreasons",
        help="Configure les raisons disponibles pour les tickets",
        description="Permet de définir les différentes raisons pouvant être choisies lors de la création d'un ticket",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def setup_ticket_reasons(self, ctx):
        """Configure les raisons disponibles pour les tickets"""
        await ctx.send("🔄 Configuration des raisons de tickets. Envoyez `annuler` pour annuler à tout moment.\n\n"
                      "Veuillez entrer le nombre de raisons que vous souhaitez configurer (1-10):")
        
        def check(m):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id
        
        # Demander le nombre de raisons
        try:
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            if response.content.lower() == 'annuler':
                await ctx.send("❌ Configuration annulée.")
                return
                
            try:
                num_reasons = int(response.content)
                if num_reasons < 1 or num_reasons > 10:
                    await ctx.send("❌ Le nombre doit être entre 1 et 10. Configuration annulée.")
                    return
            except ValueError:
                await ctx.send("❌ Veuillez entrer un nombre valide. Configuration annulée.")
                return
                
            # Initialiser une liste pour les nouvelles raisons
            new_reasons = []
            
            # Recueillir les informations pour chaque raison
            for i in range(1, num_reasons + 1):
                await ctx.send(f"📝 Configuration de la raison #{i}:\n\n"
                              f"Veuillez entrer le libellé (ex: 'Assistance technique'):")
                
                label_resp = await self.bot.wait_for('message', check=check, timeout=60.0)
                if label_resp.content.lower() == 'annuler':
                    await ctx.send("❌ Configuration annulée.")
                    return
                label = label_resp.content.strip()
                
                await ctx.send(f"Entrez un emoji pour cette raison (ex: '🔧'):")
                emoji_resp = await self.bot.wait_for('message', check=check, timeout=60.0)
                if emoji_resp.content.lower() == 'annuler':
                    await ctx.send("❌ Configuration annulée.")
                    return
                emoji = emoji_resp.content.strip()
                
                await ctx.send(f"Entrez une description courte (max 100 caractères):")
                desc_resp = await self.bot.wait_for('message', check=check, timeout=60.0)
                if desc_resp.content.lower() == 'annuler':
                    await ctx.send("❌ Configuration annulée.")
                    return
                description = desc_resp.content[:100].strip()
                
                new_reasons.append({
                    "label": label,
                    "emoji": emoji,
                    "description": description
                })
                
                await ctx.send(f"✅ Raison #{i} configurée: {emoji} {label}")
            
            # Sauvegarder les nouvelles raisons
            self.ticket_reasons = new_reasons
            self.save_config()
            
            # Mettre à jour le message de tickets avec le nouveau menu
            try:
                if self.ticket_message_id:
                    channel = self.bot.get_channel(self.create_channel_id)
                    if channel:
                        try:
                            message = await channel.fetch_message(self.ticket_message_id)
                            await message.edit(embed=self.create_ticket_embed(), view=TicketCreationView(self))
                            await ctx.send("✅ Menu de tickets mis à jour avec les nouvelles raisons!")
                        except:
                            await ctx.send("⚠️ Message de tickets introuvable. Utilisez !ticketsetup pour recréer le message.")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la mise à jour du menu de tickets: {str(e)}")
                await ctx.send("⚠️ Les raisons ont été enregistrées mais le menu n'a pas pu être mis à jour.")
                
            await ctx.send(f"✅ Configuration terminée! {len(new_reasons)} raisons de tickets configurées.")
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Temps écoulé. Configuration annulée.")

    @commands.command(
        name="ticketsync",
        help="Rafraîchit le menu de création de tickets",
        description="Régénère le message interactif permettant la création de tickets",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def refresh_ticket_menu(self, ctx):
        """Rafraîchit le menu de création de tickets"""
        try:
            if not self.create_channel_id:
                embed = discord.Embed(
                    title="❌ Erreur", 
                    description="Canal de création de tickets non configuré. Utilisez !ticketsetup d'abord.",
                    color=self.color
                )
                await ctx.send(embed=embed)
                return
                
            channel = self.bot.get_channel(self.create_channel_id)
            if not channel:
                embed = discord.Embed(
                    title="❌ Erreur", 
                    description="Canal de création de tickets introuvable.",
                    color=self.color
                )
                await ctx.send(embed=embed)
                return
                
            await channel.purge(limit=10)  # Nettoyer les anciens messages
            ticket_embed = self.create_ticket_embed()
            ticket_message = await channel.send(embed=ticket_embed, view=TicketCreationView(self))
            
            self.ticket_message_id = ticket_message.id
            self.save_config()
            
            embed = discord.Embed(
                title="✅ Menu rafraîchi", 
                description="Le menu de création de tickets a été rafraîchi avec succès!",
                color=self.color
            )
            embed.add_field(name="Canal", value=channel.mention, inline=True)
            embed.add_field(name="ID du message", value=self.ticket_message_id, inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement du menu: {str(e)}")
            embed = discord.Embed(
                title="❌ Erreur", 
                description=f"Une erreur est survenue: {str(e)}",
                color=self.color
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="ticketclose",
        help="Supprime immédiatement un ticket sans l'archiver",
        description="Supprime définitivement un ticket sans l'archiver (admin uniquement)",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def delete_ticket_command(self, ctx):
        """Supprime immédiatement un ticket sans l'archiver (admin uniquement)"""
        channel_id = ctx.channel.id
        if str(channel_id) not in [str(id) for id in self.active_tickets.keys()]:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Ce salon n'est pas un ticket actif.",
                color=self.color
            )
            await ctx.send(embed=embed)
            return
        
        # Demander confirmation avec un embed
        embed = discord.Embed(
            title="⚠️ ATTENTION ⚠️",
            description=(
                "Vous êtes sur le point de **supprimer définitivement** ce ticket.\n"
                "Cette action est irréversible et le contenu ne sera PAS archivé."
            ),
            color=self.color
        )
        embed.set_footer(text="Réagissez avec 🗑️ pour confirmer la suppression.")
        
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction("🗑️")
        
        # Ajouter la réaction pour confirmation
        def reaction_check(reaction, user):
            return (
                user.id == ctx.author.id and 
                reaction.message.id == confirm_msg.id and 
                str(reaction.emoji) == "🗑️"
            )
        
        try:
            # Attendre la réaction de l'administrateur
            reaction, user = await self.bot.wait_for('reaction_add', check=reaction_check, timeout=15.0)
            
            # Stocker les informations du ticket avant suppression
            ticket_data = self.active_tickets[channel_id]
            ticket_name = ctx.channel.name
            owner_id = ticket_data.get("owner")
            owner = ctx.guild.get_member(owner_id) or f"Utilisateur (ID: {owner_id})"
            
            # Générer un ID unique pour le ticket
            ticket_id = f"{ticket_name}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            
            # Collecter les messages du ticket (limité pour éviter les limites de l'API)
            ticket_messages = []
            async for msg in ctx.channel.history(limit=100, oldest_first=True):
                author_name = msg.author.name if not msg.author.bot else f"[BOT] {msg.author.name}"
                if msg.content:
                    ticket_messages.append({
                        "author": author_name,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat()
                    })
            
            # Sauvegarder dans les archives pour conserver l'historique
            self.archived_tickets[ticket_id] = {
                "owner": ticket_data.get("owner"),
                "archived_by": ctx.author.id,
                "archived_at": datetime.utcnow().isoformat(),
                "topic": ctx.channel.topic,
                "name": ctx.channel.name,
                "messages": ticket_messages,
                "close_reason": "Suppression directe par administrateur"
            }
            self.save_archived_tickets()
            
            # Envoyer un message de confirmation
            await ctx.send("🗑️ Suppression du ticket dans 5 secondes...")
            
            # Journal de la suppression du ticket
            log_channel = self.bot.get_channel(self.log_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title=f"🗑️ Ticket Supprimé: {ticket_name}",
                    description=f"Un ticket a été supprimé par {ctx.author.mention}",
                    color=self.color,
                    timestamp=datetime.utcnow()
                )
                
                log_embed.add_field(name="ID du ticket", value=ticket_id, inline=True)
                log_embed.add_field(name="Raison", value="Suppression directe", inline=True)
                log_embed.add_field(name="Créé par", value=str(owner), inline=True)
                
                created_at = ticket_data.get("created_at")
                if created_at:
                    try:
                        creation_time = datetime.fromisoformat(created_at)
                        log_embed.add_field(
                            name="Créé le", 
                            value=creation_time.strftime("%d/%m/%Y à %H:%M"),
                            inline=True
                        )
                    except:
                        pass
                
                log_embed.set_footer(text=f"Supprimé par: {ctx.author.name} (ID: {ctx.author.id})")
                
                # Créer la vue pour le log
                view = TicketLogView(self, ticket_id)
                
                # Envoyer le log avec la vue
                await log_channel.send(
                    content=f"📢 **Ticket supprimé** • ID: `{ticket_id}`",
                    embed=log_embed,
                    view=view
                )
            
            await asyncio.sleep(5)
            
            # Retirer de la liste des tickets actifs
            del self.active_tickets[channel_id]
            self.save_config()
            
            # Supprimer le canal
            await ctx.channel.delete()
            
        except asyncio.TimeoutError:
            await ctx.send("❌ Suppression annulée : temps écoulé.", delete_after=10)

    @commands.command(
        name="ticketrename",
        help="Renomme un ticket actif",
        description="Permet de changer le nom d'un ticket ouvert",
        usage="<nouveau_nom>"
    )
    @commands.has_permissions(administrator=True)
    async def rename_ticket_command(self, ctx, *, new_name: str):
        """Renomme un ticket actif (admin uniquement)"""
        channel_id = ctx.channel.id
        if str(channel_id) not in [str(id) for id in self.active_tickets.keys()]:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Ce salon n'est pas un ticket actif.",
                color=self.color
            )
            await ctx.send(embed=embed)
            return
        
        old_name = ctx.channel.name
        
        # Nettoyer le nom pour le format Discord
        clean_name = ''.join(c for c in new_name.strip().lower() if c.isalnum() or c == '-')
        
        if not clean_name:
            await ctx.send("❌ Nom invalide. Veuillez réessayer avec un nom valide.")
            return
        
        # Renommer le canal
        try:
            await ctx.channel.edit(name=clean_name)
            embed = discord.Embed(
                title="✅ Ticket renommé",
                description=f"Ticket renommé de `{old_name}` à `{clean_name}`",
                color=self.color
            )
            await ctx.send(embed=embed)
            logger.info(f"Ticket renommé par {ctx.author}: {old_name} → {clean_name}")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Je n'ai pas la permission de renommer ce canal.",
                color=self.color
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Erreur lors du renommage: {str(e)}",
                color=self.color
            )
            await ctx.send(embed=embed)

    @commands.command(
        name="ticketname",
        help="Alias de ticketrename",
        description="Permet de changer le nom d'un ticket ouvert",
        usage="<nouveau_nom>"
    )
    @commands.has_permissions(administrator=True)
    async def ticket_name_command(self, ctx, *, new_name: str):
        """Alias de ticketrename"""
        await self.rename_ticket_command(ctx, new_name=new_name)

    @commands.command(
        name="ticketadd",
        help="Ajoute un utilisateur à un ticket",
        description="Permet d'ajouter un membre au ticket actuel",
        usage="<@membre>"
    )
    @commands.has_permissions(manage_channels=True)
    async def add_to_ticket(self, ctx, member: discord.Member):
        """Ajoute un utilisateur à un ticket"""
        channel_id = ctx.channel.id
        if str(channel_id) not in [str(id) for id in self.active_tickets.keys()]:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Ce salon n'est pas un ticket actif.",
                color=self.color
            )
            await ctx.send(embed=embed)
            return
        
        try:
            # Ajouter l'utilisateur au ticket
            await ctx.channel.set_permissions(member,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
            
            embed = discord.Embed(
                title="✅ Utilisateur ajouté",
                description=f"{member.mention} a été ajouté au ticket.",
                color=self.color
            )
            await ctx.send(embed=embed)
            
            # Mentionner l'utilisateur ajouté
            await ctx.send(f"👋 Bienvenue {member.mention} dans ce ticket!")
            
            logger.info(f"{ctx.author} a ajouté {member} au ticket {ctx.channel.name}")
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Erreur",
                description="Je n'ai pas la permission d'ajouter cet utilisateur au ticket.",
                color=self.color
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur est survenue: {str(e)}",
                color=self.color
            )
            await ctx.send(embed=embed)

    async def handle_ticket_close_reaction(self, channel, member, is_owner):
        """Gère le processus de fermeture de ticket via réaction"""
        # Message pour demander la raison avec embed
        embed = discord.Embed(
            title="📝 Fermeture de ticket",
            description=f"{'Vous avez demandé à fermer votre ticket.' if is_owner else f'{member.mention} a demandé la fermeture de ce ticket.'}",
            color=self.color
        )
        embed.add_field(
            name="Instructions",
            value="**Merci d'indiquer la raison de la fermeture:**\n_(Tapez votre raison, ou écrivez 'annuler' pour annuler)_",
            inline=False
        )
        
        close_msg = await channel.send(embed=embed)
        
        def check(m):
            return m.author.id == member.id and m.channel.id == channel.id
        
        try:
            # Attendre la réponse de l'utilisateur
            response = await self.bot.wait_for('message', check=check, timeout=60.0)
            
            # Vérifier si l'utilisateur souhaite annuler
            if response.content.lower() == 'annuler':
                await channel.send("❌ Fermeture du ticket annulée.", delete_after=10)
                return
            
            # Récupérer la raison
            close_reason = response.content
            
            # Remplacer le message de confirmation par un embed
            confirm_embed = discord.Embed(
                title="⚠️ Confirmation de fermeture",
                description=f"Êtes-vous sûr de vouloir fermer ce ticket?\n**Raison:** {close_reason}",
                color=self.color
            )
            confirm_embed.set_footer(text="Réagissez avec ✅ pour confirmer ou ❌ pour annuler.")
            
            confirm_msg = await channel.send(embed=confirm_embed)
            
            # Ajouter les réactions pour confirmation/annulation
            await confirm_msg.add_reaction("✅")
            await confirm_msg.add_reaction("❌")
            
            # Fonction pour vérifier la réaction
            def reaction_check(reaction, user):
                return (
                    user.id == member.id and 
                    reaction.message.id == confirm_msg.id and 
                    str(reaction.emoji) in ["✅", "❌"]
                )
            
            try:
                # Attendre la réaction de l'utilisateur
                reaction, user = await self.bot.wait_for('reaction_add', check=reaction_check, timeout=30.0)
                
                # Traiter la réaction
                if str(reaction.emoji) == "✅":
                    # Procéder à l'archivage du ticket avec la raison fournie
                    await self.archive_ticket_with_reason(channel, member, close_reason)
                else:
                    await channel.send("❌ Fermeture du ticket annulée.", delete_after=10)
                    
            except asyncio.TimeoutError:
                await channel.send("❌ Confirmation expirée. Fermeture du ticket annulée.", delete_after=10)
                
        except asyncio.TimeoutError:
            await channel.send("❌ Temps écoulé. Veuillez réessayer si vous souhaitez toujours fermer ce ticket.", delete_after=10)

    async def archive_ticket_with_reason(self, channel, member, reason):
        """Archive un ticket avec une raison spécifiée"""
        try:
            channel_id = channel.id
            if str(channel_id) not in [str(id) for id in self.active_tickets.keys()]:
                await channel.send("❌ Ce salon n'est pas un ticket actif.")
                return
                
            # Processus d'archivage
            ticket_data = self.active_tickets[channel_id]
            guild = channel.guild
                
            # Générer un ticket ID unique
            ticket_id = f"{channel.name}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
            
            # Collecter tous les messages du ticket
            ticket_messages = []
            async for msg in channel.history(limit=500, oldest_first=True):
                author_name = msg.author.name if not msg.author.bot else f"[BOT] {msg.author.name}"
                if msg.content:
                    ticket_messages.append({
                        "author": author_name,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat()
                    })
            
            # Sauvegarder les informations du ticket avec la raison
            self.archived_tickets[ticket_id] = {
                "owner": ticket_data.get("owner"),
                "archived_by": member.id,
                "archived_at": datetime.utcnow().isoformat(),
                "topic": channel.topic,
                "name": channel.name,
                "messages": ticket_messages,
                "close_reason": reason
            }
            self.save_archived_tickets()
            
            # Log de l'archivage du ticket avec la raison et bouton d'interaction
            log_channel = self.bot.get_channel(self.log_channel_id)
            if log_channel:
                # Créer un embed amélioré pour les logs
                log_embed = discord.Embed(
                    title=f"🔒 Ticket Archivé: {channel.name}",
                    description=f"Un ticket a été fermé par {member.mention}",
                    color=self.color,
                    timestamp=datetime.utcnow()
                )
                
                # Ajouter des informations détaillées
                log_embed.add_field(name="ID du ticket", value=ticket_id, inline=True)
                log_embed.add_field(name="Raison de fermeture", value=reason, inline=True)
                
                # Ajout d'informations sur le propriétaire du ticket
                owner_id = ticket_data.get("owner")
                owner = guild.get_member(owner_id) or f"Utilisateur (ID: {owner_id})"
                log_embed.add_field(name="Créé par", value=str(owner), inline=True)
                
                # Ajouter un timestamp de création si disponible
                created_at = ticket_data.get("created_at")
                if created_at:
                    try:
                        creation_time = datetime.fromisoformat(created_at)
                        log_embed.add_field(
                            name="Créé le", 
                            value=creation_time.strftime("%d/%m/%Y à %H:%M"),
                            inline=True
                        )
                    except:
                        pass
                
                log_embed.set_footer(text=f"ID Utilisateur: {member.id}")
                
                # Créer la vue avec le bouton pour voir le contenu
                view = TicketLogView(self, ticket_id)
                
                # Envoyer le log avec la vue
                await log_channel.send(
                    content=f"📢 **Ticket fermé** • ID: `{ticket_id}`",  # Mention claire du ticket fermé
                    embed=log_embed,
                    view=view
                )
            
            # Message de confirmation
            await channel.send(f"🗃️ Ce ticket va être archivé dans 5 secondes...\n**Raison:** {reason}\n**ID:** {ticket_id}")
            await asyncio.sleep(5)
            
            # Traitement d'archivage ou suppression
            archive_category = self.bot.get_channel(self.archive_category_id)
            if archive_category:
                try:
                    # Définir les permissions pour n'autoriser que les admins
                    archive_overwrites = {
                        guild.default_role: discord.PermissionOverwrite(view_channel=False),
                        guild.me: discord.PermissionOverwrite(view_channel=True)
                    }
                    
                    # Ajouter des permissions pour les rôles d'admin
                    for role in guild.roles:
                        if role.permissions.administrator:
                            archive_overwrites[role] = discord.PermissionOverwrite(view_channel=True)
                    
                    # Renommer et déplacer dans la catégorie d'archives
                    await channel.edit(
                        name=f"archive-{ticket_id}",
                        category=archive_category,
                        overwrites=archive_overwrites
                    )
                    
                    # Retirer de la liste des tickets actifs
                    del self.active_tickets[channel.id]
                    self.save_config()
                    
                    await channel.send(f"📁 Ce ticket a été archivé pour raison: **{reason}**")
                    
                except discord.Forbidden:
                    await channel.send("❌ Je n'ai pas les permissions pour archiver ce ticket. Il sera supprimé.")
                    await asyncio.sleep(2)
                    await channel.delete()
                    del self.active_tickets[channel.id]
                    self.save_config()
            else:
                # Supprimer le canal si pas de catégorie d'archives
                await channel.delete()
                del self.active_tickets[channel.id]
                self.save_config()
                
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'archivage du ticket: {str(e)}")
            embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur est survenue lors de l'archivage: {str(e)}",
                color=self.color
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gère les réactions pour la création et la fermeture de tickets"""
        # Ignorer les réactions du bot
        if payload.user_id == self.bot.user.id:
            return
        
        # Vérifier s'il s'agit d'une réaction au message du créateur de tickets
        if hasattr(self, 'ticket_message_id') and payload.message_id == self.ticket_message_id:
            if str(payload.emoji) == "📩":
                # Gérer la création de tickets
                return
        
        # Vérifier s'il s'agit d'une réaction pour fermer un ticket
        channel_id = payload.channel_id
        if str(channel_id) in [str(id) for id in self.active_tickets.keys()]:
            ticket_data = self.active_tickets[channel_id]
            if payload.message_id == ticket_data.get("config_message"):
                guild = self.bot.get_guild(payload.guild_id)
                member = guild.get_member(payload.user_id)
                channel = self.bot.get_channel(channel_id)
                message = await channel.fetch_message(payload.message_id)
                
                # Enlever la réaction
                await message.remove_reaction(payload.emoji, member)
                
                # Vérifier si c'est la réaction pour fermer le ticket
                if str(payload.emoji) == "🔒":
                    # Vérifier si la personne est le propriétaire du ticket ou un admin
                    is_owner = ticket_data.get("owner") == payload.user_id
                    is_admin = member.guild_permissions.administrator
                    
                    if is_owner or is_admin:
                        await self.handle_ticket_close_reaction(channel, member, is_owner)
                    else:
                        await channel.send(f"{member.mention} Seul le créateur du ticket ou un administrateur peut fermer ce ticket.", delete_after=10)

    @commands.Cog.listener()
    async def on_color_change(self):
        """Mettre à jour la couleur des tickets quand la couleur globale change"""
        try:
            # Récupérer la nouvelle couleur et s'assurer qu'elle est au format entier
            new_color = EmbedManager.get_default_color()
            if isinstance(new_color, discord.Color):
                new_color = new_color.value
            self.color = new_color
            
            # Rafraîchir le message d'embed du ticket si nécessaire
            if hasattr(self, 'create_channel_id') and self.create_channel_id:
                channel = self.bot.get_channel(self.create_channel_id)
                if channel and hasattr(self, 'ticket_message_id'):
                    try:
                        message = await channel.fetch_message(self.ticket_message_id)
                        ticket_embed = self.create_ticket_embed()
                        await message.edit(embed=ticket_embed)
                        logger.info("✅ Couleur du menu de tickets mise à jour")
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de la mise à jour de la couleur: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la mise à jour de la couleur: {str(e)}")

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))