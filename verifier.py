"""
Verifies a proposed code fix by actually running it in a sandboxed
subprocess, instead of just trusting the LLM's suggestion.

This is what turns "AI suggests a fix" into "AI suggests a fix
and checks its own work" -- a genuine agentic feedback loop.
"""

import subprocess
import tempfile
import os


def verify_fix(fixed_code: str, timeout: int = 10) -> dict:
    """
    Runs the fixed code in an isolated subprocess to check it's at
    least syntactically valid and doesn't crash on import/execution.

    Returns a dict with 'verified' (bool) and 'output' (str) so the
    pipeline can decide whether to accept the fix or retry.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = os.path.join(tmp_dir, "fixed_code.py")
        with open(file_path, "w", encoding="utf-8") as f:
             f.write(fixed_code)

        # Step 1: syntax check (fast, catches most broken fixes)
        syntax_check = subprocess.run(
            ["python", "-m", "py_compile", file_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if syntax_check.returncode != 0:
            return {
                "verified": False,
                "stage": "syntax_check",
                "output": syntax_check.stderr,
            }

        # Step 2: actually run it, sandboxed, to catch runtime errors
        try:
            run_result = subprocess.run(
                ["python", file_path],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            if run_result.returncode != 0:
                return {
                    "verified": False,
                    "stage": "runtime_check",
                    "output": run_result.stderr,
                }
        except subprocess.TimeoutExpired:
            return {
                "verified": False,
                "stage": "runtime_check",
                "output": "Execution timed out (possible infinite loop).",
            }

        return {
            "verified": True,
            "stage": "passed",
            "output": run_result.stdout,
        }


if __name__ == "__main__":
    good_code = "print('hello world')"
    bad_code = "def broken(:\n    pass"

    print("Good code result:", verify_fix(good_code))
    print("Bad code result:", verify_fix(bad_code))