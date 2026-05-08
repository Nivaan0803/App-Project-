import base64
import os
import random
import sys
import time
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from auth_store import (
    add_loved_one,
    authenticate_user,
    clear_password_reset,
    clear_loved_ones,
    create_password_reset,
    get_user,
    reset_password_with_code,
    save_profile,
    save_progress,
    save_activity_progress,
    save_reminders,
)
from ui_preferences import default_settings, get_theme, normalize_settings


MIN_PASSWORD_LENGTH = 9
RESET_CODE_EXPIRY_MINUTES = 15


def _asset_path(relative_path: str) -> str:
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path))


VISUAL_ASSET_FILES = {
    "Apple": "assets/visuals/apple.png",
    "Banana": "assets/visuals/banana.png",
    "Bathroom": "assets/visuals/bathroom.png",
    "Bed": "assets/visuals/bed.png",
    "Blanket": "assets/visuals/blanket.png",
    "Book": "assets/visuals/book.png",
    "Chocolate": "assets/visuals/chocolate.png",
    "Clock": "assets/visuals/clock.png",
    "Closet": "assets/visuals/closet.png",
    "Coat": "assets/visuals/coat.png",
    "Dog": "assets/visuals/dog.png",
    "Kitchen": "assets/visuals/kitchen.png",
    "Lamp": "assets/visuals/lamp.png",
    "Milk": "assets/visuals/milk.png",
    "Pillow": "assets/visuals/pillow.png",
    "Plate": "assets/visuals/plate.png",
    "Refrigerator": "assets/visuals/refrigerator.png",
    "Rose": "assets/visuals/rose.png",
    "Shelf": "assets/visuals/shelf.png",
    "Soap": "assets/visuals/soap.png",
    "Socks": "assets/visuals/socks.png",
    "Spoon": "assets/visuals/spoon.png",
    "Table": "assets/visuals/table.png",
    "Toothbrush": "assets/visuals/toothbrush.png",
}


def _visual_asset(name: str) -> str:
    relative_path = VISUAL_ASSET_FILES.get(name)
    if not relative_path:
        return ""
    return _asset_path(relative_path)


def _secret_or_env(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
        smtp_section = st.secrets.get("smtp", {})
        section_key = name.lower().replace("smtp_", "")
        if hasattr(smtp_section, "get"):
            value = smtp_section.get(section_key)
            if value is not None:
                return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def _to_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def send_password_reset_email(recipient_email: str, reset_code: str):
    project_root = os.path.dirname(os.path.abspath(__file__))
    removed_paths = []
    for candidate in ("", project_root):
        while candidate in sys.path:
            sys.path.remove(candidate)
            removed_paths.append(candidate)

    sys.modules.pop("calendar", None)
    try:
        import smtplib
        from email.message import EmailMessage
    finally:
        for candidate in reversed(removed_paths):
            sys.path.insert(0, candidate)

    smtp_host = _secret_or_env("SMTP_HOST")
    smtp_port = int(_secret_or_env("SMTP_PORT", "587"))
    smtp_username = _secret_or_env("SMTP_USERNAME")
    smtp_password = _secret_or_env("SMTP_PASSWORD")
    from_email = _secret_or_env("SMTP_FROM_EMAIL", smtp_username)
    from_name = _secret_or_env("SMTP_FROM_NAME", "Mindful")
    use_tls = _to_bool(_secret_or_env("SMTP_USE_TLS", "true"), default=True)
    use_ssl = _to_bool(_secret_or_env("SMTP_USE_SSL", "false"))

    if not smtp_host or not from_email:
        return False, "Email sending is not configured yet. Add SMTP settings before using password reset."

    message = EmailMessage()
    message["Subject"] = "Your Mindful password reset code"
    message["From"] = f"{from_name} <{from_email}>"
    message["To"] = recipient_email
    message.set_content(
        "\n".join(
            [
                "A password reset was requested for your Mindful account.",
                "",
                f"Your reset code is: {reset_code}",
                f"This code expires in {RESET_CODE_EXPIRY_MINUTES} minutes.",
                "",
                "If you did not request this change, you can ignore this email.",
            ]
        )
    )

    try:
        if use_ssl:
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
                server.ehlo()
                if use_tls:
                    server.starttls()
                    server.ehlo()
                if smtp_username:
                    server.login(smtp_username, smtp_password)
                server.send_message(message)
    except Exception as exc:
        return False, f"Unable to send reset email right now: {exc}"

    return True, "Reset email sent."


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
                "study": ["Rose", "Chocolate", "Socks"],
                "question": "Which item was in the list?",
                "options": ["Chocolate", "Plate", "Window"],
                "answer": "Chocolate",
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
    "Memory Match": {
        "type": "matching",
        "prompt": "Match each picture on the left to the place it belongs. Use the place pictures below as a guide.",
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
        "success": "Memory Match saved.",
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
    st.session_state.setdefault("background_theme", default_settings()["background_theme"])
    st.session_state.setdefault("familiar_greeting", default_settings()["familiar_greeting"])
    st.session_state.setdefault("show_familiar_greeting", default_settings()["show_familiar_greeting"])
    st.session_state.setdefault("text_size", default_settings()["text_size"])
    st.session_state.setdefault("password_reset_email", "")
    st.session_state.setdefault("password_reset_notice", "")


def apply_styles():
    theme = get_theme(st.session_state.get("background_theme", default_settings()["background_theme"]))
    text_size = st.session_state.get("text_size", "Standard")
    body_font_size = "1.06rem" if text_size == "Large" else "1rem"
    title_scale = "3.05rem" if text_size == "Large" else "2.85rem"
    css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Nunito:wght@600;700&display=swap');

        :root {
            --bg-top: __BG_TOP__;
            --bg-bottom: __BG_BOTTOM__;
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
                radial-gradient(circle at top left, __GLOW_LEFT__, transparent 28%),
                radial-gradient(circle at top right, __GLOW_RIGHT__, transparent 22%),
                linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
            color: var(--ink);
            font-family: 'Lexend', sans-serif;
            font-size: __BODY_SIZE__;
        }

        .block-container {
            padding-top: 1.55rem;
            padding-bottom: 3rem;
            max-width: 1120px;
        }

        h1, h2, h3, .stTabs [data-baseweb="tab"] {
            font-family: 'Nunito', sans-serif;
            color: var(--ink);
        }

        .hero {
            background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(247, 241, 227, 0.92));
            border: 1px solid var(--line);
            border-radius: 30px;
            padding: 1.65rem 1.65rem 1.45rem 1.65rem;
            box-shadow: 0 22px 54px rgba(63, 74, 62, 0.09);
            margin-bottom: 1rem;
        }

        .hero-title {
            font-size: __TITLE_SCALE__;
            font-weight: 800;
            margin-bottom: 0.35rem;
            line-height: 1.05;
        }

        .hero-copy {
            color: var(--muted);
            font-size: 1.12rem;
            max-width: 48rem;
        }

        .card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 26px;
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
            box-shadow: 0 12px 32px rgba(63, 74, 62, 0.07);
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
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247, 241, 227, 0.92));
            border-radius: 22px;
            border: 1px solid #eadfcf;
            border-left: 10px solid #d98b3a;
            padding: 1rem 1.05rem;
            margin-bottom: 0.85rem;
            box-shadow: 0 10px 24px rgba(63, 74, 62, 0.06);
        }

        .reminder-time {
            color: #8c4d25;
            font-size: 1.18rem;
            font-weight: 800;
            margin-bottom: 0.15rem;
        }

        .reminder-title {
            color: var(--ink);
            font-size: 1.08rem;
            font-weight: 800;
            margin-bottom: 0.1rem;
        }

        .quiet {
            color: var(--muted);
        }

        .snapshot-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.7rem;
            margin-bottom: 1rem;
        }

        .snapshot-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(247, 241, 227, 0.92));
            border: 1px solid #e2d8c8;
            border-radius: 22px;
            padding: 1rem 1.05rem;
            box-shadow: 0 10px 24px rgba(63, 74, 62, 0.05);
        }

        .snapshot-label {
            color: #7c6a58;
            font-size: 0.9rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.22rem;
        }

        .snapshot-value {
            color: var(--ink);
            font-family: 'Nunito', sans-serif;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
        }

        .contact-strip {
            background: rgba(255,255,255,0.84);
            border: 1px solid #e5dbcb;
            border-radius: 18px;
            padding: 0.95rem 1rem;
            margin-top: 0.25rem;
        }

        .contact-name {
            color: var(--ink);
            font-weight: 800;
            margin-bottom: 0.18rem;
        }

        .contact-meta {
            color: var(--muted);
            font-size: 0.95rem;
        }

        @media (max-width: 900px) {
            .snapshot-grid {
                grid-template-columns: 1fr;
            }
        }

        .history-list {
            display: grid;
            gap: 0.8rem;
            margin-top: 0.4rem;
        }

        .history-item {
            background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(247, 241, 227, 0.82));
            border: 1px solid #e3d8c7;
            border-radius: 20px;
            padding: 0.95rem 1rem;
            box-shadow: 0 10px 22px rgba(63, 74, 62, 0.05);
        }

        .history-topline {
            color: var(--ink);
            font-weight: 800;
            font-size: 1rem;
            margin-bottom: 0.15rem;
        }

        .history-meta {
            color: #8c5a30;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .history-note {
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.45;
        }

        .footer-action {
            background: linear-gradient(180deg, rgba(255,255,255,0.97), rgba(247, 241, 227, 0.88));
            border: 1px solid var(--line);
            border-radius: 24px;
            padding: 1rem;
            margin-top: 0.2rem;
            box-shadow: 0 12px 28px rgba(63, 74, 62, 0.06);
        }

        .footer-copy {
            color: var(--muted);
            text-align: center;
            font-size: 0.98rem;
            margin-bottom: 0.75rem;
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
            border-radius: 18px;
            min-height: 3.35rem;
            font-size: 1.03rem;
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
            border-radius: 18px;
            padding: 0.95rem 1.15rem;
            font-size: 1.03rem;
            transition: transform 0.16s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }

        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 18px rgba(37, 66, 77, 0.08);
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        .stDateInput > div > div,
        .stTextArea textarea {
            min-height: 3.25rem !important;
            border-radius: 18px !important;
            font-size: 1.02rem !important;
            background: #fffdf9 !important;
        }

        .stTextArea textarea {
            min-height: 130px !important;
            padding-top: 0.95rem !important;
        }

        label, .stMarkdown p, .stCaption {
            font-size: 1rem !important;
        }
        </style>
        """
    css = (
        css.replace("__BG_TOP__", theme["bg_top"])
        .replace("__BG_BOTTOM__", theme["bg_bottom"])
        .replace("__GLOW_LEFT__", theme["glow_left"])
        .replace("__GLOW_RIGHT__", theme["glow_right"])
        .replace("__BODY_SIZE__", body_font_size)
        .replace("__TITLE_SCALE__", title_scale)
    )
    st.markdown(
        css,
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


def parse_time_label(value, fallback):
    raw_value = value or fallback
    try:
        parsed = datetime.strptime(raw_value, "%I:%M %p")
        return parsed.strftime("%I:%M %p")
    except ValueError:
        return datetime.strptime(fallback, "%I:%M %p").strftime("%I:%M %p")


def render_time_picker(prefix, label, default_value):
    normalized_default = parse_time_label(default_value, "06:00 PM")
    time_options = [
        datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").strftime("%I:%M %p")
        for hour in range(24)
        for minute in (0, 30)
    ]
    default_index = time_options.index(normalized_default) if normalized_default in time_options else time_options.index("06:00 PM")
    return st.selectbox(label, time_options, index=default_index, key=f"{prefix}_time")


def render_visual_card_grid(names, caption=None):
    if caption:
        st.caption(caption)
    columns = st.columns(len(names))
    for index, name in enumerate(names):
        with columns[index]:
            asset_path = _visual_asset(name)
            if asset_path:
                st.image(asset_path, use_container_width=True)
            st.caption(name)


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


def apply_user_settings(user):
    settings = normalize_settings(user.get("profile", {}).get("settings", {}))
    st.session_state.background_theme = settings["background_theme"]
    st.session_state.familiar_greeting = settings["familiar_greeting"]
    st.session_state.show_familiar_greeting = settings["show_familiar_greeting"]
    st.session_state.text_size = settings["text_size"]


def render_password_reset():
    reset_expanded = bool(st.session_state.password_reset_email or st.session_state.password_reset_notice)

    with st.expander("Forgot your password?", expanded=reset_expanded):
        st.caption("Request a 6-digit code by email, then enter it below to create a new password.")

        if st.session_state.password_reset_notice:
            st.info(st.session_state.password_reset_notice)
            st.session_state.password_reset_notice = ""

        with st.form("request_reset_code_form"):
            request_email = st.text_input(
                "Account email",
                value=st.session_state.password_reset_email or st.session_state.pending_email,
                key="request_reset_email",
            )
            requested = st.form_submit_button("Send Reset Code", use_container_width=True)

        if requested:
            if not request_email.strip():
                st.error("Enter the email address for the account.")
            else:
                reset_email = request_email.strip().lower()
                reset_code = f"{random.randint(0, 999999):06d}"
                created, message = create_password_reset(
                    reset_email,
                    reset_code,
                    expiry_minutes=RESET_CODE_EXPIRY_MINUTES,
                )
                if created:
                    sent, send_message = send_password_reset_email(reset_email, reset_code)
                    if sent:
                        st.session_state.password_reset_email = reset_email
                        st.session_state.pending_email = reset_email
                        st.session_state.password_reset_notice = (
                            f"A reset code was sent to {reset_email}. It expires in "
                            f"{RESET_CODE_EXPIRY_MINUTES} minutes."
                        )
                        st.rerun()
                    else:
                        clear_password_reset(reset_email)
                        st.error(send_message)
                else:
                    st.error(message)

        with st.form("reset_password_form"):
            reset_email = st.text_input(
                "Email for reset",
                value=st.session_state.password_reset_email or st.session_state.pending_email,
                key="confirm_reset_email",
            )
            reset_code = st.text_input("Reset code", max_chars=6, key="confirm_reset_code")
            new_password = st.text_input("New password", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            reset_submitted = st.form_submit_button("Reset Password", use_container_width=True)

        if reset_submitted:
            if not reset_email.strip() or not reset_code.strip() or not new_password or not confirm_password:
                st.error("Complete all password reset fields.")
            elif len(new_password) < MIN_PASSWORD_LENGTH:
                st.error("Your new password must be more than 8 characters.")
            elif new_password != confirm_password:
                st.error("New passwords do not match.")
            else:
                reset_done, reset_message = reset_password_with_code(
                    reset_email.strip().lower(),
                    reset_code.strip(),
                    new_password,
                )
                if reset_done:
                    st.session_state.password_reset_email = ""
                    st.session_state.pending_email = reset_email.strip().lower()
                    st.session_state.auth_notice = "Password reset complete. Please log in with your new password."
                    st.rerun()
                else:
                    st.error(reset_message)


def login_view():
    render_hero(
        "Mindful",
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
            apply_user_settings(user)
            st.success("Login successful.")
            st.rerun()
        else:
            st.error("Incorrect email or password.")

    render_password_reset()


def render_today_snapshot(user):
    profile = user.get("profile", {})
    reminders = sorted(user.get("progress", {}).get("reminders", []), key=lambda item: parse_reminder_time(item.get("time", "")))
    support_name = profile.get("support_name") or "Your family member"
    support_email = profile.get("support_email") or "No support email saved yet"
    support_phone = profile.get("support_phone", "").strip()
    loved_ones = profile.get("loved_ones", [])

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Today at a glance")
    st.markdown(
        f"""
        <div class='snapshot-grid'>
            <div class='snapshot-card'>
                <div class='snapshot-label'>Today</div>
                <div class='snapshot-value'>{datetime.now().strftime("%B %d")}</div>
            </div>
            <div class='snapshot-card'>
                <div class='snapshot-label'>Time of day</div>
                <div class='snapshot-value'>{format_part_of_day()}</div>
            </div>
            <div class='snapshot-card'>
                <div class='snapshot-label'>Reminders</div>
                <div class='snapshot-value'>{len(reminders)}</div>
            </div>
        </div>
        <div class='contact-strip'>
            <div class='contact-name'>Support contact: {support_name}</div>
            <div class='contact-meta'>{support_email} | {support_phone or 'No support phone saved yet'}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
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
        st.write("Open the Family Recognition page in the left sidebar to see loved ones' photos and play saved voice messages.")
        if st.button("Open Family Recognition", use_container_width=True):
            st.switch_page("pages/family_recognition.py")
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
            render_visual_card_grid(game["study"], "Look at each item before starting the round.")
            if st.button("Start Memory Round", use_container_width=True):
                st.session_state.memory_game_started = True
                st.rerun()

        elif st.session_state.memory_game_started and not st.session_state.memory_game_ready:
            list_placeholder = st.empty()
            countdown_placeholder = st.empty()
            with list_placeholder.container():
                render_visual_card_grid(game["study"], "Study these items. The pictures will disappear soon.")
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
            st.caption("Choose the best place for each picture.")
            render_visual_card_grid(game["right"], "Places to choose from")
            selections = {}
            for item in game["left"]:
                row = st.columns([1, 1.15])
                with row[0]:
                    asset_path = _visual_asset(item)
                    if asset_path:
                        st.image(asset_path, use_container_width=True)
                    st.caption(item)
                with row[1]:
                    selections[item] = st.selectbox(
                        f"Where does {item} belong?",
                        game["right"],
                        key=f"match_{round_index}_{item}",
                        label_visibility="visible",
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
        st.markdown("<div class='history-list'>", unsafe_allow_html=True)
        for item in history[:5]:
            st.markdown(
                f"""
                <div class='history-item'>
                    <div class='history-topline'>{item.get('challenge_name', 'Check-in')}</div>
                    <div class='history-meta'>{item.get('saved_at', 'N/A')} | Mood {item.get('mood', 'N/A')}</div>
                    <div class='history-note'>{item.get('challenge_response', '') or 'No note saved.'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.write("No check-ins saved yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_family_tools(user, show_gallery_preview=None):
    profile = user.get("profile", {})
    reminders = user.get("progress", {}).get("reminders", [])
    loved_ones = profile.get("loved_ones", [])
    if show_gallery_preview is None:
        show_gallery_preview = st.session_state.get("family_tools_show_gallery_preview", True)

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
    st.caption("Add a photo and optionally record a voice message. You can listen first, then save it to the Family Recognition page.")
    loved_one_name = st.text_input("Loved one's name", placeholder="Sarah")
    relationship = st.text_input("Relationship", placeholder="daughter")
    photo = st.file_uploader("Family photo", type=["jpg", "jpeg", "png"])
    audio_recorder = getattr(st, "audio_input", None)
    voice_note = audio_recorder("Record a short voice message (optional)") if callable(audio_recorder) else None
    voice_upload = st.file_uploader("Or upload a voice message (optional)", type=["wav", "mp3", "m4a", "ogg"])
    audio_source = voice_note if voice_note is not None else voice_upload

    if photo is not None:
        st.caption("Photo preview")
        st.image(photo.getvalue(), use_container_width=True)

    if audio_source is not None:
        st.caption("Voice message preview")
        st.audio(audio_source.getvalue(), format=audio_source.type or "audio/wav")

    submitted = st.button("Save to Family Recognition", use_container_width=True)

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
                audio_source.getvalue() if audio_source is not None else None,
                audio_source.type if audio_source is not None else "",
            )
            if saved:
                st.success("Saved to the Family Recognition page.")
                st.rerun()
            else:
                st.error("Unable to save this family photo.")

    if loved_ones:
        if show_gallery_preview:
            featured_loved_one = loved_ones[0]
            if featured_loved_one.get("image_data"):
                st.image(
                    base64.b64decode(featured_loved_one["image_data"]),
                    caption=f"{featured_loved_one.get('relationship', 'Loved one')}: {featured_loved_one.get('name', '')}",
                    use_container_width=True,
                )
            if featured_loved_one.get("audio_data"):
                st.caption(f"Voice note from {featured_loved_one.get('name', 'family')}")
                st.audio(
                    base64.b64decode(featured_loved_one["audio_data"]),
                    format=featured_loved_one.get("audio_mime_type") or "audio/wav",
                )
            if len(loved_ones) > 1:
                st.caption(f"{len(loved_ones)} family entries are saved.")
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
            with col2:
                reminder_time = render_time_picker(f"time_{index}", "Time", existing.get("time", "06:00 PM"))
            note = st.text_input(
                "Helpful note",
                value=existing.get("note", ""),
                key=f"note_{index}",
                placeholder="Family will call after this.",
            )
            reminder_entries.append(
                {
                    "title": title,
                    "time": reminder_time,
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
    if user:
        apply_user_settings(user)

    render_hero(
        f"Welcome, {st.session_state.full_name}",
        "This dashboard keeps everyday routines visible and calm. Open reminders, save a short check-in, and use the puzzle corner whenever it feels helpful.",
    )
    familiar_greeting = st.session_state.get("familiar_greeting", "").strip()
    if st.session_state.get("show_familiar_greeting", True) and familiar_greeting:
        st.markdown(
            f"""
            <div class='card' style="background: linear-gradient(135deg, rgba(255,255,255,0.98), rgba(244, 215, 191, 0.82));">
                <div class='pill'>Familiar greeting</div>
                <div style="font-family: 'Nunito', sans-serif; font-size: 1.8rem; font-weight: 800; color: #25424d;">{familiar_greeting}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col1, col2, col3 = st.columns(3)
    col1.metric("Check-ins saved", progress.get("total_sessions", 0))
    col2.metric("Activities completed", progress.get("completed_challenges", 0))
    col3.metric("Support reminders", len(progress.get("reminders", [])))

    tab1, tab2 = st.tabs(["Today", "Activities"])

    with tab1:
        render_today_snapshot(user)
        render_check_in(user)
        render_recent_history(user)

    with tab2:
        render_activities(user)
        render_puzzles()

    st.markdown(
        """
        <div class='footer-action'>
            <div class='footer-copy'>When you are finished, you can safely sign out here.</div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Log Out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.email = ""
        st.session_state.pending_email = ""
        st.session_state.password_reset_email = ""
        st.session_state.password_reset_notice = ""
        st.session_state.background_theme = default_settings()["background_theme"]
        st.session_state.familiar_greeting = default_settings()["familiar_greeting"]
        st.session_state.show_familiar_greeting = default_settings()["show_familiar_greeting"]
        st.session_state.text_size = default_settings()["text_size"]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Mindful", page_icon=":sunflower:", layout="wide")
    init_session()
    apply_styles()
    apply_button_feedback()

    if st.session_state.logged_in:
        dashboard_view()
    else:
        login_view()


if __name__ == "__main__":
    main()
