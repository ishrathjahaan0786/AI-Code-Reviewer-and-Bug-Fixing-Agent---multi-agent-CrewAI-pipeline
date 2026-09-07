"""
Runs REAL static analysis tools (pylint + bandit) on a Python file
and returns structured, deterministic results.

This is the credibility upgrade: instead of asking an LLM to "guess"
at code smells, we run actual tools and let the LLM reason over
verified output.
"""

import json
import subprocess
import tempfile
import os


def run_pylint(file_path: str) -> list:
    """Run pylint on a file and return structured issues."""
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            return json.loads(result.stdout)
        return []
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return [{"message": f"pylint failed to run: {e}", "type": "error"}]


def run_bandit(file_path: str) -> list:
    """Run bandit (security linter) on a file and return structured issues."""
    try:
        result = subprocess.run(
            ["bandit", "-f", "json", file_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            data = json.loads(result.stdout)
            return data.get("results", [])
        return []
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return [{"issue_text": f"bandit failed to run: {e}", "issue_severity": "ERROR"}]


def analyze_code(code_str: str, filename: str = "submitted_code.py") -> dict:
    """
    Write code to a temp file, run both tools, return combined structured results.
    This is the single entry point the CrewAI agents will call.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_str)

        pylint_issues = run_pylint(file_path)
        bandit_issues = run_bandit(file_path)

        return {
            "pylint_issues": pylint_issues,
            "bandit_issues": bandit_issues,
            "pylint_count": len(pylint_issues),
            "bandit_count": len(bandit_issues),
        }


if __name__ == "__main__":
    sample = "import os\ndef foo(x):\n    y = eval(x)\n    return y\n"
    print(json.dumps(analyze_code(sample), indent=2))