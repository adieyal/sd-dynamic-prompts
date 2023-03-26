import pytest

from sd_dynamic_prompts.attention_generator import SpecialSyntaxAwareAttentionGenerator


@pytest.mark.slow
def test_default_generator():
    pytest.importorskip("spacy")
    generator = SpecialSyntaxAwareAttentionGenerator()
    for prompt in generator.generate(
        "purple cat singing opera, artistic, painting "
        "<lora:loraname:0.7> <hypernet:v18000Steps:1>",
        5,
    ):
        # These must remain unchanged
        assert "<lora:loraname:0.7>" in prompt
        assert "<hypernet:v18000Steps:1>" in prompt
        # but we should expect to see the emphasis added in other words
        assert "(purple" in prompt or "(artistic" in prompt or "(painting" in prompt
        assert ")" in prompt
