import logging
from string import Template
from pathlib import Path
import math

import gradio as gr

import modules.scripts as scripts
from modules.processing import process_images, fix_seed, Processed
from modules.shared import opts

from prompts.wildcardmanager import WildcardManager
from prompts.uicreation import UiCreation
from prompts.generators import RandomPromptGenerator, CombinatorialPromptGenerator, MagicPromptGenerator

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

WILDCARD_DIR = getattr(opts, "wildcard_dir", base_dir / "wildcards")
VERSION = "0.11.0"

base_dir = Path(scripts.basedir())

wildcard_manager = WildcardManager(WILDCARD_DIR)

class Script(scripts.Script):
    def title(self):
        return f"Dynamic Prompting v{VERSION}"

    def ui(self, is_img2img):
        ui_creation = UiCreation(wildcard_manager)
        wildcard_html = ui_creation.probe()

        html_path = base_dir / "helptext.html"
        html = html_path.open().read()
        html = Template(html).substitute(wildcard_html=wildcard_html, WILDCARD_DIR=WILDCARD_DIR)

        is_combinatorial = gr.Checkbox(label="Combinatorial generation", value=False, elem_id="is-combinatorial")
        is_magic_prompt = gr.Checkbox(label="Magic prompt", value=False, elem_id="is-magicprompt")
        info = gr.HTML(html)
        return [info, is_combinatorial, is_magic_prompt]

    def run(self, p, info, is_combinatorial, is_magic_prompt):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        original_seed = p.seed

        if is_combinatorial:
            prompt_generator = CombinatorialPromptGenerator(wildcard_manager, original_prompt)
        else:
            prompt_generator = RandomPromptGenerator(wildcard_manager, original_prompt, original_seed)

        if is_magic_prompt:
            prompt_generator = MagicPromptGenerator(prompt_generator)
        
        num_images = p.n_iter * p.batch_size
        all_prompts = prompt_generator.generate(num_images)
        updated_count = len(all_prompts)
        p.n_iter = math.ceil(updated_count / p.batch_size)

        all_seeds = [int(p.seed) + (x if p.subseed_strength == 0 else 0) for x in range(updated_count)]

        logger.info(f"Prompt matrix will create {updated_count} images in a total of {p.n_iter} batches.")

        p.prompt = all_prompts
        p.seed = all_seeds

        p.prompt_for_display = original_prompt
        processed = process_images(p)

        p.prompt = original_prompt
        p.seed = original_seed

        return processed

wildcard_manager.ensure_directory()
