import os
from glob import glob
from pathlib import Path
import logging
import math
import re, random

import gradio as gr
import modules.scripts as scripts

from modules.processing import process_images, fix_seed
from modules.shared import opts

logger = logging.getLogger(__name__)

WILDCARD_DIR = getattr(opts, "wildcard_dir", "scripts/wildcards")

re_wildcard = re.compile(r"__([^_]*)__")
re_combinations = re.compile(r"\{([^{}]*)}")

DEFAULT_NUM_COMBINATIONS = 1

def replace_combinations(match):
    if match is None or len(match.groups()) == 0:
        logger.warning("Unexpected missing combination")
        return ""

    variants = [s.strip() for s in match.groups()[0].split("|")]
    if len(variants) > 0:
        first = variants[0].split("$$")
        num = DEFAULT_NUM_COMBINATIONS
        if len(first) == 2:
            num, first_variant = first
            variants[0] = first_variant
            try:
                num = int(num)
            except ValueError:
                logger.warning("Unexpected combination formatting, expected $$ prefix to be a number")
                num = DEFAULT_NUM_COMBINATIONS
        
        try:
            picked = random.sample(variants, num)
            return ",".join(picked)
        except ValueError as e:
            logger.exception(e)
            return ""

    return ""


def replace_wildcard(match):
    if match is None or len(match.groups()) == 0:
        logger.warning("Expected match to contain a filename")
        return ""

    wildcard_dir = Path(WILDCARD_DIR)
    if not wildcard_dir.exists():
        wildcard_dir.mkdir()

    wildcard = match.groups()[0]
    wildcard_path = wildcard_dir / f"{wildcard}.txt"

    if not wildcard_path.exists():
        logger.warning(f"Missing file {wildcard_path}")
        return ""

    options = [line.strip() for line in wildcard_path.open()]
    return random.choice(options)
    
def pick_wildcards(template):
    return re_wildcard.sub(replace_wildcard, template)


def pick_variant(template):
    """
    Generate random prompts given a template 
    This function was copied from the following colab, but I think it may have originated somewhere else: https://colab.research.google.com/drive/1P5MEMtLM3RGCqGfSQWs1cMntrMgSnKDe?usp=sharing#scrollTo=PAsdW6XqxVO_

    Template syntax

        Variations
            {opt1|opt2|opt3} : will randomly pick 1 of the options for every batch item.

            In this case, "opt1" or "opt2" or "opt3"

        Combinations
            [2$$opt1|opt2|opt3] : will randomly combine 2 of the options for every batch, separated with a comma

            In this case, "opt1, opt2" or "opt2, opt3", or "opt1, opt3" or the same pairs in the reverse order.

            The prefix (2$$) can use any number between 1 and the total number of options you defined

            NB : if you omit the size prefix, the number of options combined will be defined randomly

        Nesting
            You can have variations inside combinations but not the other way round (for now)

            Example:

            I love[ {red|white} wine | {layered|chocolate} cake | {german|belgian} beer]
    """
    if template is None:
        return None

    return re_combinations.sub(replace_combinations, template)

def generate_prompt(template):
    return pick_wildcards(pick_variant(template))


class Script(scripts.Script):
    def title(self):
        return "Dynamic Prompting"

    def ui(self, is_img2img):
        html = f"""
            <h3><strong>Combinations</strong></h3>
            Choose a number of terms from a list, in this case we choose two artists
            <code>{2$$artist1|artist2|artist3}</code>
            If $$ is not provided, then 1$$ is assumed.
            <br/><br/>

            <h3><strong>Wildcards</strong></h3>
            <p>Available wildcards</p>
            <ul>
        """
        
        for path in Path(WILDCARD_DIR).glob("*.txt"):
            filename = path.name
            wildcard = "__" + filename.replace(".txt", "") + "__"

            html += f"<li>{wildcard}</li>"

        html += "</ul>"
        html += f"""
            <br/>
            <code>WILDCARD_DIR: {WILDCARD_DIR}</code><br/>
            <small>You can add more wildcards by creating a text file with one term per line and name is mywildcards.txt. Place it in {WILDCARD_DIR}. <code>__mywildcards__</code> will then become available.</small>
        """
        info = gr.HTML(html)
        return [info]

    def run(self, p, info):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        

        all_prompts = [
            generate_prompt(original_prompt) for _ in range(p.n_iter)
        ]
        all_seeds = [int(p.seed) + (x if p.subseed_strength == 0 else 0) for x in range(len(all_prompts))]

        p.n_iter = math.ceil(len(all_prompts) / p.batch_size)
        p.do_not_save_grid = True

        print(f"Prompt matrix will create {len(all_prompts)} images using a total of {p.n_iter} batches.")

        p.prompt = all_prompts
        p.seed = all_seeds
        p.prompt_for_display = original_prompt
        processed = process_images(p)

        return processed
