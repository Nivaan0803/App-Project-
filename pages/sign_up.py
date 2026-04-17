import re

import streamlit as st
import streamlit.components.v1 as components

from auth_store import contains_bad_words, register_user


EMAIL_PATTERN = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
MIN_PASSWORD_LENGTH = 9


def is_valid_email(email):
    return bool(re.match(EMAIL_PATTERN, email.strip()))


def is_valid_password(password):
    return len(password) >= MIN_PASSWORD_LENGTH


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Nunito:wght@700;800&display=swap');

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(244, 215, 191, 0.85), transparent 28%),
                linear-gradient(180deg, #f3efe2 0%, #fcfaf5 100%);
            font-family: 'Lexend', sans-serif;
        }

        .block-container {
            max-width: 860px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .signup-shell {
            background: rgba(255,255,255,0.94);
            border: 1px solid #d8cfbf;
            border-radius: 28px;
            padding: 1.5rem;
            box-shadow: 0 18px 45px rgba(63, 74, 62, 0.08);
        }

        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #f4d7bf;
            color: #8c4d25;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            color: #25424d;
            margin-bottom: 0.3rem;
        }

        .hero-copy {
            color: #55707b;
            margin-bottom: 1rem;
        }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 16px;
            min-height: 3rem;
            font-weight: 700;
            border: none;
            transition: transform 0.16s ease, box-shadow 0.18s ease, filter 0.18s ease;
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


def add_signup_input_styles(valid_email, valid_username, valid_password):
    selectors = []
    if valid_email:
        selectors.append("div[data-testid='stTextInput']:nth-of-type(2) div[data-baseweb='input']")
    if valid_username:
        selectors.append("div[data-testid='stTextInput']:nth-of-type(3) div[data-baseweb='input']")
    if valid_password:
        selectors.append("div[data-testid='stTextInput']:nth-of-type(4) div[data-baseweb='input']")

    if selectors:
        st.markdown(
            f"""
            <style>
            {", ".join(selectors)} {{
                border-color: #7ea37f !important;
                box-shadow: 0 0 0 2px rgba(126, 163, 127, 0.22) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


def top_nav():
    show_help = st.session_state.get("logged_in", False)
    columns = st.columns(3 if show_help else 2)
    col1, col2 = columns[0], columns[1]
    if col1.button("Login", use_container_width=True):
        st.switch_page("login.py")
    col2.button("Sign Up", use_container_width=True, type="primary")
    if show_help:
        col3 = columns[2]
        if col3.button("Help", use_container_width=True):
            st.switch_page("pages/help.py")


st.set_page_config(page_title="Sign Up", page_icon=":memo:", layout="centered")
apply_styles()
apply_button_feedback()

st.markdown("<div class='signup-shell'>", unsafe_allow_html=True)
st.markdown("<div class='eyebrow'>Create a calm care account</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-title'>Set up Memory Lane Companion</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='hero-copy'>Create one account for a senior or family member. After login, you can add reminders for meals, medicine, calls, and game time.</div>",
    unsafe_allow_html=True,
)
top_nav()

full_name = st.text_input("Full name")
email = st.text_input("Email")
username = st.text_input("Choose a username")
password = st.text_input("Create a password", type="password")
confirm_password = st.text_input("Confirm password", type="password")

email_valid = is_valid_email(email)
username_valid = bool(username.strip()) and not contains_bad_words(username)
password_valid = is_valid_password(password)
add_signup_input_styles(email_valid, username_valid, password_valid)

if email.strip():
    if email_valid:
        st.caption("Email format looks correct.")
    else:
        st.error("Enter a valid email address, for example name@example.com.")

if username.strip():
    if username_valid:
        st.caption("Username looks good.")
    else:
        st.error("Username cannot include inappropriate language.")

if password:
    if password_valid:
        st.caption("Password length looks good.")
    else:
        st.error("Password must be more than 8 characters.")

submitted = st.button("Create Account", use_container_width=True)

if submitted:
    if not full_name or not email or not username or not password:
        st.error("Please complete all fields.")
    elif contains_bad_words(full_name):
        st.error("Please remove inappropriate language from the full name.")
    elif not email_valid:
        st.error("Please enter a valid email address.")
    elif not username_valid:
        st.error("Please choose a username without inappropriate language.")
    elif password != confirm_password:
        st.error("Passwords do not match.")
    elif not password_valid:
        st.error("Password must be more than 8 characters.")
    else:
        created, message = register_user(full_name, email, username, password)
        if created:
            st.session_state.pending_email = email.strip().lower()
            st.session_state.auth_notice = message
            st.switch_page("login.py")
        else:
            st.error(message)

st.markdown("</div>", unsafe_allow_html=True)
