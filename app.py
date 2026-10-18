import io
import html
import streamlit as st
from google import genai
from google.genai import types
import speech_recognition as sr
from gtts import gTTS

st.set_page_config(page_title="AI Tutor", page_icon="🎓", layout="centered")

PROMPT = """Tum ek friendly tutor ho jo live call par students ko parhate ho.
- Student ki baat dhyan se suno.
- Agar jawab ghalat ho to pyaar se batao, wajah samjhao, phir sahi jawab do.
- Har topic ka asaan jawab do.
- Jawab 2-3 chhote jumlon mein rakho (voice hai).
- Student ki zubaan (Urdu/English) mein jawab do.
- Agar pakka nahi pata to saaf bolo, andaaza mat lagao."""

MODEL = "gemini-3.5-flash"
CODES = {"Urdu": ("ur-PK", "ur"), "English": ("en-US", "en")}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, .stApp, p, label, span, div, button, select {
    font-family: 'Poppins', sans-serif;
}
.stApp {
    background: linear-gradient(160deg, #eef2ff 0%, #fdf2f8 50%, #ecfeff 100%);
    color: #1f2937;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container {
    max-width: 560px;
    padding-top: 1.2rem;
    padding-bottom: 3rem;
}

/* Header card */
.hero {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 55%, #ec4899 100%);
    border-radius: 24px;
    padding: 26px 22px;
    text-align: center;
    color: #ffffff;
    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.35);
    margin-bottom: 18px;
}
.hero .emoji { font-size: 2.6rem; line-height: 1; }
.hero h1 {
    color: #ffffff !important;
    font-size: 1.8rem;
    font-weight: 700;
    margin: 8px 0 2px 0;
    padding: 0;
}
.hero p {
    color: #f5f3ff !important;
    font-size: 0.92rem;
    margin: 0;
}

/* Card sections */
.label {
    font-weight: 600;
    color: #374151;
    font-size: 0.9rem;
    margin: 14px 0 6px 2px;
}

/* Language radio */
div[role="radiogroup"] { gap: 8px; }
div[role="radiogroup"] label {
    background: #ffffff;
    padding: 6px 16px;
    border-radius: 999px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
div[role="radiogroup"] label p { color: #1f2937 !important; font-weight: 500; }

/* Mic box */
[data-testid="stAudioInput"] {
    background: #ffffff;
    border-radius: 22px;
    padding: 6px;
    box-shadow: 0 8px 22px rgba(99, 102, 241, 0.15);
}

/* Chat bubbles */
.chat-row { display: flex; margin: 10px 0; }
.chat-row.me { justify-content: flex-end; }
.chat-row.bot { justify-content: flex-start; }
.bubble {
    max-width: 86%;
    padding: 12px 16px;
    border-radius: 18px;
    line-height: 1.65;
    font-size: 0.98rem;
    word-wrap: break-word;
}
.bubble.me {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #ffffff;
    border-bottom-right-radius: 4px;
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.3);
}
.bubble.bot {
    background: #ffffff;
    color: #1f2937;
    border-bottom-left-radius: 4px;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
}
.who {
    font-size: 0.7rem;
    font-weight: 600;
    opacity: 0.75;
    margin-bottom: 3px;
}

/* Empty state */
.empty {
    background: rgba(255,255,255,0.7);
    border: 2px dashed #c7d2fe;
    border-radius: 20px;
    padding: 26px 16px;
    text-align: center;
    color: #4b5563;
    margin-top: 18px;
}
.empty .big { font-size: 2rem; }

/* Button */
.stButton > button {
    width: 100%;
    border-radius: 999px;
    border: 0;
    background: #ffffff;
    color: #6366f1;
    font-weight: 600;
    padding: 10px 0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.stButton > button:hover { color: #ec4899; border: 0; }

/* Error / warning boxes */
[data-testid="stAlert"] {
