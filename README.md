# 🔍 AI Code Reviewer & Bug Fixing Agent

A multi-agent code review system that combines **real static analysis tools**, **LLM-based reasoning**, and **sandboxed fix verification** — built for the Generative AI Developer Intern Build Sprint.

🔗 **Live Demo:** (https://ai-code-reviewer-and-bug-fixing-agent---multi-agent-crewai-pip.streamlit.app)
🎥 **Demo Video:** https://www.loom.com/share/90c0e36efc30433e82b8646fb3268301

---

## Why this isn't just "an LLM wrapped in a chat box"

Most code review tools ask an LLM to guess at bugs from raw text and blindly trust whatever it says back. This project is built differently, on **4 verifiable stages**:

| Stage | What it does | Why it matters |
|---|---|---|
| 1️⃣ **Static Analysis** | Runs real tools — `pylint` + `bandit` — not LLM guessing | Deterministic, tool-verified issues (style, security) instead of hallucinated bugs |
| 2️⃣ **Bug Hunter Agent** | CrewAI agent reasons over the *verified* static analysis output + reads the code itself | Catches logic bugs static tools miss (e.g. off-by-one errors, mutable default args) |
| 3️⃣ **Fix Generator Agent** | Proposes a corrected version of the full file | Produces a real patch, not just a description of the problem |
| 4️⃣ **Sandboxed Verifier** | Actually **runs** the proposed fix in an isolated subprocess (syntax check + execution check) | Confirms the fix works before showing it — with **one automatic retry** if it fails |

This is a genuine agentic feedback loop — analyze → reason → fix → verify → retry — not a single prompt-and-display pattern.

---

## Architecture
User Input (code snippet / file)
│
▼
┌─────────────────────┐
│ Static Analyzer │ ← pylint + bandit (real tools)
└─────────┬─────────────┘
▼
┌─────────────────────┐
│ Bug Hunter Agent │ ← CrewAI + Groq LLM
│ (interprets results) │
└─────────┬─────────────┘
▼
┌─────────────────────┐
│ Fix Generator Agent │ ← CrewAI + Groq LLM
│ (proposes patch) │
└─────────┬─────────────┘
▼
┌─────────────────────┐
│ Sandboxed Verifier │ ← subprocess isolation
│ (syntax + runtime) │
└─────────┬─────────────┘
▼
✅ Verified Fix / 🔁 Retry once / ⚠️ Flag for manual review


---

## Tech Stack

- **Orchestration:** CrewAI (sequential multi-agent process)
- **LLM Inference:** Groq (`openai/gpt-oss-20b`)
- **Static Analysis:** pylint, bandit
- **Verification Sandbox:** Python `subprocess` (isolated syntax + execution checks)
- **UI:** Streamlit
- **Deployment:** Streamlit Community Cloud

---

## Project Structure

├── static_analyzer.py # Real static analysis (pylint + bandit)
├── agents.py # CrewAI agents: Bug Hunter, Fix Generator
├── verifier.py # Sandboxed fix verification
├── app.py # Streamlit UI, orchestrates the full pipeline
├── requirements.txt
└── README.md


---

## Running Locally

```bash
git clone https://github.com/ishrathjahaan0786/AI-Code-Reviewer-and-Bug-Fixing-Agent---multi-agent-CrewAI-pipeline.git
cd AI-Code-Reviewer-and-Bug-Fixing-Agent---multi-agent-CrewAI-pipeline
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create a `.env` file with:

GROQ_API_KEY=your_key_here


Then run:
```bash
streamlit run app.py
```

---

## A Note on Rate Limits

This demo runs on Groq's **free tier**, which has a token-per-minute limit. On unusually large files, this can occasionally trigger a rate-limit message — the app catches this gracefully (see the `try/except` in `app.py`) and displays a clear message instead of crashing. On a paid tier, this constraint doesn't apply. This was an intentional design decision: **handle real API limits gracefully rather than pretend they don't exist.**

---

## What I'd Add With More Time

- Multi-file / full-repo review (currently single-file focused)
- A Reviewer/Critic agent to cross-check the Fix Generator's output before showing it
- Caching static analysis results to reduce redundant LLM calls
- Support for languages beyond Python

---

Built by Esharath Jahanara Abdul (Ishrath) for the Generative AI Developer Intern Build Sprint.

