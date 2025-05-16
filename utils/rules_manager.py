import discord
from discord.ext import commands
import json
import os
import logging

from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

class RulesManager:
    CONFIG_FILE = 'data/rules_config.json'

    @staticmethod
    async def refresh_rules(bot: commands.Bot):
        """Rafraîchit le message des règles sur tous les serveurs"""
        try:
            # Charger la configuration
            if not os.path.exists(RulesManager.CONFIG_FILE):
                logger.warning("❌ Fichier de configuration des règles non trouvé")
                return False

            if not os.path.exists(RulesManager.CONFIG_FILE):
                os.makedirs(os.path.dirname(RulesManager.CONFIG_FILE), exist_ok=True)
                with open(RulesManager.CONFIG_FILE, 'w') as f:
                    json.dump({
                        'rules_channel_id': None,
                        'rules_message_id': None,
                        'verified_role_id': None
                    }, f, indent=4)
                return False

            with open(RulesManager.CONFIG_FILE, 'r') as f:
                config = json.load(f)

            # Ajouter la clé verified_role_id si elle n'existe pas
            if 'verified_role_id' not in config:
                config['verified_role_id'] = None
                with open(RulesManager.CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=4)

            rules_cog = bot.get_cog('RulesCommands')
            if rules_cog:
                rules_cog.rules_channel_id = config.get('rules_channel_id')
                rules_cog.rules_message_id = config.get('rules_message_id')
                rules_cog.verified_role_id = config.get('verified_role_id')
                
                if rules_cog.rules_channel_id:
                    for guild in bot.guilds:
                        channel = guild.get_channel(rules_cog.rules_channel_id)
                        if channel:
                            # Supprimer l'ancien message si existant
                            if rules_cog.rules_message_id:
                                try:
                                    old_msg = await channel.fetch_message(rules_cog.rules_message_id)
                                    await old_msg.delete()
                                except:
                                    pass

                            # Créer nouveau message
                            embed = rules_cog.format_rules_embed(guild)
                            new_msg = await channel.send(embed=embed)
                            rules_cog.rules_message_id = new_msg.id
                            await new_msg.add_reaction("✅")

                            # Sauvegarder le nouvel ID
                            config['rules_message_id'] = new_msg.id
                            with open(RulesManager.CONFIG_FILE, 'w') as f:
                                json.dump(config, f, indent=4)

                            logger.info("✅ Message de règlement mis à jour")

            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors du rafraîchissement des règles: {str(e)}")
            return False

    @staticmethod
    async def setup_default_role(guild: discord.Guild) -> discord.Role:
        """Crée ou récupère le rôle par défaut"""
        try:
            with open(RulesManager.CONFIG_FILE, 'r') as f:
                config = json.load(f)

            default_role_id = config.get('default_role_id')
            if default_role_id:
                role = guild.get_role(default_role_id)
                if role:
                    return role

            # Créer un nouveau rôle avec des permissions limitées
            role = await guild.create_role(
                name="Nouveau Membre",
                color=discord.Color.lighter_grey(),
                reason="Rôle par défaut pour les nouveaux membres"
            )

            # Configurer les permissions pour voir uniquement le salon des règles
            for channel in guild.channels:
                if channel.id != config.get('rules_channel_id'):
                    await channel.set_permissions(role, view_channel=False)
                else:
                    await channel.set_permissions(role, view_channel=True, send_messages=False)

            # Sauvegarder l'ID
            config['default_role_id'] = role.id
            with open(RulesManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)

            return role
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du rôle par défaut: {str(e)}")
            return None

    @staticmethod
    async def should_send_welcome_dm(member: discord.Member) -> bool:
        """Vérifie si on doit envoyer un message privé de bienvenue"""
        try:
            with open(RulesManager.CONFIG_FILE, 'r') as f:
                config = json.load(f)
            
            verified_role_id = config.get('verified_role_id')
            if verified_role_id:
                # Si le membre a déjà le rôle vérifié, on ne lui envoie pas de message
                role = member.guild.get_role(int(verified_role_id))
                if role and role in member.roles:
                    logger.info(f"Le membre {member.name} a déjà le rôle vérifié, pas de message de bienvenue")
                    return False
                
            return True
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification des rôles: {str(e)}")
            return False

    @staticmethod
    async def handle_rule_accept(member, role):
        """Gère l'attribution du rôle et l'envoi du message lors de l'acceptation des règles"""
        try:
            # Vérifier si le membre a déjà le rôle
            if role in member.roles:
                logger.info(f"Le membre {member.name} a déjà le rôle {role.name}, pas de message envoyé")
                return False
                
            # Si le membre n'a pas le rôle, on le lui attribue
            await member.add_roles(role)
            
            # Envoyer le message uniquement si le rôle vient d'être ajouté
            roles_channel = discord.utils.get(member.guild.channels, name="roles-notifications")
            if roles_channel:
                embed = EmbedManager.create_access_granted(member.guild, roles_channel)
                await member.send(embed=embed)
                logger.info(f"✅ Rôle {role.name} ajouté et message envoyé à {member.name}")
            
            return True
                
        except discord.Forbidden:
            logger.error(f"❌ Impossible d'envoyer un MP à {member.name}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'attribution du rôle: {str(e)}")
            return False

__all__ = ['RulesManager']
