import discord
import requests
import asyncio
import os
import json
from datetime import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv

class EpicGamesCog(commands.Cog):
    """Cog pour gérer les annonces de jeux gratuits Epic Games"""
    
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1362436466332143706  # ID du salon
        self.ROLE_ID = 1362434828506763456  # ID du rôle à mentionner
        
        # Création du dossier data s'il n'existe pas
        self.DATA_FOLDER = "data"
        if not os.path.exists(self.DATA_FOLDER):
            os.makedirs(self.DATA_FOLDER)
            
        self.CACHE_FILE = os.path.join(self.DATA_FOLDER, "announced_games_cache.json")  # Chemin complet vers le fichier de cache
        self.epic_games_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=fr&country=FR&allowCountries=FR"
        
        # Vérifier si le cache existe, sinon le créer
        if not os.path.exists(self.CACHE_FILE):
            self.save_announced_games([])
        
        # Démarrer la tâche périodique
        self.check_epic_games.start()

    def cog_unload(self):
        """Arrêter les tâches lors du déchargement du cog"""
        self.check_epic_games.cancel()

    # Fonction pour gérer le cache des jeux annoncés
    def load_announced_games(self):
        try:
            if os.path.exists(self.CACHE_FILE):
                with open(self.CACHE_FILE, 'r') as f:
                    return json.load(f)
            return {"games": [], "last_update": ""}
        except Exception as e:
            print(f"Erreur lors du chargement du cache: {e}")
            return {"games": [], "last_update": ""}

    def save_announced_games(self, game_ids, last_update=None):
        try:
            if not last_update:
                last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cache = {"games": game_ids, "last_update": last_update}
            
            # S'assurer que le dossier data existe toujours
            if not os.path.exists(self.DATA_FOLDER):
                os.makedirs(self.DATA_FOLDER)
                
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(cache, f)
                
            print(f"Cache sauvegardé dans {self.CACHE_FILE}")
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
                    game_id = game.get("id", "")  # Récupérer l'ID du jeu
                    title = game.get("title", "Jeu sans titre")  # Valeur par défaut si pas de titre
                    
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
            return [], []  # Retourne des listes vides en cas d'erreur

    @tasks.loop(hours=24)
    async def check_epic_games(self):
        try:
            channel = self.bot.get_channel(self.CHANNEL_ID)
            if not channel:
                print(f"Impossible de trouver le canal avec l'ID {self.CHANNEL_ID}")
                return
            
            # Charger les jeux déjà annoncés
            cache = self.load_announced_games()
            announced_games = cache.get("games", [])  # Utiliser .get avec valeur par défaut
            
            # Récupérer les jeux gratuits actuels
            games, current_game_ids = self.get_free_games()  # Ne peut plus renvoyer None
            if not games:
                print("Aucun jeu gratuit disponible sur Epic Games pour le moment.")
                return  # Pas de message si pas de jeux pour éviter le spam
            
            # Filtrer pour n'obtenir que les nouveaux jeux
            new_games = []
            for game in games:
                game_id, title, url, image, end_date = game
                if game_id not in announced_games:
                    new_games.append((game_id, title, url, image, end_date))
            
            # Mettre à jour le cache avec tous les jeux actuels
            self.save_announced_games(current_game_ids)
            
            # S'il n'y a pas de nouveaux jeux, sortir sans rien faire
            if not new_games:
                print(f"Aucun nouveau jeu gratuit à annoncer. Jeux déjà annoncés: {announced_games}")
                return
                
            # Mentionner le rôle uniquement s'il y a de nouveaux jeux à annoncer
            role_mention = f"<@&{self.ROLE_ID}>"
            await channel.send(f"{role_mention} 🎮 **Nouveaux jeux gratuits sur Epic Games cette semaine !** 🎮")
            
            for game_id, title, url, image, end_date in new_games:
                embed = discord.Embed(title=title, url=url, description="Disponible gratuitement sur Epic Games !", color=0x00ff00)
                if image:
                    embed.set_image(url=image)
                
                # Ajouter la date d'expiration si disponible
                if end_date:
                    try:
                        expiry_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        embed.add_field(name="Disponible jusqu'au", value=expiry_date.strftime("%d/%m/%Y à %H:%M"))
                    except Exception as e:
                        print(f"Erreur lors du parsing de la date d'expiration: {e}")
                
                await channel.send(embed=embed)
                
        except Exception as e:
            print(f"Erreur lors de la vérification des jeux gratuits: {e}")
            if channel:
                await channel.send(f"Une erreur s'est produite lors de la récupération des jeux gratuits: {str(e)}")

    @check_epic_games.before_loop
    async def before_check_epic_games(self):
        """Attendre que le bot soit prêt avant de démarrer la tâche"""
        await self.bot.wait_until_ready()

    @commands.command(name="epicgames")
    async def epicgames_command(self, ctx):
        """Affiche les jeux gratuits disponibles actuellement sur Epic Games Store"""
        try:
            games, _ = self.get_free_games()  # Ne peut plus renvoyer None
            if not games:
                await ctx.send("Aucun jeu gratuit disponible sur Epic Games pour le moment.")
                return
            
            # Pour la commande manuelle, on affiche tous les jeux sans vérifier le cache
            role_mention = f"<@&{self.ROLE_ID}>"
            await ctx.send(f"{role_mention} 🎮 **Jeux gratuits sur Epic Games disponibles maintenant !** 🎮")
            
            for _, title, url, image, end_date in games:
                embed = discord.Embed(title=title, url=url, description="Disponible gratuitement sur Epic Games !", color=0x00ff00)
                if image:
                    embed.set_image(url=image)
                
                # Ajouter la date d'expiration si disponible
                if end_date:
                    try:
                        expiry_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                        embed.add_field(name="Disponible jusqu'au", value=expiry_date.strftime("%d/%m/%Y à %H:%M"))
                    except Exception as e:
                        print(f"Erreur lors du parsing de la date d'expiration: {e}")
                
                await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Une erreur s'est produite lors de la récupération des jeux gratuits: {str(e)}")

    @commands.command(name="resetcache")
    @commands.has_permissions(administrator=True)
    async def reset_cache(self, ctx):
        """Réinitialise le cache des jeux annoncés (admin uniquement)"""
        try:
            self.save_announced_games([])
            await ctx.send("✅ Le cache des jeux annoncés a été réinitialisé. Les prochaines vérifications annonceront tous les jeux gratuits disponibles.")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors de la réinitialisation du cache: {str(e)}")

    @reset_cache.error
    async def reset_cache_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")

# Fonction setup standard pour discord.py
def setup(bot):
    bot.add_cog(EpicGamesCog(bot))