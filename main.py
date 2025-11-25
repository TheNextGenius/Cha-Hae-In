# ==================== ULTIMATE SOLO LEVELING BOT 2025 — FINAL CLEAN ====================
import os
import discord
import json
import random
import asyncio
import time
from discord import app_commands, ui
from datetime import datetime

TOKEN = os.environ['TOKEN']
OWNER_ID = int(os.environ['OWNER_ID'])

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

DB = "db.json"
def load():
    try:
        try: return json.load(open(DB))
        except: return {}
def save(d):
    json.dump(d, open(DB, "w"), indent=2)

data = load()

ranks = ["E","D","C","B","A","S","National Level Hunter","Monarch"]
rank_color = [0x808080,0x00ff00,0x0099ff,0xffff00,0xff00ff,0x00ffff,0xffffff,0x000000]

class Player:
    def __init__(self, u):
        uid = str(u.id)
        if uid not in data:
            data[uid] = {
                "name": u.display_name, "lv": 1, "exp": 0, "next": 100,
                "rank": "E", "gold": 1500, "mana": 150, "max_mana": 150,
                "hp": 300, "max_hp": 300, "last_seen": time.time(),
                "stats": {"str":10,"agi":10,"vit":10,"int":10,"sense":10},
                "class": "Hunter", "shadows": [], "inv": {"Health Potion":5,"Mana Potion":3},
                "daily": "2000-01-01",
                "quests": {"msg_daily":0, "bosses":0},
                "training_cd": {"pushup":0, "squat":0, "run":0}
            }
            save(data)
        self.d = data[uid]
    def save(self):
        save(data)

def level_up(p: Player):
    while p.d["exp"] >= p.d["next"]:
        p.d["exp"] -= p.d["next"]
        p.d["lv"] += 1
        p.d["next"] = int(p.d["next"] * 1.45)
        for s in p.d["stats"]:
            p.d["stats"][s] += random.randint(4,9)
        p.d["max_hp"] += 40; p.d["hp"] = p.d["max_hp"]
        p.d["max_mana"] += 25; p.d["mana"] = p.d["max_mana"]
        if p.d["lv"] % 50 == 0:
            bonus = random.choice(["Max mana +300","All stats +30","Shadow extract +30%","Double boss gold"])
            p.d["gold"] += 10000
        new_rank = min(p.d["lv"]//60, 7)
        if new_rank > ranks.index(p.d["rank"]):
            p.d["rank"] = ranks[new_rank]
        p.save()

# =========================== EVENTS ===========================
@client.event
async def on_ready():
    print(f"SYSTEM ONLINE — {client.user}")
    await tree.sync()
    client.loop.create_task(boss_spawner())
    client.loop.create_task(passive_offline_exp())

@client.event
async def on_message(msg):
    if msg.author.bot: return
    p = Player(msg.author)
    p.d["last_seen"] = time.time()
    mult = 3 if "training" in msg.channel.name.lower() else 1
    p.d["exp"] += random.randint(18, 35) * mult
    p.d["quests"]["msg_daily"] += 1
    level_up(p)
    p.save()

async def passive_offline_exp():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(3600)
        now = time.time()
        for uid, pd in data.items():
            last = pd.get("last_seen", now)
            if now - last > 1800:  # offline >30 min
                hours = min(8, (now - last) // 3600)
                pd["exp"] += hours * 100
                pd["last_seen"] = now
        save(data)

# =========================== BOSS FIGHT ===========================
class BossView(ui.View):
    def __init__(self, name, hp, reward):
        super().__init__(timeout=240)
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.reward = reward
        self.alive = True

    @ui.button(label="Attack", style=discord.ButtonStyle.danger, emoji="Sword")
    async def attack(self, i: discord.Interaction, _):
        p = Player(i.user)
        dmg = p.d["stats"]["str"] + random.randint(40,100)
        if p.d["class"] == "Monarch": dmg = int(dmg * 1.7)
        self.hp -= dmg
        await i.response.send_message(f"{i.user.mention} dealt **{dmg:,}** damage!", ephemeral=True)
        await self.update(i.channel)

    @ui.button(label="Skill", style=discord.ButtonStyle.blurple, emoji="Magic")
    async def skill(self, i: discord.Interaction, _):
        p = Player(i.user)
        view = ui.View()
        skills = {"Fireball":(30,120), "Heal":(25,0), "Shadow Extract":(80,0), "Ruler’s Authority":(150,450)}
        for name, (cost, dmg) in skills.items():
            async def cb(inter, n=name, c=cost, d=dmg):
                if p.d["mana"] < c:
                    return await inter.response.send_message("No mana!", ephemeral=True)
                p.d["mana"] -= c
                if d: self.hp -= d
                if n == "Shadow Extract" and p.d["class"] == "Necromancer" and random.random() < 0.6:
                    p.d["shadows"].append(f"{self.name} Shadow")
                    await inter.response.send_message("Shadow extracted!", ephemeral=False)
                p.save()
                await self.update(inter.channel)
            view.add_item(ui.Button(label=f"{name} ({cost} Mana)", callback=cb))
        await i.response.send_message("Choose skill:", view=view, ephemeral=True)

    async def update(self, channel):
        if self.hp <= 0 and self.alive:
            self.alive = False
            gold_each = self.reward // 5
            for b in self.children: b.disabled = True
            await self.message.edit(content=f"**{self.name} DEFEATED!**\nEveryone gets **{gold_each:,} gold**!", view=self)
            for member in channel.guild.members:
                if not member.bot:
                    pp = Player(member)
                    pp.d["gold"] += gold_each
                    pp.d["quests"]["bosses"] += 1
                    pp.save()
        else:
            bar = "█" * int(20 * self.hp / self.max_hp) + "░" * (20 - int(20 * self.hp / self.max_hp))
            await self.message.edit(content=f"**{self.name}**  ❤️ {self.hp:,}/{self.max_hp:,}\n`{bar}`", view=self)

async def boss_spawner():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(2700,5400))
        if not client.guilds: continue
        guild = random.choice(list(client.guilds))
        channel = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        bosses = ["Beru","Igris","Iron","Tank","Baran","Ant King","Metus","Kaisel"]
        boss = random.choice(bosses)
        hp = random.randint(12000, 40000)
        reward = hp * 4
        embed = discord.Embed(title=f"{boss} HAS APPEARED!", color=0xff0000)
        view = BossView(boss, hp, reward)
        view.message = await channel.send(embed=embed, view=view)

# =========================== COMMANDS ===========================
@tree.command(name="register", description="Awaken as a Hunter")
async def register(i: discord.Interaction):
    p = Player(i.user)
    if p.d["lv"] > 1:
        return await i.response.send_message("You are already awakened.", ephemeral=True)
    await i.response.send_message(embed=discord.Embed(
        title="SYSTEM", color=0x1e1f22,
        description=f"**{i.user.name}**, you have awakened as an **E-Rank Hunter**.\n"
                    "Type **/system** for the full guide!"
    ).set_image(url="https://i.imgur.com/7QzYwZf.png"))

@tree.command(name="profile")
async def profile(i: discord.Interaction, member: discord.Member = None):
    u = member or i.user
    p = Player(u)
    e = discord.Embed(title=f"≪ {p.d['name']} ≫", color=rank_color[ranks.index(p.d['rank'])])
    e.add_field(name="Class • Rank", value=f"{p.d['class']} • **{p.d['rank']}**")
    e.add_field(name="Level", value=p.d["lv"], inline=True)
    e.add_field(name="HP", value=f"{p.d['hp']}/{p.d['max_hp']}", inline=True)
    e.add_field(name="Mana", value=f"{p.d['mana']}/{p.d['max_mana']}", inline=True)
    e.add_field(name="Gold", value=f"{p.d['gold']:,}", inline=True)
    e.add_field(name="Shadows", value=len(p.d["shadows"]), inline=True)
    for k, v in p.d['stats'].items():
        e.add_field(name=k.capitalize(), value=v, inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    await i.response.send_message(embed=e)

@tree.command(name="daily")
async def daily(i: discord.Interaction):
    p = Player(i.user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if p.d["daily"] == today:
        return await i.response.send_message("Already claimed today!", ephemeral=True)
    gold = random.randint(1800,3500)
    p.d["gold"] += gold
    p.d["mana"] = p.d["max_mana"]
    p.d["daily"] = today
    p.save()
    await i.response.send_message(embed=discord.Embed(title="Daily Quest Clear!", color=0x00ff00, description=f"+{gold:,} gold & full mana!"))

@tree.command(name="pushup")
async def pushup(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["pushup"]:
        return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Starting 100 push-ups…")
    await asyncio.sleep(30)
    p.d["stats"]["str"] += 15
    p.d["training_cd"]["pushup"] = time.time() + 14400  # 4h
    p.save()
    await i.followup.send("**100 Push-ups complete!** +15 Strength")

@tree.command(name="squat")
async def squat(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["squat"]:
        return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Starting 100 squats…")
    await asyncio.sleep(35)
    p.d["stats"]["vit"] += 15
    p.d["training_cd"]["squat"] = time.time() + 14400
    p.save()
    await i.followup.send("**100 Squats complete!** +15 Vitality")

@tree.command(name="run")
async def run(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["run"]:
        return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Running 10km…")
    await asyncio.sleep(40)
    p.d["stats"]["agi"] += 15
    p.d["training_cd"]["run"] = time.time() + 21600  # 6h
    p.save()
    await i.followup.send("**10km complete!** +15 Agility")

@tree.command(name="jobchange")
@app_commands.choices(job=[app_commands.Choice(name="Necromancer",value="Necromancer"), app_commands.Choice(name="Monarch",value="Monarch")])
async def jobchange(i: discord.Interaction, job: str):
    p = Player(i.user)
    if p.d["class"] != "Hunter":
        return await i.response.send_message("Already changed class!", ephemeral=True)
    if p.d["lv"] < 80:
        return await i.response.send_message("Need level 80+", ephemeral=True)
    p.d["class"] = job
    if job == "Necromancer":
        p.d["max_mana"] += 300; p.d["mana"] += 300
    if job == "Monarch":
        for s in ["str","int"]: p.d["stats"][s] += 50
    p.save()
    await i.response.send_message(embed=discord.Embed(title="JOB CHANGE SUCCESS", description=f"You are now **{job}**!", color=0x000000 if job=="Monarch" else 0x8A2BE2))

@tree.command(name="system", description="Open the System Guide")
async def system_guide(i: discord.Interaction):
    embed = discord.Embed(title="SYSTEM", description="Welcome to the System, Hunter.\nChoose a category:", color=0x1e1f22)
    embed.set_image(url="https://i.imgur.com/7QzYwZf.png")
    await i.response.send_message(embed=embed, view=GuideView(), ephemeral=True)

class GuideView(ui.View):
    @ui.button(label="Beginner Guide", style=discord.ButtonStyle.green)
    async def beginner(self, i, _):
        await i.response.send_message(embed=discord.Embed(title="Beginner Guide", color=0x00ff00,
            description="• Chat = EXP\n• #training-ground = 3× EXP\n• `/daily` = free gold\n• Bosses spawn every ~1h\n• `/profile` to view stats"), ephemeral=True)

    @ui.button(label="Training", style=discord.ButtonStyle.blurple)
    async def training(self, i, _):
        await i.response.send_message(embed=discord.Embed(title="Training Commands", color=0x5865f2,
            description="/pushup • /squat • /run\nAll have cooldowns\nOffline EXP every hour"), ephemeral=True)

    @ui.button(label="Classes & Skills", style=discord.ButtonStyle.red)
    async def classes(self, i, _):
        await i.response.send_message(embed=discord.Embed(title="Classes", color=0xff0000,
            description="Level 80 → /jobchange\nNecromancer = shadows\nMonarch = damage\nUse Skill button in raids"), ephemeral=True)

    @ui.button(label="All Commands", style=discord.ButtonStyle.grey)
    async def cmds(self, i, _):
        cmds = "\n".join([f"</{c.name}:{c.id}>" for c in tree.get_commands()])
        await i.response.send_message(embed=discord.Embed(title="Full Command List", description=cmds, color=0x2f3136), ephemeral=True)

client.run(TOKEN)
