import os
import tempfile
from unittest import mock

import pytest

from sd_dynamic_prompts.helpers import (
    generate_prompt_cross_product,
    generate_prompts,
    get_seeds,
    load_magicprompt_models,
)


@pytest.fixture
def processing():
    m = mock.Mock()
    m.seed = 1000
    m.subseed = 2000
    m.all_seeds = list(range(3000, 3000 + 10))
    m.all_subseeds = list(range(4000, 4000 + 10))
    m.subseed_strength = 0

    return m


def test_get_seeds_with_fixed_seed(processing):
    num_seeds = 10

    seeds, subseeds = get_seeds(processing, num_seeds, use_fixed_seed=True)
    assert seeds == [processing.seed] * num_seeds
    assert subseeds == [processing.subseed] * num_seeds

    processing.subseed_strength = 0.5

    seeds, subseeds = get_seeds(processing, num_seeds, use_fixed_seed=True)
    assert seeds == [processing.all_seeds[0]] * num_seeds
    assert subseeds == [processing.all_subseeds[0]] * num_seeds


def test_get_seeds_with_fixed_seed_batched_combinatorial(processing):
    num_seeds = 10
    combinatorial_batches = 3
    seeds, subseeds = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
        is_combinatorial=True,
        combinatorial_batches=combinatorial_batches,
    )
    seed0 = processing.seed
    assert seeds == (
        [seed0] * (num_seeds // 3)
        + [seed0 + 1] * (num_seeds // 3)
        + [seed0 + 2] * (num_seeds // 3)
    )
    assert subseeds == [processing.subseed] * num_seeds

    processing.subseed_strength = 0.5

    seeds, subseeds = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
        is_combinatorial=True,
        combinatorial_batches=combinatorial_batches,
    )
    seed0 = processing.all_seeds[0]
    assert seeds == (
        [seed0] * (num_seeds // 3)
        + [seed0 + 1] * (num_seeds // 3)
        + [seed0 + 2] * (num_seeds // 3)
    )
    assert subseeds == [processing.all_subseeds[0]] * num_seeds


def test_get_seeds_with_random_seed(processing):
    num_seeds = 10

    seed, subseed = processing.seed, processing.subseed
    seeds, subseeds = get_seeds(processing, num_seeds=num_seeds, use_fixed_seed=False)
    assert seeds == list(range(seed, seed + num_seeds))
    assert subseeds == list(range(subseed, subseed + num_seeds))

    processing.subseed_strength = 0.5

    seed, subseed = processing.all_seeds[0], processing.all_subseeds[0]
    seeds, subseeds = get_seeds(processing, num_seeds=num_seeds, use_fixed_seed=False)
    assert seeds == [seed] * num_seeds
    assert subseeds == list(range(subseed, subseed + num_seeds))


def test_load_magicprompt_models():
    s = """# a comment
model1 # another comment
# empty lines below


model 2


    """

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
        tmp_file.write(s)
        tmp_filename = tmp_file.name

    try:
        load_magicprompt_models(tmp_filename)
    finally:
        os.unlink(tmp_filename)


def test_cross_product():
    prompts = []
    negative_prompts = []
    expected_output = [], []
    assert generate_prompt_cross_product(prompts, negative_prompts) == expected_output

    prompts = ["A", "B", "C"]
    negative_prompts = ["X", "Y"]
    expected_output = (["A", "A", "B", "B", "C", "C"], ["X", "Y", "X", "Y", "X", "Y"])
    assert generate_prompt_cross_product(prompts, negative_prompts) == expected_output


@pytest.mark.parametrize("num_prompts", [5, None])
def test_generate_with_num_prompts(num_prompts: int | None):
    prompt_generator = mock.Mock()
    negative_prompt_generator = mock.Mock()
    prompt_generator.generate.return_value = [
        "Positive Prompt 1",
        "Positive Prompt 2",
        "Positive Prompt 3",
        "Positive Prompt 4",
        "Positive Prompt 5",
    ]
    negative_prompt_generator.generate.return_value = [
        "Negative Prompt 1",
        "Negative Prompt 2",
    ]
    prompt = "This is a positive prompt."
    negative_prompt = "This is a negative prompt."
    seeds = [1, 2, 3, 4, 5]

    positive_prompts, negative_prompts = generate_prompts(
        prompt_generator,
        negative_prompt_generator,
        prompt,
        negative_prompt,
        num_prompts,
        seeds,
    )

    if num_prompts:
        assert positive_prompts == [
            "Positive Prompt 1",
            "Positive Prompt 2",
            "Positive Prompt 3",
            "Positive Prompt 4",
            "Positive Prompt 5",
        ]
        assert negative_prompts == [
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
        ]
    else:
        assert positive_prompts == [
            "Positive Prompt 1",
            "Positive Prompt 1",
            "Positive Prompt 2",
            "Positive Prompt 2",
            "Positive Prompt 3",
            "Positive Prompt 3",
            "Positive Prompt 4",
            "Positive Prompt 4",
            "Positive Prompt 5",
            "Positive Prompt 5",
        ]
        assert negative_prompts == [
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
            "Negative Prompt 2",
            "Negative Prompt 1",
            "Negative Prompt 2",
        ]
