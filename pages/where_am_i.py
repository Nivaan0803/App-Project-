import json

import streamlit as st
import streamlit.components.v1 as components

from auth_store import get_user
from ui_preferences import apply_user_settings_to_session, build_theme_css, default_settings


def init_session():
    st.session_state.setdefault("logged_in", False)
    st.session_state.setdefault("username", "")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("email", "")
    st.session_state.setdefault("background_theme", default_settings()["background_theme"])
    st.session_state.setdefault("familiar_greeting", default_settings()["familiar_greeting"])
    st.session_state.setdefault("show_familiar_greeting", default_settings()["show_familiar_greeting"])
    st.session_state.setdefault("text_size", default_settings()["text_size"])


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1040px",
            extra_css="""

        .shell {
            background: var(--panel-bg);
            border: 1px solid var(--line-color);
            border-radius: 30px;
            padding: 1.6rem;
            box-shadow: 0 22px 54px rgba(58, 74, 66, 0.09);
        }

        .nav-card {
            background: var(--panel-bg);
            border: 1px solid var(--line-color);
            border-radius: 22px;
            padding: 0.7rem;
            margin-bottom: 1rem;
        }

        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.72rem;
            border-radius: 999px;
            background: #dcefe5;
            color: #2d6851;
            font-size: 0.92rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
        }

        .hero-title {
            font-family: 'Nunito', sans-serif;
            color: #24453b;
            font-size: 2.7rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }

        .hero-copy {
            color: #557067;
            font-size: 1.1rem;
            margin-bottom: 1rem;
            max-width: 40rem;
        }

        .section-card {
            background: rgba(255,255,255,0.97);
            border: 1px solid #e2ddd2;
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
        """,
        ),
        unsafe_allow_html=True,
    )


def top_nav():
    show_help = st.session_state.get("logged_in", False)
    st.markdown("<div style='height: 0.55rem;'></div>", unsafe_allow_html=True)
    columns = st.columns(3 if show_help else 2)
    col1, col2 = columns[0], columns[1]
    if col1.button("Login", use_container_width=True, type="secondary" if show_help else "primary"):
        st.switch_page("login.py")
    if show_help:
        if col2.button("Help", use_container_width=True):
            st.switch_page("pages/help.py")
    else:
        if col2.button("Sign Up", use_container_width=True):
            st.switch_page("pages/sign_up.py")
    if show_help:
        col3 = columns[2]
        col3.button("Where Am I?", use_container_width=True, type="primary")
    st.markdown("<div style='height: 0.8rem;'></div>", unsafe_allow_html=True)


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


def render_location_widget(support_name, support_phone, support_email):
    config = {
        "supportName": support_name or "your support person",
        "supportPhone": clean_phone(support_phone),
        "supportEmail": support_email,
    }
    config_json = json.dumps(config)
    components.html(
        f"""
        <div id="where-card" style="font-family: 'Lexend', sans-serif;">
          <style>
            .where-shell {{
              background: linear-gradient(135deg, #eef8f2, #ffffff);
              border: 2px solid #b7d9c4;
              border-radius: 28px;
              padding: 20px;
              box-shadow: 0 18px 36px rgba(74, 117, 94, 0.10);
            }}
            .where-title {{
              color: #204b3e;
              font-size: 34px;
              font-weight: 800;
              margin-bottom: 4px;
            }}
            .where-copy {{
              color: #557067;
              font-size: 18px;
              margin-bottom: 18px;
            }}
            .where-status {{
              background: #ffffff;
              border: 1px solid #d5e7dc;
              border-radius: 20px;
              padding: 16px;
              margin-bottom: 14px;
            }}
            .status-line {{
              color: #355f51;
              font-size: 21px;
              font-weight: 700;
              margin-bottom: 8px;
            }}
            .quiet {{
              color: #5c756c;
              font-size: 17px;
            }}
            .where-actions {{
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 10px;
              margin-bottom: 12px;
            }}
            .where-actions button, .where-links a {{
              width: 100%;
              border: none;
              border-radius: 20px;
              padding: 18px 18px;
              font-weight: 800;
              font-size: 18px;
              cursor: pointer;
              text-decoration: none;
              display: inline-flex;
              justify-content: center;
              align-items: center;
              box-sizing: border-box;
            }}
            .locate {{
              background: #2e7b5a;
              color: #ffffff;
            }}
            .track {{
              background: #dcefe5;
              color: #275d48;
            }}
            .where-links {{
              display: grid;
              grid-template-columns: 1fr;
              gap: 10px;
            }}
            .hidden {{
              display: none;
            }}
            .call {{
              background: #d8452d;
              color: #ffffff;
            }}
            .message {{
              background: #ffffff;
              color: #ad3a28;
              border: 2px solid #efb3a8;
            }}
            .email {{
              background: #fff8f2;
              color: #8f5d22;
              border: 2px dashed #efc684;
            }}
            .map {{
              background: #eef6ff;
              color: #295c95;
              border: 2px solid #c4daf3;
            }}
            .note {{
              background: #f8f5ef;
              border-radius: 18px;
              padding: 16px 18px;
              color: #5d665e;
              font-size: 16px;
              margin-top: 12px;
            }}
          </style>
          <div class="where-shell">
            <div class="where-title">Where Am I?</div>
            <div class="where-copy">Press the green button to find your location. You are safe. This page can help you contact family with your current location.</div>
            <div class="where-status">
              <div id="statusLine" class="status-line">Location not requested yet.</div>
              <div id="statusDetail" class="quiet">When you allow location access, this page will show your address and a map link.</div>
            </div>
            <div class="where-actions">
              <button class="locate" id="locateButton" type="button">Find My Location</button>
              <button class="track" id="trackButton" type="button">Start Tracking</button>
            </div>
            <div class="where-links">
              <a id="callLink" class="call hidden" href="#">Call Support</a>
              <a id="messageLink" class="message hidden" href="#">Message Family My Location</a>
              <a id="emailLink" class="email hidden" href="#">Email Family My Location</a>
              <a id="mapLink" class="map hidden" href="#" target="_blank">Open My Location in Maps</a>
            </div>
            <div class="note">This uses your browser's location permission. Tracking only works while this page stays open.</div>
          </div>
        </div>
        <script>
          const config = {config_json};
          const statusLine = document.getElementById("statusLine");
          const statusDetail = document.getElementById("statusDetail");
          const locateButton = document.getElementById("locateButton");
          const trackButton = document.getElementById("trackButton");
          const callLink = document.getElementById("callLink");
          const messageLink = document.getElementById("messageLink");
          const emailLink = document.getElementById("emailLink");
          const mapLink = document.getElementById("mapLink");
          let watchId = null;

          if (config.supportPhone) {{
            callLink.href = `tel:${{config.supportPhone}}`;
            callLink.textContent = `Call ${{config.supportName}}`;
            callLink.classList.remove("hidden");
          }}

          async function lookupAddress(latitude, longitude) {{
            const reverseUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${{latitude}}&lon=${{longitude}}`;
            try {{
              const response = await fetch(reverseUrl, {{
                headers: {{
                  "Accept-Language": "en"
                }}
              }});
              if (!response.ok) {{
                throw new Error("Reverse geocoding failed");
              }}
              const data = await response.json();
              return data.display_name || "";
            }} catch (error) {{
              return "";
            }}
          }}

          function updateLinks(latitude, longitude, address) {{
            const coords = `${{latitude.toFixed(5)}}, ${{longitude.toFixed(5)}}`;
            const mapsUrl = `https://www.google.com/maps?q=${{latitude}},${{longitude}}`;
            const locationLabel = address || coords;
            const message = encodeURIComponent(`I may need help. My location is ${{locationLabel}}. Map: ${{mapsUrl}}`);
            const emailBody = encodeURIComponent(`I may need help. My current location is ${{locationLabel}}.\\n\\nMap: ${{mapsUrl}}`);

            mapLink.href = mapsUrl;
            mapLink.classList.remove("hidden");

            if (config.supportPhone) {{
              messageLink.href = `sms:${{config.supportPhone}}?body=${{message}}`;
              messageLink.textContent = `Message ${{config.supportName}} My Location`;
              messageLink.classList.remove("hidden");
            }}

            if (config.supportEmail) {{
              emailLink.href = `mailto:${{config.supportEmail}}?subject=${{encodeURIComponent("My location")}}&body=${{emailBody}}`;
              emailLink.textContent = `Email ${{config.supportName}} My Location`;
              emailLink.classList.remove("hidden");
            }}
          }}

          async function showLocation(position) {{
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            const accuracy = Math.round(position.coords.accuracy);
            statusLine.textContent = "Finding your address...";
            statusDetail.textContent = `Your location was found. Accuracy is about ${{accuracy}} meters.`;
            const address = await lookupAddress(latitude, longitude);
            if (address) {{
              statusLine.textContent = `You are here: ${{address}}`;
              statusDetail.textContent = `You are safe. Location accuracy is about ${{accuracy}} meters. Stay where you are and contact family if needed.`;
            }} else {{
              statusLine.textContent = `Nearby location: ${{latitude.toFixed(5)}}, ${{longitude.toFixed(5)}}`;
              statusDetail.textContent = `We found your location, but could not turn it into a street address. Accuracy is about ${{accuracy}} meters.`;
            }}
            updateLinks(latitude, longitude, address);
          }}

          function showError(error) {{
            statusLine.textContent = "We could not get your location.";
            const errors = {{
              1: "Location permission was denied.",
              2: "Location information is unavailable right now.",
              3: "The location request timed out."
            }};
            statusDetail.textContent = errors[error.code] || "Please try again or contact family another way.";
          }}

          locateButton.addEventListener("click", () => {{
            statusLine.textContent = "Finding your location...";
            statusDetail.textContent = "Please allow location access if your browser asks.";
            navigator.geolocation.getCurrentPosition(showLocation, showError, {{
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 0
            }});
          }});

          trackButton.addEventListener("click", () => {{
            if (watchId !== null) {{
              navigator.geolocation.clearWatch(watchId);
              watchId = null;
              trackButton.textContent = "Start Tracking";
              statusDetail.textContent = "Tracking stopped. Your last location is still shown above.";
              return;
            }}
            statusLine.textContent = "Tracking your location...";
            statusDetail.textContent = "Please allow location access if your browser asks.";
            watchId = navigator.geolocation.watchPosition(showLocation, showError, {{
              enableHighAccuracy: true,
              timeout: 15000,
              maximumAge: 5000
            }});
            trackButton.textContent = "Stop Tracking";
          }});
        </script>
        """,
        height=700,
    )


def main():
    st.set_page_config(page_title="Where Am I?", page_icon=":round_pushpin:", layout="centered")
    init_session()
    if not st.session_state.logged_in:
        st.switch_page("login.py")
    user = get_user(st.session_state.username) if st.session_state.username else None
    if user:
        apply_user_settings_to_session(st.session_state, user)
    apply_styles()
    top_nav()

    support_name, support_phone, support_email = get_support_defaults()

    st.markdown("<div class='shell'>", unsafe_allow_html=True)
    st.markdown("<div class='eyebrow'>Location and reassurance</div>", unsafe_allow_html=True)
    st.markdown("<div class='hero-title'>Where Am I?</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='hero-copy'>Find your location and share it with a trusted support person.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("Support contact")
    if support_name or support_phone or support_email:
        st.write(f"Support person: **{support_name or 'Saved family contact'}**")
        st.caption(f"{support_phone or 'No phone saved'} | {support_email or 'No email saved'}")
    else:
        st.warning("No support contact is saved yet. Add one in Family Tools so this page can message or email location.")
    st.markdown("</div>", unsafe_allow_html=True)

    render_location_widget(support_name, support_phone, support_email)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("How this works")
    st.write("1. Press `Find My Location` and allow browser location access.")
    st.write("2. The page will show your location and a map link.")
    st.write("3. Use the message or email buttons to send it to family.")
    st.caption("Tracking only works while this page stays open in the browser.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
