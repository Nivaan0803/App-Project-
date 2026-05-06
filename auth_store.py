import base64
import hashlib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

from ui_preferences import default_settings, normalize_settings


DATA_FILE = Path(__file__).with_name("users.json")
BAD_WORDS = ("damn", "hell", "stupid", "idiot", "dumb", "crap")


def default_progress():
    return {
        "total_sessions": 0,
        "completed_challenges": 0,
        "last_check_in": {},
        "history": [],
        "reminders": [],
        "calendar_events": [],
        "activity_history": [],
    }


def default_profile():
    return {
        "role": "senior",
        "support_name": "",
        "support_email": "",
        "support_phone": "",
        "loved_ones": [],
        "settings": default_settings(),
    }


def normalize_user_record(user):
    normalized = dict(user)
    normalized.setdefault("email", "")
    normalized.setdefault("password_reset", {})
    normalized["profile"] = {**default_profile(), **normalized.get("profile", {})}
    normalized["profile"]["loved_ones"] = [
        {
            "name": loved_one.get("name", ""),
            "relationship": loved_one.get("relationship", ""),
            "image_data": loved_one.get("image_data", ""),
            "mime_type": loved_one.get("mime_type", "image/jpeg"),
            "audio_data": loved_one.get("audio_data", ""),
            "audio_mime_type": loved_one.get("audio_mime_type", ""),
        }
        for loved_one in normalized["profile"].get("loved_ones", [])[:12]
    ]
    normalized["profile"]["settings"] = normalize_settings(normalized["profile"].get("settings", {}))
    progress = {**default_progress(), **normalized.get("progress", {})}
    progress["history"] = progress.get("history", [])[:10]
    progress["reminders"] = progress.get("reminders", [])
    progress["calendar_events"] = progress.get("calendar_events", [])[:48]
    progress["activity_history"] = progress.get("activity_history", [])[:12]
    normalized["progress"] = progress
    return normalized


def _read_users():
    if not DATA_FILE.exists():
        return {}

    try:
        users = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    if not isinstance(users, dict):
        return {}

    return {username: normalize_user_record(user) for username, user in users.items()}


def _write_users(users):
    DATA_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def contains_bad_words(text):
    lowered = text.strip().lower()
    return any(bad_word in lowered for bad_word in BAD_WORDS)


def sanitize_text(text):
    sanitized = text
    for bad_word in BAD_WORDS:
        pattern = re.compile(re.escape(bad_word), re.IGNORECASE)
        sanitized = pattern.sub("*" * len(bad_word), sanitized)
    return sanitized


def register_user(full_name, email, username, password):
    users = _read_users()
    normalized_username = username.strip().lower()
    normalized_email = email.strip().lower()

    if normalized_username in users:
        return False, "That username is already in use."

    if any(user.get("email", "").lower() == normalized_email for user in users.values()):
        return False, "That email is already in use."

    users[normalized_username] = {
        "full_name": sanitize_text(full_name.strip()),
        "email": normalized_email,
        "password_hash": hash_password(password),
        "created_at": datetime.utcnow().isoformat(),
        "profile": default_profile(),
        "progress": default_progress(),
    }
    _write_users(users)
    return True, "Account created. You can log in now."


def authenticate_user(email, password):
    users = _read_users()
    normalized_email = email.strip().lower()
    matched_username = None
    user = None

    for username, stored_user in users.items():
        if stored_user.get("email", "").lower() == normalized_email:
            matched_username = username
            user = stored_user
            break

    if not user or user["password_hash"] != hash_password(password):
        return False, None

    return True, {
        "username": matched_username,
        "full_name": user["full_name"],
        "email": user.get("email", ""),
        "profile": user.get("profile", default_profile()),
        "progress": user.get("progress", {}),
    }


def _find_user_by_email(users, email):
    normalized_email = email.strip().lower()
    for username, stored_user in users.items():
        if stored_user.get("email", "").lower() == normalized_email:
            return username, stored_user
    return None, None


def get_user(username):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)
    if not user:
        return None

    return {
        "username": normalized_username,
        "full_name": user["full_name"],
        "email": user.get("email", ""),
        "profile": user.get("profile", default_profile()),
        "progress": user.get("progress", {}),
    }


def create_password_reset(email, code, expiry_minutes=15):
    users = _read_users()
    username, user = _find_user_by_email(users, email)

    if not user:
        return False, "We couldn't find an account with that email."

    user["password_reset"] = {
        "code_hash": hash_password(code.strip()),
        "expires_at": (datetime.utcnow() + timedelta(minutes=expiry_minutes)).isoformat(),
        "requested_at": datetime.utcnow().isoformat(),
        "attempts": 0,
    }
    _write_users(users)
    return True, username


def clear_password_reset(email):
    users = _read_users()
    _, user = _find_user_by_email(users, email)

    if not user:
        return False

    user["password_reset"] = {}
    _write_users(users)
    return True


def reset_password_with_code(email, code, new_password, max_attempts=5):
    users = _read_users()
    _, user = _find_user_by_email(users, email)

    if not user:
        return False, "We couldn't find an account with that email."

    reset_data = user.get("password_reset", {})
    code_hash = reset_data.get("code_hash", "")
    expires_at = reset_data.get("expires_at", "")

    if not code_hash or not expires_at:
        return False, "Please request a new reset code first."

    try:
        expires_on = datetime.fromisoformat(expires_at)
    except ValueError:
        user["password_reset"] = {}
        _write_users(users)
        return False, "Your reset code is no longer valid. Please request a new one."

    if datetime.utcnow() > expires_on:
        user["password_reset"] = {}
        _write_users(users)
        return False, "Your reset code has expired. Please request a new one."

    if hash_password(code.strip()) != code_hash:
        reset_data["attempts"] = int(reset_data.get("attempts", 0)) + 1
        if reset_data["attempts"] >= max_attempts:
            user["password_reset"] = {}
            _write_users(users)
            return False, "Too many incorrect code attempts. Please request a new code."
        user["password_reset"] = reset_data
        _write_users(users)
        return False, "That reset code is incorrect."

    user["password_hash"] = hash_password(new_password)
    user["password_reset"] = {}
    _write_users(users)
    return True, "Password updated successfully."


def save_progress(username, mood, medicine_taken, challenge_name, challenge_response):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    progress = user.setdefault("progress", {})
    history = progress.setdefault("history", [])
    progress["total_sessions"] = int(progress.get("total_sessions", 0)) + 1
    progress["completed_challenges"] = int(progress.get("completed_challenges", 0)) + 1
    progress["last_check_in"] = {
        "mood": mood,
        "medicine_taken": medicine_taken,
        "challenge_name": challenge_name,
        "challenge_response": sanitize_text(challenge_response),
        "saved_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    }
    history.insert(0, progress["last_check_in"])
    progress["history"] = history[:10]

    _write_users(users)
    return True


def save_activity_progress(username, activity_name, score_label, details):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    progress = user.setdefault("progress", default_progress())
    activity_history = progress.setdefault("activity_history", [])
    activity_entry = {
        "activity_name": activity_name,
        "score_label": score_label,
        "details": sanitize_text(details),
        "saved_at": datetime.now().strftime("%B %d, %Y %I:%M %p"),
    }
    activity_history.insert(0, activity_entry)
    progress["activity_history"] = activity_history[:12]
    progress["completed_challenges"] = int(progress.get("completed_challenges", 0)) + 1
    _write_users(users)
    return True


def save_reminders(username, reminders):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    cleaned_reminders = []
    for reminder in reminders:
        title = sanitize_text(reminder.get("title", "").strip())
        time_label = reminder.get("time", "").strip()
        note = sanitize_text(reminder.get("note", "").strip())

        if title and time_label:
            cleaned_reminders.append(
                {
                    "title": title,
                    "time": time_label,
                    "note": note,
                }
            )

    user.setdefault("progress", default_progress())["reminders"] = cleaned_reminders[:8]
    _write_users(users)
    return True


def save_calendar_events(username, events):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    cleaned_events = []
    for index, event in enumerate(events):
        title = sanitize_text(event.get("title", "").strip())
        event_date = event.get("date", "").strip()
        start_time = event.get("start_time", "").strip()
        end_time = event.get("end_time", "").strip()
        color = event.get("color", "").strip() or "#4d8f7a"
        note = sanitize_text(event.get("note", "").strip())

        if title and event_date and start_time:
            cleaned_events.append(
                {
                    "id": event.get("id") or f"{normalized_username}-{index}-{event_date}-{start_time}",
                    "title": title,
                    "date": event_date,
                    "start_time": start_time,
                    "end_time": end_time,
                    "color": color,
                    "note": note,
                }
            )

    user.setdefault("progress", default_progress())["calendar_events"] = cleaned_events[:48]
    _write_users(users)
    return True


def save_profile(username, role, support_name, support_email, support_phone):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    profile = {**default_profile(), **user.get("profile", {})}
    user["profile"] = {
        "role": role.strip().lower() or "senior",
        "support_name": sanitize_text(support_name.strip()),
        "support_email": support_email.strip().lower(),
        "support_phone": support_phone.strip(),
        "loved_ones": profile.get("loved_ones", []),
        "settings": normalize_settings(profile.get("settings", {})),
    }
    _write_users(users)
    return True


def save_settings(username, settings):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    profile = {**default_profile(), **user.get("profile", {})}
    user["profile"] = {
        **profile,
        "settings": normalize_settings(settings),
    }
    _write_users(users)
    return True


def add_loved_one(username, loved_one_name, relationship, image_bytes, mime_type, audio_bytes=None, audio_mime_type=""):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    profile = user.setdefault("profile", default_profile())
    loved_ones = profile.setdefault("loved_ones", [])
    loved_ones.append(
        {
            "name": sanitize_text(loved_one_name.strip()),
            "relationship": sanitize_text(relationship.strip()),
            "image_data": base64.b64encode(image_bytes).decode("utf-8"),
            "mime_type": mime_type.strip() or "image/jpeg",
            "audio_data": base64.b64encode(audio_bytes).decode("utf-8") if audio_bytes else "",
            "audio_mime_type": audio_mime_type.strip() if audio_bytes else "",
        }
    )
    profile["loved_ones"] = loved_ones[:12]
    _write_users(users)
    return True


def clear_loved_ones(username):
    users = _read_users()
    normalized_username = username.strip().lower()
    user = users.get(normalized_username)

    if not user:
        return False

    profile = user.setdefault("profile", default_profile())
    profile["loved_ones"] = []
    _write_users(users)
    return True
