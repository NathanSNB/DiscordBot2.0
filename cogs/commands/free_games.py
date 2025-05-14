import discord
import requests
import asyncio
import os
import json
from datetime import datetime
from discord.ext import commands
from bs4 import BeautifulSoup

class EpicGamesCog(commands.Cog):
    """Cog pour gérer les commandes des jeux gratuits Epic Games"""
    
    def __init__(self, bot):
        self.bot = bot
        self.ROLE_ID = 1362434828506763456  # ID du rôle à mentionner
        
        # Création du dossier data s'il n'existe pas
        self.DATA_FOLDER = "data"
        if not os.path.exists(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER)
            
        self.CACHE_FILE = os.path.join(self.DATA_FOLDER, "announced_games_cache.json")
        self.epic_games_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=fr&country=FR&allowCountries=FR"
        self.steam_url = "https://steamdb.info/upcoming/free/"
        
        # Vérifier si le cache existe, sinon le créer
        if not os.path.exists(self.CACHE_FILE):
            self.save_announced_games([])

    # Fonctions utilitaires pour la gestion du cache
    def load_announced_games(self):
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            return {"games": [], "last_update": ""}
        except Exception as e:
            print(f"Erreur lors du chargement du cache: {e}")
            return {"games": [], "last_update": ""}

    def save_announced_games(self, game_ids, steam_games=None, last_update=None):
        try:
            if not last_update:
                last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cache = {
                "games": game_ids,
                "steam_games": steam_games if steam_games is not None else [],
                "last_update": last_update
            }
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du cache: {e}")

    def get_free_games(self):
        try:
            response = requests.get(self.epic_games_url)
            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code} lors de la requête vers Epic Games")
                return [], []  # Retourne des listes vides au lieu de None
            
            data = response.json()
            free_games = []
            game_ids = []  # Pour tracker les IDs des jeux
            
            # Vérifier que le chemin existe dans le JSON
            if not data.get("data") or not data["data"].get("Catalog") or not data["data"]["Catalog"].get("searchStore"):
                print("Format de données invalide depuis l'API Epic Games")
                return [], []  # Retourne des listes vides au lieu de None
            
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
                    
                    # Amélioration du traitement de la description
                    short_desc = game.get("shortDescription", "").strip()
                    description = game.get("description", "").strip()
                    
                    final_description = ""
                    
                    # 1. Essayer d'utiliser la description courte si elle existe et n'est pas trop longue
                    if short_desc and len(short_desc) < 150:
                        final_description = short_desc
                    
                    # 2. Sinon, traiter la description longue
                    elif description:
                        # Nettoyer le texte
                        description = description.replace("\n", " ").replace("  ", " ")
                        
                        # Essayer de trouver une première phrase pertinente
                        sentences = description.split(". ")
                        first_sentence = sentences[0]
                        
                        if len(first_sentence) < 150:
                            final_description = first_sentence + "."
                        else:
                            # Si la première phrase est trop longue, prendre un segment significatif
                            words = first_sentence.split()
                            shortened = []
                            total_length = 0
                            
                            for word in words:
                                if total_length + len(word) > 120:
                                    break
                                shortened.append(word)
                                total_length += len(word) + 1
                            
                            final_description = " ".join(shortened) + "..."
                    
                    # 3. Message par défaut si aucune description valide
                    if not final_description:
                        final_description = "🎮 Un nouveau jeu gratuit à découvrir ! Cliquez pour plus d'informations."
                    
                    # 4. Ajouter des émojis pertinents en fonction du type de jeu
                    if "RPG" in game.get("tags", []) or "role" in description.lower():
                        final_description = "⚔️ " + final_description
                    elif "strategy" in description.lower() or "stratégie" in description.lower():
                        final_description = "🎯 " + final_description
                    elif "adventure" in description.lower() or "aventure" in description.lower():
                        final_description = "🗺️ " + final_description
                    elif "action" in description.lower():
                        final_description = "💥 " + final_description
                    else:
                        final_description = "🎮 " + final_description

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
                    free_games.append((game_id, title, url, image, end_date, final_description))
                    game_ids.append(game_id)
            
            return free_games, game_ids
        except Exception as e:
            print(f"Erreur lors de la récupération des jeux gratuits: {e}")
            return [], []  # Retourne des listes vides en cas d'erreur

    def get_steam_free_games(self):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
            }
            
            response = requests.get(self.steam_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Erreur HTTP {response.status_code} lors de la requête vers Steam")
                return [], []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            free_games = []
            game_ids = []
            
            # Chercher la table des jeux gratuits
            table = soup.find('table', {'class': 'table-products'})
            if not table:
                return [], []
                
            for row in table.find_all('tr', {'class': 'app'}):
                try:
                    app_id = row.get('data-appid')
                    if not app_id:
                        continue
                        
                    name_cell = row.find('td', {'class': 'appname'})
                    if not name_cell:
                        continue
                        
                    title = name_cell.text.strip()
                    url = f"https://store.steampowered.com/app/{app_id}"
                    image = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{app_id}/header.jpg"
                    
                    # Récupérer la date de fin
                    time_cell = row.find('td', class_='timeago')
                    end_date = time_cell.get('title') if time_cell else None
                    
                    free_games.append((app_id, title, url, image, end_date))
                    game_ids.append(app_id)
                    
                except Exception as e:
                    print(f"Erreur lors du traitement d'un jeu Steam: {e}")
                    continue
                   
            return free_games, game_ids
            
        except Exception as e:
            print(f"Erreur lors de la récupération des jeux Steam gratuits: {e}")
            return [], []

    @commands.command(name="epicgames")
    async def epicgames_command(self, ctx):
        """Affiche les jeux gratuits disponibles actuellement sur Epic Games Store"""
        try:
            games, _ = self.get_free_games()
            if not games:
                await ctx.send("Aucun jeu gratuit disponible sur Epic Games pour le moment.")
                return
            
            role_mention = f"<@&{self.ROLE_ID}>"
            await ctx.send(f"{role_mention} 🎮 **Nouveaux jeux gratuits !** 🎮")
            
            for _, title, url, image, end_date, description in games:
                embed = discord.Embed(
                    title=title,
                    url=url,
                    description=description,  # Utiliser la description du jeu
                    color=0x00ff00
                )
                if image:
                    embed.set_image(url=image)
                if end_date:
                    try:
                        expiry_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        embed.add_field(
                            name="Disponible jusqu'au", 
                            value=expiry_date.strftime("%d/%m/%Y à %H:%M"),
                            inline=False
                        )
                    except Exception as e:
                        print(f"Erreur lors du parsing de la date d'expiration: {e}")
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite lors de la récupération des jeux gratuits: {str(e)}")

    @commands.command(name="steamgames")
    async def steamgames_command(self, ctx):
        """Affiche les jeux gratuits temporaires sur Steam"""
        try:
            games, _ = self.get_steam_free_games()
            if not games:
                await ctx.send("Aucun jeu gratuit temporaire disponible sur Steam pour le moment.")
                return
            
            role_mention = f"<@&{self.ROLE_ID}>"
            await ctx.send(f"{role_mention} 🎮 **Jeux gratuits temporaires sur Steam !** 🎮")
            
            for _, title, url, image, end_date in games:
                embed = discord.Embed(title=title, url=url, description="Disponible gratuitement sur Steam !", color=0x1b2838)
                if image:
                    embed.set_image(url=image)
                if end_date:
                    embed.add_field(name="Disponible jusqu'au", value=end_date)
                await ctx.send(embed=embed)
                
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite lors de la récupération des jeux Steam: {str(e)}")

    @commands.command(name="resetcache")
    @commands.has_permissions(administrator=True)
    async def reset_cache(self, ctx):
        """Réinitialise le cache des jeux annoncés (admin uniquement)"""
        try:
            self.save_announced_games([])
            await ctx.send("✅ Le cache des jeux annoncés a été réinitialisé.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la réinitialisation du cache: {str(e)}")

    @reset_cache.error
    async def reset_cache_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")

def setup(bot):
    bot.add_cog(EpicGamesCog(bot))