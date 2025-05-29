import discord
from discord.ext import commands
import json
import os
import logging

import discord
from discord.ext import commands
import logging
import asyncio  # Importer asyncio
from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

class PrivateVoiceChannels(commands.Cog, name="private_voice"):  # Ajout du name
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {}  # Stocke les salons temporaires : {channel_id: owner_id}
        
    @commands.command(
        name="voicesetup",
        help="Configure les salons vocaux privés",
        description="Crée la catégorie et le salon nécessaires pour le système de salons vocaux privés",
        usage="!voicesetup"
    )
    @commands.has_permissions(administrator=True)
    async def setup_private_voice(self, ctx):
        """Crée la catégorie et le salon pour les salons vocaux privés"""
        try:
            # Vérifier si la catégorie existe déjà
            category = discord.utils.get(ctx.guild.categories, name="Salons privés")
            if not category:
                # Créer la catégorie avec des permissions par défaut
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True)
                }
                category = await ctx.guild.create_category("Salons privés", overwrites=overwrites)
                logger.info(f"✅ Catégorie 'Salons privés' créée")
            
            # Vérifier si le salon de création existe déjà
            create_channel = discord.utils.get(category.channels, name="➕ Créer votre salon")
            if not create_channel:
                # Créer le salon avec des permissions spécifiques
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(
                        view_channel=True,
                        connect=True,
                        speak=False
                    )
                }
                create_channel = await category.create_voice_channel(
                    "➕ Créer votre salon",
                    overwrites=overwrites
                )
                logger.info(f"✅ Salon de création créé")
            
            embed = discord.Embed(
                title="✅ Configuration des salons privés",
                description="Le système de salons privés est prêt !\nRejoignez le salon '➕ Créer votre salon' pour créer votre propre salon vocal.",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration: {str(e)}")
            await ctx.send("❌ Une erreur est survenue lors de la configuration")

    def create_config_embed(self, member: discord.Member, channel: discord.VoiceChannel) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 Panneau de Configuration",
            description=(
                f"Bienvenue dans votre salon privé, {member.mention} !\n"
                "Utilisez les réactions ci-dessous pour personnaliser votre salon."
            ),
            color=EmbedManager.get_default_color()
        )

        controls = (
            "🔒 • Verrouiller/Déverrouiller le salon\n"
            "✏️ • Modifier le nom\n"
            "👥 • Définir une limite de membres\n"
            "👑 • Transférer la propriété\n"
            "🗑️ • Supprimer le salon"
        )
        embed.add_field(name="🛠️ Contrôles", value=controls, inline=False)
        
        embed.set_footer(text="⭐ Tip: Seul le propriétaire peut utiliser ces contrôles")
        embed.set_thumbnail(url=member.guild.icon.url if member.guild.icon else None)
        
        return embed

    @commands.command(name="setupcategory")
    @commands.has_permissions(administrator=True)
    async def setup_category_config(self, ctx, *, role: discord.Role = None):
        """Configure les permissions de la catégorie des salons privés"""
        try:
            category = discord.utils.get(ctx.guild.categories, name="Salons privés")
            if not category:
                await ctx.send("❌ La catégorie 'Salons privés' n'existe pas. Utilisez !setupvoice d'abord.")
                return

            if role:
                # Configurer les permissions pour le rôle spécifié
                overwrites = {
                    role: discord.PermissionOverwrite(view_channel=True, connect=True),
                    ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False)
                }
            else:
                # Permissions par défaut (tout le monde peut voir)
                overwrites = {
                    ctx.guild.default_role: discord.PermissionOverwrite(view_channel=True)
                }

            await category.edit(overwrites=overwrites)
            
            embed = discord.Embed(
                title="✅ Configuration de la catégorie",
                description=(
                    f"La catégorie a été configurée avec succès.\n"
                    f"Accès restreint: {'✅ Oui' if role else '❌ Non'}\n"
                    f"Rôle requis: {role.mention if role else 'Aucun'}"
                ),
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)

        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration de la catégorie: {str(e)}")
            await ctx.send("❌ Une erreur est survenue lors de la configuration")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        try:
            # Création d'un salon privé
            if after.channel and after.channel.name == "➕ Créer votre salon":
                category = after.channel.category
                channel_name = f"🎧 Salon de {member.display_name}"
                
                # Configuration des permissions avec text_in_voice
                overwrites = {
                    member: discord.PermissionOverwrite(
                        manage_channels=True,
                        manage_permissions=True,
                        connect=True,
                        speak=True,
                        move_members=True,
                        send_messages=True,
                        read_messages=True
                    ),
                    member.guild.default_role: discord.PermissionOverwrite(
                        view_channel=True,
                        connect=True,
                        speak=True,
                        send_messages=True,
                        read_messages=True
                    )
                }
                
                # Créer le salon vocal avec text_in_voice activé
                new_channel = await category.create_voice_channel(
                    channel_name,
                    overwrites=overwrites
                )
                
                # Déplacer l'utilisateur
                await member.move_to(new_channel)
                
                # Envoyer le message de configuration avec les réactions
                embed = self.create_config_embed(member, new_channel)
                config_message = await new_channel.send(embed=embed)
                
                # Ajouter toutes les réactions
                reactions = ['🔒', '✏️', '👥', '👑', '🗑️']
                for reaction in reactions:
                    await config_message.add_reaction(reaction)
                
                self.temp_channels[new_channel.id] = {
                    'owner': member.id,
                    'config_message': config_message.id,
                    'locked': False  # Ajout d'un état de verrouillage initial
                }

                logger.info(f"✅ Salon privé créé pour {member.display_name}")

            # Si l'utilisateur quitte un salon temporaire
            if before.channel and before.channel.id in self.temp_channels:
                await asyncio.sleep(0.5)  # Court délai pour s'assurer que l'état du salon est à jour
                
                try:
                    # Vérifier si le salon existe toujours et s'il est vide
                    channel = self.bot.get_channel(before.channel.id)
                    if channel and len(channel.members) == 0:
                        logger.info(f"🗑️ Suppression du salon privé '{channel.name}' (vide)")
                        
                        # Supprimer le salon de la mémoire avant de le supprimer de Discord
                        # pour éviter des problèmes si plusieurs personnes quittent en même temps
                        channel_data = self.temp_channels.pop(channel.id, None)
                        
                        # Tenter de supprimer le salon
                        await channel.delete(reason="Salon privé vide")
                        
                        logger.info(f"✅ Salon privé supprimé avec succès")
                except discord.NotFound:
                    # Le salon a déjà été supprimé
                    if before.channel.id in self.temp_channels:
                        del self.temp_channels[before.channel.id]
                    logger.info(f"ℹ️ Le salon a déjà été supprimé")
                except discord.Forbidden:
                    logger.error(f"❌ Permissions insuffisantes pour supprimer le salon")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la suppression du salon: {str(e)}")
                    # Tenter de nettoyer les données si le salon n'existe plus
                    if before.channel.id in self.temp_channels:
                        del self.temp_channels[before.channel.id]
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la gestion des salons: {str(e)}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return

        if channel.id not in self.temp_channels or payload.message_id != self.temp_channels[channel.id]['config_message']:
            return

        if payload.user_id != self.temp_channels[channel.id]['owner']:
            return

        member = channel.guild.get_member(payload.user_id)
        message = await channel.fetch_message(payload.message_id)
        await message.remove_reaction(payload.emoji, member)

        if str(payload.emoji) == '🔒':
            # Récupérer l'état du verrouillage actuel
            is_locked = self.temp_channels[channel.id].get('locked', False)
            
            if not is_locked:
                # Verrouiller le salon
                self.temp_channels[channel.id]['locked'] = True
                current_overwrites = channel.overwrites_for(channel.guild.default_role)
                current_overwrites.connect = False
                await channel.set_permissions(channel.guild.default_role, overwrite=current_overwrites)
                
                # Créer un embed pour le verrouillage
                embed = discord.Embed(
                    title="🔒 Salon verrouillé",
                    description="L'accès au salon est maintenant restreint.",
                    color=discord.Color.red()
                )
                embed.set_footer(text=f"Action exécutée par {member.display_name}", icon_url=member.display_avatar.url)
                await channel.send(embed=embed)
            else:
                # Déverrouiller le salon
                self.temp_channels[channel.id]['locked'] = False
                current_overwrites = channel.overwrites_for(channel.guild.default_role)
                current_overwrites.connect = True
                await channel.set_permissions(channel.guild.default_role, overwrite=current_overwrites)
                
                # Créer un embed pour le déverrouillage
                embed = discord.Embed(
                    title="🔓 Salon déverrouillé",
                    description="L'accès au salon est maintenant ouvert à tous.",
                    color=discord.Color.green()
                )
                embed.set_footer(text=f"Action exécutée par {member.display_name}", icon_url=member.display_avatar.url)
                await channel.send(embed=embed)

        elif str(payload.emoji) == '✏️':
            # Créer un embed pour la demande de changement de nom
            embed = discord.Embed(
                title="✏️ Modification du nom",
                description="Envoyez le nouveau nom du salon dans les 30 prochaines secondes.",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            try:
                response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author.id == payload.user_id and m.channel.id == channel.id
                )
                await channel.edit(name=f"🎧 {response.content}")
                
                # Embed de confirmation du changement de nom
                success_embed = discord.Embed(
                    title="✅ Nom modifié",
                    description=f"Le nom du salon a été changé en : **{response.content}**",
                    color=discord.Color.green()
                )
                success_embed.set_footer(text=f"Action exécutée par {member.display_name}", icon_url=member.display_avatar.url)
                await channel.send(embed=success_embed)
            except asyncio.TimeoutError:
                # Embed en cas d'expiration du délai
                timeout_embed = discord.Embed(
                    title="❌ Temps écoulé",
                    description="Vous n'avez pas répondu à temps. Opération annulée.",
                    color=discord.Color.red()
                )
                await channel.send(embed=timeout_embed)

        elif str(payload.emoji) == '👥':
            # Créer un embed pour la demande de limite de membres
            embed = discord.Embed(
                title="👥 Limite de membres",
                description="Envoyez le nombre maximum de membres (0-99) dans les 30 prochaines secondes.",
                color=discord.Color.blue()
            )
            await channel.send(embed=embed)
            try:
                response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author.id == payload.user_id and m.channel.id == channel.id
                )
                limit = int(response.content)
                if 0 <= limit <= 99:
                    await channel.edit(user_limit=limit)
                    
                    # Embed de confirmation de la limite
                    success_embed = discord.Embed(
                        title="✅ Limite définie",
                        description=f"Le salon est maintenant limité à **{limit}** membres.",
                        color=discord.Color.green()
                    )
                    success_embed.set_footer(text=f"Action exécutée par {member.display_name}", icon_url=member.display_avatar.url)
                    await channel.send(embed=success_embed)
                else:
                    # Embed en cas de valeur invalide
                    error_embed = discord.Embed(
                        title="❌ Valeur invalide",
                        description="Veuillez entrer un nombre entre 0 et 99.",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=error_embed)
            except (asyncio.TimeoutError, ValueError):
                # Embed en cas d'erreur
                error_embed = discord.Embed(
                    title="❌ Erreur",
                    description="Temps écoulé ou valeur invalide. Opération annulée.",
                    color=discord.Color.red()
                )
                await channel.send(embed=error_embed)

        elif str(payload.emoji) == '👑':
            # Créer un embed pour la demande de transfert de propriété
            embed = discord.Embed(
                title="👑 Transfert de propriété",
                description="Mentionnez (@user) le nouveau propriétaire du salon.",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
            try:
                response = await self.bot.wait_for(
                    'message',
                    timeout=30.0,
                    check=lambda m: m.author.id == payload.user_id and m.channel.id == channel.id and len(m.mentions) == 1
                )
                new_owner = response.mentions[0]
                if new_owner in channel.members:
                    self.temp_channels[channel.id]['owner'] = new_owner.id
                    await channel.set_permissions(new_owner, manage_channels=True, manage_permissions=True)
                    await channel.set_permissions(member, overwrite=None)
                    
                    # Embed de confirmation du transfert
                    success_embed = discord.Embed(
                        title="👑 Propriété transférée",
                        description=f"**{new_owner.display_name}** est maintenant le propriétaire de ce salon.",
                        color=discord.Color.gold()
                    )
                    success_embed.set_footer(text=f"Action exécutée par {member.display_name}", icon_url=member.display_avatar.url)
                    await channel.send(embed=success_embed)
                else:
                    # Embed en cas de membre absent
                    error_embed = discord.Embed(
                        title="❌ Membre non présent",
                        description="Cette personne n'est pas dans le salon.",
                        color=discord.Color.red()
                    )
                    await channel.send(embed=error_embed)
            except asyncio.TimeoutError:
                # Embed en cas d'expiration du délai
                timeout_embed = discord.Embed(
                    title="❌ Temps écoulé",
                    description="Vous n'avez pas répondu à temps. Opération annulée.",
                    color=discord.Color.red()
                )
                await channel.send(embed=timeout_embed)

        elif str(payload.emoji) == '🗑️':
            # Créer un embed pour la confirmation de suppression
            confirm_embed = discord.Embed(
                title="⚠️ Confirmation de suppression",
                description="Êtes-vous sûr de vouloir supprimer ce salon ?\nRéagissez avec ✅ pour confirmer.",
                color=discord.Color.orange()
            )
            confirm_msg = await channel.send(embed=confirm_embed)
            await confirm_msg.add_reaction('✅')
            
            try:
                await self.bot.wait_for(
                    'reaction_add',
                    timeout=30.0,
                    check=lambda r, u: u.id == payload.user_id and str(r.emoji) == '✅' and r.message.id == confirm_msg.id
                )
                # La suppression sera effectuée directement
                await channel.delete()
                del self.temp_channels[channel.id]
            except asyncio.TimeoutError:
                await confirm_msg.delete()
                # Embed pour l'annulation de la suppression
                cancel_embed = discord.Embed(
                    title="❌ Suppression annulée",
                    description="L'opération de suppression a été annulée.",
                    color=discord.Color.green()
                )
                await channel.send(embed=cancel_embed, delete_after=5)

async def setup(bot):
    await bot.add_cog(PrivateVoiceChannels(bot))
