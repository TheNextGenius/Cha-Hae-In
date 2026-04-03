import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from config import DATABASE_PATH

logger = logging.getLogger('database')

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.migrate_from_json()

    def create_tables(self):
        """Create all required tables"""
        cursor = self.conn.cursor()

        # Players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                next_level_exp INTEGER DEFAULT 100,
                rank TEXT DEFAULT 'E',
                gold INTEGER DEFAULT 1500,
                mana INTEGER DEFAULT 150,
                max_mana INTEGER DEFAULT 150,
                hp INTEGER DEFAULT 300,
                max_hp INTEGER DEFAULT 300,
                last_seen REAL,
                class TEXT DEFAULT 'Hunter',
                stats TEXT DEFAULT '{"str":10,"agi":10,"vit":10,"int":10,"sense":10}',
                shadows TEXT DEFAULT '[]',
                inventory TEXT DEFAULT '{"Health Potion":5,"Mana Potion":3}',
                daily TEXT DEFAULT '2000-01-01',
                quests TEXT DEFAULT '{"msg_daily":0,"bosses":0}',
                training_cd TEXT DEFAULT '{"pushup":0,"squat":0,"run":0}',
                created_at REAL DEFAULT (strftime('%s', 'now')),
                updated_at REAL DEFAULT (strftime('%s', 'now'))
            )
        ''')

        # Servers table (track guilds the bot is in)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                guild_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                member_count INTEGER DEFAULT 0,
                joined_at REAL DEFAULT (strftime('%s', 'now')),
                last_seen REAL
            )
        ''')

        # Analytics: Command usage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS command_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT,
                user_id TEXT,
                command TEXT NOT NULL,
                used_at REAL DEFAULT (strftime('%s', 'now')),
                FOREIGN KEY (guild_id) REFERENCES servers(guild_id),
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')

        # Items shop
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shop_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price INTEGER NOT NULL,
                type TEXT NOT NULL,
                stats_bonus TEXT DEFAULT '{}',
                description TEXT,
                available BOOLEAN DEFAULT 1
            )
        ''')

        # Insert default shop items if empty
        cursor.execute("SELECT COUNT(*) FROM shop_items")
        if cursor.fetchone()[0] == 0:
            default_items = [
                ("Health Potion", 200, "consumable", '{"heal":100}', "Restores 100 HP", 1),
                ("Mana Potion", 300, "consumable", '{"restore_mana":80}', "Restores 80 Mana", 1),
                ("Strength Elixir", 1000, "consumable", '{"str":5}', "+5 STR for 1 hour", 1),
                ("Hunter's Dagger", 5000, "weapon", '{"str":15,"agi":5}', "A sharp hunter's blade", 1),
                ("S-Rank Badge", 25000, "accessory", '{"rank_bonus":1.1}', "10% more stat gain", 1),
            ]
            cursor.executemany(
                "INSERT INTO shop_items (name, price, type, stats_bonus, description, available) VALUES (?, ?, ?, ?, ?, ?)",
                default_items
            )

        # Equipment table (user inventory equipment)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equipment (
                user_id TEXT,
                item_id INTEGER,
                equipped BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES players(user_id),
                FOREIGN KEY (item_id) REFERENCES shop_items(id)
            )
        ''')

        self.conn.commit()
        logger.info("Database tables created/verified")

    def migrate_from_json(self):
        """Migrate existing JSON data to SQLite"""
        try:
            with open('db.json', 'r') as f:
                json_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No JSON data found or invalid, starting fresh")
            return

        cursor = self.conn.cursor()
        migrated = 0

        for user_id, player_data in json_data.items():
            # Check if already exists
            cursor.execute("SELECT user_id FROM players WHERE user_id = ?", (str(user_id),))
            if cursor.fetchone():
                continue

            # Insert player data
            cursor.execute('''
                INSERT INTO players (
                    user_id, name, level, exp, next_level_exp, rank, gold, mana, max_mana,
                    hp, max_hp, last_seen, class, stats, shadows, inventory, daily,
                    quests, training_cd, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(user_id),
                player_data.get('name', 'Unknown'),
                player_data.get('lv', 1),
                player_data.get('exp', 0),
                player_data.get('next', 100),
                player_data.get('rank', 'E'),
                player_data.get('gold', 1500),
                player_data.get('mana', 150),
                player_data.get('max_mana', 150),
                player_data.get('hp', 300),
                player_data.get('max_hp', 300),
                player_data.get('last_seen', datetime.now().timestamp()),
                player_data.get('class', 'Hunter'),
                json.dumps(player_data.get('stats', {"str":10,"agi":10,"vit":10,"int":10,"sense":10})),
                json.dumps(player_data.get('shadows', [])),
                json.dumps(player_data.get('inv', {"Health Potion":5,"Mana Potion":3})),
                player_data.get('daily', '2000-01-01'),
                json.dumps(player_data.get('quests', {"msg_daily":0,"bosses":0})),
                json.dumps(player_data.get('training_cd', {"pushup":0,"squat":0,"run":0})),
                datetime.now().timestamp(),
                datetime.now().timestamp()
            ))
            migrated += 1

        self.conn.commit()
        logger.info(f"Migrated {migrated} players from JSON to SQLite")

    def get_player_row(self, user_id: str) -> Optional[sqlite3.Row]:
        """Get player row by user_id"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players WHERE user_id = ?", (str(user_id),))
        return cursor.fetchone()

    def create_player(self, user_id: str, name: str) -> bool:
        """Create new player if doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM players WHERE user_id = ?", (str(user_id),))
        if cursor.fetchone():
            return False

        now = datetime.now().timestamp()
        cursor.execute('''
            INSERT INTO players (
                user_id, name, level, exp, next_level_exp, rank, gold, mana, max_mana,
                hp, max_hp, last_seen, class, stats, shadows, inventory, daily,
                quests, training_cd, created_at, updated_at
            ) VALUES (?, ?, 1, 0, 100, 'E', 1500, 150, 150, 300, 300, ?, 'Hunter',
                      '{"str":10,"agi":10,"vit":10,"int":10,"sense":10}',
                      '[]', '{"Health Potion":5,"Mana Potion":3}',
                      '2000-01-01', '{"msg_daily":0,"bosses":0}',
                      '{"pushup":0,"squat":0,"run":0}', ?, ?)
        ''', (now, now, now, now))

        self.conn.commit()
        return True

    def update_player(self, user_id: str, data: Dict[str, Any]):
        """Update player fields"""
        cursor = self.conn.cursor()

        # Build SET clause dynamically
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        values = list(data.values())
        values.append(str(user_id))

        cursor.execute(f"UPDATE players SET {set_clause}, updated_at = ? WHERE user_id = ?", values)
        self.conn.commit()

    def increment_stat(self, user_id: str, field: str, amount: int):
        """Increment a numeric field"""
        cursor = self.conn.cursor()
        if field in ['exp', 'gold', 'level', 'hp', 'mana', 'max_hp', 'max_mana']:
            cursor.execute(f"UPDATE players SET {field} = {field} + ?, updated_at = ? WHERE user_id = ?",
                          (amount, datetime.now().timestamp(), str(user_id)))
        else:
            # For JSON fields like stats, need special handling
            pass
        self.conn.commit()

    def get_all_players(self) -> List[sqlite3.Row]:
        """Get all players"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM players")
        return cursor.fetchall()

    def get_server(self, guild_id: str) -> Optional[sqlite3.Row]:
        """Get server info"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM servers WHERE guild_id = ?", (str(guild_id),))
        return cursor.fetchone()

    def update_server(self, guild_id: str, name: str, member_count: int):
        """Update or create server entry"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO servers (guild_id, name, member_count, last_seen)
            VALUES (?, ?, ?, ?)
        ''', (str(guild_id), name, member_count, datetime.now().timestamp()))
        self.conn.commit()

    def log_command(self, guild_id: str, user_id: str, command: str):
        """Log command usage"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO command_usage (guild_id, user_id, command)
            VALUES (?, ?, ?)
        ''', (str(guild_id), str(user_id), command))
        self.conn.commit()

    def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get analytics data"""
        cursor = self.conn.cursor()
        cutoff = datetime.now().timestamp() - (days * 86400)

        # Total players
        cursor.execute("SELECT COUNT(*) FROM players")
        total_players = cursor.fetchone()[0]

        # Active players (seen in last 7 days)
        cursor.execute("SELECT COUNT(*) FROM players WHERE last_seen > ?", (cutoff,))
        active_players = cursor.fetchone()[0]

        # Total servers
        cursor.execute("SELECT COUNT(*) FROM servers")
        total_servers = cursor.fetchone()[0]

        # Command usage
        cursor.execute('''
            SELECT command, COUNT(*) as count
            FROM command_usage
            WHERE used_at > ?
            GROUP BY command
            ORDER BY count DESC
        ''', (cutoff,))
        command_stats = {row[0]: row[1] for row in cursor.fetchall()}

        # Top players by level
        cursor.execute('''
            SELECT name, level, rank FROM players
            ORDER BY level DESC LIMIT 10
        ''')
        top_players = [{"name": r[0], "level": r[1], "rank": r[2]} for r in cursor.fetchall()]

        return {
            "total_players": total_players,
            "active_players": active_players,
            "total_servers": total_servers,
            "command_stats": command_stats,
            "top_players": top_players
        }

    def get_shop_items(self, available_only: bool = True) -> List[sqlite3.Row]:
        """Get shop items"""
        cursor = self.conn.cursor()
        if available_only:
            cursor.execute("SELECT * FROM shop_items WHERE available = 1")
        else:
            cursor.execute("SELECT * FROM shop_items")
        return cursor.fetchall()

    def add_shop_item(self, name: str, price: int, item_type: str, stats_bonus: str, description: str):
        """Add new shop item"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO shop_items (name, price, type, stats_bonus, description, available)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', (name, price, item_type, stats_bonus, description))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        self.conn.close()
