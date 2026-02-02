import os
import smtplib
import json
import sqlite3
import httpx
from email.message import EmailMessage
from dotenv import load_dotenv
from app.core.logger import DB_PATH
from app.core.settings import settings

load_dotenv()

class NotificationManager:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")
        
        self.discord_url = os.getenv("DISCORD_WEBHOOK_URL")
        self.slack_url = os.getenv("SLACK_WEBHOOK_URL")

    def get_rules(self, event_type):
        try:
            # ADD TIMEOUT HERE
            conn = sqlite3.connect(DB_PATH, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT channels FROM notification_rules WHERE event_type = ? AND enabled = 1", (event_type,))
            row = c.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
            print(f"DEBUG: No enabled rules found in DB for event '{event_type}'")
            return []
        except Exception as e:
            print(f"DEBUG: DB Read Error in Notifications: {e}")
            return []

    async def send_alert(self, event_type, subject, message):
        print(f"DEBUG: Processing Alert '{event_type}'")
        channels = self.get_rules(event_type)
        
        if not channels:
            print("DEBUG: Channel list empty. Aborting.")
            return

        print(f"DEBUG: Channels active: {channels}")

        if "smtp" in channels and self.smtp_host:
            self._send_email(subject, message)
        
        if "discord" in channels and self.discord_url:
            await self._send_discord(subject, message)
            
        if "slack" in channels and self.slack_url:
            await self._send_slack(subject, message)

    def _send_email(self, subject, body):
        try:
            from_addr = settings.get("smtp_from_email", self.smtp_user)
            to_addr = settings.get("admin_alert_email", self.smtp_user)

            print(f"DEBUG: Attempting SMTP to {to_addr} from {from_addr}")

            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = f"[GoNoGo Alert] {subject}"
            msg['From'] = from_addr
            msg['To'] = to_addr

            s = smtplib.SMTP(self.smtp_host, self.smtp_port)
            s.starttls()
            s.login(self.smtp_user, self.smtp_pass)
            s.send_message(msg)
            s.quit()
            print("DEBUG: Email Sent Successfully.")
        except Exception as e:
            print(f"SMTP ERROR: {e}")

    async def _send_discord(self, subject, body):
        try:
            payload = {
                "username": "GoNoGo Watchdog",
                "embeds": [{
                    "title": subject,
                    "description": body,
                    "color": 15158332
                }]
            }
            async with httpx.AsyncClient() as client:
                await client.post(self.discord_url, json=payload)
        except Exception as e:
            print(f"DISCORD ERROR: {e}")

    async def _send_slack(self, subject, body):
        try:
            payload = {"text": f"*{subject}*\n{body}"}
            async with httpx.AsyncClient() as client:
                await client.post(self.slack_url, json=payload)
        except Exception as e:
            print(f"SLACK ERROR: {e}")

notifier = NotificationManager()