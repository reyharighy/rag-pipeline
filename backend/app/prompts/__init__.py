from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
PROMPTS_DEFAULTS_DIR = PROMPTS_DIR / "defaults"

__all__ = ["PROMPTS_DIR", "PROMPTS_DEFAULTS_DIR"]
