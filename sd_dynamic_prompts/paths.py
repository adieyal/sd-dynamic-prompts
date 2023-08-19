from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_extension_base_path() -> Path:
    """
    Get the directory the extension is installed in.
    """
    path = Path(__file__).parent.parent
    assert (path / "sd_dynamic_prompts").is_dir()  # sanity check
    assert (path / "scripts").is_dir()  # sanity check
    return path


def get_magicprompt_models_txt_path() -> Path:
    return Path(get_extension_base_path() / "config" / "magicprompt_models.txt")


def get_wildcard_dir() -> Path:
    try:
        from modules.shared import opts
    except ImportError:  # likely not in an a1111 context
        opts = None

    wildcard_dir = getattr(opts, "wildcard_dir", None)
    if wildcard_dir is None:
        wildcard_dir = get_extension_base_path() / "wildcards"
    wildcard_dir = Path(wildcard_dir)
    try:
        wildcard_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(f"Failed to create wildcard directory {wildcard_dir}")
    return wildcard_dir
