import streamlit as st
import requests
import os
from dotenv import load_dotenv
import asyncio
from typing import AsyncGenerator

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎬",
    layout="wide",
)

st.markdown(
    """
    <style>
        body {
            color: #ffffff;
            background-color: #1a1a1a;
        }
        .stButton>button {
            color: #ffffff;
            background-color: #ff7f00;
            border-color: #ff7f00;
        }
        .stTextInput>div>div>input {
            color: #ffffff;
            background-color: #333333;
            border-color: #555555;
        }
        .stExpander>details>summary {
            color: #ffffff;
        }
        .stExpander>details>div {
            color: #ffffff;
            background-color: #333333;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🎬 YouTube Summarizer")

video_url = st.text_input("Enter YouTube Video URL:")

if video_url:
    col1, col2 = st.columns(2)
    with col1:
        if "video_info" not in st.session_state or st.session_state.get("video_url") != video_url:
            # Clear summary if video URL changes
            st.session_state.pop("summary", None)
            try:
                response = requests.post(f"{API_URL}/api/video-info", json={"url": video_url})
                response.raise_for_status()
                video_info = response.json()
                st.session_state["video_info"] = video_info
                st.session_state["video_url"] = video_url
            except requests.exceptions.RequestException as e:
                st.error(f"Error fetching video info: {e}")
        
        if "video_info" in st.session_state and st.session_state.get("video_url") == video_url:
            st.subheader("Video Information")
            st.image(st.session_state["video_info"]["thumbnail"], width=300)
            st.write(f"**Title:** {st.session_state['video_info']['title']}")

    with col2:
        if "summary" not in st.session_state:
            # Summary placeholder for typing effect
            summary_placeholder = st.empty()
            if st.button("Summarize Video"):
                try:
                    response = requests.post(f"{API_URL}/api/summarize", json={"url": video_url})
                    response.raise_for_status()
                    summary = response.json()["summary"]

                    async def type_summary(text: str) -> AsyncGenerator[str, None]:
                        step_size = 5  # Number of characters added at once
                        for i in range(step_size, len(text) + 1, step_size):
                            yield text[:i]
                            await asyncio.sleep(0.005)  # Reduced delay for faster typing
                    
                    async def display_summary():
                        summary_placeholder.empty()  # Clear previous content
                        typing_text = ""
                        async for partial_summary in type_summary(summary):
                            typing_text = partial_summary
                            summary_placeholder.markdown(typing_text)
                        # Store the complete summary in session_state
                        st.session_state["summary"] = typing_text
                    
                    asyncio.run(display_summary())
                except requests.exceptions.RequestException as e:
                    st.error(f"Error summarizing video: {e}")
        else:
            # Display the stored summary without typing effect
            st.subheader("Video Summary")
            st.markdown(st.session_state["summary"])

    # Ask a question section
    if "summary" in st.session_state:
        question = st.text_input("Ask a question about the summary:")
        if question:
            try:
                response = requests.post(f"{API_URL}/api/answer", json={"summary": st.session_state["summary"], "question": question})
                response.raise_for_status()
                answer = response.json()["answer"]
                st.write(f"**Answer:** {answer}")
            except requests.exceptions.RequestException as e:
                st.error(f"Error answering question: {e}")