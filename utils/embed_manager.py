import discord
import json
import os
from typing import Optional
import logging


class EmbedManager:
    """Gestionnaire d'embeds centralisé pour maintenir une apparence cohérente"""

    _default_color = None  # Cache de la couleur par défaut

    # Constantes pour les footers d'embed
    FOOTER_DEFAULT = "MathysieBot™"
    FOOTER_SYSTEM_ROLES = "Bot Discord - Système de Rôles"
    FOOTER_SYSTEM_STATS = "📊 Système de Statistiques"
    FOOTER_SYSTEM_STATS_GAMETIME = "Temps total de jeu"
    FOOTER_SYSTEM_MUSIC = "Bot de Musique"
    FOOTER_SYSTEM_SUPPORT = "Support · Utilisez le menu déroulant pour ouvrir un ticket"
    FOOTER_SYSTEM_LOGS = "Système de Logs"
    FOOTER_SYSTEM_URGENT = "Système d'Urgence - Hérésie"
    FOOTER_SYSTEM_ECONOMY = "Système de Crédits Sociaux"
    FOOTER_SYSTEM_PERMISSIONS = "MathysieBot™ • Système de permissions"
    FOOTER_UTILITIES_WEB = "Bot Discord - Utilitaires Web"
    FOOTER_UTILITIES_GENERAL = "Bot Discord - Commandes Générales"
    FOOTER_YOUTUBE_INFO = "MathysieBot™ • YouTube Info"
    FOOTER_YOUTUBE_EXTRACTOR = "MathysieBot™ • YouTube Extractor"
    FOOTER_YOUTUBE_DOWNLOADER = "MathysieBot™ • YtDw"
    FOOTER_WIKIPEDIA = "MathysieBot™ • Wikipédia"
    FOOTER_HELP_SYSTEM = "Développé avec ❤️ par l'équipe Mathysie"
    FOOTER_HELP_NAVIGATION = (
        "Utilisez le menu déroulant pour naviguer entre les catégories"
    )
    FOOTER_WELCOME = (
        "Une fois ces étapes terminées, tu auras accès à l'ensemble du serveur !"
    )
    FOOTER_BEDTIME = "Passez une douce nuit"

    # Constantes pour les headers/titres d'embed
    HEADER_WELCOME = "🌟 Bienvenue sur {guild_name} !"
    HEADER_ACCESS_GRANTED = "✅ Accès accordé !"
    HEADER_TICKET_SYSTEM = "🎫 Système de Tickets"
    HEADER_RULES = "📜 Règlement du Serveur"
    HEADER_HELP_MAIN = "📚 Menu d'aide de MathysieBot™"
    HEADER_STATS = "📊 Statistiques"
    HEADER_ROLES = "🎭 Choisissez vos rôles"
    HEADER_MUSIC = "🎵 Lecteur de Musique"
    HEADER_WIKIPEDIA = "📖 Wikipédia"
    HEADER_YOUTUBE = "📺 YouTube"
    HEADER_URGENT = "🚨 Alerte d'Urgence"
    HEADER_ECONOMY = "💰 Système Économique"

    @classmethod
    def get_default_color(cls) -> discord.Color:
        """
        Récupère la couleur par défaut pour les embeds

        Essaie de lire la couleur depuis le fichier de configuration,
        sinon utilise la couleur par défaut du bot
        """
        if cls._default_color is not None:
            return cls._default_color

        try:
            if os.path.exists("data/bot_settings.json"):
                with open("data/bot_settings.json", "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "embed_color" in settings:
                        cls._default_color = discord.Color(settings["embed_color"])
                        return cls._default_color
        except Exception as e:
            # Log l'erreur pour débuggage
            logging.getLogger("bot").error(
                f"Erreur lors de la lecture de la couleur: {e}"
            )
            pass

        # Couleur par défaut si impossible de lire le fichier
        from config import Config

        cls._default_color = discord.Color(Config.DEFAULT_COLOR)
        return cls._default_color

    @classmethod
    def reload_color(cls):
        """Recharge la couleur depuis la configuration et déclenche l'événement de changement de couleur"""
        try:
            from config import Config

            Config.initialize_colors()

            # Réinitialiser le cache de couleur
            cls._default_color = None

            # Essayer de notifier les cogs du changement de couleur
            import asyncio

            async def notify_color_change():
                # Attendre un peu pour que tous les modules aient le temps de charger
                await asyncio.sleep(1)

                # Récupérer le bot de la boucle courante
                for task in asyncio.all_tasks():
                    if (
                        hasattr(task, "get_name")
                        and "Client._connect" in task.get_name()
                    ):
                        try:
                            client = task.get_coro().cr_frame.f_locals.get("self")
                            if client and hasattr(client, "dispatch"):
                                client.dispatch("color_change")
                                logging.getLogger("bot").info(
                                    "✅ Événement de changement de couleur envoyé"
                                )
                                break
                        except:
                            pass

            asyncio.create_task(notify_color_change())

            return Config.DEFAULT_COLOR
        except:
            # Fallback to default color if we can't import config
            return 0x2BA3B3

    @classmethod
    def create_embed(
        cls,
        title: str,
        description: Optional[str] = None,
        color: Optional[discord.Color] = None,
        footer: Optional[str] = None,
        footer_icon: Optional[str] = None,
        **kwargs,
    ):
        """
        Crée un embed standardisé avec la couleur par défaut

        Args:
            title: Titre de l'embed
            description: Description de l'embed (optionnel)
            color: Couleur personnalisée (si omise, utilise la couleur par défaut)
            footer: Texte du footer (optionnel)
            footer_icon: Icône du footer (optionnel)
            **kwargs: Arguments supplémentaires pour l'embed

        Returns:
            discord.Embed: L'embed créé
        """
        if color is None:
            color = cls.get_default_color()

        embed = discord.Embed(
            title=title, description=description, color=color, **kwargs
        )

        if footer is not None:
            embed.set_footer(text=footer, icon_url=footer_icon)

        return embed

    @staticmethod
    def create_welcome_dm(
        member: discord.Member, rules_channel: discord.TextChannel
    ) -> discord.Embed:
        """Crée un embed d'accueil pour les messages privés"""
        embed = discord.Embed(
            title=EmbedManager.HEADER_WELCOME.format(guild_name=member.guild.name),
            description=(
                "Nous sommes enchantés de t'accueillir parmi nous !\n"
                "Pour que ton intégration se passe au mieux, voici quelques étapes à suivre :"
            ),
            color=EmbedManager.get_default_color(),
        )

        # Étapes à suivre
        embed.add_field(
            name="📝 Première étape",
            value=f"Rends-toi dans le salon {rules_channel.mention}",
            inline=False,
        )

        embed.add_field(
            name="📖 Deuxième étape",
            value="Lis attentivement le règlement qui s'y trouve",
            inline=False,
        )

        embed.add_field(
            name="✅ Dernière étape",
            value="Clique sur la réaction ✅ sous le règlement pour obtenir accès au serveur",
            inline=False,
        )

        # Ajout d'un footer informatif
        embed.set_footer(text=EmbedManager.FOOTER_WELCOME)

        # Ajout de l'icône du serveur si disponible
        if member.guild.icon:
            embed.set_thumbnail(url=member.guild.icon.url)

        return embed

    @staticmethod
    def create_access_granted(
        guild: discord.Guild, roles_channel: discord.TextChannel
    ) -> discord.Embed:
        """Crée un embed de confirmation d'accès avec les informations sur les rôles"""
        embed = discord.Embed(
            title=EmbedManager.HEADER_ACCESS_GRANTED,
            description=(
                f"Bienvenue officiellement sur **{guild.name}** !\n"
                f"Tu as maintenant accès à l'ensemble du serveur."
            ),
            color=EmbedManager.get_default_color(),
        )

        # Ajout des informations sur les rôles
        embed.add_field(
            name="🎭 Attribution des Rôles",
            value=f"Rends-toi dans {roles_channel.mention} pour choisir tes rôles !",
            inline=False,
        )

        embed.add_field(
            name="📋 Comment faire ?",
            value="Choisis les rôles qui t'intéressent en cliquant sur les réactions correspondantes.",
            inline=False,
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        return embed

    @staticmethod
    def create_access_granted_dm(guild=None, roles_channel=None) -> discord.Embed:
        """Crée un embed pour le message de bienvenue en DM"""
        embed = discord.Embed(
            title=EmbedManager.HEADER_ACCESS_GRANTED,
            description=f"Bienvenue officiellement sur {guild.name if guild else 'notre serveur'} !\nTu as maintenant accès à l'ensemble du serveur.",
            color=EmbedManager.get_default_color(),
        )

        if roles_channel:
            embed.add_field(
                name="🎭 Attribution des Rôles",
                value=f"Rends-toi dans {roles_channel.mention} pour choisir tes rôles !",
                inline=False,
            )

        if guild and guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        return embed
