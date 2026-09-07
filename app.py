"""
Streamlit UI for the AI Code Reviewer & Bug Fixing Agent.

Flow:
1. User pastes/uploads Python code
2. Real static analysis (pylint + bandit) runs
3. Bug Hunter + Fix Generator agents reason over the results
4. The proposed fix is verified in a sandbox
5. If verification fails, one retry is attempted
6. Final result (fix + verified/unverified status) is shown
"""

import streamlit as st
from static_analyzer import analyze_code
from agents import run_review
from verifier import verify_fix

st.set_page_config(page_title="AI Code Reviewer & Bug Fixing Agent", layout="wide")

st.title("🔍 AI Code Reviewer & Bug Fixing Agent")
st.caption(
    "Real static analysis (pylint + bandit) + multi-agent reasoning (CrewAI + Groq) "
    "+ sandboxed fix verification with a retry loop."
)

input_mode = st.radio("Input method", ["Paste code", "Upload .py file"], horizontal=True)

code_input = ""
if input_mode == "Paste code":
    code_input = st.text_area("Paste your Python code here", height=300)
else:
    uploaded = st.file_uploader("Upload a .py file", type=["py"])
    if uploaded:
        code_input = uploaded.read().decode("utf-8")



MAX_CHARS = 6000  # keeps us safely under Groq's free-tier rate limit

if code_input and len(code_input) > MAX_CHARS:
    st.info(
        f"This file is {len(code_input)} characters. To stay within the free-tier "
        f"rate limit, only the first {MAX_CHARS} characters will be reviewed."
    )
    code_input = code_input[:MAX_CHARS]

if st.button("Run Review", type="primary"):
    if not code_input.strip():
        st.warning("Please provide some code first.")
    else:
        with st.spinner("Running static analysis..."):
            analysis = analyze_code(code_input)

        st.subheader("Static Analysis Results (real tools, not LLM guesses)")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Pylint issues", analysis["pylint_count"])
        with col2:
            st.metric("Bandit (security) issues", analysis["bandit_count"])

        with st.expander("Raw pylint/bandit output"):
            st.json(analysis)

        try:
            with st.spinner("Agents reasoning over issues (this can take 20-40s)..."):
                result = run_review(code_input, analysis)
        except Exception as e:
            if "rate_limit" in str(e).lower() or "RateLimitError" in str(e):
                st.error(
                    "⏳ Hit the free-tier rate limit. Please wait about 15-20 seconds "
                    "and click 'Run Review' again."
                )
            else:
                st.error(f"Something went wrong while reviewing: {e}")
            st.stop()

        st.subheader("Bug Hunter Report")
        st.markdown(result["bug_report"])

        st.subheader("Proposed Fix")
        fixed_code = result["fixed_code"]

        with st.spinner("Verifying fix in sandbox..."):
            verification = verify_fix(fixed_code)

            if not verification["verified"]:
                st.warning(f"First fix failed verification at {verification['stage']}. Retrying once...")
                import time
                time.sleep(25)
            try:
                with st.spinner("Retrying fix..."):
                    
                    retry_result = run_review(fixed_code, analysis)
                    fixed_code = retry_result["fixed_code"]
                    verification = verify_fix(fixed_code)
            except Exception as e:
                st.error(f"Retry failed: {e}. Showing original fix attempt below.")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Original Code**")
            st.code(code_input, language="python")
        with col_b:
            st.markdown("**Fixed Code**")
            st.code(fixed_code, language="python")

        if verification["verified"]:
            st.success("✅ Fix verified — passed syntax and runtime checks in sandbox.")
        else:
            st.error(f"⚠️ Fix unverified — failed at {verification['stage']}. Manual review needed.")
            with st.expander("Verification error details"):
                st.text(verification["output"])