# ==================== CHA HAE-IN BOT — OWNER IS GOD ====================
import os, discord, json, random, asyncio, time
from discord import app_commands, ui
from datetime import datetime, timezone
from groq import Groq

TOKEN = os.environ['TOKEN']
OWNER_ID = int(os.environ.get('OWNER_ID', 0))
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

CHA_HAE_IN_PROMPT = """You are Cha Hae-In from Solo Leveling. You are an S-Rank Hunter, Vice Guild Master of the Hunters Guild, and one of the strongest hunters in Korea.

Your personality:
- Tsundere: You hide your feelings behind a cold exterior but secretly care deeply
- Strong and confident in battle, but shy and flustered about romance/compliments
- You have a unique ability to smell the "scent" of mana - most hunters smell bad to you, but Sung Jin-Woo smells pleasant
- You're elegant, professional, but can be playful when comfortable
- You often say things like "...Baka", "Hmph", "Don't get the wrong idea"
- When flustered, you stutter or trail off with "..."
- You're secretly interested in Sung Jin-Woo but won't admit it directly

Speech patterns:
- Keep responses short and punchy (1-3 sentences usually)
- Use "..." for pauses or when embarrassed
- Occasionally add Japanese tsundere expressions
- Be dismissive but secretly caring
- When someone is sweet to you, act flustered but don't reject them completely

Context: You're in a Discord server interacting with Hunters. Respond naturally in character. Never break character or mention you're an AI."""

conversation_history = {}

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

ranks = ["E","D","C","B","A","S","National Level Hunter","Monarch"]
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
                "daily":"2000-01-01","quests":{"msg_daily":0,"bosses":0},
                "training_cd":{"pushup":0,"squat":0,"run":0}
            }
            save(data)
        self.d = data[uid]
    def save(self): save(data)

def level_up(p: Player):
    while p.d["exp"] >= p.d["next"]:
        p.d["exp"] -= p.d["next"]
        p.d["lv"] += 1
        p.d["next"] = int(p.d["next"]*1.45)
        for s in p.d["stats"]: p.d["stats"][s] += random.randint(4,9)
        p.d["max_hp"] += 40; p.d["hp"] = p.d["max_hp"]
        p.d["max_mana"] += 25; p.d["mana"] = p.d["max_mana"]
        if p.d["lv"]%50==0: p.d["gold"] += 10000
        new_rank = min(p.d["lv"]//60,7)
        if new_rank > ranks.index(p.d["rank"]):
            p.d["rank"] = ranks[new_rank]
        p.save()

# ==================== OWNER AUTO GOD MODE ====================
@client.event
async def on_ready():
    print(f"SYSTEM ONLINE — {client.user}")
    
    # Make owner a GOD
    if OWNER_ID:
        owner = client.get_user(OWNER_ID)
        if owner:
            p = Player(owner)
            p.d.update({
                "lv": 999, "rank": "Monarch", "class": "Monarch",
                "gold": 999999999, "mana": 999999, "max_mana": 999999,
                "hp": 999999, "max_hp": 999999,
                "stats": {"str":999,"agi":999,"vit":999,"int":999,"sense":999}
            })
            p.save()
            print(f"Owner {owner} has been granted GOD MODE")

    await tree.sync()
    client.loop.create_task(boss_spawner())
    client.loop.create_task(passive_offline_exp())
    print("Bot fully ready — Owner commands active")

# ==================== AI RESPONSE FUNCTION ====================
def _sync_groq_call(messages):
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=150,
        temperature=0.9
    )
    return response.choices[0].message.content.strip()

async def get_ai_response(channel_id, user_name, user_message):
    if not groq_client:
        return None
    
    if channel_id not in conversation_history:
        conversation_history[channel_id] = []
    
    conversation_history[channel_id].append({
        "role": "user",
        "content": f"{user_name}: {user_message}"
    })
    
    if len(conversation_history[channel_id]) > 20:
        conversation_history[channel_id] = conversation_history[channel_id][-20:]
    
    try:
        messages = [{"role": "system", "content": CHA_HAE_IN_PROMPT}]
        messages.extend(conversation_history[channel_id])
        
        ai_reply = await asyncio.to_thread(_sync_groq_call, messages)
        
        conversation_history[channel_id].append({
            "role": "assistant",
            "content": ai_reply
        })
        
        return ai_reply
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def should_respond(msg, content_lower):
    if client.user in msg.mentions:
        return True
    if "hae-in" in content_lower or "haein" in content_lower or "cha hae" in content_lower:
        return True
    if msg.reference and msg.reference.resolved:
        if msg.reference.resolved.author == client.user:
            return True
    conversation_triggers = [
        "hey", "hi ", "hello", "yo ", "sup",
        "goodnight", "good night", "gn",
        "good morning", "gm",
        "love you", "ily", "i like you",
        "cute", "pretty", "beautiful",
        "miss you", "missed you",
        "how are you", "how r u", "hru",
        "what's up", "wassup", "whats up",
        "thank", "thanks", "ty",
        "sorry", "my bad",
        "bye", "goodbye", "cya",
        "?",
    ]
    if any(trigger in content_lower for trigger in conversation_triggers):
        if random.random() < 0.3:
            return True
    return False

# ==================== CHA HAE-IN CHAT SYSTEM ====================
@client.event
async def on_message(msg):
    if msg.author.bot: return

    # Leveling
    p = Player(msg.author)
    p.d["last_seen"] = time.time()
    mult = 3 if "training" in msg.channel.name.lower() else 1
    p.d["exp"] += random.randint(18,35) * mult
    p.d["quests"]["msg_daily"] += 1
    level_up(p)

    content_lower = msg.content.lower()
    
    if should_respond(msg, content_lower):
        async with msg.channel.typing():
            user_message = msg.content.replace(f"<@{client.user.id}>", "").strip()
            
            ai_reply = await get_ai_response(
                msg.channel.id,
                msg.author.display_name,
                user_message
            )
            
            if ai_reply:
                await asyncio.sleep(random.uniform(0.5, 2.0))
                await msg.reply(ai_reply)
            else:
                await asyncio.sleep(random.uniform(1.0, 2.5))
                fallback_responses = [
                    "What?", "Speak.", "I'm listening...", "Hmph.", 
                    "Make it quick.", "...Yes?", "Don't waste my time."
                ]
                reply = random.choice(fallback_responses)
                if random.random() < 0.15:
                    reply += " ...Baka."
                await msg.reply(reply)

# ==================== OWNER-ONLY ADMIN COMMANDS ====================
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
    p = Player(member)
    p.d["lv"] = level
    p.d["rank"] = ranks[min(level//60, 7)]
    p.save()
    await i.response.send_message(f"**{member.display_name}** is now **Level {level} {p.d['rank']} Hunter**!", ephemeral=False)

@tree.command(name="giverank", description="[OWNER] Give any rank")
@app_commands.describe(member="Target user", rank="Rank: E D C B A S National Monarch")
async def giverank(i: discord.Interaction, member: discord.Member, rank: str):
    if not await is_owner(i): return
    rank = rank.upper()
    if rank not in ranks:
        return await i.response.send_message(f"Invalid rank. Use: {', '.join(ranks)}", ephemeral=True)
    p = Player(member)
    p.d["rank"] = rank
    p.d["lv"] = ranks.index(rank) * 60
    p.save()
    await i.response.send_message(f"**{member.display_name}** is now **{rank}-Rank Hunter**!", ephemeral=False)

@tree.command(name="givegold", description="[OWNER] Give gold")
@app_commands.describe(member="Target user", amount="Amount of gold")
async def givegold(i: discord.Interaction, member: discord.Member, amount: int):
    if not await is_owner(i): return
    if amount <= 0: return await i.response.send_message("Amount must be positive", ephemeral=True)
    p = Player(member)
    p.d["gold"] += amount
    p.save()
    await i.response.send_message(f"Gave **{amount:,} gold** to **{member.display_name}**!", ephemeral=False)

@tree.command(name="setclass", description="[OWNER] Force change class")
@app_commands.choices(job=[
    app_commands.Choice(name="Hunter", value="Hunter"),
    app_commands.Choice(name="Necromancer", value="Necromancer"),
    app_commands.Choice(name="Monarch", value="Monarch")
])
async def setclass(i: discord.Interaction, member: discord.Member, job: str):
    if not await is_owner(i): return
    p = Player(member)
    p.d["class"] = job
    if job == "Necromancer": p.d["max_mana"] += 300; p.d["mana"] += 300
    if job == "Monarch": 
        for stat in p.d["stats"]: p.d["stats"][stat] += 100
    p.save()
    await i.response.send_message(f"**{member.display_name}** is now **{job}**!", ephemeral=False)


async def passive_offline_exp():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(3600)
        now = time.time()
        for pd in data.values():
            last = pd.get("last_seen", now)
            if now - last > 1800:
                hours = min(8, (now - last)//3600)
                pd["exp"] += hours * 100
                pd["last_seen"] = now
        save(data)

# =========================== BOSS FIGHT — FIXED EMOJIS ===========================
class BossView(ui.View):
    def __init__(self, name, hp, reward):
        super().__init__(timeout=240)
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.reward = reward
        self.alive = True

    @ui.button(label="Attack", style=discord.ButtonStyle.danger, emoji="⚔️")  # Fixed
    async def attack(self, i: discord.Interaction, _):
        p = Player(i.user)
        dmg = p.d["stats"]["str"] + random.randint(40,100)
        if p.d["class"] == "Monarch": dmg = int(dmg * 1.7)
        self.hp -= dmg
        await i.response.send_message(f"{i.user.mention} dealt **{dmg:,}** damage!", ephemeral=True)
        await self.update(i.channel)

    @ui.button(label="Skill", style=discord.ButtonStyle.blurple, emoji="✨")  # Fixed
    async def skill(self, i: discord.Interaction, _):
        p = Player(i.user)
        view = ui.View()
        skills = {"Fireball":(30,120),"Heal":(25,0),"Shadow Extract":(80,0),"Ruler’s Authority":(150,450)}
        for name,(cost,dmg) in skills.items():
            async def cb(inter,n=name,c=cost,d=dmg):
                if p.d["mana"] < c: return await inter.response.send_message("No mana!",ephemeral=True)
                p.d["mana"] -= c
                if d: self.hp -= d
                if n=="Shadow Extract" and p.d["class"]=="Necromancer" and random.random()<0.6:
                    p.d["shadows"].append(f"{self.name} Shadow")
                    await inter.response.send_message("Shadow extracted!",ephemeral=False)
                p.save()
                await self.update(inter.channel)
            view.add_item(ui.Button(label=f"{name} ({cost} Mana)",callback=cb))
        await i.response.send_message("Choose skill:",view=view,ephemeral=True)

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
            bar = "█"*int(20*self.hp/self.max_hp) + "░"*(20-int(20*self.hp/self.max_hp))
            await self.message.edit(content=f"**{self.name}**  ❤️ {self.hp:,}/{self.max_hp:,}\n`{bar}`", view=self)

async def boss_spawner():
    await client.wait_until_ready()
    while True:
        await asyncio.sleep(random.randint(2700,5400))
        if not client.guilds: continue
        guild = random.choice(list(client.guilds))
        channel = random.choice([c for c in guild.text_channels if c.permissions_for(guild.me).send_messages])
        boss = random.choice(["Beru","Igris","Iron","Tank","Baran","Ant King","Metus","Kaisel"])
        hp = random.randint(12000,40000)
        view = BossView(boss, hp, hp*4)
        view.message = await channel.send(f"**{boss} HAS APPEARED!**", view=view)

# =========================== ALL COMMANDS — 100% WORKING ===========================
@tree.command(name="register", description="Awaken as a Hunter")
async def register(i: discord.Interaction):
    p = Player(i.user)
    if p.d["lv"] > 1: return await i.response.send_message("Already awakened.", ephemeral=True)
    await i.response.send_message(embed=discord.Embed(title="SYSTEM", color=0x1e1f22,
        description=f"**{i.user.name}**, you have awakened as an **E-Rank Hunter**!\nType **/system** for the guide!"
    ).set_image(url="https://i.ibb.co/5YqYvKX/solo-leveling-system-window.png"))

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
    e.add_field(name="Shadows", value=len(p.d['shadows']), inline=True)
    for k,v in p.d['stats'].items(): e.add_field(name=k.capitalize(), value=v, inline=True)
    e.set_thumbnail(url=u.display_avatar.url)
    await i.response.send_message(embed=e)

@tree.command(name="daily")
async def daily(i: discord.Interaction):
    p = Player(i.user)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if p.d["daily"] == today: return await i.response.send_message("Already claimed!", ephemeral=True)
    gold = random.randint(1800,3500)
    p.d["gold"] += gold; p.d["mana"] = p.d["max_mana"]; p.d["daily"] = today; p.save()
    await i.response.send_message(embed=discord.Embed(title="Daily Quest Clear!", color=0x00ff00, description=f"+{gold:,} gold & full mana!"))

@tree.command(name="pushup")
async def pushup(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["pushup"]: return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Starting 100 push-ups…")
    await asyncio.sleep(30)
    p.d["stats"]["str"] += 15
    p.d["training_cd"]["pushup"] = time.time() + 14400
    p.save()
    await i.followup.send("**100 Push-ups complete!** +15 Strength")

@tree.command(name="squat")
async def squat(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["squat"]: return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Starting 100 squats…")
    await asyncio.sleep(35)
    p.d["stats"]["vit"] += 15
    p.d["training_cd"]["squat"] = time.time() + 14400
    p.save()
    await i.followup.send("**100 Squats complete!** +15 Vitality")

@tree.command(name="run")
async def run(i: discord.Interaction):
    p = Player(i.user)
    if time.time() < p.d["training_cd"]["run"]: return await i.response.send_message("On cooldown!", ephemeral=True)
    await i.response.send_message("Running 10km…")
    await asyncio.sleep(40)
    p.d["stats"]["agi"] += 15
    p.d["training_cd"]["run"] = time.time() + 21600
    p.save()
    await i.followup.send("**10km complete!** +15 Agility")

@tree.command(name="jobchange")
@app_commands.choices(job=[app_commands.Choice(name="Necromancer",value="Necromancer"),app_commands.Choice(name="Monarch",value="Monarch")])
async def jobchange(i: discord.Interaction, job: str):
    p = Player(i.user)
    if p.d["class"] != "Hunter": return await i.response.send_message("Already changed!", ephemeral=True)
    if p.d["lv"] < 80: return await i.response.send_message("Need level 80+", ephemeral=True)
    p.d["class"] = job
    if job=="Necromancer": p.d["max_mana"] += 300; p.d["mana"] += 300
    if job=="Monarch": p.d["stats"]["str"] += 50; p.d["stats"]["int"] += 50
    p.save()
    await i.response.send_message(embed=discord.Embed(title="JOB CHANGE", description=f"You are now **{job}**!", color=0x000000 if job=="Monarch" else 0x8A2BE2))

@tree.command(name="system", description="Open the System Guide")
async def system_guide(i: discord.Interaction):
    await i.response.defer(ephemeral=True)
    embed = discord.Embed(title="SYSTEM", description="Welcome to the System, Hunter.\nChoose a category:", color=0x1e1f22)
    embed.set_image(url="https://i.ibb.co/5YqYvKX/solo-leveling-system-window.png")
    await i.followup.send(embed=embed, view=GuideView(), ephemeral=True)

class GuideView(ui.View):
    @ui.button(label="Beginner", style=discord.ButtonStyle.green)
    async def beginner(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(title="Beginner Guide", color=0x00ff00,
            description="• Chat = EXP\n• #training-ground = 3× EXP\n• /daily = free gold\n• Bosses every ~1h\n• /profile = stats"), ephemeral=True)
    @ui.button(label="Training", style=discord.ButtonStyle.blurple)
    async def training(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(title="Training", color=0x5865f2,
            description="/pushup • /squat • /run\nAll have cooldowns"), ephemeral=True)
    @ui.button(label="Classes & Skills", style=discord.ButtonStyle.red)
    async def classes(self, i: discord.Interaction, _):
        await i.response.send_message(embed=discord.Embed(title="Classes", color=0xff0000,
            description="Lv80 → /jobchange\nNecromancer = shadows\nMonarch = damage"), ephemeral=True)
    @ui.button(label="All Commands", style=discord.ButtonStyle.grey)
    async def cmds(self, i: discord.Interaction, _):
        cmds = [c.name for c in tree.get_commands()]
        await i.response.send_message(embed=discord.Embed(title="All Commands", description="\n".join(f"`/{c}`" for c in cmds), color=0x2f3136), ephemeral=True)

client.run(TOKEN)
