import discord
import requests
import os
import json
from datetime import datetime
from discord.ext import commands

# Constantes pour ce module (copies des constantes de epic_games_events.py)
ROLE_ID = 1362434828506763456  # ID du rôle à mentionner
DATA_FOLDER = "data"
CACHE_FILE = os.path.join(DATA_FOLDER, "announced_games_cache.json")
EPIC_GAMES_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=fr&country=FR&allowCountries=FR"

# Fonctions utilitaires dupliquées depuis epic_games_events.py
def load_announced_games():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {"games": [], "last_update": ""}
    except Exception as e:
        print(f"Erreur lors du chargement du cache: {e}")
        return {"games": [], "last_update": ""}


def save_announced_games(game_ids, last_update=None):
    try:
        if not last_update:
            last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cache = {"games": game_ids, "last_update": last_update}
        
        # S'assurer que le dossier data existe toujours
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
            
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
            
        print(f"Cache sauvegardé dans {CACHE_FILE}")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde du cache: {e}")


def get_free_games():
    try:
        response = requests.get(EPIC_GAMES_URL)
        if response.status_code != 200:
            print(f"Erreur HTTP {response.status_code} lors de la requête vers Epic Games")
            return [], []
        
        data = response.json()
        free_games = []
        game_ids = []
        
        # Vérifier que le chemin existe dans le JSON
        if not data.get("data") or not data["data"].get("Catalog") or not data["data"]["Catalog"].get("searchStore"):
            print("Format de données invalide depuis l'API Epic Games")
            return [], []
        
        for game in data["data"]["Catalog"]["searchStore"]["elements"]:
            # Vérifiez si le jeu est actuellement gratuit
            is_free = False
            end_date = None
            if game.get("promotions") and game["promotions"].get("promotionalOffers"):
                promotional_offers = game["promotions"]["promotionalOffers"]
                if promotional_offers and len(promotional_offers) > 0 and promotional_offers[0].get("promotionalOffers"):
                    for offer in promotional_offers[0]["promotionalOffers"]:
                        if offer.get("discountSetting") and offer["discountSetting"].get("discountPercentage") == 0:
                            is_free = True
                            # Récupérer la date de fin de l'offre
                            if offer.get("endDate"):
                                end_date = offer["endDate"]
                            break
            
            if is_free:
                game_id = game.get("id", "")
                title = game.get("title", "Jeu sans titre")
                
                # Construction correcte de l'URL
                url = None
                # Utiliser le pageSlug s'il existe
                if game.get("catalogNs") and game["catalogNs"].get("mappings"):
                    for mapping in game["catalogNs"]["mappings"]:
                        if mapping.get("pageSlug"):
                            url = f'https://store.epicgames.com/fr/p/{mapping["pageSlug"]}'
                            break
                
                # Utiliser le productSlug comme solution de repli
                if not url and game.get("productSlug") and game["productSlug"] != "[]":
                    url = f'https://store.epicgames.com/fr/p/{game["productSlug"]}'
                
                # Si toujours pas d'URL, utiliser l'URL du jeu si disponible
                if not url and game.get("urlSlug"):
                    url = f'https://store.epicgames.com/fr/p/{game["urlSlug"]}'
                    
                # Si aucune méthode ne fonctionne, utiliser l'offerId
                if not url and game.get("id"):
                    url = f'https://store.epicgames.com/fr/offers/{game["id"]}'
                
                # Valeur par défaut si aucune URL trouvée
                if not url:
                    url = "https://store.epicgames.com"
                
                # Sélectionner une image appropriée
                image = None
                if game.get("keyImages"):
                    for img in game["keyImages"]:
                        if img.get("type") == "OfferImageWide" or img.get("type") == "DieselStoreFrontWide":
                            image = img.get("url")
                            break
                    
                    # Si aucune image large n'est trouvée, prendre la première disponible
                    if not image and len(game["keyImages"]) > 0 and game["keyImages"][0].get("url"):
                        image = game["keyImages"][0]["url"]
                
                # Ajouter le jeu à la liste
                free_games.append((game_id, title, url, image, end_date))
                game_ids.append(game_id)
        
        return free_games, game_ids
    except Exception as e:
        print(f"Erreur lors de la récupération des jeux gratuits: {e}")
        return [], []


def create_game_embed(title, url, image, end_date):
    embed = discord.Embed(
        title=title, 
        url=url, 
        description="Disponible gratuitement sur Epic Games Store!", 
        color=0x0078f2  # Couleur officielle d'Epic Games (bleu)
    )
    
    if image:
        embed.set_image(url=image)
    
    # Ajouter la date d'expiration si disponible
    if end_date:
        try:
            expiry_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            embed.add_field(name="Disponible jusqu'au", value=expiry_date.strftime("%d/%m/%Y à %H:%M"))
        except Exception as e:
            print(f"Erreur lors du parsing de la date d'expiration: {e}")
    
    # Footer uniforme pour tous les embeds
    embed.set_footer(text="Epic Games Bot • Mis à jour le " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
    
    return embed


# Cog pour les commandes
class EpicGamesCommands(commands.Cog):
    """Commandes pour interagir avec le bot Epic Games"""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="epicgames")
    async def epicgames_command(self, ctx):
        """Affiche les jeux gratuits disponibles actuellement sur Epic Games Store"""
        try:
            games, _ = get_free_games()
            if not games:
                # Embed pour aucun jeu disponible
                no_games_embed = discord.Embed(
                    title="Aucun jeu gratuit disponible", 
                    description="Il n'y a actuellement aucun jeu gratuit sur Epic Games Store.",
                    color=0xFFA500  # Orange pour information
                )
                no_games_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
                await ctx.send(embed=no_games_embed)
                return
            
            # Pour la commande manuelle, on affiche tous les jeux sans vérifier le cache
            role_mention = f"<@&{ROLE_ID}>"
            
            # Création d'un embed d'annonce
            announcement_embed = discord.Embed(
                title="🎮 Jeux gratuits sur Epic Games ! 🎮",
                description=f"Voici les jeux gratuits actuellement disponibles sur Epic Games Store {role_mention}",
                color=0x0078f2
            )
            announcement_embed.set_footer(text="Epic Games Bot • Mis à jour le " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
            
            await ctx.send(embed=announcement_embed)
            
            for _, title, url, image, end_date in games:
                embed = create_game_embed(title, url, image, end_date)
                await ctx.send(embed=embed)
                
        except Exception as e:
            # Embed d'erreur
            error_embed = discord.Embed(
                title="❌ Erreur", 
                description=f"Une erreur s'est produite lors de la récupération des jeux gratuits: {str(e)}",
                color=0xFF0000
            )
            error_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
            await ctx.send(embed=error_embed)

    @commands.command(name="resetcache")
    @commands.has_permissions(administrator=True)
    async def reset_cache(self, ctx):
        """Réinitialise le cache des jeux annoncés (admin uniquement)"""
        try:
            save_announced_games([])
            
            # Embed de succès
            success_embed = discord.Embed(
                title="✅ Cache réinitialisé", 
                description="Le cache des jeux annoncés a été réinitialisé. Les prochaines vérifications annonceront tous les jeux gratuits disponibles.",
                color=0x00FF00  # Vert pour succès
            )
            success_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
            await ctx.send(embed=success_embed)
            
        except Exception as e:
            # Embed d'erreur
            error_embed = discord.Embed(
                title="❌ Erreur", 
                description=f"Erreur lors de la réinitialisation du cache: {str(e)}",
                color=0xFF0000
            )
            error_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
            await ctx.send(embed=error_embed)

    @reset_cache.error
    async def reset_cache_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            # Embed pour permission manquante
            perm_error_embed = discord.Embed(
                title="⛔ Accès refusé", 
                description="Vous n'avez pas les permissions nécessaires pour exécuter cette commande.",
                color=0xFF0000
            )
            perm_error_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
            await ctx.send(embed=perm_error_embed)

    @commands.command(name="help")
    async def help_command(self, ctx):
        """Affiche l'aide du bot Epic Games"""
        help_embed = discord.Embed(
            title="📚 Aide Bot Epic Games",
            description="Voici la liste des commandes disponibles pour le bot Epic Games:",
            color=0x0078f2
        )
        
        help_embed.add_field(
            name="!epicgames", 
            value="Affiche les jeux gratuits actuellement disponibles sur Epic Games Store", 
            inline=False
        )
        
        help_embed.add_field(
            name="!resetcache", 
            value="[Admin uniquement] Réinitialise le cache des jeux annoncés", 
            inline=False
        )
        
        help_embed.add_field(
            name="!help", 
            value="Affiche ce message d'aide", 
            inline=False
        )
        
        help_embed.add_field(
            name="À propos", 
            value="Ce bot vérifie automatiquement (toutes les 24h) les nouveaux jeux gratuits sur Epic Games Store et les annonce dans le canal désigné.", 
            inline=False
        )
        
        help_embed.set_footer(text="Epic Games Bot • " + datetime.now().strftime("%d/%m/%Y à %H:%M"))
        await ctx.send(embed=help_embed)


# Fonction setup standard pour discord.py
def setup(bot):
    # Initialiser le dossier de données si nécessaire
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
    
    # Ajouter le cog au bot
    bot.add_cog(EpicGamesCommands(bot))