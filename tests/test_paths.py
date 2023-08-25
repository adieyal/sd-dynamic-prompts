from sd_dynamic_prompts.paths import (
    get_extension_base_path,
    get_magicprompt_models_txt_path,
    get_wildcard_dir,
)


def test_get_paths():
    assert get_extension_base_path().is_dir()
    assert get_magicprompt_models_txt_path().is_file()
    assert get_wildcard_dir().is_dir()
