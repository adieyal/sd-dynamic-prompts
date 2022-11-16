from unittest import mock

from prompts.generators import MagicPromptGenerator
from prompts.generators import DummyGenerator

class TestMagicPrompt:
    def test_cleanup_magic_prompt(self):
        #patch the load_pipeline method to return a mock generator
        with mock.patch.object(MagicPromptGenerator, "_load_pipeline") as mock_load_pipeline:
            mock_load_pipeline.return_value = mock.MagicMock()
            magic_prompt_generator = MagicPromptGenerator(None)

            prompt = "This is a {prompt} xyz" 
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is a (prompt) xyz"

            prompt = "$$ This is a prompt $$"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is a prompt"

            prompt = "This ( is ) a prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This (is) a prompt"

            prompt = "This is - a prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is-a prompt"

            # prompt = re.sub(r"\s*[,;\.]+\s*", ", ", prompt)  # other analogues to ', '
            prompt = "This is a prompt; another prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is a prompt, another prompt"

            prompt = "This is. a prompt; another prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is, a prompt, another prompt"

            prompt = "This is a prompt _ another prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is a prompt another prompt"

            prompt = "This is a prompt , , another prompt"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "This is a prompt, another prompt"

            prompt = "This is a prompt! dddd"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "(This is a prompt:1.1) dddd"

            prompt = "This is a prompt!! dddd"
            cleaned_prompt = magic_prompt_generator.clean_up_magic_prompt(prompt)
            assert cleaned_prompt == "(This is a prompt:1.21) dddd"



    