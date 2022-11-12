from __future__ import annotations
import logging
from string import Template
from pathlib import Path
import math
import unicodedata
import re
import random

import gradio as gr

import modules.scripts as scripts
from modules.processing import process_images, fix_seed, Processed
from modules.shared import opts

from prompts.wildcardmanager import WildcardManager
from prompts.uicreation import UiCreation
from prompts.generators import (
    RandomPromptGenerator,
    CombinatorialPromptGenerator,
    MagicPromptGenerator,
    BatchedCombinatorialPromptGenerator,
)
from prompts import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

base_dir = Path(scripts.basedir())

wildcard_dir = getattr(opts, "wildcard_dir", None)

if wildcard_dir is None:
    WILDCARD_DIR = base_dir / "wildcards"
else:
    WILDCARD_DIR = Path(wildcard_dir)
    
VERSION = "0.17.1"


wildcard_manager = WildcardManager(WILDCARD_DIR)

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')

def get_unique_path(directory: Path, original_filename) -> Path:    
    filename = original_filename
    for i in range(1000):
        path = (directory / filename).with_suffix(".txt")
        if not path.exists():
            return path
        filename = f"{slugify(original_filename)}-{math.floor(random.random() * 1000)}"

    raise Exception("Failed to find unique path")

class Script(scripts.Script):
    original_negative_prompt = None
    
    def __init__(self):
        print(f"Script __init__ ;")

    def title(self):
        return f"Dynamic Prompts v{VERSION}"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        ui_creation = UiCreation(wildcard_manager)
        wildcard_html = ui_creation.probe()

        html_path = base_dir / "helptext.html"
        html = html_path.open().read()
        html = Template(html).substitute(
            wildcard_html=wildcard_html, WILDCARD_DIR=WILDCARD_DIR
        )

        with gr.Group():
            with gr.Accordion("Dynamic Prompts", open=False):
                is_combinatorial = gr.Checkbox(label="Combinatorial generation", value=False, elem_id="is-combinatorial")
                combinatorial_batches = gr.Slider(label="Combinatorial batches", min=1, max=10, step=1, value=1, elem_id="combinatorial-times")

                is_magic_prompt = gr.Checkbox(label="Magic prompt", value=False, elem_id="is-magicprompt")
                magic_prompt_length = gr.Slider(label="Max magic prompt length", value=100, minimum=1, maximum=300, step=10)
                magic_temp_value = gr.Slider(label="Magic prompt creativity", value=0.7, minimum=0.1, maximum=3.0, step=0.10)

                use_fixed_seed = gr.Checkbox(label="Fixed seed", value=False, elem_id="is-fixed-seed")
                write_prompts = gr.Checkbox(label="Write prompts to file", value=False, elem_id="write-prompts")
                UNLINK_SEED_FROM_PROMPT = gr.Checkbox(label='UNLINK_SEED_FROM_PROMPT', value=True, elem_id="is-wildcardRe")
                
                info = gr.HTML(html)

        return [
            info,
            is_combinatorial,
            combinatorial_batches,
            is_magic_prompt,
            magic_prompt_length,
            magic_temp_value,
            use_fixed_seed,
            write_prompts,
            UNLINK_SEED_FROM_PROMPT
        ]

    def process(
        self,
        p,
        info,
        is_combinatorial,
        combinatorial_batches,
        is_magic_prompt,
        magic_prompt_length,
        magic_temp_value,
        use_fixed_seed,
        write_prompts,
        UNLINK_SEED_FROM_PROMPT
    ):

        constants.UNLINK_SEED_FROM_PROMPT=UNLINK_SEED_FROM_PROMPT;
        
        fix_seed(p)
        
        #print(f"p.negative_prompt ; {p.negative_prompt}")

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        if self.original_negative_prompt is None :
            self.original_negative_prompt = p.negative_prompt[0] if type(p.negative_prompt) == list else p.negative_prompt
        original_seed = p.seed

        try:
            combinatorial_batches = int(combinatorial_batches)
            if combinatorial_batches < 1:
                combinatorial_batches = 1
        except (ValueError, TypeError):
            combinatorial_batches = 1

        if is_combinatorial:
            prompt_generator = CombinatorialPromptGenerator(
                wildcard_manager, original_prompt
            )
            prompt_generator = BatchedCombinatorialPromptGenerator(
                prompt_generator, combinatorial_batches
            )
            
            negative_prompt_generator = CombinatorialPromptGenerator(wildcard_manager, self.original_negative_prompt)
            negative_prompt_generator = BatchedCombinatorialPromptGenerator(negative_prompt_generator, combinatorial_batches)
        else:
            prompt_generator = RandomPromptGenerator(
                wildcard_manager, original_prompt, original_seed
            )
            
            negative_prompt_generator = RandomPromptGenerator(wildcard_manager, self.original_negative_prompt, original_seed)

        if is_magic_prompt:
            prompt_generator = MagicPromptGenerator(
                prompt_generator, magic_prompt_length, magic_temp_value
            )
            
            negative_prompt_generator = MagicPromptGenerator(negative_prompt_generator, magic_prompt_length, magic_temp_value)

        num_images = p.n_iter * p.batch_size
        all_prompts = prompt_generator.generate(num_images)
        all_negative_prompts = negative_prompt_generator.generate(1)[0]
        updated_count = len(all_prompts)
        p.n_iter = math.ceil(updated_count / p.batch_size)

        if use_fixed_seed:
            all_seeds = [original_seed] * updated_count
        else:
            all_seeds = [
                int(p.seed) + (x if p.subseed_strength == 0 else 0)
                for x in range(updated_count)
            ]

        logger.info(
            f"Prompt matrix will create {updated_count} images in a total of {p.n_iter} batches."
        )

        try:
            if write_prompts:
                prompt_filename = get_unique_path(Path(p.outpath_samples), slugify(original_prompt))
                prompt_filename.write_text("\n".join(all_prompts))
        except Exception as e:
            logger.error(f"Failed to write prompts to file: {e}")

        p.all_prompts = all_prompts
        p.negative_prompt = all_negative_prompts
        p.all_seeds = all_seeds
        
        #print(f"p.negative_prompt ; {p.negative_prompt}")

        p.prompt_for_display = original_prompt

        p.prompt = original_prompt
        p.seed = original_seed



wildcard_manager.ensure_directory()
