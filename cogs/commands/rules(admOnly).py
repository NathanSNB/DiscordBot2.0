import discord
from discord.ext import commands
from utils import logger
from utils.error import ErrorHandler
from utils.rules_manager import RulesManager
from utils.embed_manager import EmbedManager
import json
import os

class RulesCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rules_file = 'data/rules.json'
        self.config_file = 'data/rules_config.json'
        self.load_rules()
        self.load_config()

    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.rules_channel_id = config.get('rules_channel_id')
                    self.rules_message_id = config.get('rules_message_id')
                    self.verified_role_id = config.get('verified_role_id')
            else:
                self.save_config()
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")

    def save_config(self):
        """Sauvegarde la configuration"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'rules_channel_id': self.rules_channel_id,
                    'rules_message_id': self.rules_message_id,
                    'verified_role_id': self.verified_role_id
                }, f, indent=4)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")

    def load_rules(self):
        """Charge les règles depuis le fichier JSON"""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    self.rules_data = json.load(f)
            else:
                self.rules_data = {}
        except Exception as e:
            print(f"Erreur lors du chargement des règles: {e}")

    def save_rules(self):
        """Sauvegarde les règles dans le fichier JSON"""
        try:
            os.makedirs(os.path.dirname(self.rules_file), exist_ok=True)
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.rules_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde des règles: {e}")

    def format_rules_embed(self, guild):
        """Crée l'embed des règles"""
        embed = discord.Embed(
            title="📜 Règlement du Serveur",
            description=self.rules_data["welcome_message"].format(server_name=guild.name),
            color=discord.Color(0x2BA3B3)
        )

        # Ajouter les règles
        for rule in self.rules_data["rules"]:
            embed.add_field(
                name=f"{rule['emoji']}・**{rule['title']}**",
                value=rule['description'],
                inline=False
            )

        # Ajouter les sanctions
        sanctions = self.rules_data["sanctions"]
        sanctions_text = "\n".join(f"> {sanction}" for sanction in sanctions["content"])
        embed.add_field(
            name=f"{sanctions['emoji']}・**{sanctions['title']}**",
            value=f"{sanctions_text}{sanctions['separator']}",
            inline=False
        )

        # Formater et ajouter le footer comme un champ séparé
        formatted_footer = self.rules_data["footer"].format(server_name=guild.name)
        embed.add_field(
            name="\u200b",  # Caractère invisible pour le nom du champ
            value=formatted_footer,
            inline=False
        )

        return embed

    @commands.command(
        name="setrules",
        help="Définit le salon des règles",
        description="Définit le salon où seront affichées les règles",
        usage="!setrules #salon"
    )
    @commands.has_permissions(administrator=True)
    async def set_rules_channel(self, ctx, channel: discord.TextChannel):
        """Configure le salon des règles"""
        self.rules_channel_id = channel.id
        self.save_config()
        await self.update_rules(ctx.guild)
        await ctx.send(f"✅ Salon des règles défini sur {channel.mention}")

    async def update_rules(self, guild):
        """Met à jour ou crée le message des règles"""
        if not self.rules_channel_id:
            return

        channel = guild.get_channel(self.rules_channel_id)
        if not channel:
            return

        # Supprimer l'ancien message s'il existe
        try:
            if self.rules_message_id:
                try:
                    old_message = await channel.fetch_message(self.rules_message_id)
                    await old_message.delete()
                except:
                    pass
        except Exception as e:
            print(f"Erreur lors de la suppression de l'ancien message: {e}")

        # Créer le nouvel embed
        embed = self.format_rules_embed(guild)

        # Envoyer le nouveau message
        try:
            message = await channel.send(embed=embed)
            self.rules_message_id = message.id
            await message.add_reaction("✅")
            self.save_config()
        except Exception as e:
            print(f"Erreur lors de l'envoi du nouveau message: {e}")

    @commands.command(name="setrole")
    @commands.has_permissions(administrator=True)
    async def set_verified_role(self, ctx, role: discord.Role):
        """Configure le rôle à attribuer après validation du règlement"""
        self.verified_role_id = role.id
        self.save_config()
        await ctx.send(f"✅ Rôle de vérification défini sur {role.mention}")

    @commands.command(name="setdefaultrole")
    @commands.has_permissions(administrator=True)
    async def set_default_role(self, ctx, role: discord.Role):
        """Définit le rôle par défaut pour les nouveaux membres"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        config['default_role_id'] = role.id
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
        
        await ctx.send(f"✅ Rôle par défaut défini sur {role.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Gestion de l'arrivée d'un nouveau membre"""
        try:
            # Message privé avec les instructions
            if self.rules_channel_id:
                channel = member.guild.get_channel(self.rules_channel_id)
                if channel:
                    try:
                        embed = EmbedManager.create_welcome_dm(member, channel)
                        await member.send(embed=embed)
                    except discord.Forbidden:
                        pass

        except Exception as e:
            print(f"Erreur lors de l'envoi du message de bienvenue : {str(e)}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Gestion des réactions sur le règlement"""
        if payload.message_id != self.rules_message_id or str(payload.emoji) != "✅":
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        if member.bot:
            return

        try:
            if self.verified_role_id:
                verified_role = guild.get_role(self.verified_role_id)
                if verified_role:
                    # Déléguer la gestion à RulesManager
                    await RulesManager.handle_rule_accept(member, verified_role)

            # Retirer la réaction dans tous les cas
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)

        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de la réaction: {str(e)}")

    @commands.command(
        name="updaterules",
        help="Met à jour les règles",
        description="Force la mise à jour du message des règles",
        usage="!updaterules"
    )
    @commands.has_permissions(administrator=True)
    async def update_rules_command(self, ctx):
        await RulesManager.refresh_rules(self.bot)
        await ctx.send("✅ Règles mises à jour")

async def setup(bot):
    await bot.add_cog(RulesCommands(bot))
