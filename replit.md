# Cha Hae-In Discord Bot v2.0

## Overview
**MAJOR UPGRADE COMPLETE!** This is a Solo Leveling themed Discord bot featuring Cha Hae-In AI character, now with SQLite database, inventory system, shop, analytics, and much more!

**Version 2.0 Features:**
- ✅ SQLite database (reliable, no corruption)
- ✅ Comprehensive logging system
- ✅ Command cooldowns
- ✅ Inventory & Shop system
- ✅ Server & user analytics
- ✅ Owner broadcast command
- ✅ Database backup/restore
- ✅ Improved error handling
- ✅ Auto-migration from old JSON

---

## Project Type
Python Discord bot using discord.py with Groq AI integration

**Tech Stack:**
- discord.py 2.6.4
- Groq AI (LLaMA 3.3 70B)
- SQLite3 database
- python-dotenv for config

---

## Core Features

### 🤖 AI-Powered Personality
- Cha Hae-In (S-Rank Hunter from Solo Leveling)
- Tsundere personality using Groq LLM
- Context-aware with player stats
- Owner gets special treatment (creator mode)

### 📈 RPG Progression
- Levels: 1 → 999
- 8 ranks: E → D → C → B → A → S → National Level Hunter → Monarch
- 5 stats: STR, AGI, VIT, INT, SENSE
- EXP from chatting (3× in training channels)
- Automatic stat increases on level up

### ⚔️ Boss Battles
- Automatic spawns every 45-90 minutes
- Interactive button combat
- 4 skills: Fireball, Heal, Shadow Extract, Ruler's Authority
- Cooperative gold rewards
- Shadow extraction for Necromancers!

### 🏋️ Training
- `/pushup` - +15 STR (4h cooldown)
- `/squat` - +15 VIT (4h cooldown)
- `/run` - +15 AGI (6h cooldown)

### 💼 Job System
- **Hunter** (default)
- **Necromancer** (Lv80+): Shadow army, +300 mana
- **Monarch** (Lv80+): +50 to all stats, 70% more boss damage

### 🛍️ Economy & Inventory
- Shop with consumables and gear
- `/inventory` - View items
- `/shop` - Browse available items
- `/buy <item>` - Purchase
- `/use <item>` - Use consumables
- Health/Mana potions, elixirs, equipment

### 📊 Analytics (Owner Only)
- `/analytics` - Bot statistics
- Command usage tracking
- Server/user activity
- Top players leaderboard

### 🛠️ Admin Tools (Owner Only)
- `/givelevel` - Set user level
- `/giverank` - Set user rank
- `/givegold` - Give gold
- `/setclass` - Change class
- `/broadcast` - Message all servers
- `/backup` - Create database backup
- `/health` - Bot status check

---

## Setup

### Environment Variables
Required (in Replit Secrets or Railway):
```
TOKEN=your_discord_bot_token
OWNER_ID=your_discord_user_id
GROQ_API_KEY=your_groq_api_key  # Optional but recommended
```

### Installation
```bash
pip install -r requirements.txt
python main.py
```

---

## Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/register` | Create hunter profile |
| `/profile [member]` | View stats |
| `/daily` | Claim daily rewards |
| `/pushup` | Train STR (4h cd) |
| `/squat` | Train VIT (4h cd) |
| `/run` | Train AGI (6h cd) |
| `/jobchange` | Switch class (Lv80+) |
| `/inventory` | View items |
| `/shop` | Browse shop |
| `/buy <item>` | Purchase item |
| `/use <item>` | Use item |
| `/system` | Interactive guide |
| `/health` | Bot status |

### Owner-Only Commands
| Command | Description |
|---------|-------------|
| `/givelevel` | Set user level |
| `/giverank` | Set user rank |
| `/givegold` | Grant gold |
| `/setclass` | Change class |
| `/analytics` | View stats |
| `/broadcast` | Send to all servers |
| `/backup` | Database backup |

---

## Database (SQLite)

### Tables:
- **players** - User profiles, stats, inventory
- **servers** - Guild tracking
- **command_usage** - Analytics
- **shop_items** - Shop inventory
- **equipment** - Equipment management

Auto-migrates from old `db.json` on first run!

---

## How to Talk to Cha Hae-In

The bot responds when:
- You @mention her
- You say "hae-in", "haein", or "cha hae"
- You reply to her messages
- Sometimes to greetings (hey, hi, hello, etc.) - 40% chance

Last 20 messages per channel remembered for context!

---

## Deploy 24/7 for FREE

### Railway (Recommended)
1. Fork this repo
2. Go to [railway.app](https://railway.app)
3. New Project → Deploy from GitHub
4. Add environment variables
5. Done! Free $5/month credit = always-on

### Replit
- Use the built-in workflow
- Add UptimeRobot to ping every 5 minutes
- Warning: Still sleeps on free tier

---

## Recent Changes (v2.0)

- **Database Upgrade**: Switched from JSON to SQLite
- **Logging System**: File + console with rotation
- **Command Cooldowns**: Prevents spam
- **Inventory System**: Full item management
- **Shop**: Buy/sell items with gold
- **Analytics**: Track bot usage
- **Broadcast**: Owner can message all servers
- **Backup**: Easy database backups
- **Error Handling**: Better resilience
- **Code Refactor**: Cleaner, modular structure

---

## File Structure
```
Cha-Hae-In/
├── main.py           # Main bot (v2.0 - 500+ lines)
├── database.py       # SQLite database layer
├── config.py         # Configuration
├── logger.py         # Logging setup
├── requirements.txt  # Dependencies
├── railway.json      # Railway config
├── .env.example      # Env template
├── data.db           # Database (auto-created)
├── logs/             # Log files
└── README.md         # Full docs
```

---

## Support

Issues? Check:
1. Bot token is correct
2. Bot has proper permissions
3. GROQ_API_KEY set (optional)
4. Database file is writable

---

**v2.0 - Upgraded & Improved! 🚀**
