import streamlit as st
import requests
import os
import analytics
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Segment analytics configuration
WRITE_KEY = os.getenv('WRITE_KEY')
analytics.write_key = WRITE_KEY

# Backend URL
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
if 'embeddings_ready' not in st.session_state:
    st.session_state['embeddings_ready'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())  # Generate a unique user ID

st.title("Call Transcript Analysis")

# Function to track events with Segment
def track_event(event_name, properties=None):
    try:
        analytics.track(user_id=st.session_state['user_id'], event=event_name, properties=properties)
    except Exception as e:
        print(f"Analytics tracking failed: {e}")

# File uploader
uploaded_file = st.file_uploader(
    "Upload an audio file (wav, mp3, m4a)",  # Provide a meaningful label
    type=["wav", "mp3", "m4a"]
)

if uploaded_file:
    st.audio(uploaded_file)
    # Track file upload event
    track_event("File Uploaded", {"file_name": uploaded_file.name, "file_type": uploaded_file.type, "user_id": st.session_state['user_id']})

    if st.button("Transcribe", key="transcribe"):
        with st.spinner("Transcribing..."):
            try:
                files = {"file": uploaded_file}
                response = requests.post(f"{BACKEND_URL}/transcribe", files=files)
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.transcript = response_data["full_transcript"]
                    st.session_state.combined_transcript = response_data["combined_transcript"]
                    st.session_state.utterances = response_data["utterances"]
                    st.session_state['user_id'] = response_data["user_id"]
                    st.success("Transcription completed successfully.")
                    track_event("Transcription Completed", {"user_id": st.session_state['user_id']})
                else:
                    st.error(response_data.get("error", "An error occurred."))
                    track_event("Transcription Failed", {"error": response_data.get("error", "Unknown error")})
            except Exception as e:
                st.error(f"Error: {e}")
                track_event("Transcription Exception", {"error": str(e)})

if st.session_state.transcript:
    st.subheader("Full Transcript")
    st.text_area(
        "Full Transcript Text",
        st.session_state.transcript,
        height=150,
        label_visibility="collapsed"
    )

    st.subheader("Diarized Transcript (Speaker Labels)")
    diarized_text = "\n".join([f"{utterance['speaker']}: {utterance['text']}" for utterance in st.session_state.utterances])
    st.text_area(
        "Diarized Transcript Text",
        diarized_text,
        height=150,
        label_visibility="collapsed"
    )

    # Analyze Button
    if st.button("Analyze", key="analyze"):
        with st.spinner("Analyzing the call..."):
            try:
                headers = {"User-Session-ID": st.session_state['user_id']}
                data = {"transcript": st.session_state.combined_transcript}
                response = requests.post(f"{BACKEND_URL}/analyze", json=data, headers=headers)
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.analysis = response_data["analysis"]
                    st.success("Analysis completed successfully.")
                    track_event("Analysis Completed", {"user_id": st.session_state['user_id']})
                else:
                    error_message = response_data.get("error", "An error occurred.")
                    st.error(error_message)
                    track_event("Analysis Failed", {"error": error_message, "user_id": st.session_state['user_id']})
            except Exception as e:
                st.error(f"Error: {e}")
                track_event("Analysis Exception", {"error": str(e)})

    # Display Analysis Results
    if st.session_state.analysis:
        st.subheader("Analysis Results")
        st.markdown(st.session_state.analysis, unsafe_allow_html=True)

    if not st.session_state.embeddings_ready:
        if st.button("Start AI Chat", key="start_chat"):
            with st.spinner("Creating embeddings..."):
                if not st.session_state['utterances']:
                    st.error("No utterances available for creating embeddings.")
                else:
                    try:
                        headers = {"User-Session-ID": st.session_state['user_id']}
                        response = requests.post(
                            f"{BACKEND_URL}/create_embeddings",
                            json={"utterances": st.session_state['utterances']},
                            headers=headers
                        )
                        if response.status_code == 200:
                            st.success("Embeddings created successfully. You can now chat with the AI!")
                            st.session_state.embeddings_ready = True
                            track_event("Embeddings Created", {"user_id": st.session_state['user_id']})
                        else:
                            st.error(response.json().get("error", "An error occurred."))
                            track_event("Embeddings Creation Failed", {"error": response.json().get("error")})
                    except Exception as e:
                        st.error(f"Error: {e}")
                        track_event("Embeddings Creation Exception", {"error": str(e)})
    else:
        st.subheader("Chat About the Call")
        user_query = st.text_input("Ask a question about the call:")
        if st.button("Ask", key="ask_query"):
            if user_query.strip():
                with st.spinner("Generating response..."):
                    try:
                        headers = {"User-Session-ID": st.session_state['user_id']}
                        response = requests.post(f"{BACKEND_URL}/ask", json={"query": user_query}, headers=headers)
                        if response.status_code == 200:
                            st.text_area("Response", response.json()["response"], height=150)
                            track_event("Query Success", {"query": user_query, "user_id": st.session_state['user_id']})
                        else:
                            st.error(response.json().get("error", "An error occurred."))
                            track_event("Query Failed", {"error": response.json().get("error")})
                    except Exception as e:
                        st.error(f"Error: {e}")
                        track_event("Query Exception", {"error": str(e)})
            else:
                st.error("Please enter a question before clicking 'Ask'.")