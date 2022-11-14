from __future__ import annotations
from abc import ABC, abstractmethod
from prompts.generators.promptgenerator import PromptGenerator, GeneratorException
import requests
import random

class FeelingLuckyGenerator(PromptGenerator):
    def generate(self, num_prompts) -> str:
        r = random.randint(0, 10000000)
        url = f"https://lexica.art/api/v1/search?q={r}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            images = data["images"]
            prompts = random.choices(images, k=num_prompts)
            return [v["prompt"] for v in prompts]
        except Exception as e:
            raise GeneratorException("Error while generating prompt: " + str(e))


