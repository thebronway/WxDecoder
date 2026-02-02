import json
from app.core.db import database

class SettingsManager:
    # In-memory cache to reduce DB hits
    _cache = {}

    async def load(self):
        """Populate cache from DB on startup"""
        query = "SELECT key, value FROM system_settings"
        rows = await database.fetch_all(query=query)
        self._cache = {row["key"]: row["value"] for row in rows}

    def get(self, key, default=None):
        # We read from memory (fast), no await needed for reading
        return self._cache.get(key, default)

    async def set(self, key, value):
        # Write to DB asynchronously
        query = """
            INSERT INTO system_settings (key, value) VALUES (:key, :value)
            ON CONFLICT (key) DO UPDATE SET value = :value
        """
        await database.execute(query=query, values={"key": key, "value": str(value)})
        self._cache[key] = str(value) # Update local cache
        return True

    async def get_all_rules(self):
        """Fetch notification rules"""
        query = "SELECT * FROM notification_rules"
        rows = await database.fetch_all(query)
        return [dict(row) for row in rows]

    async def set_rule(self, event_type, channels, enabled):
        query = """
            INSERT INTO notification_rules (event_type, channels, enabled) 
            VALUES (:event_type, :channels, :enabled)
            ON CONFLICT (event_type) DO UPDATE 
            SET channels = :channels, enabled = :enabled
        """
        values = {
            "event_type": event_type,
            "channels": json.dumps(channels),
            "enabled": 1 if enabled else 0
        }
        await database.execute(query, values)

settings = SettingsManager()