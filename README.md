# 🤖 Cha Hae-In Discord Bot v2.0

A Solo Leveling themed Discord bot featuring Cha Hae-In AI character, RPG progression, boss battles, and more!

---

## ✨ Features

### 🎭 AI Character (Cha Hae-In)
- **Tsundere personality** with Groq AI (LLaMA 3.3 70B)
- Context-aware responses using your player stats
- Special treatment for the bot owner (creator mode)
- Responds to mentions, keywords, and greetings

### 📈 RPG System
- Leveling from 1 → 999
- 8 ranks: E → D → C → B → A → S → National Level Hunter → **Monarch**
- 5 stats: STR, AGI, VIT, INT, SENSE
- Gain EXP from chatting (3× in #training-ground channels)
- Automatic stat increases on level up

### ⚔️ Boss Battles
- Random boss spawns every 45-90 minutes
- Click-to-fight with interactive buttons
- Skills system (Fireball, Heal, Shadow Extract, Ruler's Authority)
- All participants get gold rewards
- Necromancers can extract shadows!

### 🏋️ Training
- `/pushup` - +15 STR (4h cooldown)
- `/squat` - +15 VIT (4h cooldown)
- `/run` - +15 AGI (6h cooldown)
- Fast-track your stats

### 💼 Job System
- Base class: **Hunter**
- **Necromancer** (Lv 80+): Shadow extraction + mana boost
- **Monarch** (Lv 80+): Massive stat boost + damage bonus

### 🛍️ Inventory & Shop
- Buy items with gold
- Consumables: Health/Mana Potions, Elixirs
- Equipment: Weapons, accessories (coming soon)
- `/inventory`, `/shop`, `/buy`, `/use`

### 📊 Analytics & Admin
Owner-only commands:
- `/givelevel` - Set any user's level
- `/giverank` - Give any rank
- `/givegold` - Give gold
- `/setclass` - Change user's class
- `/analytics` - View bot statistics
- `/broadcast` - Send announcement to all servers
- `/backup` - Create database backup

---

## 🚀 Quick Deploy (Railway)

1. **Fork this repo** to your GitHub
2. **Go to [Railway.app](https://railway.app)** and sign in
3. Click **New Project** → **Deploy from GitHub**
4. Select your forked repo
5. **Add Environment Variables:**

| Variable | Description |
|----------|-------------|
| `TOKEN` | Your Discord bot token |
| `OWNER_ID` | Your Discord user ID (as number) |
| `GROQ_API_KEY` | (Optional) AI responses - get from [console.groq.com](https://console.groq.com) |

6. Deploy! Bot runs 24/7 free

---

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Discord bot token ([Create here](https://discord.com/developers/applications))

### Setup
```bash
# Clone repo
git clone https://github.com/yourusername/Cha-Hae-In.git
cd Cha-Hae-In

# Install dependencies
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env
# Edit .env and add your tokens

# Run the bot
python main.py
```

---

## 📁 Project Structure

```
Cha-Hae-In/
├── main.py           # Main bot file (v2.0)
├── database.py       # SQLite database layer
├── config.py         # Configuration management
├── logger.py         # Logging system
├── requirements.txt  # Python dependencies
├── railway.json      # Railway deployment config
├── data.db           # SQLite database (auto-created)
├── logs/             # Log files directory
├── .env.example      # Environment variables template
└── README.md         # This file
```

---

## 🗄️ Database (SQLite)

The bot uses SQLite for reliable data storage:

### Tables:
- `players` - User profiles, stats, inventory
- `servers` - Guild tracking
- `command_usage` - Analytics logging
- `shop_items` - Shop inventory
- `equipment` - User equipment

Auto-migration from old JSON format on first run.

---

## 📋 Commands

### User Commands
| Command | Description |
|---------|-------------|
| `/register` | Create your Hunter profile |
| `/profile` | View your stats (or another user's) |
| `/daily` | Claim daily gold and mana |
| `/system` | Open interactive guide |
| `/pushup` | Train strength (4h cd) |
| `/squat` | Train vitality (4h cd) |
| `/run` | Train agility (6h cd) |
| `/jobchange` | Switch to Necromancer/Monarch (Lv80+) |
| `/inventory` | View your items |
| `/shop` | Browse shop |
| `/buy <item>` | Purchase an item |
| `/use <item>` | Use an item from inventory |
| `/health` | Check bot status |

### Owner-Only
| Command | Description |
|---------|-------------|
| `/givelevel` | Set user level |
| `/giverank` | Set user rank |
| `/givegold` | Give gold |
| `/setclass` | Change class |
| `/analytics` | View statistics |
| `/broadcast` | Message all servers |
| `/backup` | Database backup |

---

## 🔧 Configuration

Environment variables (`.env`):

```bash
TOKEN=discord_bot_token
OWNER_ID=your_user_id
GROQ_API_KEY=optional_ai_key
DATABASE_PATH=data.db  # optional
LOG_LEVEL=INFO        # DEBUG, INFO, WARNING, ERROR
DEBUG=false
```

---

## 📊 Features List

- ✅ 24/7 free hosting (Railway)
- ✅ SQLite database (no JSON corruption)
- ✅ Comprehensive logging
- ✅ Command cooldowns
- ✅ Server analytics
- ✅ Inventory & shop
- ✅ Equipment system
- ✅ Backup/restore commands
- ✅ Graceful error handling
- ✅ Auto-migration from JSON
- ✅ Active server tracking
- ✅ Passive offline EXP
- ✅ Boss battle system
- ✅ AI-powered responses
- ✅ Owner god mode

---

## 🎮 Game Mechanics

### Leveling Curve
EXP required for next level scales by **1.45×** each level.

### Ranks Unlocked
| Level | Rank |
|-------|------|
| 1-59 | E |
| 60-119 | D |
| 120-179 | C |
| 180-239 | B |
| 240-299 | A |
| 300-359 | S |
| 360-419 | National Level Hunter |
| 420+ | **Monarch** |

### Stat Gains per Level
- Random +4 to +9 in all stats
- +40 Max HP
- +25 Max Mana
- Every 50 levels: +10,000 gold bonus

---

## 🤝 Contributing

Pull requests welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Test your changes
4. Submit a PR

---

## 📝 License

MIT License - feel free to use and modify

---

## 🙏 Credits

- **Anthropic** - Claude (helped build this)
- **Groq** - Fast AI inference
- **discord.py** - Discord API wrapper
- **Solo Leveling** - Inspiration

---

**Made with ❤️ for the Solo Leveling community**
