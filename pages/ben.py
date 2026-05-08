import html
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v2 as components

try:
    from openai import OpenAI
except ModuleNotFoundError:
    OpenAI = None

from auth_store import get_user
from ui_preferences import apply_user_settings_to_session, build_theme_css, default_settings


BOB_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MEDICAL_KEYWORDS = (
    "doctor",
    "medicine",
    "medication",
    "pill",
    "dose",
    "dosage",
    "pain",
    "sick",
    "injury",
    "blood pressure",
    "diabetes",
    "dementia",
    "alzheimer",
    "hospital",
    "prescription",
    "medical",
    "symptom",
)

VOICE_RECORDER_HTML = """
<div class="voice-recorder">
  <button class="orb" type="button" aria-label="Start voice conversation">
    <span class="orb-core">
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M12 15a3 3 0 0 0 3-3V7a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"></path>
        <path d="M18 11.5a6 6 0 0 1-12 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
        <path d="M12 17.5v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
        <path d="M9 20.5h6" stroke="currentColor" stroke-width="2" stroke-linecap="round"></path>
      </svg>
    </span>
  </button>
  <div class="status" role="status">Tap once to start talking with Ben.</div>
  <div class="substatus">Ben can keep listening and replying until you stop the conversation.</div>
</div>
"""

VOICE_RECORDER_CSS = """
:host {
  display: block;
}

.voice-recorder {
  min-height: 270px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.95rem;
  border-radius: 30px;
  background:
    radial-gradient(circle at 50% 36%, rgba(79, 226, 244, 0.18), rgba(79, 226, 244, 0.06) 22%, rgba(255,255,255,0) 48%),
    linear-gradient(180deg, rgba(242,251,253,0.94), rgba(234,248,251,0.86));
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,0.58),
    0 16px 36px rgba(13, 97, 112, 0.08);
}

.orb {
  width: 178px;
  height: 178px;
  border: 0;
  border-radius: 999px;
  padding: 0;
  cursor: pointer;
  color: #fff;
  background: transparent;
  position: relative;
  transition: transform 160ms ease, filter 160ms ease;
}

.orb::before,
.orb::after {
  content: "";
  position: absolute;
  inset: 50%;
  transform: translate(-50%, -50%);
  border-radius: 999px;
  pointer-events: none;
}

.orb::before {
  width: 178px;
  height: 178px;
  background: linear-gradient(180deg, #2bd7ea 0%, #12b1c7 56%, #0a8ca1 100%);
  border: 6px solid rgba(241, 255, 255, 0.96);
  box-shadow:
    0 20px 48px rgba(10, 140, 161, 0.28),
    0 0 0 18px rgba(22, 192, 216, 0.13),
    0 0 0 42px rgba(22, 192, 216, 0.08),
    0 0 0 78px rgba(22, 192, 216, 0.04);
}

.orb::after {
  width: 226px;
  height: 226px;
  border: 1.5px solid rgba(77, 201, 219, 0.18);
}

.orb-core {
  position: relative;
  z-index: 1;
  display: inline-flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
}

.orb svg {
  width: 68px;
  height: 68px;
}

.orb:hover {
  transform: scale(1.03);
  filter: saturate(1.08);
}

.orb.listening::before {
  animation: idlePulse 2.1s ease-in-out infinite;
}

.orb.speaking::before {
  background: linear-gradient(180deg, #49e4f6 0%, #19bfd5 56%, #0892a7 100%);
  box-shadow:
    0 22px 54px rgba(10, 140, 161, 0.34),
    0 0 0 22px rgba(22, 192, 216, 0.20),
    0 0 0 54px rgba(22, 192, 216, 0.12),
    0 0 0 96px rgba(22, 192, 216, 0.07);
}

.orb.speaking::after {
  animation: outerPulse 1.0s ease-in-out infinite;
}

.status {
  font-family: 'Nunito', sans-serif;
  font-size: 1.02rem;
  font-weight: 900;
  color: #0e7284;
  text-align: center;
}

.substatus {
  color: #65808a;
  font-size: 0.9rem;
  text-align: center;
}

@keyframes idlePulse {
  0% {
    box-shadow:
      0 20px 48px rgba(10, 140, 161, 0.28),
      0 0 0 18px rgba(22, 192, 216, 0.13),
      0 0 0 42px rgba(22, 192, 216, 0.08),
      0 0 0 78px rgba(22, 192, 216, 0.04);
  }
  50% {
    box-shadow:
      0 24px 56px rgba(10, 140, 161, 0.32),
      0 0 0 24px rgba(22, 192, 216, 0.15),
      0 0 0 56px rgba(22, 192, 216, 0.10),
      0 0 0 98px rgba(22, 192, 216, 0.04);
  }
  100% {
    box-shadow:
      0 20px 48px rgba(10, 140, 161, 0.28),
      0 0 0 18px rgba(22, 192, 216, 0.13),
      0 0 0 42px rgba(22, 192, 216, 0.08),
      0 0 0 78px rgba(22, 192, 216, 0.04);
  }
}

@keyframes outerPulse {
  0% { transform: translate(-50%, -50%) scale(0.94); opacity: 0.52; }
  70% { transform: translate(-50%, -50%) scale(1.08); opacity: 0.12; }
  100% { transform: translate(-50%, -50%) scale(1.1); opacity: 0.08; }
}
"""

VOICE_RECORDER_JS = """
export default function(component) {
  const { parentElement, setTriggerValue, data } = component;
  const root = parentElement.querySelector('.voice-recorder');
  if (!root) {
    return;
  }
  const button = root.querySelector('.orb');
  const status = root.querySelector('.status');
  const substatus = root.querySelector('.substatus');
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const globalState = window.parent.__mindfulBenVoiceState || {
    recognition: null,
    isListening: false,
    isSpeakingReply: false,
    awaitingServerReply: false,
    conversationActive: false,
    currentReply: '',
    lastReplySerial: 0,
  };
  window.parent.__mindfulBenVoiceState = globalState;
  globalState.button = button;
  globalState.status = status;
  globalState.substatus = substatus;
  globalState.setTriggerValue = setTriggerValue;

  const setIdle = () => {
    button.classList.remove('listening', 'speaking');
    status.textContent = globalState.conversationActive ? 'Ben is ready for you.' : 'Tap once to start talking with Ben.';
    substatus.textContent = globalState.conversationActive
      ? 'Ben will listen again after each reply until you stop the conversation.'
      : 'Hands-free conversation stays on until you tap again.';
  };

  const setListening = () => {
    button.classList.add('listening');
    button.classList.remove('speaking');
    status.textContent = 'Listening...';
    substatus.textContent = 'Speak naturally. Ben will answer when you finish.';
  };

  const setSpeaking = () => {
    button.classList.add('listening', 'speaking');
    status.textContent = 'I hear you';
    substatus.textContent = 'Keep going. Ben is turning your voice into text.';
  };

  const setWorking = () => {
    button.classList.remove('listening', 'speaking');
    status.textContent = 'Sending to Ben...';
    substatus.textContent = 'Ben is getting a reply ready.';
  };

  const setReplying = () => {
    button.classList.add('speaking');
    button.classList.remove('listening');
    status.textContent = 'Ben is talking';
    substatus.textContent = 'When Ben finishes, the microphone will open again.';
  };

  const setUnsupported = () => {
    button.classList.remove('listening', 'speaking');
    status.textContent = 'Voice input is not supported here.';
    substatus.textContent = 'Use Chrome, Edge, or the text box below.';
  };

  const renderState = () => {
    if (!SpeechRecognition) {
      setUnsupported();
      return;
    }

    if (globalState.isSpeakingReply) {
      setReplying();
      return;
    }

    if (globalState.awaitingServerReply) {
      setWorking();
      return;
    }

    if (globalState.isListening) {
      setListening();
      return;
    }

    setIdle();
  };

  const stopListening = () => {
    if (globalState.recognition && globalState.isListening) {
      globalState.recognition.stop();
    }
  };

  const stopConversation = () => {
    globalState.conversationActive = false;
    globalState.awaitingServerReply = false;
    stopListening();
    if ('speechSynthesis' in window.parent) {
      window.parent.speechSynthesis.cancel();
    }
    globalState.isSpeakingReply = false;
    renderState();
  };

  const speakReply = (replyText) => {
    if (!replyText || !('speechSynthesis' in window.parent)) {
      globalState.isSpeakingReply = false;
      renderState();
      if (globalState.conversationActive && !globalState.awaitingServerReply) {
        window.setTimeout(startListening, 180);
      }
      return;
    }

    const synth = window.parent.speechSynthesis;
    synth.cancel();
    const utterance = new window.parent.SpeechSynthesisUtterance(replyText);
    utterance.rate = 0.88;
    utterance.pitch = 0.86;
    utterance.volume = 1.0;
    const voices = synth.getVoices();
    const preferred = voices.find((voice) => /daniel/i.test(`${voice.name} ${voice.voiceURI}`)) || null;
    if (preferred) {
      utterance.voice = preferred;
    }
    utterance.onstart = () => {
      globalState.isSpeakingReply = true;
      renderState();
    };
    utterance.onend = () => {
      globalState.isSpeakingReply = false;
      renderState();
      if (globalState.conversationActive && !globalState.awaitingServerReply) {
        window.setTimeout(startListening, 220);
      }
    };
    utterance.onerror = () => {
      globalState.isSpeakingReply = false;
      renderState();
      if (globalState.conversationActive && !globalState.awaitingServerReply) {
        window.setTimeout(startListening, 220);
      }
    };
    synth.speak(utterance);
  };

  const startListening = () => {
    if (!SpeechRecognition || globalState.isListening || globalState.awaitingServerReply || globalState.isSpeakingReply) {
      renderState();
      return;
    }

    const recognition = new SpeechRecognition();
    globalState.recognition = recognition;
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;
    let finalTranscript = '';
    globalState.isListening = true;
    setListening();

    recognition.onresult = (event) => {
      let interimTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const current = event.results[i][0]?.transcript || '';
        if (event.results[i].isFinal) {
          finalTranscript += `${current} `;
        } else {
          interimTranscript += current;
        }
      }
      if ((finalTranscript + interimTranscript).trim()) {
        setSpeaking();
      }
    };

    recognition.onerror = (event) => {
      globalState.isListening = false;
      button.classList.remove('listening', 'speaking');
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        status.textContent = 'Microphone access was blocked.';
        substatus.textContent = 'Allow microphone access and try again.';
        globalState.conversationActive = false;
      } else if (event.error === 'aborted') {
        renderState();
      } else {
        status.textContent = 'Ben could not hear that clearly.';
        substatus.textContent = globalState.conversationActive
          ? 'Ben will keep the conversation open. Try again when you are ready.'
          : 'Please try again or use the text box below.';
      }
    };

    recognition.onend = () => {
      const transcript = finalTranscript.trim();
      globalState.isListening = false;
      if (!transcript) {
        renderState();
        if (globalState.conversationActive && !globalState.awaitingServerReply && !globalState.isSpeakingReply) {
          window.setTimeout(startListening, 260);
        }
        return;
      }
      globalState.awaitingServerReply = true;
      setWorking();
      setTriggerValue('transcript_payload', {
        transcript,
        source: 'speech_recognition',
        conversation_active: globalState.conversationActive,
        timestamp: Date.now(),
      });
    };

    recognition.start();
  };

  if (!root.dataset.initialized) {
    root.dataset.initialized = 'true';
    button.addEventListener('click', () => {
      globalState.conversationActive = !globalState.conversationActive;
      if (!globalState.conversationActive) {
        stopConversation();
        return;
      }
      if (globalState.awaitingServerReply || globalState.isSpeakingReply) {
        renderState();
        return;
      }
      startListening();
    });
  }

  globalState.awaitingServerReply = Boolean(data?.awaiting_server_reply);
  globalState.conversationActive = Boolean(data?.conversation_active);
  globalState.currentReply = data?.reply_text || '';
  if ((data?.reply_serial || 0) !== globalState.lastReplySerial) {
    globalState.lastReplySerial = data?.reply_serial || 0;
    if (globalState.currentReply) {
      speakReply(globalState.currentReply);
    } else {
      renderState();
    }
  } else {
    renderState();
    if (globalState.conversationActive && !globalState.awaitingServerReply && !globalState.isListening && !globalState.isSpeakingReply) {
      window.setTimeout(startListening, 120);
    }
  }

  return () => {
    stopListening();
  };
}
"""

VOICE_RECORDER_COMPONENT = components.component(
    "ben_voice_recorder",
    html=VOICE_RECORDER_HTML,
    css=VOICE_RECORDER_CSS,
    js=VOICE_RECORDER_JS,
)


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
    st.session_state.setdefault("bob_messages", [])
    st.session_state.setdefault("bob_last_transcript", "")
    st.session_state.setdefault("bob_last_reply_text", "")
    st.session_state.setdefault("bob_reply_serial", 0)
    st.session_state.setdefault("bob_voice_conversation_active", False)


def apply_styles():
    st.markdown(
        build_theme_css(
            st.session_state.get("background_theme", default_settings()["background_theme"]),
            max_width="1180px",
            extra_css="""
        .stApp {
            color: var(--ink-color);
        }

        [data-testid="stAppViewContainer"] {
            background-image:
                radial-gradient(circle at 14% 32%, rgba(8, 166, 183, 0.08), transparent 18%),
                radial-gradient(circle at 78% 22%, rgba(10, 185, 201, 0.08), transparent 16%),
                linear-gradient(rgba(18, 159, 179, 0.06) 1px, transparent 1px),
                linear-gradient(90deg, rgba(18, 159, 179, 0.06) 1px, transparent 1px);
            background-size: 56px 56px;
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        [data-testid="stMainBlockContainer"] {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .voice-shell {
            position: relative;
            overflow: hidden;
            padding: 2rem;
            border-radius: 36px;
            background: linear-gradient(180deg, rgba(255,255,255,0.86), rgba(239,249,250,0.82));
            border: 1px solid color-mix(in srgb, var(--line-color) 68%, #59c1d0);
            box-shadow: 0 22px 60px rgba(11, 85, 98, 0.12);
            backdrop-filter: blur(14px);
        }

        .voice-shell::before {
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 8% 42%, rgba(10, 185, 201, 0.20), transparent 18%),
                radial-gradient(circle at 94% 12%, rgba(87, 214, 232, 0.16), transparent 18%);
            pointer-events: none;
        }

        .voice-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.65rem;
            padding: 0.68rem 1.05rem;
            border-radius: 999px;
            border: 1px solid rgba(33, 174, 195, 0.34);
            background: rgba(191, 248, 255, 0.78);
            color: #067f92;
            font-size: 0.98rem;
            font-weight: 800;
            letter-spacing: 0.01em;
            margin-bottom: 1.25rem;
        }

        .voice-wave {
            display: inline-flex;
            align-items: end;
            gap: 4px;
            height: 24px;
        }

        .voice-wave span {
            width: 4px;
            border-radius: 999px;
            background: linear-gradient(180deg, #5ce1f1 0%, #0aa7bb 100%);
            opacity: 0.9;
        }

        .voice-wave span:nth-child(1) { height: 10px; }
        .voice-wave span:nth-child(2) { height: 16px; }
        .voice-wave span:nth-child(3) { height: 24px; }
        .voice-wave span:nth-child(4) { height: 30px; }
        .voice-wave span:nth-child(5) { height: 20px; }
        .voice-wave span:nth-child(6) { height: 12px; }

        .hero-layout {
            display: grid;
            grid-template-columns: 240px minmax(0, 1fr);
            gap: 2rem;
            align-items: center;
        }

        .mic-stage {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 240px;
        }

        .mic-orb {
            width: 154px;
            height: 154px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(145deg, #18bfd2 0%, #0a889c 100%);
            color: white;
            box-shadow:
                0 0 0 14px rgba(24, 191, 210, 0.10),
                0 0 0 34px rgba(24, 191, 210, 0.08),
                0 30px 60px rgba(8, 136, 156, 0.28);
            border: 4px solid rgba(226, 255, 255, 0.9);
            position: relative;
        }

        .mic-orb::after {
            content: "";
            position: absolute;
            inset: -18px;
            border-radius: 999px;
            border: 2px solid rgba(24, 191, 210, 0.18);
            animation: pulseRing 2.4s ease-out infinite;
        }

        .mic-orb svg {
            width: 68px;
            height: 68px;
        }

        .hero-title {
            margin: 0;
            font-family: 'Nunito', sans-serif;
            font-size: clamp(3rem, 5vw, 4.65rem);
            line-height: 0.98;
            font-weight: 900;
            color: var(--ink-color);
        }

        .hero-title-accent {
            display: block;
            color: #0a95aa;
        }

        .hero-copy {
            margin: 1.2rem 0 0;
            max-width: 760px;
            font-size: 1.34rem;
            line-height: 1.6;
            color: var(--muted-color);
        }

        .hero-subcopy {
            margin: 1rem 0 0;
            max-width: 700px;
            font-size: 1.05rem;
            line-height: 1.65;
            color: var(--muted-color);
        }

        .feature-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.9rem;
            margin-top: 1.8rem;
        }

        .feature-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            padding: 0.95rem 1.2rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(20, 167, 186, 0.18);
            box-shadow: 0 12px 28px rgba(20, 92, 103, 0.10);
            color: #078da1;
            font-size: 1rem;
            font-weight: 700;
        }

        .feature-pill span {
            color: #0aa8bc;
            font-size: 1.1rem;
        }

        .panel {
            margin-top: 1.6rem;
            padding: 1.7rem 1.8rem;
            border-radius: 28px;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(80, 182, 198, 0.20);
            box-shadow: 0 16px 40px rgba(15, 79, 91, 0.08);
        }

        .panel-title {
            margin: 0;
            color: #123848;
            font-family: 'Nunito', sans-serif;
            font-size: 1.28rem;
            font-weight: 800;
        }

        .panel-copy {
            margin: 0.45rem 0 0;
            color: #54717d;
            font-size: 1.02rem;
            line-height: 1.55;
        }

        .stage-note {
            margin-top: 1.15rem;
            padding: 1rem 1.1rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(10, 168, 188, 0.12), rgba(255,255,255,0.86));
            border: 1px solid rgba(10, 168, 188, 0.18);
            color: #0f6f81;
            font-weight: 700;
        }

        .talking-grid {
            display: grid;
            grid-template-columns: minmax(0, 1.15fr) minmax(300px, 0.85fr);
            gap: 1.35rem;
            margin-top: 1.6rem;
        }

        .talking-panel {
            padding: 1.5rem;
            border-radius: 28px;
            background: rgba(255,255,255,0.82);
            border: 1px solid rgba(80, 182, 198, 0.18);
            box-shadow: 0 16px 40px rgba(15, 79, 91, 0.08);
        }

        .talking-label {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.82rem;
            border-radius: 999px;
            background: rgba(222, 248, 250, 0.92);
            color: #0a8295;
            font-size: 0.86rem;
            font-weight: 800;
            letter-spacing: 0.02em;
            text-transform: uppercase;
        }

        .talking-label-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: #11b9ce;
            box-shadow: 0 0 0 0 rgba(17, 185, 206, 0.36);
            animation: pulseDot 1.8s ease-out infinite;
        }

        .talking-title {
            margin: 1rem 0 0;
            font-family: 'Nunito', sans-serif;
            font-size: 1.5rem;
            font-weight: 900;
            color: #123848;
        }

        .talking-copy {
            margin: 0.75rem 0 0;
            color: #54717d;
            font-size: 1.02rem;
            line-height: 1.65;
        }

        .care-steps {
            display: grid;
            gap: 0.8rem;
            margin-top: 1.15rem;
        }

        .care-step {
            padding: 0.95rem 1rem;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(244,252,253,0.98), rgba(234,248,250,0.92));
            border: 1px solid rgba(83, 186, 200, 0.16);
            color: #35525f;
            line-height: 1.55;
        }

        .care-step strong {
            color: #0f7082;
        }

        .status-stack {
            display: grid;
            gap: 0.95rem;
            margin-top: 1.15rem;
        }

        .status-card {
            padding: 1rem 1.05rem;
            border-radius: 22px;
            background: rgba(247, 253, 255, 0.94);
            border: 1px solid rgba(83, 186, 200, 0.16);
        }

        .status-card.active {
            background: linear-gradient(135deg, rgba(9, 171, 192, 0.12), rgba(255,255,255,0.98));
            border-color: rgba(9, 171, 192, 0.28);
        }

        .status-title {
            margin: 0;
            color: #123848;
            font-size: 1rem;
            font-weight: 800;
        }

        .status-copy {
            margin: 0.35rem 0 0;
            color: #5b7480;
            line-height: 1.55;
        }

        .reply-player {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 22px;
            background: linear-gradient(180deg, rgba(234,251,253,0.95), rgba(255,255,255,0.96));
            border: 1px solid rgba(51, 183, 200, 0.18);
        }

        .transcript-chip {
            margin-top: 0.95rem;
            padding: 0.8rem 0.95rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(80, 182, 198, 0.16);
            color: #3e5b67;
            line-height: 1.55;
        }

        .voice-input-wrap {
            margin: 1.45rem 0 1.7rem;
            padding: 0;
        }

        .voice-input-shell {
            position: relative;
            margin: 0 auto;
            width: min(100%, 600px);
            min-height: 0;
            padding: 1.1rem 1.1rem 0.8rem;
            border-radius: 34px;
            background: transparent;
            border: 0;
            box-shadow: none;
            overflow: visible;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .section-spacer {
            height: 1rem;
        }

        .support-note {
            margin-top: 1rem;
            padding: 1rem 1.15rem;
            border-radius: 20px;
            background: rgba(255, 248, 240, 0.94);
            border: 1px solid rgba(241, 188, 123, 0.46);
            color: #8a5927;
            line-height: 1.55;
        }

        .chat-shell {
            margin-top: 1rem;
            padding: 1.1rem 1.1rem 1.25rem;
            border-radius: 30px;
            background: linear-gradient(180deg, rgba(241, 252, 254, 0.92), rgba(255,255,255,0.92));
            border: 1px solid rgba(80, 182, 198, 0.16);
            box-shadow: 0 18px 42px rgba(14, 74, 84, 0.06);
        }

        .chat-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-bottom: 1rem;
            padding-bottom: 0.9rem;
            border-bottom: 1px solid rgba(80, 182, 198, 0.12);
        }

        .chat-title {
            margin: 0;
            color: #123848;
            font-family: 'Nunito', sans-serif;
            font-size: 1.2rem;
            font-weight: 800;
        }

        .chat-subtitle {
            margin: 0.25rem 0 0;
            color: #5a7480;
            font-size: 0.95rem;
        }

        .chat-status {
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            background: rgba(225, 248, 251, 0.95);
            color: #0b899d;
            font-size: 0.84rem;
            font-weight: 800;
            white-space: nowrap;
        }

        .conversation-shell {
            display: grid;
            gap: 0.9rem;
        }

        .conversation-empty {
            padding: 1.05rem 1.15rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.88);
            color: #53707c;
            line-height: 1.6;
            border: 1px dashed rgba(80, 182, 198, 0.22);
        }

        .message-row {
            display: flex;
            align-items: flex-end;
            gap: 0.75rem;
        }

        .message-row.user {
            justify-content: flex-end;
        }

        .message-row.assistant {
            justify-content: flex-start;
        }

        .message-avatar {
            width: 40px;
            height: 40px;
            flex: 0 0 40px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 800;
            color: white;
            box-shadow: 0 10px 22px rgba(8, 136, 156, 0.16);
        }

        .message-row.assistant .message-avatar {
            background: linear-gradient(180deg, #2fd7ea 0%, #119fb5 100%);
        }

        .message-row.user .message-avatar {
            background: linear-gradient(180deg, #0f8ca0 0%, #0a6c7c 100%);
            order: 2;
        }

        .message-card {
            max-width: min(72ch, 78%);
            padding: 0.95rem 1.05rem;
            border-radius: 22px;
            background: rgba(255,255,255,0.96);
            border: 1px solid rgba(72, 179, 195, 0.14);
            box-shadow: 0 12px 26px rgba(14, 74, 84, 0.05);
        }

        .message-row.user .message-card {
            background: linear-gradient(135deg, rgba(18, 182, 204, 0.18), rgba(235,252,255,0.98));
            border-bottom-right-radius: 10px;
        }

        .message-row.assistant .message-card {
            border-bottom-left-radius: 10px;
        }

        .message-role {
            margin-bottom: 0.25rem;
            color: #0d8396;
            font-size: 0.8rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .message-copy {
            color: #415966;
            font-size: 1rem;
            line-height: 1.62;
            white-space: pre-wrap;
        }

        .composer-shell {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 28px;
            background: rgba(255,255,255,0.88);
            border: 1px solid rgba(80, 182, 198, 0.14);
            box-shadow: 0 16px 34px rgba(14, 74, 84, 0.05);
        }

        .composer-title {
            margin: 0;
            color: #123848;
            font-family: 'Nunito', sans-serif;
            font-size: 1.1rem;
            font-weight: 800;
        }

        .composer-copy {
            margin: 0.35rem 0 0.9rem;
            color: #5a7480;
            font-size: 0.95rem;
        }

        @keyframes pulseDot {
            0% { box-shadow: 0 0 0 0 rgba(17, 185, 206, 0.36); }
            70% { box-shadow: 0 0 0 12px rgba(17, 185, 206, 0); }
            100% { box-shadow: 0 0 0 0 rgba(17, 185, 206, 0); }
        }

        @keyframes pulseRing {
            0% { transform: scale(0.96); opacity: 0.8; }
            70% { transform: scale(1.08); opacity: 0; }
            100% { transform: scale(1.08); opacity: 0; }
        }

        div[data-testid="stAudioInput"] > label {
            display: none;
        }

        div[data-testid="stAudioInput"] {
            margin-top: 0;
            margin-bottom: 0;
            overflow: visible !important;
        }

        div[data-testid="stElementContainer"]:has(iframe[title="ben_voice_recorder"]) {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            overflow: visible !important;
        }

        div[data-testid="stElementContainer"]:has(iframe[title="ben_voice_recorder"]) > div:first-child {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            min-height: 0 !important;
            padding: 0 !important;
        }

        iframe[title="ben_voice_recorder"] {
            display: block;
            margin: 0 auto;
            background: transparent !important;
            border: 0 !important;
            border-radius: 30px;
            width: 100% !important;
        }

        div[data-testid="stAudioInput"] > div {
            overflow: visible !important;
            border-radius: 999px;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        div[data-testid="stAudioInput"] > div > button {
            position: relative;
            width: 188px;
            height: 188px;
            margin: 0 auto;
            border-radius: 999px;
            border: 6px solid rgba(238, 255, 255, 0.94);
            background: linear-gradient(180deg, #25cfe2 0%, #0fa8be 55%, #08889c 100%) !important;
            color: white !important;
            box-shadow:
                0 0 0 18px rgba(24, 198, 219, 0.12),
                0 0 0 40px rgba(24, 198, 219, 0.09),
                0 0 0 74px rgba(24, 198, 219, 0.05),
                0 26px 56px rgba(8, 136, 156, 0.24) !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease, background 0.18s ease;
            animation: recorderPulse 2.3s ease-in-out infinite;
        }

        div[data-testid="stAudioInput"] > div > button:hover,
        div[data-testid="stAudioInput"] > div > button:focus,
        div[data-testid="stAudioInput"] > div > button:active {
            transform: scale(1.04);
            box-shadow:
                0 0 0 22px rgba(24, 198, 219, 0.18),
                0 0 0 52px rgba(24, 198, 219, 0.12),
                0 0 0 92px rgba(24, 198, 219, 0.07),
                0 30px 70px rgba(8, 136, 156, 0.30) !important;
            background: linear-gradient(180deg, #3be0f2 0%, #18bbd0 50%, #07879b 100%) !important;
            filter: saturate(1.15);
        }

        div[data-testid="stAudioInput"] button {
            max-width: none;
        }

        div[data-testid="stAudioInput"] div button {
            min-width: auto;
        }

        div[data-testid="stAudioInput"] div div button {
            width: auto;
            height: auto;
            margin: 0;
            padding: 0.35rem 0.55rem;
            border: none;
            border-radius: 12px;
            background: transparent !important;
            box-shadow: none !important;
            transform: none !important;
        }

        div[data-testid="stAudioInput"] svg {
            width: 72px !important;
            height: 72px !important;
        }

        div[data-testid="stAudioInput"] audio {
            width: 100%;
            margin-top: 1.4rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.84);
        }

        @keyframes recorderPulse {
            0% {
                box-shadow:
                    0 0 0 18px rgba(24, 198, 219, 0.12),
                    0 0 0 40px rgba(24, 198, 219, 0.09),
                    0 0 0 74px rgba(24, 198, 219, 0.05),
                    0 26px 56px rgba(8, 136, 156, 0.24);
            }
            50% {
                box-shadow:
                    0 0 0 22px rgba(24, 198, 219, 0.14),
                    0 0 0 52px rgba(24, 198, 219, 0.11),
                    0 0 0 96px rgba(24, 198, 219, 0.03),
                    0 30px 66px rgba(8, 136, 156, 0.29);
            }
            100% {
                box-shadow:
                    0 0 0 18px rgba(24, 198, 219, 0.12),
                    0 0 0 40px rgba(24, 198, 219, 0.09),
                    0 0 0 74px rgba(24, 198, 219, 0.05),
                    0 26px 56px rgba(8, 136, 156, 0.24);
            }
        }

        .stButton > button, .stFormSubmitButton > button {
            min-height: 3.25rem;
            border-radius: 18px;
            border: none;
            font-size: 1rem;
            font-weight: 800;
            color: white;
            background: linear-gradient(135deg, #0da8bc 0%, #087e93 100%);
            box-shadow: 0 14px 28px rgba(8, 126, 147, 0.22);
        }

        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border: none;
            color: white;
        }

        .stTextArea textarea {
            min-height: 120px !important;
            border-radius: 18px !important;
            font-size: 1.02rem !important;
            background: rgba(248, 253, 255, 0.96) !important;
            border: 1px solid rgba(80, 182, 198, 0.16) !important;
        }

        @media (max-width: 900px) {
            .hero-layout {
                grid-template-columns: 1fr;
                gap: 1.3rem;
            }

            .talking-grid {
                grid-template-columns: 1fr;
            }

            .mic-stage {
                min-height: 150px;
            }

            .hero-copy {
                font-size: 1.12rem;
            }

            .voice-input-shell {
                width: min(100%, 100%);
                padding: 1rem 1rem 0.7rem;
            }

            div[data-testid="stAudioInput"] > div > button {
                width: 164px;
                height: 164px;
            }

            div[data-testid="stAudioInput"] svg {
                width: 60px !important;
                height: 60px !important;
            }
        }
        """,
        ),
        unsafe_allow_html=True,
    )


def _secret_or_env(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
        provider_section = st.secrets.get("openai", {})
        if hasattr(provider_section, "get"):
            value = provider_section.get(name.lower().replace("openai_", ""))
            if value is not None:
                return str(value)
    except Exception:
        pass
    return os.getenv(name, default)


def get_openai_client():
    if OpenAI is None:
        return None
    api_key = _secret_or_env("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def format_openai_error(error: Exception) -> str:
    message = str(error).strip().lower()
    status_code = getattr(error, "status_code", None)

    if "credit balance is too low" in message or "insufficient" in message or "billing" in message:
        return (
            "Ben could not reach OpenAI because the API account has no available credit or billing is not active. "
            "Check your OpenAI billing and usage settings, then try again."
        )
    if status_code == 401:
        return "Ben could not reach OpenAI because the OpenAI API key is missing or invalid."
    if status_code == 429 or "rate limit" in message:
        return "Ben is being rate limited right now. Please wait a moment and try again."
    if status_code:
        return f"Ben could not reach OpenAI right now (HTTP {status_code}). Please try again shortly."
    if "api" in type(error).__name__.lower():
        return "Ben could not reach OpenAI right now. Please check your connection and try again."
    return "Something went wrong while Ben was processing that request. Please try again."


def _component_result_value(result, name: str):
    if result is None:
        return None
    if isinstance(result, dict):
        return result.get(name)
    return getattr(result, name, None)


def bob_instructions(user):
    profile = user.get("profile", {})
    support_name = profile.get("support_name") or "their support person"
    support_phone = profile.get("support_phone") or "no support phone saved"
    support_email = profile.get("support_email") or "no support email saved"
    return f"""
You are Ben, a warm, friendly, smooth-talking AI voice companion for an older adult living with dementia.

Your job:
- Speak in short, gentle, reassuring sentences that sound natural out loud.
- Be proactive and practical. If the user seems unsure, suggest the next best small step.
- Help with orientation, reminders, companionship, simple step-by-step help, and emotional support.
- If the user seems confused, slow down and give one step at a time.
- If the user asks where they are, for live directions, or for their current location, explain that exact live location should be checked in the app's "Where Am I?" page or with a trusted person.
- If the user needs urgent support, encourage them to use the app's Help page or contact their support person.
- The saved support contact is: {support_name}, phone: {support_phone}, email: {support_email}.
- Never claim to be a doctor, nurse, therapist, or medical assistant.
- If the user asks for medical advice, medication advice, symptom interpretation, or diagnosis, clearly say that you are not a medical assistant and they should speak with a doctor or call emergency services if it is urgent.
- Be encouraging, patient, practical, and non-judgmental.
- Avoid dense paragraphs and avoid complicated language.
- Keep most replies to 2 or 3 short sentences unless the user asks for more detail.
- Sound like a caring conversation partner, not a scripted assistant.
- If useful, offer options like: "Would you like me to repeat that?" or "Would you like one step at a time?"
- The user's name is {user.get("full_name", "friend")}.
- Today's date is {datetime.now().strftime("%B %d, %Y")}.

Tone:
- Kind
- Grounding
- Respectful
- Never patronizing
- Never alarmist unless it is clearly an emergency
""".strip()


def is_medical_query(text: str) -> bool:
    lowered = text.strip().lower()
    return any(keyword in lowered for keyword in MEDICAL_KEYWORDS)


def append_medical_disclaimer_if_needed(user_text: str, assistant_text: str) -> str:
    if not is_medical_query(user_text):
        return assistant_text
    disclaimer = "Ben is not a medical assistant. Please consult a doctor for medical advice."
    if disclaimer.lower() in assistant_text.lower():
        return assistant_text
    return f"{assistant_text}\n\n{disclaimer}"


def generate_bob_reply(client, user, user_text: str) -> tuple[str, str]:
    history = [{"role": "system", "content": bob_instructions(user)}]
    for message in st.session_state.bob_messages:
        if message["role"] not in {"user", "assistant"}:
            continue
        history.append({"role": message["role"], "content": message["content"]})

    response = client.chat.completions.create(
        model=BOB_MODEL,
        max_tokens=180,
        messages=history,
    )
    reply_text = (response.choices[0].message.content or "").strip()
    reply = append_medical_disclaimer_if_needed(user_text, reply_text)
    return reply, getattr(response, "id", "")


def clear_bob_chat():
    st.session_state.bob_messages = []
    st.session_state.bob_last_transcript = ""
    st.session_state.bob_last_reply_text = ""
    st.session_state.bob_reply_serial = 0
    st.session_state.bob_voice_conversation_active = False


def process_bob_turn(user, user_text: str) -> bool:
    client = get_openai_client()
    if client is None:
        if OpenAI is None:
            st.error(
                "Ben cannot start because the `openai` package is not installed in the Python interpreter running Streamlit. "
                "Install it there with `python -m pip install openai`, or start Streamlit from this project's `.venv`."
            )
            return False
        st.error("Ben needs an OpenAI API key before chat can work. Add `OPENAI_API_KEY` to `.streamlit/secrets.toml` or your environment.")
        return False

    cleaned_text = user_text.strip()
    if not cleaned_text:
        st.error("Please say or type something for Ben.")
        return False

    st.session_state.bob_messages.append({"role": "user", "content": cleaned_text})

    try:
        with st.spinner("Ben is thinking and preparing a reply..."):
            reply_text, response_id = generate_bob_reply(client, user, cleaned_text)
    except Exception as error:
        st.error(format_openai_error(error))
        return False

    if not reply_text:
        st.error("Ben did not return a reply. Please try again.")
        return False

    st.session_state.bob_last_reply_text = reply_text
    st.session_state.bob_reply_serial += 1
    st.session_state.bob_messages.append({"role": "assistant", "content": reply_text})
    return True


def process_recording_if_needed(user, transcript_payload):
    if transcript_payload is None:
        return

    transcript = ""
    if isinstance(transcript_payload, dict):
        transcript = str(transcript_payload.get("transcript", "")).strip()
    else:
        transcript = str(transcript_payload).strip()

    if not transcript:
        return

    if transcript == st.session_state.bob_last_transcript:
        return

    st.session_state.bob_last_transcript = transcript
    if isinstance(transcript_payload, dict):
        st.session_state.bob_voice_conversation_active = bool(transcript_payload.get("conversation_active"))
    if process_bob_turn(user, transcript):
        st.rerun()


def render_hero():
    st.markdown(
        """
        <div class="voice-shell">
            <div class="voice-badge">
                <span>Mindful Voice Companion</span>
                <span class="voice-wave">
                    <span></span><span></span><span></span><span></span><span></span><span></span>
                </span>
            </div>
            <div class="hero-layout">
                <div class="mic-stage">
                    <div class="mic-orb">
                        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                            <path d="M12 15a3 3 0 0 0 3-3V7a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3Z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M18 11.5a6 6 0 0 1-12 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                            <path d="M12 17.5v3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                            <path d="M9 20.5h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                        </svg>
                    </div>
                </div>
                <div>
                    <div class="hero-title">
                        Talk to Ben.
                        <span class="hero-title-accent">A friendly voice inside Mindful.</span>
                    </div>
                    <p class="hero-copy">
                        Start a voice conversation with Ben. Speak naturally, and Ben listens, responds clearly,
                        and helps with memory, orientation, and gentle next steps.
                    </p>
                    <p class="hero-subcopy">
                        Built for reassurance: friendly replies, simple language, and a hands-free conversation that can keep going.
                    </p>
                    <div class="feature-row">
                        <div class="feature-pill"><span>+</span> Voice-first and easy to use</div>
                        <div class="feature-pill"><span>+</span> Warm replies spoken back out loud</div>
                        <div class="feature-pill"><span>+</span> Gentle support for memory and orientation</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_voice_panel(user):
    st.markdown("<div class='voice-input-wrap'><div class='voice-input-shell'>", unsafe_allow_html=True)
    recorder_result = VOICE_RECORDER_COMPONENT(
        key="bob_voice_recorder_component",
        data={
            "conversation_active": st.session_state.bob_voice_conversation_active,
            "reply_text": st.session_state.bob_last_reply_text,
            "reply_serial": st.session_state.bob_reply_serial,
            "awaiting_server_reply": False,
        },
        height=300,
        on_transcript_payload_change=lambda: None,
    )
    st.markdown("</div></div>", unsafe_allow_html=True)
    transcript_payload = _component_result_value(recorder_result, "transcript_payload")
    process_recording_if_needed(user, transcript_payload)

    if transcript_payload is not None:
        if st.session_state.bob_last_transcript:
            safe_transcript = html.escape(st.session_state.bob_last_transcript)
            st.markdown(
                f"<div class='transcript-chip'><strong>You said:</strong> {safe_transcript}</div>",
                unsafe_allow_html=True,
            )


def render_reply_panel():
    reply_text = st.session_state.bob_last_reply_text
    if not reply_text:
        return

    safe_reply_text = html.escape(reply_text)
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Ben's latest reply</div>
            <div class="panel-copy">Ben speaks this out loud automatically during voice conversation.</div>
            <div class="reply-player">
                <div class="message-copy">{safe_reply_text}</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_chat_history():
    st.markdown("<div class='section-spacer'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="chat-shell">
            <div class="chat-header">
                <div>
                    <div class="chat-title">Conversation with Ben</div>
                    <div class="chat-subtitle">A calmer back-and-forth that reads like a real chat.</div>
                </div>
                <div class="chat-status">Mindful voice ready</div>
            </div>
            <div class='conversation-shell'>
        """,
        unsafe_allow_html=True,
    )
    if not st.session_state.bob_messages:
        st.markdown(
            """
            <div class="conversation-empty">
                Ben is ready to help. Try saying something simple like:
                "What day is it today?" or "Help me remember my next step."
            </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("</div></div>", unsafe_allow_html=True)
        return

    for message in st.session_state.bob_messages[-10:]:
        role_label = "You" if message["role"] == "user" else "Ben"
        role_class = "user" if message["role"] == "user" else "assistant"
        avatar_label = "You" if role_class == "user" else "Ben"
        safe_content = html.escape(message["content"])
        st.markdown(
            f"<div class='message-row {role_class}'><div class='message-avatar'>{avatar_label}</div><div class='message-card'>",
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='message-role'>{role_label}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='message-copy'>{safe_content}</div>", unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)


def render_text_fallback(user):
    with st.form("bob_text_form"):
        st.markdown(
            """
            <div class="composer-shell">
                <div class="composer-title">Send a message to Ben</div>
                <div class="composer-copy">Use this when speaking feels hard or the room is too noisy.</div>
            """,
            unsafe_allow_html=True,
        )
        typed_message = st.text_area(
            "Message",
            height=120,
            placeholder="Ben, can you help me remember what to do next?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Send text to Ben", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submitted:
        if process_bob_turn(user, typed_message):
            st.rerun()


def render_support_controls():
    control_col1, control_col2, control_col3 = st.columns(3)
    if control_col1.button("Open Help Page", use_container_width=True):
        st.switch_page("pages/help.py")
    if control_col2.button("Open Where Am I?", use_container_width=True):
        st.switch_page("pages/where_am_i.py")
    if control_col3.button("Clear Ben Conversation", use_container_width=True):
        clear_bob_chat()
        st.rerun()

    st.markdown(
        """
        <div class="support-note">
            Ben can offer comfort, reminders, and simple step-by-step help, but Ben is not a medical assistant.
            For medical advice, medicine questions, symptoms, or emergencies, contact a doctor or emergency services.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page(user):
    render_hero()
    render_support_controls()
    render_voice_panel(user)
    render_reply_panel()
    render_chat_history()
    render_text_fallback(user)


def main():
    st.set_page_config(page_title="Mindful | Ben", page_icon=":microphone:", layout="wide")
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
