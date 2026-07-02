import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from pymongo import MongoClient, errors
from pymongo.database import Database as MongoDatabase
from pymongo.collection import Collection
from vars import *
import colorama
from colorama import Fore, Style
import time
import certifi

# Init colors for Windows
colorama.init()

class Database:
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        """
        Initialize MongoDB connection with retry logic
        """
        self._print_startup_message()
        self.client: Optional[MongoClient] = None
        self.db: Optional[MongoDatabase] = None
        self.users: Optional[Collection] = None
        self.settings: Optional[Collection] = None
        self.subject_groups: Optional[Collection] = None
        self.scheduled_fetches: Optional[Collection] = None
        self.bot_settings: Optional[Collection] = None
        
        self._connect_with_retry(max_retries, retry_delay)
        
    def _connect_with_retry(self, max_retries: int, retry_delay: float):
        """Establish MongoDB connection with retry mechanism"""
        for attempt in range(1, max_retries + 1):
            try:
                print(f"{Fore.YELLOW}⌛ Attempt {attempt}/{max_retries}: Connecting to MongoDB...{Style.RESET_ALL}")
                
                # Enhanced connection parameters
                self.client = MongoClient(
                    MONGO_URL,
                    serverSelectionTimeoutMS=20000,
                    connectTimeoutMS=20000,
                    socketTimeoutMS=30000,
                    tlsCAFile=certifi.where(),
                    retryWrites=True,
                    retryReads=True
                )
                
                # Test connection
                self.client.server_info()
                
                # Initialize database and collections
                self.db = self.client.get_database(DATABASE_NAME)
                self.users = self.db['users']
                self.settings = self.db['user_settings']
                self.subject_groups = self.db['subject_groups']
                self.scheduled_fetches = self.db['scheduled_fetches']
                self.bot_settings = self.db['bot_settings']
                
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
                print(f"{Fore.RED}✕ Unexpected error during connection: {str(e)}{Style.RESET_ALL}")
                raise

    def _print_startup_message(self):
        """Print formatted startup message"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print(f"{Fore.CYAN}🚀 UGDEV 2.0 Uploader Bot - Database Initialization")
        print(f"{'='*50}{Style.RESET_ALL}\n")

    def _initialize_database(self):
        """Initialize database indexes safely - check existence first"""
        print(f"{Fore.YELLOW}⌛ Setting up database indexes...{Style.RESET_ALL}")
        
        try:
            # ---------- USERS COLLECTION ----------
            existing_indexes = self.users.index_information()
            if "user_identity" not in existing_indexes:
                self.users.create_index(
                    [("bot_username", 1), ("user_id", 1)], 
                    unique=True,
                    name="user_identity"
                )
                print(f"{Fore.GREEN}✓ Created index: user_identity{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Index already exists: user_identity (skipped){Style.RESET_ALL}")

            # ---------- SETTINGS COLLECTION ----------
            existing_indexes = self.settings.index_information()
            if "user_settings" not in existing_indexes:
                self.settings.create_index(
                    [("user_id", 1)],
                    unique=True,
                    name="user_settings"
                )
                print(f"{Fore.GREEN}✓ Created index: user_settings{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Index already exists: user_settings (skipped){Style.RESET_ALL}")

            # ---------- SUBJECT GROUPS ----------
            existing_indexes = self.subject_groups.index_information()
            if "subject_groups_index" not in existing_indexes:
                self.subject_groups.create_index(
                    [("user_id", 1), ("bot_username", 1)],
                    unique=True,
                    name="subject_groups_index"
                )
                print(f"{Fore.GREEN}✓ Created index: subject_groups_index{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Index already exists: subject_groups_index (skipped){Style.RESET_ALL}")

            # ---------- SCHEDULED FETCHES ----------
            existing_indexes = self.scheduled_fetches.index_information()
            if "scheduled_fetches_index" not in existing_indexes:
                self.scheduled_fetches.create_index(
                    [("bot_username", 1), ("user_id", 1), ("batch_id", 1)],
                    unique=True,
                    name="scheduled_fetches_index"
                )
                print(f"{Fore.GREEN}✓ Created index: scheduled_fetches_index{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Index already exists: scheduled_fetches_index (skipped){Style.RESET_ALL}")

            print(f"{Fore.GREEN}✓ Database initialization complete!{Style.RESET_ALL}\n")
            
        except Exception as e:
            print(f"{Fore.RED}⚠ Database initialization error: {str(e)}{Style.RESET_ALL}")
            raise

    # ==================== USER MANAGEMENT ====================
    def get_user(self, user_id: int, bot_username: str = "ugdevbot") -> Optional[dict]:
        """Retrieve a user document"""
        try:
            return self.users.find_one({
                "user_id": user_id,
                "bot_username": bot_username
            })
        except Exception as e:
            print(f"{Fore.RED}Error getting user {user_id}: {str(e)}{Style.RESET_ALL}")
            return None

    def is_user_authorized(self, user_id: int, bot_username: str = "ugdevbot") -> bool:
        """Check if user is authorized (admin or has valid subscription)"""
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
            print(f"{Fore.RED}Authorization error for {user_id}: {str(e)}{Style.RESET_ALL}")
            return False

    def add_user(self, user_id: int, name: str, days: int, bot_username: str = "ugdevbot") -> tuple[bool, Optional[datetime]]:
        """Add or update a user in the database"""
        try:
            expiry_date = datetime.now() + timedelta(days=days)
            update_result = self.users.update_one(
                {"user_id": user_id, "bot_username": bot_username},
                {"$set": {
                    "name": name,
                    "expiry_date": expiry_date,
                    "added_date": datetime.now(),
                    "last_updated": datetime.now()
                }},
                upsert=True
            )
            if update_result.upserted_id or update_result.modified_count > 0:
                return True, expiry_date
            return False, None
        except Exception as e:
            print(f"{Fore.RED}Add user error for {user_id}: {str(e)}{Style.RESET_ALL}")
            return False, None

    def remove_user(self, user_id: int, bot_username: str = "ugdevbot") -> bool:
        """Remove a user from the database"""
        try:
            result = self.users.delete_one({
                "user_id": user_id,
                "bot_username": bot_username
            })
            return result.deleted_count > 0
        except Exception as e:
            print(f"{Fore.RED}Remove user error for {user_id}: {str(e)}{Style.RESET_ALL}")
            return False

    def list_users(self, bot_username: str = "ugdevbot") -> List[dict]:
        """List all users for a specific bot"""
        try:
            return list(self.users.find(
                {"bot_username": bot_username},
                {"_id": 0, "name": 1, "user_id": 1, "expiry_date": 1}
            ))
        except Exception as e:
            print(f"{Fore.RED}List users error: {str(e)}{Style.RESET_ALL}")
            return []

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin or owner"""
        try:
            return user_id == OWNER_ID or user_id in ADMINS
        except Exception as e:
            print(f"{Fore.RED}Admin check error: {str(e)}{Style.RESET_ALL}")
            return False

    def list_bot_usernames(self) -> List[str]:
        """Get distinct bot usernames from users collection"""
        try:
            usernames = self.users.distinct("bot_username")
            return usernames if usernames else ["ugdevbot"]
        except Exception as e:
            print(f"{Fore.RED}List bot usernames error: {str(e)}{Style.RESET_ALL}")
            return ["ugdevbot"]

    # ==================== SETTINGS SYSTEM ====================
    def get_user_settings(self, user_id: int, bot_username: str) -> dict:
        """Get all settings for a user."""
        try:
            doc = self.settings.find_one({"user_id": user_id, "bot_username": bot_username})
            if doc:
                return doc.get("settings", {})
            return {}
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {}

    def update_user_setting(self, user_id: int, bot_username: str, key: str, value):
        """Update a single setting for a user."""
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

    def delete_user_settings(self, user_id: int, bot_username: str):
        """Delete all settings for a user (reset)."""
        try:
            result = self.settings.delete_one({"user_id": user_id, "bot_username": bot_username})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting settings: {e}")
            return False

    # ==================== SUBJECT GROUP MANAGEMENT ====================
    def get_subject_groups(self, user_id: int, bot_username: str) -> dict:
        """Returns dict of {subject: chat_id} for this user."""
        try:
            doc = self.subject_groups.find_one(
                {"user_id": user_id, "bot_username": bot_username}
            )
            if doc:
                return doc.get("groups", {})
            return {}
        except Exception as e:
            print(f"Error getting subject groups: {e}")
            return {}

    def add_subject_group(self, user_id: int, bot_username: str, subject: str, chat_id: int) -> bool:
        """Add a subject->chat mapping."""
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
        """Remove a subject mapping."""
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
        """Get default chat ID for unmatched files."""
        try:
            doc = self.subject_groups.find_one(
                {"user_id": user_id, "bot_username": bot_username}
            )
            if doc:
                return doc.get("default_chat_id")
            return None
        except Exception as e:
            print(f"Error getting default group: {e}")
            return None

    def set_default_group(self, user_id: int, bot_username: str, chat_id: int) -> bool:
        """Set default chat ID for unmatched files."""
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
        """Find matching subject group for a given file title."""
        groups = self.get_subject_groups(user_id, bot_username)
        for subject, chat_id in groups.items():
            if subject.lower() in title.lower():
                return chat_id
        default = self.get_default_group(user_id, bot_username)
        return default

    # ==================== SCHEDULED FETCHES ====================
    def add_schedule(self, user_id: int, bot_username: str, batch_id: str, time_str: str, source: str = "generic", channel_id: int = None):
        """Add or update a scheduled fetch"""
        try:
            self.scheduled_fetches.update_one(
                {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
                {"$set": {
                    "time": time_str, 
                    "source": source, 
                    "enabled": True, 
                    "last_run_date": None, 
                    "channel_id": channel_id
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error adding schedule: {e}")
            return False

    def remove_schedule(self, user_id: int, bot_username: str, batch_id: str):
        """Remove a scheduled fetch"""
        try:
            self.scheduled_fetches.delete_one({
                "user_id": user_id, 
                "bot_username": bot_username, 
                "batch_id": batch_id
            })
            return True
        except Exception as e:
            print(f"Error removing schedule: {e}")
            return False

    def get_schedules(self, bot_username: str) -> List[dict]:
        """Get all active schedules for a bot"""
        try:
            return list(self.scheduled_fetches.find({
                "bot_username": bot_username, 
                "enabled": True
            }))
        except Exception as e:
            print(f"Error getting schedules: {e}")
            return []

    def get_due_schedules(self, bot_username: str, time_str: str, date_str: str) -> List[dict]:
        """Get schedules that are due to run"""
        try:
            return list(self.scheduled_fetches.find({
                "bot_username": bot_username,
                "enabled": True,
                "time": time_str,
                "$or": [{"last_run_date": {"$ne": date_str}}, {"last_run_date": None}]
            }))
        except Exception as e:
            print(f"Error getting due schedules: {e}")
            return []

    def update_last_run(self, user_id: int, bot_username: str, batch_id: str, date_str: str):
        """Update last run date for a schedule"""
        try:
            self.scheduled_fetches.update_one(
                {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
                {"$set": {"last_run_date": date_str}}
            )
            return True
        except Exception as e:
            print(f"Error updating last run: {e}")
            return False

    def toggle_schedule(self, user_id: int, bot_username: str, batch_id: str, enabled: bool):
        """Enable or disable a schedule"""
        try:
            self.scheduled_fetches.update_one(
                {"user_id": user_id, "bot_username": bot_username, "batch_id": batch_id},
                {"$set": {"enabled": enabled}}
            )
            return True
        except Exception as e:
            print(f"Error toggling schedule: {e}")
            return False

    # ==================== LOG CHANNEL ====================
    def get_log_channel(self, bot_username: str):
        """Get the log channel ID for a specific bot"""
        try:
            settings = self.bot_settings.find_one({"bot_username": bot_username})
            if settings and 'log_channel' in settings:
                return settings['log_channel']
            return None
        except Exception as e:
            print(f"Error getting log channel: {str(e)}")
            return None

    def set_log_channel(self, bot_username: str, channel_id: int):
        """Set the log channel ID for a specific bot"""
        try:
            self.bot_settings.update_one(
                {"bot_username": bot_username},
                {"$set": {"log_channel": channel_id}},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error setting log channel: {str(e)}")
            return False

    # ==================== CLEANUP ====================
    async def cleanup_expired_users(self, bot) -> int:
        """Clean up expired users and notify them"""
        try:
            current_time = datetime.now()
            expired_users = self.users.find({
                "expiry_date": {"$lt": current_time},
                "user_id": {"$nin": [OWNER_ID] + ADMINS}
            })
            removed_count = 0
            for user in expired_users:
                try:
                    await bot.send_message(
                        user["user_id"],
                        f"**⚠️ Your subscription has expired!**\n\n"
                        f"• Name: {user['name']}\n"
                        f"• Expired on: {user['expiry_date'].strftime('%d-%m-%Y')}\n\n"
                        f"Contact admin to renew your subscription."
                    )
                    self.users.delete_one({"_id": user["_id"]})
                    removed_count += 1
                except Exception as e:
                    print(f"Error processing user {user['user_id']}: {str(e)}")
                    continue
            return removed_count
        except Exception as e:
            print(f"{Fore.RED}Cleanup error: {str(e)}{Style.RESET_ALL}")
            return 0

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print(f"{Fore.YELLOW}✓ MongoDB connection closed{Style.RESET_ALL}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# Initialize database
try:
    db = Database(max_retries=3, retry_delay=2)
    print(f"{Fore.GREEN}✅ Database initialized successfully!{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}❌ Fatal Error: DB initialization failed!{Style.RESET_ALL}")
    print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
    raise
