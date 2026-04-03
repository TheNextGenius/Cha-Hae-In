# ==================== CONFIGURATION ====================
import os
from dotenv import load_dotenv

load_dotenv()

# Discord
TOKEN = os.getenv('TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID', 0))

# AI
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Database
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data.db')

# Bot Settings
BOT_PREFIX = os.getenv('BOT_PREFIX', '/')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
