from discord.ext import commands
from typing import Dict, List, Tuple, Optional, Callable

def command_help(
    description: str,
    usage: Optional[str] = None,
    examples: Optional[List[str]] = None,
    permission_level: Optional[int] = None,
    hidden: bool = False
) -> Callable:
    """
    Décorateur qui permet de standardiser l'aide des commandes
    
    Args:
        description: Description détaillée de la commande
        usage: Comment utiliser la commande (arguments)
        examples: Liste d'exemples d'utilisation
        permission_level: Niveau de permission requis (0-5)
        hidden: Si la commande doit être cachée de l'aide
        
    Retourne:
        Un décorateur à appliquer sur une commande
    """
    def decorator(func):
        # Définir l'attribut help pour la description
        func.help = description
        
        # Définir l'usage si fourni
        if usage:
            func.usage = usage
            
        # Ajouter les exemples si fournis
        if examples:
            func.examples = examples
            
        # Définir le niveau de permission si fourni
        if permission_level is not None:
            func.permission_level = permission_level
            
        # Définir si la commande est cachée
        func.hidden = hidden
        
        return func
    return decorator

def ensure_help_compatibility(bot):
    """
    S'assure que toutes les commandes ont les attributs nécessaires 
    pour le système d'aide
    """
    for command in bot.commands:
        if not hasattr(command, 'help') or command.help is None:
            command.help = "Aucune description disponible."
            
        if not hasattr(command, 'usage'):
            command.usage = ""
            
        if not hasattr(command, 'permission_level'):
            command.permission_level = None
    
    # S'assurer que tous les cogs sont visibles dans l'aide
    for cog_name, cog in bot.cogs.items():
        # Vérifier si le cog a une docstring pour l'aide
        if not cog.__doc__ and cog_name == "ColorCommands":
            cog.__doc__ = """Commandes pour personnaliser les couleurs du bot et son apparence
            
            Ce module permet de:
            • Changer la couleur des embeds par nom ou code hexadécimal
            • Gérer automatiquement le rôle décoratif du bot
            • Synchroniser la couleur du rôle du bot avec les embeds
            • Actualiser les menus avec la nouvelle couleur choisie
            """
