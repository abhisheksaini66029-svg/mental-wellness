"""
config.py — Application-wide constants, labels, and settings for MindLog.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Gemini ────────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = "wellness_journal.db"
DB_URL: str = f"sqlite:///{DB_PATH}"

# ── Scale bounds ──────────────────────────────────────────────────────────────
MOOD_MIN, MOOD_MAX = 1, 10
STRESS_MIN, STRESS_MAX = 1, 10

# ── Rich mood labels ──────────────────────────────────────────────────────────
MOOD_LABELS = {
    1:  ("Terrible",      "😭", "#e53935"),
    2:  ("Very Bad",      "😢", "#ef5350"),
    3:  ("Bad",           "😟", "#f4511e"),
    4:  ("Below Average", "😕", "#fb8c00"),
    5:  ("Neutral",       "😐", "#fdd835"),
    6:  ("Okay",          "🙂", "#c0ca33"),
    7:  ("Good",          "😊", "#7cb342"),
    8:  ("Great",         "😁", "#43a047"),
    9:  ("Excellent",     "🤩", "#00897b"),
    10: ("Amazing",       "🥳", "#1e88e5"),
}

STRESS_LABELS = {
    1:  ("Completely Calm",    "🧘", "#1e88e5"),
    2:  ("Very Relaxed",       "😌", "#00897b"),
    3:  ("Relaxed",            "😊", "#43a047"),
    4:  ("Mild Stress",        "🙂", "#7cb342"),
    5:  ("Moderate Stress",    "😐", "#fdd835"),
    6:  ("Noticeable Stress",  "😕", "#fb8c00"),
    7:  ("Stressed",           "😟", "#f4511e"),
    8:  ("Very Stressed",      "😰", "#ef5350"),
    9:  ("Extremely Stressed", "😱", "#e53935"),
    10: ("Overwhelmed",        "🤯", "#b71c1c"),
}

ENERGY_LABELS = {
    1:  "Completely Drained",
    2:  "Very Low Energy",
    3:  "Low Energy",
    4:  "Sluggish",
    5:  "Moderate",
    6:  "Getting There",
    7:  "Energised",
    8:  "High Energy",
    9:  "Very High Energy",
    10: "Fully Charged",
}

# ── Activity tags ─────────────────────────────────────────────────────────────
POSITIVE_ACTIVITIES = [
    "Exercise / Gym", "Morning Walk", "Meditation", "Yoga",
    "Reading", "Journaling", "Creative Activity", "Cooking Healthy",
    "Social Time", "Time in Nature", "Therapy Session", "Good Sleep",
    "Healthy Eating", "Music / Podcast", "Acts of Kindness",
]
NEGATIVE_ACTIVITIES = [
    "Poor Sleep", "Skipped Meals", "Alcohol / Substances", "Excessive Screen Time",
    "Social Isolation", "Overworking", "Late Night", "Conflict / Argument",
    "Skipped Exercise", "Junk Food",
]
ALL_ACTIVITIES = POSITIVE_ACTIVITIES + NEGATIVE_ACTIVITIES

# ── Analytics thresholds ──────────────────────────────────────────────────────
LOW_MOOD_THRESHOLD       = 4
HIGH_STRESS_THRESHOLD    = 7
CONSECUTIVE_CONCERN_DAYS = 3
ROLLING_WINDOW_DAYS      = 7

# ── Navigation pages ──────────────────────────────────────────────────────────
PAGES = {
    "Daily Journal":       "📝",
    "Analytics Dashboard": "📊",
    "AI Insights":         "🤖",
    "Therapist Report":    "📋",
    "My History":          "📅",
}

# ── App metadata ──────────────────────────────────────────────────────────────
APP_TITLE   = "MindLog"
APP_TAGLINE = "Your private AI-powered mental wellness companion"
APP_ICON    = "🧠"
APP_VERSION = "2.0"

# ── Colour palette (used in charts) ──────────────────────────────────────────
COLOR_MOOD       = "#4CAF50"
COLOR_STRESS     = "#F44336"
COLOR_ENERGY     = "#FF9800"
COLOR_SLEEP      = "#2196F3"
COLOR_MOOD_ROLL  = "#A5D6A7"
COLOR_STRESS_ROLL= "#EF9A9A"
COLOR_ACCENT     = "#7C4DFF"
COLOR_BG         = "#F8F9FA"
