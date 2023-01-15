import sys
import logging
from pathlib import Path


logger = logging.getLogger(__name__)

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

import launch

def clean_package_name(s):
    s = s.split("==")[0].strip()
    s = s.split(">=")[0].strip()
    s = s.split("<=")[0].strip()
    s = s.split(">")[0].strip()
    s = s.split("<")[0].strip()
    s = s.split("~=")[0].strip()
    s = s.split("!=")[0].strip()
    s = s.split(" ")[0].strip()
    s = s.split("[")[0].strip()

    return s

def ensure_installed(package):
    isinstalled = launch.is_installed(package)
    if not isinstalled:
        launch.run_pip(f"install {package}", desc=f"{package}")

def ensure_version(dependency, version):
    package = clean_package_name(dependency)
    isinstalled = launch.is_installed(package)
    if isinstalled:
        installed_version = importlib_metadata.version(package)
        if installed_version == version:
            return

    launch.run_pip(f"install {dependency}=={version}", desc=f"{dependency}=={version}")


def check_versions():
    req_file = Path(__file__).parent / "requirements.txt"
    for row in open(req_file):
        splits = row.split("==")
        try:
            if len(splits) == 2:
                dependency = splits[0].strip()
                version = splits[1].strip()

                ensure_version(dependency, version)
            else:
                package = row.strip()
                ensure_installed(package)
        except Exception as e:
            logger.exception(e)


check_versions()
