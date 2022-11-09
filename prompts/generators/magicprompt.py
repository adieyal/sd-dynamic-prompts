from __future__ import annotations
from . import PromptGenerator

class MagicPromptGenerator(PromptGenerator):
    generator = None

    def _load_pipeline(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers import pipeline

        from modules.safe import unsafe_torch_load, torch
        from modules.devices import get_optimal_device
        # TODO this needs to be fixed
        device = 0 if get_optimal_device() == "cuda" else -1

        try:
            safe_load = torch.load
            torch.load = unsafe_torch_load

            if MagicPromptGenerator.generator is None:
                tokenizer = AutoTokenizer.from_pretrained("Gustavosta/MagicPrompt-Stable-Diffusion")
                model = AutoModelForCausalLM.from_pretrained("Gustavosta/MagicPrompt-Stable-Diffusion")

                MagicPromptGenerator.tokenizer = tokenizer
                MagicPromptGenerator.model = model

                MagicPromptGenerator.generator = pipeline(task="text-generation", model=model, tokenizer=tokenizer, device=device)

            return MagicPromptGenerator.generator
        finally:
            torch.load = safe_load

        return MagicPromptGenerator.generator

    def __init__(self, prompt_generator: PromptGenerator, max_prompt_length: 100, temperature: 0.7):
        self._generator         = self._load_pipeline()
        self._prompt_generator  = prompt_generator
        self._max_prompt_length = max_prompt_length
        self._temperature       = float(temperature)

    def generate(self, *args, **kwargs) -> str:
        prompts = self._prompt_generator.generate(*args, **kwargs)
        new_prompts = [self._generator(prompt, max_length=self._max_prompt_length, temperature=self._temperature)[0]["generated_text"] for prompt in prompts]

        return new_prompts

