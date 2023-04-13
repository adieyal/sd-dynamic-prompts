from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_seeds(
    p,
    num_seeds,
    use_fixed_seed,
    is_combinatorial=False,
    combinatorial_batches=1,
):
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


def load_magicprompt_models(modelfile: str) -> list[str]:
    try:
        models = []
        with open(modelfile) as f:
            for line in f:
                # ignore comments and empty lines
                line = line.split("#")[0].strip()
                if line:
                    models.append(line)
        return models
    except FileNotFoundError:
        logger.warning(f"Could not find magicprompts config file at {modelfile}")
        return []


def get_magicmodels_path(base_dir: str) -> str:
    magicprompt_models_path = Path(base_dir / "config" / "magicprompt_models.txt")

    return magicprompt_models_path
