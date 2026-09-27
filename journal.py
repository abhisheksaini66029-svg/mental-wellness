"""
journal.py — Polished daily journal entry form for MindLog v2.
"""

from __future__ import annotations

import datetime
from typing import Optional

import streamlit as st

from config import (
    MOOD_LABELS, STRESS_LABELS, ENERGY_LABELS,
    POSITIVE_ACTIVITIES, NEGATIVE_ACTIVITIES,
)
from database import get_entry_for_date, upsert_entry, JournalEntry


def _prefill(entry: Optional[JournalEntry]) -> dict:
    if entry is None:
        return dict(mood=5, stress=5, energy=6, sleep=7.5,
                    journal_notes="", gratitude_notes="",
                    pos_activities=[], neg_activities=[])
    acts = (entry.activities or "").split(",")
    return dict(
        mood=entry.mood_score,
        stress=entry.stress_score,
        energy=entry.energy_level or 6,
        sleep=entry.sleep_hours or 7.5,
        journal_notes=entry.journal_notes or "",
        gratitude_notes=entry.gratitude_notes or "",
        pos_activities=[a for a in acts if a in POSITIVE_ACTIVITIES],
        neg_activities=[a for a in acts if a in NEGATIVE_ACTIVITIES],
    )


def render_journal_form(username: str) -> None:
    # ── Header ─────────────────────────────────────────────────────────────────
    st.markdown("## 📝 Daily Journal")
    st.markdown(
        "> *\"Logging how you feel is the first step to understanding yourself.\"*  \n"
        "Take a few minutes to check in with yourself. Your entries stay private."
    )
    st.divider()

    # ── Date ───────────────────────────────────────────────────────────────────
    col_d, col_day = st.columns([2, 5])
    with col_d:
        entry_date: datetime.date = st.date_input(
            "Entry Date",
            value=datetime.date.today(),
            max_value=datetime.date.today(),
            key="journal_date",
        )
    with col_day:
        st.markdown(f"**{entry_date.strftime('%A, %B %d %Y')}**")
        st.caption("You can back-fill entries for previous days.")

    existing = get_entry_for_date(username, entry_date)
    pf = _prefill(existing)

    if existing:
        st.info("✏️ An entry already exists for this date — you are editing it.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — WELLNESS SCORES
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 🌡️ How are you feeling right now?")
    st.caption("Drag each slider to reflect your current state.")

    col1, col2, col3 = st.columns(3)

    with col1:
        mood_name, mood_emoji, mood_color = MOOD_LABELS[5]
        mood = st.slider("Mood", 1, 10, pf["mood"], key="mood_sl",
                         help="1 = Terrible · 10 = Amazing")
        mood_name, mood_emoji, mood_color = MOOD_LABELS[mood]
        st.metric(label="Mood Score", value=f"{mood}/10",
                  delta=mood_name)

    with col2:
        stress = st.slider("Stress Level", 1, 10, pf["stress"], key="stress_sl",
                           help="1 = Completely Calm · 10 = Overwhelmed")
        stress_name, stress_emoji, stress_color = STRESS_LABELS[stress]
        st.metric(label="Stress Score", value=f"{stress}/10",
                  delta=stress_name, delta_color="inverse")

    with col3:
        energy = st.slider("Energy Level", 1, 10, pf["energy"], key="energy_sl",
                           help="1 = Exhausted · 10 = Fully Charged")
        st.metric(label="Energy Score", value=f"{energy}/10",
                  delta=ENERGY_LABELS[energy])

    # Visual mood status bar
    st.markdown("---")
    mood_bar_cols = st.columns(10)
    for i, col in enumerate(mood_bar_cols, start=1):
        nm, em, _ = MOOD_LABELS[i]
        if i == mood:
            col.markdown(f"**{em}**")
        else:
            col.markdown(f"{em}")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — SLEEP
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 💤 Sleep Quality")
    sl1, sl2 = st.columns([2, 5])
    with sl1:
        sleep = st.number_input(
            "Hours slept last night",
            min_value=0.0, max_value=16.0,
            value=float(pf["sleep"]), step=0.5,
            key="sleep_inp",
        )
    with sl2:
        if sleep < 5:
            st.warning(f"Only **{sleep}h** — chronic short sleep impacts mood and cognition.")
        elif sleep > 9:
            st.info(f"**{sleep}h** — oversleeping can sometimes indicate low energy or mood issues.")
        else:
            st.success(f"**{sleep}h** — great! You're in the healthy sleep range.")

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — ACTIVITIES
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 🏃 Activities & Habits")
    st.caption("Select everything that applies to your day.")

    act_col1, act_col2 = st.columns(2)
    with act_col1:
        st.markdown("**Positive habits today:**")
        pos_acts = st.multiselect(
            "Positive activities",
            options=POSITIVE_ACTIVITIES,
            default=[a for a in pf["pos_activities"] if a in POSITIVE_ACTIVITIES],
            key="pos_acts",
            label_visibility="collapsed",
        )
    with act_col2:
        st.markdown("**Challenging habits today:**")
        neg_acts = st.multiselect(
            "Challenging activities",
            options=NEGATIVE_ACTIVITIES,
            default=[a for a in pf["neg_activities"] if a in NEGATIVE_ACTIVITIES],
            key="neg_acts",
            label_visibility="collapsed",
        )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — JOURNAL NOTES
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 📖 Free Journal")
    st.caption("Write freely — no structure needed. The AI reads this to personalise insights.")
    journal_notes = st.text_area(
        "What's on your mind today?",
        value=pf["journal_notes"],
        height=180,
        placeholder=(
            "How are you feeling? What happened today? "
            "Any thoughts, worries, or wins worth noting? "
            "The more you write, the better the AI insights."
        ),
        key="jnotes",
    )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — GRATITUDE
    # ═══════════════════════════════════════════════════════════════════════════
    st.markdown("### 🙏 Gratitude Check-in")
    st.caption(
        "Research shows that noting 3 things you're grateful for "
        "significantly improves wellbeing over time."
    )
    gratitude_notes = st.text_area(
        "What are you grateful for today?",
        value=pf["gratitude_notes"],
        height=110,
        placeholder="1. A good cup of coffee\n2. A kind message from a friend\n3. The sun was out today",
        key="gnotes",
    )

    st.divider()

    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════════════════════════
    save_c, tip_c = st.columns([2, 5])
    with save_c:
        save_btn = st.button(
            "💾  Save Entry",
            type="primary",
            use_container_width=True,
        )
    with tip_c:
        st.caption(
            "After saving, head to **AI Insights** for personalised feedback "
            "or **Analytics Dashboard** to see your trends."
        )

    if save_btn:
        all_acts = pos_acts + neg_acts
        entry = upsert_entry(
            username=username,
            entry_date=entry_date,
            mood_score=mood,
            stress_score=stress,
            energy_level=energy,
            sleep_hours=sleep,
            journal_notes=journal_notes,
            gratitude_notes=gratitude_notes,
            activities=",".join(all_acts),
        )
        st.success(
            f"Entry saved for **{entry_date.strftime('%A, %B %d %Y')}**! "
            "Navigate to AI Insights for personalised feedback."
        )
        st.session_state["last_saved_entry_id"] = entry.id
        st.balloons()
