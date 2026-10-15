"""Carga prompts versionados desde archivos .txt."""
import os
from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name="system", version=None):
    version = version or os.getenv("PROMPT_VERSION", "v2")
    return version, (PROMPTS_DIR / f"{name}_{version}.txt").read_text(encoding="utf-8")