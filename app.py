import streamlit as st
from scorer import score_resume

st.set_page_config(page_title="Resume Match Scorer", page_icon="📄", layout="wide")

st.title("Resume to Job Match Scorer")
st.caption("Powered by Llama 3.2 running locally via Ollama")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Job Description")
    job_description = st.text_area(
        "Paste the job description here",
        height=350,
        placeholder="Paste the full job description...",
        label_visibility="collapsed",
    )

with col2:
    st.subheader("Resume")
    upload_tab, paste_tab = st.tabs(["Upload .txt file", "Paste text"])

    with upload_tab:
        uploaded_file = st.file_uploader(
            "Upload your resume as a .txt file",
            type=["txt"],
            label_visibility="collapsed",
        )
        resume_from_file = uploaded_file.read().decode("utf-8") if uploaded_file else ""

    with paste_tab:
        resume_from_paste = st.text_area(
            "Paste your resume here",
            height=290,
            placeholder="Paste your resume text...",
            label_visibility="collapsed",
        )

resume = resume_from_file or resume_from_paste

st.divider()

run = st.button("Score My Resume", type="primary", use_container_width=True)

if run:
    if not job_description.strip():
        st.error("Please paste a job description.")
    elif not resume.strip():
        st.error("Please upload or paste your resume.")
    else:
        with st.spinner("Analyzing with Llama 3.2..."):
            try:
                result = score_resume(resume, job_description)
            except ConnectionError as e:
                st.error(str(e))
                st.stop()
            except Exception as e:
                st.error(f"Something went wrong: {e}")
                st.stop()

        score = result.get("score", 0)
        missing = result.get("missing_keywords", [])
        matched = result.get("matched_keywords", [])
        summary = result.get("summary", "")

        # Score display
        if score >= 75:
            color = "green"
            label = "Strong Match"
        elif score >= 50:
            color = "orange"
            label = "Partial Match"
        else:
            color = "red"
            label = "Weak Match"

        st.markdown(
            f"<h1 style='text-align:center; color:{color};'>{score}/100 — {label}</h1>",
            unsafe_allow_html=True,
        )

        st.progress(score / 100)

        if summary:
            st.info(summary)

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Missing Keywords")
            if missing:
                for kw in missing:
                    st.markdown(f"- {kw}")
            else:
                st.success("No major gaps found!")

        with col_b:
            st.subheader("Matched Keywords")
            if matched:
                for kw in matched:
                    st.markdown(f"- {kw}")
            else:
                st.warning("No keyword matches detected.")
