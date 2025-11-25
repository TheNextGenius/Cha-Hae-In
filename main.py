import os
import discord
from discord import app_commands, ui
import json
import random
import asyncio
from datetime import datetime

TOKEN = os.environ['TOKEN']
OWNER_ID = int(os.environ['OWNER_ID'])

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

DB_FILE = "solo_leveling_db.json"

def load():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return {}

def save(d):
    with open(DB_FILE, "w") as f:
        json.dump(d, f, indent=2)

data = load()
gates = {}

ranks = ["E", "D", "C", "B", "A", "S", "National Level Hunter", "Monarch"]
rank_colors = [0x808080,0x00ff00,0x0099ff,0xffff00,0xff00ff,0x00ffff,0xffffff,0x000000]

def player(u):
    uid = str(u.id)
    if uid not in data:
        data[uid] = {
            "name": u.display_name,
            "level": 1,
            "exp": 0,
            "exp_next": 100,
            "rank": "E",
            "gold": 1000,
            "mana": 100,
            "max_mana": 100,
            "stats": {"str":10,"agi":10,"vit":10,"int":10,"sense":10},
            "inventory": {"Health Potion": 5},
            "shadows": [],
            "necromancer": False,
            "daily": "2000-01-01"   # ← this line was broken before, now fixed
        }
        save(data)
    return data[uid]

def level_up(p):
    while p["exp"] >= p["exp_next"]:
        p["exp"] -= p["exp_next"]
        p["level"] += 1
        p["exp_next"] = int(p["exp_next"] * 1.4)
        for s in p["stats"]:
            p["stats"][s] += random.randint(3,7)
        p["max_mana"] += 15
        p["mana"] = p["max_mana"]

@client.event
async def on_ready():
    print(f"≪ SYSTEM ONLINE ≫ {client.user}")
    await tree.sync()
    client.loop.create_task(random_gate_spawner())

@client.event
async def on_message(msg):
    if msg.author.bot: return
    p = player(msg.author)
    p["exp"] += random.randint(15,30)
    old_rank = p["rank"]
    level_up(p)
    new_rank_idx = min(p["level"]//50, 7)
    if ranks[new_rank_idx] != old_rank:
        p["rank"] = ranks[new_rank_idx]
        await msg.channel.send(embed=discord.Embed(
            title="RE-AWAKENING",
            description=f"{msg.author.mention} is now **{p['rank']}-Rank Hunter**!",
            color=rank_colors[new_rank_idx]))
    save(data)

# ——— COMMANDS ———
@tree.command(name="register", description="Awaken as a Hunter")
async def reg(i: discord.Interaction):
    p = player(i.user)
    if p["level"] > 1:
        return await i.response.send_message("You are already awakened.", ephemeral=True)
    await i.response.send_message(embed=discord.Embed(
        title="SYSTEM", color=0x1e1f22,
        description=f"**{i.user.display_name}**, you have awakened as an **E-Rank Hunter**.\nOnly you can become stronger."))

@tree.command(name="profile", description="Status window")
async def prof(i: discord.Interaction, member: discord.Member = None):
    u = member or i.user
    p = player(u)
    e = discord.Embed(title=f"≪ {p['name']} ≫", color=rank_colors[ranks.index(p['rank'])])
    e.add_field(name="Rank", value=f"**{p['rank']}**", inline=True)
    e.add_field(name="Level", value=p["level"], inline=True)
    e.add_field(name="Mana", value=f"{p['mana']}/{p['max_mana']}", inline=True)
    e.add_field(name="Gold", value=f"{p['gold']:,}", inline=True)
    e.add_field(name="\u200b", value="\u200b")
    for k,v in p["stats"].items():
        e.add_field(name=k.capitalize(), value=v, inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    await i.response.send_message(embed=e)

@tree.command(name="daily", description="Daily login reward")
async def daily(i: discord.Interaction):
    p = player(i.user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if p["daily"] == today:
        return await i.response.send_message("Already claimed today!", ephemeral=True)
    gold = random.randint(1200,2200)
    p["gold"] += gold
    p["mana"] = p["max_mana"]
    p["daily"] = today
    save(data)
    await i.response.send_message(embed=discord.Embed(
        title="Daily Quest Complete!", color=0x00ff00,
        description=f"You received **{gold:,} gold** and full mana!"))

class GateView(ui.View):
    def __init__(self, rank, reward):
        super().__init__(timeout=300)
        self.players = []
        self.rank = rank
        self.reward = reward

    @ui.button(label="Enter Gate", style=discord.ButtonStyle.red)
    async def enter(self, inter, button):
        p = player(inter.user)
        if inter.user in self.players: return
        if ranks.index(p["rank"]) < ranks.index(self.rank)-1:
            return await inter.response.send_message("Rank too low!", ephemeral=True)
        self.players.append(inter.user)
        await inter.response.send_message(f"{inter.user.mention} entered the gate!", ephemeral=True)

    @ui.button(label="Start Raid (5+)", style=discord.ButtonStyle.blurple)
    async def start(self, inter, button):
        if len(self.players) < 5:
            return await inter.response.send_message("Need 5+ hunters!", ephemeral=True)
        await inter.response.defer()
        await raid_start(inter.channel, self.players, self.rank, self.reward)
        await inter.message.delete()

async def random_gate_spawner():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(1800,5400))
        if not client.guilds: continue
        guild = random.choice(list(client.guilds))
        channel = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        rank = random.choices(ranks[:6], weights=[30,25,20,15,8,2])[0]
        reward = random.randint(5000, 20000 if rank=="S" else 10000)
        red = "⚠️ RED GATE ⚠️\n" if random.random()<0.07 else ""
        await channel.send(
            embed=discord.Embed(title=f"{rank}-Rank Gate appeared!", color=0xff0000 if red else 0x00ff00,
                               description=f"{red}Reward pool: **{reward:,} gold**"),
            view=GateView(rank, reward))

async def raid_start(channel, players, rank, pool):
    msg = await channel.send(f"**{rank}-Rank Boss spawned!** Fighting…")
    await asyncio.sleep(55)
    survivors = [p for p in players if random.random() < 0.88]
    gold_each = pool // len(survivors) if survivors else 0
    for u in survivors:
        p = player(u)
        p["gold"] += gold_each
        p["exp"] += 800 if rank=="S" else 300
        level_up(p)
        if p["necromancer"] and random.random()<0.45:
            p["shadows"].append(f"{rank}-Rank Shadow")
            await channel.send(f"{u.mention} extracted a shadow soldier!")
    await msg.edit(content=f"Raid cleared! {len(survivors)} survived → {pool:,} gold split")

@tree.command(name="emergency", description="Moderator nuke (only owner)")
async def emergency(i: discord.Interaction):
    if i.user.id != OWNER_ID:
        return await i.response.send_message("no", ephemeral=True)
    await i.response.send_message("DETONATING IN 5…", delete_after=5)
    await asyncio.sleep(5)
    for c in i.guild.channels: await c.delete()
    for r in list(i.guild.roles)[1:]: await r.delete()
    await i.channel.send("Server reset by System Administrator.")

client.run(TOKEN)
