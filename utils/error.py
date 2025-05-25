import discord
from discord.ext import commands
import logging
import time
from collections import defaultdict
from utils.embed_manager import EmbedManager

logger = logging.getLogger('bot')

class ErrorHandler:
    _recent_errors = defaultdict(dict)  # Cache pour les erreurs par utilisateur et par canal
    _error_timeout = 5  # Temps en secondes avant qu'un message d'erreur similaire puisse réapparaître

    @staticmethod
    async def send_error_message(ctx, message: str) -> None:
        """Envoie un message d'erreur formaté sur Discord (sans duplication)"""
        # Créer une clé unique pour cette erreur
        error_key = f"{ctx.channel.id}:{message}"
        current_time = time.time()

        # Vérifier si une erreur similaire a été envoyée récemment
        if ctx.author.id in ErrorHandler._recent_errors:
            if error_key in ErrorHandler._recent_errors[ctx.author.id]:
                last_time = ErrorHandler._recent_errors[ctx.author.id][error_key]
                if current_time - last_time < ErrorHandler._error_timeout:
                    return  # Ne pas envoyer de message si une erreur similaire est trop récente

        # Mettre à jour le cache des erreurs
        ErrorHandler._recent_errors[ctx.author.id][error_key] = current_time

        # Créer et envoyer l'embed d'erreur
        embed = EmbedManager.create_embed(
            title="❌ Erreur",
            description=message,
            color=discord.Color.red()  # Garder la couleur rouge pour les erreurs
        )
        await ctx.send(embed=embed)

        # Nettoyer les anciennes entrées du cache
        ErrorHandler._clean_error_cache()

    @staticmethod
    async def handle_command_error(ctx, error):
        """Gère les erreurs de commande de manière centralisée"""
        if isinstance(error, commands.MissingPermissions):
            embed = EmbedManager.create_embed(
                title="❌ Permission refusée",
                description="Vous n'avez pas les permissions nécessaires pour exécuter cette commande.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
            return True
        
        # Ajouter d'autres cas d'erreurs communs ici
        
        return False

    @staticmethod
    def _clean_error_cache():
        """Nettoie le cache des erreurs périmées"""
        current_time = time.time()
        for user_id in list(ErrorHandler._recent_errors.keys()):
            user_errors = ErrorHandler._recent_errors[user_id]
            for error_key in list(user_errors.keys()):
                if current_time - user_errors[error_key] > ErrorHandler._error_timeout:
                    del user_errors[error_key]
            if not user_errors:
                del ErrorHandler._recent_errors[user_id]