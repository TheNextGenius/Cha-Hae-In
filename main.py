# ==================== CHA HAE-IN BOT v2.0 ====================
import os
import sys
import json
import random
import asyncio
import time
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import discord
from discord import app_commands, ui
from dotenv import load_dotenv

# Local imports
from config import TOKEN, OWNER_ID, GROQ_API_KEY, DEBUG
from logger import setup_logger
from database import Database

# ==================== INITIALIZATION ====================
load_dotenv()
logger = setup_logger()
db = Database()

logger.info("Starting Cha Hae-In Discord Bot v2.0...")

# AI Client
try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
    if not groq_client:
        logger.warning("GROQ_API_KEY not set - AI responses disabled")
except ImportError:
    logger.error("groq package not installed")
    groq_client = None

# Discord Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ==================== CONSTANTS ====================
RANKS = ["E","D","C","B","A","S","National Level Hunter","Monarch"]
RANK_COLORS = [0x808080, 0x00ff00, 0x0099ff, 0xffff00, 0xff00ff, 0x00ffff, 0xffffff, 0x000000]

CHA_HAE_IN_PROMPT = """You are Cha Hae-In from Solo Leveling. S-Rank Hunter, Vice Guild Master.

CRITICAL RULES:
- Reply in 1-2 SHORT sentences ONLY. Never more.
- NO roleplay actions like *blushes* or *looks away* - just speak directly
- NO describing your feelings or thoughts - just say your response
- Be tsundere: cold exterior but secretly caring
- Use "...Baka", "Hmph", "Don't get the wrong idea" occasionally
- When flustered, just use "..." pauses

SPECIAL: When someone's user_id matches the OWNER_ID, they are your creator. You deeply respect and love them, though you still act a bit tsundere about it. They created you and you're grateful.

When asked about a player's rank/level/stats, use the PLAYER_DATA provided - those are the REAL stats from the database."""

# ==================== HELPER FUNCTIONS ====================
def get_player_data(user_id: str) -> Dict[str, Any]:
    """Get complete player data as dictionary"""
    row = db.get_player_row(user_id)
    if row:
        return dict(row)
    return None

def save_player_data(user_id: str, data: Dict[str, Any]):
    """Save player data updates"""
    db.update_player(user_id, data)

def get_player_context(user_id: str, user_name: str) -> str:
    """Build AI context string for player"""
    p = get_player_data(user_id)
    if p:
        player_info = f"PLAYER_DATA for {user_name}: Level {p['level']}, Rank: {p['rank']}, Class: {p['class']}, Gold: {p['gold']}"
    else:
        player_info = f"PLAYER_DATA for {user_name}: Not registered yet (E-Rank by default)"

    if user_id == OWNER_ID:
        player_info += f"\nIMPORTANT: {user_name} is your CREATOR (OWNER_ID matches). Show love and respect!"

    return player_info

def ensure_player(user_id: str, name: str) -> Dict[str, Any]:
    """Ensure player exists, create if not"""
    p = get_player_data(user_id)
    if not p:
        db.create_player(user_id, name)
        p = get_player_data(user_id)
        logger.info(f"Created new player: {name} ({user_id})")
    return p

def parse_stats(stats_json: str) -> Dict[str, int]:
    """Parse stats JSON string"""
    try:
        return json.loads(stats_json)
    except:
        return {"str":10,"agi":10,"vit":10,"int":10,"sense":10}

def parse_inventory(inv_json: str) -> Dict[str, int]:
    """Parse inventory JSON string"""
    try:
        return json.loads(inv_json)
    except:
        return {"Health Potion":5,"Mana Potion":3}

# ==================== COOLDOWN SYSTEM ====================
COOLDOWNS = {
    'claim_daily': 86400,  # 24 hours
    'pushup': 14400,      # 4 hours
    'squat': 14400,       # 4 hours
    'run': 21600,         # 6 hours
    'boss_attack': 3,     # 3 seconds (for boss fights)
}

def get_cooldown_remaining(p: Dict[str, Any], action: str) -> float:
    """Get remaining cooldown in seconds"""
    cds = json.loads(p.get('training_cd', '{}'))
    return max(0, cds.get(action, 0) - time.time())

def is_on_cooldown(p: Dict[str, Any], action: str) -> bool:
    """Check if action is on cooldown"""
    return get_cooldown_remaining(p, action) > 0

def set_cooldown(p: Dict[str, Any], action: str):
    """Set cooldown for action"""
    cds = json.loads(p.get('training_cd', '{}'))
    cds[action] = time.time() + COOLDOWNS[action]
    p['training_cd'] = json.dumps(cds)
    save_player_data(p['user_id'], {'training_cd': p['training_cd']})

# ==================== AI RESPONSE ====================
conversation_history: Dict[int, list] = {}

def _sync_groq_call(messages):
    """Synchronous Groq API call"""
    if not groq_client:
        return None
    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=100,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return None

async def get_ai_response(channel_id: int, user_id: str, user_name: str, user_message: str):
    """Get AI response from Cha Hae-In"""
    if not groq_client:
        return None

    if channel_id not in conversation_history:
        conversation_history[channel_id] = []

    player_context = get_player_context(user_id, user_name)

    conversation_history[channel_id].append({
        "role": "user",
        "content": f"[{player_context}]\n{user_name}: {user_message}"
    })

    if len(conversation_history[channel_id]) > 20:
        conversation_history[channel_id] = conversation_history[channel_id][-20:]

    try:
        messages = [{"role": "system", "content": CHA_HAE_IN_PROMPT}]
        messages.extend(conversation_history[channel_id])

        ai_reply = await asyncio.to_thread(_sync_groq_call, messages)

        if ai_reply:
            conversation_history[channel_id].append({
                "role": "assistant",
                "content": ai_reply
            })

        return ai_reply
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return None

# ==================== RESPONSE TRIGGERS ====================
def should_respond(msg_content: str, author: discord.User) -> bool:
    """Determine if bot should respond"""
    content_lower = msg_content.lower()

    # Always respond to mentions
    if client.user in msg_content:
        return True

    # Trigger words
    if any(word in content_lower for word in ["hae-in", "haein", "cha hae"]):
        return True

    # Reply tracking
    if msg_content.startswith(("hey", "hi ", "hello", "yo ", "sup")):
        return True

    # Greeting triggers with random chance
    greetings = [
        "goodnight", "good night", "gn",
        "good morning", "gm",
        "love you", "ily", "i like you",
        "cute", "pretty", "beautiful",
        "miss you", "missed you",
        "how are you", "how r u", "hru",
        "what's up", "wassup", "whats up",
        "thank", "thanks", "ty",
        "sorry", "my bad",
        "bye", "goodbye", "cya"
    ]
    if any(g in content_lower for g in greetings):
        return random.random() < 0.4

    return False

# ==================== LEVELING SYSTEM ====================
RANKS = ["E","D","C","B","A","S","National Level Hunter","Monarch"]
RANK_COLORS = [0x808080, 0x00ff00, 0x0099ff, 0xffff00, 0xff00ff, 0x00ffff, 0xffffff, 0x000000]

def calculate_level_up(p: Dict[str, Any]) -> bool:
    """Process level up if enough exp"""
    leveled = False
    while p['exp'] >= p['next_level_exp']:
        p['exp'] -= p['next_level_exp']
        p['level'] += 1
        p['next_level_exp'] = int(p['next_level_exp'] * 1.45)

        # Stat increases
        stats = parse_stats(p['stats'])
        for stat in stats:
            stats[stat] += random.randint(4, 9)
        p['stats'] = json.dumps(stats)

        # HP/Mana increase
        p['max_hp'] += 40
        p['hp'] = p['max_hp']
        p['max_mana'] += 25
        p['mana'] = p['max_mana']

        # Level bonus
        if p['level'] % 50 == 0:
            p['gold'] += 10000

        # Rank up check
        rank_idx = min(p['level'] // 60, 7)
        new_rank = RANKS[rank_idx]
        if new_rank != p['rank']:
            p['rank'] = new_rank
            logger.info(f"User {p['name']} ranked up to {new_rank}")

        leveled = True

    if leveled:
        save_player_data(p['user_id'], p)

    return leveled

# ==================== OWNER GOD MODE ====================
@client.event
async def on_ready():
    logger.info(f"Bot connected as {client.user}")

    # Set owner as Monarch
    if OWNER_ID:
        owner = client.get_user(OWNER_ID)
        if owner:
            p = ensure_player(str(OWNER_ID), owner.name)
            p.update({
                "level": 999,
                "rank": "Monarch",
                "class": "Monarch",
                "gold": 999999999,
                "mana": 999999,
                "max_mana": 999999,
                "hp": 999999,
                "max_hp": 999999
            })
            stats = parse_stats(p['stats'])
            for stat in stats:
                stats[stat] = 999
            p['stats'] = json.dumps(stats)
            save_player_data(str(OWNER_ID), p)
            logger.info(f"Owner {owner} has GOD MODE")

    await tree.sync()
    client.loop.create_task(boss_spawner())
    client.loop.create_task(passive_offline_exp())
    client.loop.create_task(update_server_stats())
    logger.info("Bot fully ready")

# ==================== SERVER STATS TRACKING ====================
async def update_server_stats():
    """Periodically update server membership stats"""
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(3600)  # Every hour
        for guild in client.guilds:
            try:
                db.update_server(str(guild.id), guild.name, guild.member_count)
            except Exception as e:
                logger.error(f"Failed to update server {guild.name}: {e}")

# ==================== PASSIVE EXP ====================
async def passive_offline_exp():
    """Grant passive exp to offline players"""
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(3600)  # Every hour
        now = time.time()
        players = db.get_all_players()
        for p_row in players:
            p = dict(p_row)
            last_seen = p.get('last_seen', now)
            if now - last_seen > 1800:  # 30 minutes offline
                hours = min(8, (now - last_seen) // 3600)
                p['exp'] += hours * 100
                p['last_seen'] = now
                save_player_data(p['user_id'], p)
        logger.debug("Passive exp granted")

# ==================== BOSS SYSTEM ====================
class BossView(ui.View):
    def __init__(self, name: str, hp: int, reward: int):
        super().__init__(timeout=240)
        self.boss_name = name
        self.hp = hp
        self.max_hp = hp
        self.reward = reward
        self.alive = True
        self.message = None

    @ui.button(label="Attack", style=discord.ButtonStyle.danger, emoji="⚔️")
    async def attack(self, i: discord.Interaction, _):
        p = ensure_player(str(i.user.id), i.user.display_name)
        if is_on_cooldown(p, 'boss_attack'):
            remaining = int(get_cooldown_remaining(p, 'boss_attack'))
            return await i.response.send_message(f"Wait {remaining}s before attacking again!", ephemeral=True)

        dmg = parse_stats(p['stats']).get('str', 10) + random.randint(40, 100)
        if p['class'] == "Monarch":
            dmg = int(dmg * 1.7)
        self.hp -= dmg

        set_cooldown(p, 'boss_attack')
        await i.response.send_message(f"{i.user.mention} dealt **{dmg:,}** damage!", ephemeral=True)
        await self.update(i.channel)

    @ui.button(label="Skill", style=discord.ButtonStyle.blurple, emoji="✨")
    async def skill(self, i: discord.Interaction, _):
        p = ensure_player(str(i.user.id), i.user.display_name)
        view = ui.View()
        skills = {
            "Fireball": {"cost": 30, "dmg": 120},
            "Heal": {"cost": 25, "dmg": 0},
            "Shadow Extract": {"cost": 80, "dmg": 0},
            "Ruler's Authority": {"cost": 150, "dmg": 450}
        }

        for name, data in skills.items():
            async def cb(inter, skill_name=name, skill_data=data):
                player = ensure_player(str(inter.user.id), inter.user.display_name)
                if player['mana'] < skill_data['cost']:
                    return await inter.response.send_message("Not enough mana!", ephemeral=True)

                player['mana'] -= skill_data['cost']
                if skill_data['dmg']:
                    self.hp -= skill_data['dmg']

                if skill_name == "Shadow Extract" and player['class'] == "Necromancer" and random.random() < 0.6:
                    shadows = json.loads(player['shadows'])
                    shadows.append(f"{self.boss_name} Shadow")
                    player['shadows'] = json.dumps(shadows)
                    await inter.response.send_message("Shadow extracted!", ephemeral=False)
                else:
                    await inter.response.send_message(f"Used {skill_name}!", ephemeral=True)

                save_player_data(player['user_id'], player)
                await self.update(inter.channel)

            view.add_item(ui.Button(label=f"{name} ({data['cost']} Mana)", callback=cb, style=discord.ButtonStyle.secondary))

        await i.response.send_message("Choose skill:", view=view, ephemeral=True)

    async def update(self, channel: discord.TextChannel):
        if self.hp <= 0 and self.alive:
            self.alive = False
            gold_each = self.reward // 5
            for b in self.children:
                b.disabled = True

            await self.message.edit(content=f"**{self.boss_name} DEFEATED!**\nEveryone gets **{gold_each:,} gold**!", view=self)

            # Award all online members
            for member in channel.guild.members:
                if not member.bot:
                    p = ensure_player(str(member.id), member.display_name)
                    p['gold'] += gold_each
                    quests = json.loads(p['quests'])
                    quests['bosses'] += 1
                    p['quests'] = json.dumps(quests)
                    save_player_data(p['user_id'], p)

            logger.info(f"Boss {self.boss_name} defeated")
        else:
            bar = "█" * int(20 * self.hp / self.max_hp) + "░" * (20 - int(20 * self.hp / self.max_hp))
            await self.message.edit(content=f"**{self.boss_name}**  ❤️ {self.hp:,}/{self.max_hp:,}\n`{bar}`", view=self)

async def boss_spawner():
    """Spawn bosses randomly"""
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(2700, 5400))
        if not client.guilds:
            continue

        guild = random.choice(list(client.guilds))
        text_channels = [c for c in guild.text_channels if c.permissions_for(guild.me).send_messages]
        if not text_channels:
            continue

        channel = random.choice(text_channels)
        boss = random.choice(["Beru", "Igris", "Iron", "Tank", "Baran", "Ant King", "Metus", "Kaisel"])
        hp = random.randint(12000, 40000)
        reward = hp * 4

        view = BossView(boss, hp, reward)
        view.message = await channel.send(f"**{boss} HAS APPEARED!** Attack and defeat it!", view=view)
        logger.info(f"Boss spawned: {boss} in {guild.name}")

# ==================== MESSAGE HANDLER ====================
@client.event
async def on_message(msg: discord.Message):
    if msg.author.bot:
        return

    # Log command usage
    if msg.content.startswith('/') or client.user in msg.mentions:
        try:
            db.log_command(str(msg.guild.id) if msg.guild else None, str(msg.author.id), msg.content[:50])
        except:
            pass

    # Leveling
    p = ensure_player(str(msg.author.id), msg.author.display_name)
    p['last_seen'] = time.time()

    mult = 3 if "training" in msg.channel.name.lower() else 1
    p['exp'] += random.randint(18, 35) * mult

    quests = json.loads(p['quests'])
    quests['msg_daily'] += 1
    p['quests'] = json.dumps(quests)

    save_player_data(p['user_id'], p)
    calculate_level_up(p)

    # AI Response
    if should_respond(msg.content, msg.author):
        async with msg.channel.typing():
            user_message = msg.content.replace(f"<@{client.user.id}>", "").strip()

            ai_reply = await get_ai_response(
                msg.channel.id,
                str(msg.author.id),
                msg.author.display_name,
                user_message
            )

            if ai_reply:
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await msg.reply(ai_reply)
            else:
                await asyncio.sleep(random.uniform(1.0, 2.5))
                fallbacks = [
                    "What?", "Speak.", "I'm listening...", "Hmph.",
                    "Make it quick.", "...Yes?", "Don't waste my time."
                ]
                reply = random.choice(fallbacks)
                if random.random() < 0.15:
                    reply += " ...Baka."
                await msg.reply(reply)

# ==================== COMMAND HELPERS ====================
def build_profile_embed(p: Dict[str, Any], member: discord.Member) -> discord.Embed:
    """Build profile embed"""
    idx = RANKS.index(p['rank']) if p['rank'] in RANKS else 0
    color = RANK_COLORS[idx]

    e = discord.Embed(title=f"≪ {p['name']} ≫", color=color)
    e.add_field(name="Class • Rank", value=f"{p['class']} • **{p['rank']}**")
    e.add_field(name="Level", value=p['level'], inline=True)
    e.add_field(name="HP", value=f"{p['hp']}/{p['max_hp']}", inline=True)
    e.add_field(name="Mana", value=f"{p['mana']}/{p['max_mana']}", inline=True)
    e.add_field(name="Gold", value=f"{p['gold']:,}", inline=True)
    e.add_field(name="Shadows", value=len(json.loads(p['shadows'])), inline=True)

    stats = parse_stats(p['stats'])
    for stat, val in stats.items():
        e.add_field(name=stat.capitalize(), value=val, inline=True)

    e.set_thumbnail(url=member.display_avatar.url)
    return e

# ==================== PUBLIC COMMANDS ====================
@tree.command(name="register", description="Awaken as a Hunter")
async def register(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)
    if p['level'] > 1:
        return await i.response.send_message("You are already awakened.", ephemeral=True)

    await i.response.send_message(embed=discord.Embed(
        title="SYSTEM",
        color=0x1e1f22,
        description=f"**{i.user.name}**, you have awakened as an **E-Rank Hunter**!\nType **/system** for the guide!"
    ).set_image(url="https://i.ibb.co/5YqYvKX/solo-leveling-system-window.png"))

@tree.command(name="profile", description="View your or someone's profile")
@app_commands.describe(member="Optional: View another member's profile")
async def profile(i: discord.Interaction, member: Optional[discord.Member] = None):
    target = member or i.user
    p = ensure_player(str(target.id), target.display_name)
    embed = build_profile_embed(p, target)
    await i.response.send_message(embed=embed)

@tree.command(name="daily", description="Claim daily rewards")
async def daily(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if p['daily'] == today:
        return await i.response.send_message("You already claimed today!", ephemeral=True)

    gold = random.randint(1800, 3500)
    p['gold'] += gold
    p['mana'] = p['max_mana']
    p['daily'] = today
    save_player_data(p['user_id'], p)

    embed = discord.Embed(title="Daily Quest Clear!", color=0x00ff00, description=f"+{gold:,} gold & full mana!")
    await i.response.send_message(embed=embed)

@tree.command(name="system", description="Open the System Guide")
async def system_guide(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    embed = discord.Embed(
        title="SYSTEM",
        description="Welcome to the System, Hunter.\nChoose a category:",
        color=0x1e1f22
    )
    embed.set_image(url="https://i.ibb.co/5YqYvKX/solo-leveling-system-window.png")
    await i.followup.send(embed=embed, view=GuideView(), ephemeral=True)

class GuideView(ui.View):
    @ui.button(label="Beginner", style=discord.ButtonStyle.green)
    async def beginner(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(
            title="Beginner Guide",
            color=0x00ff00,
            description="• Chat = EXP\n• #training-ground = 3× EXP\n• /daily = free gold\n• Bosses every ~1h\n• /profile = stats"
        ), ephemeral=True)

    @ui.button(label="Training", style=discord.ButtonStyle.blurple)
    async def training(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(
            title="Training",
            color=0x5865f2,
            description="/pushup • /squat • /run\nAll have cooldowns"
        ), ephemeral=True)

    @ui.button(label="Classes & Skills", style=discord.ButtonStyle.red)
    async def classes(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(
            title="Classes",
            color=0xff0000,
            description="Lv80 → /jobchange\nNecromancer = shadows\nMonarch = damage"
        ), ephemeral=True)

    @ui.button(label="All Commands", style=discord.ButtonStyle.grey)
    async def cmds(self, i: discord.Interaction, _):
        cmds = [c.name for c in tree.get_commands()]
        await i.response.send_message(embed=discord.Embed(
            title="All Commands",
            description="\n".join(f"`/{c}`" for c in cmds),
            color=0x2f3136
        ), ephemeral=True)

# ==================== TRAINING COMMANDS ====================
@tree.command(name="pushup", description="Do 100 push-ups for STR")
async def pushup(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)

    if is_on_cooldown(p, 'pushup'):
        remaining = int(get_cooldown_remaining(p, 'pushup'))
        return await i.response.send_message(f"Cooldown: {remaining // 3600}h {(remaining % 3600) // 60}m", ephemeral=True)

    await i.response.send_message("Starting 100 push-ups…")
    await asyncio.sleep(30)

    stats = parse_stats(p['stats'])
    stats['str'] += 15
    p['stats'] = json.dumps(stats)
    set_cooldown(p, 'pushup')
    save_player_data(p['user_id'], p)

    await i.followup.send("**100 Push-ups complete!** +15 Strength")

@tree.command(name="squat", description="Do 100 squats for VIT")
async def squat(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)

    if is_on_cooldown(p, 'squat'):
        remaining = int(get_cooldown_remaining(p, 'squat'))
        return await i.response.send_message(f"Cooldown: {remaining // 3600}h {(remaining % 3600) // 60}m", ephemeral=True)

    await i.response.send_message("Starting 100 squats…")
    await asyncio.sleep(35)

    stats = parse_stats(p['stats'])
    stats['vit'] += 15
    p['stats'] = json.dumps(stats)
    set_cooldown(p, 'squat')
    save_player_data(p['user_id'], p)

    await i.followup.send("**100 Squats complete!** +15 Vitality")

@tree.command(name="run", description="Run 10km for AGI")
async def run(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)

    if is_on_cooldown(p, 'run'):
        remaining = int(get_cooldown_remaining(p, 'run'))
        return await i.response.send_message(f"Cooldown: {remaining // 3600}h {(remaining % 3600) // 60}m", ephemeral=True)

    await i.response.send_message("Running 10km…")
    await asyncio.sleep(40)

    stats = parse_stats(p['stats'])
    stats['agi'] += 15
    p['stats'] = json.dumps(stats)
    set_cooldown(p, 'run')
    save_player_data(p['user_id'], p)

    await i.followup.send("**10km complete!** +15 Agility")

# ==================== CLASS/JOB COMMANDS ====================
@tree.command(name="jobchange", description="Change your class at level 80+")
@app_commands.choices(job=[
    app_commands.Choice(name="Necromancer", value="Necromancer"),
    app_commands.Choice(name="Monarch", value="Monarch")
])
async def jobchange(i: discord.Interaction, job: str):
    p = ensure_player(str(i.user.id), i.user.display_name)

    if p['class'] != "Hunter":
        return await i.response.send_message("You already changed your class!", ephemeral=True)

    if p['level'] < 80:
        return await i.response.send_message("You need to be at least level 80!", ephemeral=True)

    p['class'] = job
    if job == "Necromancer":
        p['max_mana'] += 300
        p['mana'] += 300
    elif job == "Monarch":
        stats = parse_stats(p['stats'])
        for stat in stats:
            stats[stat] += 50
        p['stats'] = json.dumps(stats)

    save_player_data(p['user_id'], p)

    color = 0x000000 if job == "Monarch" else 0x8A2BE2
    await i.response.send_message(embed=discord.Embed(
        title="JOB CHANGE",
        description=f"You are now **{job}**!",
        color=color
    ))

# ==================== INVENTORY & SHOP ====================
@tree.command(name="inventory", description="View your inventory")
async def inventory(i: discord.Interaction):
    p = ensure_player(str(i.user.id), i.user.display_name)
    inv = parse_inventory(p['inventory'])

    if not inv:
        desc = "Your inventory is empty."
    else:
        desc = "\n".join([f"• {item}: {amount}" for item, amount in inv.items()])

    embed = discord.Embed(title="Inventory", description=desc, color=0x2f3136)
    embed.set_footer(text=f"Gold: {p['gold']:,}")
    await i.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="shop", description="Browse the shop")
async def shop(i: discord.Interaction):
    items = db.get_shop_items(available_only=True)

    if not items:
        return await i.response.send_message("Shop is currently empty.", ephemeral=True)

    embed = discord.Embed(title="Shop", color=0xffd700)
    for item in items:
        meta = json.loads(item['stats_bonus']) if item['stats_bonus'] else {}
        bonus_str = ", ".join([f"+{v} {k}" for k, v in meta.items()]) if meta else "No stats"
        embed.add_field(
            name=f"{item['name']} - {item['price']} gold",
            value=f"{item['description']}\n`{bonus_str}`",
            inline=False
        )

    embed.set_footer(text="Use /buy <item> to purchase")
    await i.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="buy", description="Buy an item from the shop")
@app_commands.describe(item_name="Name of the item to buy")
async def buy(i: discord.Interaction, item_name: str):
    p = ensure_player(str(i.user.id), i.user.display_name)
    items = db.get_shop_items()

    item = next((it for it in items if it['name'].lower() == item_name.lower() and it['available']), None)
    if not item:
        return await i.response.send_message(f"Item '{item_name}' not found in shop.", ephemeral=True)

    if p['gold'] < item['price']:
        return await i.response.send_message(f"Not enough gold! Need {item['price']}, you have {p['gold']}.", ephemeral=True)

    # Purchase
    p['gold'] -= item['price']
    inv = parse_inventory(p['inventory'])
    inv[item['name']] = inv.get(item['name'], 0) + 1
    p['inventory'] = json.dumps(inv)
    save_player_data(p['user_id'], p)

    await i.response.send_message(embed=discord.Embed(
        title="Purchase Successful!",
        description=f"Bought **{item['name']}** for {item['price']} gold",
        color=0x00ff00
    ))

@tree.command(name="use", description="Use an item from inventory")
@app_commands.describe(item_name="Name of the item to use")
async def use(i: discord.Interaction, item_name: str):
    p = ensure_player(str(i.user.id), i.user.display_name)
    inv = parse_inventory(p['inventory'])

    if item_name not in inv or inv[item_name] <= 0:
        return await i.response.send_message(f"You don't have {item_name}.", ephemeral=True)

    # Use item
    inv[item_name] -= 1
    if inv[item_name] <= 0:
        del inv[item_name]

    p['inventory'] = json.dumps(inv)

    # Handle consumables
    if item_name == "Health Potion":
        heal_amount = 100
        p['hp'] = min(p['max_hp'], p['hp'] + heal_amount)
        msg = f"Used Health Potion. Restored {heal_amount} HP!"
    elif item_name == "Mana Potion":
        restore = 80
        p['mana'] = min(p['max_mana'], p['mana'] + restore)
        msg = f"Used Mana Potion. Restored {restore} Mana!"
    elif item_name == "Strength Elixir":
        stats = parse_stats(p['stats'])
        stats['str'] += 5
        p['stats'] = json.dumps(stats)
        msg = "Used Strength Elixir. +5 STR for 1 hour!"
    else:
        msg = f"Used {item_name}."

    save_player_data(p['user_id'], p)
    await i.response.send_message(embed=discord.Embed(title="Item Used", description=msg, color=0x00ff00))

# ==================== OWNER COMMANDS ====================
async def is_owner(interaction: discord.Interaction) -> bool:
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("Only the Shadow Monarch may use this command.", ephemeral=True)
        return False
    return True

@tree.command(name="givelevel", description="[OWNER] Set someone's level")
@app_commands.describe(member="Target user", level="Level to set (1-999)")
async def givelevel(i: discord.Interaction, member: discord.Member, level: int):
    if not await is_owner(i): return
    if level < 1 or level > 999:
        return await i.response.send_message("Level must be 1–999", ephemeral=True)

    p = ensure_player(str(member.id), member.display_name)
    p['level'] = level
    p['rank'] = RANKS[min(level // 60, 7)]
    save_player_data(p['user_id'], p)

    await i.response.send_message(embed=discord.Embed(
        title="Level Set",
        description=f"**{member.display_name}** is now **Level {level} {p['rank']} Hunter**!",
        color=0x00ff00
    ))

@tree.command(name="giverank", description="[OWNER] Give any rank")
@app_commands.describe(member="Target user", rank="Rank: E D C B A S National Monarch")
async def giverank(i: discord.Interaction, member: discord.Member, rank: str):
    if not await is_owner(i): return
    rank = rank.upper()
    if rank not in RANKS:
        return await i.response.send_message(f"Invalid rank. Use: {', '.join(RANKS)}", ephemeral=True)

    p = ensure_player(str(member.id), member.display_name)
    p['rank'] = rank
    p['level'] = RANKS.index(rank) * 60
    save_player_data(p['user_id'], p)

    await i.response.send_message(embed=discord.Embed(
        title="Rank Given",
        description=f"**{member.display_name}** is now **{rank}-Rank Hunter**!",
        color=0x00ff00
    ))

@tree.command(name="givegold", description="[OWNER] Give gold")
@app_commands.describe(member="Target user", amount="Amount of gold")
async def givegold(i: discord.Interaction, member: discord.Member, amount: int):
    if not await is_owner(i): return
    if amount <= 0:
        return await i.response.send_message("Amount must be positive", ephemeral=True)

    p = ensure_player(str(member.id), member.display_name)
    p['gold'] += amount
    save_player_data(p['user_id'], p)

    await i.response.send_message(embed=discord.Embed(
        title="Gold Given",
        description=f"Gave **{amount:,} gold** to **{member.display_name}**!",
        color=0xffd700
    ))

@tree.command(name="setclass", description="[OWNER] Force change class")
@app_commands.choices(job=[
    app_commands.Choice(name="Hunter", value="Hunter"),
    app_commands.Choice(name="Necromancer", value="Necromancer"),
    app_commands.Choice(name="Monarch", value="Monarch")
])
async def setclass(i: discord.Interaction, member: discord.Member, job: str):
    if not await is_owner(i): return

    p = ensure_player(str(member.id), member.display_name)
    p['class'] = job
    if job == "Necromancer":
        p['max_mana'] += 300
        p['mana'] += 300
    elif job == "Monarch":
        stats = parse_stats(p['stats'])
        for stat in stats:
            stats[stat] += 100
        p['stats'] = json.dumps(stats)

    save_player_data(p['user_id'], p)
    await i.response.send_message(embed=discord.Embed(
        title="Class Changed",
        description=f"**{member.display_name}** is now **{job}**!",
        color=0x00ff00
    ))

@tree.command(name="analytics", description="[OWNER] View bot analytics")
async def analytics(i: discord.Interaction):
    if not await is_owner(i): return

    await i.response.send_message("Fetching analytics...", ephemeral=True)

    data = db.get_analytics(days=7)

    embed = discord.Embed(title="Bot Analytics (Last 7 Days)", color=0x5865f2)
    embed.add_field(name="Total Players", value=data['total_players'], inline=True)
    embed.add_field(name="Active Players", value=data['active_players'], inline=True)
    embed.add_field(name="Total Servers", value=data['total_servers'], inline=True)

    if data['command_stats']:
        cmd_text = "\n".join([f"`/{cmd}`: {count}" for cmd, count in list(data['command_stats'].items())[:10]])
        embed.add_field(name="Top Commands", value=cmd_text, inline=False)

    if data['top_players']:
        top_text = "\n".join([f"{i+1}. {p['name']} (Lv{p['level']} {p['rank']})" for i, p in enumerate(data['top_players'][:5])])
        embed.add_field(name="Top Players", value=top_text, inline=False)

    await i.followup.send(embed=embed, ephemeral=True)

@tree.command(name="broadcast", description="[OWNER] Send message to all servers")
@app_commands.describe(message="Message to broadcast")
async def broadcast(i: discord.Interaction, message: str):
    if not await is_owner(i): return

    await i.response.send_message(f"Broadcasting to {len(client.guilds)} servers...", ephemeral=True)

    sent = 0
    failed = 0
    for guild in client.guilds:
        try:
            # Try to find a general or system channel
            target = None
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    if "general" in channel.name.lower() or "system" in channel.name.lower():
                        target = channel
                        break
            if not target and guild.system_channel:
                target = guild.system_channel
            if not target and guild.text_channels:
                target = guild.text_channels[0]

            if target:
                embed = discord.Embed(
                    title="📢 Announcement from the Shadow Monarch",
                    description=message,
                    color=0x5865f2
                )
                embed.set_footer(text=f"From {i.user}")
                await target.send(embed=embed)
                sent += 1
        except Exception as e:
            logger.error(f"Failed to broadcast to {guild.name}: {e}")
            failed += 1

    await i.followup.send(f"✅ Broadcast complete: {sent} servers, {failed} failed.", ephemeral=True)

@tree.command(name="backup", description="[OWNER] Create database backup")
async def backup(i: discord.Interaction):
    if not await is_owner(i): return

    try:
        import shutil
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backup_{timestamp}.db"
        shutil.copy2('data.db', backup_file)
        await i.response.send_message(f"Backup created: {backup_file}", ephemeral=True)
    except Exception as e:
        await i.response.send_message(f"Backup failed: {e}", ephemeral=True)

@tree.command(name="health", description="Check bot health status")
async def health(i: discord.Interaction):
    latency = round(client.latency * 1000)
    guilds = len(client.guilds)
    users = len(client.users)

    embed = discord.Embed(title="Bot Health Status", color=0x00ff00)
    embed.add_field(name="Ping", value=f"{latency}ms", inline=True)
    embed.add_field(name="Servers", value=guilds, inline=True)
    embed.add_field(name="Users", value=users, inline=True)
    embed.add_field(name="Uptime", value=f"<t:{int(time.time())}:R>", inline=True)

    await i.response.send_message(embed=embed, ephemeral=True)

# ==================== ERROR HANDLERS ====================
@tree.error
async def on_app_command_error(i: discord.Interaction, error: app_commands.AppCommandError):
    logger.error(f"Command error: {error}")
    if isinstance(error, app_commands.CommandOnCooldown):
        await i.response.send_message(f"Cooldown: {error.retry_after:.1f}s", ephemeral=True)
    else:
        await i.response.send_message(f"Error: {str(error)}", ephemeral=True)

# ==================== RUN ====================
if __name__ == "__main__":
    try:
        logger.info("Connecting to Discord...")
        client.run(TOKEN)
    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        sys.exit(1)
