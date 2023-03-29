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

    seeds, subseeds = get_seeds(processing, num_seeds, use_fixed_seed=True)
    assert seeds == [processing.seed] * num_seeds
    assert subseeds == [processing.subseed] * num_seeds

    processing.subseed_strength = 0.5

    seeds, subseeds = get_seeds(processing, num_seeds, use_fixed_seed=True)
    assert seeds == [processing.all_seeds[0]] * num_seeds
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
