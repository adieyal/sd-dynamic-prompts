from __future__ import annotations
import random

from .promptgenerator import PromptGenerator

class AttentionGenerator(PromptGenerator):
    def __init__(self, generator: PromptGenerator, min_attention=0.1, max_attention=0.9):
        import spacy
        self._nlp = spacy.load("en_core_web_sm")
        self._prompt_generator = generator
        m, M = min(min_attention, max_attention), max(min_attention, max_attention)
        self._min_attention, self._max_attention = m, M
        
    def _add_emphasis(self, prompt):
        doc = self._nlp(prompt)
        keywords = [k for k in doc.noun_chunks]
        if len(keywords) == 0:
            return prompt

        keyword = random.choice(keywords)
        attention = round(random.uniform(self._min_attention, self._max_attention), 2)
        prompt = prompt.replace(str(keyword), f"({keyword}:{attention})")

        return prompt

    def generate(self, *args, **kwargs) -> list[str]:
        prompts = self._prompt_generator.generate(*args, **kwargs)
        new_prompts = [self._add_emphasis(p) for p in prompts]
        
        return new_prompts

        
