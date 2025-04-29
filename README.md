# 🃏 Shuffle And Slay
Single Player Card-Based Dungeon Crawler Bot for Discord.

Played entirely through a Discord chat. Draw from a deck of custom-modified playing cards to battle monsters, heal with potions, equip weapons, and survive the dungeon — or die trying.

This bot was built for fun, strategy, and replayability. It offers a single-player adventure with minimal setup and fast gameplay.

# 🕹️ How to Play

Once the bot is running, go to a channel named #shuffle-and-slay and type:

!start

You'll be prompted to draw cards from a dungeon deck. Each card represents either:

A Monster (Spades or Clubs): Fight or take damage.

A Potion (Hearts): Heals you.

A Weapon (Diamonds): Equip to reduce future damage.

Strategically choose whether to fight with fists, use a weapon, equip new weapons, or heal.

Each action is triggered via buttons — no typing needed once the game starts!

![Banner](https://i.postimg.cc/qv5PS92Y/Play-Screen.png)

# 📋 Game Rules
Use **!rules** to view the rules in the #shuffle-and-slay channel.

Basic Mechanics:

Each "dungeon room" is a hand of 4 cards.

You may only deal new cards when 1 card remains.

Weapons degrade: If you attack a card lower than your last monster kill, you can no longer attack higher ones.

Potions heal, but you can only use 1 per dungeon room.

You may flee to avoid a dangerous room, but only when it's full and not consecutively.

Death is permanent — health does not regenerate unless you heal.

# 🛠️ Installation
1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set your Discord bot token in the code: `bot.run("YOUR_BOT_TOKEN")`
4. Run the bot: `python shuffle_and_slay.py`

# 🔧 Requirements
- Python 3.10+
- discord.py 2.3+
- A Discord bot token and bot invited to your server


# 📜 License
This project is open-source and released under the MIT License.
Feel free to modify, share, or fork it!

**App Icon**: AI-generated with assistance from OpenAI's ChatGPT. Free to use and distribute under the same license as this project.

This project was developed with the assistance of OpenAI's ChatGPT.


# ❤️ Contributing
If you find a bug or have an idea, feel free to open an issue.

