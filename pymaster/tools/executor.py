"""
Subprocess Python execution sandbox with timeout and error capture.
"""

import sys
import subprocess
import time
from pathlib import Path
from typing import Optional
from pymaster.tools.base import registry


@registry.register(
    name="run_python_file",
    description="Execute a Python script in an isolated subprocess with timeout and capture output/errors.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to Python script to execute."},
            "args": {"type": "string", "description": "Optional command-line arguments to pass to the script."},
            "timeout_seconds": {"type": "integer", "description": "Execution timeout in seconds (default: 30)."},
        },
        "required": ["path"],
    },
)
def run_python_file(path: str, args: str = "", timeout_seconds: int = 30) -> str:
    target = Path(path).resolve()
    if not target.exists():
        return f"Error: Script '{path}' does not exist."

    # Use current running python interpreter (the virtualenv python)
    python_bin = sys.executable
    cmd = [python_bin, str(target)]
    if args.strip():
        cmd.extend(args.strip().split())

    start_time = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=str(target.parent),
        )
        duration = round(time.time() - start_time, 3)

        out = []
        out.append(f"=== Execution Completed (Exit Code: {proc.returncode}, Time: {duration}s) ===")
        if proc.stdout.strip():
            out.append("[STDOUT]\n" + proc.stdout.strip())
        if proc.stderr.strip():
            out.append("[STDERR / TRACEBACK]\n" + proc.stderr.strip())
        if not proc.stdout.strip() and not proc.stderr.strip():
            out.append("(Program produced no console output)")

        return "\n\n".join(out)
    except subprocess.TimeoutExpired:
        return f"Execution Error: Script timed out after {timeout_seconds} seconds."
    except Exception as e:
        return f"Execution Error: {e}"


@registry.register(
    name="run_inline_python",
    description="Execute a small snippet of Python code directly and get the result.",
    parameters={
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code snippet to execute."},
            "timeout_seconds": {"type": "integer", "description": "Timeout in seconds (default: 15)."},
        },
        "required": ["code"],
    },
)
def run_inline_python(code: str, timeout_seconds: int = 15) -> str:
    python_bin = sys.executable
    try:
        proc = subprocess.run(
            [python_bin, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        out = []
        if proc.returncode != 0:
            out.append(f"Failed with exit code {proc.returncode}")
        if proc.stdout:
            out.append(f"[Output]\n{proc.stdout}")
        if proc.stderr:
            out.append(f"[Error/Traceback]\n{proc.stderr}")
        return "\n".join(out) if out else "(No output, executed successfully)"
    except subprocess.TimeoutExpired:
        return f"Error: Inline execution timed out after {timeout_seconds}s."
    except Exception as e:
        return f"Error executing inline python: {e}"
