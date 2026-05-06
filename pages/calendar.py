import html
from datetime import date, datetime

import streamlit as st
import streamlit.components.v1 as components

from auth_store import get_user, save_calendar_events
from ui_preferences import apply_user_settings_to_session, build_theme_css, default_settings


COLOR_OPTIONS = {
    "Medicine": "#d98b3a",
    "Family time": "#4a86c5",
    "Meals": "#5b9b6b",
    "Activity": "#d46f5b",
    "Appointment": "#8a6fb8",
    "Quiet time": "#6f9aa6",
}

WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def init_session():
    today = date.today()
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("pending_email", "")
    st.session_state.setdefault("auth_notice", "")
    st.session_state.setdefault("calendar_month", today.month)
    st.session_state.setdefault("calendar_year", today.year)
    st.session_state.setdefault("background_theme", default_settings()["background_theme"])
    st.session_state.setdefault("familiar_greeting", default_settings()["familiar_greeting"])
    st.session_state.setdefault("show_familiar_greeting", default_settings()["show_familiar_greeting"])
    st.session_state.setdefault("text_size", default_settings()["text_size"])


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1380px",
            extra_css="""
        :root {
            --panel: var(--panel-bg);
            --line: var(--line-color);
            --ink: var(--ink-color);
            --muted: var(--muted-color);
            --warm: var(--accent-color);
            --soft: var(--accent-soft);
            --today: #fff3cf;
        }

        .stApp {
            color: var(--ink);
        }

        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2.5rem;
        }

        .hero-card, .panel-card {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 28px;
            box-shadow: 0 20px 50px rgba(63, 74, 62, 0.09);
        }

        .hero-card {
            padding: 1.5rem 1.6rem;
            margin-bottom: 1rem;
        }

        .panel-card {
            padding: 1.2rem 1.2rem;
            margin-bottom: 1.05rem;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.38rem 0.8rem;
            border-radius: 999px;
            background: var(--soft);
            color: #8c4d25;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            font-size: 2.9rem;
            line-height: 1.05;
            font-weight: 800;
            color: var(--ink);
            margin-bottom: 0.35rem;
        }

        .hero-copy, .helper-copy {
            color: var(--muted);
            font-size: 1.1rem;
            max-width: 52rem;
        }

        .summary-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1rem;
        }

        .summary-card {
            background: var(--panel-soft);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1rem 1.1rem;
        }

        .summary-label {
            color: #7a6653;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.22rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .summary-value {
            color: var(--ink);
            font-family: 'Nunito', sans-serif;
            font-size: 1.7rem;
            font-weight: 800;
        }

        .calendar-scroll {
            width: 100%;
            overflow-x: auto;
            padding-bottom: 0.45rem;
        }

        .calendar-shell {
            display: grid;
            grid-template-columns: repeat(7, minmax(185px, 1fr));
            gap: 0.95rem;
            min-width: 1160px;
        }

        .weekday-chip {
            text-align: center;
            font-family: 'Nunito', sans-serif;
            font-size: 1.12rem;
            font-weight: 800;
            color: var(--ink);
            background: rgba(255, 255, 255, 0.68);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 0.85rem 0.2rem;
        }

        .day-card {
            min-height: 210px;
            background: #ffffff;
            border: 1px solid #ddd4c4;
            border-radius: 24px;
            padding: 0.95rem;
            box-shadow: 0 10px 28px rgba(37, 66, 77, 0.07);
        }

        .day-card.today {
            background: linear-gradient(180deg, var(--today) 0%, #fffdf7 100%);
            border-color: #e2c67f;
        }

        .day-card.blank {
            background: rgba(255, 255, 255, 0.45);
            border-style: dashed;
            box-shadow: none;
        }

        .day-number {
            font-family: 'Nunito', sans-serif;
            font-size: 1.7rem;
            font-weight: 800;
            color: var(--ink);
            margin-bottom: 0.75rem;
        }

        .event-pill {
            border-radius: 18px;
            padding: 0.72rem 0.78rem;
            margin-bottom: 0.55rem;
            color: #17313a;
            font-size: 1rem;
            font-weight: 600;
            line-height: 1.34;
            word-break: normal;
            overflow-wrap: break-word;
        }

        .event-time {
            display: block;
            font-size: 0.92rem;
            font-weight: 800;
            opacity: 0.92;
            margin-bottom: 0.2rem;
            white-space: nowrap;
        }

        .event-note {
            display: block;
            font-size: 0.9rem;
            opacity: 0.85;
            margin-top: 0.18rem;
        }

        .empty-day {
            color: #7a8a90;
            font-size: 1rem;
        }

        .legend-row {
            display: flex;
            flex-wrap: nowrap;
            gap: 0.6rem;
            margin-top: 0.2rem;
            width: 100%;
            overflow-x: auto;
            padding-bottom: 0.35rem;
            scrollbar-width: thin;
        }

        .legend-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            flex: 0 0 auto;
            background: rgba(255,255,255,0.82);
            border: 1px solid var(--line);
            border-radius: 999px;
            padding: 0.5rem 0.82rem;
            font-size: 1rem;
            color: var(--ink);
            font-weight: 600;
            white-space: nowrap;
        }

        .legend-dot {
            width: 0.9rem;
            height: 0.9rem;
            border-radius: 999px;
            display: inline-block;
        }

        .stButton > button, .stFormSubmitButton > button {
            border-radius: 18px;
            min-height: 3.45rem;
            font-weight: 700;
            border: none;
            font-size: 1.04rem;
            box-shadow: 0 10px 22px rgba(37, 66, 77, 0.08);
        }

        .month-title {
            font-family: 'Nunito', sans-serif;
            font-size: 2.15rem;
            font-weight: 800;
            color: var(--ink);
            text-align: center;
            padding-top: 0.32rem;
        }

        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div,
        .stDateInput > div > div,
        .stTextArea textarea {
            border-radius: 18px !important;
            min-height: 3.35rem !important;
            font-size: 1.02rem !important;
            border-color: #d8cfbf !important;
            background: #fffdf9 !important;
        }

        .stTextArea textarea {
            min-height: 140px !important;
            padding-top: 0.95rem !important;
        }

        label, .stMarkdown p {
            font-size: 1rem;
        }

        .section-title {
            font-family: 'Nunito', sans-serif;
            font-size: 1.65rem;
            font-weight: 800;
            color: var(--ink);
            margin-bottom: 0.25rem;
        }

        .section-copy {
            color: var(--muted);
            font-size: 1rem;
            margin-bottom: 0.8rem;
        }

        @media (max-width: 1100px) {
            .summary-strip {
                grid-template-columns: 1fr;
            }

            .day-card {
                min-height: 170px;
            }
        }
        """,
        ),
        unsafe_allow_html=True,
    )


def apply_button_feedback():
    components.html(
        """
        <script>
        const selectors = ['[data-testid="stButton"] button', '[data-testid="stFormSubmitButton"] button'];
        const bindButtons = () => {
          const buttons = window.parent.document.querySelectorAll(selectors.join(','));
          buttons.forEach((button) => {
            if (button.dataset.calendarBound === 'true') {
              return;
            }
            button.dataset.calendarBound = 'true';
            button.addEventListener('click', () => {
              button.animate(
                [
                  { transform: 'scale(0.98)', boxShadow: '0 0 0 0 rgba(126, 163, 127, 0.0)' },
                  { transform: 'scale(1.02)', boxShadow: '0 0 0 12px rgba(126, 163, 127, 0.20)' },
                  { transform: 'scale(1.0)', boxShadow: '0 10px 22px rgba(37, 66, 77, 0.08)' }
                ],
                { duration: 700, easing: 'ease-out' }
              );
            });
          });
        };
        bindButtons();
        new MutationObserver(bindButtons).observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )


def month_name(year: int, month: int) -> str:
    return date(year, month, 1).strftime("%B %Y")


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    moved_month = month + delta
    moved_year = year
    while moved_month < 1:
        moved_month += 12
        moved_year -= 1
    while moved_month > 12:
        moved_month -= 12
        moved_year += 1
    return moved_year, moved_month


def days_in_month(year: int, month: int) -> int:
    next_year, next_month = shift_month(year, month, 1)
    return (date(next_year, next_month, 1) - date(year, month, 1)).days


def build_month_cells(year: int, month: int) -> list:
    first_day = date(year, month, 1)
    start_offset = (first_day.weekday() + 1) % 7
    total_days = days_in_month(year, month)
    cells = [None] * start_offset + [date(year, month, day) for day in range(1, total_days + 1)]
    while len(cells) % 7 != 0:
        cells.append(None)
    while len(cells) < 35:
        cells.append(None)
    return cells


def parse_event_sort_value(event: dict) -> datetime:
    timestamp = f"{event.get('date', '')} {event.get('start_time', '12:00 AM')}"
    try:
        return datetime.strptime(timestamp, "%Y-%m-%d %I:%M %p")
    except ValueError:
        return datetime.max


def format_time_range(event: dict) -> str:
    start = event.get("start_time", "")
    end = event.get("end_time", "")
    if start and end:
        return f"{start} to {end}"
    return start or "All day"


def safe_text(value: str) -> str:
    return html.escape(value or "")


def parse_time_label(value: str, fallback: str) -> str:
    raw_value = value or fallback
    try:
        parsed = datetime.strptime(raw_value, "%I:%M %p")
        return parsed.strftime("%I:%M %p")
    except ValueError:
        return datetime.strptime(fallback, "%I:%M %p").strftime("%I:%M %p")


def render_time_picker(prefix: str, label: str, default_value: str) -> str:
    normalized_default = parse_time_label(default_value, "09:00 AM")
    time_options = [
        datetime.strptime(f"{hour:02d}:{minute:02d}", "%H:%M").strftime("%I:%M %p")
        for hour in range(24)
        for minute in (0, 30)
    ]
    default_index = time_options.index(normalized_default) if normalized_default in time_options else time_options.index("09:00 AM")
    return st.selectbox(label, time_options, index=default_index, key=f"{prefix}_time")


def render_login_prompt():
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Calendar page</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Open the family calendar</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-copy'>This page is designed to show one calm, easy-to-read schedule by itself. Log in first so the calendar can load that person's reminders.</div>",
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2)
    if col1.button("Go to Login", use_container_width=True, type="primary"):
        st.switch_page("login.py")
    if col2.button("Go to Sign Up", use_container_width=True):
        st.switch_page("pages/sign_up.py")
    st.markdown("</div>", unsafe_allow_html=True)


def render_header(user: dict):
    total_events = len(user.get("progress", {}).get("calendar_events", []))
    today_events = sum(1 for event in user.get("progress", {}).get("calendar_events", []) if event.get("date") == date.today().isoformat())
    st.markdown("<div class='hero-card'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Large-print family planner</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Care Calendar</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='hero-copy'>A clear monthly schedule for <strong>{safe_text(user.get('full_name', 'this account'))}</strong>.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<div class='legend-row'>", unsafe_allow_html=True)
    for label, color in COLOR_OPTIONS.items():
        st.markdown(
            f"<div class='legend-chip'><span class='legend-dot' style='background:{color};'></span>{label}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class='summary-strip'>
            <div class='summary-card'>
                <div class='summary-label'>This Month</div>
                <div class='summary-value'>{month_name(st.session_state.calendar_year, st.session_state.calendar_month)}</div>
            </div>
            <div class='summary-card'>
                <div class='summary-label'>Today</div>
                <div class='summary-value'>{today_events} reminder{'s' if today_events != 1 else ''}</div>
            </div>
            <div class='summary-card'>
                <div class='summary-label'>Saved</div>
                <div class='summary-value'>{total_events} total</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_month_controls():
    col1, col2, col3 = st.columns([1, 2, 1])
    if col1.button("Previous Month", use_container_width=True):
        year, month = shift_month(st.session_state.calendar_year, st.session_state.calendar_month, -1)
        st.session_state.calendar_year = year
        st.session_state.calendar_month = month
        st.rerun()
    col2.markdown(
        f"<div class='month-title'>{month_name(st.session_state.calendar_year, st.session_state.calendar_month)}</div>",
        unsafe_allow_html=True,
    )
    if col3.button("Next Month", use_container_width=True):
        year, month = shift_month(st.session_state.calendar_year, st.session_state.calendar_month, 1)
        st.session_state.calendar_year = year
        st.session_state.calendar_month = month
        st.rerun()


def render_event_form(events: list):
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Add Reminder</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-copy'>Keep each reminder short and easy to spot.</div>", unsafe_allow_html=True)
    with st.form("calendar_event_form", clear_on_submit=True):
        title = st.text_input("Reminder title", placeholder="Morning medicine")
        event_date = st.date_input("Date", value=date.today())
        col1, col2 = st.columns(2)
        with col1:
            start_time_label = render_time_picker("calendar_start", "Start time", "09:00 AM")
        with col2:
            end_time_label = render_time_picker("calendar_end", "End time", "09:30 AM")
        color_name = st.selectbox("Color group", list(COLOR_OPTIONS.keys()))
        note = st.text_area("Helpful note", placeholder="Take with breakfast. Sarah will call after lunch.", height=110)
        submitted = st.form_submit_button("Save to Calendar", use_container_width=True)

    if submitted:
        if not title.strip():
            st.error("Please enter a reminder title.")
        else:
            updated_events = events + [
                {
                    "title": title,
                    "date": event_date.isoformat(),
                    "start_time": start_time_label,
                    "end_time": end_time_label,
                    "color": COLOR_OPTIONS[color_name],
                    "note": note,
                }
            ]
            updated_events.sort(key=parse_event_sort_value)
            if save_calendar_events(st.session_state.username, updated_events):
                st.success("Calendar reminder saved.")
                st.rerun()
            st.error("Unable to save this reminder.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_event_list(events: list):
    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Upcoming</div>", unsafe_allow_html=True)
    if not events:
        st.info("No reminders yet. Add one to start the calendar.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    upcoming = sorted(events, key=parse_event_sort_value)[:10]
    for event in upcoming:
        friendly_date = datetime.strptime(event["date"], "%Y-%m-%d").strftime("%A, %B %d")
        col1, col2 = st.columns([5, 1])
        col1.markdown(
            f"""
            <div style="border-left: 10px solid {event.get('color', '#4d8f7a')}; background:#fbfaf6; border-radius:18px; padding:0.9rem 1rem; margin-bottom:0.65rem;">
                <div style="font-weight:800; color:#23414b; font-size:1.08rem;">{safe_text(event.get('title', ''))}</div>
                <div style="color:#5d737b; font-weight:600; margin-top:0.1rem;">{friendly_date} | {format_time_range(event)}</div>
                <div style="color:#5d737b; margin-top:0.18rem;">{safe_text(event.get('note', 'No note added.') or 'No note added.')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if col2.button("Delete", key=f"delete_{event.get('id', event['date'] + event['title'])}", use_container_width=True):
            remaining = [item for item in events if item.get("id") != event.get("id")]
            if save_calendar_events(st.session_state.username, remaining):
                st.rerun()
            st.error("Unable to delete this reminder.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_month_grid(events: list):
    year = st.session_state.calendar_year
    month = st.session_state.calendar_month
    events_by_date = {}
    for event in events:
        events_by_date.setdefault(event.get("date", ""), []).append(event)
    for grouped_events in events_by_date.values():
        grouped_events.sort(key=parse_event_sort_value)

    weekday_row = "".join(f"<div class='weekday-chip'>{weekday}</div>" for weekday in WEEKDAYS)
    day_cards = []
    today = date.today()
    for day_value in build_month_cells(year, month):
        if day_value is None:
            day_cards.append("<div class='day-card blank'></div>")
            continue

        event_markup = ""
        daily_events = events_by_date.get(day_value.isoformat(), [])
        for event in daily_events[:3]:
            note = event.get("note", "").strip()
            note_markup = f"<span class='event-note'>{safe_text(note)}</span>" if note else ""
            event_markup += (
                f"<div class='event-pill' style='background:{event.get('color', '#4d8f7a')}33; border-left:8px solid {event.get('color', '#4d8f7a')};'>"
                f"<span class='event-time'>{format_time_range(event)}</span>"
                f"{safe_text(event.get('title', ''))}"
                f"{note_markup}</div>"
            )
        if len(daily_events) > 3:
            event_markup += f"<div class='empty-day'>+{len(daily_events) - 3} more reminders</div>"
        if not daily_events:
            event_markup = "<div class='empty-day'>Open time</div>"

        today_class = " today" if day_value == today else ""
        day_cards.append(
            f"<div class='day-card{today_class}'><div class='day-number'>{day_value.day}</div>{event_markup}</div>"
        )

    st.markdown("<div class='panel-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Month View</div>", unsafe_allow_html=True)
    render_month_controls()
    st.markdown(
        f"<div class='calendar-scroll'><div class='calendar-shell'>{weekday_row}{''.join(day_cards)}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Care Calendar", page_icon=":calendar:", layout="wide")
    init_session()

    if not st.session_state.logged_in or not st.session_state.username:
        apply_styles()
        apply_button_feedback()
        render_login_prompt()
        return

    user = get_user(st.session_state.username)
    if not user:
        apply_styles()
        apply_button_feedback()
        render_login_prompt()
        return

    apply_user_settings_to_session(st.session_state, user)
    apply_styles()
    apply_button_feedback()

    events = user.get("progress", {}).get("calendar_events", [])

    render_header(user)

    left, right = st.columns([1.08, 2.12], gap="large")
    with left:
        render_event_form(events)
        render_event_list(events)
    with right:
        render_month_grid(events)


if __name__ == "__main__":
    main()
