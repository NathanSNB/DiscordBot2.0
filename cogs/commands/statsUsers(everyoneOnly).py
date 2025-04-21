import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import json
import os
from io import BytesIO
from collections import defaultdict
import logging
from dotenv import load_dotenv

load_dotenv()  # Charge les variables d'environnement du fichier .env

# Récupère la chaîne et transforme-la en liste
filtered_words_str = os.getenv("FILTERED_GAME_WORDS", "")
filtered_game_words = filtered_words_str.split(",") if filtered_words_str else []

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class StatsCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Assigner filtered_game_words à l'instance
        self.filtered_game_words = filtered_game_words
        self.load_stats()
        self.stats_cache = {}
        self.last_update = 0

    def load_stats(self):
        try:
            if os.path.exists('data/stats.json'):
                with open('data/stats.json', 'r', encoding='utf-8') as f:
                    self.stats_data = json.load(f)
            else:
                self.stats_data = self.init_empty_stats()
            logger.info("📈 Données statistiques chargées")
        except json.JSONDecodeError:
            logger.error("❌ Erreur de lecture du fichier stats.json")
            self.stats_data = self.init_empty_stats()
        except Exception as e:
            logger.error(f"❌ Erreur chargement stats: {str(e)}")

    def init_empty_stats(self):
        """Initialise des statistiques vides"""
        return {
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

    def is_rate_limited(self, user_id):
        now = datetime.datetime.now().timestamp()
        if user_id in self.stats_cache:
            if now - self.stats_cache[user_id] < 60:  # 1 minute de cooldown
                return True
        self.stats_cache[user_id] = now
        return False
        
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

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs"""
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Il manque un argument requis.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ L'argument fourni n'est pas valide.")
        else:
            await ctx.send(f"❌ Une erreur est survenue : {str(error)}")

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        """Traque les activités de jeu des membres"""
        try:
            # Ignorer les bots
            if after.bot:
                return
                
            # Vérifie les changements d'activité
            before_game = next((activity for activity in before.activities if activity.type == discord.ActivityType.playing), None)
            after_game = next((activity for activity in after.activities if activity.type == discord.ActivityType.playing), None)

            # Si aucun changement pertinent, on sort
            if before_game == after_game:
                return

            # Initialise la section games si nécessaire
            if 'games' not in self.stats_data:
                self.stats_data['games'] = {}

            # Si un jeu se termine
            if before_game and not after_game:
                game_name = before_game.name
                # Vérifier si le jeu doit être filtré
                if not self.should_filter_game(game_name):
                    # Correction ici: s'assurer que la valeur est un entier avant d'incrémenter
                    current_count = self.stats_data['games'].get(game_name, 0)
                    # Vérifier si current_count est un dictionnaire
                    if isinstance(current_count, dict):
                        # Si c'est un dictionnaire, initialiser avec 1
                        self.stats_data['games'][game_name] = 1
                    else:
                        # Sinon, incrémenter normalement
                        self.stats_data['games'][game_name] = current_count + 1
                    logger.info(f"🎮 {after.name} a terminé de jouer à {game_name}")

            # Si un nouveau jeu commence
            elif after_game and not before_game:
                game_name = after_game.name
                # Vérifier si le jeu doit être filtré
                if not self.should_filter_game(game_name):
                    # S'assurer qu'il existe une entrée pour ce jeu
                    if game_name not in self.stats_data['games']:
                        self.stats_data['games'][game_name] = 0
                    # Vérifier si la valeur est un dictionnaire
                    elif isinstance(self.stats_data['games'][game_name], dict):
                        self.stats_data['games'][game_name] = 0
                    logger.info(f"🎮 {after.name} a commencé à jouer à {game_name}")

            # Sauvegarde des données
            with open('data/stats.json', 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, indent=4)

        except Exception as e:
            logger.error(f"❌ Erreur tracking jeu: {str(e)}")

    def create_embed(self, title, description=None, color=discord.Color(0x2BA3B3)):
        """Crée un embed standard"""
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="📊 Système de Statistiques")
        return embed

    def format_time(self, minutes):
        """Formate le temps en format lisible"""
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        hours = minutes // 60
        remaining_mins = minutes % 60
        if hours < 24:
            return f"{hours}h {remaining_mins}min"
        days = hours // 24
        remaining_hours = hours % 24
        return f"{days}j {remaining_hours}h {remaining_mins}min"

    def create_chart(self, data, title, ylabel, filename, kind='bar'):
        """Crée un graphique"""
        plt.clf()  # Nettoie la figure précédente
        plt.figure(figsize=(10, 6))
        plt.style.use('dark_background')
        
        # Conversion des données pour le graphique
        labels = list(data.keys())
        values = list(data.values())
        
        if kind == 'bar':
            plt.bar(range(len(labels)), values, color='#2BA3B3', alpha=0.7)
            plt.xticks(range(len(labels)), labels, rotation=45, ha='right')
        elif kind == 'line':
            try:
                # Pour les séries temporelles
                dates = [datetime.datetime.strptime(str(label), "%Y-%m-%d %H:00") 
                        if isinstance(label, str) else label 
                        for label in labels]
                plt.plot(dates, values, marker='o', linestyle='-', color='#2BA3B3')
                plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
                plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=2))
            except ValueError:
                # Pour les données non-temporelles
                plt.plot(range(len(labels)), values, marker='o', 
                        linestyle='-', color='#2BA3B3')
                plt.xticks(range(len(labels)), labels, rotation=45, ha='right')

        plt.title(title)
        plt.ylabel(ylabel)
        plt.grid(True, linestyle='--', alpha=0.3)
        plt.tight_layout()

        # Sauvegarde en mémoire
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        plt.close()
        
        return buffer

    def get_sorted_data(self, data_dict, limit=None, reverse=True):
        """Trie les données d'un dictionnaire"""
        if not data_dict:
            return []
        try:
            # Conversion explicite des valeurs en float pour la comparaison
            sorted_items = sorted(
                [(k, float(v) if isinstance(v, (str, int)) else v) 
                 for k, v in data_dict.items()],
                key=lambda x: x[1],
                reverse=reverse
            )
            return sorted_items[:limit] if limit else sorted_items
        except (ValueError, TypeError) as e:
            logger.error(f"Erreur de tri: {e}")
            return []

    @commands.command(
        name="stats",
        help="Voir les statistiques d'un membre",
        description="Affiche les statistiques détaillées d'un membre du serveur",
        usage="!stats [@membre]"
    )
    async def show_stats(self, ctx, member: discord.Member = None):
        """Affiche les statistiques d'un membre"""
        target = member or ctx.author
        
        # Ignorer les bots
        if target.bot:
            await ctx.send("❌ Les statistiques des bots ne sont pas suivies.")
            return
            
        logger.info(f"📊 Stats demandées pour {target}")
        try:
            user_id = str(target.id)

            embed = self.create_embed(f"📊 Statistiques de {target.display_name}")
            embed.set_thumbnail(url=target.display_avatar.url)

            # Messages
            messages = self.stats_data.get('messages', {}).get(user_id, 0)
            embed.add_field(name="Messages envoyés", value=str(messages), inline=True)

            # Temps vocal
            voice_time = self.stats_data.get('voice_time', {}).get(user_id, 0)
            embed.add_field(name="Temps en vocal", value=self.format_time(voice_time), inline=True)

            # Dernière activité
            last_seen = self.stats_data.get('last_online', {}).get(user_id, "Jamais")
            embed.add_field(name="Dernière activité", value=last_seen, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"❌ Erreur affichage stats: {str(e)}")

    @commands.command(
        name="serverstats",
        help="Statistiques du serveur",
        description="Affiche les statistiques globales du serveur avec graphique",
        usage="!serverstats"
    )
    async def server_stats(self, ctx):
        """Affiche les statistiques du serveur avec graphique"""
        guild = ctx.guild
        
        # Statistiques de base
        # Compter uniquement les messages des non-bots
        messages = {uid: count for uid, count in self.stats_data.get('messages', {}).items() 
                   if not self.bot.get_user(int(uid)) or not self.bot.get_user(int(uid)).bot}
        
        # Compter uniquement le temps vocal des non-bots
        voice_time = {uid: time for uid, time in self.stats_data.get('voice_time', {}).items()
                     if not self.bot.get_user(int(uid)) or not self.bot.get_user(int(uid)).bot}
        
        total_messages = sum(messages.values())
        total_voice = sum(voice_time.values())
        
        # Meilleurs utilisateurs parmi les non-bots
        top_chatter_id = max(messages, key=messages.get) if messages else None
        top_voice_id = max(voice_time, key=voice_time.get) if voice_time else None
        
        # Création de l'embed
        embed = self.create_embed(f"📈 Statistiques de {guild.name}")
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        
        # Ajout des champs
        embed.add_field(name="Total Messages", value=str(total_messages), inline=True)
        embed.add_field(name="Total Vocal", value=self.format_time(total_voice), inline=True)
        embed.add_field(name="Membres (non-bots)", 
                       value=str(sum(1 for m in guild.members if not m.bot)), 
                       inline=True)
        
        if top_chatter_id:
            try:
                member = await guild.fetch_member(int(top_chatter_id))
                embed.add_field(
                    name="Plus actif (Messages)", 
                    value=f"{member.name}: {messages[top_chatter_id]} msgs",
                    inline=False
                )
            except:
                pass
                
        if top_voice_id:
            try:
                member = await guild.fetch_member(int(top_voice_id))
                embed.add_field(
                    name="Plus actif (Vocal)", 
                    value=f"{member.name}: {self.format_time(voice_time[top_voice_id])}",
                    inline=False
                )
            except:
                pass

        # Création du graphique d'activité
        buffer = self.create_chart(
            self.stats_data.get('hourly_activity', {}),
            "Activité par heure",
            "Activité",
            "server_activity",
            'bar'
        )

        await ctx.send(embed=embed)
        await ctx.send(file=discord.File(buffer, filename='server_activity.png'))

    @commands.command(
        name="top",
        help="Classement des membres",
        description="Affiche le top des membres selon différents critères",
        usage="!top [messages/vocal/streaming] [nombre]"
    )
    async def top_members(self, ctx, category="messages", limit: int = 5):
        """Affiche le classement des membres"""
        # Filtrer les données pour exclure les bots
        filtered_messages = {}
        filtered_vocal = {}
        filtered_streaming = {}
        
        for user_id, value in self.stats_data.get('messages', {}).items():
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member and not member.bot:
                    filtered_messages[user_id] = value
            except:
                continue
                
        for user_id, value in self.stats_data.get('voice_time', {}).items():
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member and not member.bot:
                    filtered_vocal[user_id] = value
            except:
                continue
                
        for user_id, value in self.stats_data.get('streaming', {}).items():
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member and not member.bot:
                    filtered_streaming[user_id] = value
            except:
                continue
        
        categories = {
            "messages": filtered_messages,
            "vocal": filtered_vocal,
            "streaming": filtered_streaming
        }

        if category not in categories:
            await ctx.send("❌ Catégorie invalide. Utilisez 'messages', 'vocal' ou 'streaming'")
            return

        sorted_data = self.get_sorted_data(categories[category], limit)
        
        if not sorted_data:
            await ctx.send("❌ Aucune donnée disponible pour cette catégorie")
            return

        embed = self.create_embed(f"🏆 Top {limit} - {category}")
        
        for i, (user_id, value) in enumerate(sorted_data, 1):
            try:
                member = await ctx.guild.fetch_member(int(user_id))
                if member and not member.bot:
                    name = member.display_name
                    value_str = self.format_time(value) if category != "messages" else str(value)
                    embed.add_field(name=f"#{i} {name}", value=value_str, inline=False)
            except:
                continue

        await ctx.send(embed=embed)

    @commands.command(
        name="channelstats",
        help="Statistiques des salons",
        description="Affiche les statistiques des salons textuels ou vocaux",
        usage="!channelstats [text/voice]"
    )
    async def channel_stats(self, ctx, channel_type="text"):
        """Affiche les statistiques des salons"""
        if channel_type not in ["text", "voice"]:
            await ctx.send("❌ Type invalide. Utilisez 'text' ou 'voice'")
            return

        channels_data = self.stats_data.get('channels', {}).get(channel_type, {})
        sorted_channels = self.get_sorted_data(channels_data, 10)

        embed = self.create_embed(f"📊 Top 10 salons {channel_type}")
        
        for channel_id, value in sorted_channels:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                value_str = str(value) if channel_type == "text" else self.format_time(value)
                embed.add_field(name=channel.name, value=value_str, inline=False)

        await ctx.send(embed=embed)

    @commands.command(
        name="emojistats",
        help="Statistiques des emojis",
        description="Affiche les emojis les plus utilisés sur le serveur",
        usage="!emojistats [nombre]"
    )
    async def emoji_stats(self, ctx, limit: int = 10):
        """Affiche les statistiques des emojis"""
        emojis_data = self.stats_data.get('emojis', {})
        reactions_data = self.stats_data.get('reactions', {})
        
        # Combine les données des emojis et des réactions
        all_emojis = defaultdict(int)
        for emoji_id, count in emojis_data.items():
            all_emojis[emoji_id] += count
        for emoji_str, count in reactions_data.items():
            all_emojis[emoji_str] += count

        sorted_emojis = self.get_sorted_data(all_emojis, limit)
        embed = self.create_embed("😀 Top emojis")

        for emoji_id, count in sorted_emojis:
            try:
                # Essaie de récupérer un emoji personnalisé
                emoji = self.bot.get_emoji(int(emoji_id))
                if emoji:
                    emoji_display = str(emoji)
                else:
                    # Si ce n'est pas un ID valide, c'est probablement un emoji Unicode
                    emoji_display = emoji_id
                
                embed.add_field(
                    name=emoji_display,
                    value=f"Utilisé {count} fois",
                    inline=True
                )
            except (ValueError, TypeError):
                # Si la conversion en int échoue, c'est un emoji Unicode
                embed.add_field(
                    name=emoji_id,
                    value=f"Utilisé {count} fois",
                    inline=True
                )

        await ctx.send(embed=embed)

    @commands.command(
        name="activity",
        help="Graphique d'activité",
        description="Affiche un graphique d'activité par heure ou par jour",
        usage="!activity [hourly/daily]"
    )
    async def activity_chart(self, ctx, chart_type="hourly"):
        """Affiche un graphique d'activité"""
        if chart_type not in ["hourly", "daily"]:
            await ctx.send("❌ Type invalide. Utilisez 'hourly' ou 'daily'")
            return

        if chart_type == "hourly":
            data = self.stats_data.get('hourly_activity', {})
            title = "Activité par heure"
            ordered_data = {f"{i}h": data.get(str(i), 0) for i in range(24)}
        else:
            data = self.stats_data.get('daily_activity', {})
            days = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
            ordered_data = {days[int(d)]: data.get(d, 0) for d in data}
            title = "Activité par jour"

        buffer = self.create_chart(
            ordered_data,
            title,
            "Niveau d'activité",
            f"{chart_type}_activity"
        )

        await ctx.send(
            file=discord.File(buffer, filename=f'activity_{chart_type}.png')
        )

    @commands.command(
        name="gamestats",
        help="Statistiques des jeux",
        description="Affiche les jeux les plus joués sur le serveur",
        usage="!gamestats [nombre]"
    )
    async def game_stats(self, ctx, limit: int = 10):
        """Affiche les statistiques des jeux"""
        try:
            games_data = self.stats_data.get('games', {})
            
            if not games_data:
                await ctx.send("❌ Aucune donnée de jeu disponible")
                return

            # Filtrer les jeux contenant les mots à exclure
            filtered_games = {}
            for game_name, minutes in games_data.items():
                if not self.should_filter_game(game_name) and minutes and str(minutes).replace('.','',1).isdigit():
                    filtered_games[str(game_name)] = float(minutes)

            if not filtered_games:
                await ctx.send("❌ Aucune donnée valide trouvée après filtrage")
                return

            sorted_games = self.get_sorted_data(filtered_games, limit)
            
            embed = self.create_embed("🎮 Top jeux joués")
            embed.set_footer(text="Temps total de jeu")

            for game_name, minutes in sorted_games:
                embed.add_field(
                    name=game_name,
                    value=self.format_time(int(minutes)),
                    inline=False
                )
                
            # Création du graphique
            if len(sorted_games) > 0:
                chart_data = {
                    str(game): float(mins) 
                    for game, mins in sorted_games[:5]
                }
                buffer = self.create_chart(
                    chart_data,
                    "Top 5 jeux les plus joués",
                    "Temps de jeu (minutes)",
                    "games_stats"
                )
                
                await ctx.send(embed=embed)
                await ctx.send(file=discord.File(buffer, filename='games_stats.png'))
            else:
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Erreur dans game_stats: {e}")
            await ctx.send(f"❌ Une erreur est survenue : {str(e)}")

async def setup(bot):
    await bot.add_cog(StatsCommands(bot))