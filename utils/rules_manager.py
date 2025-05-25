import discord
import json
import os
import logging

logger = logging.getLogger("bot")

class RulesManager:
    CONFIG_FILE = 'data/rules_config.json'

    @staticmethod
    async def refresh_rules(bot: discord.ext.commands.Bot):
        """Rafraîchit le message des règles sur tous les serveurs"""
        try:
            # Charger la configuration
            if not os.path.exists(RulesManager.CONFIG_FILE):
                logger.warning("❌ Fichier de configuration des règles non trouvé")
                return False

            # Créer le fichier s'il n'existe pas
            if not os.path.exists(RulesManager.CONFIG_FILE):
                os.makedirs(os.path.dirname(RulesManager.CONFIG_FILE), exist_ok=True)
                with open(RulesManager.CONFIG_FILE, 'w') as f:
                    json.dump({
                        'rules_channel_id': None,
                        'rules_message_id': None,
                        'verified_role_id': None,
                        'default_role_id': None
                    }, f, indent=4)
                return False

            with open(RulesManager.CONFIG_FILE, 'r') as f:
                config = json.load(f)

            # Ajouter les clés manquantes si nécessaire
            if 'verified_role_id' not in config:
                config['verified_role_id'] = None
            if 'default_role_id' not in config:
                config['default_role_id'] = None
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

            # Vérifier si le rôle existe déjà par ID
            default_role_id = config.get('default_role_id')
            if default_role_id:
                role = guild.get_role(default_role_id)
                if role:
                    return role

            # Vérifier si le rôle existe par nom
            role = discord.utils.get(guild.roles, name="Nouveau Membre")
            if role:
                # Sauvegarder l'ID du rôle existant
                config['default_role_id'] = role.id
                with open(RulesManager.CONFIG_FILE, 'w') as f:
                    json.dump(config, f, indent=4)
                return role

            # Créer le rôle s'il n'existe pas
            role = await guild.create_role(
                name="Nouveau Membre",
                color=discord.Color.lighter_grey(),
                reason="Rôle par défaut pour les nouveaux membres"
            )

            # Configurer les permissions
            for channel in guild.channels:
                if channel.id != config.get('rules_channel_id'):
                    await channel.set_permissions(role, view_channel=False)
                else:
                    await channel.set_permissions(role, view_channel=True, send_messages=False)

            # Sauvegarder l'ID
            config['default_role_id'] = role.id
            with open(RulesManager.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)

            logger.info(f"✅ Rôle Nouveau Membre créé/configuré")
            return role

        except Exception as e:
            logger.error(f"❌ Erreur lors de la création/récupération du rôle par défaut: {str(e)}")
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
    async def handle_rule_accept(member: discord.Member, role: discord.Role):
        """Gère l'attribution du rôle et l'envoi du message lors de l'acceptation des règles"""
        try:
            # Vérifier si le membre a déjà le rôle
            if role in member.roles:
                logger.info(f"Le membre {member.name} a déjà le rôle {role.name}, pas de message envoyé")
                return False
                
            # Retirer le rôle par défaut
            with open(RulesManager.CONFIG_FILE, 'r') as f:
                config = json.load(f)
                
            default_role_id = config.get('default_role_id')
            if default_role_id:
                default_role = member.guild.get_role(default_role_id)
                if default_role and default_role in member.roles:
                    try:
                        # Retirer le rôle "Nouveau Membre"
                        await member.remove_roles(default_role, reason="Acceptation des règles")
                        logger.info(f"✅ Rôle {default_role.name} retiré de {member.name}")
                    except Exception as e:
                        logger.error(f"❌ Erreur lors du retrait du rôle par défaut: {str(e)}")
                        # Continuer malgré l'erreur
                    
            # Ajouter le rôle vérifié
            try:
                await member.add_roles(role, reason="Acceptation des règles")
                logger.info(f"✅ Rôle {role.name} attribué à {member.name}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'ajout du rôle vérifié: {str(e)}")
                # Réessayer une fois en cas d'échec
                import asyncio
                await asyncio.sleep(1)
                await member.add_roles(role, reason="Acceptation des règles (2ème tentative)")
                logger.info(f"✅ Rôle {role.name} attribué à {member.name} (2ème tentative)")
            
            # Trouver un salon de rôles si existant
            roles_channel = None
            for channel in member.guild.channels:
                if "rôle" in channel.name.lower() or "role" in channel.name.lower():
                    roles_channel = channel
                    break
                    
            # Envoyer un message privé de confirmation
            try:
                from utils.embed_manager import EmbedManager
                embed = EmbedManager.create_access_granted_dm(member.guild, roles_channel)
                await member.send(embed=embed)
                logger.info(f"✅ Message de confirmation envoyé à {member.name}")
            except discord.Forbidden:
                logger.warning(f"❌ Impossible d'envoyer un message privé à {member.name}")
                
            return True
                
        except discord.Forbidden:
            logger.error(f"❌ Permissions insuffisantes pour gérer les rôles de {member.name}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'attribution du rôle: {str(e)}")
            return False

__all__ = ['RulesManager']