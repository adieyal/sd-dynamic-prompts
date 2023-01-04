from __future__ import annotations
from pathlib import Path
import csv

from dynamicprompts import constants


def write_prompts(
    path: Path | str,
    positive_prompt: str,
    negative_prompt: str,
    positive_prompts: list[str],
    negative_prompts: list[str],
) -> Path:
    path = Path(path)
    with path.open("w", encoding=constants.DEFAULT_ENCODING, errors="ignore") as f:
        writer = csv.writer(f)
        writer.writerow(["positive_prompt", "negative_prompt"])
        writer.writerow([positive_prompt, negative_prompt])
        for positive_prompt, negative_prompt in zip(positive_prompts, negative_prompts):
            writer.writerow([positive_prompt, negative_prompt])

    return path
