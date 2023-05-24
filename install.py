from __future__ import annotations

import importlib
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def is_empty_line(line):
    return line is None or line.strip() == "" or line.strip().startswith("#")


def get_requirements() -> list[str]:
    try:
        requirements_file_path = Path(__file__).parent / "requirements.txt"

        if not requirements_file_path.exists():
            raise FileNotFoundError("requirements.txt not found.")

        with requirements_file_path.open() as file:
            requirements = [
                line.strip()  # Stripping whitespace at start/end
                for line in file.readlines()
                if not is_empty_line(line)
            ]

    except Exception as e:
        raise Exception("Failed to parse requirements file.") from e

    return requirements


def split_package(requirement: str) -> tuple[str, str | None, str | None, str | None]:
    """
    Split a requirement string into package name, extras, comparison operator and version.

    :param requirement: Requirement string. E.g., "package[extra]>=1.0.0"
    :return: tuple of (package name, extras, comparison operator, version)
    """
    delimiters = ["==", ">=", "<=", ">", "<", "~=", "!="]

    package = requirement
    extras = None
    delimiter = None
    version = None

    for delimiter in delimiters:
        if delimiter in requirement:
            splits = requirement.split(delimiter)
            package_name_and_extras, version = splits[0], splits[1]

            # Check for extras
            if "[" in package_name_and_extras:
                package, extras = map(str.strip, package_name_and_extras.split("["))
                extras = extras.rstrip("]")
            else:
                package = package_name_and_extras.strip()

            break

    return package, extras, delimiter, version


def get_dynamic_prompts_version() -> str | None:
    """
    Get the version of dynamicprompts from the requirements.

    :return: Version of dynamicprompts if found, else None.
    """
    requirements = get_requirements()

    dynamicprompts_requirement = next(
        (r for r in requirements if r.startswith("dynamicprompts")),
        None,
    )

    if dynamicprompts_requirement is None:
        return None

    _, _, _, dynamicprompts_requirement_version = split_package(
        dynamicprompts_requirement,
    )

    return dynamicprompts_requirement_version


def check_versions():
    """Deprecated. Use check_and_install_dependencies() instead."""
    return check_and_install_dependencies()


def check_and_install_dependencies():
    import launch  # from AUTOMATIC1111

    requirements = get_requirements()

    for requirement in requirements:
        try:
            package, _, delimiter, package_version = split_package(requirement)

            if not launch.is_installed(package):
                logger.info(f"Installing {package}=={package_version}...")
                launch.run_pip(f"install {requirement}", f"{requirement}")
            else:
                module = importlib.import_module(".", package)
                version = getattr(module, "__version__", None)
                # handle the case where the dependency version is pinned or when no version is specified
                if delimiter == "==" or version is None:
                    if version is not None and version != package_version:
                        logger.info(
                            f"Found {package}=={version} but expected {package_version}. Trying to update...",
                        )
                        launch.run_pip(
                            f"install --upgrade {requirement}",
                            f"{requirement}",
                        )
                else:
                    # more general handling of version comparison operators will be handled in the future
                    pass

        except Exception as e:
            logger.error(f"Failed to check/update package {package}: {str(e)}")


def get_update_command() -> str | None:
    """
    Get the update command for dynamicprompts.

    :return: Update command for dynamicprompts if found, else None.
    """
    requirements = get_requirements()

    # Find the requirement line for dynamicprompts
    dynamicprompts_requirement = next(
        (r for r in requirements if r.startswith("dynamicprompts")),
        None,
    )

    # If dynamicprompts requirement was not found
    if dynamicprompts_requirement is None:
        return None

    # If found, return the pip install command
    return f"{sys.executable} -m pip install '{dynamicprompts_requirement}'"


def check_correct_dynamicprompts_installed() -> bool:
    """
    Check if the installed version of dynamicprompts matches the required version.

    :return: True if versions match, else False.
    """
    try:
        import dynamicprompts
    except ImportError:
        logger.error("dynamicprompts module is not installed.")
        return False
    except Exception as e:
        logger.exception("Unexpected error while importing dynamicprompts.", e)
        return False

    dynamicprompts_requirement_version = get_dynamic_prompts_version()

    if dynamicprompts_requirement_version is None:
        logger.warning("Unable to find dynamicprompts version requirement.")
        return False

    if dynamicprompts.__version__ != dynamicprompts_requirement_version:
        update_command = get_update_command()
        logger.warning(
            f"Installed dynamicprompts version ({dynamicprompts.__version__}) does not match the required version ({dynamicprompts_requirement_version}). "
            f"Please update manually by running: {update_command}",
        )
        return False

    return True


if __name__ == "__main__":
    check_and_install_dependencies()
