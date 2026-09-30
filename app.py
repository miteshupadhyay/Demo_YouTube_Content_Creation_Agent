import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from tavily import TavilyClient
import time
from google.genai import types
from moviepy import VideoFileClip

load_dotenv()

# Configure API keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is missing from the .env file.")
    st.stop()

if not TAVILY_API_KEY:
    st.error("TAVILY_API_KEY is missing from the .env file.")
    st.stop()

# Initialize Gemini and Tavily clients
geni_client = genai.Client(api_key=GEMINI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

# Select models
MODEL_INFO = "gemini-3.8-flash"
MODEL_SCRIPT = "gemini-3.8-flash"


# Streamlit configuration
st.set_page_config(
    page_title="StoryForge Agent",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="collapsed"
)


# Custom modern CSS theme
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(
                135deg, #0f2027, #203a43, #2c5364
            );
            color: #f5f5f5;
        }

        h1, h2, h3 {
            text-align: center;
            color: #F9FAFB !important;
        }

        .stTextInput>div>div>input {
            border: 1px solid #6EE7B7 !important;
            border-radius: 10px;
            padding: 12px;
            background-color: #111827;
            color: white !important;
        }

        div.stButton > button {
            background: linear-gradient(
                90deg, #06b6d4, #3b82f6
            );
            color: white;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            border: none;
            transition: 0.3s ease-in-out;
        }

        div.stButton > button:hover {
            transform: scale(1.05);
            background: linear-gradient(
                90deg, #2563eb, #06b6d4
            );
        }

        .card {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-top: 20px;
        }

        .stRadio > div {
            justify-content: center;
        }

        footer, .stCaption {
            text-align: center;
            color: #9CA3AF;
        }
    </style>
""", unsafe_allow_html=True)


# Generate real-time information
def get_realtime_info(query):
    try:
        response = tavily_client.search(
            query=query,
            max_results=3,
            topic="general"
        )

        results = response.get("results", [])

        if not results:
            return None

        summaries = []

        for res in results:
            title = res.get("title", "Untitled")
            content = res.get("content", "")
            url = res.get("url", "")

            if content:
                summaries.append(
                    f"Title: {title}\n\n"
                    f"Content: {content}\n\n"
                    f"Source: {url}"
                )

        if not summaries:
            return None

        source_info = "\n\n---\n\n".join(summaries)

    except Exception as e:
        st.error(f"Error while fetching information: {e}")
        return None

    # Summarize information using Gemini
    prompt = f"""
    You are a professional researcher and content creator
    with expertise in multiple fields.

    Using the following real-time information, write an
    accurate, engaging, and human-like summary for the topic:
    "{query}"

    Requirements:
    - Keep it factual, insightful, and concise (around 200 words).
    - Maintain a smooth, natural tone.
    - Highlight key takeaways or trends.
    - Avoid greetings or self-references.
    - Do not invent facts.
    - Clearly distinguish reported facts from speculation.

    Source Information:
    {source_info}

    Output only the refined, human-readable content.
    """

    try:
        response = geni_client.models.generate_content(
            model=MODEL_INFO,
            contents=prompt
        )

        if response and response.text:
            return response.text.strip()

        return None

    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None


# Generate a video script
def generate_video_script(information_text):
    prompt = f"""
    You are a creative script writer.

    Turn this real-time information into an engaging video script
    for YouTube Shorts or Instagram Reels.

    Requirements:
    - Use a conversational tone.
    - Start with a strong hook.
    - Make the script engaging.
    - Include a clear call to action at the end.
    - Keep it between 100 and 200 words.
    - Use only information supported by the provided content.
    - Do not invent facts.

    Information:
    {information_text}
    """

    try:
        response = geni_client.models.generate_content(
            model=MODEL_SCRIPT,
            contents=prompt
        )

        if response and response.text:
            return response.text.strip()

        return None

    except Exception as e:
        st.error(f"Error generating video script: {e}")
        return None

def generate_video_from_script(script):
    """
    Generate a 6-second video using Google Veo 3.1
    and trim it to 5 seconds.
    """

    prompt = f"""
    Create a cinematic, visually engaging vertical video
    for YouTube Shorts and Instagram Reels.

    Use the following video script as the basis for the visuals.

    Video script:
    {script}

    Requirements:
    - Portrait format (9:16).
    - Duration: 6 seconds.
    - Resolution: 720p.
    - Cinematic camera movements.
    - Realistic and high-quality visuals.
    - Smooth transitions between scenes.
    - Visually represent the main idea of the script.
    - No subtitles or text overlays.
    - Create engaging visuals suitable for social media.
    """

    try:
        # Start video generation
        operation = geni_client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            config=types.GenerateVideosConfig(
                duration_seconds=6,
                aspect_ratio="9:16",
                resolution="720p",
                number_of_videos=1
            )
        )

        # Poll until video generation is complete
        progress = st.empty()

        while not operation.done:
            progress.info("🎬 Generating your AI video... Please wait.")
            time.sleep(10)
            operation = geni_client.operations.get(operation)

        progress.empty()

        # Check the response
        if not operation.response or not operation.response.generated_videos:
            raise RuntimeError("Veo did not return a generated video.")

        generated_video = operation.response.generated_videos[0]

        # Download the generated video
        raw_video_path = "generated_video_raw.mp4"
        final_video_path = "generated_video.mp4"

        geni_client.files.download(
            file=generated_video.video,
            destination=raw_video_path
        )

        # Trim the 6-second video to 5 seconds
        with VideoFileClip(raw_video_path) as video:
            trimmed_video = video.subclipped(0, 5)

            trimmed_video.write_videofile(
                final_video_path,
                codec="libx264",
                audio_codec="aac",
                logger=None
            )

            trimmed_video.close()

        return final_video_path

    except Exception as e:
        st.error(f"Error generating video: {e}")
        return None

    
# Main Streamlit application
def main():

    st.markdown(
        "<h1>🌐 StoryForge Agent</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align:center; color:#D1D5DB;'>
        Search any topic — from world news to research trends —
        and get AI-powered insights, video scripts, and AI-generated
        videos instantly 🚀
        </p>
        """,
        unsafe_allow_html=True
    )

    query = st.text_input(
        "🔎 Enter your topic or question:",
        key="search_query"
    )

    if query.strip():

        # Fetch real-time information only when the query changes
        if st.session_state.get("last_query") != query.strip():
            st.session_state.last_query = query.strip()
            st.session_state.info_result = None
            st.session_state.video_script = None
            st.session_state.generated_video = None

        if st.session_state.get("info_result") is None:

            with st.spinner("🌐 Gathering latest information..."):
                st.session_state.info_result = get_realtime_info(
                    query.strip()
                )

        info_result = st.session_state.info_result

        if info_result:

            # Display AI-generated summary
            st.markdown(
                "<div class='card'>",
                unsafe_allow_html=True
            )

            st.subheader("📰 AI-Generated Summary")
            st.write(info_result)

            st.markdown(
                "</div>",
                unsafe_allow_html=True
            )

            # Video script selection
            generate_script = st.radio(
                "🎬 Generate a short video script?",
                ("No", "Yes"),
                index=0,
                horizontal=True,
                key="generate_script"
            )

            if generate_script == "Yes":

                # Generate video script only once per summary
                if st.session_state.get("video_script") is None:

                    with st.spinner("🎬 Crafting your video script..."):
                        st.session_state.video_script = (
                            generate_video_script(info_result)
                        )

                script = st.session_state.video_script

                if script:

                    # Display video script
                    st.markdown(
                        "<div class='card'>",
                        unsafe_allow_html=True
                    )

                    st.subheader("🎬 AI-Generated Video Script")
                    st.write(script)

                    st.download_button(
                        label="📥 Download Script",
                        data=script,
                        file_name="video_script.txt",
                        mime="text/plain",
                        key="download_script"
                    )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True
                    )

                    # Video generation section
                    st.markdown(
                        "<div class='card'>",
                        unsafe_allow_html=True
                    )

                    st.subheader("🎥 AI Video Generation")

                    st.write(
                        "Generate a 5-second AI video based "
                        "on your video script using Google Veo."
                    )

                    if st.button(
                        "🎬 Generate 5-Second AI Video",
                        key="generate_video"
                    ):

                        with st.spinner(
                            "🎥 Generating your AI video... "
                            "This may take a few minutes."
                        ):
                            video_path = generate_video_from_script(
                                script
                            )

                        if video_path:
                            st.session_state.generated_video = video_path
                            st.success(
                                "✅ Your AI video has been generated!"
                            )
                        else:
                            st.error(
                                "❌ Video generation failed. "
                                "Please try again."
                            )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True
                    )

                    # Display generated video
                    video_path = st.session_state.get(
                        "generated_video"
                    )

                    if video_path and os.path.exists(video_path):

                        st.markdown(
                            "<div class='card'>",
                            unsafe_allow_html=True
                        )

                        st.subheader("🎞️ Your AI-Generated Video")

                        st.video(video_path)

                        with open(video_path, "rb") as video_file:
                            st.download_button(
                                label="📥 Download AI Video",
                                data=video_file.read(),
                                file_name="storyforge_video.mp4",
                                mime="video/mp4",
                                key="download_video"
                            )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True
                        )

                else:
                    st.error(
                        "⚠️ Could not generate video script. "
                        "Please try again."
                    )

        else:
            st.warning(
                "⚠️ No valid information found. "
                "Please try another query."
            )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Made with 💖")


if __name__ == "__main__":
    main()