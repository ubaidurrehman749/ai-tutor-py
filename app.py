import io
import streamlit as st
from google import genai
from google.genai import types
import speech_recognition as sr
from gtts import gTTS

PROMPT = """Tum ek friendly tutor ho jo live call par students ko parhate ho.
- Student ki baat dhyan se suno.
- Agar jawab ghalat ho to pyaar se batao, wajah samjhao, phir sahi jawab do.
- Har topic ka asaan jawab do.
- Jawab 2-3 chhote jumlon mein rakho (voice hai).
- Student ki zubaan (Urdu/English) mein jawab do.
- Agar pakka nahi pata to saaf bolo, andaaza mat lagao."""

MODEL = "gemini-3.5-flash"
CODES = {"Urdu": ("ur-PK", "ur"), "English": ("en-US", "en")}

st.title("AI Tutor")
lang = st.selectbox("Zubaan", list(CODES.keys()))

if "history" not in st.session_state:
    st.session_state.history = []
if "last" not in st.session_state:
    st.session_state.last = None
if "play" not in st.session_state:
    st.session_state.play = None

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

audio = st.audio_input("Mic dabao aur bolo")

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
            st.warning("Awaaz samajh nahi aayi, dobara bolo.")
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

for m in reversed(st.session_state.history):
    who = "Aap" if m["role"] == "user" else "Tutor"
    st.write(f"**{who}:** {m['content']}")

if st.session_state.play:
    st.audio(st.session_state.play, format="audio/mp3", autoplay=True)
    st.session_state.play = None
