import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import random
from dotenv import load_dotenv
from zoneinfo import ZoneInfo  # Pour gérer le fuseau horaire
import logging
import pytz
from datetime import datetime

# Configurer le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis un fichier .env
load_dotenv()

class BedtimeReminder(commands.Cog):
    """Système de rappels personnalisés"""

    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone('Europe/Paris')
        self.current_time = datetime.now(self.timezone)
        self.reminder_time = "22:00"  # Heure par défaut
        self.load_config()
        self.reminder_check.start()

    def load_config(self):
        """Charge la configuration depuis le fichier JSON"""
        try:
            if os.path.exists('data/reminders.json'):
                with open('data/reminders.json', 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    "users": [],
                    "messages": [],
                    "reminder_time": self.reminder_time
                }
                self.save_config()
        except Exception as e:
            logger.error(f"❌ Erreur config rappels: {str(e)}")
            self.config = {"users": [], "messages": [], "reminder_time": self.reminder_time}

    def save_config(self):
        """Sauvegarde la configuration"""
        os.makedirs('data', exist_ok=True)
        with open('data/reminders.json', 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4)

    def create_embed(self, title, description=None):
        """Crée un embed standard"""
        embed = discord.Embed(title=title, description=description, color=discord.Color(0x2BA3B3))
        embed.set_footer(text="Système de Rappels ｜ © 2025")
        return embed

    @tasks.loop(minutes=1)
    async def reminder_check(self):
        """Vérifie et envoie les rappels"""
        try:
            # Utilisation du fuseau horaire France/Paris
            now = datetime.now(ZoneInfo("Europe/Paris"))
            current_time = f"{now.hour:02d}:{now.minute:02d}"
            logger.debug(f"🔍 Vérification rappels: {now.strftime('%H:%M')}")

            if current_time == self.config["reminder_time"] and self.config["messages"]:
                message = random.choice(self.config["messages"])
                embed = self.create_embed(
                    "🌙 Rappel", 
                    f"{message}\n\n_Heure France : {current_time}_"
                )
                
                message_sent = False
                for user_id in self.config["users"]:
                    try:
                        user = await self.bot.fetch_user(int(user_id))
                        await user.send(embed=embed)
                        message_sent = True
                    except Exception as e:
                        logger.error(f"❌ Erreur d'envoi: {str(e)}")
                
                if message_sent:
                    logger.info(f"📨 Rappel envoyé à {len(self.config['users'])} utilisateurs")
        except Exception as e:
            logger.error(f"❌ Erreur rappel: {str(e)}")

    async def check_time(self):
        """Vérifie l'heure actuelle"""
        now = datetime.now(self.timezone)
        target_time = datetime.strptime(self.reminder_time, "%H:%M").time()
        current_time = now.time()
        return current_time.hour == target_time.hour and current_time.minute == target_time.minute

    @commands.command(
        name="add_user",
        help="Ajoute un utilisateur aux rappels",
        description="Ajoute un utilisateur à la liste des rappels",
        usage="!add_user <@utilisateur>"
    )
    @commands.has_permissions(administrator=True)
    async def add_user(self, ctx, user: discord.Member):
        if str(user.id) not in self.config["users"]:
            self.config["users"].append(str(user.id))
            self.save_config()
            await ctx.send(embed=self.create_embed("✅ Utilisateur ajouté", 
                f"{user.name} recevra les rappels à {self.config['reminder_time']}"))
        else:
            await ctx.send("❌ Cet utilisateur reçoit déjà les rappels")

    @commands.command(
        name="add_message",
        help="Ajoute un message",
        description="Ajoute un message à la liste des rappels",
        usage="!add_message <message>"
    )
    @commands.has_permissions(administrator=True)
    async def add_message(self, ctx, *, message: str):
        self.config["messages"].append(message)
        self.save_config()
        await ctx.send(embed=self.create_embed("✅ Message ajouté", 
            f"Nouveau message ajouté à la liste"))

    @commands.command(
        name="message_list",
        help="Liste des messages",
        description="Affiche tous les messages configurés",
        usage="!message_list"
    )
    @commands.has_permissions(administrator=True)
    async def message_list(self, ctx):
        if not self.config["messages"]:
            await ctx.send("❌ Aucun message configuré")
            return

        embed = self.create_embed("📝 Liste des messages")
        for i, msg in enumerate(self.config["messages"], 1):
            embed.add_field(name=f"Message {i}", value=msg, inline=False)
        await ctx.send(embed=embed)

    @commands.command(
        name="user_list",
        help="Liste des utilisateurs",
        description="Affiche tous les utilisateurs recevant les rappels",
        usage="!user_list"
    )
    @commands.has_permissions(administrator=True)
    async def user_list(self, ctx):
        if not self.config["users"]:
            await ctx.send("❌ Aucun utilisateur configuré")
            return

        embed = self.create_embed("👥 Liste des utilisateurs", 
            f"Heure de rappel: {self.config['reminder_time']}")
        
        for user_id in self.config["users"]:
            try:
                user = await self.bot.fetch_user(int(user_id))
                embed.add_field(name=user.name, value=f"ID: {user_id}", inline=False)
            except:
                continue
        await ctx.send(embed=embed)

    @commands.command(
        name="change_heure",
        help="Change l'heure",
        description="Modifie l'heure des rappels",
        usage="!change_heure <HH:MM>"
    )
    @commands.has_permissions(administrator=True)
    async def change_heure(self, ctx, new_time: str):
        try:
            hour, minute = map(int, new_time.split(':'))
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            
            self.config["reminder_time"] = f"{hour:02d}:{minute:02d}"
            self.save_config()
            
            await ctx.send(embed=self.create_embed("✅ Heure modifiée", 
                f"Les rappels seront maintenant envoyés à {self.config['reminder_time']}"))
        except ValueError:
            await ctx.send("❌ Format d'heure invalide. Utilisez HH:MM (ex: 22:00)")

    @commands.command(
        name="remove_user",
        help="Retire un utilisateur",
        description="Retire un utilisateur de la liste des rappels",
        usage="!remove_user <@utilisateur>"
    )
    @commands.has_permissions(administrator=True)
    async def remove_user(self, ctx, user: discord.Member):
        if str(user.id) in self.config["users"]:
            self.config["users"].remove(str(user.id))
            self.save_config()
            await ctx.send(embed=self.create_embed("✅ Utilisateur retiré", 
                f"{user.name} ne recevra plus de rappels"))
        else:
            await ctx.send("❌ Cet utilisateur ne reçoit pas de rappels")

async def setup(bot):
    await bot.add_cog(BedtimeReminder(bot))