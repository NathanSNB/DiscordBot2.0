import discord
from discord.ext import commands
import logging
import time
from collections import defaultdict

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
        embed = discord.Embed(
            title="❌ Erreur",
            description=message,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

        # Nettoyer les anciennes entrées du cache
        ErrorHandler._clean_error_cache()

    @staticmethod
    async def handle_command_error(ctx, error):
        """Gestionnaire d'erreurs centralisé pour toutes les commandes"""
        error_message = None

        if isinstance(error, commands.MissingRequiredArgument):
            error_message = "Il manque un argument requis."
        elif isinstance(error, commands.BadArgument):
            error_message = "L'argument fourni n'est pas valide."
        elif isinstance(error, commands.MissingPermissions):
            error_message = "Vous n'avez pas les permissions nécessaires."
        elif isinstance(error, commands.CheckFailure):
            error_message = "Accès refusé à cette commande."
        elif isinstance(error, commands.ChannelNotFound):
            error_message = "Salon introuvable."
        elif isinstance(error, commands.CommandNotFound):
            error_message = "Cette commande n'existe pas."
        else:
            error_message = f"Une erreur est survenue : {str(error)}"
            logger.error(f"Erreur non gérée : {str(error)}")

        if error_message:
            await ErrorHandler.send_error_message(ctx, error_message)

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