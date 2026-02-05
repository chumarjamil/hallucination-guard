"""
Streamlit Dashboard — Hallucination Guard
===========================================

A simple web UI for analysing AI-generated text.

Requirements:
    pip install streamlit hallucination-guard

Run:
    streamlit run examples/streamlit_app.py
"""

from __future__ import annotations

try:
    import streamlit as st
except ImportError:
    raise SystemExit(
        "Streamlit is required: pip install streamlit"
    )

from hallucination_guard import detect


def main() -> None:
    st.set_page_config(page_title="Hallucination Guard", page_icon="🛡", layout="wide")

    st.title("🛡 Hallucination Guard")
    st.markdown("Detect hallucinations in AI-generated text.")
    st.divider()

    text = st.text_area(
        "Paste AI-generated text below:",
        height=150,
        placeholder="The Eiffel Tower is located in Berlin, Germany …",
    )

    if st.button("Analyse", type="primary", use_container_width=True):
        if not text.strip():
            st.error("Please enter some text to analyse.")
            return

        with st.spinner("Analysing …"):
            result = detect(text)

        # Risk score
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Hallucination Risk", f"{result.hallucination_risk:.0%}")
        col2.metric("Confidence", f"{result.confidence:.0%}")
        col3.metric("Total Claims", result.total_claims)
        col4.metric("Flagged", result.unsupported_claims)

        # Status
        if result.hallucinated:
            st.error(f"⚠ {result.explanation}")
        else:
            st.success(f"✓ {result.explanation}")

        # Highlighted text
        st.subheader("Highlighted Text")
        st.code(result.highlighted_text, language=None)

        # Flagged claims
        if result.flagged_claims:
            st.subheader("Flagged Claims")
            for i, fc in enumerate(result.flagged_claims, 1):
                with st.expander(f"Claim {i}: {fc['claim'][:80]}"):
                    st.write(f"**Confidence:** {fc['confidence']:.4f}")
                    st.write(f"**Source:** {fc.get('source', 'N/A')}")
                    st.write(f"**Evidence:** {fc['evidence']}")

        # Explanations
        if result.explanations:
            st.subheader("Detailed Explanations")
            for exp in result.explanations:
                icon = "🔴" if exp.hallucinated else "🟢"
                st.markdown(f"{icon} **{exp.claim[:80]}** — severity: `{exp.severity}`")
                st.caption(exp.explanation)

        # Raw JSON
        with st.expander("Raw JSON output"):
            st.json(result.to_dict())


if __name__ == "__main__":
    main()
