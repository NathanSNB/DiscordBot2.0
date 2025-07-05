import discord
import json
import os
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime


class EmbedManager:
    """Gestionnaire d'embeds centralisé pour maintenir une apparence cohérente et professionnelle"""

    _default_color = None  # Cache de la couleur par défaut

    # Constantes unifiées pour les footers et headers d'embed
    # Footer standard pour tous les embeds
    FOOTER_STANDARD = "MathysieBot™ • Développé avec ❤️ par l'équipe Mathysie"

    # Header standard pour tous les embeds
    HEADER_STANDARD = "🌟 MathysieBot™"

    # Constantes spéciales pour les cas d'usage spécifiques
    HEADER_WELCOME = "🌟 Bienvenue sur {guild_name} !"
    HEADER_ACCESS_GRANTED = "✅ Accès accordé !"
    FOOTER_WELCOME = (
        "Une fois ces étapes terminées, tu auras accès à l'ensemble du serveur !"
    )

    # Emojis professionnels pour différents types d'embed
    EMOJIS = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "music": "🎵",
        "stats": "📊",
        "tools": "🔧",
        "settings": "⚙️",
        "help": "❓",
        "user": "👤",
        "server": "🏠",
        "bot": "🤖",
        "time": "⏰",
        "star": "⭐",
        "fire": "🔥",
        "trophy": "🏆",
        "game": "🎮",
        "link": "🔗",
        "download": "📥",
        "upload": "📤",
        "search": "🔍",
        "lock": "🔒",
        "unlock": "🔓",
        "shield": "🛡️",
        "crown": "👑",
        "diamond": "💎",
        "rocket": "🚀",
        "heart": "❤️",
        "thumbsup": "👍",
        "thumbsdown": "👎",
        "wave": "👋",
        "party": "🎉",
        "bell": "🔔",
        "mail": "📧",
        "folder": "📁",
        "page": "📄",
        "bookmark": "🔖",
        "calendar": "📅",
        "clock": "🕐",
        "chart": "📈",
        "graph": "📊",
        "target": "🎯",
        "medal": "🏅",
        "gem": "💠",
        "flash": "⚡",
        "bulb": "💡",
    }

    # Couleurs professionnelles
    COLORS = {
        "primary": discord.Color(0x2BA3B3),  # Bleu principal
        "success": discord.Color(0x00D166),  # Vert succès
        "error": discord.Color(0xFF3838),  # Rouge erreur
        "warning": discord.Color(0xFFB800),  # Orange avertissement
        "info": discord.Color(0x3498DB),  # Bleu information
        "secondary": discord.Color(0x6C757D),  # Gris secondaire
        "dark": discord.Color(0x2C2F33),  # Sombre
        "light": discord.Color(0xF8F9FA),  # Clair
        "purple": discord.Color(0x9B59B6),  # Violet
        "pink": discord.Color(0xE91E63),  # Rose
        "orange": discord.Color(0xFF9500),  # Orange
        "yellow": discord.Color(0xF1C40F),  # Jaune
        "green": discord.Color(0x2ECC71),  # Vert
        "red": discord.Color(0xE74C3C),  # Rouge
        "blue": discord.Color(0x3498DB),  # Bleu
        "indigo": discord.Color(0x6610F2),  # Indigo
        "teal": discord.Color(0x20C997),  # Turquoise
        "cyan": discord.Color(0x17A2B8),  # Cyan
    }

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

    @classmethod
    def create_professional_embed(
        cls,
        title: str,
        description: Optional[str] = None,
        embed_type: str = "info",
        fields: Optional[List[Dict[str, Any]]] = None,
        thumbnail: Optional[str] = None,
        image: Optional[str] = None,
        author: Optional[Dict[str, str]] = None,
        timestamp: bool = True,
        footer_override: Optional[str] = None,
        color_override: Optional[discord.Color] = None,
        **kwargs,
    ) -> discord.Embed:
        """
        Crée un embed professionnel avec une structure standardisée

        Args:
            title: Titre de l'embed
            description: Description de l'embed
            embed_type: Type d'embed (success, error, warning, info, etc.)
            fields: Liste des champs à ajouter
            thumbnail: URL de la miniature
            image: URL de l'image
            author: Dictionnaire avec name, url, icon_url
            timestamp: Ajouter un timestamp
            footer_override: Footer personnalisé (sinon utilise le standard)
            color_override: Couleur personnalisée
            **kwargs: Arguments supplémentaires

        Returns:
            discord.Embed: L'embed créé
        """
        # Déterminer la couleur
        if color_override:
            color = color_override
        elif embed_type in cls.COLORS:
            color = cls.COLORS[embed_type]
        else:
            color = cls.get_default_color()

        # Ajouter emoji au titre si applicable
        emoji = cls.EMOJIS.get(embed_type, "")
        if emoji and not title.startswith(emoji):
            title = f"{emoji} {title}"

        # Créer l'embed
        embed = discord.Embed(
            title=title, description=description, color=color, **kwargs
        )

        # Ajouter l'auteur si fourni
        if author:
            embed.set_author(
                name=author.get("name", ""),
                url=author.get("url", ""),
                icon_url=author.get("icon_url", ""),
            )

        # Ajouter les champs
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get("name", ""),
                    value=field.get("value", ""),
                    inline=field.get("inline", True),
                )

        # Ajouter thumbnail et image
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        if image:
            embed.set_image(url=image)

        # Ajouter timestamp
        if timestamp:
            embed.timestamp = datetime.utcnow()

        # Ajouter footer
        footer_text = footer_override or cls.FOOTER_STANDARD
        embed.set_footer(text=footer_text)

        return embed

    @classmethod
    def create_success_embed(
        cls, title: str, description: Optional[str] = None, **kwargs
    ) -> discord.Embed:
        """Crée un embed de succès standardisé"""
        return cls.create_professional_embed(
            title=title, description=description, embed_type="success", **kwargs
        )

    @classmethod
    def create_error_embed(
        cls, title: str, description: Optional[str] = None, **kwargs
    ) -> discord.Embed:
        """Crée un embed d'erreur standardisé"""
        return cls.create_professional_embed(
            title=title, description=description, embed_type="error", **kwargs
        )

    @classmethod
    def create_warning_embed(
        cls, title: str, description: Optional[str] = None, **kwargs
    ) -> discord.Embed:
        """Crée un embed d'avertissement standardisé"""
        return cls.create_professional_embed(
            title=title, description=description, embed_type="warning", **kwargs
        )

    @classmethod
    def create_info_embed(
        cls, title: str, description: Optional[str] = None, **kwargs
    ) -> discord.Embed:
        """Crée un embed d'information standardisé"""
        return cls.create_professional_embed(
            title=title, description=description, embed_type="info", **kwargs
        )

    @classmethod
    def create_command_embed(
        cls,
        command_name: str,
        description: str,
        usage: Optional[str] = None,
        examples: Optional[List[str]] = None,
        **kwargs,
    ) -> discord.Embed:
        """Crée un embed standardisé pour l'aide des commandes"""
        fields = []

        if usage:
            fields.append(
                {
                    "name": f"{cls.EMOJIS['help']} Utilisation",
                    "value": f"`{usage}`",
                    "inline": False,
                }
            )

        if examples:
            examples_text = "\n".join([f"`{ex}`" for ex in examples])
            fields.append(
                {
                    "name": f"{cls.EMOJIS['star']} Exemples",
                    "value": examples_text,
                    "inline": False,
                }
            )

        return cls.create_professional_embed(
            title=f"Commande: {command_name}",
            description=description,
            embed_type="help",
            fields=fields,
            **kwargs,
        )

    @classmethod
    def create_stats_embed(
        cls, title: str, stats_data: Dict[str, Any], **kwargs
    ) -> discord.Embed:
        """Crée un embed standardisé pour les statistiques"""
        fields = []

        for key, value in stats_data.items():
            # Formatage intelligent des valeurs
            if isinstance(value, (int, float)):
                if value >= 1000000:
                    formatted_value = f"{value/1000000:.1f}M"
                elif value >= 1000:
                    formatted_value = f"{value/1000:.1f}K"
                else:
                    formatted_value = str(value)
            else:
                formatted_value = str(value)

            fields.append({"name": key, "value": formatted_value, "inline": True})

        return cls.create_professional_embed(
            title=title, embed_type="stats", fields=fields, **kwargs
        )

    @classmethod
    def create_user_embed(
        cls,
        user: discord.Member,
        additional_info: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> discord.Embed:
        """Crée un embed standardisé pour les informations utilisateur"""
        fields = [
            {
                "name": f"{cls.EMOJIS['user']} Nom d'utilisateur",
                "value": f"{user.mention}",
                "inline": True,
            },
            {
                "name": f"{cls.EMOJIS['calendar']} Rejoint le serveur",
                "value": f"<t:{int(user.joined_at.timestamp())}:R>",
                "inline": True,
            },
            {
                "name": f"{cls.EMOJIS['clock']} Compte créé",
                "value": f"<t:{int(user.created_at.timestamp())}:R>",
                "inline": True,
            },
        ]

        if additional_info:
            for key, value in additional_info.items():
                fields.append({"name": key, "value": str(value), "inline": True})

        return cls.create_professional_embed(
            title=f"Profil de {user.display_name}",
            embed_type="user",
            fields=fields,
            thumbnail=user.display_avatar.url,
            **kwargs,
        )

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
