import base64
from datetime import datetime

import streamlit as st

from auth_store import get_user
from login import render_family_tools
from ui_preferences import apply_user_settings_to_session, build_theme_css, default_settings


def init_session():
    defaults = default_settings()
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("background_theme", defaults["background_theme"])
    st.session_state.setdefault("familiar_greeting", defaults["familiar_greeting"])
    st.session_state.setdefault("show_familiar_greeting", defaults["show_familiar_greeting"])
    st.session_state.setdefault("text_size", defaults["text_size"])


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1120px",
            extra_css="""
        .hero, .panel {
            background: var(--panel-bg);
            border: 1px solid var(--line-color);
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
            background: var(--accent-soft);
            color: #8c4d25;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            font-size: 2.75rem;
            font-weight: 800;
            color: var(--ink-color);
            margin-bottom: 0.25rem;
        }

        .hero-copy, .memory-copy {
            color: var(--muted-color);
            font-size: 1.08rem;
        }

        .memory-name {
            font-family: 'Nunito', sans-serif;
            font-size: 1.9rem;
            font-weight: 800;
            color: #25424d;
            margin-top: 0.8rem;
            margin-bottom: 0.15rem;
        }

        .memory-role {
            color: #7b6552;
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
        }

        .featured-audio {
            margin-bottom: 1rem;
        }

        .count-copy {
            color: #7b6552;
            font-size: 0.98rem;
            margin-top: 0.6rem;
        }
        """,
        ),
        unsafe_allow_html=True,
    )


def render_page(user):
    loved_ones = user.get("profile", {}).get("loved_ones", [])

    st.markdown("<div class='hero'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Photos and familiar voices</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Family Recognition</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-copy'>This page keeps loved ones together in one place so photos and voice messages are easy to revisit.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if not loved_ones:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("No family gallery yet")
        st.write("Use the family tools below to add photos and optional voice messages to this page.")
        st.markdown("</div>", unsafe_allow_html=True)

    if loved_ones:
        featured_index = datetime.now().timetuple().tm_yday % len(loved_ones)
        featured = loved_ones[featured_index]
        featured_name = featured.get("name", "Someone you love")
        featured_relationship = featured.get("relationship", "family member")

        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.subheader("Featured family memory")
        if featured.get("audio_data"):
            st.markdown("<div class='featured-audio'>", unsafe_allow_html=True)
            st.caption(f"Play {featured_name}'s voice")
            st.audio(
                base64.b64decode(featured["audio_data"]),
                format=featured.get("audio_mime_type") or "audio/wav",
            )
            st.markdown("</div>", unsafe_allow_html=True)
        if featured.get("image_data"):
            st.image(
                base64.b64decode(featured["image_data"]),
                caption=f"This is your {featured_relationship}, {featured_name}.",
                use_container_width=True,
            )
        st.success(f"This is your {featured_relationship}, {featured_name}.")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"<div class='memory-name'>{featured_name}</div>"
            f"<div class='memory-role'>{featured_relationship}</div>",
            unsafe_allow_html=True,
        )
        if len(loved_ones) > 1:
            st.markdown(
                f"<div class='count-copy'>{len(loved_ones)} family entries are saved. This page shows one at a time.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    st.session_state["family_tools_show_gallery_preview"] = False
    render_family_tools(user)
    st.session_state["family_tools_show_gallery_preview"] = True


def main():
    st.set_page_config(page_title="Family Recognition", page_icon=":heart:", layout="wide")
    init_session()
    if not st.session_state.logged_in or not st.session_state.username:
        st.switch_page("login.py")

    user = get_user(st.session_state.username)
    if not user:
        st.switch_page("login.py")

    apply_user_settings_to_session(st.session_state, user)
    apply_styles()
    render_page(user)


if __name__ == "__main__":
    main()
