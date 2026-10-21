"""
Python AST & Static Analysis Intelligence for PyMaster.
Analyzes syntax, symbol tables, functions, classes, and dependencies without executing.
"""

import ast
from pathlib import Path
from typing import Dict, Any, List
from pymaster.tools.base import registry


@registry.register(
    name="check_syntax",
    description="Check if a Python file or code snippet has syntax errors before running it.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to Python file to validate."},
        },
        "required": ["path"],
    },
)
def check_syntax(path: str) -> str:
    target = Path(path).resolve()
    if not target.exists():
        return f"Error: File '{path}' does not exist."

    try:
        with open(target, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code, filename=str(target))
        return f"Syntax OK: '{path}' parsed successfully with zero syntax errors."
    except SyntaxError as e:
        return (
            f"SYNTAX ERROR in '{path}' at line {e.lineno}, col {e.offset}:\n"
            f"  {e.text.strip() if e.text else ''}\n"
            f"  Error details: {e.msg}"
        )
    except Exception as e:
        return f"Error checking syntax of '{path}': {e}"


@registry.register(
    name="inspect_symbols",
    description="Inspect Python symbols: list all classes, methods, functions, docstrings, and imported libraries in a file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to Python file."},
        },
        "required": ["path"],
    },
)
def inspect_symbols(path: str) -> str:
    target = Path(path).resolve()
    if not target.exists():
        return f"Error: File '{path}' does not exist."

    try:
        with open(target, "r", encoding="utf-8") as f:
            code = f.read()
        tree = ast.parse(code, filename=str(target))

        imports = []
        functions = []
        classes = []

        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = ", ".join(alias.name for alias in node.names)
                imports.append(f"from {module} import {names}")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = [arg.arg for arg in node.args.args]
                is_async = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                doc = ast.get_docstring(node)
                summary = doc.splitlines()[0] if doc else "No docstring"
                functions.append(f"  - {is_async}def {node.name}({', '.join(args)}) [line {node.lineno}]: {summary}")
            elif isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                summary = doc.splitlines()[0] if doc else "No docstring"
                methods = []
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(sub.name)
                classes.append(
                    f"  - class {node.name} [line {node.lineno}]: {summary}\n"
                    f"      methods: {', '.join(methods) if methods else 'none'}"
                )

        output = [f"=== Codebase Intelligence for '{path}' ==="]
        output.append("\n[Imports]")
        output.extend(imports if imports else ["  (none)"])
        output.append("\n[Classes]")
        output.extend(classes if classes else ["  (none)"])
        output.append("\n[Top-Level Functions]")
        output.extend(functions if functions else ["  (none)"])

        return "\n".join(output)
    except Exception as e:
        return f"Error analyzing symbols in '{path}': {e}"
