import streamlit as st
from pathlib import Path

st.set_page_config(page_title="mathsPlayz", page_icon="▲", layout="wide")
st.title("▲ mathsPlayz")
st.caption("RAG-powered educational math animation generator")

with st.sidebar:
    n = st.slider("Scenes", 1, 6, 3)
    st.caption("Powered by Manim CE + Ollama")

topic = st.text_area("Math topic", height=100, placeholder="e.g. Pythagorean theorem visualized with squares")

if st.button("Generate", type="primary", use_container_width=True):
    if not topic.strip():
        st.error("Enter a topic.")
    else:
        logs, box = [], st.empty()
        def log(m):
            logs.append(m)
            box.code("\n".join(logs))

        with st.spinner("Running pipeline..."):
            from src.pipeline import run
            path = run(topic.strip(), n_scenes=n, output="output.mp4", log=log)

        if path and Path(path).exists():
            st.success("Done!")
            st.video(path)
            st.download_button("Download MP4", open(path, "rb"), "animation.mp4", "video/mp4")
        else:
            st.error("Pipeline failed. See logs above.")
