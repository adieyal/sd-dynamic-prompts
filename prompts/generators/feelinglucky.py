from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from prompts.generators.promptgenerator import PromptGenerator, GeneratorException
import requests
import random

logger = logging.getLogger(__name__)

class FeelingLuckyGenerator(PromptGenerator):
    def __init__(self, search_query):
        self._search_query = search_query

    def generate(self, num_prompts) -> str:
        if self._search_query.strip() == "":
            query = random.randint(0, 10000000)
        else:
            query = self._search_query

        url = f"https://lexica.art/api/v1/search?q={query}"
        
        try:
            logger.info(f"Requesting {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            images = data["images"]
            prompts = random.choices(images, k=num_prompts)
            return [v["prompt"] for v in prompts]
        except Exception as e:
            raise GeneratorException("Error while generating prompt: " + str(e))


