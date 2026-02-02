import sqlite3
import datetime
import os

DB_PATH = "flight_logs.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        # ENABLE WAL MODE (Fixes concurrency locking)
        conn.execute("PRAGMA journal_mode=WAL")
        c = conn.cursor()
        
        # 1. LOGS TABLE
        c.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
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
            )
        ''')

        try:
            c.execute("ALTER TABLE logs ADD COLUMN model_used TEXT")
            c.execute("ALTER TABLE logs ADD COLUMN tokens_used INTEGER")
        except sqlite3.OperationalError: pass

        # 2. FLIGHT CACHE
        c.execute('''
            CREATE TABLE IF NOT EXISTS flight_cache (
                key TEXT PRIMARY KEY,
                icao TEXT,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                data TEXT
            )
        ''')

        # 3. SETTINGS
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT
            )
        ''')

        # 4. NOTIFICATION RULES
        c.execute('''
            CREATE TABLE IF NOT EXISTS notification_rules (
                event_type TEXT,
                channels TEXT,
                enabled INTEGER DEFAULT 1,
                PRIMARY KEY (event_type)
            )
        ''')

        defaults = [
            ("rate_limit_calls", "5", "Max requests allowed per period"),
            ("rate_limit_period", "300", "Period in seconds"),
            ("global_pause", "false", "Pause system"),
            ("global_pause_message", "Maintenance in progress.", "Pause message"),
            ("app_timezone", "UTC", "Log Timezone"),
            ("openai_model", "gpt-4o-mini", "AI Model"),
            ("smtp_from_email", "alerts@yourdomain.com", "From Email"),
            ("admin_alert_email", "you@yourdomain.com", "To Email")
        ]
        
        for key, val, desc in defaults:
            c.execute("INSERT OR IGNORE INTO system_settings (key, value, description) VALUES (?, ?, ?)", (key, val, desc))

        c.execute("INSERT OR IGNORE INTO notification_rules (event_type, channels, enabled) VALUES ('rate_limit', '[\"smtp\"]', 1)")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB INIT ERROR: {e}")

def log_attempt(client_id, ip, input_icao, resolved_icao, plane, duration, status, error_msg=None, model=None, tokens=0):
    try:
        # Add timeout to prevent immediate failure if locked
        conn = sqlite3.connect(DB_PATH, timeout=10.0) 
        c = conn.cursor()
        c.execute('''
            INSERT INTO logs (
                timestamp, client_id, ip_address, input_icao, resolved_icao, 
                plane_profile, duration_seconds, status, error_message,
                model_used, tokens_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.datetime.now(), client_id, ip, input_icao, resolved_icao, 
            plane, duration, status, error_msg, model, tokens
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"LOGGING ERROR: {e}")