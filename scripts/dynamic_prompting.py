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
    PromptGenerator
)

from prompts.generators.jinjagenerator import JinjaGenerator
from prompts.generators.promptgenerator import GeneratorException
from prompts import constants

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

base_dir = Path(scripts.basedir())

wildcard_dir = getattr(opts, "wildcard_dir", None)

if wildcard_dir is None:
    WILDCARD_DIR = base_dir / "wildcards"
else:
    WILDCARD_DIR = Path(wildcard_dir)

VERSION = "0.19.2"


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
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")


def get_unique_path(directory: Path, original_filename) -> Path:
    filename = original_filename
    for i in range(1000):
        path = (directory / filename).with_suffix(".txt")
        if not path.exists():
            return path
        filename = f"{slugify(original_filename)}-{math.floor(random.random() * 1000)}"

    raise Exception("Failed to find unique path")


def old_generation(
    original_prompt: str,
    is_combinatorial: bool,
    combinatorial_batches: int,
    original_seed: int,

) -> PromptGenerator:
    if is_combinatorial:
        prompt_generator = CombinatorialPromptGenerator(
            wildcard_manager, original_prompt
        )
        prompt_generator = BatchedCombinatorialPromptGenerator(
            prompt_generator, combinatorial_batches
        )
    else:
        prompt_generator = RandomPromptGenerator(
            wildcard_manager, original_prompt, original_seed
        )

    return prompt_generator
    

def new_generation(prompt) -> PromptGenerator:
    generator = JinjaGenerator(prompt, wildcard_manager)
    return generator

class Script(scripts.Script):
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

        jinja_html_path = base_dir / "jinja_help.html"
        jinja_help = jinja_html_path.open().read()

        with gr.Group():
            with gr.Accordion("Dynamic Prompts", open=False):
                is_combinatorial = gr.Checkbox(
                    label="Combinatorial generation",
                    value=False,
                    elem_id="is-combinatorial",
                )
                combinatorial_batches = gr.Slider(
                    label="Combinatorial batches",
                    min=1,
                    max=10,
                    step=1,
                    value=1,
                    elem_id="combinatorial-times",
                )

                is_magic_prompt = gr.Checkbox(
                    label="Magic prompt", value=False, elem_id="is-magicprompt"
                )
                magic_prompt_length = gr.Slider(
                    label="Max magic prompt length",
                    value=100,
                    minimum=1,
                    maximum=300,
                    step=10,
                )
                magic_temp_value = gr.Slider(
                    label="Magic prompt creativity",
                    value=0.7,
                    minimum=0.1,
                    maximum=3.0,
                    step=0.10,
                )

                use_fixed_seed = gr.Checkbox(
                    label="Fixed seed", value=False, elem_id="is-fixed-seed"
                )
                write_prompts = gr.Checkbox(
                    label="Write prompts to file", value=False, elem_id="write-prompts"
                )

                info = gr.HTML(html)

                with gr.Group():
                    with gr.Accordion("Advanced options", open=False):
                        unlink_seed_from_prompt = gr.Checkbox(
                            label="Unlink seed from prompt", value=False, elem_id="unlink-seed-from-prompt"
                        )

                        enable_jinja_templates = gr.Checkbox(
                            label="Enable Jinja2 templates", value=False, elem_id="enable-jinja-templates"
                        )

                        jinja_info = gr.HTML(jinja_help)

        return [
            info,
            is_combinatorial,
            combinatorial_batches,
            is_magic_prompt,
            magic_prompt_length,
            magic_temp_value,
            use_fixed_seed,
            write_prompts,
            unlink_seed_from_prompt,
            enable_jinja_templates,
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
        unlink_seed_from_prompt,
        enable_jinja_templates,
    ):
        fix_seed(p)

        original_prompt = p.prompt[0] if type(p.prompt) == list else p.prompt
        original_seed = p.seed
        num_images = p.n_iter * p.batch_size

        if unlink_seed_from_prompt:
            constants.UNLINK_SEED_FROM_PROMPT = True

        try:
            combinatorial_batches = int(combinatorial_batches)
            if combinatorial_batches < 1:
                combinatorial_batches = 1
        except (ValueError, TypeError):
            combinatorial_batches = 1

        try:
            
            if enable_jinja_templates:
                generator = new_generation(original_prompt)
                
            else:
                generator = old_generation(
                    original_prompt,
                    is_combinatorial,
                    combinatorial_batches,
                    original_seed,
                )

            if is_magic_prompt:
                generator = MagicPromptGenerator(
                    generator, magic_prompt_length, magic_temp_value
                )

            all_prompts = generator.generate(num_images)
            
        except GeneratorException as e:
            logger.exception(e)
            all_prompts = [str(e)]
             

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
                prompt_filename = get_unique_path(
                    Path(p.outpath_samples), slugify(original_prompt)
                )
                prompt_filename.write_text("\n".join(all_prompts))
        except Exception as e:
            logger.error(f"Failed to write prompts to file: {e}")

        p.all_prompts = all_prompts
        p.all_seeds = all_seeds

        p.prompt_for_display = original_prompt

        p.prompt = original_prompt
        p.seed = original_seed


wildcard_manager.ensure_directory()
