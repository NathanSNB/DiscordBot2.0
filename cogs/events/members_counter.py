import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
from utils.embed_manager import EmbedManager  # Ajout de l'import pour l'EmbedManager

logger = logging.getLogger('bot')

class MembersCounter(commands.Cog, name="compteur_membres"):
    """Système de compteur de membres en salon vocal"""
    
    def __init__(self, bot):
        self.bot = bot
        self.config_file = 'data/members_counter.json'
        self.config = self.load_config()
        self.update_counter.start()
    
    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        default_config = {
            'enabled': False,
            'channel_id': None,
            'format': '👥 Membres: {count}',
            'category_id': None
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.save_config(default_config)
                return default_config
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement de la configuration du compteur: {e}")
            return default_config
    
    def save_config(self, config=None):
        """Sauvegarde la configuration dans le fichier JSON"""
        if config is None:
            config = self.config
            
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la configuration du compteur: {e}")
    
    async def get_non_bot_member_count(self, guild):
        """Compte le nombre de membres non-bots dans le serveur"""
        return sum(1 for member in guild.members if not member.bot)
    
    @tasks.loop(minutes=10)
    async def update_counter(self):
        """Met à jour périodiquement le compteur de membres"""
        if not self.config.get('enabled', False) or not self.config.get('channel_id'):
            return
            
        for guild in self.bot.guilds:
            try:
                channel_id = self.config.get('channel_id')
                channel = guild.get_channel(channel_id)
                
                if not channel:
                    continue
                    
                member_count = await self.get_non_bot_member_count(guild)
                new_name = self.config.get('format', '👥 Membres: {count}').format(count=member_count)
                
                if channel.name != new_name:
                    await channel.edit(name=new_name)
                    logger.info(f"✅ Compteur de membres mis à jour: {new_name}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la mise à jour du compteur pour {guild.name}: {e}")
    
    @update_counter.before_loop
    async def before_update_counter(self):
        """Attend que le bot soit prêt avant de démarrer la boucle"""
        await self.bot.wait_until_ready()
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Initialise le compteur au démarrage du bot"""
        if not self.config.get('enabled', False):
            return
            
        await asyncio.sleep(5)  # Attendre que tout soit chargé
        
        # Vérifier si le salon existe, sinon le créer
        for guild in self.bot.guilds:
            channel_id = self.config.get('channel_id')
            if channel_id:
                channel = guild.get_channel(channel_id)
                if not channel:
                    await self.create_counter_channel(guild)
            else:
                await self.create_counter_channel(guild)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Met à jour le compteur quand un membre rejoint"""
        if member.bot or not self.config.get('enabled', False):
            return
            
        guild = member.guild
        channel_id = self.config.get('channel_id')
        channel = guild.get_channel(channel_id)
        
        if not channel:
            return
            
        member_count = await self.get_non_bot_member_count(guild)
        new_name = self.config.get('format', '👥 Membres: {count}').format(count=member_count)
        
        await channel.edit(name=new_name)
        logger.info(f"✅ Compteur de membres mis à jour après arrivée: {new_name}")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Met à jour le compteur quand un membre quitte"""
        if member.bot or not self.config.get('enabled', False):
            return
            
        guild = member.guild
        channel_id = self.config.get('channel_id')
        channel = guild.get_channel(channel_id)
        
        if not channel:
            return
            
        member_count = await self.get_non_bot_member_count(guild)
        new_name = self.config.get('format', '👥 Membres: {count}').format(count=member_count)
        
        await channel.edit(name=new_name)
        logger.info(f"✅ Compteur de membres mis à jour après départ: {new_name}")
    
    async def create_counter_channel(self, guild):
        """Crée un salon vocal pour le compteur de membres"""
        try:
            # Vérifier si un salon de compteur existe déjà
            for channel in guild.channels:
                if channel.name.startswith("👥 Membres:"):
                    # Salon existant trouvé, utilisons-le
                    self.config['channel_id'] = channel.id
                    self.save_config()
                    logger.info(f"✅ Réutilisation d'un salon compteur existant: {channel.name}")
                    return channel
                
            # Si aucun salon existant n'est trouvé, continuer avec la création
            category_id = self.config.get('category_id')
            category = guild.get_channel(category_id) if category_id else None
            
            member_count = await self.get_non_bot_member_count(guild)
            channel_name = self.config.get('format', '👥 Membres: {count}').format(count=member_count)
            
            # Permissions: visible par tous mais personne ne peut se connecter
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(
                    view_channel=True,
                    connect=False
                )
            }
            
            channel = await guild.create_voice_channel(
                name=channel_name,
                overwrites=overwrites,
                category=category
            )
            
            self.config['channel_id'] = channel.id
            self.save_config()
            
            logger.info(f"✅ Salon compteur de membres créé: {channel_name}")
            return channel
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du salon compteur: {e}")
            return None
    
    @commands.command(
        name="setupcounter",
        help="Configure le compteur de membres",
        description="Configure ou réinitialise le salon vocal affichant le nombre de membres",
        usage="[catégorie_id]"
    )
    @commands.has_permissions(administrator=True)
    async def setup_counter(self, ctx, category_id: int = None):
        """Configure le compteur de membres"""
        try:
            guild = ctx.guild
            
            # Supprimer l'ancien salon s'il existe
            if self.config.get('channel_id'):
                old_channel = guild.get_channel(self.config.get('channel_id'))
                if old_channel:
                    await old_channel.delete()
                    # Création d'un embed pour la confirmation de suppression
                    delete_embed = discord.Embed(
                        title="🗑️ Compteur de membres",
                        description="L'ancien salon compteur a été supprimé.",
                        color=EmbedManager.get_default_color()
                    )
                    await ctx.send(embed=delete_embed)
            
            # Mettre à jour la configuration
            self.config['enabled'] = True
            self.config['category_id'] = category_id
            self.save_config()
            
            # Créer le nouveau salon
            channel = await self.create_counter_channel(guild)
            
            if channel:
                # Création d'un embed pour la confirmation de création
                success_embed = discord.Embed(
                    title="✅ Compteur de membres configuré",
                    description=f"Le compteur de membres a été configuré avec succès dans le salon {channel.mention}.",
                    color=EmbedManager.get_default_color()
                )
                success_embed.add_field(
                    name="Détails",
                    value=f"📊 Affiche le nombre total de membres non-bots\n🔄 Mise à jour automatique toutes les 10 minutes",
                    inline=False
                )
                await ctx.send(embed=success_embed)
            else:
                # Création d'un embed pour l'erreur
                error_embed = discord.Embed(
                    title="❌ Erreur de configuration",
                    description="Une erreur est survenue lors de la création du salon compteur.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration du compteur: {e}")
            error_embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    

    @commands.command(
        name="togglecounter",
        help="Active/désactive le compteur",
        description="Active ou désactive le compteur de membres. Quand activé, le compteur sera visible pour tous les membres. Quand désactivé, le compteur sera invisible.",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def toggle_counter(self, ctx):
        """Active ou désactive le compteur de membres"""
        try:
            self.config['enabled'] = not self.config.get('enabled', False)
            self.save_config()
            
            state = "activé" if self.config['enabled'] else "désactivé"
            
            # Création d'un embed pour le statut du compteur
            status_embed = discord.Embed(
                title=f"{'✅' if self.config['enabled'] else '⏸️'} Compteur de membres {state}",
                description=f"Le compteur de membres est maintenant **{state}**.",
                color=EmbedManager.get_default_color() if self.config['enabled'] else discord.Color.light_grey()
            )
            
            channel_id = self.config.get('channel_id')
            channel = ctx.guild.get_channel(channel_id) if channel_id else None
            
            if channel:
                # Mettre à jour les permissions de visibilité
                overwrites = channel.overwrites.copy()
                overwrites[ctx.guild.default_role].view_channel = self.config['enabled']
                await channel.edit(overwrites=overwrites)
                
                status_embed.add_field(
                    name="Salon",
                    value=f"{channel.mention}",
                    inline=True
                )
                
                if self.config['enabled']:
                    status_embed.add_field(
                        name="Mise à jour",
                        value="Le compteur sera mis à jour immédiatement",
                        inline=True
                    )
                    # Forcer une mise à jour immédiate
                    self.update_counter.restart()
                else:
                    status_embed.add_field(
                        name="Visibilité",
                        value="Le compteur est maintenant invisible pour tous les membres",
                        inline=True
                    )
                    status_embed.color = discord.Color.light_grey()
            elif self.config['enabled']:
                new_channel = await self.create_counter_channel(ctx.guild)
                if new_channel:
                    status_embed.add_field(
                        name="Nouveau salon",
                        value=f"Un nouveau salon compteur a été créé: {new_channel.mention}",
                        inline=False
                    )
            
            await ctx.send(embed=status_embed)
        except Exception as e:
            logger.error(f"❌ Erreur lors du basculement du compteur: {e}")
            error_embed = discord.Embed(
                title="❌ Erreur",
                description=f"Une erreur est survenue: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
    
    def cog_unload(self):
        """Nettoie les ressources lors du déchargement du cog"""
        self.update_counter.cancel()

async def setup(bot):
    await bot.add_cog(MembersCounter(bot))
