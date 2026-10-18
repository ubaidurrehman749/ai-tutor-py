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
[data-testid="stAlert"] { border-radius: 16px; }
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <div class="emoji">🎓</div>
        <h1>AI Tutor</h1>
        <p>Mic dabao, sawal poochho, aur seekho</p>
    </div>
    """,
    unsafe_allow_html=True,
)

for k, v in {"history": [], "last": None, "play": None}.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_chat():
    st.session_state.history = []
    st.session_state.play = None


client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

st.markdown('<div class="label">🌐 Zubaan</div>', unsafe_allow_html=True)
lang = st.radio("Zubaan", list(CODES.keys()), horizontal=True,
                label_visibility="collapsed")

st.markdown('<div class="label">🎤 Apna sawal bolo</div>', unsafe_allow_html=True)
audio = st.audio_input("Mic", label_visibility="collapsed")

if audio is not None:
    data = audio.getvalue()
    key = hash(data)
    if key != st.session_state.last:
        st.session_state.last = key
        rec = sr.Recognizer()
        try:
            with sr.AudioFile(io.BytesIO(data)) as src:
                clip = rec.record(src)
            text = rec.recognize_google(clip, language=CODES[lang][0])
        except Exception:
            text = None

        if not text:
            st.warning("Awaaz samajh nahi aayi, dobara saaf bolo.")
        else:
            st.session_state.history.append({"role": "user", "content": text})
            contents = [
                types.Content(
                    role="user" if m["role"] == "user" else "model",
                    parts=[types.Part(text=m["content"])],
                )
                for m in st.session_state.history[-20:]
            ]
            try:
                with st.spinner("Tutor soch raha hai..."):
                    resp = client.models.generate_content(
                        model=MODEL,
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=PROMPT,
                        ),
                    )
                    reply = resp.text or "Maaf kijiye, dobara poochiye."
                    st.session_state.history.append(
                        {"role": "assistant", "content": reply}
                    )
                    buf = io.BytesIO()
                    gTTS(reply, lang=CODES[lang][1]).write_to_fp(buf)
                    st.session_state.play = buf.getvalue()
            except Exception as e:
                st.session_state.history.pop()
                st.error("Gemini error: " + str(e)[:300])

if st.session_state.play:
    st.audio(st.session_state.play, format="audio/mp3", autoplay=True)
    st.session_state.play = None

if not st.session_state.history:
    st.markdown(
        """
        <div class="empty">
            <div class="big">👋</div>
            <b>Assalam o Alaikum!</b><br>
            Upar mic dabao aur apna pehla sawal poochho.
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown('<div class="label">💬 Baat cheet</div>', unsafe_allow_html=True)
    for m in reversed(st.session_state.history):
        safe = html.escape(m["content"]).replace("\n", "<br>")
        if m["role"] == "user":
            st.markdown(
                f'<div class="chat-row me"><div class="bubble me" dir="auto">'
                f'<div class="who">Aap</div>{safe}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-row bot"><div class="bubble bot" dir="auto">'
                f'<div class="who">🎓 Tutor</div>{safe}</div></div>',
                unsafe_allow_html=True,
            )
    st.write("")
    st.button("🗑️ Nayi baat shuru karo", on_click=reset_chat)
