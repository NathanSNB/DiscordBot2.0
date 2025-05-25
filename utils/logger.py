import logging
import os
import sys
from datetime import datetime

# S'assurer que le dossier de logs existe
os.makedirs("logs", exist_ok=True)

# Définir les formateurs pour les différents handlers
CONSOLE_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
FILE_FORMAT = '%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s'

# Un dictionnaire pour suivre les loggers déjà configurés
_configured_loggers = {}

def setup_logger(name='bot', level=logging.INFO):
    """
    Configure et retourne un logger avec des handlers pour la console et les fichiers
    en s'assurant que les handlers ne sont pas dupliqués.
    """
    # Si le logger a déjà été configuré, le retourner directement
    if name in _configured_loggers:
        return _configured_loggers[name]
    
    # Créer ou récupérer le logger
    logger = logging.getLogger(name)
    
    # Éviter la propagation aux loggers parents pour éviter les doublons
    logger.propagate = False
    
    # Définir le niveau de log
    logger.setLevel(level)
    
    # Ne pas ajouter de handlers si le logger en a déjà
    if logger.handlers:
        _configured_loggers[name] = logger
        return logger
    
    # Créer un handler pour la console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(CONSOLE_FORMAT)
    console_handler.setFormatter(console_formatter)
    
    # Créer un handler pour les fichiers
    log_filename = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(level)
    file_formatter = logging.Formatter(FILE_FORMAT)
    file_handler.setFormatter(file_formatter)
    
    # Ajouter les handlers au logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Enregistrer le logger configuré
    _configured_loggers[name] = logger
    
    return logger

def get_logger(name='bot'):
    """
    Récupère un logger existant ou en crée un nouveau.
    Cette fonction assure qu'aucun handler n'est ajouté en double.
    """
    if name in _configured_loggers:
        return _configured_loggers[name]
    return setup_logger(name)