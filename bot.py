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
    {"type": "open",  "text": "What is the first thing you noticed about your partner when you met? 👀"},
    {"type": "open",  "text": "What does a perfect morning together look like for you? ☀️"},
    {"type": "open",  "text": "What is one thing your partner does that you secretly find adorable? 🥹"},
    {"type": "open",  "text": "If you could only keep one photo of the two of you, which moment would it capture?"},
    {"type": "open",  "text": "What is the kindest thing a stranger has ever witnessed you do for each other?"},
    {"type": "open",  "text": "What is something you do together that recharges you both? 🔋"},
    {"type": "open",  "text": "What is a fear you have overcome because of your partner's support? 💪"},
    {"type": "open",  "text": "What is a place that feels special to your relationship and why?"},
    {"type": "open",  "text": "What is the funniest thing that has ever happened to you two on a date? 😂"},
    {"type": "open",  "text": "If you could send your partner a message they would find at a random moment in the future, what would it say? 💌"},
    {"type": "open",  "text": "What is something you have taught each other without even trying?"},
    {"type": "open",  "text": "What holiday or celebration means the most to you as a couple and why? 🎉"},
    {"type": "open",  "text": "What is a small ritual you have that makes an ordinary day feel special?"},
    {"type": "open",  "text": "If you could describe your relationship as a type of weather, what would it be and why? 🌤️"},
    {"type": "open",  "text": "What is something your partner said that you will never forget?"},
    {"type": "open",  "text": "What is the best piece of relationship advice you have ever received?"},
    {"type": "open",  "text": "What is a skill or talent your partner has that you deeply admire? ✨"},
    {"type": "open",  "text": "What was the moment you knew you could fully trust your partner?"},
    {"type": "open",  "text": "How has your partner changed your life for the better?"},
    {"type": "open",  "text": "What is something you used to do alone that is now better because you do it together?"},
    {"type": "open",  "text": "What is the most thoughtful gift your partner has ever given you? 🎁"},
    {"type": "open",  "text": "If your relationship were a colour, what would it be and why? 🎨"},
    {"type": "open",  "text": "What is something about your future together that genuinely excites you? 🌟"},
    {"type": "open",  "text": "What is a moment where your partner made you feel truly seen and understood?"},
    {"type": "open",  "text": "What is the most spontaneous thing you have ever done together? 🎲"},
    {"type": "open",  "text": "What is a movie, book, or show that feels like it was made for your relationship? 🎬"},
    {"type": "open",  "text": "If you could go back and relive your first meeting, what would you do differently?"},
    {"type": "open",  "text": "What is something your partner worries about that you wish you could take away?"},
    {"type": "open",  "text": "What is a goal your partner has that you are their biggest cheerleader for? 📣"},
    {"type": "open",  "text": "What is the most romantic place you have ever been together? 🌹"},
    {"type": "open",  "text": "What does home feel like to you, and does your partner fit into that feeling?"},
    {"type": "open",  "text": "What is something you both disagree on but have learned to respect? 🤝"},
    {"type": "open",  "text": "What is a personality trait of your partner that took you time to fully appreciate?"},
    {"type": "open",  "text": "If you could plan the perfect week away together, where would you go and what would you do? ✈️"},
    {"type": "open",  "text": "What is a challenge you have faced together that made you stronger as a couple? 💪"},
    {"type": "open",  "text": "What is something that always makes your partner laugh without fail?"},
    {"type": "open",  "text": "What is a compliment you give your partner in your head but should say out loud more often?"},
    {"type": "open",  "text": "What is the most fun you have ever had spending very little money together? 💸"},
    {"type": "open",  "text": "What is a dream you both share that you have never told anyone else?"},
    {"type": "open",  "text": "What does your partner do when they think no one is watching that you absolutely love?"},
    {"type": "open",  "text": "What is something new you learned about your partner in the last few months?"},
    {"type": "open",  "text": "If you could name a star after a moment in your relationship, which moment would it be? ⭐"},
    {"type": "open",  "text": "What is a song that takes you straight back to a specific memory with your partner? 🎵"},
    {"type": "open",  "text": "What is something your partner does when you are sad that helps more than anything else?"},
    {"type": "open",  "text": "If your relationship had a mascot, what would it be and why? 🐾"},
    {"type": "open",  "text": "What is a way your partner shows love that does not involve words?"},
    {"type": "open",  "text": "What is the best decision you ever made as a couple?"},
    {"type": "open",  "text": "What is something you are looking forward to experiencing together for the first time? 🎟️"},
    {"type": "open",  "text": "What is something small your partner does every day that you would miss the most?"},
    {"type": "open",  "text": "If you wrote your partner a thank you note today, what would be the main thing you thanked them for?"},
    {"type": "open",  "text": "What is a habit of your partner that you have picked up without realising?"},
    {"type": "open",  "text": "What is the most beautiful thing about the way your partner loves you?"},
    {"type": "open",  "text": "What is a place on your shared bucket list that you keep saying you will visit one day? 🗺️"},
    {"type": "open",  "text": "What is the longest you have gone without seeing each other, and how did it feel?"},
    {"type": "open",  "text": "What food or drink do you now associate with your relationship? ☕"},
    {"type": "open",  "text": "What is a version of yourself that your partner helped bring out?"},
    {"type": "open",  "text": "What is the most creative date you have ever planned or been taken on?"},
    {"type": "open",  "text": "If your partner gave a speech about you, what do you hope they would say?"},
    {"type": "open",  "text": "What is a value you both share that you think is the foundation of your relationship?"},
    {"type": "open",  "text": "What is something your partner is really good at that you brag about to others?"},
    {"type": "open",  "text": "What does a quiet evening in with your partner look like at its very best? 🕯️"},
    {"type": "open",  "text": "What is a time your partner surprised you in a way you did not expect at all?"},
    {"type": "open",  "text": "If your relationship had a tagline like a movie poster, what would it say?"},
    {"type": "open",  "text": "What is the most meaningful conversation you have ever had together?"},
    {"type": "open",  "text": "What is something about your partner that you fall in love with over and over again?"},
    {"type": "open",  "text": "What is the silliest nickname you have for each other and how did it start?"},
    {"type": "open",  "text": "If you could freeze one ordinary moment from this past year, which would it be?"},
    {"type": "open",  "text": "What has being in this relationship shown you about what love actually means?"},
    {"type": "open",  "text": "What is something you want to make sure you never take for granted about your partner?"},
    {"type": "open",  "text": "What is the most unexpected thing you have in common? 🤔"},
    {"type": "open",  "text": "What is a dream you had before this relationship that has changed because of it?"},
    {"type": "open",  "text": "What is something about your partner that makes you feel safe? 🫂"},
    {"type": "open",  "text": "What is the most beautiful place you have ever watched a sunset or sunrise together? 🌅"},
    {"type": "open",  "text": "What is a personality trait of yours that your partner has always embraced without question?"},
    {"type": "open",  "text": "What is the most fun you have had doing something completely ordinary together?"},
    {"type": "open",  "text": "What is something you would love to learn together as a couple? 📚"},
    {"type": "open",  "text": "What is a moment from early in your relationship that still makes you smile?"},
    {"type": "open",  "text": "What is one way your relationship is different from anything you imagined love would be?"},
    {"type": "open",  "text": "What is something your partner has forgiven you for that meant the world to you?"},
    {"type": "open",  "text": "What is an adventure you want to go on before the end of this year? 🏕️"},
    {"type": "open",  "text": "What is something you love doing for your partner just because it makes them happy?"},
    {"type": "open",  "text": "What is the most romantic gesture you have ever seen in real life — from each other or anyone else? 💕"},
    {"type": "open",  "text": "If you could redesign your first date knowing what you know now, what would you change?"},
    {"type": "open",  "text": "What is a hidden talent of your partner that not many people know about?"},
    {"type": "open",  "text": "What is something that used to seem important in a relationship that no longer matters to you?"},
    {"type": "open",  "text": "What is a time your partner showed up for you in a way you really needed?"},
    {"type": "open",  "text": "If you had to describe your love story in three emojis, which would you pick and why?"},
    {"type": "open",  "text": "What is something about your relationship that you think other people admire?"},
    {"type": "open",  "text": "What is a way you have grown individually because of this relationship?"},
    {"type": "open",  "text": "What is a time you laughed so hard together that you could not stop? 😂"},
    {"type": "open",  "text": "What is something your partner does to take care of themselves that you find really attractive?"},
    {"type": "open",  "text": "What is a small luxury you love sharing together? ✨"},
    {"type": "open",  "text": "What is a lesson your relationship has taught you about communication?"},
    {"type": "open",  "text": "What is a tradition from your own family that you want to carry into your life together?"},
    {"type": "open",  "text": "What is a way your partner challenges you to be better without even trying?"},
    {"type": "open",  "text": "What is something you are both terrible at but do together anyway? 😅"},
    {"type": "open",  "text": "What is a piece of music that means something special to your relationship? 🎶"},
    {"type": "open",  "text": "What is the most generous thing your partner has ever done for someone else?"},
    {"type": "open",  "text": "What is something your partner does in the morning that you love? ☀️"},
    {"type": "open",  "text": "What is a way you knew this relationship was different from others you had before?"},
    {"type": "open",  "text": "What is something your partner has introduced you to that you now love? 🍜"},
    {"type": "open",  "text": "What is the most meaningful place you have visited together? 📍"},
    {"type": "open",  "text": "What is a future milestone you are most excited to reach together? 🏠"},
    {"type": "open",  "text": "What is something you never have to explain to your partner because they just get it?"},
    {"type": "poll",  "text": "Who takes longer to get ready?",                                   "options": ["Me 🪞", "My partner 🪞"]},
    {"type": "poll",  "text": "Who is the better cook?",                                          "options": ["Me 👨‍🍳", "My partner 👨‍🍳"]},
    {"type": "poll",  "text": "Who said 'I love you' first?",                                     "options": ["I did 💬", "My partner did 💬"]},
    {"type": "poll",  "text": "Who is more likely to cry at a sad movie?",                        "options": ["Me 😭", "My partner 😭"]},
    {"type": "poll",  "text": "Who is the better gift giver?",                                    "options": ["Me 🎁", "My partner 🎁"]},
    {"type": "poll",  "text": "Who is more likely to get lost?",                                  "options": ["Me 🗺️", "My partner 🗺️"]},
    {"type": "poll",  "text": "Who hogs the blanket?",                                            "options": ["Me 🛌", "My partner 🛌"]},
    {"type": "poll",  "text": "Who is messier?",                                                  "options": ["Me 🧹", "My partner 🧹"]},
    {"type": "poll",  "text": "Who is more likely to stay up too late?",                          "options": ["Me 🦉", "My partner 🦉"]},
    {"type": "poll",  "text": "Who is more likely to suggest a spontaneous trip?",                "options": ["Me ✈️", "My partner ✈️"]},
    {"type": "poll",  "text": "Who remembers important dates better?",                            "options": ["Me 📅", "My partner 📅"]},
    {"type": "poll",  "text": "Who is more stubborn?",                                            "options": ["Me 😤", "My partner 😤"]},
    {"type": "poll",  "text": "Who apologises first after an argument?",                          "options": ["Me 🙏", "My partner 🙏"]},
    {"type": "poll",  "text": "Who is more affectionate in public?",                             "options": ["Me 💑", "My partner 💑"]},
    {"type": "poll",  "text": "Who snacks more?",                                                 "options": ["Me 🍿", "My partner 🍿"]},
    {"type": "poll",  "text": "Who picks the restaurant?",                                        "options": ["Me 🍽️", "My partner 🍽️"]},
    {"type": "poll",  "text": "Who is more likely to plan ahead?",                               "options": ["Me 📋", "My partner 📋"]},
    {"type": "poll",  "text": "Who is more patient?",                                             "options": ["Me 😌", "My partner 😌"]},
    {"type": "poll",  "text": "Who is the better driver?",                                        "options": ["Me 🚗", "My partner 🚗"]},
    {"type": "poll",  "text": "Who takes more photos?",                                           "options": ["Me 📸", "My partner 📸"]},
    {"type": "poll",  "text": "Who is more likely to be running late?",                           "options": ["Me ⏰", "My partner ⏰"]},
    {"type": "poll",  "text": "Who falls asleep on the sofa more?",                              "options": ["Me 😴", "My partner 😴"]},
    {"type": "poll",  "text": "Who makes the other laugh more?",                                  "options": ["Me 😂", "My partner 😂"]},
    {"type": "poll",  "text": "Who is more likely to start a new hobby and abandon it?",          "options": ["Me 🎸", "My partner 🎸"]},
    {"type": "poll",  "text": "Who worries more?",                                                "options": ["Me 😟", "My partner 😟"]},
    {"type": "poll",  "text": "Ideal weekend: stay in or go out?",                               "options": ["Stay in 🏠", "Go out 🌍"]},
    {"type": "poll",  "text": "Do you think soulmates are real?",                                 "options": ["Yes 💫", "Not quite — but close enough 🌱"]},
    {"type": "poll",  "text": "Coffee or tea as a couple?",                                       "options": ["Coffee ☕", "Tea 🍵"]},
    {"type": "poll",  "text": "Do you have a favourite season you both share?",                   "options": ["Yes we do 🍂", "We disagree 😅"]},
    {"type": "poll",  "text": "Pets or no pets in your ideal home?",                              "options": ["Yes to pets 🐾", "No pets 🏡"]},
    {"type": "poll",  "text": "City life or countryside?",                                        "options": ["City 🏙️", "Countryside 🌿"]},
    {"type": "poll",  "text": "Do you think you and your partner balance each other out?",        "options": ["Totally ⚖️", "We're more similar than different 🪞"]},
    {"type": "poll",  "text": "Sweet or savoury when you're snacking together?",                  "options": ["Sweet 🍫", "Savoury 🧀"]},
    {"type": "poll",  "text": "Do you have a shared TV show you are always rewatching?",          "options": ["Yes always 📺", "We can never agree 😂"]},
    {"type": "poll",  "text": "Has your partner met your whole family?",                          "options": ["Yes 👨‍👩‍👧", "Not all of them yet"]},
    {"type": "poll",  "text": "Do you think you two bring out the best in each other?",           "options": ["Absolutely 💪", "We're working on it 🌱"]},
    {"type": "poll",  "text": "Pool or ocean?",                                                   "options": ["Pool 🏊", "Ocean 🌊"]},
    {"type": "poll",  "text": "Do you have a shared playlist?",                                   "options": ["Yes 🎶", "No but we should 😅"]},
    {"type": "poll",  "text": "Would you rather revisit your favourite trip or go somewhere brand new?", "options": ["Revisit 🔁", "Somewhere new 🗺️"]},
    {"type": "poll",  "text": "Do you both agree on how tidy the home should be?",               "options": ["Pretty much 🧹", "Not at all 😂"]},
    {"type": "poll",  "text": "Window seat or aisle seat when you fly together?",                 "options": ["Window 🪟", "Aisle 🚶"]},
    {"type": "poll",  "text": "Has your relationship ever survived a long distance period?",      "options": ["Yes it has 💌", "No we've always been close 🏡"]},
    {"type": "poll",  "text": "Do you think you have a healthier relationship than most?",        "options": ["Yes honestly 💚", "We have our moments 😅"]},
    {"type": "poll",  "text": "Hot holiday or cold adventure?",                                   "options": ["Hot ☀️", "Cold ❄️"]},
    {"type": "poll",  "text": "Have you ever laughed during a serious argument?",                 "options": ["Yes and it helped 😂", "No we keep it serious 😤"]},
    {"type": "poll",  "text": "Do you think you communicate well as a couple?",                  "options": ["Yes really well 💬", "It's something we work at 🌱"]},
    {"type": "poll",  "text": "Do you have a go-to comfort food you both love?",                  "options": ["Yes definitely 🍜", "We have different ones 🍕"]},
    {"type": "poll",  "text": "Have you cried happy tears because of your partner?",              "options": ["Yes 🥹", "Not yet but maybe one day"]},
    {"type": "poll",  "text": "Would you rather have a big wedding or a small intimate one?",     "options": ["Big celebration 🎊", "Small and intimate 🕯️"]},
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
#  SCHEDULED NOTES
#  /writenote  — write a note to your partner for later
#  /mynotes    — see your pending outgoing notes
#  check_notes — background task that delivers on time
# ══════════════════════════════════════════════════════════

NOTES_FILE = "scheduled_notes.json"

def load_notes() -> list:        return _load(NOTES_FILE, [])
def save_notes(n: list) -> None: _save(NOTES_FILE, n)


@tree.command(name="writenote", description="Write a secret note to your partner, delivered at a time you choose 💌")
@app_commands.describe(
    message  = "Your note to them",
    date     = "Delivery date in YYYY-MM-DD format",
    time     = "Delivery time in HH:MM (24hr UTC)",
    to       = "Who to send it to — defaults to your linked partner",
)
async def writenote_cmd(interaction: discord.Interaction,
                        message: str,
                        date: str,
                        time: str,
                        to: discord.Member = None):

    # resolve recipient
    recipient_id = to.id if to else get_partner(interaction.user.id)
    if not recipient_id:
        await interaction.response.send_message(
            "⚠️ No recipient found. Either use `/setpartner` first or specify someone with the `to` option.",
            ephemeral=True)
        return

    try:
        deliver_at = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M").replace(
            tzinfo=datetime.timezone.utc)
    except ValueError:
        await interaction.response.send_message(
            "⚠️ Bad format. Use `YYYY-MM-DD` for date and `HH:MM` for time.", ephemeral=True)
        return

    if deliver_at <= datetime.datetime.now(datetime.timezone.utc):
        await interaction.response.send_message(
            "⚠️ That time is already in the past! Pick a future date and time.", ephemeral=True)
        return

    notes = load_notes()
    notes.append({
        "from_id":      interaction.user.id,
        "from_name":    interaction.user.display_name,
        "to_id":        recipient_id,
        "guild_id":     interaction.guild_id,
        "channel_id":   interaction.channel_id,
        "message":      message,
        "deliver_at":   deliver_at.isoformat(),
        "delivered":    False,
    })
    save_notes(notes)

    # confirmation (only the sender sees this)
    e = discord.Embed(
        title="💌  Note Scheduled!",
        description=f"*\"{message}\"*",
        colour=PINK,
    )
    e.add_field(name="📬 To",         value=f"<@{recipient_id}>",                       inline=True)
    e.add_field(name="🕐 Delivers at", value=f"<t:{int(deliver_at.timestamp())}:F>",    inline=True)
    e.add_field(name="⏳ That's in",   value=f"<t:{int(deliver_at.timestamp())}:R>",    inline=False)
    e.set_footer(text="They won't know until it arrives 🤫")
    await interaction.response.send_message(embed=e, ephemeral=True)


@tree.command(name="mynotes", description="See your pending scheduled notes 📬")
async def mynotes_cmd(interaction: discord.Interaction):
    notes = load_notes()
    pending = [n for n in notes
               if n["from_id"] == interaction.user.id and not n["delivered"]]

    if not pending:
        await interaction.response.send_message(
            "You have no pending notes. Use `/writenote` to schedule one! 💌", ephemeral=True)
        return

    e = discord.Embed(title="💌  Your Pending Notes", colour=PINK)
    for i, n in enumerate(pending, 1):
        dt = datetime.datetime.fromisoformat(n["deliver_at"])
        preview = n["message"][:60] + ("…" if len(n["message"]) > 60 else "")
        e.add_field(
            name=f"Note {i} → <@{n['to_id']}>",
            value=f"*\"{preview}\"*\n🕐 <t:{int(dt.timestamp())}:F> (<t:{int(dt.timestamp())}:R>)",
            inline=False,
        )
    e.set_footer(text="Only you can see this")
    await interaction.response.send_message(embed=e, ephemeral=True)


@tasks.loop(minutes=1)
async def check_notes():
    notes = load_notes()
    now   = datetime.datetime.now(datetime.timezone.utc)
    dirty = False

    for note in notes:
        if note["delivered"]:
            continue
        deliver_at = datetime.datetime.fromisoformat(note["deliver_at"])
        if now < deliver_at:
            continue

        # time to deliver
        try:
            channel = bot.get_channel(note["channel_id"]) or bot.get_channel(QUESTION_CHANNEL_ID)

            e = discord.Embed(
                title="💌  You have a note!",
                description=f"*\"{note['message']}\"*",
                colour=PINK,
            )
            e.set_author(name=f"From {note['from_name']}")
            e.set_footer(text=f"Written for this moment — delivered just for you 🕊️")
            await channel.send(content=f"<@{note['to_id']}>", embed=e)
            note["delivered"] = True
            dirty = True
        except Exception as ex:
            print(f"[Notes] Failed to deliver note: {ex}")

    if dirty:
        save_notes(notes)

# ══════════════════════════════════════════════════════════
#  ON READY
# ══════════════════════════════════════════════════════════
@bot.event
async def on_ready():
    print(f"✅  {bot.user} online (ID: {bot.user.id})")
    
    # 1. Sync slash commands safely
    try:
        synced = await tree.sync()
        print(f"✅  {len(synced)} slash command(s) synced")
    except Exception as e:
        print(f"[ERROR] Sync failed: {e}")
    
    # 2. Start daily_question safely by checking if it's already running
    if not daily_question.is_running():
        daily_question.start()
        print(f"✅  Daily question loop started (Scheduled for {DAILY_HOUR:02d}:{DAILY_MINUTE:02d} UTC)")
    else:
        print("ℹ️  Daily question loop already running.")

    # 3. Start check_notes safely
    if not check_notes.is_running():
        check_notes.start()
        print("✅  Check notes loop started")
    else:
        print("ℹ️  Check notes loop already running.")

# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════
bot.run(TOKEN)
