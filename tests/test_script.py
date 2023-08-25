import pytest


@pytest.mark.parametrize("enable_hr", [True, False], ids=["yes_hr", "no_hr"])
@pytest.mark.parametrize("is_combinatorial", [True, False], ids=["yes_comb", "no_comb"])
def test_script(
    monkeypatch,
    monkeypatch_webui,
    processing,
    enable_hr,
    is_combinatorial,
):
    from scripts.dynamic_prompting import Script

    s = Script()
    if not is_combinatorial:
        processing.batch_size = 3
    processing.set_prompt_for_test("{red|green|blue} ball")
    processing.set_negative_prompt_for_test("ugly")
    processing.enable_hr = enable_hr
    s.process(
        p=processing,
        is_enabled=True,
        is_combinatorial=is_combinatorial,
        combinatorial_batches=1,
        is_magic_prompt=False,
        is_feeling_lucky=False,
        is_attention_grabber=False,
        min_attention=0,
        max_attention=1,
        magic_prompt_length=0,
        magic_temp_value=1,
        use_fixed_seed=False,
        unlink_seed_from_prompt=False,
        disable_negative_prompt=False,
        enable_jinja_templates=False,
        no_image_generation=False,
        max_generations=0,
        magic_model="magic",
        magic_blocklist_regex=None,
    )
    assert isinstance(processing.all_prompts, list)
    assert isinstance(processing.all_negative_prompts, list)
    assert isinstance(processing.all_hr_prompts, list)
    assert isinstance(processing.all_hr_negative_prompts, list)

    if is_combinatorial:
        assert processing.all_prompts == ["red ball", "green ball", "blue ball"]
        assert processing.all_negative_prompts == ["ugly"] * 3

        if enable_hr:
            assert processing.all_hr_prompts == processing.all_prompts
            assert processing.all_hr_negative_prompts == processing.all_negative_prompts
    else:
        assert len(processing.all_prompts) == 3  # can't assert on the contents
