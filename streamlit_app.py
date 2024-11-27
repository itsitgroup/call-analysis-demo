import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Backend URL
# BACKEND_URL = st.secrets["CUSTOM_API"]
BACKEND_URL = os.getenv("BACKEND")

# Initialize session state
if 'transcript' not in st.session_state:
    st.session_state['transcript'] = ''
if 'combined_transcript' not in st.session_state:
    st.session_state['combined_transcript'] = ''
if 'utterances' not in st.session_state:
    st.session_state['utterances'] = []
if 'analysis' not in st.session_state:
    st.session_state['analysis'] = ''

st.title("Call Transcript Analysis")

# File uploader
uploaded_file = st.file_uploader(
    "Upload an audio file (wav, mp3, m4a)",  # Provide a meaningful label
    type=["wav", "mp3", "m4a"]
)

if uploaded_file:
    st.audio(uploaded_file)
    if st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            try:
                files = {"file": uploaded_file}
                response = requests.post(f"{BACKEND_URL}/transcribe", files=files)
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.transcript = response_data["full_transcript"]
                    st.session_state.combined_transcript = response_data["combined_transcript"]
                    st.session_state.utterances = response_data["utterances"]
                    st.success("Transcription completed.")
                else:
                    st.error(response_data.get("error", "An error occurred."))
            except Exception as e:
                st.error(str(e))

if st.session_state.transcript:
    # Display Full Transcript
    st.subheader("Full Transcript")
    st.text_area(
        "Full Transcript Text",  # Provide a meaningful label
        st.session_state.transcript,
        height=150,
        label_visibility="collapsed"
    )

    # Display Diarized Transcript (Speaker Labels)
    st.subheader("Diarized Transcript (Speaker Labels)")
    diarized_text = "\n".join([f"{utterance['speaker']}: {utterance['text']}" for utterance in st.session_state.utterances])
    st.text_area(
        "Diarized Transcript Text",  # Provide a meaningful label
        diarized_text,
        height=150,
        label_visibility="collapsed"
    )

    # Analyze Button
    if st.button("Analyze"):
        with st.spinner("Analyzing..."):
            try:
                data = {
                    "transcript": st.session_state.combined_transcript
                }
                response = requests.post(f"{BACKEND_URL}/analyze", json=data)
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.analysis = response_data["analysis"]
                    st.success("Analysis completed.")
                else:
                    st.error(response_data.get("error", "An error occurred."))
            except Exception as e:
                st.error(str(e))

# Display Analysis Results
if st.session_state.analysis:
    st.subheader("Analysis Results")
    try:
        # Render the analysis as Markdown
        st.markdown(st.session_state.analysis, unsafe_allow_html=True)
    except Exception as e:
        st.error("Unable to render the analysis. Please check the formatting.")