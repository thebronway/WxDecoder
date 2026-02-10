import os
import logging
import redis.asyncio as redis
from databases import Database

# Configure Logger
logger = logging.getLogger(__name__)

# 1. DATABASE CONNECTION
DATABASE_URL = os.getenv("DATABASE_URL")
database = Database(DATABASE_URL)

# 2. CACHE CONNECTION
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def init_db_tables():
    """
    Creates tables if they don't exist and adds performance indices.
    """
    query_logs = """
    CREATE TABLE IF NOT EXISTS logs (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        client_id TEXT,
        ip_address TEXT,
        input_icao TEXT,
        resolved_icao TEXT,
        plane_profile TEXT,
        duration_seconds REAL,
        status TEXT,
        error_message TEXT,
        model_used TEXT,
        tokens_used INTEGER
    );
    """
    
    query_cache = """
    CREATE TABLE IF NOT EXISTS flight_cache (
        key TEXT PRIMARY KEY,
        icao TEXT,
        category TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data TEXT
    );
    """
    
    query_settings = """
    CREATE TABLE IF NOT EXISTS system_settings (
        key TEXT PRIMARY KEY,
        value TEXT,
        description TEXT
    );
    """
    
    query_notif = """
    CREATE TABLE IF NOT EXISTS notification_rules (
        event_type TEXT PRIMARY KEY,
        channels TEXT,
        enabled INTEGER DEFAULT 1
    );
    """
    
    try:
        async with database.transaction():
            await database.execute(query_logs)
            await database.execute(query_cache)
            await database.execute(query_settings)
            await database.execute(query_notif)
            
            await database.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            await database.execute("CREATE INDEX IF NOT EXISTS idx_logs_client_id ON logs(client_id)")
            await database.execute("CREATE INDEX IF NOT EXISTS idx_logs_input_icao ON logs(input_icao)")

            try:
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS weather_icao TEXT")
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS expiration_timestamp TIMESTAMP")                
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS duration_wx REAL")
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS duration_notams REAL")
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS duration_ai REAL")
                await database.execute("ALTER TABLE logs ADD COLUMN IF NOT EXISTS duration_alt REAL")
            except Exception as ex:
                logger.warning(f"Schema migration warning: {ex}")

    except Exception as e:
        logger.info(f"DB Init skipped or failed (likely race condition): {e}")