from __future__ import annotations

import dataclasses
import sys
import types
from unittest.mock import MagicMock, Mock

import pytest


@dataclasses.dataclass
class MockProcessing:
    seed: int
    subseed: int
    all_seeds: list[int]
    all_subseeds: list[int]
    subseed_strength: float
    prompt: str = ""
    negative_prompt: str = ""
    hr_prompt: str = ""
    hr_negative_prompt: str = ""
    n_iter: int = 1
    batch_size: int = 1
    enable_hr: bool = False
    all_prompts: list[str] = dataclasses.field(default_factory=list)
    all_hr_prompts: list[str] = dataclasses.field(default_factory=list)
    all_negative_prompts: list[str] = dataclasses.field(default_factory=list)
    all_hr_negative_prompts: list[str] = dataclasses.field(default_factory=list)

    def set_prompt_for_test(self, prompt):
        self.prompt = prompt
        self.hr_prompt = prompt
        self.all_prompts = [prompt] * self.n_iter * self.batch_size
        self.all_hr_prompts = self.all_prompts.copy()

    def set_negative_prompt_for_test(self, negative_prompt):
        self.negative_prompt = negative_prompt
        self.hr_negative_prompt = negative_prompt
        self.all_negative_prompts = [negative_prompt] * self.n_iter * self.batch_size
        self.all_hr_negative_prompts = self.all_negative_prompts.copy()


@pytest.fixture
def processing() -> MockProcessing:
    p = MockProcessing(
        seed=1000,
        subseed=2000,
        all_seeds=list(range(3000, 3000 + 10)),
        all_subseeds=list(range(4000, 4000 + 10)),
        subseed_strength=0,
    )
    p.set_prompt_for_test("beautiful sheep")
    p.set_negative_prompt_for_test("ugly")
    return p


@pytest.fixture
def monkeypatch_webui(monkeypatch, tmp_path):
    """
    Patch sys.modules to look like we have a (partial) WebUI installation.
    """
    import torch

    fake_webui = {
        "gradio": {"__getattr__": MagicMock()},
        "modules": {},
        "modules.scripts": {"Script": object, "basedir": lambda: str(tmp_path)},
        "modules.devices": {"device": torch.device("cpu")},
        "modules.processing": {"fix_seed": Mock()},
        "modules.shared": {
            "opts": types.SimpleNamespace(
                dp_auto_purge_cache=True,
                dp_ignore_whitespace=True,
                dp_limit_jinja_prompts=False,
                dp_magicprompt_batch_size=1,
                dp_parser_variant_end="}",
                dp_parser_variant_start="{",
                dp_parser_wildcard_wrap="__",
                dp_wildcard_manager_no_dedupe=False,
                dp_wildcard_manager_no_sort=False,
                dp_wildcard_manager_shuffle=False,
                dp_write_prompts_to_file=False,
                dp_write_raw_template=False,
            ),
        },
        "modules.script_callbacks": {
            "ImageSaveParams": object,
            "__getattr__": MagicMock(),
        },
        "modules.generation_parameters_copypaste": {
            "parse_generation_parameters": Mock(),
        },
    }

    for module_name, contents in fake_webui.items():
        if module_name in sys.modules:
            continue
        mod = types.ModuleType(module_name)
        for name, obj in contents.items():
            setattr(mod, name, obj)
        monkeypatch.setitem(sys.modules, module_name, mod)
