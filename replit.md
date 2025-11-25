# Cha Hae-In Discord Bot

## Overview
This is a Discord bot based on the "Solo Leveling" anime/manga series, featuring Cha Hae-In as the bot personality. The bot includes an RPG leveling system where users can level up, train, fight bosses, and interact with the bot as if they're communicating with Cha Hae-In herself.

## Project Type
Python Discord bot using discord.py library

## Core Features
- **Leveling System**: Users gain EXP from chatting (3x in training channels)
- **Cha Hae-In Personality**: Bot responds in character when mentioned or when "hae-in" is mentioned
- **Training Commands**: /pushup, /squat, /run (with cooldowns)
- **Boss Battles**: Automatic boss spawns with button-based combat
- **Job System**: Change to Necromancer or Monarch at level 80+
- **Daily Rewards**: Gold and mana restoration
- **Owner Admin Commands**: Give levels, ranks, gold, change classes

## Setup
The bot is configured and running with:
- Python 3.11
- discord.py 2.6.4
- PyYAML 6.0.2

## Environment Variables
Required secrets (already configured):
- `TOKEN`: Discord bot token from Discord Developer Portal
- `OWNER_ID`: Discord user ID for admin commands

## How to Use
1. The bot is automatically running via the "Discord Bot" workflow
2. Invite your bot to a Discord server using the OAuth2 URL from Discord Developer Portal
3. Users can start with `/register` to begin their hunter journey
4. Use `/system` to view the complete guide

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
- 2025-11-25: Imported from GitHub and configured for Replit
  - Removed duplicate code definitions (Player class, event handlers)
  - Configured Python 3.11 environment
  - Set up Discord Bot workflow
  - Added .gitignore for Python project

## Project Architecture
- `main.py` - Main bot file with all functionality
- `db.json` - Player data storage (auto-generated)
- `requirements.txt` - Python dependencies

## Chat Personality
The bot responds to mentions with Cha Hae-In's tsundere personality:
- Greetings: "Hey.", "Finally.", "You're late."
- Love/compliments: "...Idiot.", "*blushes* Shut up!"
- Cute comments: "W-What?!", "Say that again and die."
- 10% chance to add "...Baka." to any response
