from abc import ABC, abstractmethod
import re

class PromptGenerator(ABC):
    @abstractmethod
    def generate(self, *args, **kwargs) -> str:
        pass


