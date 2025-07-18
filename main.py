import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import av
import queue
import wave
import io
import speech_recognition as sr
import os

# Setup audio queue for mic input
audio_queue = queue.Queue()

# Streamlit WebRTC audio processor
class AudioProcessor:
    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray().tobytes()
        audio_queue.put(audio)
        return frame

# Convert raw mic audio to WAV stream
def get_wav_audio(audio_bytes, sample_rate=48000, sample_width=2, channels=1):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_bytes)
    buffer.seek(0)
    return buffer

# Transcribe mic input using Google Speech Recognition
def transcribe(language):
    recognizer = sr.Recognizer()
    audio_bytes = b"".join(list(audio_queue.queue))
    audio_queue.queue.clear()

    if not audio_bytes:
        return ""

    wav_buffer = get_wav_audio(audio_bytes)

    with sr.AudioFile(wav_buffer) as source:
        audio = recognizer.record(source)

    try:
        return recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError as e:
        return f"API error: {e}"

# Load chatbot knowledge base
def load_paragraphs(file_path="daily_advice.txt"):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [p.strip() for p in text.split('\n\n') if p.strip()]

# Simple keyword-matching chatbot
def find_best_paragraph(query, paragraphs):
    query_words = set(query.lower().split())
    best_score = 0
    best_para = "Sorry, I don't know how to answer that yet."
    for para in paragraphs:
        para_words = set(para.lower().split())
        score = len(query_words & para_words)
        if score > best_score:
            best_score = score
            best_para = para
    return best_para

# Streamlit app UI
def main():
    st.set_page_config(page_title="Voice Chatbot", layout="centered")
    st.title("🤖 Speak And Ask The Chatbot")

    paragraphs = load_paragraphs()

    language = st.selectbox("Choose Speech Language", ["en-US", "fr-FR"])

    # Start mic streaming
    webrtc_streamer(
        key="chatbot-mic",
        mode=WebRtcMode.SENDONLY,
        audio_processor_factory=AudioProcessor,
        media_stream_constraints={"video": False, "audio": True},
    )

    st.markdown("### 🎙️ Voice Input")
    if st.button("Transcribe and Ask"):
        query = transcribe(language)
        st.write("🗣️ You said:", query)
        if query:
            response = find_best_paragraph(query, paragraphs)
            st.write("🤖 Chatbot:", response)

    st.markdown("---")
    st.markdown("### 💬 Text Input")
    text_input = st.text_input("Type your question here:")
    if st.button("Submit Text"):
        if text_input.strip():
            response = find_best_paragraph(text_input, paragraphs)
            st.write("🤖 Chatbot:", response)
        else:
            st.warning("Please enter a question.")

if __name__ == "__main__":
    main()