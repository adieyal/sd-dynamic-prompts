import os
import tempfile
from unittest import mock

import pytest

from sd_dynamic_prompts.helpers import get_seeds, load_magicprompt_models


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

    image_seeds, image_subseeds, _ = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
    )
    assert image_seeds == [processing.seed] * num_seeds
    assert image_subseeds == [processing.subseed] * num_seeds

    processing.subseed_strength = 0.5

    image_seeds, image_subseeds, _ = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
    )
    assert image_seeds == [processing.all_seeds[0]] * num_seeds
    assert image_subseeds == [processing.all_subseeds[0]] * num_seeds


def test_get_seeds_with_fixed_seed_batched_combinatorial(processing):
    num_seeds = 10
    combinatorial_batches = 3
    image_seeds, image_subseeds, _ = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
        is_combinatorial=True,
        combinatorial_batches=combinatorial_batches,
    )
    seed0 = processing.seed
    assert image_seeds == (
        [seed0] * (num_seeds // 3)
        + [seed0 + 1] * (num_seeds // 3)
        + [seed0 + 2] * (num_seeds // 3)
    )
    assert image_subseeds == [processing.subseed] * num_seeds

    processing.subseed_strength = 0.5

    image_seeds, image_subseeds, _ = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=True,
        is_combinatorial=True,
        combinatorial_batches=combinatorial_batches,
    )
    seed0 = processing.all_seeds[0]
    assert image_seeds == (
        [seed0] * (num_seeds // 3)
        + [seed0 + 1] * (num_seeds // 3)
        + [seed0 + 2] * (num_seeds // 3)
    )
    assert image_subseeds == [processing.all_subseeds[0]] * num_seeds


def test_get_seeds_with_random_seed(processing):
    num_seeds = 10

    image_seeds, image_subseeds = processing.seed, processing.subseed
    seeds, subseeds, _ = get_seeds(
        processing,
        num_seeds=num_seeds,
        use_fixed_seed=False,
    )
    assert seeds == list(range(image_seeds, image_seeds + num_seeds))
    assert subseeds == list(range(image_subseeds, image_subseeds + num_seeds))

    processing.subseed_strength = 0.5

    image_seeds, image_subseeds = processing.all_seeds[0], processing.all_subseeds[0]
    seeds, subseeds, _ = get_seeds(
        processing,
        num_seeds=num_seeds,
        use_fixed_seed=False,
    )
    assert seeds == [image_seeds] * num_seeds
    assert subseeds == list(range(image_subseeds, image_subseeds + num_seeds))


@pytest.mark.parametrize("use_fixed_seed", [True, False])
def test_get_with_unlinked_seed(processing, use_fixed_seed):
    num_seeds = 10

    image_seeds, _, prompt_seeds = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=use_fixed_seed,
        unlink_seed_from_prompt=False,
    )
    assert image_seeds == prompt_seeds

    image_seeds, _, prompt_seeds = get_seeds(
        processing,
        num_seeds,
        use_fixed_seed=use_fixed_seed,
        unlink_seed_from_prompt=True,
    )
    assert image_seeds != prompt_seeds


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
