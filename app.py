import os
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from src.documents import extract_text, make_chunks, retrieve
from src.models import answer_with_gemini, answer_with_ollama

load_dotenv()
st.set_page_config(page_title="StudyMate", page_icon="📚", layout="wide")

st.markdown("""
<style>
.main {max-width: 1150px;}
[data-testid="stSidebar"] {background: #f4f7fb;}
.hero {padding: 1.4rem 1.6rem; border-radius: 18px; background: linear-gradient(120deg,#e9f2ff,#effaf5); margin-bottom: 1rem;}
.hero h1 {margin: 0; color: #17365d;}
.hero p {margin: .4rem 0 0; color: #50647d;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>📚 StudyMate</h1><p>Your personal AI study assistant. Learn from your notes, plan your week, and check your understanding.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Settings")
    provider = st.selectbox("AI provider", ["Ollama (local)", "Gemini (cloud)"])
    if provider.startswith("Ollama"):
        model_name = st.text_input("Ollama model", os.getenv("OLLAMA_MODEL", "llama3.2"))
        base_url = st.text_input("Ollama URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    else:
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        base_url = ""
    st.caption("Local mode keeps model requests on your machine. Gemini sends prompts to Google's API.")
    st.divider()
    uploads = st.file_uploader("Add your study notes", type=["pdf", "txt", "md"], accept_multiple_files=True)

if "chunks" not in st.session_state:
    st.session_state.chunks = []
    st.session_state.doc_names = []
if uploads:
    try:
        all_chunks, names = [], []
        for file in uploads:
            text = extract_text(file.name, file.getvalue())
            all_chunks.extend(make_chunks(text, source=file.name))
            names.append(file.name)
        st.session_state.chunks, st.session_state.doc_names = all_chunks, names
        st.sidebar.success(f"Loaded {len(names)} file(s)")
    except Exception as exc:
        st.sidebar.error(f"Could not read a file: {exc}")

chat_tab, plan_tab, quiz_tab = st.tabs(["💬 Ask your notes", "🗓️ Study planner", "✍️ Practice quiz"])

with chat_tab:
    st.subheader("Ask anything about your studies")
    if st.session_state.doc_names:
        st.caption("Using: " + ", ".join(st.session_state.doc_names))
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    prompt = st.chat_input("Explain a concept, summarize a topic, or ask about your notes…")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        context = retrieve(prompt, st.session_state.chunks) if st.session_state.chunks else ""
        system = "You are StudyMate, a supportive and accurate personal study assistant. Explain ideas clearly, use examples, and say when you are uncertain. If provided study-note context, ground the answer in it and distinguish it from general knowledge."
        if context:
            system += "\n\nRelevant excerpts from the student's notes:\n" + context
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                try:
                    if provider.startswith("Ollama"):
                        response = answer_with_ollama(prompt, system, model_name, base_url)
                    else:
                        response = answer_with_gemini(prompt, system, model_name)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as exc:
                    st.error(str(exc))

with plan_tab:
    st.subheader("Make a realistic study plan")
    with st.form("plan_form"):
        subjects = st.text_input("Subjects or topics", placeholder="Biology, calculus, world history")
        hours = st.slider("Study time per day (hours)", 1, 10, 3)
        days = st.slider("Plan length (days)", 1, 30, 7)
        exam = st.date_input("Target date (optional)", value=date.today() + timedelta(days=days))
        make_plan = st.form_submit_button("Create my plan", type="primary")
    if make_plan:
        topics = [s.strip() for s in subjects.split(",") if s.strip()]
        if not topics:
            st.warning("Add at least one subject to build your plan.")
        else:
            st.markdown("### Your revision schedule")
            for day in range(min(days, max((exam-date.today()).days, 1))):
                topic = topics[day % len(topics)]
                st.markdown(f"**Day {day+1} · {date.today()+timedelta(days=day):%a, %b %d}**  \n{hours} hours: review {topic}, practice retrieval, then write down questions to revisit.")
            st.info("Tip: Keep the final 15 minutes for a closed-book recall check. Adjust this schedule around your classes and deadlines.")

with quiz_tab:
    st.subheader("Check what you remember")
    quiz_topic = st.text_input("Topic for the quiz", placeholder="Cell respiration")
    quiz_count = st.selectbox("Number of questions", [3, 5, 8, 10], index=1)
    if st.button("Generate practice quiz", type="primary"):
        context = retrieve(quiz_topic or "key ideas", st.session_state.chunks) if st.session_state.chunks else ""
        prompt = f"Create {quiz_count} varied practice questions about {quiz_topic or 'the uploaded study notes'}. Mix concise short-answer and multiple-choice questions. Put a complete answer key after the questions."
        if context:
            prompt += "\nUse these study notes as the source:\n" + context
        system = "You are a careful tutor. Make questions clear, avoid ambiguity, and provide answers with brief explanations."
        with st.spinner("Writing questions…"):
            try:
                if provider.startswith("Ollama"):
                    result = answer_with_ollama(prompt, system, model_name, base_url)
                else:
                    result = answer_with_gemini(prompt, system, model_name)
                st.markdown(result)
            except Exception as exc:
                st.error(str(exc))

st.caption("StudyMate is an educational aid. Check important answers against your course materials.")

