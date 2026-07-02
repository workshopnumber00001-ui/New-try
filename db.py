import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Union
from pymongo import MongoClient, errors
from pymongo.database import Database as MongoDatabase
from pymongo.collection import Collection
from vars import *
import colorama
from colorama import Fore, Style
import time
import certifi

colorama.init()

class Database:
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self._print_startup_message()
        self.client: Optional[MongoClient] = None
        self.db: Optional[MongoDatabase] = None
        self.users: Optional[Collection] = None
        self.settings: Optional[Collection] = None
        self.subject_groups: Optional[Collection] = None
        self.scheduled_fetches: Optional[Collection] = None  # नया
        self._connect_with_retry(max_retries, retry_delay)
        
    def _connect_with_retry(self, max_retries: int, retry_delay: float):
        for attempt in range(1, max_retries + 1):
            try:
                print(f"{Fore.YELLOW}⌛ Attempt {attempt}/{max_retries}: Connecting to MongoDB...{Style.RESET_ALL}")
                self.client = MongoClient(
                    MONGO_URL,
                    serverSelectionTimeoutMS=20000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=30000,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    retryReads=True
                )
                self.client.server_info()
                self.db = self.client.get_database('ugdev_db')
                self.users = self.db['users']
                self.settings = self.db['user_settings']
                self.subject_groups = self.db['subject_groups']
                self.scheduled_fetches = self.db['scheduled_fetches']  # नया
                print(f"{Fore.GREEN}✓ MongoDB Connected Successfully!{Style.RESET_ALL}")
                self._initialize_database()
                return
            except errors.ServerSelectionTimeoutError as e:
                print(f"{Fore.RED}✕ Connection attempt {attempt} failed: {str(e)}{Style.RESET_ALL}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                else:
                    raise ConnectionError(f"Failed to connect to MongoDB after {max_retries} attempts") from e
            except Exception as e:
                print(f"{Fore.RED}✕ Unexpected error: {str(e)}{Style.RESET_ALL}")
                raise

    def _print_startup_message(self):
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}🚀 UGDEV 2.0 Uploader Bot - Database Initialization")
        print(f"{'='*50}{Style.RESET_ALL}\n")

    def _initialize_database(self):
        print(f"{Fore.YELLOW}⌛ Setting up database...{Style.RESET_ALL}")
        try:
            self.users.create_index([("bot_username", 1), ("user_id", 1)], unique=True)
            self.settings.create_index([("user_id", 1)], unique=True)
            self.subject_groups.create_index([("user_id", 1), ("bot_username", 1)], unique=True)
            self.scheduled_fetches.create_index([("bot_username", 1), ("user_id", 1), ("batch_id", 1)], unique=True)
            print(f"{Fore.GREEN}✓ Database indexes created!{Style.RESET_ALL}")
            self._migrate_existing_users()
            print(f"{Fore.GREEN}✓ Database initialization complete!{Style.RESET_ALL}\n")
        except Exception as e:
            print(f"{Fore.RED}⚠ Database initialization error: {str(e)}{Style.RESET_ALL}")
            raise

    def _migrate_existing_users(self):
        try:
            update_result = self.users.update_many(
                {"bot_username": {"$exists": False}},
                {"$set": {"bot_username": "ugdevbot"}}
            )
            if update_result.modified_count > 0:
                print(f"{Fore.YELLOW}⚠ Migrated {update_result.modified_count} users{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}⚠ Could not migrate users: {str(e)}{Style.RESET_ALL}")

    # ---------- USER MANAGEMENT ----------
    def get_user(self, user_id: int, bot_username: str = "ugdevbot") -> Optional[dict]:
        try:
            return self.users.find_one({"user_id": user_id, "bot_username": bot_username})
        except Exception as e:
            print(f"{Fore.RED}Error getting user {user_id}: {str(e)}{Style.RESET_ALL}")
            return None

    def is_user_authorized(self, user_id: int, bot_username: str = "ugdevbot") -> bool:
        try:
            if user_id == OWNER_ID or user_id in ADMINS:
                return True
            user = self.get_user(user_id, bot_username)
            if not user:
                return False
            expiry = user.get('expiry_date')
            if not expiry:
                return False
            if isinstance(expiry, str):
                expiry = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
            return expiry > datetime.now()
        except Exception as e:
            print(f"{Fore.RED}Authorization error: {str(e)}{Style.RESET_ALL}")
            return False

    def add_user(self, user_id: int, name: str, days: int, bot_username: str = "ugdevbot") -> tuple[bool, Optional[datetime]]:
        try:
            expiry_date = datetime.now() + timedelta(days=days)
            update_result = self.users.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$set": {"name": name, "expiry_date": expiry_date, "added_date": datetime.now(), "last_updated": datetime.now()}},
                upsert=True
            )
            if update_result.upserted_id or update_result.modified_count > 0:
                return True, expiry_date
            return False, None
        except Exception as e:
            print(f"{Fore.RED}Add user error: {str(e)}{Style.RESET_ALL}")
            return False, None

    def remove_user(self, user_id: int, bot_username: str = "ugdevbot") -> bool:
        try:
            result = self.users.delete_one({"user_id": user_id, "bot_username": bot_username})
            return result.deleted_count > 0
        except Exception as e:
            print(f"{Fore.RED}Remove user error: {str(e)}{Style.RESET_ALL}")
            return False

    def list_users(self, bot_username: str = "ugdevbot") -> List[dict]:
        try:
            return list(self.users.find({"bot_username": bot_username}, {"_id": 0, "name": 1, "user_id": 1, "expiry_date": 1}))
        except Exception as e:
            print(f"{Fore.RED}List users error: {str(e)}{Style.RESET_ALL}")
            return []

    def is_admin(self, user_id: int) -> bool:
        try:
            return user_id == OWNER_ID or user_id in ADMINS
        except Exception as e:
            print(f"{Fore.RED}Admin check error: {str(e)}{Style.RESET_ALL}")
            return False

    def list_bot_usernames(self) -> List[str]:
        try:
            usernames = self.users.distinct("bot_username")
            return usernames if usernames else ["ugdevbot"]
        except Exception as e:
            print(f"{Fore.RED}List bot usernames error: {str(e)}{Style.RESET_ALL}")
            return ["ugdevbot"]

    # ---------- SETTINGS ----------
    def get_user_settings(self, user_id: int, bot_username: str) -> dict:
        try:
            doc = self.settings.find_one({"user_id": user_id, "bot_username": bot_username})
            if doc:
                return doc.get("settings", {})
            return {}
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {}

    def update_user_setting(self, user_id: int, bot_username: str, key: str, value):
        try:
            result = self.settings.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$set": {f"settings.{key}": value}},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"Error updating setting {key}: {e}")
            return False

    # ---------- SUBJECT GROUPS ----------
    def get_subject_groups(self, user_id: int, bot_username: str) -> dict:
        try:
            doc = self.subject_groups.find_one({"user_id": user_id, "bot_username": bot_username})
            if doc:
                return doc.get("groups", {})
            return {}
        except Exception as e:
            print(f"Error getting subject groups: {e}")
            return {}

    def add_subject_group(self, user_id: int, bot_username: str, subject: str, chat_id: int) -> bool:
        try:
            result = self.subject_groups.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$set": {f"groups.{subject}": chat_id}},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"Error adding subject group: {e}")
            return False

    def remove_subject_group(self, user_id: int, bot_username: str, subject: str) -> bool:
        try:
            result = self.subject_groups.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$unset": {f"groups.{subject}": ""}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error removing subject group: {e}")
            return False

    def get_default_group(self, user_id: int, bot_username: str) -> int:
        try:
            doc = self.subject_groups.find_one({"user_id": user_id, "bot_username": bot_username})
            if doc:
                return doc.get("default_chat_id")
            return None
        except Exception as e:
            print(f"Error getting default group: {e}")
            return None

    def set_default_group(self, user_id: int, bot_username: str, chat_id: int) -> bool:
        try:
            result = self.subject_groups.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$set": {"default_chat_id": chat_id}},
                upsert=True
            )
            return result.modified_count > 0 or result.upserted_id is not None
        except Exception as e:
            print(f"Error setting default group: {e}")
            return False

    def get_group_for_file(self, user_id: int, title: str, bot_username: str) -> int:
        groups = self.get_subject_groups(user_id, bot_username)
        for subject, chat_id in groups.items():
            if subject.lower() in title.lower():
                return chat_id
        default = self.get_default_group(user_id, bot_username)
        return default

    # ---------- SCHEDULED FETCHES ----------
    def add_schedule(self, user_id: int, bot_username: str, batch_id: str, time_str: str, source: str = "generic", channel_id: int = None):
        self.scheduled_fetches.update_one(
            {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
            {"$set": {"time": time_str, "source": source, "enabled": True, "last_run_date": None, "channel_id": channel_id}},
            upsert=True
        )

    def remove_schedule(self, user_id: int, bot_username: str, batch_id: str):
        self.scheduled_fetches.delete_one({"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id})

    def get_schedules(self, bot_username: str):
        return list(self.scheduled_fetches.find({"bot_username": bot_username, "enabled": True}))

    def get_due_schedules(self, bot_username: str, time_str: str, date_str: str):
        return list(self.scheduled_fetches.find({
            "bot_username": bot_username,
            "enabled": True,
            "time": time_str,
            "$or": [{"last_run_date": {"$ne": date_str}}, {"last_run_date": None}]
        }))

    def update_last_run(self, user_id: int, bot_username: str, batch_id: str, date_str: str):
        self.scheduled_fetches.update_one(
            {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
            {"$set": {"last_run_date": date_str}}
        )

    def toggle_schedule(self, user_id: int, bot_username: str, batch_id: str, enabled: bool):
        self.scheduled_fetches.update_one(
            {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
            {"$set": {"enabled": enabled}}
        )

    # ---------- LOG CHANNEL ----------
    def get_log_channel(self, bot_username: str):
        try:
            settings = self.db.bot_settings.find_one({"bot_username": bot_username})
            if settings and 'log_channel' in settings:
                return settings['log_channel']
            return None
        except Exception as e:
            print(f"Error getting log channel: {str(e)}")
            return None

    def set_log_channel(self, bot_username: str, channel_id: int):
        try:
            self.db.bot_settings.update_one(
                {"bot_username": bot_username},
                {"$set": {"log_channel": channel_id}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error setting log channel: {str(e)}")
            return False

    def close(self):
        if self.client:
            self.client.close()
            print(f"{Fore.YELLOW}✓ MongoDB connection closed{Style.RESET_ALL}")

# Initialize
try:
    db = Database(max_retries=3, retry_delay=2)
except Exception as e:
    print(f"{Fore.RED}✕ Fatal Error: DB initialization failed!{Style.RESET_ALL}")
    raise
