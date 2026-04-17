import base64
import random
import time
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from auth_store import (
    add_loved_one,
    authenticate_user,
    clear_loved_ones,
    get_user,
    save_profile,
    save_progress,
    save_activity_progress,
    save_reminders,
)


ACTIVITIES = {
    "Trivia Puzzles": {
        "type": "choice",
        "prompt": "Which two items usually go together?",
        "question": "Pick the best match.",
        "options": ["Pillow and Bed", "Fork and Rain", "Banana and Shoe"],
        "answer": "Pillow and Bed",
        "success": "That pair belongs together.",
    },
    "Word Warm-Up": {
        "type": "multi_text",
        "prompt": "Write three words that feel calm or happy today.",
        "labels": ["Word 1", "Word 2", "Word 3"],
        "success": "Those words were saved.",
    },
    "Today Noticing": {
        "type": "text",
        "prompt": "What is one thing you can see, hear, or smell right now?",
        "placeholder": "I can hear birds outside.",
        "success": "Your noticing activity was saved.",
    },
    "Memory Game": {
        "type": "memory_game",
        "prompt": "Look at a short list, then answer one question from memory.",
        "sets": [
            {
                "study": ["Apple", "Lamp", "Dog"],
                "question": "Which item was in the list?",
                "options": ["Apple", "Chair", "Cloud"],
                "answer": "Apple",
            },
            {
                "study": ["Rose", "Cup", "Socks"],
                "question": "Which item was in the list?",
                "options": ["Rose", "Plate", "Window"],
                "answer": "Rose",
            },
            {
                "study": ["Book", "Banana", "Clock"],
                "question": "Which item was in the list?",
                "options": ["Clock", "Pillow", "Fork"],
                "answer": "Clock",
            },
        ],
        "success": "Memory game saved.",
    },
    "Matching Game": {
        "type": "matching",
        "prompt": "Match each item to the place or idea that fits best.",
        "sets": [
            {
                "left": ["Toothbrush", "Pillow", "Spoon"],
                "right": ["Bed", "Kitchen", "Bathroom"],
                "answers": {
                    "Toothbrush": "Bathroom",
                    "Pillow": "Bed",
                    "Spoon": "Kitchen",
                },
            },
            {
                "left": ["Coat", "Milk", "Book"],
                "right": ["Refrigerator", "Shelf", "Closet"],
                "answers": {
                    "Coat": "Closet",
                    "Milk": "Refrigerator",
                    "Book": "Shelf",
                },
            },
            {
                "left": ["Soap", "Plate", "Blanket"],
                "right": ["Bathroom", "Bed", "Table"],
                "answers": {
                    "Soap": "Bathroom",
                    "Plate": "Table",
                    "Blanket": "Bed",
                },
            },
        ],
        "success": "Matching game saved.",
    },
}

PUZZLE_BANK = {
    "Category Match": [
        {
            "question": "Which one belongs in the fruit group?",
            "answer": "Apple",
            "options": ["Apple", "Carrot", "Potato"],
        },
        {
            "question": "Which one belongs in the animal group?",
            "answer": "Dog",
            "options": ["Dog", "Oak", "Rose"],
        },
        {
            "question": "Which one belongs in the kitchen group?",
            "answer": "Plate",
            "options": ["Plate", "Blanket", "Curtain"],
        },
        {
            "question": "Which one belongs in the clothing group?",
            "answer": "Sweater",
            "options": ["Sweater", "Lamp", "Curtain"],
        },
        {
            "question": "Which one belongs in the flower group?",
            "answer": "Rose",
            "options": ["Rose", "Oak", "Fern"],
        },
    ],
    "Simple Orientation": [
        {
            "question": "Which season comes after spring?",
            "answer": "Summer",
            "options": ["Summer", "Tuesday", "Lunch"],
        },
        {
            "question": "Which month comes after April?",
            "answer": "May",
            "options": ["May", "Tuesday", "Morning"],
        },
        {
            "question": "Which day comes after Tuesday?",
            "answer": "Wednesday",
            "options": ["Wednesday", "April", "Spring"],
        },
        {
            "question": "Which time of day comes after morning?",
            "answer": "Afternoon",
            "options": ["Afternoon", "Sunday", "May"],
        },
        {
            "question": "Which meal often comes after breakfast?",
            "answer": "Lunch",
            "options": ["Lunch", "April", "Monday"],
        },
    ],
    "Color Finder": [
        {
            "question": "Which word is a shade of blue?",
            "answer": "Navy",
            "options": ["Navy", "Triangle", "Square"],
        },
        {
            "question": "Which word is a shade of red?",
            "answer": "Crimson",
            "options": ["Crimson", "Rectangle", "Circle"],
        },
        {
            "question": "Which word is a shade of green?",
            "answer": "Olive",
            "options": ["Olive", "Oval", "Star"],
        },
        {
            "question": "Which word is a shade of yellow?",
            "answer": "Gold",
            "options": ["Gold", "Triangle", "Diamond"],
        },
        {
            "question": "Which word is a shade of purple?",
            "answer": "Lilac",
            "options": ["Lilac", "Circle", "Heart"],
        },
    ],
}

MOOD_LABELS = {
    "Needs support": 1,
    "A little low": 2,
    "Steady": 3,
    "Good": 4,
    "Very good": 5,
}


def init_session():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("pending_email", "")
    st.session_state.setdefault("auth_notice", "")
    st.session_state.setdefault("reminder_save_feedback", False)
    st.session_state.setdefault("puzzle_round", 0)
    st.session_state.setdefault("memory_game_started", False)
    st.session_state.setdefault("memory_game_ready", False)


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Nunito:wght@600;700&display=swap');

        :root {
            --bg-top: #f3efe2;
            --bg-bottom: #fcfaf5;
            --panel: rgba(255, 255, 255, 0.94);
            --panel-soft: #f7f1e3;
            --line: #d8cfbf;
            --ink: #25424d;
            --muted: #55707b;
            --accent: #cf7c4d;
            --accent-soft: #f4d7bf;
            --calm: #7ea37f;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(244, 215, 191, 0.85), transparent 28%),
                radial-gradient(circle at top right, rgba(126, 163, 127, 0.18), transparent 22%),
                linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
            color: var(--ink);
            font-family: 'Lexend', sans-serif;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1040px;
        }

        h1, h2, h3, .stTabs [data-baseweb="tab"] {
            font-family: 'Nunito', sans-serif;
            color: var(--ink);
        }

        .hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(247, 241, 227, 0.92));
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.5rem 1.5rem 1.3rem 1.5rem;
            box-shadow: 0 20px 50px rgba(63, 74, 62, 0.08);
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.35rem;
            line-height: 1.05;
        }

        .hero-copy {
            color: var(--muted);
            font-size: 1.1rem;
            max-width: 46rem;
        }

        .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            box-shadow: 0 10px 28px rgba(63, 74, 62, 0.06);
        }

        .pill {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: var(--accent-soft);
            color: #8c4d25;
            font-size: 0.92rem;
            font-weight: 600;
            margin-bottom: 0.6rem;
        }

        .reminder-row {
            background: var(--panel-soft);
            border-radius: 18px;
            border: 1px solid #eadfcf;
            padding: 0.8rem 0.95rem;
            margin-bottom: 0.75rem;
        }

        .reminder-time {
            color: #8c4d25;
            font-size: 1.15rem;
            font-weight: 700;
        }

        .reminder-title {
            color: var(--ink);
            font-size: 1.05rem;
            font-weight: 700;
        }

        .quiet {
            color: var(--muted);
        }

        .success-glow {
            background: linear-gradient(135deg, rgba(126, 163, 127, 0.2), rgba(232, 247, 234, 0.96));
            border: 1px solid rgba(126, 163, 127, 0.55);
            border-radius: 22px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
            color: #1f5a33;
            box-shadow: 0 0 0 rgba(126, 163, 127, 0.0);
            animation: reminderGlow 1.2s ease-out 1;
        }

        .success-glow strong {
            display: block;
            font-size: 1.05rem;
            margin-bottom: 0.2rem;
        }

        @keyframes reminderGlow {
            0% {
                box-shadow: 0 0 0 0 rgba(126, 163, 127, 0.0);
                transform: scale(0.985);
            }
            35% {
                box-shadow: 0 0 0 12px rgba(126, 163, 127, 0.18);
                transform: scale(1.01);
            }
            100% {
                box-shadow: 0 0 0 0 rgba(126, 163, 127, 0.0);
                transform: scale(1);
            }
        }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 16px;
            min-height: 3rem;
            font-weight: 700;
            border: none;
            transition: transform 0.16s ease, box-shadow 0.18s ease, filter 0.18s ease, background-color 0.18s ease;
            box-shadow: 0 8px 18px rgba(37, 66, 77, 0.08);
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 24px rgba(37, 66, 77, 0.12);
            filter: saturate(1.03);
        }

        .stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {
            outline: none;
            box-shadow: 0 0 0 4px rgba(126, 163, 127, 0.22), 0 12px 24px rgba(37, 66, 77, 0.12);
        }

        .stButton > button:active, .stFormSubmitButton > button:active {
            transform: scale(0.98);
            box-shadow: 0 0 0 12px rgba(126, 163, 127, 0.18);
        }

        .button-clicked {
            animation: buttonGlowPulse 0.8s ease-out 1;
        }

        @keyframes buttonGlowPulse {
            0% {
                transform: scale(0.98);
                box-shadow: 0 0 0 0 rgba(126, 163, 127, 0.0);
            }
            30% {
                transform: scale(1.02);
                box-shadow: 0 0 0 12px rgba(126, 163, 127, 0.24);
            }
            100% {
                transform: scale(1);
                box-shadow: 0 8px 18px rgba(37, 66, 77, 0.08);
            }
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255,255,255,0.8);
            border: 1px solid var(--line);
            border-radius: 16px;
            padding: 0.75rem 1rem;
            transition: transform 0.16s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 18px rgba(37, 66, 77, 0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def apply_button_feedback():
    components.html(
        """
        <script>
        const CLICKABLE_SELECTORS = [
          '[data-testid="stButton"] button',
          '[data-testid="stFormSubmitButton"] button',
          '[data-baseweb="tab"]'
        ];

        const attachEffects = () => {
          const buttons = window.parent.document.querySelectorAll(CLICKABLE_SELECTORS.join(','));
          buttons.forEach((button) => {
            if (button.dataset.glowBound === 'true') {
              return;
            }
            button.dataset.glowBound = 'true';
            button.addEventListener('click', () => {
              button.classList.remove('button-clicked');
              void button.offsetWidth;
              button.classList.add('button-clicked');
              window.setTimeout(() => button.classList.remove('button-clicked'), 850);
            });
          });
        };

        attachEffects();
        const observer = new MutationObserver(attachEffects);
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )


def top_nav(current_page):
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    show_help = st.session_state.get("logged_in", False)
    columns = st.columns(4 if show_help else 2)
    col1, col2 = columns[0], columns[1]
    if col1.button(
        "Login",
        use_container_width=True,
        type="primary" if current_page == "login" else "secondary",
    ):
        st.switch_page("login.py")
    if col2.button(
        "Sign Up",
        use_container_width=True,
        type="primary" if current_page == "signup" else "secondary",
    ):
        st.switch_page("pages/sign_up.py")
    if show_help:
        col3 = columns[2]
        col4 = columns[3]
        if col3.button(
            "Help",
            use_container_width=True,
            type="primary" if current_page == "help" else "secondary",
        ):
            st.switch_page("pages/help.py")
        if col4.button(
            "Where Am I?",
            use_container_width=True,
            type="primary" if current_page == "where" else "secondary",
        ):
            st.switch_page("pages/where_am_i.py")
    st.markdown("</div>", unsafe_allow_html=True)


def format_part_of_day():
    hour = datetime.now().hour
    if hour < 12:
        return "Morning"
    if hour < 18:
        return "Afternoon"
    return "Evening"


def parse_reminder_time(value):
    try:
        return datetime.strptime(value, "%I:%M %p")
    except ValueError:
        return datetime.max


def render_hero(title, copy):
    st.markdown(
        f"""
        <div class="hero">
            <div class="pill">Calm support for everyday routines</div>
            <div class="hero-title">{title}</div>
            <div class="hero-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def login_view():
    render_hero(
        "Memory Lane Companion",
        "A warm Streamlit space for seniors with dementia: simple check-ins, gentle puzzles, and reminders that family can update.",
    )
    top_nav("login")
    st.subheader("Login")
    st.caption("Enter your email and password to open your care dashboard.")

    if st.session_state.auth_notice:
        st.success(st.session_state.auth_notice)
        st.session_state.auth_notice = ""

    with st.form("login_form"):
        email = st.text_input("Email", value=st.session_state.pending_email)
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Open Dashboard", use_container_width=True)

    if submitted:
        authenticated, user = authenticate_user(email, password)
        if authenticated:
            st.session_state.logged_in = True
            st.session_state.username = user["username"]
            st.session_state.full_name = user["full_name"]
            st.session_state.email = user.get("email", "")
            st.session_state.pending_email = ""
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Incorrect email or password.")


def render_today_snapshot(user):
    profile = user.get("profile", {})
    reminders = sorted(user.get("progress", {}).get("reminders", []), key=lambda item: parse_reminder_time(item.get("time", "")))
    support_name = profile.get("support_name") or "Your family member"
    support_email = profile.get("support_email") or "No support email saved yet"
    support_phone = profile.get("support_phone", "").strip()
    loved_ones = profile.get("loved_ones", [])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Today at a glance")
    col1, col2, col3 = st.columns(3)
    col1.metric("Today", datetime.now().strftime("%B %d"))
    col2.metric("Time of day", format_part_of_day())
    col3.metric("Reminders", len(reminders))
    st.write(f"Support contact: **{support_name}**")
    st.caption(f"{support_email} | {support_phone or 'No support phone saved yet'}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Upcoming reminders")
    if reminders:
        for reminder in reminders:
            note = reminder.get("note", "")
            note_markup = f"<div class='quiet'>{note}</div>" if note else ""
            st.markdown(
                f"""
                <div class="reminder-row">
                    <div class="reminder-time">{reminder.get("time", "Time not set")}</div>
                    <div class="reminder-title">{reminder.get("title", "Reminder")}</div>
                    {note_markup}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No reminders saved yet. A family member can add meals, medicine times, walks, or games.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Family recognition")
    if loved_ones:
        recognition_index = datetime.now().timetuple().tm_yday % len(loved_ones)
        featured = loved_ones[recognition_index]
        name = featured.get("name", "Someone you love")
        relationship = featured.get("relationship", "family member")
        image_data = featured.get("image_data", "")
        if image_data:
            st.image(base64.b64decode(image_data), caption=f"This is your {relationship}, {name}.", use_container_width=True)
        st.success(f"This is your {relationship}, {name}.")

        st.caption("Family gallery")
        columns = st.columns(min(3, len(loved_ones)))
        for index, loved_one in enumerate(loved_ones[:6]):
            with columns[index % len(columns)]:
                if loved_one.get("image_data"):
                    st.image(
                        base64.b64decode(loved_one["image_data"]),
                        caption=f"{loved_one.get('relationship', 'Loved one')}: {loved_one.get('name', '')}",
                        use_container_width=True,
                    )
    else:
        st.info("No family gallery yet. Add photos and names in Family Tools.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_check_in(user):
    progress = user.get("progress", {})
    last_check_in = progress.get("last_check_in", {})

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Daily check-in")
    st.caption("Keep this gentle. One small note is enough.")

    if last_check_in:
        st.write(
            f"Last saved on **{last_check_in.get('saved_at', 'N/A')}** with the activity "
            f"**{last_check_in.get('challenge_name', 'N/A')}**."
        )

    with st.form("progress_form"):
        mood_label = st.select_slider("How are you feeling right now?", options=list(MOOD_LABELS.keys()), value="Steady")
        medicine_taken = st.radio(
            "Have you taken your medicine today?",
            ["Yes", "No", "Not sure"],
            horizontal=True,
        )
        challenge_response = st.text_area(
            "Add a short note about today",
            placeholder="I had breakfast and feel okay.",
            height=120,
        )
        submitted = st.form_submit_button("Save Check-In", use_container_width=True)

    if submitted:
        if not challenge_response.strip():
            st.error("Please add a few words before saving.")
        else:
            saved = save_progress(
                st.session_state.username,
                MOOD_LABELS[mood_label],
                medicine_taken,
                "Daily Note",
                challenge_response.strip(),
            )
            if saved:
                st.success("Check-in saved.")
                st.rerun()
            else:
                st.error("Unable to save progress for this account.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_activities(user):
    activity_history = user.get("progress", {}).get("activity_history", [])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Gentle activities")
    st.caption("Choose one and complete it right here. Each activity saves progress.")

    activity_name = st.selectbox("Choose a gentle activity", list(ACTIVITIES.keys()))
    activity = ACTIVITIES[activity_name]
    st.info(activity["prompt"])

    if activity["type"] == "choice":
        with st.form("activity_choice_form"):
            choice = st.radio(activity["question"], activity["options"])
            submitted = st.form_submit_button("Complete Activity", use_container_width=True)

        if submitted:
            is_correct = choice == activity["answer"]
            score_label = "Completed correctly" if is_correct else "Completed with support"
            details = f"Selected answer: {choice}"
            saved = save_activity_progress(st.session_state.username, activity_name, score_label, details)
            if saved:
                if is_correct:
                    st.success(activity["success"])
                else:
                    st.info(f"Nice try. A helpful answer is {activity['answer']}.")
                st.rerun()
            else:
                st.error("Unable to save this activity.")

    elif activity["type"] == "multi_text":
        with st.form("activity_words_form"):
            words = [st.text_input(label, key=f"{activity_name}_{index}") for index, label in enumerate(activity["labels"])]
            submitted = st.form_submit_button("Complete Activity", use_container_width=True)

        if submitted:
            cleaned_words = [word.strip() for word in words if word.strip()]
            if len(cleaned_words) < 3:
                st.error("Please enter three words.")
            else:
                details = ", ".join(cleaned_words[:3])
                saved = save_activity_progress(st.session_state.username, activity_name, "Completed", details)
                if saved:
                    st.success(activity["success"])
                    st.rerun()
                else:
                    st.error("Unable to save this activity.")

    elif activity["type"] == "text":
        with st.form("activity_text_form"):
            response = st.text_area("Your response", placeholder=activity["placeholder"], height=120)
            submitted = st.form_submit_button("Complete Activity", use_container_width=True)

        if submitted:
            if not response.strip():
                st.error("Please add a response before saving.")
            else:
                saved = save_activity_progress(st.session_state.username, activity_name, "Completed", response.strip())
                if saved:
                    st.success(activity["success"])
                    st.rerun()
                else:
                    st.error("Unable to save this activity.")

    elif activity["type"] == "memory_game":
        round_index = st.session_state.get("memory_game_round", 0) % len(activity["sets"])
        game = activity["sets"][round_index]
        if not st.session_state.memory_game_started and not st.session_state.memory_game_ready:
            st.write("Press start to study the items for a few seconds.")
            if st.button("Start Memory Round", use_container_width=True):
                st.session_state.memory_game_started = True
                st.rerun()

        elif st.session_state.memory_game_started and not st.session_state.memory_game_ready:
            list_placeholder = st.empty()
            countdown_placeholder = st.empty()
            list_placeholder.markdown(f"**{' | '.join(game['study'])}**")
            for seconds_left in range(5, 0, -1):
                countdown_placeholder.info(f"Study these items. The list will disappear in {seconds_left} seconds.")
                time.sleep(1)
            list_placeholder.empty()
            countdown_placeholder.empty()
            st.session_state.memory_game_started = False
            st.session_state.memory_game_ready = True
            st.rerun()

        elif st.session_state.memory_game_ready:
            st.caption("The study list is hidden now. Answer from memory.")
            with st.form("activity_memory_form"):
                choice = st.radio(game["question"], game["options"])
                submitted = st.form_submit_button("Complete Activity", use_container_width=True)

            if submitted:
                is_correct = choice == game["answer"]
                score_label = "Completed correctly" if is_correct else "Completed with support"
                details = f"Study list: {', '.join(game['study'])} | Selected: {choice}"
                saved = save_activity_progress(st.session_state.username, activity_name, score_label, details)
                if saved:
                    st.session_state.memory_game_round = round_index + 1
                    st.session_state.memory_game_started = False
                    st.session_state.memory_game_ready = False
                    if is_correct:
                        st.success(activity["success"])
                    else:
                        st.info(f"Nice try. The item from the list was {game['answer']}.")
                    st.rerun()
                else:
                    st.error("Unable to save this activity.")

    elif activity["type"] == "matching":
        round_index = st.session_state.get("matching_game_round", 0) % len(activity["sets"])
        game = activity["sets"][round_index]
        with st.form("activity_matching_form"):
            st.write("Choose the best match for each item.")
            selections = {}
            for item in game["left"]:
                selections[item] = st.selectbox(
                    item,
                    game["right"],
                    key=f"match_{round_index}_{item}",
                )
            submitted = st.form_submit_button("Complete Activity", use_container_width=True)

        if submitted:
            correct_count = sum(1 for item, answer in game["answers"].items() if selections.get(item) == answer)
            score_label = f"{correct_count} of {len(game['left'])} correct"
            details = ", ".join(f"{item}: {selections[item]}" for item in game["left"])
            saved = save_activity_progress(st.session_state.username, activity_name, score_label, details)
            if saved:
                st.session_state.matching_game_round = round_index + 1
                if correct_count == len(game["left"]):
                    st.success(activity["success"])
                else:
                    st.info(f"You matched {correct_count} out of {len(game['left'])} correctly.")
                st.rerun()
            else:
                st.error("Unable to save this activity.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Saved activity progress")
    if activity_history:
        for item in activity_history[:6]:
            st.write(
                f"**{item.get('saved_at', 'N/A')}** | {item.get('activity_name', 'Activity')} | "
                f"{item.get('score_label', 'Completed')}"
            )
            st.caption(item.get("details", ""))
    else:
        st.write("No activities completed yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def build_puzzle_set(seed_value, puzzle_count=3):
    random.seed(seed_value)
    puzzles = []
    for title, entries in PUZZLE_BANK.items():
        entry = random.choice(entries)
        options = entry["options"][:]
        random.shuffle(options)
        puzzles.append(
            {
                "title": title,
                "question": entry["question"],
                "answer": entry["answer"],
                "options": options,
            }
        )
    random.shuffle(puzzles)
    return puzzles[:puzzle_count]


def render_puzzles():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Calm puzzle corner")
    st.caption("These are simple and low-pressure. Use Next Questions for a fresh set anytime.")

    puzzle_seed = f"{st.session_state.username}-{st.session_state.puzzle_round}"
    puzzles = build_puzzle_set(puzzle_seed)

    for index, puzzle in enumerate(puzzles):
        with st.form(f"puzzle_{index}"):
            st.markdown(f"**{puzzle['title']}**")
            choice = st.radio(puzzle["question"], puzzle["options"], key=f"choice_{index}")
            submitted = st.form_submit_button("Check Answer", use_container_width=True)

        if submitted:
            if choice == puzzle["answer"]:
                st.success("Nice work. That answer is correct.")
            else:
                st.info(f"The best match is {puzzle['answer']}.")

    if st.button("Next Questions", use_container_width=True):
        st.session_state.puzzle_round += 1
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_recent_history(user):
    history = user.get("progress", {}).get("history", [])
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Recent check-ins")
    if history:
        for item in history[:5]:
            st.write(
                f"**{item.get('saved_at', 'N/A')}** | Mood {item.get('mood', 'N/A')} | "
                f"{item.get('challenge_name', 'N/A')}"
            )
            st.caption(item.get("challenge_response", ""))
    else:
        st.write("No check-ins saved yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_family_tools(user):
    profile = user.get("profile", {})
    reminders = user.get("progress", {}).get("reminders", [])
    loved_ones = profile.get("loved_ones", [])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Family and caregiver settings")
    with st.form("profile_form"):
        role = st.selectbox(
            "Who usually uses this account?",
            ["senior", "family"],
            index=0 if profile.get("role", "senior") == "senior" else 1,
        )
        support_name = st.text_input("Primary support person", value=profile.get("support_name", ""))
        support_email = st.text_input("Support email", value=profile.get("support_email", ""))
        support_phone = st.text_input("Support phone", value=profile.get("support_phone", ""), placeholder="555-123-4567")
        submitted = st.form_submit_button("Save Contact Details", use_container_width=True)

    if submitted:
        if save_profile(st.session_state.username, role, support_name, support_email, support_phone):
            st.success("Contact details updated.")
            st.rerun()
        else:
            st.error("Unable to save contact details.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Family gallery")
    st.caption("Upload a loved one's photo with their name and relationship to create personalized reminders.")
    with st.form("loved_one_form"):
        loved_one_name = st.text_input("Loved one's name", placeholder="Sarah")
        relationship = st.text_input("Relationship", placeholder="daughter")
        photo = st.file_uploader("Family photo", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("Add to Gallery", use_container_width=True)

    if submitted:
        if not loved_one_name.strip() or not relationship.strip() or photo is None:
            st.error("Please add a name, relationship, and photo.")
        else:
            saved = add_loved_one(
                st.session_state.username,
                loved_one_name,
                relationship,
                photo.getvalue(),
                photo.type or "image/jpeg",
            )
            if saved:
                st.success("Family photo added.")
                st.rerun()
            else:
                st.error("Unable to save this family photo.")

    if loved_ones:
        gallery_columns = st.columns(min(3, len(loved_ones)))
        for index, loved_one in enumerate(loved_ones[:9]):
            with gallery_columns[index % len(gallery_columns)]:
                if loved_one.get("image_data"):
                    st.image(
                        base64.b64decode(loved_one["image_data"]),
                        caption=f"{loved_one.get('relationship', 'Loved one')}: {loved_one.get('name', '')}",
                        use_container_width=True,
                    )
        if st.button("Clear Family Gallery", use_container_width=True):
            if clear_loved_ones(st.session_state.username):
                st.success("Family gallery cleared.")
                st.rerun()
            else:
                st.error("Unable to clear the family gallery.")
    else:
        st.write("No loved ones saved yet.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Reminder planner")
    st.caption("Use short titles such as Dinner, Medicine, Walk, Bible Study, or Game Time.")

    if st.session_state.reminder_save_feedback:
        st.markdown(
            """
            <div class="success-glow">
                <strong>Reminders saved</strong>
                The schedule was updated successfully.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.reminder_save_feedback = False

    reminder_count = st.slider("How many reminders would you like to show?", 1, 6, max(3, len(reminders) or 3))
    with st.form("reminder_form"):
        reminder_entries = []
        for index in range(reminder_count):
            existing = reminders[index] if index < len(reminders) else {}
            st.markdown(f"**Reminder {index + 1}**")
            col1, col2 = st.columns([2, 1])
            title = col1.text_input(
                "Title",
                value=existing.get("title", ""),
                key=f"title_{index}",
                placeholder="Dinner time",
            )
            default_time = datetime.strptime(existing.get("time", "06:00 PM"), "%I:%M %p").time() if existing.get("time") else datetime.strptime("06:00 PM", "%I:%M %p").time()
            reminder_time = col2.time_input("Time", value=default_time, key=f"time_{index}", step=1800)
            note = st.text_input(
                "Helpful note",
                value=existing.get("note", ""),
                key=f"note_{index}",
                placeholder="Family will call after this.",
            )
            reminder_entries.append(
                {
                    "title": title,
                    "time": reminder_time.strftime("%I:%M %p"),
                    "note": note,
                }
            )
        submitted = st.form_submit_button("Save Reminders", use_container_width=True)

    if submitted:
        if save_reminders(st.session_state.username, reminder_entries):
            st.session_state.reminder_save_feedback = True
            st.rerun()
        else:
            st.error("Unable to save reminders.")
    st.markdown("</div>", unsafe_allow_html=True)


def dashboard_view():
    user = get_user(st.session_state.username)
    progress = user.get("progress", {}) if user else {}

    render_hero(
        f"Welcome, {st.session_state.full_name}",
        "This dashboard keeps everyday routines visible and calm. Open reminders, save a short check-in, and use the puzzle corner whenever it feels helpful.",
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Check-ins saved", progress.get("total_sessions", 0))
    col2.metric("Activities completed", progress.get("completed_challenges", 0))
    col3.metric("Support reminders", len(progress.get("reminders", [])))

    tab1, tab2, tab3 = st.tabs(["Today", "Activities", "Family Tools"])

    with tab1:
        render_today_snapshot(user)
        render_check_in(user)
        render_recent_history(user)

    with tab2:
        render_activities(user)
        render_puzzles()

    with tab3:
        render_family_tools(user)

    if st.button("Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.email = ""
        st.session_state.pending_email = ""
        st.rerun()


def main():
    st.set_page_config(page_title="Memory Lane Companion", page_icon=":sunflower:", layout="wide")
    init_session()
    apply_styles()
    apply_button_feedback()

    if st.session_state.logged_in:
        dashboard_view()
    else:
        login_view()


if __name__ == "__main__":
    main()
