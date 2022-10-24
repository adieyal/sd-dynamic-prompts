import os
from pathlib import Path
import logging
import math
import re, random
import pathlib
from typing import Set

import gradio as gr
import modules.scripts as scripts

from modules.processing import process_images, fix_seed, Processed
from modules.shared import opts

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

WILDCARD_DIR = getattr(opts, "wildcard_dir", "scripts/wildcards")
MAX_RECURSIONS = 20
VERSION = "0.5.0"

re_wildcard = re.compile(r"__(.*?)__")
re_combinations = re.compile(r"\{([^{}]*)}")

DEFAULT_NUM_COMBINATIONS = 1

def replace_combinations(match):
    if match is None or len(match.groups()) == 0:
        logger.warning("Unexpected missing combination")
        return ""

    variants = [s.strip() for s in match.groups()[0].split("|")]
    if len(variants) > 0:
        first = variants[0].split("$$")
        quantity = DEFAULT_NUM_COMBINATIONS
        if len(first) == 2: # there is a $$
            prefix_num, first_variant = first
            variants[0] = first_variant
            
            try:
                prefix_ints = [int(i) for i in prefix_num.split("-")]
                if len(prefix_ints) == 1:
                    quantity = prefix_ints[0]
                elif len(prefix_ints) == 2:
                    prefix_low = min(prefix_ints)
                    prefix_high = max(prefix_ints)
                    quantity = random.randint(prefix_low, prefix_high)
                else:
                    raise 
            except Exception:
                logger.warning(f"Unexpected combination formatting, expected $$ prefix to be a number or interval. Defaulting to {DEFAULT_NUM_COMBINATIONS}")
        
        try:
            picked = random.sample(variants, quantity)
            return ", ".join(picked)
        except ValueError as e:
            logger.exception(e)
            return ""

    return ""


def replace_wildcard(match):
    is_empty_line = lambda line: line is None or line.strip() == "" or line.strip().startswith("#")
    if match is None or len(match.groups()) == 0:
        logger.warning("Expected match to contain a filename")
        return ""

    wildcard_dir = Path(WILDCARD_DIR)
    if not wildcard_dir.exists():
        wildcard_dir.mkdir()

    wildcard = match.groups()[0]
    txt_files = list(pathlib.Path(wildcard_dir).rglob("*.txt"))

    replacement_files = []
    for path in txt_files:
        if wildcard in str(path.absolute()) or os.path.normpath(wildcard) in str(path.absolute()):
            replacement_files.append(str(path.absolute()))

    contents: Set = set()
    for replacement_file in replacement_files:
        if os.path.exists(replacement_file):
            with open(replacement_file, encoding="utf8", errors="ignore") as f:
                lines = [line.strip() for line in f if not is_empty_line(line)]
                contents.update(lines)
    options = list(contents)

    return random.choice(options)
    
def pick_wildcards(template):
    return re_wildcard.sub(replace_wildcard, template)


def pick_variant(template):
    if template is None:
        return None

    return re_combinations.sub(replace_combinations, template)

def generate_prompt(template):
    old_prompt = template
    counter = 0
    while True:
        counter += 1
        if counter > MAX_RECURSIONS:
            raise Exception("Too many recursions, something went wrong with generating the prompt")

        prompt = pick_variant(old_prompt)
        prompt = pick_wildcards(prompt)

        if prompt == old_prompt:
            logger.info(f"Prompt: {prompt}")
            return prompt
        old_prompt = prompt
        
class Script(scripts.Script):
    def title(self):
        return f"Dynamic Prompting v{VERSION}"

    def ui(self, is_img2img):
        html = f"""
            <h3><strong>Combinations</strong></h3>
            Choose a number of terms from a list, in this case we choose two artists
            <code>{{2$$artist1|artist2|artist3}}</code>
            If $$ is not provided, then 1$$ is assumed.
            <br>
            A range can be provided:
            <code>{{1-3$$artist1|artist2|artist3}}</code>
            In this case, a random number of artists between 1 and 3 is chosen.
            <br/><br/>

            <h3><strong>Wildcards</strong></h3>
            <p>Available wildcards</p>
            <ul style="overflow-y:auto;max-height:6rem;">
        """
        
        for path in Path(WILDCARD_DIR).rglob("*.txt"):
            filename = str(path.relative_to(WILDCARD_DIR))
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
        original_seed = p.seed
        
        num_images = p.n_iter * p.batch_size
        all_prompts = [
            generate_prompt(original_prompt) for _ in range(num_images)
        ]

        all_seeds = [int(p.seed) + (x if p.subseed_strength == 0 else 0) for x in range(num_images)]

        logger.info(f"Prompt matrix will create {len(all_prompts)} images in a total of {p.n_iter} batches.")

        p.prompt = all_prompts
        p.seed = all_seeds

        p.prompt_for_display = original_prompt
        processed = process_images(p)

        p.prompt = original_prompt
        p.seed = original_seed

        return processed
