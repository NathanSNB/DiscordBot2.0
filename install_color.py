import os
import shutil
import logging
import sys

def setup_logger():
    # Configuration du logger
    logger = logging.getLogger("ColorInstaller")
    logger.setLevel(logging.INFO)
    
    # Handler pour la console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format des logs
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Ajout du handler au logger
    logger.addHandler(console_handler)
    
    return logger

def install_color_system():
    logger = setup_logger()
    
    logger.info("🔄 Installation du système de gestion des couleurs...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Vérifier si le fichier source existe
    source_file = os.path.join(base_dir, "color.py")
    if not os.path.exists(source_file):
        logger.error(f"❌ Le fichier source {source_file} n'existe pas!")
        return False
    
    # Créer les répertoires nécessaires
    cogs_dir = os.path.join(base_dir, "cogs")
    commands_dir = os.path.join(cogs_dir, "commands")
    utils_dir = os.path.join(base_dir, "utils")
    data_dir = os.path.join(base_dir, "data")
    
    os.makedirs(cogs_dir, exist_ok=True)
    os.makedirs(commands_dir, exist_ok=True)
    os.makedirs(utils_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)
    
    # Destination pour le fichier color.py
    dest_file = os.path.join(commands_dir, "color.py")
    
    # Copier le fichier
    try:
        shutil.copy2(source_file, dest_file)
        logger.info(f"✅ Fichier color.py copié vers {dest_file}")
    except Exception as e:
        logger.error(f"❌ Erreur lors de la copie du fichier: {str(e)}")
        return False
    
    # Créer un fichier bot_settings.json par défaut s'il n'existe pas
    settings_file = os.path.join(data_dir, "bot_settings.json")
    if not os.path.exists(settings_file):
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                f.write('{\n    "embed_color": 2828211,\n    "last_modified": "Installation initiale"\n}')
            logger.info(f"✅ Fichier de configuration créé: {settings_file}")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création du fichier de configuration: {str(e)}")
    
    logger.info("✅ Installation terminée! Vous pouvez maintenant utiliser les commandes de gestion des couleurs.")
    logger.info("📝 Commandes disponibles:")
    logger.info("   !setcolor <nom_couleur | #hex> - Change la couleur des embeds")
    logger.info("   !listcolors - Affiche la liste des couleurs disponibles")
    logger.info("   !currentcolor - Affiche la couleur actuelle")
    logger.info("   !refreshmenus - Actualise tous les menus avec la nouvelle couleur")
    logger.info("   !updatebotrole - Crée/mise à jour le rôle décoratif du bot")
    
    return True

if __name__ == "__main__":
    success = install_color_system()
    sys.exit(0 if success else 1)
