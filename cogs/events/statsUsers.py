import discord
from discord.ext import commands, tasks
import json
import os
import datetime
import re
import logging
from collections import defaultdict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

# Récupérer les mots filtrés pour les jeux
filtered_words_str = os.getenv("FILTERED_GAME_WORDS", "")
filtered_game_words = filtered_words_str.split(",") if filtered_words_str else []

class StatsListener(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = 'data/stats.json'
        self.filtered_game_words = filtered_game_words
        self.init_stats_data()
        self.check_voice_time.start()
        self.track_activities.start()
        self.update_history.start()

    def should_filter_game(self, game_name):
        """Vérifie si le nom du jeu contient un des mots à filtrer"""
        if not game_name:
            return False

        # Convertir le nom du jeu en minuscules pour une comparaison insensible à la casse
        game_name_lower = game_name.lower()

        # Vérifier si l'un des mots filtrés est présent dans le nom du jeu
        for word in self.filtered_game_words:
            if word.lower() in game_name_lower:
                return True
        return False

    def init_stats_data(self):
        """Initialise ou charge les données de statistiques"""
        if os.path.exists('data/stats.json'):
            with open('data/stats.json', 'r', encoding='utf-8') as f:
                self.stats_data = json.load(f)
        else:
            self.stats_data = {
                'messages': {},
                'voice_time': {},
                'last_online': {},
                'channels': {'text': {}, 'voice': {}},
                'emojis': {},
                'reactions': {},
                'hourly_activity': {str(i): 0 for i in range(24)},
                'daily_activity': {str(i): 0 for i in range(7)},
                'games': {},
                'streaming': {},
                'message_history': {},
                'voice_history': {},
                'commands_used': 0
            }

    async def load_stats(self):
        """Charge les statistiques depuis le fichier"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.stats_data = json.load(f)
            else:
                self.init_default_stats()
                self.save_stats()

            # Structure complète requise
            required_keys = {
                'messages': {},
                'voice_time': {},
                'last_online': {},
                'channels': {'text': {}, 'voice': {}},
                'emojis': {},
                'reactions': {},
                'hourly_activity': {str(i): 0 for i in range(24)},
                'daily_activity': {str(i): 0 for i in range(7)},
                'games': {},
                'streaming': {},
                'message_history': {},
                'voice_history': {},
                'commands_used': 0,
                'last_update': ""
            }

            # Vérification récursive des clés
            for key, default_value in required_keys.items():
                if key not in self.stats_data:
                    self.stats_data[key] = default_value
                elif isinstance(default_value, dict) and key in ['channels']:
                    for subkey, subvalue in default_value.items():
                        if subkey not in self.stats_data[key]:
                            self.stats_data[key][subkey] = subvalue

            self.save_stats()
            logger.info("📈 Données statistiques chargées")
        except Exception as e:
            logger.error(f"❌ Erreur de chargement des stats: {str(e)}")
            self.init_default_stats()

    def init_default_stats(self):
        """Initialise la structure par défaut des stats"""
        self.stats_data = {
            'messages': {},
            'voice_time': {},
            'last_online': {},
            'channels': {
                'text': {},
                'voice': {}
            },
            'emojis': {},
            'reactions': {},
            'hourly_activity': {str(i): 0 for i in range(24)},
            'daily_activity': {str(i): 0 for i in range(7)},
            'games': {},
            'streaming': {},
            'message_history': {},
            'voice_history': {},
            'commands_used': 0,
            'last_update': ""
        }

    def save_stats(self):
        """Sauvegarde les statistiques dans le fichier JSON"""
        os.makedirs('data', exist_ok=True)
        with open('data/stats.json', 'w', encoding='utf-8') as f:
            json.dump(self.stats_data, f, ensure_ascii=False, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user.name} - Système de statistiques activé")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        user_id = str(message.author.id)
        channel_id = str(message.channel.id)
        now = datetime.datetime.now()
        hour = str(now.hour)
        day = str(now.weekday())

        # Mise à jour des statistiques de messages
        self.stats_data['messages'][user_id] = self.stats_data['messages'].get(user_id, 0) + 1
        self.stats_data['channels']['text'][channel_id] = self.stats_data['channels']['text'].get(channel_id, 0) + 1
        self.stats_data['last_online'][user_id] = now.strftime("%Y-%m-%d %H:%M:%S")
        self.stats_data['hourly_activity'][hour] = self.stats_data['hourly_activity'].get(hour, 0) + 1
        self.stats_data['daily_activity'][day] = self.stats_data['daily_activity'].get(day, 0) + 1

        # Analyse des emojis
        custom_emojis = re.findall(r'<:\w+:(\d+)>', message.content)
        for emoji_id in custom_emojis:
            self.stats_data['emojis'][emoji_id] = self.stats_data['emojis'].get(emoji_id, 0) + 1

        self.save_stats()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        emoji = str(reaction.emoji.id) if isinstance(reaction.emoji, discord.Emoji) else str(reaction.emoji)
        self.stats_data['reactions'][emoji] = self.stats_data['reactions'].get(emoji, 0) + 1
        self.save_stats()

    @tasks.loop(minutes=1)
    async def check_voice_time(self):
        """Vérifie et met à jour le temps passé en vocal"""
        now = datetime.datetime.now()
        for guild in self.bot.guilds:
            for member in guild.members:
                if not member.bot and member.voice and member.voice.channel and not member.voice.afk:
                    user_id = str(member.id)
                    channel_id = str(member.voice.channel.id)
                    
                    # Mise à jour des stats vocales
                    self.stats_data['voice_time'][user_id] = self.stats_data['voice_time'].get(user_id, 0) + 1
                    self.stats_data['channels']['voice'][channel_id] = self.stats_data['channels']['voice'].get(channel_id, 0) + 1

        self.save_stats()

    @tasks.loop(minutes=5)
    async def track_activities(self):
        """Suit les activités des membres"""
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.bot:
                    continue
                
                user_id = str(member.id)
                for activity in member.activities:
                    if activity.type == discord.ActivityType.playing:
                        game_name = activity.name
                        # Vérifier si le jeu doit être filtré
                        if not self.should_filter_game(game_name):
                            if game_name not in self.stats_data['games']:
                                self.stats_data['games'][game_name] = {}
                            self.stats_data['games'][game_name][user_id] = self.stats_data['games'][game_name].get(user_id, 0) + 5
                    
                    elif activity.type == discord.ActivityType.streaming:
                        self.stats_data['streaming'][user_id] = self.stats_data['streaming'].get(user_id, 0) + 5

        self.save_stats()

    @tasks.loop(hours=1)
    async def update_history(self):
        """Met à jour l'historique des statistiques"""
        today = datetime.datetime.now().strftime("%Y-%m-%d %H:00")
        
        for user_id, count in self.stats_data['messages'].items():
            if user_id not in self.stats_data['message_history']:
                self.stats_data['message_history'][user_id] = {}
            self.stats_data['message_history'][user_id][today] = count
        
        for user_id, minutes in self.stats_data['voice_time'].items():
            if user_id not in self.stats_data['voice_history']:
                self.stats_data['voice_history'][user_id] = {}
            self.stats_data['voice_history'][user_id][today] = minutes
        
        self.save_stats()

    def cog_unload(self):
        """Arrête les tâches quand le cog est déchargé"""
        self.check_voice_time.cancel()
        self.track_activities.cancel()
        self.update_history.cancel()

async def setup(bot):
    await bot.add_cog(StatsListener(bot))