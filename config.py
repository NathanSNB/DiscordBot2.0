import os
import json
from dotenv import load_dotenv, dotenv_values
from utils.logger import get_logger

# Récupération d'un logger déjà configuré
logger = get_logger(__name__)

# Chargement des variables d'environnement avec gestion d'erreurs
try:
    # Essayer de charger le fichier .env
    env_loaded = load_dotenv()
    if not env_loaded:
        logger.warning("Aucun fichier .env trouvé ou fichier vide")
except Exception as e:
    # Capturer toutes les erreurs de parsing du fichier .env
    logger.error(f"Erreur lors du chargement du fichier .env: {str(e)}")
    logger.error("Le bot continuera avec les valeurs par défaut ou les variables d'environnement système")

class Config:
    """Configuration globale du bot Discord"""
    
    # Bot configuration
    TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    PREFIX = os.getenv("COMMAND_PREFIX", "!")  # Valeur par défaut ajoutée
    GUILD_ID = int(os.getenv("GUILD_ID", "0"))
    OWNER_IDS = [int(id) for id in os.getenv("OWNER_IDS", "123456789012345678").split(",")]
    
    # API Keys
    BITLY_KEY = os.getenv("BITLY_API_KEY", "")
    VIRUSTOTAL_KEY = os.getenv("VIRUSTOTAL_API_KEY", "")
    
    # Autorisations
    AUTHORIZED_CC = os.getenv("AUTHORIZED_USERS_CC", "").split(",")
    AUTHORIZED_HERESIE = os.getenv("AUTHORIZED_USERS_HERESIE", "").split(",")
    
    # IDs Cibles
    TARGET_CHANNEL = int(os.getenv("TARGET_CHANNEL_ID", "0"))
    TARGET_USER = int(os.getenv("TARGET_USER_ID", "0"))
    
    # Chemins
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    COGS_DIR = os.path.join(BASE_DIR, "cogs")
    UTILS_DIR = os.path.join(BASE_DIR, "utils")
    LOGS_DIR = os.path.join(BASE_DIR, "logs")
    DATA_DIR = os.path.join(BASE_DIR, "data")
    
    # Liste des Cogs
    EXTENSIONS = [
        # Commands
        "commands.statsUsers(everyoneOnly)",
        "commands.couleur",
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
        "commands.pic",
        "commands.wiki",
        "commands.free_games",
        "commands.role",
        "commands.rules_admin",  # Remplacer rules(admOnly) par rules_admin
        "commands.whitelist",
        # Events
        "events.logs",
        "events.role_events",
        "events.private_chanel",
        "events.color",
        "events.members_counter",
        "events.mcstatusTraker",
        "events.ticket_system",  # Version utilisant le menu déroulant
        "events.free_games_events",
        "events.statsUsers",
    ]
    
    # Couleurs par défaut
    DEFAULT_COLOR = 0x2BA3B3
    COLOR_SUCCESS = 0x2ECC71
    COLOR_ERROR = 0xE74C3C
    COLOR_WARNING = 0xF1C40F
    
    @classmethod
    def initialize_colors(cls):
        """Initialise les couleurs depuis le fichier de configuration"""
        try:
            config_file = os.path.join(cls.DATA_DIR, 'bot_settings.json')
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'embed_color' in settings:
                        cls.DEFAULT_COLOR = settings['embed_color']
                        # Définir également les couleurs contextuelles basées sur la couleur principale
                        cls.COLOR_SUCCESS = 0x2ECC71  # Vert
                        cls.COLOR_ERROR = 0xE74C3C    # Rouge
                        cls.COLOR_WARNING = 0xF1C40F  # Jaune
                        logger.info(f"🎨 Couleur d'embed chargée: #{cls.DEFAULT_COLOR:06X}")
            else:
                logger.warning("Fichier de configuration des couleurs non trouvé, utilisation de la couleur par défaut")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des couleurs: {e}")
    
    @classmethod
    def check_config(cls):
        """Vérifie la validité de la configuration et crée les dossiers nécessaires"""
        required_vars = [
            ("DISCORD_BOT_TOKEN", cls.TOKEN),
            ("BITLY_API_KEY", cls.BITLY_KEY),
            ("VIRUSTOTAL_API_KEY", cls.VIRUSTOTAL_KEY),
        ]
        
        # Vérification des variables requises
        for var_name, var_value in required_vars:
            if not var_value:
                raise ValueError(f"❌ {var_name} manquant dans .env")
        
        # Vérifications supplémentaires
        if cls.GUILD_ID == 0:
            raise ValueError("❌ GUILD_ID invalide dans .env")
            
        if not cls.AUTHORIZED_CC or not cls.AUTHORIZED_HERESIE:
            raise ValueError("❌ Listes d'utilisateurs autorisés manquantes")
            
        if not cls.TOKEN:
            raise ValueError("❌ Token Discord manquant dans .env")
            
        if len(cls.TOKEN) < 50:  # Les tokens Discord font généralement plus de 50 caractères
            raise ValueError("❌ Token Discord invalide")
        
        # Création des dossiers nécessaires
        for directory in [cls.LOGS_DIR, cls.DATA_DIR, cls.UTILS_DIR]:
            os.makedirs(directory, exist_ok=True)
        
        # Initialisation des couleurs
        cls.initialize_colors()
        
        return True

    @classmethod
    def get_embed_color(cls, type="default"):
        """Renvoie la couleur appropriée pour les embeds selon le type"""
        colors = {
            "success": cls.COLOR_SUCCESS,
            "error": cls.COLOR_ERROR,
            "warning": cls.COLOR_WARNING,
            "default": cls.DEFAULT_COLOR
        }
        return colors.get(type.lower(), cls.DEFAULT_COLOR)

# Initialize colors at module import time
Config.initialize_colors()
