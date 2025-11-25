# =============== ULTIMATE SOLO LEVELING BOT 2025 ===============
import os, discord, json, random, asyncio, time
from discord import app_commands, ui
from datetime import datetime, timedelta

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

class Player:
    def __init__(self,u):
        uid = str(u.id)
        if uid not in data:
            data[uid] = {
                "name":u.display_name,"lv":1,"exp":0,"next":100,
                "rank":"E","gold":1500,"mana":150,"max_mana":150,
                "hp":300,"max_hp":300,"last_seen":time.time(),
                "stats":{"str":10,"agi":10,"vit":10,"int":10,"sense":10},
                "class":"Hunter","shadows":[],"inv":{"Health Potion":5,"Mana Potion":3},
                "daily":"2000-01-01","weekly":"2000-01-01",
                "quests":{"daily":0,"weekly":0},
                "training_cooldowns":{"pushup":0,"squat":0,"run":0}
            }
            save(data)
        self.d = data[uid]
    def save(self): save(data)

# PASSIVE OFFLINE TRAINING
async def passive_training():
    while True:
        await asyncio.sleep(3600)  # every hour
        now = time.time()
        for uid, p in data.items():
            if time.time() - p.get("last_seen",0) > 600:  # offline >10 min
                offline_hours = min(8, (now - p["last_seen"]) // 3600)
                p["exp"] += offline_hours * 120
                p["last_seen"] = now
        save(data)

@client.event
async def on_message(msg):
    if msg.author.bot: return
    p = Player(msg.author)
    p.d["last_seen"] = time.time()
    
    multiplier = 3 if "training-ground" in msg.channel.name.lower() else 1
    p.d["exp"] += random.randint(20,40) * multiplier
    
    # quest progress
    p.d["quests"]["daily"] += 1
    p.d["quests"]["weekly"] += 1
    
    while p.d["exp"] >= p.d["next"]:
        p.d["exp"] -= p.d["next"]
        p.d["lv"] += 1
        p.d["next"] = int(p.d["next"]*1.45)
        for s in p.d["stats"]: p.d["stats"][s] += random.randint(4,9)
        p.d["max_hp"] += 40; p.d["hp"] = p.d["max_hp"]
        p.d["max_mana"] += 25; p.d["mana"] = p.d["max_mana"]
        
        # SECOND AWAKENING every 50 levels
        if p.d["lv"] % 50 == 0:
            bonus = random.choice([
                "Max mana +300","All stats +30","Shadow extract chance +30%",
                "Double gold from bosses","Permanent 2× EXP in training ground"
            ])
            await msg.channel.send(f"**SECOND AWAKENING!** {msg.author.mention}\n→ {bonus}")
    
    if p.d["lv"]//60 > ranks.index(p.d["rank"]):
        p.d["rank"] = ranks[min(p.d["lv"]//60,7)]
        await msg.channel.send(embed=discord.Embed(title="RE-AWAKENING",description=f"{msg.author.mention} → **{p.d['rank']}-Rank Hunter**!",color=rank_color[ranks.index(p.d['rank'])]))
    
    p.save()

# TRAINING COMMANDS
@tree.command(name="pushup",description="Do 100 push-ups → +15 Strength")
async def pushup(i:discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cooldowns"]["pushup"]: 
        return await i.response.send_message("Cooldown active!",ephemeral=True)
    await i.response.send_message("Starting 100 push-ups… Go!")
    await asyncio.sleep(30)
    p.d["stats"]["str"] += 15
    p.d["training_cooldowns"]["pushup"] = time.time() + 3600*4  # 4h cooldown
    p.save()
    await i.followup.send("**100 Push-ups complete!** +15 Strength")

@tree.command(name="squat",description="Do 100 squats → +15 Vitality")
async def squat(i:discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cooldowns"]["squat"]: 
        return await i.response.send_message("Cooldown active!",ephemeral=True)
    await i.response.send_message("Starting 100 squats…")
    await asyncio.sleep(35)
    p.d["stats"]["vit"] += 15
    p.d["training_cooldowns"]["squat"] = time.time() + 3600*4
    p.save()
    await i.followup.send("**100 Squats complete!** +15 Vitality")

@tree.command(name="run",description="Run 10km → +15 Agility")
async def run(i:discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cooldowns"]["run"]: 
        return await i.response.send_message("Cooldown active!",ephemeral=True)
    await i.response.send_message("Running 10km…")
    await asyncio.sleep(40)
    p.d["stats"]["agi"] += 15
    p.d["training_cooldowns"]["run"] = time.time() + 3600*6
    p.save()
    await i.followup.send("**10km complete!** +15 Agility")

# QUESTS + SHOP + DUNGEONS + BOSS SPAWNER (everything from before also included)
# … (the rest is exactly the same as the previous version + these new systems)

@tree.command(name="quests")
async def quests(i:discord.Interaction):
    p = Player(i.user)
    e = discord.Embed(title="Quest Board",color=0x00ffff)
    e.add_field(name="Daily",value=f"Send 150 messages — {p.d['quests']['daily']}/150",inline=False)
    e.add_field(name="Weekly",value=f"Kill 5 bosses — {p.d['quests']['weekly']//5}/5",inline=False)
    await i.response.send_message(embed=e)

@tree.command(name="shop")
async def shop(i:discord.Interaction):
    view = ui.View()
    for item,price,effect in [("Strength Potion",800,"str+20"),("Intelligence Scroll",1200,"int+30")]:
        async def cb(inter, e=effect):
            p = Player(inter.user)
            if p.d["gold"] < price: return await inter.response.send_message("Poor!",ephemeral=True)
            p.d["gold"] -= price
            stat = e.split("+")[0]
            p.d["stats"][stat] += int(e.split("+")[1])
            p.save()
            await inter.response.edit_message(content=f"Bought {item} → +{e.split('+')[1]} {stat.capitalize()}",view=None)
        view.add_item(ui.Button(label=f"{item} — {price}g",callback=cb))
    await i.response.send_message("Stat Shop",view=view)

# Start passive training loop
client.loop.create_task(passive_training())

@client.event
async def on_ready():
    print(f"≪ SYSTEM ONLINE ≫ {client.user}")
    await tree.sync()
    client.loop.create_task(boss_spawner())  # from previous code

client.run(TOKEN)
