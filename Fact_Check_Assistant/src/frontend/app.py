import logging
import sys
from pathlib import Path

import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

try:
    # Import fact_check_supervisor directly
    from fact_check_supervisor import fact_check_supervisor

    logger.info("Successfully imported fact_check_supervisor")
except Exception as e:
    logger.error(f"Failed to import fact_check_supervisor: {e}")
    st.error(f"Application startup error: {e}")
    st.stop()

# Configure Streamlit page
st.set_page_config(
    page_title="Fact Check Assistant",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "👋 Welcome to the Fake News Agent! \n\nI can help you analyse for potential misinformation and fact-check claims.\n\n📹 Video captions are ready for analysis.\n\n🤔 Do you want to check the captions for misinformation?\n\nJust click the button below or ask me to analyse the video content!",
        }
    ]

if "session_id" not in st.session_state:
    st.session_state.session_id = "streamlit-session"

if "captions_content" not in st.session_state:
    st.session_state.captions_content = ""

if "captions_loaded" not in st.session_state:
    st.session_state.captions_loaded = False

# Configuration
ASSETS_DIR = Path(__file__).parent / "assets"


def load_captions():
    """Load captions from the VTT file"""
    try:
        caption_file = ASSETS_DIR / "caption.vtt"
        if caption_file.exists():
            with open(caption_file, "r", encoding="utf-8") as f:
                content = f.read()
                st.session_state.captions_content = content
                st.session_state.captions_loaded = True
                return True
    except Exception as e:
        st.error(f"Error loading captions: {e}")
    return False


def is_asking_about_captions(message):
    """Check if user is asking about captions/video content"""
    caption_keywords = [
        "caption",
        "captions",
        "video",
        "transcript",
        "analyze video",
        "check video",
        "video content",
        "what does the video say",
        "analyze captions",
        "check captions",
        "video analysis",
        "check the captions",
        "misinformation",
        "fact check",
        "analyze",
        "suspicious claims",
    ]
    return any(keyword.lower() in message.lower() for keyword in caption_keywords)


def send_message_to_supervisor(message):
    """Send message to fact_check_supervisor"""
    try:
        # Include captions if analyzing video content
        message_to_send = message
        if is_asking_about_captions(message) and st.session_state.captions_loaded:
            message_to_send = f"{message}\n\n[CAPTIONS TO ANALYZE]:\n{st.session_state.captions_content}"

        # Call the supervisor directly
        response = fact_check_supervisor(message_to_send)
        return response, st.session_state.session_id
    except Exception as e:
        logging.error(f"Error using fact_check_supervisor: {str(e)}")
        return f"Error: {str(e)}", None


def send_predefined_message(message):
    """Send a predefined message"""
    st.session_state.messages.append({"role": "user", "content": message})

    with st.spinner("Analyzing..."):
        response, new_session_id = send_message_to_supervisor(message)

    if new_session_id:
        st.session_state.session_id = new_session_id

    # Extract message content from response
    if (
        hasattr(response, "message")
        and response.message
        and "content" in response.message
    ):
        response_text = response.message["content"][0]["text"]
    else:
        response_text = str(response)

    st.session_state.messages.append({"role": "assistant", "content": response_text})
    st.rerun()


# Load captions on startup
if not st.session_state.captions_loaded:
    load_captions()

# Main UI
st.title("🕵️ Fact Check Assistant")

# Create two columns for layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📹 Video Content")

    # Video player
    video_file = ASSETS_DIR / "video.mp4"
    if video_file.exists():
        st.video(str(video_file))
    else:
        st.error("Video file not found")

    # Captions display
    st.subheader("📝 Captions")
    if st.session_state.captions_loaded:
        with st.expander("View Captions", expanded=False):
            st.text_area(
                "Caption Content",
                value=st.session_state.captions_content,
                height=200,
                disabled=True,
                label_visibility="collapsed",
            )
    else:
        st.warning("⚠️ Captions not loaded")

with col2:
    st.subheader("💬 Chat Interface")

    # Quick action button
    if st.session_state.captions_loaded:
        if st.button(
            "✅ Fact Check Video Content", type="primary", use_container_width=True
        ):
            send_predefined_message("Fact check this video content")

    # Chat messages container
    chat_container = st.container(height=400)

    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])

    # Chat input
    if prompt := st.chat_input(
        "Ask me to analyze the video captions...",
        disabled=not st.session_state.captions_loaded,
    ):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Display user message
        with chat_container:
            with st.chat_message("user"):
                st.write(prompt)

        # Get assistant response
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response, new_session_id = send_message_to_supervisor(prompt)

                if new_session_id:
                    st.session_state.session_id = new_session_id

                # Extract message content from response
                if (
                    hasattr(response, "message")
                    and response.message
                    and "content" in response.message
                ):
                    response_text = response.message["content"][0]["text"]
                else:
                    response_text = str(response)

                st.write(response_text)

        # Add assistant message to history
        st.session_state.messages.append(
            {"role": "assistant", "content": response_text}
        )

# Footer
st.markdown("---")
st.markdown("**Fact Check Assistant** - Powered by Streamlit")
