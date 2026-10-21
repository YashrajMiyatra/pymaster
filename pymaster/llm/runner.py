"""
Standalone Model Manager and Native Engine for PyMaster.
Downloads compact GGUF models and manages local llama-server if external Ollama is not present.
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional
import httpx
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.console import Console

console = Console()

MODELS = {
    "qwen-1.5b": {
        "name": "Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "size_mb": 986,
        "description": "Ultra-lightweight (986MB). Runs at 80+ tok/s on CPU or GPU. Master of Python basics, scripts, utilities.",
    },
    "qwen-7b": {
        "name": "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "size_mb": 4680,
        "description": "Full Python Powerhouse (~4.6GB). Fits in RTX 3050 VRAM. Beats 34B models on Python coding & logic.",
    },
}

CACHE_DIR = Path.home() / ".pymaster" / "models"


def ensure_model_downloaded(model_key: str = "qwen-1.5b") -> Path:
    """Download the requested model with a progress bar if not already cached."""
    if model_key not in MODELS:
        raise ValueError(f"Unknown model key '{model_key}'. Choose from: {list(MODELS.keys())}")

    meta = MODELS[model_key]
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_file = CACHE_DIR / meta["name"]

    if target_file.exists() and target_file.stat().st_size > 1024 * 1024 * 100:
        console.print(f"[bold green]✔ Model already cached:[/bold green] {target_file}")
        return target_file

    console.print(f"\n[bold cyan]Downloading {meta['name']} ({meta['size_mb']} MB)...[/bold cyan]")
    console.print(f"[dim]{meta['description']}[/dim]\n")

    with Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task_id = progress.add_task("Downloading", total=None)

        with httpx.stream("GET", meta["url"], follow_redirects=True, timeout=60.0) as response:
            total_size = int(response.headers.get("content-length", 0))
            progress.update(task_id, total=total_size)

            with open(target_file, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    progress.update(task_id, advance=len(chunk))

    console.print(f"\n[bold green]✔ Download complete:[/bold green] {target_file}")
    return target_file
