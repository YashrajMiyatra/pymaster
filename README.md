# 🐍 PyMaster

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](tests/)
[![Architecture](https://img.shields.io/badge/Architecture-Autonomous%20ReAct-orange.svg)](#-architecture)
[![Local First](https://img.shields.io/badge/Privacy-100%25%20Local-purple.svg)](#-what-is-pymaster)

> **Autonomous Local Python AI Coding Engine**  
> *Zero external framework bloat. 100% private, runs fast on any computer or device.*

---

## ⚡ What is PyMaster?

**PyMaster** is an autonomous, local-first Python software engineer modeled after agentic systems like Antigravity and Claude Code, designed specifically for **Python mastery**.

Instead of relying on heavy cloud APIs or bulky frameworks (no LangChain, no CrewAI, no Docker required), PyMaster runs against **ultra-fast local quantized models** (like `Qwen2.5-Coder-1.5B` or `7B`) directly on your hardware:
- **CPU or GPU**: Runs on modern GPUs (CUDA) or directly on consumer CPUs (AVX2).
- **Lightweight Footprint**: Uses ~1GB to 2GB RAM with the 1.5B model, generating 40–80+ tokens/sec.
- **Self-Healing Loop**: Generates code, runs AST checks, executes scripts/tests, captures tracebacks, and automatically patches bugs until the code works.

---

## 🏗️ Architecture

```
User Prompt (e.g., "Build an async rate-limited GitHub repo fetcher")
      │
      ▼
┌────────────────────────────────────────────────────────┐
│ PyMaster Autonomous Agent Core                         │
│                                                        │
│  1. Plan & Architect Solution                          │
│  2. Dispatch Native Tools:                             │
│     ├── write_file / edit_file (Diff Replacer)         │
│     ├── check_syntax (Pure Python AST Parser)          │
│     ├── inspect_symbols (Imports, Classes, Functions)  │
│     ├── run_python_file (Subprocess Sandbox)           │
│     └── run_tests (Pytest Assertion Extractor)         │
│                                                        │
│  3. Self-Healing Cycle:                                │
│     Error / Traceback ──► Model Diagnoses ──► Auto-Fix │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart

### 1. Installation
In your terminal:
```bash
git clone https://github.com/YashrajMiyatra/pymaster.git
cd pymaster
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
```

### 2. Connect to a Local Model
PyMaster connects to any local OpenAI-compatible inference server out-of-the-box:

**Option A: Using Ollama (Recommended)**
```bash
ollama run qwen2.5-coder:1.5b    # or qwen2.5-coder:7b
pymaster
```

**Option B: Using LM Studio or llama-server**
```bash
# Point to custom local port
pymaster --url http://localhost:1234/v1 --model local-model
```

**Option C: Non-interactive One-Shot Prompt**
```bash
pymaster --prompt "Write a CLI tool that parses CSV logs and outputs top error frequencies"
```

---

## 💬 Interactive Commands

Inside the PyMaster REPL:
- `/tools` — Display all registered tools and their input parameters
- `/models` — Query available models on your local server
- `/reset` — Clear conversation context and start fresh
- `/exit` — Exit PyMaster

---

## 🛠️ Built-in Tools

| Tool | Purpose |
| :--- | :--- |
| `write_file` | Create or replace project files with clean formatting |
| `edit_file` | Surgical diff replacement of exact code blocks |
| `read_file` | Read files with line numbers and range filtering |
| `list_files` | Visualize workspace structure and file sizes |
| `check_syntax` | Validate AST syntax without executing untrusted code |
| `inspect_symbols`| Extract classes, methods, signatures, and imports |
| `run_python_file`| Subprocess runner with timeout and traceback capture |
| `run_tests` | Pytest runner with pass/fail and assertion parsing |

---

## 🧪 Running Tests
```bash
pytest tests/ -v
```
All unit tests and simulated self-healing agent workflows execute in **under 0.3s**!

---

## 📄 License
MIT License. Free to use, modify, and distribute.
