from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def is_empty_line(line):
    return line is None or line.strip() == "" or line.strip().startswith("#")


def get_requirements() -> list[str]:
    requirements = [
        line
        for line in (Path(__file__).parent / "requirements.txt")
        .read_text()
        .splitlines()
        if not is_empty_line(line)
    ]
    return requirements


def split_package(requirement) -> tuple[str, str | None, str | None, str | None]:
    delimiters = ["==", ">=", "<=", ">", "<", "~=", "!="]
    for delimiter in delimiters:
        if delimiter in requirement:
            splits = requirement.split(delimiter)
            package_split = splits[0].split("[")
            if len(package_split) == 2:
                package, extras = package_split
                extras = extras.strip("]")
            else:
                package = package_split[0]
                extras = ""

            return package, extras, delimiter, splits[1]
    return requirement, None, None, None


def get_dynamic_prompts_version() -> str | None:
    requirements = get_requirements()
    dynamicprompts_requirement = [
        r for r in requirements if r.startswith("dynamicprompts")
    ][0]
    _, _, _, dynamicprompts_requirement_version = split_package(
        dynamicprompts_requirement,
    )

    return dynamicprompts_requirement_version


def check_versions() -> None:
    import launch  # from AUTOMATIC1111

    requirements = get_requirements()

    for requirement in requirements:
        package, _, _, _ = split_package(requirement)
        if not launch.is_installed(package):
            launch.run_pip(f"install {requirement}", f"{requirement}")


def get_update_command() -> str:
    requirements = get_requirements()
    dynamicprompts_requirement = [
        r for r in requirements if r.startswith("dynamicprompts")
    ][0]
    return f"{sys.executable} -m pip install '{dynamicprompts_requirement}'"


def check_correct_dynamicprompts_installed() -> bool:
    try:
        import dynamicprompts

        dynamicprompts_requirement_version = get_dynamic_prompts_version()
        if dynamicprompts_requirement_version:
            if dynamicprompts.__version__ == dynamicprompts_requirement_version:
                return True
            else:
                update_command = get_update_command()
                print(
                    f"""*** WARNING: Something went wrong when updating to the latest dynamicprompts version. Please install it manually by running the following command:
    {update_command}
""",
                )
    except Exception as e:
        logger.exception(e)

    return False


if __name__ == "__main__":
    check_versions()
