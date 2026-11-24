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
    st.session_state.rooms = ["Introduction", "Bedroom", "Corridor", "The Compound", "Ritual Site", "Prolific Detective", "Outside"]
    st.session_state.compound_location = "main"
    st.session_state.bells_rung = 1
    st.session_state.kitchen_explored = False
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
    st.write("You have spent months trying to worm your way into a cult known as 'The Cloaks'. \n\nYou finally managed to pinpoint the next town they would hit. \n\nYou let yourself get taken in order to join them, and after spending even longer gaining their trust, they begin treating you as a member. \n\nThey do not show their faces or give you their real names. \n\nYou came here to find out what happened to your son, if he is still alive, to put a stop to this group, and to stop more families from being broken apart. \n\nThey are preparing for a ritual, before moving onto another town.")
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
                                add_item("Prefidues Member List")
                                set_result(
                                    "story",
                                    "The safe opens to reveal money inside, and a folder labeled 'Prefidus'. \n\nYou open the file to find the what seems to be a record of every memeber of the cult, including their faces, names, locations, and whether they are active or not. \n\nThis is groundbreaking. It's what you've spent months working so hard to get. You put it inside your cloak."
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