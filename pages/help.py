from urllib.parse import quote

import streamlit as st

from auth_store import get_user


def init_session():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")


def apply_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Nunito:wght@700;800&display=swap');

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 211, 202, 0.88), transparent 24%),
                linear-gradient(180deg, #f7e9e5 0%, #fffaf8 100%);
            font-family: 'Lexend', sans-serif;
        }

        .block-container {
            max-width: 980px;
            padding-top: 1.55rem;
            padding-bottom: 3rem;
        }

        .shell {
            background: rgba(255,255,255,0.96);
            border: 1px solid #e6ccc4;
            border-radius: 30px;
            padding: 1.6rem;
            box-shadow: 0 22px 54px rgba(125, 69, 57, 0.1);
        }

        .nav-card {
            background: rgba(255,255,255,0.95);
            border: 1px solid #e6ccc4;
            border-radius: 22px;
            padding: 0.7rem;
            margin-bottom: 1rem;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: #ffd9d3;
            color: #972d20;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            color: #872618;
            font-size: 2.7rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .hero-copy {
            color: #7b4d43;
            font-size: 1.1rem;
            margin-bottom: 1rem;
            max-width: 40rem;
        }

        .help-card {
            background: linear-gradient(135deg, #ffefe9, #ffd8d0);
            border: 2px solid #d6422a;
            border-radius: 30px;
            padding: 1.3rem;
            margin-bottom: 1rem;
            box-shadow: 0 20px 40px rgba(214, 66, 42, 0.16);
        }

        .help-title {
            color: #8d2618;
            font-size: 2rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .help-copy {
            color: #7c3c31;
            margin-bottom: 1rem;
        }

        .action-link {
            display: block;
            text-align: center;
            text-decoration: none;
            font-weight: 800;
            border-radius: 22px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 0.75rem;
            font-size: 1.08rem;
            transition: transform 0.16s ease, box-shadow 0.18s ease;
        }

        .call-link {
            background: #cf2f1c;
            color: #ffffff;
            box-shadow: 0 16px 30px rgba(207, 47, 28, 0.28);
        }

        .text-link {
            background: #ffffff;
            color: #a02e1f;
            border: 2px solid #e29385;
        }

        .mail-link {
            background: #fff4f1;
            color: #8e2c1d;
            border: 2px dashed #dd8d80;
        }

        .action-link:hover {
            transform: translateY(-1px);
        }

        .section-card {
            background: rgba(255,255,255,0.97);
            border: 1px solid #ecd6cf;
            border-radius: 26px;
            padding: 1.15rem 1.2rem;
            margin-bottom: 1rem;
        }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 18px;
            min-height: 3.35rem;
            font-size: 1.03rem;
            font-weight: 700;
        }

        div[data-baseweb="input"] > div,
        .stTextArea textarea {
            min-height: 3.2rem !important;
            border-radius: 18px !important;
            font-size: 1.02rem !important;
            background: #fffdf9 !important;
        }

        .stTextArea textarea {
            min-height: 130px !important;
            padding-top: 0.95rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def top_nav():
    st.markdown("<div class='nav-card'>", unsafe_allow_html=True)
    show_help = st.session_state.get("logged_in", False)
    columns = st.columns(4 if show_help else 2)
    col1, col2 = columns[0], columns[1]
    if col1.button("Login", use_container_width=True):
        st.switch_page("login.py")
    if col2.button("Sign Up", use_container_width=True):
        st.switch_page("pages/sign_up.py")
    if show_help:
        col3 = columns[2]
        col4 = columns[3]
        col3.button("Help", use_container_width=True, type="primary")
        if col4.button("Where Am I?", use_container_width=True):
            st.switch_page("pages/where_am_i.py")
    st.markdown("</div>", unsafe_allow_html=True)


def clean_phone(phone):
    allowed = []
    for char in phone:
        if char.isdigit() or char == "+":
            allowed.append(char)
    return "".join(allowed)


def get_support_defaults():
    if st.session_state.logged_in and st.session_state.username:
        user = get_user(st.session_state.username)
        if user:
            profile = user.get("profile", {})
            return (
                profile.get("support_name", ""),
                profile.get("support_phone", ""),
                profile.get("support_email", ""),
            )
    return "", "", ""


def render_actions(name, phone, email, note):
    st.markdown("<div class='help-card'>", unsafe_allow_html=True)
    st.markdown("<div class='help-title'>Get Help Now</div>", unsafe_allow_html=True)
    support_label = name or "your support person"
    st.markdown(
        f"<div class='help-copy'>Use these buttons to quickly contact {support_label}. Stay where you are and wait for help.</div>",
        unsafe_allow_html=True,
    )

    if phone:
        safe_phone = clean_phone(phone)
        sms_body = quote(note or "I need help. Please call or come check on me.")
        st.markdown(
            f"""
            <a class="action-link call-link" href="tel:{safe_phone}">CALL {support_label.upper()}</a>
            <a class="action-link text-link" href="sms:{safe_phone}?body={sms_body}">MESSAGE {support_label.upper()}</a>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Add a support phone number below or save one in Family Tools to enable call and text buttons.")

    if email:
        subject = quote("Need help")
        body = quote(note or "I need help. Please call or come check on me.")
        st.markdown(
            f'<a class="action-link mail-link" href="mailto:{email}?subject={subject}&body={body}">EMAIL {support_label.upper()}</a>',
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Help", page_icon=":rotating_light:", layout="centered")
    init_session()
    if not st.session_state.logged_in:
        st.switch_page("login.py")
    apply_styles()
    top_nav()

    default_name, default_phone, default_email = get_support_defaults()

    st.markdown("<div class='shell'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Emergency support page</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Help</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-copy'>Quick ways to call, message, or email a trusted support person.</div>",
        unsafe_allow_html=True,
    )

    with st.form("help_contact_form"):
        support_name = st.text_input("Support person", value=default_name, placeholder="Daughter, son, or caregiver")
        support_phone = st.text_input("Support phone", value=default_phone, placeholder="555-123-4567")
        support_email = st.text_input("Support email", value=default_email, placeholder="family@example.com")
        help_note = st.text_area(
            "Message to send",
            value="I need help. Please call or come check on me.",
            height=100,
        )
        submitted = st.form_submit_button("Update Help Contacts", use_container_width=True)

    if submitted:
        st.success("Help contacts are ready on this page.")

    render_actions(support_name, support_phone, support_email, help_note)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Take a Picture")
    st.caption("You can take a picture and keep it on screen while you call or message your support person.")
    photo = st.camera_input("Open camera")
    if photo is not None:
        st.success("Picture captured.")
        st.image(photo, caption="Recent picture", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("What to do next")
    st.write("1. Press the red call button if you need someone right away.")
    st.write("2. Use the message button for a quick note.")
    st.write("3. Keep the picture open if it helps explain the problem.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
