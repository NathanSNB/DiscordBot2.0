import discord
from discord.ext import commands, tasks
import os
from datetime import datetime
from ..commands.free_games import EpicGamesCog
from utils.embed_manager import EmbedManager

class EpicGamesEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.CHANNEL_ID = 1362436466332143706  # ID du salon
        self.ROLE_ID = 1362434828506763456  # ID du rôle à mentionner
        self.epic_games = EpicGamesCog(bot)  # Instance du cog de commandes
        self.check_all_games.start()  # Remplacer check_epic_games.start()

    def cog_unload(self):
        """Arrêter les tâches lors du déchargement du cog"""
        self.check_all_games.cancel()  # Remplacer check_epic_games.cancel()

    @tasks.loop(hours=1)  # Changer à 1 heure au lieu de 24
    async def check_all_games(self):
        """Vérifie les jeux gratuits sur Epic Games et Steam"""
        try:
            channel = self.bot.get_channel(self.CHANNEL_ID)
            if not channel:
                print(f"Impossible de trouver le canal avec l'ID {self.CHANNEL_ID}")
                return
            
            # Vérifier Epic Games
            await self.check_epic_games(channel)
            # Vérifier Steam
            await self.check_steam_games(channel)
                
        except Exception as e:
            print(f"Erreur lors de la vérification des jeux gratuits: {e}")
            if channel:
                await channel.send(f"Une erreur s'est produite lors de la vérification des jeux gratuits: {str(e)}")

    async def check_epic_games(self, channel):
        """Vérifie les jeux Epic Games"""
        try:
            cache = self.epic_games.load_announced_games()
            announced_games = cache.get("games", [])
            
            games, current_game_ids = self.epic_games.get_free_games()
            if not games:
                return
            
            new_games = [game for game in games if game[0] not in announced_games]
            
            if new_games:
                role_mention = f"<@&{self.ROLE_ID}>"
                await channel.send(f"{role_mention} 🎮 **Nouveaux jeux gratuits !** 🎮")
                
                for game_id, title, url, image, end_date, description in new_games:
                    embed = EmbedManager.create_embed(
                        title=title,
                        url=url,
                        description=description,
                        color=discord.Color.green()  # Couleur verte spécifique pour les jeux gratuits
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
                
                    await channel.send(embed=embed)
                
                self.epic_games.save_announced_games(current_game_ids)
                
        except Exception as e:
            print(f"Erreur lors de la vérification des jeux Epic Games: {e}")
            raise e

    async def check_steam_games(self, channel):
        """Vérifie les jeux Steam"""
        try:
            games, current_game_ids = self.epic_games.get_steam_free_games()
            if not games:
                return
            
            cache = self.epic_games.load_announced_games()
            announced_games = cache.get("steam_games", [])
            
            new_games = [game for game in games if game[0] not in announced_games]
            
            if new_games:
                role_mention = f"<@&{self.ROLE_ID}>"
                await channel.send(f"{role_mention} 🎮 **Nouveaux jeux gratuits temporaires sur Steam !** 🎮")
                
                for game_id, title, url, image, end_date in new_games:
                    embed = discord.Embed(
                        title=title,
                        url=url,
                        description="Disponible gratuitement sur Steam !",
                        color=0x1b2838
                    )
                    if image:
                        embed.set_image(url=image)
                    if end_date:
                        embed.add_field(name="Disponible jusqu'au", value=end_date)
                    
                    await channel.send(embed=embed)
                
                # Mettre à jour le cache avec les nouveaux jeux Steam
                cache["steam_games"] = current_game_ids
                self.epic_games.save_announced_games(cache["games"], steam_games=current_game_ids)
                
        except Exception as e:
            print(f"Erreur lors de la vérification des jeux Steam: {e}")
            raise e

    @check_all_games.before_loop
    async def before_check_all_games(self):
        """Attendre que le bot soit prêt avant de démarrer la tâche"""
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(EpicGamesEvents(bot))