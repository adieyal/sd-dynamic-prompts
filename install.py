import logging
from pathlib import Path

from dynamicprompts.utils import is_empty_line

logger = logging.getLogger(__name__)


def check_versions() -> None:
    requirements = [
        line
        for line
        in (Path(__file__).parent / "requirements.txt").read_text().splitlines()
        if not is_empty_line(line)
    ]
    pip_command = f"install {' '.join(requirements)}"
    try:
        from launch import run_pip  # from AUTOMATIC1111
        run_pip(pip_command, desc="sd-dynamic-prompts requirements.txt")
    except Exception as e:
        logger.exception(e)


check_versions()
