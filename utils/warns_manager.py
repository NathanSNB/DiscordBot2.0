import json
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger('bot')

class WarnsManager:
    def __init__(self, file_path="data/warns.json"):
        self.file_path = file_path
        self.warnings = {}
        self.bot = None
        self._load_warns()

    def set_bot(self, bot):
        """Définit l'instance du bot pour les événements"""
        self.bot = bot

    def _load_warns(self):
        """Charge les avertissements depuis le fichier JSON"""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.warnings = {
                        int(k): [
                            (datetime.fromisoformat(w[0]), w[1], w[2])
                            for w in v
                        ] for k, v in data.items()
                    }
                logger.info(f"✅ {len(self.warnings)} avertissements chargés depuis {self.file_path}")
            else:
                os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
                self._save_warns()
                logger.info("📝 Nouveau fichier d'avertissements créé")
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des avertissements: {e}")
            self.warnings = {}

    def _save_warns(self):
        """Sauvegarde les avertissements dans le fichier JSON"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                data = {
                    str(k): [
                        (w[0].isoformat(), w[1], w[2])
                        for w in v
                    ] for k, v in self.warnings.items()
                }
                json.dump(data, f, indent=4, ensure_ascii=False)
            logger.info("💾 Avertissements sauvegardés")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des avertissements: {e}")

    async def add_warning(self, user_id: int, reason: str, author_id: int) -> int:
        """Ajoute un avertissement et retourne le nombre total"""
        current_time = datetime.now()
        
        if user_id not in self.warnings:
            self.warnings[user_id] = []

        self.warnings[user_id].append((current_time, reason, author_id))
        self._save_warns()

        # Amélioration de la gestion des événements
        if self.bot:
            try:
                user = await self.bot.fetch_user(user_id)
                author = await self.bot.fetch_user(author_id)
                if user and author:
                    total_warns = len(self.warnings[user_id])
                    self.bot.dispatch('warning_add', user, reason, author, total_warns)
                    
                    # Vérification pour le mute automatique
                    if total_warns >= 3 and all(
                        datetime.now() - w[0] <= timedelta(minutes=20)
                        for w in self.warnings[user_id][-3:]
                    ):
                        self.bot.dispatch('warning_auto_mute', user)
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'envoi du log d'avertissement: {e}")
        
        return len(self.warnings[user_id])

    async def remove_warning(self, user_id: int, warn_index: int, author_id: int) -> bool:
        """Supprime un avertissement spécifique"""
        if user_id in self.warnings and 0 <= warn_index < len(self.warnings[user_id]):
            self.warnings[user_id].pop(warn_index)
            self._save_warns()
            
            # Déclencher l'événement de log
            if self.bot:
                try:
                    member = await self.bot.fetch_user(user_id)
                    author = await self.bot.fetch_user(author_id)
                    self.bot.dispatch('warning_remove', member, author, warn_index + 1)
                except Exception as e:
                    logger.error(f"Erreur lors de l'envoi du log de suppression d'avertissement: {e}")
            
            return True
        return False

    def clean_warnings(self, user_id: int):
        """Nettoie les avertissements expirés"""
        if user_id not in self.warnings:
            return

        initial_count = len(self.warnings[user_id])
        current_time = datetime.now()
        has_recent_warn = any(
            current_time - w[0] <= timedelta(hours=24)
            for w in self.warnings[user_id]
        )

        if has_recent_warn:
            self.warnings[user_id] = [
                w for w in self.warnings[user_id]
                if current_time - w[0] <= timedelta(minutes=20)
            ]
        else:
            self.warnings[user_id] = []

        # Amélioration de la notification d'expiration
        if self.bot and len(self.warnings[user_id]) < initial_count:
            try:
                self.bot.dispatch('warning_expire', self.bot.get_user(user_id))
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'envoi du log d'expiration: {e}")
        
        self._save_warns()

    def get_warnings(self, user_id: int):
        """Récupère les avertissements actifs d'un utilisateur"""
        self.clean_warnings(user_id)
        return self.warnings.get(user_id, [])
