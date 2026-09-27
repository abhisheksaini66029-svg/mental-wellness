"""
ai_engine.py — Gemini 2.5 Flash integration for MindLog v2.
Uses the modern google-genai SDK.
"""

from __future__ import annotations

import textwrap

import pandas as pd
import streamlit as st
from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL
from database import JournalEntry, update_ai_fields, save_therapist_note
from analytics import entries_to_df, detect_patterns, compute_summary


# ── Client ─────────────────────────────────────────────────────────────────────

def _get_client():
    api_key = GEMINI_API_KEY or st.session_state.get("gemini_api_key", "")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)


def _generate(prompt: str) -> str:
    client = _get_client()
    if client is None:
        return "__NO_KEY__"
    response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
    return response.text.strip()


# ── Prompts ────────────────────────────────────────────────────────────────────

def _entry_prompt(entry: JournalEntry) -> str:
    return textwrap.dedent(f"""
        You are a compassionate mental wellness AI assistant.
        Analyse the following journal entry and provide a structured response.

        --- Journal Entry ---
        Date        : {entry.entry_date.date() if entry.entry_date else 'Unknown'}
        Mood        : {entry.mood_score}/10
        Stress      : {entry.stress_score}/10
        Energy      : {entry.energy_level or 'N/A'}/10
        Sleep       : {entry.sleep_hours or 'N/A'} hours
        Activities  : {entry.activities or 'None'}
        Journal     : {entry.journal_notes or '(none)'}
        Gratitude   : {entry.gratitude_notes or '(none)'}
        ---

        Reply in this EXACT format (no markdown, no extra lines):
        INSIGHT: <3-5 warm empathetic sentences about this specific entry>
        FLAG: FLAGGED or NOT_FLAGGED
        FLAG_REASON: <1-2 clinical sentences if FLAGGED, else None>
        SUGGESTION: <one specific, actionable coping suggestion for today>
    """).strip()


def _trend_prompt(df: pd.DataFrame, summary: dict, patterns: list) -> str:
    recent_rows = "\n".join(
        f"  {r['date'].date()} | Mood {r['mood']} | Stress {r['stress']} "
        f"| Energy {r['energy'] or 'N/A'} | Sleep {r['sleep'] or 'N/A'}h"
        for _, r in df.tail(10).iterrows()
    )
    pattern_lines = (
        "\n".join(f"  [{p.severity.upper()}] {p.pattern_type}: {p.description}" for p in patterns)
        if patterns else "  None detected."
    )
    return textwrap.dedent(f"""
        You are a compassionate mental wellness AI coach reviewing a user's journal trends.

        --- Recent Entries (last 10) ---
{recent_rows}

        --- Summary ---
        Total entries : {summary.get('total_entries')}
        Avg mood      : {summary.get('avg_mood')}/10
        Avg stress    : {summary.get('avg_stress')}/10
        Avg sleep     : {summary.get('avg_sleep')} hrs
        Flagged days  : {summary.get('flagged_days')}
        Mood trend    : {summary.get('mood_trend'):+.2f}/day

        --- Detected Patterns ---
{pattern_lines}

        Provide a rich, warm analysis using markdown formatting:

        ## Trend Summary
        (3-4 sentences on the overall wellness trajectory — be specific and data-grounded)

        ## Key Observations
        (3 bullet points highlighting notable patterns, wins, or concerns)

        ## Encouragement
        (1 personalised motivating message based on this specific data)

        ## Recommended Coping Strategies
        (3 specific, actionable strategies tailored to the patterns detected)
    """).strip()


def _therapist_prompt(df: pd.DataFrame, summary: dict, patterns: list, username: str) -> str:
    data_rows = "\n".join(
        f"  {r['date'].date()} | Mood {r['mood']} | Stress {r['stress']} "
        f"| Energy {r['energy'] or 'N/A'} | Sleep {r['sleep'] or 'N/A'}h | Flagged: {r['ai_flagged']}"
        for _, r in df.iterrows()
    )
    pattern_lines = (
        "\n".join(f"  [{p.severity.upper()}] {p.pattern_type}: {p.description}" for p in patterns)
        if patterns else "  None detected."
    )
    return textwrap.dedent(f"""
        You are a clinical mental health AI assistant preparing a structured wellness report
        for a licensed therapist. Use professional clinical language throughout.

        Patient alias : {username}
        Report period : {summary.get('date_range', ('N/A','N/A'))[0]} to {summary.get('date_range', ('N/A','N/A'))[1]}
        Total entries : {summary.get('total_entries')}

        --- Full Data Log ---
{data_rows}

        --- Detected Patterns ---
{pattern_lines}

        --- Summary Statistics ---
        Avg mood     : {summary.get('avg_mood')}/10
        Avg stress   : {summary.get('avg_stress')}/10
        Avg sleep    : {summary.get('avg_sleep')} hrs
        Mood trend   : {summary.get('mood_trend'):+.2f}/day
        Flagged days : {summary.get('flagged_days')} of {summary.get('total_entries')}

        Provide the following sections using markdown:

        ## Clinical Summary
        ## Data Overview
        ## Identified Concerning Patterns
        ## Risk Assessment
        (State risk level: Low / Moderate / High with brief justification)
        ## Therapeutic Recommendations
        (3-5 specific recommendations for the therapist to explore)
        ## Positive Indicators
        (Strengths, resilience factors, protective behaviours)
    """).strip()


def _chat_prompt(user_message: str, summary: dict) -> str:
    ctx = ""
    if summary:
        ctx = (
            f"\nUser's journal summary: avg mood {summary.get('avg_mood')}/10, "
            f"avg stress {summary.get('avg_stress')}/10, "
            f"avg sleep {summary.get('avg_sleep')}h, "
            f"{summary.get('total_entries')} entries, "
            f"{summary.get('flagged_days')} flagged days."
        )
    return textwrap.dedent(f"""
        You are MindBot, a warm, empathetic AI wellness companion built into MindLog.
        You support users in understanding their mental wellness journal data.
        You are NOT a licensed therapist. Always recommend professional help when appropriate.
        {ctx}

        User: {user_message}

        Reply warmly and helpfully (2-4 paragraphs). Use markdown formatting.
        If the user seems in crisis, strongly encourage them to contact a mental health professional.
    """).strip()


# ── Public API ─────────────────────────────────────────────────────────────────

def analyse_entry(entry: JournalEntry) -> dict:
    prompt = _entry_prompt(entry)
    try:
        text = _generate(prompt)
    except Exception as exc:
        return {"insight": f"AI analysis failed: {exc}", "flagged": False,
                "flag_reason": "", "suggestion": ""}

    if text == "__NO_KEY__":
        return {"insight": "Add your Gemini API key in the sidebar to enable AI analysis.",
                "flagged": False, "flag_reason": "", "suggestion": ""}

    insight = flag_reason = suggestion = ""
    flagged = False
    for line in text.splitlines():
        if line.startswith("INSIGHT:"):
            insight = line[8:].strip()
        elif line.startswith("FLAG:"):
            flagged = "FLAGGED" in line and "NOT_FLAGGED" not in line
        elif line.startswith("FLAG_REASON:"):
            flag_reason = line[12:].strip()
            if flag_reason.lower() == "none":
                flag_reason = ""
        elif line.startswith("SUGGESTION:"):
            suggestion = line[11:].strip()

    if not insight:
        insight = text

    update_ai_fields(entry.id, insight, flagged, flag_reason, suggestion)
    return {"insight": insight, "flagged": flagged,
            "flag_reason": flag_reason, "suggestion": suggestion}


def get_trend_insights(entries: list[JournalEntry]) -> str:
    if not entries:
        return "No entries found. Start journaling to receive AI insights."
    df = entries_to_df(entries)
    summary = compute_summary(df)
    patterns = detect_patterns(df)
    try:
        text = _generate(_trend_prompt(df, summary, patterns))
        return "Add your Gemini API key in the sidebar to enable AI insights." if text == "__NO_KEY__" else text
    except Exception as exc:
        return f"AI analysis failed: {exc}"


def generate_therapist_report(entries: list[JournalEntry], username: str) -> tuple[str, str, str]:
    if not entries:
        return ("No data available.", "", "")
    df = entries_to_df(entries)
    summary = compute_summary(df)
    patterns = detect_patterns(df)
    try:
        report = _generate(_therapist_prompt(df, summary, patterns, username))
        if report == "__NO_KEY__":
            return ("Add your Gemini API key in the sidebar.", "", "")
    except Exception as exc:
        return (f"Report generation failed: {exc}", "", "")

    # Extract sections
    concerning, recommendations = [], []
    in_c = in_r = False
    for line in report.splitlines():
        if "## Identified Concerning" in line:
            in_c, in_r = True, False
        elif "## Therapeutic Recommendations" in line:
            in_c, in_r = False, True
        elif line.startswith("## "):
            in_c = in_r = False
        elif in_c:
            concerning.append(line)
        elif in_r:
            recommendations.append(line)

    if df["date"].notna().any():
        save_therapist_note(
            username=username,
            period_start=df["date"].min().to_pydatetime(),
            period_end=df["date"].max().to_pydatetime(),
            report_text=report,
            concerning_patterns="\n".join(concerning).strip(),
            recommendations="\n".join(recommendations).strip(),
        )
    return report, "\n".join(concerning).strip(), "\n".join(recommendations).strip()


def chat_with_ai(user_message: str, context_entries: list[JournalEntry]) -> str:
    df = entries_to_df(context_entries) if context_entries else pd.DataFrame()
    summary = compute_summary(df) if not df.empty else {}
    try:
        text = _generate(_chat_prompt(user_message, summary))
        return "Add your Gemini API key in the sidebar." if text == "__NO_KEY__" else text
    except Exception as exc:
        return f"Error: {exc}"
