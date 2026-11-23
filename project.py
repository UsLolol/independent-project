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
    st.session_state.rooms = ["Introduction", "Bedroom", "The Compound", "Ritual Site", "Prolific Detective", "Outside"]
    st.session_state.room_number = 0
    st.session_state.result_type = ""
    st.session_state.result_message = ""
    st.session_state.result_value = ""
    st.session_state.action_complete = False

def restart_game():
    st.session_state.clear()
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
        f" of {len(st.session_state.rooms)}"
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
    elif kind == "damage":
        st.error(f"◉ INCREASED SUSPICION: Your suspicion has increased.")
    elif kind == "heal":
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
    st.write("You have spent months trying to worm your way into a cult known as 'The Cloaks'. \nYou finally managed to pinpoint the next town they would hit. \nYou let yourself get taken in order to join them, and after spending even longer gaining their trust, they begin treating you as a member. \nThey do not show their faces or give you their real names. \nYou came here to find out what happened to your son, if he is still alive, to put a stop to this group, and to stop more families from being broken apart. \nThey are preparing for a ritual, before moving onto another town.")
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
        show_room("👁 The Beginning", "You wake up in your bed. \nYou aren't sure of what this building is. \nThe windows are boarded up, and so you have never managed to peer outside. \nBefore they recruited you, they would keep a bag on your head inbetween interviews and trials. \nNow, they don't. They believe you are one of them.")
        
        show_continue_button("🛏️ Get up from the bed.")

    # ============================================================
    # ROOM 2 — BEDROOM (MODEL RESULT -> CONTINUE)
    # ============================================================
    elif room == "bedroom":
        show_room("💤 The Bedroom", "Your bedroom is a fancy place. Adorned in expensive tapestries and antique furniture. \nA chandelier hangs in the middle of the room. It is made of glass, refracting the candle flames like little specks of stardust throughout the room. \nYour attire has been carefully laid out on a chair next to your bed. \nIt isn't like the usual bland, black cloak you usually wear. This one is adorned with golden lines and symbols you do not know.")
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
