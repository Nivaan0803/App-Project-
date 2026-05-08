THEME_OPTIONS = {
    "Warm Cream": {
        "bg_top": "#f3efe2",
        "bg_bottom": "#fcfaf5",
        "glow_left": "rgba(244, 215, 191, 0.85)",
        "glow_right": "rgba(126, 163, 127, 0.18)",
    },
    "Soft Sky": {
        "bg_top": "#e8f0f8",
        "bg_bottom": "#f9fcff",
        "glow_left": "rgba(181, 206, 236, 0.72)",
        "glow_right": "rgba(255, 221, 186, 0.24)",
    },
    "Gentle Mint": {
        "bg_top": "#eaf4ee",
        "bg_bottom": "#fbfdfb",
        "glow_left": "rgba(196, 227, 208, 0.75)",
        "glow_right": "rgba(246, 221, 192, 0.22)",
    },
    "Rose Morning": {
        "bg_top": "#f7ece7",
        "bg_bottom": "#fffaf7",
        "glow_left": "rgba(240, 201, 193, 0.72)",
        "glow_right": "rgba(247, 225, 188, 0.24)",
    },
}


def default_settings():
    return {
        "background_theme": "Warm Cream",
        "familiar_greeting": "",
        "show_familiar_greeting": True,
        "text_size": "Standard",
        "ben_voice_uri": "",
        "ben_voice_name": "",
    }


def normalize_settings(settings):
    normalized = {**default_settings(), **(settings or {})}
    if normalized["background_theme"] not in THEME_OPTIONS:
        normalized["background_theme"] = "Warm Cream"
    if normalized["text_size"] not in {"Standard", "Large"}:
        normalized["text_size"] = "Standard"
    normalized["familiar_greeting"] = str(normalized.get("familiar_greeting", "")).strip()
    normalized["show_familiar_greeting"] = bool(normalized.get("show_familiar_greeting", True))
    normalized["ben_voice_uri"] = str(normalized.get("ben_voice_uri", "")).strip()
    normalized["ben_voice_name"] = str(normalized.get("ben_voice_name", "")).strip()
    return normalized


def get_theme(theme_name):
    normalized = normalize_settings({"background_theme": theme_name})
    return THEME_OPTIONS[normalized["background_theme"]]


def apply_user_settings_to_session(session_state, user):
    settings = normalize_settings(user.get("profile", {}).get("settings", {}))
    session_state.background_theme = settings["background_theme"]
    session_state.familiar_greeting = settings["familiar_greeting"]
    session_state.show_familiar_greeting = settings["show_familiar_greeting"]
    session_state.text_size = settings["text_size"]
    session_state.ben_voice_uri = settings["ben_voice_uri"]
    session_state.ben_voice_name = settings["ben_voice_name"]
    return settings


def build_theme_css(theme_name, max_width="1040px", extra_css=""):
    theme = get_theme(theme_name)
    return f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Lexend:wght@400;500;600;700&family=Nunito:wght@700;800&display=swap');

        :root {{
            --bg-top: {theme['bg_top']};
            --bg-bottom: {theme['bg_bottom']};
            --glow-left: {theme['glow_left']};
            --glow-right: {theme['glow_right']};
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, var(--glow-left), transparent 28%),
                radial-gradient(circle at top right, var(--glow-right), transparent 22%),
                linear-gradient(180deg, var(--bg-top) 0%, var(--bg-bottom) 100%);
            font-family: 'Lexend', sans-serif;
        }}

        .block-container {{
            max-width: {max_width};
            padding-top: 1.55rem;
            padding-bottom: 3rem;
        }}

        {extra_css}
        </style>
    """
