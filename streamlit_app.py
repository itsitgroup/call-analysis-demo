import streamlit as st
import requests
import analytics
import uuid

# Segment analytics configuration
WRITE_KEY = st.secrets['SECRET_KEY']
analytics.write_key = WRITE_KEY

# Backend URL
BACKEND_URL = st.secrets['BACKEND']

# Initialize session state
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ''
if 'transcript' not in st.session_state:
    st.session_state['transcript'] = ''
if 'combined_transcript' not in st.session_state:
    st.session_state['combined_transcript'] = ''
if 'utterances' not in st.session_state:
    st.session_state['utterances'] = []
if 'analysis' not in st.session_state:
    st.session_state['analysis'] = ''
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

    if st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            try:
                # Track transcription request
                track_event("Transcription Started", {"file_name": uploaded_file.name, "user_id": st.session_state['user_id']})
                
                files = {"file": uploaded_file}
                response = requests.post(f"{BACKEND_URL}/transcribe", files=files, headers=get_headers())
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.transcript = response_data["full_transcript"]
                    st.session_state.combined_transcript = response_data["combined_transcript"]
                    st.session_state.utterances = response_data["utterances"]
                    st.success("Transcription completed.")
                    
                    # Track transcription success
                    track_event("Transcription Completed", {"file_name": uploaded_file.name, "user_id": st.session_state['user_id']})
                else:
                    error_message = response_data.get("error", "An error occurred.")
                    st.error(error_message)
                    # Track transcription failure
                    track_event("Transcription Failed", {"error": error_message, "user_id": st.session_state['user_id']})
            except Exception as e:
                st.error(str(e))
                # Track transcription exception
                track_event("Transcription Exception", {"error": str(e), "user_id": st.session_state['user_id']})

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
                # Track analysis request
                track_event("Analysis Started", {"transcript_length": len(st.session_state.combined_transcript), "user_id": st.session_state['user_id']})

                data = {
                    "transcript": st.session_state.combined_transcript
                }
                response = requests.post(f"{BACKEND_URL}/analyze", json=data)
                response_data = response.json()
                if response.status_code == 200:
                    st.session_state.analysis = response_data["analysis"]
                    st.success("Analysis completed.")
                    
                    # Track analysis success
                    track_event("Analysis Completed", {"transcript_length": len(st.session_state.combined_transcript), "user_id": st.session_state['user_id']})
                else:
                    error_message = response_data.get("error", "An error occurred.")
                    st.error(error_message)
                    # Track analysis failure
                    track_event("Analysis Failed", {"error": error_message, "user_id": st.session_state['user_id']})
            except Exception as e:
                st.error(str(e))

    # Display Analysis Results
    if st.session_state.analysis:
        st.subheader("Analysis Results")
        st.markdown(st.session_state.analysis, unsafe_allow_html=True)
    except Exception as e:
        st.error("Unable to render the analysis. Please check the formatting.")