import discord
from discord.ext import commands, tasks
import json
import os
import random
import logging
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import pytz
from datetime import datetime, timedelta

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("BedtimeReminder")

# Chargement des variables d'environnement
load_dotenv()

# Constantes
CONFIG_FILE = 'data/reminders.json'
USER_PREFERENCES_FILE = 'data/user_preferences.json'
DEFAULT_REMINDER_TIME = "22:00"
EMBED_COLOR = 0x2BA3B3
FOOTER_TEXT = "Système de Rappels ｜ © 2025"
TIMEZONE = "Europe/Paris"

# Styles d'embeds pour les rappels
REMINDER_STYLES = [
    {
        "title": "🌙 Il est temps de se reposer",
        "color": 0x7B68EE,  # Violet moyen
        "image": "https://i.imgur.com/2DrXEHX.png",  # Image de nuit étoilée
        "emoji": "🌠"
    },
    {
        "title": "😴 L'heure du sommeil a sonné",
        "color": 0x483D8B,  # Bleu ardoise foncé
        "image": "https://i.imgur.com/qL31YcD.png",  # Image de lune
        "emoji": "🌜"
    },
    {
        "title": "💤 Un rappel pour bien dormir",
        "color": 0x4682B4,  # Bleu acier
        "image": "https://i.imgur.com/E4LJ8EY.png",  # Image zen
        "emoji": "✨"
    },
    {
        "title": "🛌 Votre rappel nocturne",
        "color": 0x2E8B57,  # Vert marin
        "image": "https://i.imgur.com/H8FZHEC.png",  # Image relaxante
        "emoji": "🌿"
    }
]

# Citations pour les rappels
REMINDER_QUOTES = [
    "Un bon sommeil est la clé d'une journée productive.",
    "Dormir suffisamment améliore votre mémoire et concentration.",
    "Reposez votre esprit pour mieux affronter demain.",
    "Le sommeil est le meilleur médicament.",
    "Une bonne nuit de sommeil répare le corps et l'esprit."
]

class BedtimeReminder(commands.Cog):
    """Système de rappels personnalisés pour les utilisateurs Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone(TIMEZONE)
        self.messages = self._load_messages()
        self.user_preferences = self._load_user_preferences()
        self.reminder_check.start()
        logger.info("✅ Module de rappels personnalisés initialisé")

    def _load_messages(self):
        """Charge les messages de rappel depuis le fichier JSON"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    logger.info(f"📂 Messages chargés: {len(config.get('messages', []))}")
                    return config.get('messages', [])
            else:
                default_messages = [
                    "Il est temps de se détendre et de se préparer pour la nuit.",
                    "N'oubliez pas de vous reposer pour être en forme demain.",
                    "Accordez-vous du temps pour un sommeil réparateur.",
                    "Pensez à mettre votre téléphone en mode silencieux pour une meilleure qualité de sommeil."
                ]
                os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump({"messages": default_messages}, f, indent=4)
                logger.info("📝 Fichier de messages par défaut créé")
                return default_messages
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des messages: {str(e)}")
            return []

    def _save_messages(self, messages):
        """Sauvegarde les messages dans le fichier JSON"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump({"messages": messages}, f, indent=4)
            self.messages = messages
            logger.info("💾 Messages sauvegardés")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des messages: {str(e)}")

    def _load_user_preferences(self):
        """Charge les préférences utilisateur depuis le fichier JSON"""
        try:
            if os.path.exists(USER_PREFERENCES_FILE):
                with open(USER_PREFERENCES_FILE, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                    logger.info(f"📂 Préférences chargées: {len(preferences)} utilisateurs")
                    return preferences
            else:
                os.makedirs(os.path.dirname(USER_PREFERENCES_FILE), exist_ok=True)
                with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                    json.dump({}, f, indent=4)
                logger.info("📝 Fichier de préférences utilisateur créé")
                return {}
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des préférences: {str(e)}")
            return {}

    def _save_user_preferences(self):
        """Sauvegarde les préférences utilisateur dans le fichier JSON"""
        try:
            with open(USER_PREFERENCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, indent=4)
            logger.info("💾 Préférences utilisateur sauvegardées")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des préférences: {str(e)}")

    def create_reminder_embed(self, message):
        """
        Crée un embed Discord attrayant pour un rappel
        
        Args:
            message (str): Message principal du rappel
            
        Returns:
            discord.Embed: L'embed formaté
        """
        # Sélectionner un style aléatoire
        style = random.choice(REMINDER_STYLES)
        
        # Ajouter une citation
        quote = random.choice(REMINDER_QUOTES)
        
        # Obtenir l'heure actuelle dans le fuseau horaire configuré
        now = datetime.now(ZoneInfo(TIMEZONE))
        current_time = f"{now.hour:02d}:{now.minute:02d}"
        
        # Créer l'embed
        embed = discord.Embed(
            title=style["title"],
            description=f"**{style['emoji']} {message}**\n\n> *\"{quote}\"*",
            color=discord.Color(style["color"]),
            timestamp=datetime.now()
        )
        
        # Ajouter l'image si disponible
        if style.get("image"):
            embed.set_thumbnail(url=style["image"])
        
        # Ajouter la date et l'heure
        embed.add_field(
            name="⏰ Heure locale",
            value=f"{current_time}",
            inline=True
        )
        
        embed.add_field(
            name="📅 Date",
            value=f"{now.strftime('%d/%m/%Y')}",
            inline=True
        )
        
        # Ajouter un conseil aléatoire pour le sommeil
        sleep_tips = [
            "Évitez les écrans 1h avant de dormir",
            "Gardez votre chambre fraîche et sombre",
            "Une routine régulière améliore la qualité du sommeil",
            "Limitez la caféine en fin de journée",
            "La méditation peut vous aider à mieux dormir"
        ]
        
        embed.add_field(
            name="💡 Conseil du jour",
            value=random.choice(sleep_tips),
            inline=False
        )
        
        embed.set_footer(text=f"{FOOTER_TEXT} • Passez une douce nuit")
        return embed

    def create_embed(self, title, description=None, fields=None, color=None):
        """
        Crée un embed Discord standard pour les réponses de commandes
        
        Args:
            title (str): Titre de l'embed
            description (str, optional): Description de l'embed
            fields (list, optional): Liste de tuples (name, value, inline) pour les champs
            color (int, optional): Couleur personnalisée de l'embed
            
        Returns:
            discord.Embed: L'embed formaté
        """
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color(color if color else EMBED_COLOR),
            timestamp=datetime.now()
        )
        
        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
                
        embed.set_footer(text=FOOTER_TEXT)
        return embed

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        """Vérifie si c'est l'heure d'envoyer les rappels et les envoie si nécessaire"""
        try:
            # Obtenir l'heure actuelle dans le fuseau horaire configuré
            now = datetime.now(ZoneInfo(TIMEZONE))
            current_time = f"{now.hour:02d}:{now.minute:02d}"
            
            if not self.messages:
                return
                
            # Vérifier pour chaque utilisateur si c'est l'heure de son rappel
            users_notified = 0
            
            for user_id, prefs in self.user_preferences.items():
                if not prefs.get("active", False):
                    continue
                    
                if current_time != prefs.get("time", DEFAULT_REMINDER_TIME):
                    continue
                
                # Choisir un message pour l'utilisateur
                message = random.choice(self.messages)
                
                # Créer l'embed personnalisé
                embed = self.create_reminder_embed(message)
                
                # Envoyer le rappel
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    await user.send(embed=embed)
                    users_notified += 1
                    logger.info(f"📨 Rappel envoyé à {user.name} ({user_id})")
                except Exception as e:
                    logger.error(f"❌ Impossible d'envoyer le rappel à l'utilisateur {user_id}: {str(e)}")
            
            if users_notified > 0:
                logger.info(f"📨 Rappels envoyés à {users_notified} utilisateurs")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification des rappels: {str(e)}")

    @reminder_check.before_loop
    async def before_reminder_check(self):
        """Attendre que le bot soit prêt avant de commencer la boucle de vérification"""
        await self.bot.wait_until_ready()
        logger.info("🔄 Démarrage de la boucle de vérification des rappels")

    @commands.command(name="rappel_activer", aliases=["reminder_on", "activate_reminder"])
    async def activate_reminder(self, ctx):
        """Active les rappels pour l'utilisateur"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "active": True,
                "time": DEFAULT_REMINDER_TIME,
                "name": ctx.author.name
            }
        else:
            self.user_preferences[user_id]["active"] = True
            
        self._save_user_preferences()
        
        user_time = self.user_preferences[user_id]["time"]
        
        embed = self.create_embed(
            "✅ Rappels Activés",
            f"Vous recevrez désormais des rappels quotidiens à **{user_time}**.\n\nUtilisez `!rappel_heure HH:MM` pour modifier l'heure de rappel."
        )
        await ctx.send(embed=embed)

    @commands.command(name="rappel_desactiver", aliases=["reminder_off", "deactivate_reminder"])
    async def deactivate_reminder(self, ctx):
        """Désactive les rappels pour l'utilisateur"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                "active": False,
                "time": DEFAULT_REMINDER_TIME,
                "name": ctx.author.name
            }
        else:
            self.user_preferences[user_id]["active"] = False
            
        self._save_user_preferences()
        
        embed = self.create_embed(
            "🔕 Rappels Désactivés",
            "Vous ne recevrez plus de rappels quotidiens.\n\nUtilisez `!rappel_activer` pour les réactiver."
        )
        await ctx.send(embed=embed)

    @commands.command(name="rappel_heure", aliases=["reminder_time", "set_reminder_time"])
    async def set_reminder_time(self, ctx, new_time: str):
        """Modifie l'heure à laquelle l'utilisateur reçoit les rappels"""
        user_id = str(ctx.author.id)
        
        # Vérifier le format de l'heure
        try:
            hour, minute = map(int, new_time.split(':'))
            
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Heure invalide")
                
            formatted_time = f"{hour:02d}:{minute:02d}"
            
            # Mettre à jour les préférences utilisateur
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {
                    "active": True,
                    "time": formatted_time,
                    "name": ctx.author.name
                }
            else:
                self.user_preferences[user_id]["time"] = formatted_time
                if "active" not in self.user_preferences[user_id]:
                    self.user_preferences[user_id]["active"] = True
                    
            self._save_user_preferences()
            
            # Calculer le temps restant avant le prochain rappel
            now = datetime.now(ZoneInfo(TIMEZONE))
            reminder_time = datetime.strptime(formatted_time, "%H:%M").time()
            
            if now.time() > reminder_time:
                # Le rappel est pour demain
                next_reminder = datetime.combine(now.date() + timedelta(days=1), reminder_time)
            else:
                # Le rappel est pour aujourd'hui
                next_reminder = datetime.combine(now.date(), reminder_time)
                
            next_reminder = pytz.timezone(TIMEZONE).localize(next_reminder)
            time_delta = next_reminder - now
            hours, remainder = divmod(time_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Confirmer la modification
            embed = self.create_embed(
                "⏰ Heure de Rappel Modifiée",
                f"Vos rappels seront désormais envoyés à **{formatted_time}**.\n\n"
                f"Prochain rappel dans: **{hours}h {minutes}m**"
            )
            
            status = "activés" if self.user_preferences[user_id]["active"] else "désactivés"
            embed.add_field(
                name="État des rappels",
                value=f"Vos rappels sont actuellement **{status}**.",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except ValueError:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                "Format d'heure invalide. Utilisez le format `HH:MM` (ex: 22:00)."
            ))

    @commands.command(name="rappel_test", aliases=["test_reminder"])
    async def test_reminder(self, ctx):
        """Envoie un rappel de test à l'utilisateur"""
        if not self.messages:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                "Aucun message configuré pour le test."
            ))
            return
            
        # Sélectionner un message aléatoire
        message = random.choice(self.messages)
        
        # Créer l'embed pour le rappel de test
        test_embed = self.create_reminder_embed(message)
        test_embed.description = f"{test_embed.description}\n\n*Ceci est un rappel de test.*"
        
        # Envoyer le rappel de test
        try:
            await ctx.author.send(embed=test_embed)
            await ctx.send(embed=self.create_embed(
                "✅ Test Réussi",
                "Un rappel de test vous a été envoyé par message privé."
            ))
        except Exception as e:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                f"Impossible de vous envoyer un message privé: {str(e)}\n\n"
                "Vérifiez que vous avez activé la réception des messages privés sur ce serveur."
            ))

    @commands.command(name="rappel_statut", aliases=["reminder_status", "reminder_info"])
    async def reminder_status(self, ctx):
        """Affiche le statut des rappels pour l'utilisateur"""
        user_id = str(ctx.author.id)
        
        if user_id not in self.user_preferences:
            await ctx.send(embed=self.create_embed(
                "ℹ️ Statut des Rappels",
                "Vous n'avez pas encore configuré de rappels.\n\n"
                "Utilisez `!rappel_activer` pour commencer à recevoir des rappels."
            ))
            return
            
        prefs = self.user_preferences[user_id]
        status = "activés" if prefs.get("active", False) else "désactivés"
        
        # Calculer le temps restant avant le prochain rappel
        now = datetime.now(ZoneInfo(TIMEZONE))
        reminder_time = datetime.strptime(prefs.get("time", DEFAULT_REMINDER_TIME), "%H:%M").time()
        
        if now.time() > reminder_time or not prefs.get("active", False):
            # Le rappel est pour demain ou les rappels sont désactivés
            next_reminder = datetime.combine(now.date() + timedelta(days=1), reminder_time)
        else:
            # Le rappel est pour aujourd'hui
            next_reminder = datetime.combine(now.date(), reminder_time)
            
        next_reminder = pytz.timezone(TIMEZONE).localize(next_reminder)
        time_delta = next_reminder - now
        hours, remainder = divmod(time_delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        embed = self.create_embed(
            "📊 Statut de vos Rappels",
            f"**État:** {status}\n"
            f"**Heure configurée:** {prefs.get('time', DEFAULT_REMINDER_TIME)}\n"
            f"**Fuseau horaire:** {TIMEZONE}\n\n"
            f"**Heure actuelle:** {now.strftime('%H:%M')}\n"
            f"**Prochain rappel:** {hours}h {minutes}m" if prefs.get("active", False) else "Rappels désactivés"
        )
        
        embed.add_field(
            name="💡 Commandes utiles",
            value="- `!rappel_test` pour recevoir un rappel de test\n"
                 f"- `!rappel_{'desactiver' if prefs.get('active', False) else 'activer'}` pour {('désactiver' if prefs.get('active', False) else 'activer')} les rappels\n"
                 "- `!rappel_heure HH:MM` pour changer l'heure",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="rappel_ajouter", aliases=["add_reminder_message"])
    @commands.has_permissions(administrator=True)
    async def add_reminder_message(self, ctx, *, message: str):
        """Ajoute un message à la liste des rappels"""
        # Vérifier si le message existe déjà
        if message in self.messages:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                "Ce message existe déjà dans la liste."
            ))
            return
            
        self.messages.append(message)
        self._save_messages(self.messages)
        
        await ctx.send(embed=self.create_embed(
            "✅ Message Ajouté",
            f"**Message ajouté à la liste des rappels:**\n{message}"
        ))

    @commands.command(name="rappel_messages", aliases=["list_reminder_messages"])
    @commands.has_permissions(administrator=True)
    async def list_reminder_messages(self, ctx):
        """Affiche tous les messages de rappel configurés"""
        if not self.messages:
            await ctx.send(embed=self.create_embed(
                "📝 Messages de Rappel",
                "Aucun message configuré. Utilisez `!rappel_ajouter` pour en ajouter."
            ))
            return

        # Créer des pages si nécessaire pour les grands ensembles de messages
        messages_per_page = 5
        pages = [self.messages[i:i+messages_per_page] for i in range(0, len(self.messages), messages_per_page)]
        
        for i, page in enumerate(pages):
            embed = self.create_embed(
                f"📝 Messages de Rappel (Page {i+1}/{len(pages)})",
                f"**{len(self.messages)}** messages disponibles"
            )
            
            for j, msg in enumerate(page):
                index = i * messages_per_page + j + 1
                embed.add_field(
                    name=f"Message #{index}",
                    value=msg,
                    inline=False
                )
                
            await ctx.send(embed=embed)

    @commands.command(name="rappel_supprimer", aliases=["delete_reminder_message"])
    @commands.has_permissions(administrator=True)
    async def delete_reminder_message(self, ctx, index: int):
        """Supprime un message de la liste des rappels"""
        if not self.messages:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                "Aucun message configuré à supprimer."
            ))
            return
            
        try:
            # Ajuster l'index pour correspondre à l'affichage (commençant à 1)
            adj_index = index - 1
            
            if adj_index < 0 or adj_index >= len(self.messages):
                raise IndexError()
                
            removed_message = self.messages.pop(adj_index)
            self._save_messages(self.messages)
            
            await ctx.send(embed=self.create_embed(
                "✅ Message Supprimé",
                f"**Message #{index} supprimé:**\n{removed_message}"
            ))
            
        except IndexError:
            await ctx.send(embed=self.create_embed(
                "❌ Erreur",
                f"Index invalide. Utilisez un nombre entre 1 et {len(self.messages)}."
            ))

    @commands.command(name="rappel_utilisateurs", aliases=["list_reminder_users"])
    @commands.has_permissions(administrator=True)
    async def list_reminder_users(self, ctx):
        """Affiche tous les utilisateurs configurés pour recevoir des rappels"""
        if not self.user_preferences:
            await ctx.send(embed=self.create_embed(
                "👥 Utilisateurs Configurés",
                "Aucun utilisateur n'a encore configuré de rappels."
            ))
            return

        active_users = [uid for uid, prefs in self.user_preferences.items() if prefs.get("active", False)]
        
        embed = self.create_embed(
            "👥 Utilisateurs Configurés",
            f"**{len(active_users)}/{len(self.user_preferences)}** utilisateurs ont activé les rappels"
        )
        
        # Ajouter des informations sur les utilisateurs actifs
        if active_users:
            active_field = ""
            for user_id in active_users:
                prefs = self.user_preferences[user_id]
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    active_field += f"• {user.mention} - {prefs.get('time', DEFAULT_REMINDER_TIME)}\n"
                except:
                    active_field += f"• Utilisateur {prefs.get('name', 'inconnu')} (ID: {user_id}) - {prefs.get('time', DEFAULT_REMINDER_TIME)}\n"
            
            embed.add_field(
                name="✅ Utilisateurs avec rappels activés",
                value=active_field if active_field else "Aucun",
                inline=False
            )
        
        # Ajouter des informations sur les utilisateurs inactifs
        inactive_users = [uid for uid, prefs in self.user_preferences.items() if not prefs.get("active", False)]
        if inactive_users:
            inactive_field = ""
            for user_id in inactive_users:
                prefs = self.user_preferences[user_id]
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    inactive_field += f"• {user.mention} - {prefs.get('time', DEFAULT_REMINDER_TIME)}\n"
                except:
                    inactive_field += f"• Utilisateur {prefs.get('name', 'inconnu')} (ID: {user_id}) - {prefs.get('time', DEFAULT_REMINDER_TIME)}\n"
            
            embed.add_field(
                name="🔕 Utilisateurs avec rappels désactivés",
                value=inactive_field if inactive_field else "Aucun",
                inline=False
            )
                
        await ctx.send(embed=embed)

async def setup(bot):
    """Fonction d'initialisation du module pour Discord.py"""
    await bot.add_cog(BedtimeReminder(bot))
    logger.info("✅ Module BedtimeReminder personnalisé chargé avec succès")