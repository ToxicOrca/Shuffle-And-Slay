import discord
from discord.ext import commands
import random


# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Define suits and emojis
suits = ['Spades', 'Clubs', 'Hearts', 'Diamonds']
suit_emojis = {
    'Spades': '♠️',
    'Clubs': '♣️',
    'Hearts': '♥️',
    'Diamonds': '♦️'
}

# Define the valid cards for each suit
# Deck has 43 cards, no red jack up face cards, no Jokers
valid_cards = {
    'Spades': ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'],
    'Clubs': ['2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14'],
    'Hearts': ['2', '3', '4', '5', '6', '7', '8', '9', '10'],
    'Diamonds': ['2', '3', '4', '5', '6', '7', '8', '9', '10']
}

# Deck has 43 cards, no red jack up face cards, no Jokers
# Create deck (full deck with suits and values)
def create_deck():
    deck = []
    for suit in suits:
        for card in valid_cards[suit]:
            deck.append((card, suit))
    return deck

# Convert card value to readable name
# This is probably pointless and could have been done above. but it works so oh well. 
def card_name(card_value):
    if card_value == '11':
        return 'Jack'
    elif card_value == '12':
        return 'Queen'
    elif card_value == '13':
        return 'King'
    elif card_value == '14':
        return 'Ace'
    else:
        return card_value

# Storage for player health and dungeon, including deck state
player_data = {}


# EquipButton class (OUTSIDE of DungeonView)
class EquipButton(discord.ui.Button):
    def __init__(self, index, label, style=discord.ButtonStyle.secondary, row=1):
        super().__init__(label=label, style=style, row=row) # <-- Forces into row 1
        self.index = index  # Which card in the dungeon this button equips

    async def callback(self, interaction: discord.Interaction):
        view: DungeonView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True, delete_after=4)
            return
            
        user_id = view.user_id
        # Get the card that this button represents
        if self.index >= len(player_data[user_id]['dungeon']):
            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message("❌ That card is no longer available!", ephemeral=True, delete_after=4)
            else:
                await interaction.response.defer()   
            return
        
        # REMOVED AS IT WAS BAD
        # New check: Prevent actions when only 1 card is left
#        if len(player_data[user_id]['dungeon']) <= 1:
#            if not player_data[user_id].get('has_played_before', False):
#                await interaction.response.send_message("❌ You only have 1 card left — you must DEAL before acting!", ephemeral=True, delete_after=4)
#            else:
#                await interaction.response.defer() 
#            return

        
        card_value, suit = player_data[user_id]['dungeon'][self.index]

        # --- POTION Mode ---
        if player_data[user_id]['attack_mode'] == "potion":
            if suit != 'Hearts':
                if not player_data[user_id].get('has_played_before', False):
                    await interaction.response.send_message(
                        "❌ You can only use Hearts (♥️) as potions!",
                        ephemeral=True,
                        delete_after=4
                    )
                else:
                    await interaction.response.defer()
                return

            if player_data[user_id].get('potion_used', False):
                # Already used a potion — discard Heart without healing
                del player_data[user_id]['dungeon'][self.index]
                player_data[user_id]['attack_mode'] = None
                # ✅ Check for WIN condition if everything is clear
                if player_data[user_id]['health'] > 0 and len(player_data[user_id]['deck']) == 0 and len(player_data[user_id]['dungeon']) == 0:
                    if await view.check_win(interaction):
                        return


                # ✅ EARLY DEATH CHECK
                if player_data[user_id]['health'] <= 0:
                    await view.update_display(interaction)
                    return

                # ✅ WIN CHECK
                if await view.check_win(interaction):
                    return

                await view.update_display(interaction)

                if not player_data[user_id].get('has_played_before', False):
                    await interaction.followup.send(
                        f"💔 You discarded {card_name(card_value)} {suit_emojis[suit]} (already used your potion!)",
                        ephemeral=True
                    )
                else:
                    await interaction.response.defer()
                return

            # First time using a potion
            heal_amount = int(card_value) if card_value.isdigit() else {
                'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
            }[card_name(card_value)]

            player_data[user_id]['health'] = min(20, player_data[user_id]['health'] + heal_amount)
            player_data[user_id]['potion_used'] = True

            del player_data[user_id]['dungeon'][self.index]
            player_data[user_id]['attack_mode'] = None

            # ✅ EARLY DEATH CHECK (theoretically unnecessary here, but good structure)
            if player_data[user_id]['health'] <= 0:
                await view.update_display(interaction)
                return

            # ✅ WIN CHECK
            if await view.check_win(interaction):
                return

            await view.update_display(interaction)

            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message(
                    f"💖 You used a Potion and healed {heal_amount} health!",
                    ephemeral=True,
                    delete_after=4
                )
            else:
                await interaction.response.defer()
            return



        # --- FIST Mode ---
        elif player_data[user_id]['attack_mode'] == "fist":
            fist_power = 0

            card_number = int(card_value) if card_value.isdigit() else {
                'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
            }[card_name(card_value)]
            
            damage = card_number - fist_power
            player_data[user_id]['health'] = max(0, player_data[user_id]['health'] - damage)

            del player_data[user_id]['dungeon'][self.index]
            player_data[user_id]['attack_mode'] = None

            # ✅ Check for WIN condition if everything is clear
            if player_data[user_id]['health'] > 0 and len(player_data[user_id]['deck']) == 0 and len(player_data[user_id]['dungeon']) == 0:
                if await view.check_win(interaction):
                    return


            # ✅ Handle player death early to avoid crashing update_display
            if player_data[user_id]['health'] <= 0:
                await view.update_display(interaction)
                return

            # ✅ Check for win only if alive
            if await view.check_win(interaction):
                return

            await view.update_display(interaction)

            if not player_data[user_id].get('has_played_before', False):
                await interaction.followup.send(f"👊 You punched and took {damage} damage!", ephemeral=True, delete_after=4)
            else:
                await interaction.response.defer()
            return

        
        # --- WEAPON Mode ---
        elif player_data[user_id]['attack_mode'] == "weapon":
            weapon_power = player_data[user_id]['current_weapon_power']
            last_kill = player_data[user_id]['last_kill']

            if weapon_power is None:
                if not player_data[user_id].get('has_played_before', False):
                    await interaction.response.send_message("❌ You have no weapon equipped!", ephemeral=True, delete_after=4)
                else:
                    await interaction.response.defer()
                return

            card_number = int(card_value) if card_value.isdigit() else {
                'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
            }[card_name(card_value)]

            # --- Last kill limitation ---
            if last_kill:
                last_kill_value = int(last_kill[0]) if last_kill[0].isdigit() else {
                    'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
                }[card_name(last_kill[0])]

                if card_number >= last_kill_value:
                    if not player_data[user_id].get('has_played_before', False):
                        await interaction.response.send_message(
                            "❌ Your weapon is too weak to attack this monster! Use your fists instead!",
                            ephemeral=True,
                            delete_after=4
                        )
                    else:
                        await interaction.response.defer()
                    return  # IMPORTANT: cannot continue if too strong

            # --- Normal allowed weapon attack ---
            if weapon_power >= card_number:
                if not player_data[user_id].get('has_played_before', False):
                    await interaction.response.send_message(f"⚔️ You defeated the {card_name(card_value)}!", ephemeral=True, delete_after=4)
                else:
                    await interaction.response.defer()

                player_data[user_id]['current_weapon_power'] = card_number
                if suit in ['Spades', 'Clubs']:
                    player_data[user_id]['last_kill'] = (card_value, suit)

            else:
                damage = card_number - weapon_power
                player_data[user_id]['health'] = max(0, player_data[user_id]['health'] - damage)

                if not player_data[user_id].get('has_played_before', False):
                    await interaction.response.send_message(f"🩸 You attacked {card_name(card_value)} and took {damage} damage!", ephemeral=True, delete_after=4)
                else:
                    await interaction.response.defer()

                if suit in ['Spades', 'Clubs']:
                    player_data[user_id]['last_kill'] = (card_value, suit)

            # --- Cleanup ---
            del player_data[user_id]['dungeon'][self.index]
            player_data[user_id]['attack_mode'] = None
            # ✅ Check for WIN condition if everything is clear
            if player_data[user_id]['health'] > 0 and len(player_data[user_id]['deck']) == 0 and len(player_data[user_id]['dungeon']) == 0:
                if await view.check_win(interaction):
                    return


            # ✅ EARLY death check
            if player_data[user_id]['health'] <= 0:
                await view.update_display(interaction)
                return

            # ✅ WIN CHECK
            if await view.check_win(interaction):
                return

            await view.update_display(interaction)
            return



        
        # --- EQUIP Mode ---
        elif player_data[user_id]['attack_mode'] == "equip":
            if suit != 'Diamonds':
                if not player_data[user_id].get('has_played_before', False):
                    await interaction.response.send_message("❌ You can only equip Diamonds as weapons!", ephemeral=True, delete_after=4)
                else:
                    await interaction.response.defer()
                return

            player_data[user_id]['weapon'] = (card_value, suit)
            player_data[user_id]['current_weapon_power'] = int(card_value) if card_value.isdigit() else {
                'Jack': 11, 'Queen': 12, 'King': 13, 'Ace': 14
            }[card_name(card_value)]
            player_data[user_id]['last_kill'] = None  # Clear last kill when equipping new weapon

            del player_data[user_id]['dungeon'][self.index]
            player_data[user_id]['attack_mode'] = None
            
            # ✅ Check for WIN condition if everything is clear
            if player_data[user_id]['health'] > 0 and len(player_data[user_id]['deck']) == 0 and len(player_data[user_id]['dungeon']) == 0:
                if await view.check_win(interaction):
                    return

            # ✅ EARLY death check — unlikely for equip, but safe to include for consistency
            if player_data[user_id]['health'] <= 0:
                await view.update_display(interaction)
                return

            # ✅ WIN CHECK
            if await view.check_win(interaction):
                return

            await view.update_display(interaction)
            
            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message("🗡️ Weapon equipped!", ephemeral=True, delete_after=4)
            else:
                await interaction.response.defer()
            return

        
# DUNGEON VIEW **********
# Custom view with buttons
class DungeonView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
        player_data[self.user_id] = {
            'health': 20, # Your health Variable
            'dungeon': [],   # The dungeon board
            'deck': create_deck(),  # Store the deck as a list of cards
            'weapon': None,  # <-- Starting with no weapon, No Diamond card
            'last_kill': None,   # Stores (value, suit) of the last monster killed
            'dungeon_started': False, # variable for deal button to allow start with no cards
            'attack_mode': None, # variable for setting attack mode  
            'potion_used': False, # variable for if you have used a potion this dungeon yet. 
            'current_weapon_power': None,  # tracks the current remaining weapon strength
            'has_played_before': False, # variable for removing annoying popups if you are pro

            
        }
        random.shuffle(player_data[self.user_id]['deck']) 

    def generate_dungeon_display(self, user_id):
        dungeon = player_data[user_id]['dungeon']
        display = ""
        for card_value, suit in dungeon:
            name = card_name(card_value)
            emoji = suit_emojis[suit]
            display += f"{name} {emoji}\n"
        return display

    async def update_display(self, interaction):
        # Defer immediately to acknowledge the interaction
        if not interaction.response.is_done():
            await interaction.response.defer()

        health = player_data[self.user_id]['health']
        dungeon_display = self.generate_dungeon_display(self.user_id)

        weapon = player_data[self.user_id]['weapon']
        last_kill = player_data[self.user_id]['last_kill']
        
        if health > 0 and len(player_data[self.user_id]['deck']) == 0 and len(player_data[self.user_id]['dungeon']) == 0:
            if await self.check_win(interaction):
                return    

        if weapon:
            weapon_display = f"{card_name(weapon[0])} {suit_emojis[weapon[1]]}"
        else:
            weapon_display = "None"

        if last_kill:
            last_kill_display = f"{card_name(last_kill[0])} {suit_emojis[last_kill[1]]}"
        else:
            last_kill_display = "None"

        if health <= 0:
            self.create_equip_buttons()
            try:
                await interaction.message.edit(
                    content="💀 **Game Over!** You have died in the dungeon.",
                    view=None
                )
            except Exception as e:
                print(f"Edit error (Game Over): {e}")
            del player_data[self.user_id]
        else:
            self.create_equip_buttons()
            try:
                await interaction.message.edit(
                    content=f"🃏 Your dungeon cards:\n{dungeon_display}\n"
                            f"❤️ Health: {health}/20\n"
                            f"🗡️ Weapon: {weapon_display}\n"
                            f"🪦 Last Kill: {last_kill_display}",
                    view=self
                )
            except Exception as e:
                print(f"Edit error (Normal Update): {e}")


            
            
    def create_equip_buttons(self):
        # Remove old buttons (except main ones)
        self.clear_items()

        # Re-add the main buttons (Deal, Damage, Heal, Flee, Fist)
        self.add_item(self.deal_button)
        # self.add_item(self.damage_button) REMOVED AS IT WAS FOR TESTING
        # self.add_item(self.heal_button) REMOVED AS IT WAS FOR TESTING
        # self.add_item(self.flee_button) REMOVED TO MAKE COOLER
        # Flee Button: dynamically change color based on if player can flee
        if player_data[self.user_id].get('can_flee', False):
            flee_button_style = discord.ButtonStyle.primary  # 🟦 Blue if allowed
        else:
            flee_button_style = discord.ButtonStyle.secondary  # ⚪ Gray if not

        self.add_item(FleeButton(style=flee_button_style))

        self.add_item(AttackButton()) # 👊
        #self.add_item(WeaponAttackButton())   # 🗡️ REMOVED TO MAKE COOLER
        # Weapon Attack Button dynamically changes color
        if player_data[self.user_id]['weapon']:
            weapon_button_style = discord.ButtonStyle.success  # 🗡️ Ready
        else:
            weapon_button_style = discord.ButtonStyle.secondary  # ⬜ Not ready

        self.add_item(WeaponAttackButton(style=weapon_button_style))
        #self.add_item(PotionButton())   # 💖  REMOVED TO MAKE COOLER
        # Potion Button dynamically colored
        if player_data[self.user_id].get('potion_used', False):
            potion_button_style = discord.ButtonStyle.secondary  # 🩶 Used = gray
        else:
            potion_button_style = discord.ButtonStyle.success    # 💖 Not used = green

        self.add_item(PotionButton(style=potion_button_style))

        self.add_item(EquipButtonMain()) 


        # Now create Equip buttons for each dungeon card
        for index, (card_value, suit) in enumerate(player_data[self.user_id]['dungeon']):
            name = card_name(card_value)
            emoji = suit_emojis[suit]
            
            label = f"{name} {emoji}"

            # Decide button color based on suit
            if suit in ['Hearts', 'Diamonds']:
                button_style = discord.ButtonStyle.danger  # ❤️ Red buttons for Hearts and Diamonds
            else:
                button_style = discord.ButtonStyle.secondary  # Gray buttons for Spades and Clubs

            # Auto-calculate row (row 1, 2, etc.)
            row_number = 1 + (index // 5)
            
            self.add_item(EquipButton(index=index, label=label, style=button_style, row=row_number))


    # Sets up Deal and stores can_flee for some reason, should probably be in player stuff
    @discord.ui.button(label="Deal", style=discord.ButtonStyle.primary)

    async def deal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.name != "shuffle-and-slay":
            await interaction.response.send_message("❌ You can only deal cards in #shuffle-and-slay!", ephemeral=True, delete_after=4)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True, delete_after=4)
            return
            
        # First-time Deal (empty dungeon)
        if not player_data[self.user_id]['dungeon']:
            # Draw 4 cards normally
            hand = []
            for _ in range(4):
                if len(player_data[self.user_id]['deck']) > 0:
                    hand.append(player_data[self.user_id]['deck'].pop())

            player_data[self.user_id]['dungeon'] = hand
            player_data[self.user_id]['can_flee'] = True
            player_data[self.user_id]['dungeon_started'] = True

            await self.update_display(interaction)
            return

        # Normal Deal (must have exactly 1 card left)
        if player_data[self.user_id]['dungeon_started'] and len(player_data[self.user_id]['dungeon']) != 1:
            if not player_data[self.user_id].get('has_played_before', False):
                await interaction.response.send_message(
                    "❌ You must have exactly 1 card left to deal!",
                    ephemeral=True,
                    delete_after=4
                )
            else:
                await interaction.response.defer()
            return

        # If deck is empty, handle end-of-game logic
        if len(player_data[self.user_id]['deck']) == 0:
            if len(player_data[self.user_id]['dungeon']) == 1:
                final_card_value, final_card_suit = player_data[self.user_id]['dungeon'][0]

                if final_card_suit in ['Spades', 'Clubs']:
                    # Last card is a monster — must defeat it manually
                    await interaction.response.send_message(
                        "⚔️ The final monster awaits! You must defeat it to win!",
                        ephemeral=True,
                        delete_after=4
                    )
                    return
                else:
                    # Last card is Heart or Diamond — auto WIN
                    health = player_data[self.user_id]['health']
                    await interaction.response.edit_message(
                        content=f"🏆 **Victory!** You cleared the dungeon with {health} health left!",
                        view=None
                    )
                    del player_data[self.user_id]
                    return
            else:
                # No cards left at all (maybe fled with no cards)
                await interaction.response.edit_message(
                    content="💀 **Game Over!** The deck and dungeon are empty.",
                    view=None
                )
                del player_data[self.user_id]
                return


        # Keep the last card and draw 3 new cards
        current_dungeon = player_data[self.user_id]['dungeon']

        new_cards = []
        for _ in range(3):
            if len(player_data[self.user_id]['deck']) > 0:
                new_cards.append(player_data[self.user_id]['deck'].pop())

        player_data[self.user_id]['dungeon'] = current_dungeon + new_cards
        player_data[self.user_id]['can_flee'] = True
        player_data[self.user_id]['potion_used'] = False # resets potion usage for new dungeon

        await self.update_display(interaction)
        
    # sets up Damage button COMMENTED OUT AS THIS WAS FOR TESTING
#    @discord.ui.button(label="Damage", style=discord.ButtonStyle.danger)
#    async def damage_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#        if interaction.channel.name != "shuffle-and-slay":
#            await interaction.response.send_message("❌ You can only use this in #shuffle-and-slay!", ephemeral=True)
#            return

#        if interaction.user.id != self.user_id:
#            await interaction.response.send_message("❌ This is not your game!", ephemeral=True, delete_after=4)
#            return

#        player_data[self.user_id]['health'] = max(0, player_data[self.user_id]['health'] - 1)

#        await self.update_display(interaction)
    # sets up Heal COMMENTED OUT AS THIS WAS FOR TESTING
#    @discord.ui.button(label="Heal", style=discord.ButtonStyle.success)
#    async def heal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
#        if interaction.channel.name != "shuffle-and-slay":
#            await interaction.response.send_message("❌ You can only use this in #shuffle-and-slay!", ephemeral=True)
#            return

#        if interaction.user.id != self.user_id:
#            await interaction.response.send_message("❌ This is not your game!", ephemeral=True, delete_after=4)
#            return

#        player_data[self.user_id]['health'] = min(20, player_data[self.user_id]['health'] + 1)

#        await self.update_display(interaction)

    # sets up flee
    @discord.ui.button(label="Flee", style=discord.ButtonStyle.primary)
    async def flee_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.channel.name != "shuffle-and-slay":
            await interaction.response.send_message("❌ You can only use this in #shuffle-and-slay!", ephemeral=True)
            return

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This is not your game!", ephemeral=True, delete_after=4)
            return

        if not player_data[self.user_id]['can_flee']:
            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message("❌ You can't flee again so soon!", ephemeral=True, delete_after=4)    # <-- Auto delete after 3 seconds
            else:
                await interaction.response.defer()    
            return
                
        
        #  Must have full dungeon to flee
        if len(player_data[self.user_id]['dungeon']) < 4:
            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message(
                    "❌ You can't flee unless the dungeon is full (no cards used or equipped)!", ephemeral=True, delete_after=4
                )
            else:
                await interaction.response.defer()     
            return
        
        dungeon_cards = player_data[self.user_id]['dungeon']

        if not dungeon_cards:
            if not player_data[user_id].get('has_played_before', False):
                await interaction.response.send_message("❌ You can't flee — there are no dungeon cards!", ephemeral=True)
            else:
                await interaction.response.defer()     
            return

        # Shuffle dungeon cards and add to bottom
        random.shuffle(dungeon_cards)
        for card in reversed(dungeon_cards):
            player_data[self.user_id]['deck'].insert(0, card)

        # Clear the current dungeon
        player_data[self.user_id]['dungeon'] = []

        # Check if enough cards left
        if len(player_data[self.user_id]['deck']) < 4:
            await interaction.response.edit_message(
                content="💀 **Game Over!** Not enough cards left to flee into the next room.",
                view=None
            )
            del player_data[self.user_id]
            return

        # Deal 4 new dungeon cards
        new_hand = []
        for _ in range(4):
            card = player_data[self.user_id]['deck'].pop()
            new_hand.append(card)

        player_data[self.user_id]['dungeon'] = new_hand

        player_data[self.user_id]['can_flee'] = False  # <-- Prevent back-to-back fleeing!

        await self.update_display(interaction)
        
    async def check_win(self, interaction):
        if len(player_data[self.user_id]['deck']) == 0 and len(player_data[self.user_id]['dungeon']) == 0:
            try:
                await interaction.followup.send(
                    f"🏆 **Victory!** You cleared the dungeon with {player_data[self.user_id]['health']} health left!",
                    ephemeral=False
                )
            except Exception as e:
                print(f"Victory message error: {e}")
            del player_data[self.user_id]
            return True
        return False

# Run the bot
try:
    bot.run("BOT_TOKEN_HERE") # <-- ADD YOUR BOT TOKEN, LEAVE QUOTES 
except Exception as e:
    print(f"Error when running the bot: {e}")
    input("Press Enter to exit...")
