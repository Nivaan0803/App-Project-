import streamlit as st


def init_session():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("pending_email", "")
    st.session_state.setdefault("auth_notice", "")


def apply_sidebar_styles():
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #f8f3e8 0%, #fffdf8 100%);
            border-right: 2px solid #d9cfbc;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            padding-top: 1rem;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] > div:first-child {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid #dccfb9;
            border-radius: 22px;
            padding: 0.6rem;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] p {
            color: #8a5a2b;
            font-weight: 800;
            letter-spacing: 0.08em;
            font-size: 0.78rem;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            background: #ffffff;
            border: 1px solid #ddd4c4;
            border-radius: 20px;
            margin-bottom: 0.6rem;
            padding: 0.8rem 0.85rem;
            color: #27424a;
            min-height: 3.4rem;
            box-shadow: 0 10px 24px rgba(49, 63, 60, 0.06);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span {
            color: #27424a !important;
            font-weight: 900 !important;
            font-size: 1.08rem !important;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: #fff7e8;
            border-color: #d8b679;
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(135deg, #cf7c4d, #e8a05b);
            color: #ffffff;
            border-color: #cf7c4d;
            box-shadow: 0 12px 26px rgba(207, 124, 77, 0.22);
        }

        section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {
            color: #ffffff !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    init_session()
    st.set_page_config(
        page_title="Memory Lane Companion",
        page_icon=":sunflower:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_sidebar_styles()

    account_pages = []

    support_pages = []
    if st.session_state.logged_in:
        account_pages.append(st.Page("login.py", title="DASHBOARD", icon=":material/dashboard:"))
        account_pages.append(st.Page("pages/calendar.py", title="CALENDAR", icon=":material/calendar_month:"))
        account_pages.append(st.Page("pages/settings.py", title="SETTINGS", icon=":material/settings:"))
        support_pages.append(st.Page("pages/help.py", title="HELP", icon=":material/emergency_home:"))
        support_pages.append(st.Page("pages/where_am_i.py", title="WHERE AM I?", icon=":material/pin_drop:"))
    else:
        account_pages.append(st.Page("login.py", title="LOGIN", icon=":material/login:"))
        account_pages.append(st.Page("pages/sign_up.py", title="SIGN UP", icon=":material/person_add:"))

    navigation = st.navigation(
        {
            "ACCOUNT": account_pages,
            "SUPPORT": support_pages,
        }
    )
    navigation.run()


if __name__ == "__main__":
    main()
