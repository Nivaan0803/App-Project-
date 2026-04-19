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
    }


def normalize_settings(settings):
    normalized = {**default_settings(), **(settings or {})}
    if normalized["background_theme"] not in THEME_OPTIONS:
        normalized["background_theme"] = "Warm Cream"
    if normalized["text_size"] not in {"Standard", "Large"}:
        normalized["text_size"] = "Standard"
    normalized["familiar_greeting"] = str(normalized.get("familiar_greeting", "")).strip()
    normalized["show_familiar_greeting"] = bool(normalized.get("show_familiar_greeting", True))
    return normalized


def get_theme(theme_name):
    normalized = normalize_settings({"background_theme": theme_name})
    return THEME_OPTIONS[normalized["background_theme"]]
