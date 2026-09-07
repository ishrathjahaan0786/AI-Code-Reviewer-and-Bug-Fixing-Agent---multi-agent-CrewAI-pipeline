"""
Defines the CrewAI agents: Bug Hunter and Fix Generator.
They reason over the REAL static analysis output (from static_analyzer.py),
not raw code guessing.
"""

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process, LLM

load_dotenv()

llm = LLM(
    model="groq/openai/gpt-oss-20b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0.2,
    max_tokens=800,
)

bug_hunter = Agent(
    role="Senior Bug Hunter",
    goal="Interpret static analysis results and identify the most important real bugs and security issues",
    backstory=(
        "You are an experienced code reviewer. You are given verified output "
        "from real static analysis tools (pylint and bandit). Your job is to "
        "explain, in plain English, which issues actually matter, ranked by severity, "
        "and ignore purely stylistic noise unless nothing else is found."
    ),
    llm=llm,
    verbose=True,
)

fix_generator = Agent(
    role="Fix Generator",
    goal="Write a corrected version of the full code file that resolves the identified bugs",
    backstory=(
        "You are a precise Python developer. Given the original code and a list of "
        "confirmed issues, you rewrite the FULL file with fixes applied. "
        "You never remove functionality, only fix the flagged issues. "
        "You output ONLY the corrected Python code, no explanation, no markdown fences."
    ),
    llm=llm,
    verbose=True,
)


def build_review_tasks(original_code: str, analysis_results: dict):
    bug_hunt_task = Task(
        description=(
            f"Here is the original code:\n\n{original_code}\n\n"
            f"Here are the static analysis results:\n\n{analysis_results}\n\n"
            "Identify and rank the most important real issues (bugs, security problems). "
            "Ignore trivial style issues if there are more serious ones present."
        ),
        expected_output="A ranked list of real issues with a one-line explanation each.",
        agent=bug_hunter,
    )

    fix_task = Task(
        description=(
            f"Here is the original code:\n\n{original_code}\n\n"
            "Using the issues identified in the previous task, rewrite the FULL file "
            "with fixes applied. Output ONLY the corrected Python code, nothing else."
        ),
        expected_output="The full corrected Python file, code only.",
        agent=fix_generator,
        context=[bug_hunt_task],
    )

    return bug_hunt_task, fix_task


def run_review(original_code: str, analysis_results: dict) -> dict:
    bug_hunt_task, fix_task = build_review_tasks(original_code, analysis_results)

    crew = Crew(
        agents=[bug_hunter, fix_generator],
        tasks=[bug_hunt_task, fix_task],
        process=Process.sequential,
        verbose=True,
    )

    result = crew.kickoff()

    return {
        "bug_report": bug_hunt_task.output.raw if bug_hunt_task.output else "",
        "fixed_code": fix_task.output.raw if fix_task.output else "",
    }