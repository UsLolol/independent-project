import os
import random
import streamlit as st
from dotenv import load_dotenv
from google import genai
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
 
client = genai.Client(api_key=api_key) if api_key else None
 
MODEL_NAME = "gemini-3.5-flash-lite"

# ================================================================
# 1. PAGE SETUP
# ================================================================
#REMEMBER TO COME BACK AND GIVE IT A NAME
st.set_page_config(page_title = "....", page_icon = "⛧", layout = "centered" )
st.title("⛧ ....")

# ================================================================
# 2. GAME SETUP — INITIALISE VALUES ONCE
# ================================================================
# Session state remembers values when Streamlit reruns the script.

if "game_started" not in st.session_state:
    st.session_state.game_started = False

def start_game(name):
    st.session_state.game_started = True
    st.session_state.player_name = name
    st.session_state.suspicion = 0
    st.session_state.max_suspicion = 5
    st.session_state.pouch = []
    st.session_state.rooms = ["Introduction", "Bedroom", "Corridor", "The Compound", "Ritual Site", "Ending", "Credits"]
    st.session_state.compound_location = "main"
    st.session_state.bells_rung = 1
    st.session_state.kitchen_explored = False
    st.session_state.drawer_opened = False
    st.session_state.office_explored = False
    st.session_state.office_view = "main"
    st.session_state.office_desk_explored = False
    st.session_state.office_painting_explored = False
    st.session_state.powder_left = False
    st.session_state.room_number = 0
    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False
    st.session_state.ritual_site_step = 1
    st.session_state.ritual_choice = ""

def restart_game():
    st.session_state.clear()
    st.rerun()

def return_from_office():
    st.session_state.office_explored = True
    st.session_state.bells_rung = min(st.session_state.bells_rung + 1, 3)
    st.session_state.compound_location = "main"
    st.session_state.office_view = "main"
    st.session_state.action_complete = False
    st.session_state.powder_left = False
    st.rerun()

def get_current_room():
    return st.session_state.rooms[st.session_state.room_number].lower()

def continue_game():
    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False
    st.session_state.room_number += 1
    st.rerun()

def add_item(item):
    if item not in st.session_state.pouch:
        st.session_state.pouch.append(item)

def has_item(item):
    return item in st.session_state.pouch

def remove_item(item):
    if item in st.session_state.pouch:
        st.session_state.pouch.remove(item)

def increase_suspicion(amount):
    st.session_state.suspicion = min(
        st.session_state.max_suspicion,
        st.session_state.suspicion + amount
    )

def decrease_suspicion(amount):
    old_suspicion = st.session_state.suspicion
    st.session_state.suspicion = max(
        0,
        st.session_state.suspicion - amount
    )
    return st.session_state.suspicion - old_suspicion

def generate_story_with_gemini(room, action, outcome, fallback_message):
    if client is None:
        return fallback_message

    pouch_text = ", ".join(st.session_state.pouch)

    prompt = f"""
You are the storyteller for a dark detective story adventure game about a person who is investigating a cult that has been linked to disappearences all over the country but has managed to stay out of the eye of the law, despite journalist reports. You will be narrating the story to the player, who is playing as the person. The person has managed to infiltrate the cult after months of trying to track them down and looking for a way in. This person wants to find their son - who disappeared at the same time the reports started.

Player: {st.session_state.player_name}
Room: {room}
Suspicion: {st.session_state.suspicion}/{st.session_state.max_suspicion}
Inventory: {pouch_text}

Action: 
{action}


Outcome:
{outcome}

Describe what happens in 30-50 words.

Use second person.
Use atmospheric dark occultist and "detective stories" language.
Do not change the outcome.
Do not change suspicion or inventory.
Do not introduce new choices.
"""
    try:
        interaction = client.interactions.create(
            model = "gemini-3.5-flash-lite",
            input=prompt,
            generation_config={"thinking_level":"minimal"}
        )
        if interaction.output_text:
            return interaction.output_text
        return fallback_message
    except Exception as error:
        st.error(f"Gemini error: {error}")
        return fallback_message

def generate_story(room, action, outcome, fallback_message):
    if room.lower() != "the bedroom":
        return fallback_message

    if "gemini_scene_story" not in st.session_state:
        st.session_state.gemini_scene_story = generate_story_with_gemini(
            room, action, outcome, fallback_message
        )

    return st.session_state.gemini_scene_story

def roll_dice():
    return random.randint(1,6)

def chance_encounter(room, action, success_number, success_outcome, success_fallback, failure_outcome, failure_fallback, suspicion, bonus_item=""):
    roll = roll_dice()
    bonus = 1 if bonus_item and has_item(bonus_item) else 0
    total = roll + bonus

    roll_message = (f"You rolled: {roll}")
    if bonus:
        roll_message += (f" + {bonus} bonus.")
    roll_message += (f" = {total}.")

    if total >= success_number:
        story = generate_story(room, action, success_outcome, success_fallback)
        set_result("success", f"{roll_message} {story}")

    else:
        increase_suspicion(suspicion)
        story = generate_story(room, action, failure_outcome, failure_fallback)
        set_result("increased suspicion", f"{roll_message} {story}", suspicion)

# ================================================================
# 3. REUSABLE DISPLAY FUNCTIONS — KEEP EVERY ROOM CONSISTENT
# ================================================================

#Showing the room
def show_room(title, description):
    st.header(title)
    st.write(description)

#Inventory Management
#Show player info
def show_player_info():
    st.subheader(f"🥸 {st.session_state.player_name}")
    left, right = st.columns(2)
    with left:
        st.write(f"👁️‍🗨️ Suspicion: {st.session_state.suspicion} / {st.session_state.max_suspicion}")
    with right: 
        st.write(f"🎒 Pouch: {', '.join(st.session_state.pouch)}")
    st.caption(
        f"Room {st.session_state.room_number + 1}"
    )
    st.divider()

def set_result(result_type, message, value = ""):
    st.session_state.result_type = result_type
    st.session_state.result_message = message
    st.session_state.result_value = value
    st.session_state.action_complete = True
    st.rerun()

def show_result():
    kind = st.session_state.result_type
    value = st.session_state.result_value
 
    if kind == "item":
        st.success(f"🎒 NEW ITEM: {value}")
    elif kind == "increased suspicion":
        st.error(f"◉ INCREASED SUSPICION: Your suspicion has increased.")
    elif kind == "decreased suspicion":
        st.success(f"◎ DECREASED SUSPICION: Your suscpicion has decreased.")
    elif kind == "success":
        st.success("✅ Success!")
    else:
        st.info("The story continues...")
 
    st.write(st.session_state.result_message)

#Continue button
def show_continue_button(text = "Continue"):
    if st.button(text):
        continue_game()

# ================================================================
# 4. START SCREEN — NAME INPUT 
# ================================================================
####CULT NAME IS A PLACEHOLDER, REMEMBER TO CHANGE IT
if not st.session_state.game_started:
    st.write("You have spent months trying to worm your way into a cult known as 'Perfidus'. \n\nYou finally managed to pinpoint the next town they would hit. \n\nYou let yourself get taken in order to join them, and after spending even longer gaining their trust, they begin treating you as a member. \n\nThey do not show their faces or give you their real names. \n\nYou came here to find out what happened to your son, if he is still alive, to put a stop to this group, and to stop more families from being broken apart. \n\nThey are preparing for a ritual, before moving onto another town.")
    name = st.text_input("What is your name? ")

    if st.button("Begin."):
        if name.strip():
            start_game(name)
            st.rerun()
        else:
            st.warning("Enter your name before taking on the cult.")
else:
    #Show the same player information in every room
    show_player_info()
    room = get_current_room()

    if st.session_state.suspicion >= st.session_state.max_suspicion:
        if st.session_state.action_complete:
            show_result()

        show_room("💀 Game Over", "The cult has become too suspicious of you. They will make sure you never leave alive.")
        st.error("You have been taken care of. Better luck next time.")
        if st.button("🔄 Try Again"):
            restart_game()
        st.stop()

    # ============================================================
    # ROOM 1 — INTRODUCTION (MODEL SIMPLE CONTINUE NAVIGATION)
    # ============================================================
    if room == "introduction":
        show_room("👁 The Beginning", "You wake up in your bed. \n\nYou aren't sure of what this building is. \n\nThe windows are boarded up, and so you have never managed to peer outside. \n\nBefore they recruited you, they would keep a bag on your head inbetween interviews and trials. \n\nNow, they don't. They believe you are one of them.")
        
        show_continue_button("🛏️ Get up from the bed.")

    # ============================================================
    # ROOM 2 — BEDROOM (MODEL RESULT -> CONTINUE)
    # ============================================================
    elif room == "bedroom":
        show_room("💤 The Bedroom", "Your bedroom is a fancy place. Adorned in expensive tapestries and antique furniture. \n\nA chandelier hangs in the middle of the room. It is made of glass, refracting the candle flames like little specks of stardust throughout the room. \n\nYour attire has been carefully laid out on a chair next to your bed. \n\nIt isn't like the usual bland, black cloak you usually wear. This one is adorned with golden lines and symbols you do not know.")
        if not st.session_state.action_complete:
            left, right = st.columns(2)
            with left:
                if st.button("🔮 Don the ritual attire"):
                    outcome = "The player dons the ritual attire."
                    story = generate_story(
                        "The Bedroom", "dons the attire", outcome, "You decide to pick up the cloak and to put it on."
                    )
                    add_item("Ritual Attire")
                    set_result("item", story, "Ritual Attire")
                    st.rerun()
                   
            with right:
                if st.button("Ignore the attire"):
                    outcome = "The player leaves the attire alone and continues"
                    increase_suspicion(1)
                    story = generate_story(
                        "The Bedroom", "leaves the attire", outcome, "You decide to leave the cloak alone and continue on your way."
                    )
                    set_result("story", story)
                    st.rerun()
        else:
            show_result()
            show_continue_button()

    # ============================================================
    # ROOM 3 — The Corridor
    # ============================================================
    elif room == "corridor":
        show_room("🚪 The Corridor", "You step through your bedroom door to find yourself in corridor that stretches as far as the eye can see, in both directions. \n\n Various doors, just like yours, litter both walls of the corridor. \n\nThe silence of this place is suffocating. \n\nYou have to stop the ritual, but you have some time to explore beforehand, and hopefully find clues as to what happened to your son.")
        show_continue_button()

    # ============================================================
    # ROOM 4 — The Compound
    # ============================================================
    elif room == "compound":
        location = st.session_state.compound_location

        if location == "main":
            bell_messages = {
               1:  "'Ding \n\nDong \n\nDing \n\nDong'. \n\nYou have heard this sound before - it's the clock bell signifying your time is running out. \n\nThis bell plays 3 times - once every hour, to alert the memembers to hurry with preperations. \n\nWhen the third bell rings you have to be at the ritual site, or they will not let you in, and all of these months of hard work will have been for naught.",
                2: "'Ding \n\nDong \n\nDing \n\nDong'. \n\nThe second bell has rung. You are running out of time.",
                3:"'Ding \n\nDong \n\nDing \n\nDong'. \n\nThe third bell has rung. If you do not head to the ritual site now, you will have to find another way in."
             }
            bell_message = bell_messages[st.session_state.bells_rung]
            show_room("☢️ The Compound", f"You arrive at the main salon of the building. \n\nMuch like the other rooms, a deafening silence is present. Even the candle flames dare not whisper. \n\n{bell_message}")
            
            if not st.session_state.action_complete:
                if st.session_state.bells_rung >= 2:
                    if st.button("🕯️ Go to the ritual site"):
                        continue_game()

                if st.session_state.bells_rung < 3:       
                 left, right = st.columns(2)
                 with left:
                    if not st.session_state.kitchen_explored:
                     if st.button("🚪 Investigate the kitchen"):
                        st.session_state.compound_location = "kitchen"
                        st.rerun()
                 with right:
                    if not st.session_state.office_explored:
                     if st.button("🚪 Investigate the leader's office"):
                        if has_item("Office Secret"):
                            st.session_state.compound_location = "office"
                            st.session_state.office_view = "main"
                            st.rerun()
                        else:
                            st.warning("No matter how much you try to force the door, it won't open. There isn't even a visible lock on it.")

        # ============================================================
        # ROOM 4.1 — The Kitchen
        # ============================================================
        elif location == "kitchen":
            show_room(
                "🔪 The Kitchen",
                "You enter the kitchen, to find two cloaked figures talking over the cooking station. What will you do?"
            )

            if not st.session_state.action_complete:
                if not st.session_state.get("drawer_opened", False):
                    left, right = st.columns(2)

                    with left:
                        if st.button("🍴 Investigate the cutlery drawer"):
                            st.session_state.drawer_opened = True
                            st.rerun()

                    with right:
                        if st.button("👂 Eavesdrop"):
                            roll = roll_dice()
                            if not has_item("Ritual Attire"):
                                roll += 1
                            if roll >= 4:
                                add_item("Office Secret")
                                set_result("story", "You manage to remain out of sight whilst listenting to the conversation. \n\nThese cult memembers are responsible for the upkeep of the leader's office. \n\nYou overhear them discussing the unusual method of getting the door open - one must tilt the second candlestick from the left on the wall next to the door.")
                            else:
                                increase_suspicion(1)
                                set_result("increased suspicion", "You stood out a bit too much when attemping to listen in on the conversation. \n\nThe cloaked figures stop talking.")

                else:
                    st.write(
                        "You find a butcher's knife in the drawer. "
                        "Will you take it?"
                    )
                    left, right = st.columns(2)

                    with left:
                        if st.button("Take the knife"):
                            add_item("Butcher's Knife")
                            set_result(
                                "item",
                                "You take the butcher's knife.",
                                "Butcher's Knife"
                            )

                    with right:
                        if st.button("Leave the knife"):
                            set_result(
                                "story",
                                "You leave the knife in the drawer."
                            )

            else:
                show_result()
                if st.button("Return to main hall"):
                    st.session_state.kitchen_explored = True
                    st.session_state.bells_rung = min(
                        st.session_state.bells_rung + 1, 3
                    )
                    st.session_state.compound_location = "main"
                    st.session_state.action_complete = False
                    st.rerun()
        # ============================================================
        # ROOM 4.2 — The Office
        # ============================================================
        elif location == "office":
            show_room(
                "🜏 The Office", "You manage to get the office door open by tilting the correct candlestick. If there are answers to be found, they will be here. \n\nThere's an antique and ornate desk in the middle of the room, and right behind it there is a strangely big painting depicting the ninth circle of hell, as per Dante's Inferno. \n\nYou have read this book many times before, your son used to love it. \n\nYou can't look away from the painting. There are people encased within ice, naked, and in agony. \n\n... \n\nYou shake it off and continue investigating, the third bell with ring any time now."
            )
            if st.session_state.office_view == "main":
                left, right = st.columns (2)
                with left:
                    if not st.session_state.office_desk_explored: 
                     if st.button("🪑 Investigate the desk"):
                        st.session_state.office_view = "desk"
                        st.rerun()

                with right:
                    if not st.session_state.office_painting_explored:        
                     if st.button("👹 Investigate the painting"):
                        st.session_state.office_view = "painting"
                        st.rerun()

                if st.button("Return to the main hall"):
                    return_from_office()

            elif st.session_state.office_view == "desk":
                if st.session_state.action_complete:
                    show_result()
                    if st.button("Return to the main hall"):
                        return_from_office()

                else:
                    st.write(
                       "You approach the desk, and despite your fear of what you might find, you quickly open each drawer and look inside. There are files, a gun, and a strange purple poweder without a label. What will you look at?"
                    )
                    files, gun, powder = st.columns (3)

                    with files:
                        if st.button("Look at the files"):
                            add_item("Incriminating Files")
                            set_result("story", "You pick up a folder full of files and quickly look through them. Most pages are people who have been reported missing on the news. There are hundreds of pages. You feel sick. \n\nYou keep flipping through the pages until you freeze. There is a file on your son. All of his private information and family history laid bare in front of you. \n\nYou pause, and staring at his picture, a tear falls down your cheek. \n\n... \n\nYou compose yourself and place the folder inside your cloak. You hope the police will use this file to finally stop this group.")


                    with gun:
                        if st.button("Inspect the gun"):
                            add_item("Antique Revolver")
                            set_result("story", "You pick up the gun. You can very clearly see it is an antique revolver. You open the barrel to see 6 bullets inside. This thing packs a punch. You take it.")

                    with powder:
                        if st.button("Examine the powder"):
                            st.session_state.office_view = "powder"

            elif st.session_state.office_view == "powder":
                if st.session_state.action_complete:
                    show_result()
                    if st.session_state.powder_left:
                        keep_exploring, leave_office = st.columns(2)
                        with keep_exploring:
                            if st.button("Keep exploring the office"):
                                st.session_state.office_desk_explored = True
                                st.session_state.office_view = "main"
                                st.session_state.action_complete = False
                                st.session_state.powder_left = False
                                st.rerun()
                        with leave_office:
                            if st.button("Return to the main hall"):
                                return_from_office()
                    elif st.button("Return to the main hall"):
                        return_from_office()
                else:
                    st.write("What will you do with the powder?")
                    take, inhale, leave = st.columns(3)

                    with take:
                        if st.button("🍄 Take it"):
                            add_item("Purple Powder")
                            set_result(
                                "story",
                                "You decide to take the vial with you. Even if you are unsure of what it is, it may prove useful."
                            )

                    with inhale:
                        if st.button("👃 Inhale it"):
                            add_item("The Mark")
                            set_result(
                                "story",
                                "You have no time to waste, and decide to inhale the powder to figure out what it could be. \n\n... \n\nAs soon as you inhale the powder your head starts to feel like it's floating and you fall to the floor. \n\nAs you open your eyes, you find yourself in the same hell depicted by that painting. \n\nWhat seems to be a demon speaks to you. \n\n'Veni, o proles perfida. Una adhuc victima, et inter vivos in mundo mortalium ambulabo. Abi, o proles perfida. Una adhuc victima, et inter vivos in mundo mortalium ambulabo.' \n\nAs you tremble in terror, the demon approaches you and claws a mark upon your flesh. \n\nYou pass out again. \n\n... \n\nYou open your eyes and wake up. Unsure of how long as passed, you stand up, and look upon your arm to find the mark etched by the demon."
                            )
                    with leave:
                        if st.button("🚪 Leave it"):
                            st.session_state.powder_left = True
                            set_result(
                                "story",
                                "You decide it is better to not mess with strange substances you do not know, especially if they seem like class A drugs."
                            )

            elif st.session_state.office_view == "painting":
                if st.session_state.action_complete:
                    show_result()
                    if st.button("Return to the main hall"):
                        return_from_office()

                else:
                    st.write(
                        "You decide to approach the painting, and as revolting as it is, you decide to take a closer look. \n\nYou notice a very faint string of numbers written on the right corner of the frame. \n\n'9257' \n\nYou decide to move the painting after noting down the code, and behind it a safe is revealed. What will you do?"
                    )                        
                    open_safe, leave_safe = st.columns (2)

                    with open_safe:
                        if st.button("🔐 Open the safe"):
                            roll = roll_dice()

                            if roll >= 4:
                                add_item("Perfidus Member List")
                                set_result(
                                    "story",
                                    "The safe opens to reveal money inside, and a folder labeled 'Perfidi'. \n\nYou open the file to find the what seems to be a record of every memeber of the cult, including their faces, names, locations, and whether they are active or not. \n\nThis is groundbreaking. It's what you've spent months working so hard to get. You put it inside your cloak."
                                )
                            else:
                                increase_suspicion(3)
                                set_result(
                                    "increased suspicion",
                                    "As you open the safe, a container of liquid nitrogen bursts and a cloud spreads. Everything that was inside this safe is now frozen, and part of your cloak is now frozen solid. You have made a grave mistake, but there is nothing you can do about it now. You decide to leave."
                                )    
                    with leave_safe:
                        if st.button("🔐 Leave the safe alone"):
                            set_result(
                                "story",
                                "You decide to leave the safe alone. After all, you've spent long enough in this group to know there is probably some kind of dangerous contraption within it, and you also know you have no idea on how to safely deactivate right now."
                            )

        # ============================================================
        # ROOM 5 — The Ritual Site
        # ============================================================
        elif room == "ritual site":
            if st.session_state.ritual_site_step == 1:
              show_room("🕯️ The Ritual Site", "You walk down the long corridor that leads to the ritual site. \n\nYou have never been allowed to walk down this corridor before and do not know what to expect. \n\nYour guard is up, and you are filled with anxious and fearful thoughts. You know these people are crazy, and you know they are willing and capable of making anyone disappear. \n\nOne single wrong step could mean it's all over for you. \n\nThe corridor is dark, and cloaked figures stand along each side of it. \n\nThey do not look up at you, they do not reveal their face, and they do not reveal their eyes. \n\nWith each step your fear and panic grows. \n\n... \n\nYou arrive at two huge doors. \n\nYou take a deep breath, slowly open them, and step through... \n\n\n\n\n\nAs you step into the room, you stand in shock at the horrid sight you witness. \n\nThere are strange symbols drawn all over the walls, and in front of the altar, drawn on the floor, there is a strange mark surrounded by candles. \n\nOne cloaked figure stands in front of each candle, apart from one. They are wearing the same ritual attire from your bedroom. \n\n\n\nA man, cloaked in a red robe, wearing a horned goat mask, stands behind the altar.")
              st.toast("The ritual is starting", icon = "🕯️")

              if st.button("🕯️ Stand in front of your candle"):
                  st.session_state.ritual_site_step = 2
                  st.rerun()

            elif st.session_state.ritual_site_step == 2:
                show_room(
                    "🕯️ The Ritual",
                    "As you take place in front of your candle, there is a brief pause of deafening silence from all the whispers. \n\n\n\nThen, the leader begins speaking. \n\n'Welcome, O Treacherous ones. My children. The time of the final ritual is at hand. One more sacrifice, and our lord shall walk the mortal realm once more.' \n\nAs he finishes speaking, everyone at the ritual site begins chanting alongside him. \n\n'Sumus liberi vestri perfidi. Vas ultimum vobis tradimus. Sumus liberi vestri perfidi. Vas ultimum vobis tradimus.' \n\n\n\nAs the chanting continues, another red cloaked figure wearing a rabbit's mask, carries a man to the middle of the marking on the floor. \n\nAs the man is carefully placed on the floor, you can see his mouth is gagged with cloth, and his arms, hands, legs, and feet are all bounded by rope."
                )

                if not st.session_state.action_complete:
                    if has_item("Antique Revolver"):
                        if st.button("🔫 Use the revolver to stop the ritual"):
                            st.session_state.ritual_choice = "revolver"
                            set_result("story", "Trembling and in shock from this horrible turn of events, you pull out your revolver and point it the leader, alternating between targetting him and the other members.")

                    if has_item("Butcher's Knife"):
                        if st.button("🔪 Stab the leader"):
                            st.session_state.ritual_choice = "knife"
                            set_result("story", "Trembling and washed over by fear, you are determined to put a stop to this ritual. You break out into the fastest run of your life, and lunge towards the leader, with knife in hand.")             
                    if st.button("🜍 Chant along"):
                        st.session_state.ritual_choice = "chant"
                        set_result("story", "You are too scared to do anything. These people are dangerous. They probably killed your son. You can't stop them. \n\n\n\nMore and more of these thoughts consume your mind as you begin chanting with these cloaked figures. You are powerless, and utterly defeated.")

                else:
                    show_result()

                    if st.button("End it."):
                     st.session_state.room_number = st.session_state.rooms.index("Ending")
                     st.session_state.action_complete = False
                     st.rerun()
        # ============================================================
        # ROOM 6 — The Ending
        # ============================================================

        elif room == "ending":
            ###ENDINGS FOR THE MARK
            if has_item("The Mark"):
                if st.session_state.ritual_choice == "revolver":
                    ending = "As you wave your gun around and get ready to shoot at the leader, the tied up man in the middle of the room bursts into flames, letting out agonizing screams, that become ungodly screeches. \n\nYour arm starts to burn and you drop your gun. You can't help but scream in pain. \n\nIt's like you are being burned from the inside. \n\n\n\nThe cult leader starts to laugh, and soon after, everyone in the room takes down their hoods. \n\n\n\nStill in pain, you look at the centre of the room, and where the man once burned, the same demon from your vision emerges through the flames. \n\n\n\nThe demon looks upon you and extends his hand toward you. \n\n\n\nThe burning stops. \n\nYou start to move against your will, and place your hand on his. You are no longer in control of yourself. "
                elif st.session_state.ritual_choice == "knife":
                    ending = "You are mere inches away from the leader, who has fallen back onto the floor as a reaction to your attack. \n\nYou are about to plunge your knife deep into his chest. \n\n\n\n... \n\n\n\nYou can't move. \n\nYou simply cannot move. \n\nThe more you try the more you feel your arm start to burn where the mark has been etched. \n\nThe pain becomes so unbearable that you can't help but dropping the knife. \n\nIt's like you are being burned from the inside. \n\n\n\nThe cult leader starts to laugh, and soon after, everyone in the room takes down their hoods. \n\n\n\nStill in pain, you look at the centre of the room, and where the man once laid, flames erupt, and the same demon from your vision emerges through the flames. \n\n\n\nThe demon looks upon you and extends his hand toward you. \n\n\n\nThe burning stops. \n\nYou start to move against your will, and place your hand on his. You are no longer in control of yourself."    
                else:
                 ending = "You continue to chant alongside the cloaked figures and the leader. \n\nA few moments pass, and the man laid in the middle of the room erupts into flames. \n\nHe lets out agonizing screams of pain. \n\nThese quickly become screeches no human being could produce. \n\nFear, terror, and panic wash over you. Completely taking over your body. Breaking your mind. \n\nYou fall onto the floor and can't help but stare at the flames. \n\nThen, within mere moments, the same demon from your vision steps out of the flames. \n\nAs the demon steps onto the world, it looks upon you. \n\n'Look upon me, marked child. You will be my mortal vessel. I will be able to walk amongst the mortal realm, and you will contain my vitality. Heed your call, and serve your purpose.' \n\n\n\n...\n\n\n\nAnd just like that, with those words, you lose conscience. \n\nThe demon has taken you as a vessel for his life force. \n\nYou are no longer you. \n\nYou are his vial."
            #####ENDINGS WITHOUT THE MARK
            else:
                if st.session_state.ritual_choice == "revolver":
                    ending = "You wave your gun around, ensuring no one comes close to you. \n\nThen, you take aim at the leader, and press your finger against the trigger. \n\n\n\n... \n\n\n\nA loud bang deafens you and disorients your senses. \n\nThe red cloaked figure falls onto the floor, and as he does, his goat horned mask bounces beside him, before falling still next to the altar. \n\nYou have to make sure he's dead. \n\n\n\nYou approach his body, as the cloaked figures flee the room. \n\nAs you gaze upon his now bare face, you are left with anguish and sadness. \n\nYou begin crying uncontrollably. \n\nThis man has your son's face. \n\n\n\n...\n\n\n\n...\n\n\n\n..."

                    has_incriminating_files = has_item("Incriminating Files")
                    has_member_list = has_item("Perfidus Member List")

                    if has_incriminating_files and has_member_list:
                        ending += "\n\nYou gathered enough evidence for the police to do something about the remaining members of the cult. You stopped the ritual, and the remaining members will face justice. \n\nYour son is dead. \n\nYou saved a man's life."
                    else: 
                        ending += "\n\nYou end up handing over all the information you gathered over to the authorities, but it is not enough for them to find the remaining members of the cult. \n\nYour son is dead. \n\nThe testimony of the man you saved is the only reason you are not behind bars for his murder."

                elif st.session_state.ritual_choice == "knife":
                    ending = "You run towards the leader and plunge your knife deep into his chest. \n\nThe man does not let even a groan of pain out, before your hands are submerged in blood. \n\nHe falls to the floor, and you on top of him. \n\nYou twist the knife and even more blood gushes out onto you, covering the entire floor and altar in red. \n\n\n\nAs you slowly stand up, you can't help but hope to feel satisfation and happiness. \n\nThe man responsible for taking your son away from you is dead before your very eyes. \n\nJust as this thought comes into your head, the man's mask slips off his head and reveals his face. \n\n\n\n... \n\n\n\nHe has your son's face."    

                    has_incriminating_files = has_item("Incriminating Files")
                    has_member_list = has_item("Perfidus Member List")

                    if has_incriminating_files and has_member_list:
                        ending += "\n\nYou gathered enough evidence for the police to do something about the remaining members of the cult. You stopped the ritual, and the remaining members will face justice. \n\nYour son is dead. \n\nYou saved a man's life."
                    else: 
                        ending += "\n\nYou end up handing over all the information you gathered over to the authorities, but it is not enough for them to find the remaining members of the cult. \n\nYour son is dead. \n\nThe testimony of the man you saved is the only reason you are not behind bars for his murder."
                    
                else:
                    ending = "You continue to chant with the other people in this room. \n\nYour body is overcome with a sense of dread, panic, and shock. \n\nYou are frozen in place, chanting, and gazing onto the tied man laid bare in the middle of the room. \n\n\n\nMere moments after, the man erupts into flames, letting out agonizing screams of pain. \n\nThese screams quickly become screeches that no human could ever produce. \n\n\n\nFrom these flames, a creature without skin, bearing the head of a horned goat, standing at 10 feet tall, emerges. \n\nThe creature gazes upon the leader and extends its hand. \n\n\n\nThe leader approaches the creature, placing his hand on theirs, revealing a glowing mark etched onto his flesh. \n\n\n\n...\n\n\n\nThe ritual is complete. A demon now walks the earth, with an entire cult beckoning its every call. You have failed at stopping the ritual. And you will never know what happened to your son. \n\n\n\nDo you even want to? The apocalypse has begun. Perhaps you are better off not knowing your son's fate, for all of humanity is about to share the same one."

            show_room("The Ending", ending)
            show_continue_button("Continue")

        # ============================================================
        # ROOM 7 — Ending Screen
        # ============================================================
        elif room == "credits":
            show_room("Credits", "This interactive story was produced by Filipe. \n\nThere are multiple endings and outcomes to explore. \n\nThank you for playing.") 
            st.snow()       

            if st.button("🔄 Restart"):
                restart_game()