def fake_generator(prompts, **_kwargs):
    assert isinstance(prompts, list)  # be as particular as transformers is
    for prompt in prompts:
        assert "<" not in prompt  # should have been stripped
        yield [{"generated_text": f"magical {prompt},,,, wow, so nice"}]


def test_magic_prompts(monkeypatch):
    # Instrument the superclass so it doesn't try to load the model
    import dynamicprompts.generators.magicprompt as mp

    if hasattr(mp, "_import_transformers"):
        monkeypatch.setattr(mp, "_import_transformers", lambda: None)
    monkeypatch.setattr(
        mp.MagicPromptGenerator,
        "_load_pipeline",
        lambda self, model_name: fake_generator,
    )

    from sd_dynamic_prompts.magic_prompt import SpecialSyntaxAwareMagicPromptGenerator

    generator = SpecialSyntaxAwareMagicPromptGenerator()
    for prompt in generator.generate(
        "purple cat singing opera, artistic, painting "
        "<lora:loraname:0.7> <hypernet:v18000Steps:1>",
        5,
    ):
        # These must remain unchanged
        assert "<lora:loraname:0.7>" in prompt
        assert "<hypernet:v18000Steps:1>" in prompt
        # but we should expect to see some magic
        assert prompt.startswith("magical ")
        # See that multiple commas are coalesced
        assert ",,,," not in prompt
        assert ", wow, so nice" in prompt
