import os
import sys
import logging

logger = logging.getLogger(__name__)

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

import launch


def ensure_version(package, version):
    if isinstalled := launch.is_installed(package):
        installed_version = importlib_metadata.version(package)

        if installed_version == version:
            return

    launch.run_pip(f"install {package}=={version}", desc=f"{package}=={version}")


def check_versions():
    req_file = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "requirements.txt"
    )
    for row in open(req_file):
        splits = row.split("==")
        try:
            if len(splits) == 2:
                package = splits[0].strip()
                version = splits[1].strip()

                ensure_version(package, version)
        except Exception as e:
            logger.exception(e)


check_versions()
