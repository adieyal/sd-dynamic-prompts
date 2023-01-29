from tempfile import NamedTemporaryFile

import pytest

from sd_dynamic_prompts.ui.prompt_writer import PromptWriter


@pytest.fixture()
def prompt_writer() -> PromptWriter:
    return PromptWriter()


@pytest.fixture()
def populated_prompt_writer() -> PromptWriter:
    prompt_writer = PromptWriter()
    prompt_writer.set_data(
        positive_template="positive",
        negative_template="negative",
        positive_prompts=["positive1", "positive2"],
        negative_prompts=["negative1", "negative2"],
    )
    return prompt_writer


class TestPromptWriter:
    def _write_to_file(self, prompt_writer: PromptWriter) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", delete=True) as f:
            prompt_writer.write_prompts(f.name)

    def _checks_writes_empty_file(self, prompt_writer: PromptWriter) -> bool:
        with NamedTemporaryFile("w", encoding="utf-8", delete=True) as f:
            prompt_writer.write_prompts(f.name)
            output = open(f.name).read()
            return output == ""

    def test_default_disabled(self, prompt_writer: PromptWriter) -> None:
        assert prompt_writer.enabled is False

    def test_reset(self, prompt_writer: PromptWriter) -> None:
        prompt_writer._already_saved = True
        prompt_writer._positive_template = "positive"
        prompt_writer._negative_template = "negative"
        prompt_writer._positive_prompts = ["positive1", "positive2"]
        prompt_writer._negative_prompts = ["negative1", "negative2"]

        prompt_writer.reset()

        assert prompt_writer._already_saved is False
        assert prompt_writer._positive_template == ""
        assert prompt_writer._negative_template == ""
        assert prompt_writer._positive_prompts == []
        assert prompt_writer._negative_prompts == []

    def test_set_data(self, populated_prompt_writer: PromptWriter) -> None:
        assert populated_prompt_writer._positive_template == "positive"
        assert populated_prompt_writer._negative_template == "negative"
        assert populated_prompt_writer._positive_prompts == ["positive1", "positive2"]
        assert populated_prompt_writer._negative_prompts == ["negative1", "negative2"]

    def test_doesnt_write_when_disabled(
        self,
        populated_prompt_writer: PromptWriter,
    ) -> None:
        populated_prompt_writer.enabled = False
        assert self._checks_writes_empty_file(populated_prompt_writer)

    def test_write_prompts(self, populated_prompt_writer: PromptWriter) -> None:
        populated_prompt_writer.enabled = True

        with NamedTemporaryFile("w", encoding="utf-8", delete=True) as f:
            populated_prompt_writer.write_prompts(f.name)
            with open(f.name) as f2:
                lines = f2.read().splitlines()

                assert lines == [
                    "positive_prompt,negative_prompt",
                    "positive,negative",
                    "positive1,negative1",
                    "positive2,negative2",
                ]

    def test_only_write_once(self, populated_prompt_writer: PromptWriter) -> None:
        populated_prompt_writer.enabled = True

        self._write_to_file(populated_prompt_writer)
        assert self._checks_writes_empty_file(populated_prompt_writer)

    def test_writes_after_reset(self, populated_prompt_writer: PromptWriter) -> None:
        populated_prompt_writer.enabled = True
        self._write_to_file(populated_prompt_writer)

        populated_prompt_writer.reset()

        assert not self._checks_writes_empty_file(populated_prompt_writer)
