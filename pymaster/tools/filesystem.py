"""
Filesystem tools for PyMaster: read, write, edit, and explore codebases.
"""

import os
from pathlib import Path
from typing import Optional
from pymaster.tools.base import registry


@registry.register(
    name="read_file",
    description="Read the contents of a file. Supports line range filtering.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read."},
            "start_line": {"type": "integer", "description": "Optional 1-based start line."},
            "end_line": {"type": "integer", "description": "Optional 1-based end line."},
        },
        "required": ["path"],
    },
)
def read_file(path: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
    target_path = Path(path).resolve()
    if not target_path.exists():
        return f"Error: File '{path}' does not exist."
    if not target_path.is_file():
        return f"Error: Path '{path}' is a directory, not a file."

    try:
        with open(target_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)
        start = max(1, start_line) if start_line else 1
        end = min(total_lines, end_line) if end_line else total_lines

        output = []
        for i in range(start - 1, end):
            output.append(f"{i + 1:4d} | {lines[i]}")

        header = f"--- {path} (lines {start}-{end} of {total_lines}) ---\n"
        return header + "".join(output)
    except Exception as e:
        return f"Error reading file '{path}': {e}"


@registry.register(
    name="write_file",
    description="Create a new file or completely overwrite an existing file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Target file path."},
            "content": {"type": "string", "description": "Full text content to write."},
            "overwrite": {"type": "boolean", "description": "Set to true to overwrite if file already exists."},
        },
        "required": ["path", "content"],
    },
)
def write_file(path: str, content: str, overwrite: bool = True) -> str:
    # Reject raw XML tool hallucination
    trimmed = content.strip()
    if trimmed.startswith("<tools>") or trimmed.startswith("<function>") or "<function_name>" in trimmed:
        return (
            f"Error: Invalid content. The 'content' argument contains internal tool XML markup instead of actual Python code.\n"
            f"Please write pure Python code (e.g. import pygame, def main(): ...)."
        )

    target_path = Path(path).resolve()
    if target_path.exists() and not overwrite:
        return f"Error: File '{path}' already exists and overwrite=False."

    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Success: Wrote {len(content.splitlines())} lines to '{path}'."
    except Exception as e:
        return f"Error writing file '{path}': {e}"


@registry.register(
    name="edit_file",
    description="Replace an exact block of text in a file with new content (diff replacement).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File to edit."},
            "target": {"type": "string", "description": "Exact text block to replace."},
            "replacement": {"type": "string", "description": "New replacement text."},
        },
        "required": ["path", "target", "replacement"],
    },
)
def edit_file(path: str, target: str, replacement: str) -> str:
    target_path = Path(path).resolve()
    if not target_path.exists():
        return f"Error: File '{path}' does not exist."

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            content = f.read()

        if target not in content:
            return (
                f"Error: Exact target text not found in '{path}'.\n"
                f"Tip: Do not repeat failing edit_file calls. Instead, use 'write_file' with overwrite=true to write the complete updated file directly."
            )

        occurrences = content.count(target)
        new_content = content.replace(target, replacement, 1)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f"Success: Replaced 1 occurrence in '{path}'. (Total found: {occurrences})"
    except Exception as e:
        return f"Error editing file '{path}': {e}"


@registry.register(
    name="list_files",
    description="List files and directories in a workspace.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Directory path (defaults to current dir)."},
            "max_depth": {"type": "integer", "description": "Max depth to traverse (default: 2)."},
        },
    },
)
def list_files(path: str = ".", max_depth: int = 2) -> str:
    root = Path(path).resolve()
    if not root.exists():
        return f"Error: Directory '{path}' does not exist."

    results = []
    ignored = {".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".idea", ".vscode"}

    def scan(dir_path: Path, current_depth: int):
        if current_depth > max_depth:
            return
        try:
            for item in sorted(dir_path.iterdir()):
                if item.name in ignored or item.name.startswith("."):
                    continue
                rel_path = item.relative_to(root)
                indent = "  " * (current_depth - 1)
                if item.is_dir():
                    results.append(f"{indent}📁 {rel_path}/")
                    scan(item, current_depth + 1)
                else:
                    size = item.stat().st_size
                    results.append(f"{indent}📄 {rel_path} ({size} bytes)")
        except PermissionError:
            pass

    scan(root, 1)
    if not results:
        return f"Directory '{path}' is empty or contains only hidden files."
    return "\n".join(results)
