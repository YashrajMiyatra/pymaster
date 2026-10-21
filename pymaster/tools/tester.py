"""
Pytest integration tool for automated testing and test-driven self-healing.
"""

import sys
import subprocess
from pathlib import Path
from pymaster.tools.base import registry


@registry.register(
    name="run_tests",
    description="Run pytest on a test file or test folder to verify functionality and catch errors.",
    parameters={
        "type": "object",
        "properties": {
            "test_path": {"type": "string", "description": "Path to test file or directory (default: 'tests')."},
            "verbose": {"type": "boolean", "description": "Run with -v flag for detailed test names."},
        },
    },
)
def run_tests(test_path: str = "tests", verbose: bool = True) -> str:
    target = Path(test_path).resolve()
    if not target.exists():
        return f"Error: Test target '{test_path}' does not exist."

    python_bin = sys.executable
    cmd = [python_bin, "-m", "pytest", str(target)]
    if verbose:
        cmd.append("-v")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(target.parent if target.is_file() else target),
        )
        output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        status = "PASSED" if proc.returncode == 0 else f"FAILED (Exit Code {proc.returncode})"
        return f"=== Pytest Results: {status} ===\n\n{output}"
    except subprocess.TimeoutExpired:
        return "Pytest Error: Test suite timed out after 60 seconds."
    except Exception as e:
        return f"Pytest Execution Error: {e}"
