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
    PromptGenerator,
    FeelingLuckyGenerator,
    DummyGenerator
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

VERSION = "0.27.3"


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
    def _create_generator(self, original_prompt, original_seed, is_dummy=False, is_feeling_lucky=False, enable_jinja_templates=False, is_combinatorial=False, is_magic_prompt=False, combinatorial_batches=1, magic_prompt_length=100, magic_temp_value=0.7):
        if is_dummy:
            return DummyGenerator(original_prompt)
        elif is_feeling_lucky:
            generator = FeelingLuckyGenerator(original_prompt)
        elif enable_jinja_templates:
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

        return generator
    
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
                is_enabled = gr.Checkbox(label="Dynamic Prompts enabled", value=True)

                with gr.Group():
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

                with gr.Group():
                    is_magic_prompt = gr.Checkbox(
                        label="Magic prompt", value=False, elem_id="is-magicprompt"
                    )
                    magic_prompt_length = gr.Slider(
                        label="Max magic prompt length",
                        value=100,
                        minimum=30,
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

                is_feeling_lucky = gr.Checkbox(
                    label="I'm feeling lucky", value=False, elem_id="is-feelinglucky"
                )

                
                write_prompts = gr.Checkbox(
                    label="Write prompts to file", value=False, elem_id="write-prompts"
                )

                no_image_generation = gr.Checkbox(
                    label="Don't generate images", value=False, elem_id="no-image-generation"
                )

                with gr.Accordion("Help", open=False):
                    info = gr.HTML(html)

                with gr.Group():
                    with gr.Accordion("Jinja2 templates", open=False):
                        enable_jinja_templates = gr.Checkbox(
                            label="Enable Jinja2 templates", value=False, elem_id="enable-jinja-templates"
                        )

                        with gr.Accordion("Help for Jinja2 templates", open=False):
                            jinja_info = gr.HTML(jinja_help)

                with gr.Group():
                    with gr.Accordion("Advanced options", open=False):
                        unlink_seed_from_prompt = gr.Checkbox(
                            label="Unlink seed from prompt", value=False, elem_id="unlink-seed-from-prompt"
                        )

                        disable_negative_prompt = gr.Checkbox(
                            label="Disable negative prompt", value=False, elem_id="disable-negative-prompt"
                        )

                        use_fixed_seed = gr.Checkbox(
                           label="Fixed seed", value=False, elem_id="is-fixed-seed"
                        )

                        

        return [
            info,
            is_enabled,
            is_combinatorial,
            combinatorial_batches,
            is_magic_prompt,
            is_feeling_lucky,
            magic_prompt_length,
            magic_temp_value,
            use_fixed_seed,
            write_prompts,
            unlink_seed_from_prompt,
            disable_negative_prompt,
            enable_jinja_templates,
            no_image_generation
        ]

    def process_batch(self, p,
        info,
        is_enabled,
        is_combinatorial,
        combinatorial_batches,
        is_magic_prompt,
        is_feeling_lucky,
        magic_prompt_length,
        magic_temp_value,
        use_fixed_seed,
        write_prompts,
        unlink_seed_from_prompt,
        disable_negative_prompt,
        enable_jinja_templates,
        no_image_generation,
        *args,
        **kwargs
    ):
        if not is_enabled:
            return p
        
        generator = self._negative_prompt_generator

        try:
            p.negative_prompt = generator.generate(1)[0]
        except GeneratorException as e:
            logger.exception(e)
            all_prompts = [str(e)]
            p.negative_prompt = str(e)

    def process(
        self,
        p,
        info,
        is_enabled,
        is_combinatorial,
        combinatorial_batches,
        is_magic_prompt,
        is_feeling_lucky,
        magic_prompt_length,
        magic_temp_value,
        use_fixed_seed,
        write_prompts,
        unlink_seed_from_prompt,
        disable_negative_prompt,
        enable_jinja_templates,
        no_image_generation,
    ):

        if not is_enabled:
            return p

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
            generator = self._create_generator(
                original_prompt,
                original_seed,
                is_feeling_lucky=is_feeling_lucky,
                enable_jinja_templates=enable_jinja_templates,
                is_combinatorial=is_combinatorial,
                is_magic_prompt=is_magic_prompt,
                combinatorial_batches=combinatorial_batches,
                magic_prompt_length=magic_prompt_length,
                magic_temp_value=magic_temp_value,
                is_dummy=False
            )

        
            self._negative_prompt_generator = self._create_generator(
                p.negative_prompt,
                original_seed,
                is_feeling_lucky=is_feeling_lucky,
                enable_jinja_templates=enable_jinja_templates,
                is_combinatorial=is_combinatorial,
                is_magic_prompt=is_magic_prompt,
                combinatorial_batches=combinatorial_batches,
                magic_prompt_length=magic_prompt_length,
                magic_temp_value=magic_temp_value,
                is_dummy=disable_negative_prompt,
            )

            all_prompts = generator.generate(num_images)
            p.negative_prompt = self._negative_prompt_generator.generate(1)[0]
            
        except GeneratorException as e:
            logger.exception(e)
            all_prompts = [str(e)]
            p.negative_prompt = str(e)
             

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
                prompt_filename.write_text("\n".join(all_prompts), encoding=constants.DEFAULT_ENCODING, errors="ignore")
        except Exception as e:
            logger.error(f"Failed to write prompts to file: {e}")

        p.all_prompts = all_prompts
        if no_image_generation:
            # Need a minimum of batch size images to avoid errors
            p.batch_size = 1
            p.all_prompts = all_prompts[0:1]

        p.all_seeds = all_seeds

        p.prompt_for_display = original_prompt

        p.prompt = original_prompt
        p.seed = original_seed


wildcard_manager.ensure_directory()
