"""Simple chat-style UI for the drawing reviewer.

Run from the project root:
    streamlit run app.py

Pick a drawing from data/ (or upload a PDF), preview it, press Send, and the
review appears as a chat reply. It calls the same review_drawing() / format_review()
functions as the CLI and the notebook.
"""

import hashlib

import streamlit as st

from src.config import GEMINI_MODEL, OUTPUT_DIR, PROJECT_ROOT
from src.formatter import format_review
from src.pdf_renderer import render_pdf_page
from src.reviewer import list_available_drawings, review_drawing

UPLOAD_DIR = OUTPUT_DIR / "uploads"

st.set_page_config(page_title="Engineering Drawing Review", layout="wide")
st.title("Engineering Drawing Review")
st.caption(f"Model: {GEMINI_MODEL}")

# Chat history lives in the session: a list of {"role", "content", "image"} dicts.
if "messages" not in st.session_state:
    st.session_state.messages = []


def show_message(message: dict) -> None:
    """Render one chat message (optional image, then text)."""
    with st.chat_message(message["role"]):
        if message.get("image"):
            st.image(message["image"], width=400)
        # Plain code block keeps the report's column alignment.
        if message["role"] == "assistant":
            st.code(message["content"], language=None, wrap_lines=True)
        else:
            st.write(message["content"])


# --- Sidebar: choose the drawing and send it ---------------------------------
with st.sidebar:
    st.header("Choose a drawing")
    source = st.radio("Source", ["From data/ folder", "Upload a PDF"], label_visibility="collapsed")

    pdf_path = None
    if source == "From data/ folder":
        drawings = list_available_drawings()
        if drawings:
            pdf_path = st.selectbox(
                "Drawing", drawings, format_func=lambda p: str(p.relative_to(PROJECT_ROOT / "data"))
            )
        else:
            st.warning("No PDFs found in data/easy or data/complex.")
    else:
        uploaded = st.file_uploader("PDF file", type="pdf")
        if uploaded is not None:
            # Hash prefix keeps two different uploads with the same filename from sharing a cached PNG.
            data = uploaded.getvalue()
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            pdf_path = UPLOAD_DIR / f"{hashlib.sha1(data).hexdigest()[:8]}_{uploaded.name}"
            pdf_path.write_bytes(data)

    page = st.number_input("Page (0 = first)", min_value=0, value=0, step=1)

    preview_path = None
    if pdf_path is not None:
        try:
            preview_path = render_pdf_page(pdf_path, int(page))
            st.image(str(preview_path), caption="Preview", width="stretch")
        except (ValueError, FileNotFoundError) as exc:
            st.error(str(exc))

    send = st.button("Send", type="primary", disabled=preview_path is None, width="stretch")
    if st.button("Clear chat", width="stretch"):
        st.session_state.messages = []
        st.rerun()

# --- Handle Send --------------------------------------------------------------
if send:
    st.session_state.messages.append(
        {"role": "user", "content": f"Review: {pdf_path.name} (page {int(page)})", "image": str(preview_path)}
    )
    try:
        with st.spinner(f"Reviewing with {GEMINI_MODEL} ..."):
            report = format_review(review_drawing(pdf_path, page=int(page)))
        st.session_state.messages.append({"role": "assistant", "content": report})
    except RuntimeError as exc:
        # Show the real error (e.g. the API's status and message) in the chat.
        st.session_state.messages.append({"role": "assistant", "content": f"ERROR: {exc}"})

# --- Chat history -------------------------------------------------------------
if not st.session_state.messages:
    st.info("Choose a drawing in the sidebar and press Send.")
for message in st.session_state.messages:
    show_message(message)
