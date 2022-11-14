import re

from .promptgenerator import PromptGenerator

re_wildcard = re.compile(r"__(.*?)__")
re_combinations = re.compile(r"\{([^{}]*)}")

from .randomprompt import RandomPromptGenerator
from .combinatorial import CombinatorialPromptGenerator
from .magicprompt import MagicPromptGenerator
from .batched_combinatorial import BatchedCombinatorialPromptGenerator
from .feelinglucky import FeelingLuckyGenerator