from __future__ import annotations
import random

from .promptgenerator import PromptGenerator

class AttentionGenerator(PromptGenerator):
    def __init__(self, generator: PromptGenerator):
        import spacy
        self._nlp = spacy.load("en_core_web_sm")
        self._prompt_generator = generator

    def _add_emphasis(self, prompt):
        doc = self._nlp(prompt)
        keywords = [k for k in doc.noun_chunks]
        if len(keywords) == 0:
            return prompt

        keyword = random.choice(keywords)
        strength = random.randint(1, 9)
        prompt = prompt.replace(str(keyword), f"({keyword}:1.{strength})")

        return prompt

    def generate(self, *args, **kwargs) -> list[str]:
        prompts = self._prompt_generator.generate(*args, **kwargs)
        new_prompts = [self._add_emphasis(p) for p in prompts]
        
        return new_prompts

        
