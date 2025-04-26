from typing import Set
import json
import os

class PermissionManager:
    def __init__(self, data_path: str):
        self.data_path = data_path
        self.permissions = {}
        self._load_permissions()

    def _load_permissions(self):
        try:
            if os.path.exists(self.data_path):
                with open(self.data_path, 'r') as f:
                    self.permissions = json.load(f)
        except Exception as e:
            print(f"Erreur de chargement: {e}")
            self.permissions = {}

    def save_permissions(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        with open(self.data_path, 'w') as f:
            json.dump(self.permissions, f, indent=4)

    def get_user_permissions(self, user_id: int) -> Set[int]:
        user_id = str(user_id)
        return set(map(int, self.permissions.get(user_id, [])))

    def has_permission(self, user_id: int, level: int) -> bool:
        return level in self.get_user_permissions(user_id)

    def add_permission(self, user_id: int, level: int) -> bool:
        user_id = str(user_id)
        if user_id not in self.permissions:
            self.permissions[user_id] = []
        if level not in self.permissions[user_id]:
            self.permissions[user_id].append(level)
            self.save_permissions()
            return True
        return False
