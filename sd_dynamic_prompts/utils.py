import logging


def get_logger(name):
    from modules.shared import opts

    is_debug = getattr(opts, "is_debug", False)
    logger = logging.getLogger(name)

    if is_debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    sh = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger
