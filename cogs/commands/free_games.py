import discord
import requests
import asyncio
import os
import json
from datetime import datetime
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Configuration globale
CHANNEL_ID = 1362436466332143706  # ID du salon
ROLE_ID = 1362434828506763456  # ID du rôle à mentionner
CACHE_FILE = "data/announced_games_cache.json"  # Fichier pour stocker les jeux déjà annoncés

class EpicGamesCog(commands.Cog):
    """Cog pour gérer les annonces de jeux gratuits sur Epic Games Store"""
    
    def __init__(self, bot):
        self.bot = bot
        self.epic_games_url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=fr&country=FR&allowCountries=FR"
        # Vérifier si le cache existe, sinon le créer
        if not os.path.exists(CACHE_FILE):
            self.save_announced_games([])
        self.check_epic_games.start()
    
    def cog_unload(self):
        """Appelé lorsque le cog est déchargé"""
        self.check_epic_games.cancel()
    
    # Fonction pour gérer le cache des jeux annoncés
    def load_announced_games(self):
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
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
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache, f)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du cache: {e}")

    def get_free_games(self):
        response = requests.get(self.epic_games_url)
        if response.status_code != 200:
            return None, None
        
        data = response.json()
        free_games = []
        game_ids = []  # Pour tracker les IDs des jeux
        
        # Vérifier que le chemin existe dans le JSON
        if not data.get("data") or not data["data"].get("Catalog") or not data["data"]["Catalog"].get("searchStore"):
            return free_games, game_ids
        
        for game in data["data"]["Catalog"]["searchStore"]["elements"]:
            # Vérifiez si le jeu est actuellement gratuit
            is_free = False
            if game.get("promotions") and game["promotions"].get("promotionalOffers"):
                promotional_offers = game["promotions"]["promotionalOffers"]
                if promotional_offers and len(promotional_offers) > 0 and promotional_offers[0].get("promotionalOffers"):
                    for offer in promotional_offers[0]["promotionalOffers"]:
                        if offer.get("discountSetting") and offer["discountSetting"].get("discountPercentage") == 0:
                            is_free = True
                            break
            
            if is_free:
                game_id = game.get("id", "")  # Récupérer l'ID du jeu
                title = game["title"]
                
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
                
                # Sélectionner une image appropriée
                image = None
                if game.get("keyImages"):
                    for img in game["keyImages"]:
                        if img.get("type") == "OfferImageWide" or img.get("type") == "DieselStoreFrontWide":
                            image = img["url"]
                            break
                    
                    # Si aucune image large n'est trouvée, prendre la première disponible
                    if not image and len(game["keyImages"]) > 0:
                        image = game["keyImages"][0]["url"]
                
                # Ajouter le jeu à la liste s'il a au moins un titre et une URL
                if title and url:
                    free_games.append((game_id, title, url, image))
                    game_ids.append(game_id)
        
        return free_games, game_ids

    @tasks.loop(hours=24)
    async def check_epic_games(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        if not channel:
            print(f"Impossible de trouver le canal avec l'ID {CHANNEL_ID}")
            return
        
        try:
            # Charger les jeux déjà annoncés
            cache = self.load_announced_games()
            announced_games = cache["games"]
            
            # Récupérer les jeux gratuits actuels
            games, current_game_ids = self.get_free_games()
            if not games:
                await channel.send("Aucun jeu gratuit disponible sur Epic Games pour le moment.")
                return
            
            # Filtrer pour n'obtenir que les nouveaux jeux
            new_games = []
            for game in games:
                game_id, title, url, image = game
                if game_id not in announced_games:
                    new_games.append((game_id, title, url, image))
            
            # Mettre à jour le cache avec tous les jeux actuels
            self.save_announced_games(current_game_ids)
            
            # S'il n'y a pas de nouveaux jeux, sortir sans rien faire
            if not new_games:
                print(f"Aucun nouveau jeu gratuit à annoncer. Jeux déjà annoncés: {announced_games}")
                return
                
            # Mentionner le rôle uniquement s'il y a de nouveaux jeux à annoncer
            role_mention = f"<@&{ROLE_ID}>"
            await channel.send(f"{role_mention} 🎮 **Nouveaux jeux gratuits sur Epic Games cette semaine !** 🎮")
            
            for game_id, title, url, image in new_games:
                embed = discord.Embed(title=title, url=url, description="Disponible gratuitement sur Epic Games !", color=0x00ff00)
                if image:
                    embed.set_image(url=image)
                await channel.send(embed=embed)
                
        except Exception as e:
            print(f"Erreur lors de la vérification des jeux gratuits: {e}")
            await channel.send(f"Une erreur s'est produite lors de la récupération des jeux gratuits: {str(e)}")

    @check_epic_games.before_loop
    async def before_check_epic_games(self):
        """Attendre que le bot soit prêt avant de démarrer la tâche"""
        await self.bot.wait_until_ready()

    @commands.command(name="epicgames")
    async def epicgames_command(self, ctx):
        """Affiche les jeux gratuits disponibles actuellement sur Epic Games Store"""
        try:
            games, _ = self.get_free_games()
            if not games:
                await ctx.send("Aucun jeu gratuit disponible sur Epic Games pour le moment.")
                return
            
            # Pour la commande manuelle, on affiche tous les jeux sans vérifier le cache
            role_mention = f"<@&{ROLE_ID}>"
            await ctx.send(f"{role_mention} 🎮 **Jeux gratuits sur Epic Games disponibles maintenant !** 🎮")
            
            for _, title, url, image in games:
                embed = discord.Embed(title=title, url=url, description="Disponible gratuitement sur Epic Games !", color=0x00ff00)
                if image:
                    embed.set_image(url=image)
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

# Fichier principal main.py
async def setup(bot):
    """Fonction pour charger le cog"""
    await bot.add_cog(EpicGamesCog(bot))

def main():
    """Fonction principale pour exécuter le bot"""
    intents = discord.Intents.default()
    intents.messages = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event
    async def on_ready():
        print(f'Connecté en tant que {bot.user} à {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        # Charger le cog
        await setup(EpicGamesCog(bot))

    bot.run(TOKEN)

if __name__ == "__main__":
    main()