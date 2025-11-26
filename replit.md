# Cha Hae-In Discord Bot

## Overview
This is a Discord bot based on the "Solo Leveling" anime/manga series, featuring Cha Hae-In as the bot personality. The bot includes an RPG leveling system where users can level up, train, fight bosses, and interact with the bot using AI-powered conversations that stay true to Cha Hae-In's tsundere character.

## Project Type
Python Discord bot using discord.py library with Groq AI integration

## Core Features
- **AI-Powered Personality**: Uses Groq LLM (Llama 3.3 70B) for natural, in-character responses
- **Leveling System**: Users gain EXP from chatting (3x in training channels)
- **Smart Response Detection**: Bot responds to mentions, name triggers, replies, and sometimes joins conversations naturally
- **Training Commands**: /pushup, /squat, /run (with cooldowns)
- **Boss Battles**: Automatic boss spawns with button-based combat
- **Job System**: Change to Necromancer or Monarch at level 80+
- **Daily Rewards**: Gold and mana restoration
- **Owner Admin Commands**: Give levels, ranks, gold, change classes

## Setup
The bot is configured and running with:
- Python 3.11
- discord.py 2.6.4
- groq (Llama 3.3 70B model - FREE)
- PyYAML 6.0.2

## Environment Variables
Required secrets (already configured):
- `TOKEN`: Discord bot token from Discord Developer Portal
- `OWNER_ID`: Discord user ID for admin commands
- `GROQ_API_KEY`: Free API key from https://console.groq.com

## How to Use
1. The bot is automatically running via the "Discord Bot" workflow
2. Invite your bot to a Discord server using the OAuth2 URL from Discord Developer Portal
3. Users can start with `/register` to begin their hunter journey
4. Use `/system` to view the complete guide

## How to Talk to Cha Hae-In
The bot will respond when:
- You @mention her
- You say "hae-in", "haein", or "cha hae" in your message
- You reply to one of her messages
- Sometimes randomly when you use conversational phrases (30% chance)

She remembers the last 20 messages per channel for context!

## Commands
- `/register` - Awaken as a Hunter
- `/profile [member]` - View player stats
- `/daily` - Claim daily rewards
- `/pushup` - Training: +15 Strength (4h cooldown)
- `/squat` - Training: +15 Vitality (4h cooldown)
- `/run` - Training: +15 Agility (6h cooldown)
- `/jobchange` - Change class at level 80+
- `/system` - Interactive guide

### Owner-Only Commands
- `/givelevel` - Set someone's level (1-999)
- `/giverank` - Give any rank (E/D/C/B/A/S/National/Monarch)
- `/givegold` - Give gold to users
- `/setclass` - Force change someone's class

## Recent Changes
- 2025-11-26: Improved AI responses
  - Shorter, more direct responses (1-2 sentences max)
  - No more roleplay actions (*blushes*, *looks away*, etc)
  - Bot can now read real player data (ranks, levels, class)
  - Owner recognition - shows love/respect to the creator
- 2025-11-26: Added AI-powered responses using Groq (FREE)
  - Integrated Llama 3.3 70B model for natural conversation
  - Added detailed Cha Hae-In character prompt
  - Implemented conversation memory per channel
  - Smart detection for when to respond (mentions, name triggers, replies)
  - Non-blocking AI calls using asyncio.to_thread
- 2025-11-25: Imported from GitHub and configured for Replit
  - Removed duplicate code definitions (Player class, event handlers)
  - Configured Python 3.11 environment
  - Set up Discord Bot workflow
  - Added .gitignore for Python project

## Project Architecture
- `main.py` - Main bot file with all functionality and AI integration
- `db.json` - Player data storage (auto-generated)
- `requirements.txt` - Python dependencies

## AI Personality Details
Cha Hae-In's character traits implemented in the AI:
- Tsundere personality: Cold exterior, secretly caring
- S-Rank Hunter confidence mixed with romantic shyness
- Uses phrases like "...Baka", "Hmph", "Don't get the wrong idea"
- Gets flustered when complimented
- Short, punchy responses (1-3 sentences)
- Can smell mana - most hunters smell bad to her except Sung Jin-Woo
