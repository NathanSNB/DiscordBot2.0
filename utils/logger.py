import logging
import os
from datetime import datetime
from config import Config

def setup_logger():
    """Configure le système de logging"""
    logger = logging.getLogger("bot")
    logger.setLevel(logging.INFO)

    # Format du log
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler pour le fichier
    log_file = os.path.join(
        Config.LOGS_DIR,
        f"bot_{datetime.now().strftime('%Y%m%d')}.log"
    )
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Dans n'importe quel fichier
logger = logging.getLogger("bot")

# Différents niveaux de log
logger.debug("Message de debug")     # Détails techniques
logger.info("Information normale")   # Information générale
logger.warning("Avertissement")      # Problème potentiel
logger.error("Erreur")              # Erreur importante
logger.critical("Erreur critique")   # Erreur bloquante