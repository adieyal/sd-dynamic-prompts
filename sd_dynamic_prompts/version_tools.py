# NB: this file may not import anything from `sd_dynamic_prompts` because it is used by `install.py`.

from __future__ import annotations

import dataclasses
import logging
import shlex
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

try:
    import tomllib as tomli  # Python 3.11+
except ImportError:
    try:
        import tomli  # may have been installed already
    except ImportError:
        try:
            # pip has had this since version 21.2
            from pip._vendor import tomli
        except ImportError:
            raise ImportError(
                "A TOML library is required to install sd-dynamic-prompts, "
                "but could not be imported. "
                "Please install tomli (pip install tomli) and try again.",
            ) from None

try:
    from packaging.requirements import Requirement
except ImportError:
    # pip has had this since 2018
    from pip._vendor.packaging.requirements import Requirement

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class InstallResult:
    requirement: str
    specifier: str
    installed: str
    correct: bool

    @property
    def message(self) -> str | None:
        if self.correct:
            return None
        return (
            f"You have dynamicprompts {self.installed} installed, "
            f"but this extension requires {self.specifier}. "
            f"Please run `install.py` from the sd-dynamic-prompts extension directory, "
            f"or `{self.pip_install_command}`."
        )

    @property
    def pip_install_command(self) -> str:
        return f"pip install {self.requirement}"

    def raise_if_incorrect(self) -> None:
        message = self.message
        if message:
            raise RuntimeError(message)


@lru_cache(maxsize=1)
def get_requirements() -> tuple[str]:
    toml_text = (Path(__file__).parent.parent / "pyproject.toml").read_text()
    return tuple(tomli.loads(toml_text)["project"]["dependencies"])


def get_dynamic_prompts_requirement() -> Requirement | None:
    for req in get_requirements():
        if req.startswith("dynamicprompts"):
            return Requirement(req)
    return None


def get_dynamicprompts_install_result() -> InstallResult:
    import dynamicprompts

    dp_req = get_dynamic_prompts_requirement()
    if not dp_req:
        raise RuntimeError("dynamicprompts requirement not found")
    return InstallResult(
        requirement=str(dp_req),
        specifier=str(dp_req.specifier),
        installed=dynamicprompts.__version__,
        correct=(dynamicprompts.__version__ in dp_req.specifier),
    )


def install_requirements() -> None:
    """
    Invoke pip to install the requirements for the extension.
    """
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        *get_requirements(),
    ]
    print(f"sd-dynamic-prompts installer: running {shlex.join(command)}")
    subprocess.check_call(command)


def selftest() -> None:
    res = get_dynamicprompts_install_result()
    print(res)
    res.raise_if_incorrect()


if __name__ == "__main__":
    selftest()
