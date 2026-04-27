import streamlit as st

from auth_store import get_user, save_settings
from ui_preferences import (
    THEME_OPTIONS,
    apply_user_settings_to_session,
    build_theme_css,
    default_settings,
    normalize_settings,
)


def init_session():
    defaults = default_settings()
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("background_theme", defaults["background_theme"])
    st.session_state.setdefault("familiar_greeting", defaults["familiar_greeting"])
    st.session_state.setdefault("show_familiar_greeting", defaults["show_familiar_greeting"])
    st.session_state.setdefault("text_size", defaults["text_size"])


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1040px",
            extra_css="""
        .hero, .panel {
            background: rgba(255,255,255,0.95);
            border: 1px solid #d8cfbf;
            border-radius: 28px;
            box-shadow: 0 18px 46px rgba(63, 74, 62, 0.08);
        }

        .hero {
            padding: 1.5rem 1.6rem;
            margin-bottom: 1rem;
        }

        .panel {
            padding: 1.2rem 1.25rem;
            margin-bottom: 1rem;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.36rem 0.76rem;
            border-radius: 999px;
            background: #f4d7bf;
            color: #8c4d25;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            font-size: 2.75rem;
            font-weight: 800;
            color: #25424d;
            margin-bottom: 0.25rem;
        }

        .hero-copy {
            color: #55707b;
            font-size: 1.08rem;
            max-width: 42rem;
        }

        .theme-preview-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.7rem;
        }

        .theme-preview {
            border-radius: 22px;
            border: 1px solid #ded3c2;
            min-height: 110px;
            padding: 0.95rem;
            box-shadow: 0 10px 24px rgba(63, 74, 62, 0.06);
        }

        .theme-name {
            font-family: 'Nunito', sans-serif;
            font-size: 1.25rem;
            font-weight: 800;
            color: #25424d;
        }

        .theme-copy {
            color: #55707b;
            margin-top: 0.3rem;
        }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 18px;
            min-height: 3.35rem;
            font-size: 1.03rem;
            font-weight: 700;
            border: none;
        }

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        .stTextArea textarea {
            min-height: 3.25rem !important;
            border-radius: 18px !important;
            font-size: 1.02rem !important;
            background: #fffdf9 !important;
        }

        .stTextArea textarea {
            min-height: 120px !important;
            padding-top: 0.95rem !important;
        }

        @media (max-width: 900px) {
            .theme-preview-grid {
                grid-template-columns: 1fr;
            }
        }
        """,
        ),
        unsafe_allow_html=True,
    )


def apply_user_settings(user):
    return apply_user_settings_to_session(st.session_state, user)


def render_theme_previews():
    st.markdown("<div class='theme-preview-grid'>", unsafe_allow_html=True)
    descriptions = {
        "Warm Cream": "Soft and familiar",
        "Soft Sky": "Cool and airy",
        "Gentle Mint": "Fresh and calm",
        "Rose Morning": "Warm and cozy",
    }
    for theme_name, theme in THEME_OPTIONS.items():
        st.markdown(
            f"""
            <div class='theme-preview' style="background:
                radial-gradient(circle at top left, {theme['glow_left']}, transparent 30%),
                radial-gradient(circle at top right, {theme['glow_right']}, transparent 24%),
                linear-gradient(180deg, {theme['bg_top']} 0%, {theme['bg_bottom']} 100%);">
                <div class='theme-name'>{theme_name}</div>
                <div class='theme-copy'>{descriptions.get(theme_name, 'Calm background')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Settings", page_icon=":gear:", layout="wide")
    init_session()
    if not st.session_state.logged_in or not st.session_state.username:
        st.switch_page("login.py")

    user = get_user(st.session_state.username)
    if not user:
        st.switch_page("login.py")

    settings = apply_user_settings(user)
    apply_styles()

    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Personal comfort settings</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Settings</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-copy'>Choose a calm background, save a familiar greeting, and adjust a few everyday display settings.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader("Background choices")
    st.caption("Pick the background that feels best.")
    render_theme_previews()
    st.markdown("</div>", unsafe_allow_html=True)

    with st.form("settings_form"):
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        selected_theme = st.selectbox("Background theme", list(THEME_OPTIONS.keys()), index=list(THEME_OPTIONS.keys()).index(settings["background_theme"]))
        familiar_greeting = st.text_area(
            "Familiar greeting",
            value=settings["familiar_greeting"],
            height=110,
            placeholder="Hi Mom, we're thinking of you and cheering you on today.",
        )
        show_greeting = st.toggle("Show familiar greeting on dashboard", value=settings["show_familiar_greeting"])
        text_size = st.selectbox("Text size", ["Standard", "Large"], index=0 if settings["text_size"] == "Standard" else 1)
        submitted = st.form_submit_button("Save Settings", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        updated_settings = normalize_settings(
            {
                "background_theme": selected_theme,
                "familiar_greeting": familiar_greeting,
                "show_familiar_greeting": show_greeting,
                "text_size": text_size,
            }
        )
        if save_settings(st.session_state.username, updated_settings):
            st.session_state.background_theme = updated_settings["background_theme"]
            st.session_state.familiar_greeting = updated_settings["familiar_greeting"]
            st.session_state.show_familiar_greeting = updated_settings["show_familiar_greeting"]
            st.session_state.text_size = updated_settings["text_size"]
            st.success("Settings saved.")
            st.rerun()
        else:
            st.error("Unable to save settings right now.")


if __name__ == "__main__":
    main()
