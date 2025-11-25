import os, discord, json, random, asyncio
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
    try: return json.load(open(DB))
    except: return {}
def save(d): json.dump(d, open(DB,"w"), indent=2)

data = load()

ranks = ["E","D","C","B","A","S","National Level","Monarch"]
rank_color = [0x808080,0x00ff00,0x0099ff,0xffff00,0xff00ff,0x00ffff,0xffffff,0x000000]

SKILLS = {
    "Fireball": {"cost":30, "dmg":120},
    "Heal": {"cost":25, "heal":150},
    "Shadow Extraction": {"cost":80, "extract":True},
    "Ruler’s Authority": {"cost":150, "dmg":400}
}

class Player:
    def __init__(self,u):
        uid = str(u.id)
        if uid not in data:
            data[uid] = {
                "name":u.display_name,"lv":1,"exp":0,"next":100,
                "rank":"E","gold":1000,"mana":150,"max_mana":150,
                "hp":300,"max_hp":300,
                "stats":{"str":10,"agi":10,"vit":10,"int":10,"sense":10},
                "class":"Hunter","shadows":[],"inv":{"Health Potion":5,"Mana Potion":3},
                "daily":"2000-01-01"
            }
            save(data)
        self.d = data[uid]
    def save(self): save(data)

def level_up(p):
    while p.d["exp"] >= p.d["next"]:
        p.d["exp"] -= p.d["next"]
        p.d["lv"] += 1
        p.d["next"] = int(p.d["next"]*1.45)
        for s in p.d["stats"]: p.d["stats"][s] += random.randint(4,9)
        p.d["max_hp"] += 40; p.d["hp"] = p.d["max_hp"]
        p.d["max_mana"] += 25; p.d["mana"] = p.d["max_mana"]
        if p.d["lv"]//60 > ranks.index(p.d["rank"]): 
            p.d["rank"] = ranks[min(p.d["lv"]//60,7)]
        p.save()

# ================== COMMANDS ==================
@tree.command(name="profile", description="Status window")
async def profile(i: discord.Interaction, member:discord.Member=None):
    u = member or i.user
    p = Player(u)
    e = discord.Embed(title=f"≪ {p.d['name']} ≫", color=rank_color[ranks.index(p.d['rank'])])
    e.add_field(name="Class", value=p.d["class"], inline=False)
    e.add_field(name="Rank • Level", value=f"**{p.d['rank']}** • {p.d['lv']}", inline=True)
    e.add_field(name="HP", value=f"{p.d['hp']}/{p.d['max_hp']}", inline=True)
    e.add_field(name="Mana", value=f"{p.d['mana']}/{p.d['max_mana']}", inline=True)
    e.add_field(name="Gold", value=f"{p.d['gold']:,}", inline=True)
    e.add_field(name="Shadows", value=len(p.d["shadows"]), inline=True)
    for k,v in p.d["stats"].items():
        e.add_field(name=k.capitalize(), value=v, inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    await i.response.send_message(embed=e)

@tree.command(name="daily")
async def daily(i: discord.Interaction):
    p = Player(i.user)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    if p.d["daily"] == today: return await i.response.send_message("Already claimed!", ephemeral=True)
    p.d["gold"] += random.randint(1500,3000)
    p.d["mana"] = p.d["max_mana"]
    p.d["daily"] = today
    p.save()
    await i.response.send_message(embed=discord.Embed(title="Daily Quest Cleared!", color=0x00ff00, description="Full mana + gold reward!"))

@tree.command(name="jobchange", description="Change class (one time)")
@app_commands.choices(job=[
    app_commands.Choice(name="Necromancer", value="Necromancer"),
    app_commands.Choice(name="Monarch", value="Monarch")
])
async def job(i: discord.Interaction, job: str):
    p = Player(i.user)
    if p.d["class"] != "Hunter": return await i.response.send_message("Already changed job!", ephemeral=True)
    if p.d["lv"] < 80: return await i.response.send_message("Need level 80+", ephemeral=True)
    p.d["class"] = job
    if job=="Necromancer": p.d["mana"] += 200; p.d["max_mana"] += 200
    if job=="Monarch": p.d["stats"]["str"] += 50; p.d["stats"]["int"] += 50
    p.save()
    await i.response.send_message(embed=discord.Embed(title="JOB CHANGE COMPLETE", description=f"You are now **{job}**!", color=0x000000 if job=="Monarch" else 0x8A2BE2))

# ================== LIVE BOSS FIGHT SYSTEM ==================
class BossFight(ui.View):
    def __init__(self, boss_name, hp, reward):
        super().__init__(timeout=180)
        self.hp = hp; self.max_hp = hp; self.reward = reward
        self.name = boss_name; self.alive = True

    @ui.button(label="Attack", style=discord.ButtonStyle.red, emoji="⚔️")
    async def attack(self, i: discord.Interaction, b):
        p = Player(i.user)
        dmg = p.d["stats"]["str"] + random.randint(30,80)
        if p.d["class"] == "Monarch": dmg = int(dmg*1.6)
        self.hp -= dmg
        await i.response.send_message(f"{i.user.mention} dealt **{dmg:,}** damage!", ephemeral=True)
        await self.update()

    @ui.button(label="Skill", style=discord.ButtonStyle.blurple, emoji="✨")
    async def skill(self, i: discord.Interaction, b):
        p = Player(i.user)
        view = ui.View()
        for name,sk in SKILLS.items():
            async def cb(interaction, n=name, s=sk):
                if p.d["mana"] < s["cost"]: return await interaction.response.send_message("Not enough mana!", ephemeral=True)
                p.d["mana"] -= s["cost"]
                if "dmg" in s: self.hp -= s["dmg"]
                if s.get("extract") and p.d["class"]=="Necromancer" and random.random()<0.7:
                    p.d["shadows"].append(f"{self.name} Shadow")
                    await interaction.response.send_message("Shadow Extracted!")
                p.save()
                await interaction.message.edit(view=None)
                await self.update()
            view.add_item(ui.Button(label=f"{name} ({s['cost']}✨)", style=discord.ButtonStyle.grey, callback=cb))
        await i.response.send_message("Choose skill:", view=view, ephemeral=True)

    async def update(self):
        if self.hp <= 0 and self.alive:
            self.alive = False
            winners = [c for c in self.children if c.custom_id]
            gold_each = self.reward // 3
            for child in self.children: child.disabled = True
            await self.message.edit(content=f"**{self.name} DEFEATED!**\n{len(winners)} hunters get **{gold_each:,} gold** each!", view=self)
            for u in [i.user for i in self.message.interactions[-10:]]: # rough
                p = Player(u); p.d["gold"] += gold_each; p.save()
        else:
            bar = "█"*int(20*self.hp/self.max_hp) + "░"*(20-len(that))
            await self.message.edit(content=f"**{self.name}**  ❤️ {self.hp:,}/{self.max_hp:,}\n`{bar}`", view=self)

async def spawn_boss(channel):
    bosses = ["Beru", "Igris", "Iron", "Tank", "Baran", "Ant King"]
    boss = random.choice(bosses)
    hp = random.randint(8000, 25000)
    reward = hp * 3
    embed = discord.Embed(title=f"⚔️ {boss} appeared! ⚔️", description=f"HP: {hp:,}\nReward pool: **{reward:,} gold**", color=0xff0000)
    view = BossFight(boss, hp, reward)
    view.message = await channel.send(embed=embed, view=view)
    await asyncio.sleep(180)
    if view.alive:
        for c in view.children: c.disabled=True
        await view.message.edit(content="The boss escaped…", view=view)

# spawn every 45–90 min
async def boss_spawner():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(2700,5400))
        guild = random.choice(list(client.guilds))
        ch = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        await spawn_boss(ch)

@client.event
async def on_ready():
    print(f"≪ SYSTEM ONLINE ≫ {client.user}")
    await tree.sync()
    client.loop.create_task(boss_spawner())

client.run(TOKEN)
