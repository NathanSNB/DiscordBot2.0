import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot configuration
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    PREFIX = os.getenv("COMMAND_PREFIX", "!")
    GUILD_ID = int(os.getenv("GUILD_ID", "0"))

    # API Keys
    BITLY_KEY = os.getenv("BITLY_API_KEY")
    VIRUSTOTAL_KEY = os.getenv("VIRUSTOTAL_API_KEY")

    # Autorisations
    AUTHORIZED_CC = os.getenv("AUTHORIZED_USERS_CC", "").split(",")
    AUTHORIZED_HERESIE = os.getenv("AUTHORIZED_USERS_HERESIE", "").split(",")

    # IDs Cibles
    TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL_ID", "0"))
    TARGET_USER = int(os.getenv("TARGET_USER_ID", "0"))

    # Chemins
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    COGS_DIR = os.path.join(BASE_DIR, "cogs")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # Liste des Cogs
    EXTENSIONS = [
        # Commands
        "commands.statsUsers(everyoneOnly)",
        "commands.server(admOnly)", 
        "commands.reminder(aleksOnly)",
        "commands.economy(mixt)",
        "commands.générals(everyoneOnly)",
        "commands.moderations(admOnly)",
        "commands.heresie(admOnly)",
        "commands.utilitaire(everyoneOnly)",
        "commands.help",
        "commands.music",
        "commands.mcstatus",
        "commands.ytdw",
        "commands.free_games",
        # Events
        "events.logs",
        "events.statsUsers"
    ]

    # Couleurs
    COLOR_SUCCESS = 0x2BA3B3
    COLOR_ERROR = 0xFF0000
    COLOR_WARNING = 0xFFA500

    @classmethod
    def check_config(cls):
        """Vérifie la validité de la configuration"""
        required_vars = [
            ("DISCORD_BOT_TOKEN", cls.TOKEN),
            ("BITLY_API_KEY", cls.BITLY_KEY),
            ("VIRUSTOTAL_API_KEY", cls.VIRUSTOTAL_KEY),
        ]

        for var_name, var_value in required_vars:
            if not var_value:
                raise ValueError(f"❌ {var_name} manquant dans .env")

        if cls.GUILD_ID == 0:
            raise ValueError("❌ GUILD_ID invalide dans .env")

        if not cls.AUTHORIZED_CC or not cls.AUTHORIZED_HERESIE:
            raise ValueError("❌ Listes d'utilisateurs autorisés manquantes")

        if not cls.TOKEN:
            raise ValueError("❌ Token Discord manquant dans .env")
        if len(cls.TOKEN) < 50:  # Les tokens Discord font généralement plus de 50 caractères
            raise ValueError("❌ Token Discord invalide")

        # Création des dossiers nécessaires
        for directory in [cls.LOGS_DIR, cls.DATA_DIR]:
            os.makedirs(directory, exist_ok=True)