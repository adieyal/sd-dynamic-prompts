import math
import random
import re
import unicodedata
from pathlib import Path


def slugify(value, allow_unicode=False, max_length=50):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    return value[0:max_length]


def get_unique_path(directory: Path, original_filename, suffix="txt") -> Path:
    filename = original_filename
    for i in range(1000):
        path = (directory / filename).with_suffix("." + suffix)
        if not path.exists():
            return path
        filename = f"{slugify(original_filename)}-{math.floor(random.random() * 1000)}"

    raise Exception("Failed to find unique path")