import discord
from discord.ext import commands
import logging
import os
import json
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()
logger = logging.getLogger('bot')

class MCStatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Supprimer la référence à STATUS_CHANNEL_ID car on va le lire depuis le JSON
        
    async def save_config(self, server_address: str, channel_id: int, role_id: int = None):
        # Séparer l'IP et le port
        if ':' in server_address:
            ip, port = server_address.split(':')
        else:
            ip = server_address
            port = "25565"

        try:
            # Charger la configuration existante
            with open('data/user_preferences.json', 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Mettre à jour la configuration
            if 'minecraft' not in config:
                config['minecraft'] = {}
            
            config['minecraft']['server'] = {
                'ip': ip,
                'port': port
            }
            config['minecraft']['discord'] = {
                'statusChannelId': str(channel_id)
            }
            
            # Ajouter le rôle de notification s'il est spécifié
            if role_id is not None:
                config['minecraft']['discord']['notificationRoleId'] = str(role_id)
            elif 'notificationRoleId' not in config.get('minecraft', {}).get('discord', {}):
                # Valeur par défaut si pas encore configurée
                config['minecraft']['discord']['notificationRoleId'] = "0"
                
            config['minecraft']['lastUpdate'] = ''

            # Sauvegarder la configuration
            with open('data/user_preferences.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)

            return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde de la configuration: {e}")
            return False
        
    @commands.command(
        name="mcstatus",
        help="Affiche le statut du serveur Minecraft",
        description="Vérifie si le serveur est en ligne et affiche les joueurs connectés",
        usage=""
    )
    async def mcstat(self, ctx):
        """Commande pour afficher le statut du serveur manuellement"""
        # Récupérer le cog MCStatusTracker
        tracker_cog = self.bot.get_cog('MCStatusTracker')
        if not tracker_cog:
            await ctx.send("❌ Le système de suivi n'est pas disponible.")
            return
        
        loading_msg = await ctx.send("🔄 Vérification du statut du serveur...")
        is_online, embed, _, _ = await tracker_cog.get_status_embed()
        await loading_msg.edit(content=None, embed=embed)
        logger.info(f"✅ Commande mcstatus exécutée par {ctx.author}")
    
    @commands.command(
        name="mcupdate",
        help="Actualise le message de statut du serveur",
        description="Force l'actualisation du message de statut",
        usage=""
    )
    @commands.has_permissions(administrator=True)
    async def mcrefresh(self, ctx):
        """Force l'actualisation du message de statut"""
        tracker_cog = self.bot.get_cog('MCStatusTracker')
        if not tracker_cog:
            await ctx.send("❌ Le système de suivi n'est pas disponible.")
            return
        
        # Recharger la configuration pour avoir le bon salon
        tracker_cog.load_config()
        channel = self.bot.get_channel(tracker_cog.STATUS_CHANNEL_ID)
        
        if channel:
            await ctx.send("🔄 Actualisation du statut du serveur...")
            is_online, embed, player_count, current_player_list = await tracker_cog.get_status_embed()
            
            # Nettoyer les anciens messages de statut
            await tracker_cog.clean_status_messages(channel)
            # Nettoyer aussi les notifications joueurs
            await tracker_cog.clean_player_notify_messages(channel)
            
            # Créer un nouveau message de statut
            tracker_cog.status_message = await channel.send(embed=embed)
            
            # Mettre à jour les valeurs précédentes
            tracker_cog.previous_server_status = is_online
            tracker_cog.previous_player_count = player_count
            tracker_cog.previous_player_list = current_player_list
            
            await ctx.send("✅ Message de statut actualisé!")
        else:
            await ctx.send(f"❌ Canal de statut non trouvé (ID: {tracker_cog.STATUS_CHANNEL_ID})")
    
    @commands.command(
        name="mcsetup",
        help="Configure le suivi du serveur Minecraft",
        description="Configure l'adresse du serveur à surveiller, le canal où envoyer les notifications, et le rôle à mentionner",
        usage="<server_address> <channel_id> [role_id]"
    )
    @commands.has_permissions(administrator=True)
    async def mcconfig(self, ctx, server_address: str, channel_id: str, role_id: str = None):
        """Configure un nouveau serveur à tracker
        
        Paramètres :
        - server_address : Adresse du serveur (ip:port)
        - channel_id : ID du canal où envoyer les messages de statut
        - role_id : (Optionnel) ID du rôle à mentionner pour les notifications
        """
        try:
            # Valider le format de l'adresse
            if ':' in server_address:
                ip, port = server_address.split(':')
                try:
                    int(port)  # Vérifier que le port est un nombre
                except ValueError:
                    await ctx.send("❌ Le port doit être un nombre!")
                    return
            else:
                ip = server_address
            
            # Valider l'ID du salon
            channel_id = int(channel_id.strip('<>#'))
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await ctx.send("❌ Salon introuvable!")
                return
            
            # Valider l'ID du rôle (si fourni)
            parsed_role_id = None
            role_mention = ""
            if role_id:
                parsed_role_id = int(role_id.strip('<>@&'))
                role = ctx.guild.get_role(parsed_role_id)
                if not role:
                    await ctx.send("⚠️ Rôle introuvable, configuration sans notifications!")
                else:
                    role_mention = f"\nRôle de notification: {role.mention}"
                
            # Sauvegarder la configuration
            success = await self.save_config(server_address, channel_id, parsed_role_id)
            if not success:
                await ctx.send("❌ Erreur lors de la sauvegarde de la configuration.")
                return
            
            # Mettre à jour le tracker
            tracker_cog = self.bot.get_cog('MCStatusTracker')
            if tracker_cog:
                tracker_cog.reload_config()
                
                # Créer un embed pour la confirmation
                embed = discord.Embed(
                    title="✅ Configuration Minecraft mise à jour",
                    description=f"Le statut du serveur sera affiché et mis à jour dans {channel.mention}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Serveur", value=f"`{server_address}`", inline=True)
                embed.add_field(name="Salon", value=channel.mention, inline=True)
                if parsed_role_id and ctx.guild.get_role(parsed_role_id):
                    embed.add_field(name="Notifications", value=ctx.guild.get_role(parsed_role_id).mention, inline=True)
                
                await ctx.send(embed=embed)
            else:
                await ctx.send("❌ Le système de suivi n'est pas disponible.")
                
        except ValueError as e:
            await ctx.send(f"❌ Format invalide! Utilisation: `!mcsetup <ip:port> <channel_id> [role_id]`\nErreur: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Une erreur est survenue: {str(e)}")
            logger.error(f"Erreur dans mcsetup: {e}")

async def setup(bot):
    await bot.add_cog(MCStatusCommands(bot))