from __future__ import annotations
from . import PromptGenerator

import re
from tqdm import trange

MODEL_NAME = "Gustavosta/MagicPrompt-Stable-Diffusion"


class MagicPromptGenerator(PromptGenerator):
    generator = None

    def _load_pipeline(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM
        from transformers import pipeline

        from modules.devices import get_optimal_device

        device = 0 if get_optimal_device() == "cuda" else -1

        if MagicPromptGenerator.generator is None:
            tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)

            MagicPromptGenerator.tokenizer = tokenizer
            MagicPromptGenerator.model = model
            MagicPromptGenerator.generator = pipeline(
                task="text-generation", tokenizer=tokenizer, model=model, device=device
            )

        return MagicPromptGenerator.generator

    def __init__(
        self,
        prompt_generator: PromptGenerator,
        max_prompt_length: int = 100,
        temperature: float = 0.7,
    ):
        self._generator = self._load_pipeline()
        self._prompt_generator = prompt_generator
        self._max_prompt_length = max_prompt_length
        self._temperature = float(temperature)

    def generate(self, *args, **kwargs) -> list[str]:
        prompts = self._prompt_generator.generate(*args, **kwargs)

        new_prompts = []
        for i in trange(len(prompts), desc="Generating Magic prompts"):
            prompt = prompts[i]
            magic_prompt = self._generator(
                prompt,
                max_length=self._max_prompt_length,
                temperature=self._temperature,
            )[0]["generated_text"]

            magic_prompt = self.clean_up_magic_prompt(magic_prompt)
            new_prompts.append(magic_prompt)

        return new_prompts

    def clean_up_magic_prompt(self, prompt):
        prompt = prompt.translate(str.maketrans("{}", "()")).strip()

        # useless non-word characters at the begin/end
        prompt = re.sub(r"^\W+|\W+$", "", prompt)

        # clean up whitespace in weighted parens
        prompt = re.sub(r"\(\s+", "(", prompt)
        prompt = re.sub(r"\s+\)", ")", prompt)

        # clean up whitespace in hyphens between words
        prompt = re.sub(r"\b\s+\-\s+\b", "-", prompt)
        prompt = re.sub(r"\s*[,;\.]+\s*", ", ", prompt)  # other analogues to ', '
        prompt = re.sub(r"\s+_+\s+", " ", prompt)  # useless underscores between phrases
        prompt = re.sub(r"\b,\s*,\s*\b", ", ", prompt)  # empty phrases

        # Translate bangs into proper weight modifiers
        for match in re.findall(r"\b([\w\s\-]+)(\!+)", prompt):
            phrase = match[0]
            full_match = match[0] + match[1]
            weight = round(pow(1.1, len(match[1])), 2)

            prompt = prompt.replace(full_match, f"({phrase}:{weight})")

        return prompt
