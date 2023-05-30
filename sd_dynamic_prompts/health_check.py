import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def check_jinja_available():
    try:
        from dynamicprompts.generators import JinjaGenerator

        _ = JinjaGenerator({}, "")
        return True
    except Exception as e:
        logger.warning(
            f"Jinja2 not available: {e}. Please install Jinja2 with the following command: 'pip install -U Jinja2'",
        )
        return False
