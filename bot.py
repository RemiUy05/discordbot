import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
import random
import json
import os
from dotenv import load_dotenv

load_dotenv()


# ══════════════════════════════════════════════════════════
#  CONFIG  –  edit these before running
# ══════════════════════════════════════════════════════════
QUESTION_CHANNEL_ID = 123456789012345678   # your question channel ID
DAILY_HOUR          = 17                   # noon UTC
DAILY_MINUTE        = 0
TOKEN = os.getenv('DISCORD_TOKEN')

# ── Data files ──────────────────────────────────────────
HISTORY_FILE   = "asked_questions.json"
USER_DATA_FILE = "user_data.json"
MEMORIES_FILE  = "memories.json"
PARTNERS_FILE  = "partners.json"

# ══════════════════════════════════════════════════════════
#  ASCII BIRD LEVELS
#  Your love bird grows as your streak increases!
# ══════════════════════════════════════════════════════════
#  (min_streak, level_name, ascii_art)
LEVELS = [
    (0,   "Egg",          "  ( · )\n  ( · )\n  `---'"),
    (3,   "Hatchling",    "  _\n (o)\n  U"),
    (7,   "Chick",        "  >>\n (°v°)\n  UU"),
    (14,  "Fledgling",    " \\o/\n(°v°)\n U U"),
    (30,  "Robin",        "  \\o/\n (^v^)\n /||\\\n  UU"),
    (60,  "Songbird",     " ~\\o/~\n (^V^)\n /||\\\n  d d"),
    (90,  "Lovebird",     "  ~\\O/~\n♥(^V^)♥\n /| |\\\n  d d"),
    (180, "Lovebird Pro", " ~~\\O/~~\n♥♥(^V^)♥♥\n /|   |\\\n d |_| b"),
    (365, "Eternal Dove", "  ~~~\\O/~~~\n♥♥♥(^V^)♥♥♥\n /|     |\\\n d  ~~~  b\n  ~~   ~~"),
]

MILESTONE_STREAKS = {3, 7, 14, 30, 60, 90, 180, 365}

def get_level(streak: int) -> tuple[str, str]:
    """Return (level_name, ascii_art) for a given streak."""
    name, art = LEVELS[0][1], LEVELS[0][2]
    for min_s, lname, lart in LEVELS:
        if streak >= min_s:
            name, art = lname, lart
        else:
            break
    return name, art

def next_milestone(streak: int) -> int | None:
    for min_s, _, _ in LEVELS:
        if min_s > streak:
            return min_s
    return None

# ══════════════════════════════════════════════════════════
#  DATE IDEAS
# ══════════════════════════════════════════════════════════
DATE_IDEAS = {
    "cozy": [
        "Build a blanket fort and watch your favourite movies all night 🛋️🍿",
        "Cook a new recipe together from scratch and rate it like MasterChef 👨‍🍳",
        "Have a board game tournament — winner picks tomorrow's activity 🎲🏆",
        "Draw portraits of each other — artistic skill not required 🎨",
        "Make a scrapbook of your favourite memories together 📸",
        "Do a puzzle together with candles and a playlist 🕯️🧩",
        "Write each other a letter to open in one year ✉️",
        "Home spa night — face masks, foot soak, the whole deal 🧖",
    ],
    "adventurous": [
        "Go on a sunrise hike and bring hot drinks ☕🏔️",
        "Try an escape room — see how well you work as a team 🔐",
        "Take a spontaneous day trip somewhere neither of you has been 🗺️",
        "Go rock climbing or bouldering indoors 🧗",
        "Try a pottery or ceramics class together 🪴",
        "Rent bikes and explore somewhere new 🚲",
        "Go stargazing outside the city with a blanket and snacks 🌌",
        "Sign up for a dance class — salsa, swing, anything 💃🕺",
    ],
    "cheap": [
        "Picnic in the park with homemade sandwiches 🥪🌿",
        "Visit a free museum or gallery, each pick one favourite exhibit 🖼️",
        "Watch the sunset from the best viewpoint near you 🌅",
        "Explore a part of your town you've never been to before 🏘️",
        "Movie marathon of a director or genre you both love 🎬",
        "Charity shop challenge — each pick an outfit for the other 👗",
        "Play tourist in your own city for a day 📷",
        "Three-course dinner at home with candles and a playlist 🕯️",
    ],
    "fancy": [
        "Book a tasting menu at a restaurant you've been saving for 🍷",
        "Stay one night in a nice hotel — even if it's across town 🏨",
        "Opera, ballet, or a live concert 🎻",
        "Private chef experience for the evening 👨‍🍳✨",
        "Scenic train or boat journey with a champagne picnic 🥂",
        "Couple's spa day 💆",
        "Short flight somewhere new just for the weekend 🛫",
        "Wine or whisky tasting at a proper venue 🍾",
    ],
}

# ══════════════════════════════════════════════════════════
#  QUESTION BANK
# ══════════════════════════════════════════════════════════
QUESTIONS = [
    {"type": "open",  "text": "What was the most romantic thing you have ever done together? 💕"},
    {"type": "open",  "text": "What is your favourite memory of your first date? 🌹"},
    {"type": "open",  "text": "What song do you think best describes your relationship, and why? 🎵"},
    {"type": "open",  "text": "What little thing does your partner do that makes you smile every time? 😊"},
    {"type": "open",  "text": "If you could relive one day you have spent together, which would it be and why?"},
    {"type": "open",  "text": "What dream or goal do you most want to achieve *together* in the next year? 🌟"},
    {"type": "open",  "text": "What is one thing you appreciate about your partner that you don't say enough?"},
    {"type": "open",  "text": "Describe your partner in exactly three words — and explain each one. ✨"},
    {"type": "open",  "text": "What is the silliest argument you have ever had, and can you laugh about it now? 😂"},
    {"type": "open",  "text": "Where is your dream destination to travel together, and what would you do there? ✈️"},
    {"type": "open",  "text": "What is a new hobby or activity you would love to try together? 🎨"},
    {"type": "open",  "text": "What dish or meal do you most associate with a happy moment together? 🍽️"},
    {"type": "open",  "text": "What moment made you first realise you were falling in love?"},
    {"type": "open",  "text": "What is something your partner does that still surprises you in the best way?"},
    {"type": "open",  "text": "If you could give your relationship a movie title, what would it be and why? 🎬"},
    {"type": "open",  "text": "What is the nicest compliment your partner has ever given you?"},
    {"type": "open",  "text": "How do you each show love differently, and how has that shaped your relationship?"},
    {"type": "open",  "text": "What tradition — big or tiny — have you created that is just yours? 🕯️"},
    {"type": "open",  "text": "What would the perfect lazy Sunday together look like for you?"},
    {"type": "open",  "text": "What has your relationship taught you about yourself?"},
    {"type": "open",  "text": "If you wrote a book about your love story, what would the opening line be? 📖"},
    {"type": "open",  "text": "What is one thing on your couple bucket list you haven't done yet? 🪣"},
    {"type": "open",  "text": "What is a small kindness your partner did recently that meant a lot to you?"},
    {"type": "open",  "text": "If your relationship had a theme song right now, what would it be?"},
    {"type": "open",  "text": "What inside joke never fails to make both of you laugh?"},
    {"type": "poll",  "text": "Do you and your partner have a song that is *truly* yours?",        "options": ["Yes, we do! 🎶", "Not really 🤷"]},
    {"type": "poll",  "text": "Have you ever written your partner a handwritten love letter?",      "options": ["Yes I have ✉️", "No, but I should 😅"]},
    {"type": "poll",  "text": "Do you remember the exact outfit your partner wore on your first date?", "options": ["Yes! 👀", "Absolutely not 😂"]},
    {"type": "poll",  "text": "Have you two ever slow-danced together — even in the kitchen?",     "options": ["Yes 💃🕺", "Not yet!"]},
    {"type": "poll",  "text": "Did you know early on that this relationship was special?",         "options": ["Yes, almost immediately 💫", "It grew on me over time 🌱"]},
    {"type": "poll",  "text": "Ideal date night? 🌙",                                             "options": ["Cozy night in 🛋️", "Night out on the town 🏙️"]},
    {"type": "poll",  "text": "Which do you prefer as a couple?",                                 "options": ["Spontaneous adventures 🎲", "Carefully planned trips 🗺️"]},
    {"type": "poll",  "text": "When you argue, which style is more *you*?",                       "options": ["Talk it out immediately 🗣️", "Need space first, then talk 🧘"]},
    {"type": "poll",  "text": "Ideal holiday together…",                                          "options": ["Beach & sunshine ☀️", "Mountains & hiking 🏔️"]},
    {"type": "poll",  "text": "Pick your couple vibe:",                                           "options": ["Homebody duo 🏠", "Always out exploring 🌍"]},
    {"type": "poll",  "text": "For anniversaries you prefer…",                                    "options": ["A meaningful gift 🎁", "A special experience 🎟️"]},
    {"type": "poll",  "text": "Morning couple or night-owl couple?",                              "options": ["Early birds ☀️🐦", "Night owls 🦉🌙"]},
    {"type": "poll",  "text": "Who is more likely to plan a surprise?",                           "options": ["Me! 🙋", "My partner 🙋"]},
    {"type": "poll",  "text": "Your love language is mostly…",                                    "options": ["Words & quality time 💬", "Acts of service & touch 🤝"]},
    {"type": "poll",  "text": "Movie night pick:",                                                "options": ["Romantic comedy 🍿❤️", "Thriller / action 🔫🎬"]},
]

# ══════════════════════════════════════════════════════════
#  COLOURS
# ══════════════════════════════════════════════════════════
PINK = discord.Colour.from_rgb(255, 105, 180)
MINT = discord.Colour.from_rgb(100, 200, 150)
GOLD = discord.Colour.from_rgb(255, 200, 50)

# ══════════════════════════════════════════════════════════
#  DATA HELPERS
# ══════════════════════════════════════════════════════════

def _load(path: str, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default

def _save(path: str, data) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# Question history
def load_history() -> list:        return _load(HISTORY_FILE, [])
def save_history(h: list) -> None: _save(HISTORY_FILE, h)

def pick_question(history: list) -> tuple[dict, int]:
    available = [i for i in range(len(QUESTIONS)) if i not in history]
    if not available:
        history.clear()
        save_history(history)
        available = list(range(len(QUESTIONS)))
    idx = random.choice(available)
    return QUESTIONS[idx], idx

# User data
def load_users() -> dict:          return _load(USER_DATA_FILE, {})
def save_users(u: dict) -> None:   _save(USER_DATA_FILE, u)

def get_user(users: dict, uid: int) -> dict:
    key = str(uid)
    if key not in users:
        users[key] = {
            "streak": 0,
            "last_answered": None,
            "total_answers": 0,
            "favourites": [],
            "anniversary": None,
        }
    return users[key]

def record_answer(uid: int) -> tuple[int, bool, str, str]:
    """Returns (streak, is_milestone, level_name, ascii_art)."""
    users = load_users()
    u = get_user(users, uid)
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

    if u["last_answered"] == today:
        lname, lart = get_level(u["streak"])
        return u["streak"], False, lname, lart

    u["streak"] = u["streak"] + 1 if u["last_answered"] == yesterday else 1
    u["last_answered"] = today
    u["total_answers"] += 1
    save_users(users)

    is_milestone = u["streak"] in MILESTONE_STREAKS
    lname, lart = get_level(u["streak"])
    return u["streak"], is_milestone, lname, lart

# Memories
def load_memories() -> dict:           return _load(MEMORIES_FILE, {})
def save_memories(m: dict) -> None:    _save(MEMORIES_FILE, m)

def add_memory(guild_id: int, uid: int, username: str, text: str) -> None:
    m = load_memories()
    key = str(guild_id)
    if key not in m:
        m[key] = []
    m[key].append({"uid": uid, "username": username, "text": text,
                   "date": datetime.date.today().isoformat()})
    save_memories(m)

def random_memory(guild_id: int) -> dict | None:
    m = load_memories()
    entries = m.get(str(guild_id), [])
    return random.choice(entries) if entries else None

# Partners
def load_partners() -> dict:           return _load(PARTNERS_FILE, {})
def save_partners(p: dict) -> None:    _save(PARTNERS_FILE, p)

def set_partner(uid: int, partner_id: int) -> None:
    p = load_partners()
    p[str(uid)] = partner_id
    p[str(partner_id)] = uid
    save_partners(p)

def get_partner(uid: int) -> int | None:
    return load_partners().get(str(uid))

# ══════════════════════════════════════════════════════════
#  EMBED BUILDERS
# ══════════════════════════════════════════════════════════

def build_poll_embed(q: dict) -> discord.Embed:
    e = discord.Embed(title="💑  Daily Couple Question", description=f"**{q['text']}**", colour=PINK)
    for i, opt in enumerate(q["options"]):
        e.add_field(name=f"{'🅰️' if i == 0 else '🅱️'}  {opt}", value="\u200b", inline=False)
    e.set_footer(text="React below to vote! • /answered to log your streak 🔥")
    return e

def build_open_embed(q: dict) -> discord.Embed:
    e = discord.Embed(title="💑  Daily Couple Question", description=f"**{q['text']}**", colour=PINK)
    e.set_footer(text="Reply in the thread below 💬 • /answered to log your streak 🔥")
    return e

def build_streak_embed(target: discord.User | discord.Member,
                       streak: int, total: int,
                       lname: str, lart: str,
                       anniversary: str | None) -> discord.Embed:
    e = discord.Embed(title=f"🐦  {target.display_name}'s Love Bird", colour=PINK)
    e.add_field(name="Level",           value=f"**{lname}**",                              inline=True)
    e.add_field(name="🔥 Streak",       value=f"**{streak} day{'s' if streak!=1 else ''}**", inline=True)
    e.add_field(name="📝 Total Answers", value=f"**{total}**",                              inline=True)
    e.add_field(name="\u200b",          value=f"```\n{lart}\n```",                         inline=False)

    nm = next_milestone(streak)
    if nm:
        e.add_field(name="Next level at",
                    value=f"**{nm}-day streak** — {nm - streak} day{'s' if nm-streak!=1 else ''} to go!",
                    inline=False)
    else:
        e.add_field(name="🏆 Max Level!", value="You've reached Eternal Dove — the highest tier!", inline=False)

    if anniversary:
        ann = datetime.date.fromisoformat(anniversary)
        today = datetime.date.today()
        next_ann = ann.replace(year=today.year)
        if next_ann < today:
            next_ann = next_ann.replace(year=today.year + 1)
        days_until = (next_ann - today).days
        e.add_field(name="💍 Anniversary",
                    value=f"{ann.strftime('%B %d')} — **{days_until} day{'s' if days_until!=1 else ''} away**",
                    inline=False)
    return e

# ══════════════════════════════════════════════════════════
#  BOT SETUP
# ══════════════════════════════════════════════════════════
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ══════════════════════════════════════════════════════════
#  SHARED SEND HELPER
# ══════════════════════════════════════════════════════════
async def _send_question(channel, q: dict):
    if q["type"] == "poll":
        msg = await channel.send(embed=build_poll_embed(q))
        await msg.add_reaction("🅰️")
        await msg.add_reaction("🅱️")
    else:
        msg = await channel.send(embed=build_open_embed(q))
        try:
            await msg.create_thread(name="💬 Answer here!", auto_archive_duration=1440)
        except discord.Forbidden:
            pass

# ══════════════════════════════════════════════════════════
#  DAILY TASK
# ══════════════════════════════════════════════════════════
@tasks.loop(time=datetime.time(hour=DAILY_HOUR, minute=DAILY_MINUTE, tzinfo=datetime.timezone.utc))
async def daily_question():
    channel = bot.get_channel(QUESTION_CHANNEL_ID)
    if channel is None:
        print(f"[ERROR] Channel {QUESTION_CHANNEL_ID} not found")
        return

    history = load_history()
    q, idx = pick_question(history)
    await _send_question(channel, q)
    history.append(idx)
    save_history(history)
    print(f"[Daily] #{idx}: {q['text'][:55]}…")

    # Anniversary celebrations
    users = load_users()
    today = datetime.date.today()
    for uid_str, udata in users.items():
        ann_str = udata.get("anniversary")
        if not ann_str:
            continue
        ann = datetime.date.fromisoformat(ann_str)
        if ann.month == today.month and ann.day == today.day:
            years = today.year - ann.year
            try:
                member = await channel.guild.fetch_member(int(uid_str))
                pid = get_partner(int(uid_str))
                mention2 = f" & <@{pid}>" if pid else ""
                await channel.send(
                    f"🎉 Happy Anniversary {member.mention}{mention2}! "
                    f"{'One whole year' if years == 1 else f'{years} incredible years'} together — "
                    f"here's to many more! 💍🎂"
                )
            except Exception:
                pass

# ══════════════════════════════════════════════════════════
#  PREFIX COMMANDS
# ══════════════════════════════════════════════════════════

@bot.command(name="question")
async def force_question(ctx):
    """!question — fire a question immediately (for testing)."""
    history = load_history()
    q, idx = pick_question(history)
    await _send_question(ctx.channel, q)
    history.append(idx)
    save_history(history)

# ══════════════════════════════════════════════════════════
#  SLASH COMMANDS
# ══════════════════════════════════════════════════════════

# ── /event ───────────────────────────────────────────────
@tree.command(name="event", description="Create a couple's event on the server 📅")
@app_commands.describe(name="Event name", date="YYYY-MM-DD", time="HH:MM (UTC, 24hr)",
                       description="Optional description", location="Optional location or link")
async def create_event(interaction: discord.Interaction, name: str, date: str, time: str,
                       description: str = "", location: str = "TBD"):
    await interaction.response.defer()
    try:
        start = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
            tzinfo=datetime.timezone.utc)
        end = start + datetime.timedelta(hours=2)
        event = await interaction.guild.create_scheduled_event(
            name=name, start_time=start, end_time=end,
            description=description or f"A couple's event: {name}",
            location=location, entity_type=discord.EntityType.external,
            privacy_level=discord.PrivacyLevel.guild_only,
        )
        e = discord.Embed(title="📅  Event Created!", description=f"**{event.name}**", colour=MINT)
        e.add_field(name="🗓️ When",  value=f"<t:{int(start.timestamp())}:F>", inline=False)
        e.add_field(name="📍 Where", value=location, inline=True)
        if description:
            e.add_field(name="📝 Notes", value=description, inline=False)
        e.set_footer(text="Tap 'Interested' on the event to get a reminder!")
        await interaction.followup.send(embed=e)
    except ValueError:
        await interaction.followup.send("⚠️ Use `YYYY-MM-DD` and `HH:MM`.", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("⚠️ I need **Manage Events** permission.", ephemeral=True)


# ── /answered ────────────────────────────────────────────
@tree.command(name="answered", description="Log that you answered today's question & grow your bird 🐦")
async def answered_cmd(interaction: discord.Interaction):
    uid = interaction.user.id
    streak, is_milestone, lname, lart = record_answer(uid)
    users = load_users()
    u = get_user(users, uid)

    embed = build_streak_embed(interaction.user, streak, u["total_answers"], lname, lart, u.get("anniversary"))
    if is_milestone:
        embed.colour = GOLD
        embed.description = f"🎉 **{streak}-day milestone!** Your bird just levelled up!"

    pid = get_partner(uid)
    content = f"<@{pid}> your partner just answered — go log yours too! 💕" if pid else None
    await interaction.response.send_message(content=content, embed=embed)


# ── /streak ──────────────────────────────────────────────
@tree.command(name="streak", description="View your streak and love bird 🐦")
@app_commands.describe(user="Whose streak to view (blank = yours)")
async def streak_cmd(interaction: discord.Interaction, user: discord.Member = None):
    target = user or interaction.user
    users = load_users()
    u = get_user(users, target.id)
    lname, lart = get_level(u["streak"])
    embed = build_streak_embed(target, u["streak"], u["total_answers"], lname, lart, u.get("anniversary"))
    await interaction.response.send_message(embed=embed)


# ── /setpartner ──────────────────────────────────────────
@tree.command(name="setpartner", description="Link yourself to your partner 💑")
@app_commands.describe(partner="Your partner's Discord account")
async def setpartner_cmd(interaction: discord.Interaction, partner: discord.Member):
    if partner.id == interaction.user.id:
        await interaction.response.send_message("You can't partner with yourself! 😅", ephemeral=True)
        return
    set_partner(interaction.user.id, partner.id)
    e = discord.Embed(title="💑  Partners Linked!",
                      description=f"{interaction.user.mention} & {partner.mention} are now paired.",
                      colour=PINK)
    e.set_footer(text="You'll both be pinged when either of you logs a streak.")
    await interaction.response.send_message(embed=e)


# ── /setanniversary ──────────────────────────────────────
@tree.command(name="setanniversary", description="Set your anniversary date 💍")
@app_commands.describe(date="Your anniversary in YYYY-MM-DD format")
async def setanniversary_cmd(interaction: discord.Interaction, date: str):
    try:
        ann = datetime.date.fromisoformat(date)
    except ValueError:
        await interaction.response.send_message("⚠️ Use `YYYY-MM-DD` (e.g. `2021-06-14`).", ephemeral=True)
        return
    users = load_users()
    u = get_user(users, interaction.user.id)
    u["anniversary"] = ann.isoformat()
    save_users(users)
    today = datetime.date.today()
    next_ann = ann.replace(year=today.year)
    if next_ann < today:
        next_ann = next_ann.replace(year=today.year + 1)
    days_until = (next_ann - today).days
    await interaction.response.send_message(
        f"💍 Anniversary set to **{ann.strftime('%B %d, %Y')}**!\n"
        f"Next anniversary in **{days_until} day{'s' if days_until != 1 else ''}** — I'll celebrate with you! 🎉",
        ephemeral=True,
    )


# ── /remember ────────────────────────────────────────────
@tree.command(name="remember", description="Add a memory to your couple's memory jar 🫙")
@app_commands.describe(memory="The memory to save (e.g. 'Our first trip to Paris')")
async def remember_cmd(interaction: discord.Interaction, memory: str):
    add_memory(interaction.guild_id, interaction.user.id, interaction.user.display_name, memory)
    e = discord.Embed(title="🫙  Memory Saved!", description=f'*"{memory}"*', colour=MINT)
    e.set_footer(text=f"Added by {interaction.user.display_name} • /recall to relive a memory")
    await interaction.response.send_message(embed=e)


# ── /recall ──────────────────────────────────────────────
@tree.command(name="recall", description="Pull a random memory from the memory jar 🫙")
async def recall_cmd(interaction: discord.Interaction):
    mem = random_memory(interaction.guild_id)
    if not mem:
        await interaction.response.send_message(
            "The memory jar is empty! Use `/remember` to add your first memory. 🫙", ephemeral=True)
        return
    e = discord.Embed(title="🫙  A Memory from the Jar", description=f'*"{mem["text"]}"*', colour=PINK)
    e.set_footer(text=f"Saved by {mem['username']} on {mem['date']}")
    await interaction.response.send_message(embed=e)


# ── /dateidea ────────────────────────────────────────────
@tree.command(name="dateidea", description="Get a random date idea 🌙")
@app_commands.describe(vibe="Pick a vibe, or leave blank for a surprise")
@app_commands.choices(vibe=[
    app_commands.Choice(name="Cozy 🛋️",        value="cozy"),
    app_commands.Choice(name="Adventurous 🏔️", value="adventurous"),
    app_commands.Choice(name="Cheap 💸",        value="cheap"),
    app_commands.Choice(name="Fancy ✨",         value="fancy"),
])
async def dateidea_cmd(interaction: discord.Interaction, vibe: app_commands.Choice[str] = None):
    key = vibe.value if vibe else random.choice(list(DATE_IDEAS.keys()))
    idea = random.choice(DATE_IDEAS[key])
    e = discord.Embed(title=f"🌙  Date Idea — {key.capitalize()}", description=idea, colour=PINK)
    e.set_footer(text="Run /dateidea again for another idea!")
    await interaction.response.send_message(embed=e)


# ── /addquestion ─────────────────────────────────────────
@tree.command(name="addquestion", description="Add a custom question to the daily rotation 💬")
@app_commands.describe(question="Your question", is_poll="Is this a two-option poll?",
                       option_a="First option (polls only)", option_b="Second option (polls only)")
async def addquestion_cmd(interaction: discord.Interaction, question: str,
                          is_poll: bool = False, option_a: str = "", option_b: str = ""):
    if is_poll and (not option_a or not option_b):
        await interaction.response.send_message(
            "⚠️ Provide both `option_a` and `option_b` for a poll.", ephemeral=True)
        return
    if is_poll:
        QUESTIONS.append({"type": "poll", "text": question, "options": [option_a, option_b]})
    else:
        QUESTIONS.append({"type": "open", "text": question})
    e = discord.Embed(title="✅  Question Added!",
                      description=f'**"{question}"** is now in the rotation.',
                      colour=MINT)
    if is_poll:
        e.add_field(name="🅰️", value=option_a, inline=True)
        e.add_field(name="🅱️", value=option_b, inline=True)
    e.set_footer(text=f"Added by {interaction.user.display_name} • Total questions: {len(QUESTIONS)}")
    await interaction.response.send_message(embed=e)


# ── /status ──────────────────────────────────────────────
@tree.command(name="status", description="Show question bank stats 📊")
async def status_cmd(interaction: discord.Interaction):
    history = load_history()
    remaining = len(QUESTIONS) - len(history)
    await interaction.response.send_message(
        f"📊 **Question bank**\n"
        f"• Total: **{len(QUESTIONS)}**  •  Asked: **{len(history)}**  •  Remaining: **{remaining}**\n"
        f"Resets automatically once all questions are used.",
        ephemeral=True,
    )

# ══════════════════════════════════════════════════════════
#  ON READY
# ══════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅  {bot.user} online (ID: {bot.user.id})")
    try:
        synced = await tree.sync()
        print(f"✅  {len(synced)} slash command(s) synced")
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
    daily_question.start()
    print(f"✅  Daily question at {DAILY_HOUR:02d}:{DAILY_MINUTE:02d} UTC")

# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════
bot.run(TOKEN)