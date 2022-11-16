import re

from .promptgenerator import PromptGenerator

re_wildcard = re.compile(r"__(.*?)__")
re_combinations = re.compile(r"\{([^{}]*)}")

from .batched_combinatorial import BatchedCombinatorialPromptGenerator
from .combinatorial import CombinatorialPromptGenerator
from .dummygenerator import DummyGenerator
from .feelinglucky import FeelingLuckyGenerator
from .magicprompt import MagicPromptGenerator
from .randomprompt import RandomPromptGenerator
from .attentiongenerator import AttentionGenerator