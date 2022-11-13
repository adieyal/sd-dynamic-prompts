from __future__ import annotations
from abc import ABC, abstractmethod
import re

class PromptGenerator(ABC):
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        pass


class GeneratorException(Exception):
    pass