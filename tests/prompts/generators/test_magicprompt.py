from unittest import mock

from prompts.generators import MagicPromptGenerator
from prompts.generators import DummyGenerator
from functools import partial

class TestMagicPrompt:
    def test_cleanup_magic_prompt(self):
        #patch the load_pipeline method to return a mock generator
        with mock.patch.object(MagicPromptGenerator, "_load_pipeline") as mock_load_pipeline:
            mock_load_pipeline.return_value = mock.MagicMock()
            magic_prompt_generator = MagicPromptGenerator(None)
            
            for original_prompt in ["Original prompt", "[Original|prompt]", "{Original|prompt}", "Original - prompt"]:
                clean_up = partial(magic_prompt_generator.clean_up_magic_prompt, original_prompt)

                prompt = "- This is a {prompt} xyz" 
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is a (prompt) xyz"

                prompt = " $$ This is a prompt $$"
                cleaned_prompt =clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is a prompt"

                prompt = "This ( is ) a prompt"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This (is) a prompt"

                prompt = "This is - a prompt"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is-a prompt"

                prompt = "This is a prompt; another prompt"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is a prompt, another prompt"

                prompt = "This is. a prompt; another prompt"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is, a prompt, another prompt"

                prompt = "This is a prompt _ another prompt"
                cleaned_prompt = clean_up(original_prompt + prompt)
                assert cleaned_prompt == original_prompt + " This is a prompt another prompt"

                # TODO
                prompt = "This is a prompt , , another prompt"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " This is a prompt ,, another prompt"

                prompt = "This is a prompt! dddd"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " (This is a prompt:1.1) dddd"

                prompt = "This is a prompt!! dddd"
                cleaned_prompt = clean_up(original_prompt + " " + prompt)
                assert cleaned_prompt == original_prompt + " (This is a prompt:1.21) dddd"



    