from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    from sd_dynamic_prompts.version_tools import install_requirements

    install_requirements()
