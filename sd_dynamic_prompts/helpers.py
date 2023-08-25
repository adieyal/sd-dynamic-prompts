from __future__ import annotations

import logging
from itertools import cycle, islice, product
from pathlib import Path

from dynamicprompts.generators.promptgenerator import PromptGenerator

from sd_dynamic_prompts.paths import get_magicprompt_models_txt_path

logger = logging.getLogger(__name__)


def get_seeds(
    p,
    num_seeds,
    use_fixed_seed,
    is_combinatorial=False,
    combinatorial_batches=1,
) -> tuple[list[int], list[int]]:
    if p.subseed_strength != 0:
        seed = int(p.all_seeds[0])
        subseed = int(p.all_subseeds[0])
    else:
        seed = int(p.seed)
        subseed = int(p.subseed)

    if use_fixed_seed:
        if is_combinatorial:
            all_seeds = []
            all_subseeds = [subseed] * num_seeds
            for i in range(combinatorial_batches):
                all_seeds.extend([seed + i] * (num_seeds // combinatorial_batches))
        else:
            all_seeds = [seed] * num_seeds
            all_subseeds = [subseed] * num_seeds
    else:
        if p.subseed_strength == 0:
            all_seeds = [seed + i for i in range(num_seeds)]
        else:
            all_seeds = [seed] * num_seeds

        all_subseeds = [subseed + i for i in range(num_seeds)]

    return all_seeds, all_subseeds


def should_freeze_prompt(p):
    # When using a variation seed, the prompt shouldn't change between generations
    return p.subseed_strength > 0


def load_magicprompt_models(models_file: Path | None = None) -> list[str]:
    if not models_file:
        models_file = get_magicprompt_models_txt_path()
    try:
        # ignore empty lines
        return [
            model
            for model in (
                line.partition("#")[0].strip()
                for line in models_file.read_text().splitlines()
            )
            if model
        ]
    except FileNotFoundError:
        logger.warning(f"Could not find magicprompts config file at {models_file}")
        return []


def generate_prompts(
    prompt_generator: PromptGenerator,
    negative_prompt_generator: PromptGenerator,
    prompt: str,
    negative_prompt: str | None,
    num_prompts: int,
    seeds: list[int] | None,
) -> tuple[list[str], list[str]]:
    """
    Generate positive and negative prompts.

    Parameters:
    - prompt_generator: Object that generates positive prompts.
    - negative_prompt_generator: Object that generates negative prompts.
    - prompt: Base text for positive prompts.
    - negative_prompt: Base text for negative prompts.
    - num_prompts: Number of prompts to generate.
    - seeds: List of seeds for prompt generation.

    Returns:
    - Tuple containing list of positive and negative prompts.
    """
    all_prompts = prompt_generator.generate(prompt, num_prompts, seeds=seeds) or [""]

    negative_seeds = seeds if negative_prompt else None

    all_negative_prompts = negative_prompt_generator.generate(
        negative_prompt,
        num_prompts,
        seeds=negative_seeds,
    ) or [""]

    if num_prompts is None:
        return generate_prompt_cross_product(all_prompts, all_negative_prompts)

    return all_prompts, repeat_iterable_to_length(all_negative_prompts, num_prompts)


def generate_prompt_cross_product(
    prompts: list[str],
    negative_prompts: list[str],
) -> tuple[list[str], list[str]]:
    """
    Create a cross product of all the items in `prompts` and `negative_prompts`.
    Return the positive prompts and negative prompts in two separate lists

    Parameters:
    - prompts: List of prompts
    - negative_prompts: List of negative prompts

    Returns:
    - Tuple containing list of positive and negative prompts
    """
    if not (prompts and negative_prompts):
        return [], []

    # noqa to remain compatible with python 3.9, see issue #601
    new_positive_prompts, new_negative_prompts = zip(
        *product(prompts, negative_prompts),  # noqa: B905
    )
    return list(new_positive_prompts), list(new_negative_prompts)


def repeat_iterable_to_length(iterable, length: int) -> list:
    """Repeat an iterable to a given length.

    If the iterable is shorter than the desired length, it will be repeated
    until it is long enough. If it is longer than the desired length, it will
    be truncated.

    Args:
        iterable (Iterable): The iterable to repeat.
        length (int): The desired length of the iterable.

    Returns:
        list: The repeated iterable.

    """
    return list(islice(cycle(iterable), length))
