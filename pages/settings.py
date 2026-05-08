import streamlit as st
import streamlit.components.v2 as components

from auth_store import get_user, save_settings
from ui_preferences import (
    THEME_OPTIONS,
    apply_user_settings_to_session,
    build_theme_css,
    default_settings,
    normalize_settings,
)


VOICE_PICKER_HTML = """
<div class="voice-picker">
  <div class="voice-picker-header">
    <div class="voice-picker-title">Ben voice</div>
    <div class="voice-picker-copy">Pick a voice and preview it before saving.</div>
  </div>
  <div class="voice-picker-list"></div>
</div>
"""


VOICE_PICKER_CSS = """
:host {
  display: block;
}

.voice-picker {
  display: grid;
  gap: 0.9rem;
}

.voice-picker-title {
  font-family: 'Nunito', sans-serif;
  font-size: 1.08rem;
  font-weight: 800;
  color: #123848;
}

.voice-picker-copy {
  margin-top: 0.2rem;
  color: #5a7480;
  font-size: 0.94rem;
}

.voice-picker-list {
  display: grid;
  gap: 0.75rem;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 0.15rem;
}

.voice-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.9rem;
  align-items: center;
  padding: 0.95rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(80, 182, 198, 0.18);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 24px rgba(14, 74, 84, 0.05);
}

.voice-card.selected {
  border-color: #0da8bc;
  box-shadow: 0 0 0 2px rgba(13, 168, 188, 0.14);
  background: linear-gradient(135deg, rgba(13, 168, 188, 0.10), rgba(255, 255, 255, 0.98));
}

.voice-name {
  color: #123848;
  font-size: 1rem;
  font-weight: 800;
}

.voice-meta {
  margin-top: 0.2rem;
  color: #5a7480;
  font-size: 0.9rem;
}

.voice-actions {
  display: flex;
  gap: 0.55rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.voice-actions button {
  min-height: 2.5rem;
  border: none;
  border-radius: 14px;
  padding: 0.65rem 0.95rem;
  font-size: 0.92rem;
  font-weight: 800;
  cursor: pointer;
}

.voice-use {
  background: linear-gradient(135deg, #0da8bc 0%, #087e93 100%);
  color: #fff;
}

.voice-preview {
  background: rgba(230, 247, 249, 0.96);
  color: #0b899d;
}

.voice-empty {
  padding: 1rem;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  color: #5a7480;
  border: 1px dashed rgba(80, 182, 198, 0.22);
}

@media (max-width: 700px) {
  .voice-card {
    grid-template-columns: 1fr;
  }

  .voice-actions {
    justify-content: stretch;
  }

  .voice-actions button {
    flex: 1 1 0;
  }
}
"""


VOICE_PICKER_JS = """
export default function(component) {
  const { parentElement, data, setStateValue } = component;
  const root = parentElement.querySelector('.voice-picker');
  if (!root) {
    return;
  }

  const list = root.querySelector('.voice-picker-list');
  const synth = window.parent.speechSynthesis;
  const selectedVoiceUri = data?.selected_voice_uri || '';
  const selectedVoiceName = data?.selected_voice_name || '';

  const speakPreview = (voice) => {
    if (!synth) {
      return;
    }
    synth.cancel();
    const utterance = new window.parent.SpeechSynthesisUtterance(`Hi, I am ${voice.name}.`);
    utterance.rate = 0.92;
    utterance.pitch = 0.98;
    utterance.volume = 1.0;
    utterance.voice = voice;
    synth.speak(utterance);
  };

  const setSelected = (voice) => {
    setStateValue('selected_voice_uri', voice.voiceURI || '');
    setStateValue('selected_voice_name', voice.name || '');
  };

  const renderVoices = () => {
    if (!list) {
      return;
    }
    const allVoices = synth ? synth.getVoices() : [];
    const voices = allVoices
      .filter((voice) => /en/i.test(voice.lang || '') || /english/i.test(voice.name || ''))
      .sort((a, b) => (a.name || '').localeCompare(b.name || ''));

    if (!voices.length) {
      list.innerHTML = '<div class="voice-empty">No browser voices are available yet. Try Chrome or Edge, then reopen this page.</div>';
      return;
    }

    list.innerHTML = '';
    voices.forEach((voice) => {
      const card = document.createElement('div');
      const isSelected = (selectedVoiceUri && voice.voiceURI === selectedVoiceUri)
        || (!selectedVoiceUri && selectedVoiceName && voice.name === selectedVoiceName);
      card.className = `voice-card${isSelected ? ' selected' : ''}`;

      const info = document.createElement('div');
      info.innerHTML = `
        <div class="voice-name">${voice.name}</div>
        <div class="voice-meta">${voice.lang || 'Unknown language'}${voice.default ? ' · Browser default' : ''}</div>
      `;

      const actions = document.createElement('div');
      actions.className = 'voice-actions';

      const useButton = document.createElement('button');
      useButton.type = 'button';
      useButton.className = 'voice-use';
      useButton.textContent = isSelected ? 'Selected' : 'Use voice';
      useButton.addEventListener('click', () => setSelected(voice));

      const previewButton = document.createElement('button');
      previewButton.type = 'button';
      previewButton.className = 'voice-preview';
      previewButton.textContent = 'Preview';
      previewButton.addEventListener('click', () => speakPreview(voice));

      actions.appendChild(useButton);
      actions.appendChild(previewButton);
      card.appendChild(info);
      card.appendChild(actions);
      list.appendChild(card);
    });
  };

  renderVoices();
  if (synth && !window.parent.__mindfulVoicePickerBound) {
    window.parent.__mindfulVoicePickerBound = true;
    synth.onvoiceschanged = () => {
      renderVoices();
    };
  }
}
"""


VOICE_PICKER_COMPONENT = components.component(
    "mindful_voice_picker",
    html=VOICE_PICKER_HTML,
    css=VOICE_PICKER_CSS,
    js=VOICE_PICKER_JS,
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
    st.session_state.setdefault("ben_voice_uri", defaults["ben_voice_uri"])
    st.session_state.setdefault("ben_voice_name", defaults["ben_voice_name"])


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1040px",
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

        .hero-copy {
            color: var(--muted-color);
            font-size: 1.08rem;
            max-width: 42rem;
        }

        .theme-preview-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 0.7rem;
        }

        .voice-selected-note {
            margin-top: 0.8rem;
            color: #5a7480;
            font-size: 0.95rem;
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


def component_value(result, name: str):
    if result is None:
        return None
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


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

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    voice_result = VOICE_PICKER_COMPONENT(
        key="mindful_voice_picker_component",
        data={
            "selected_voice_uri": st.session_state.ben_voice_uri,
            "selected_voice_name": st.session_state.ben_voice_name,
        },
        height=420,
        on_selected_voice_uri_change=lambda: None,
        on_selected_voice_name_change=lambda: None,
    )
    selected_voice_uri = component_value(voice_result, "selected_voice_uri")
    selected_voice_name = component_value(voice_result, "selected_voice_name")
    if selected_voice_uri is not None:
        st.session_state.ben_voice_uri = str(selected_voice_uri)
    if selected_voice_name is not None:
        st.session_state.ben_voice_name = str(selected_voice_name)
    if st.session_state.ben_voice_name:
        st.markdown(
            f"<div class='voice-selected-note'>Current choice: <strong>{st.session_state.ben_voice_name}</strong></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='voice-selected-note'>Current choice: browser default voice</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

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
    submitted = st.button("Save Settings", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        updated_settings = normalize_settings(
            {
                "background_theme": selected_theme,
                "familiar_greeting": familiar_greeting,
                "show_familiar_greeting": show_greeting,
                "text_size": text_size,
                "ben_voice_uri": st.session_state.ben_voice_uri,
                "ben_voice_name": st.session_state.ben_voice_name,
            }
        )
        if save_settings(st.session_state.username, updated_settings):
            st.session_state.background_theme = updated_settings["background_theme"]
            st.session_state.familiar_greeting = updated_settings["familiar_greeting"]
            st.session_state.show_familiar_greeting = updated_settings["show_familiar_greeting"]
            st.session_state.text_size = updated_settings["text_size"]
            st.session_state.ben_voice_uri = updated_settings["ben_voice_uri"]
            st.session_state.ben_voice_name = updated_settings["ben_voice_name"]
            st.success("Settings saved.")
            st.rerun()
        else:
            st.error("Unable to save settings right now.")


if __name__ == "__main__":
    main()
