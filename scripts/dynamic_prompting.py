from __future__ import annotations
import logging
from string import Template
from pathlib import Path
import math
import re

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
    DummyGenerator,
    AttentionGenerator,
)

from prompts.generators.jinjagenerator import JinjaGenerator
from prompts.generators.promptgenerator import GeneratorException
from prompts import constants
from prompts.utils import slugify, get_unique_path
from prompts import prompt_writer
from ui import wildcards_tab


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

is_debug = getattr(opts, "is_debug", False)
if is_debug:
    logger.setLevel(logging.DEBUG)

base_dir = Path(scripts.basedir())

wildcard_dir = getattr(opts, "wildcard_dir", None)


if wildcard_dir is None:
    WILDCARD_DIR = base_dir / "wildcards"
else:
    WILDCARD_DIR = Path(wildcard_dir)

VERSION = "1.5.5"


wildcard_manager = WildcardManager(WILDCARD_DIR)
wildcards_tab.initialize(wildcard_manager)


def old_generation(
    original_prompt: str,
    is_combinatorial: bool,
    combinatorial_batches: int,
    original_seed: int,
    unlink_seed_from_prompt: bool = False,
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
            wildcard_manager, original_prompt, original_seed, unlink_seed_from_prompt
        )

    return prompt_generator


def new_generation(prompt, p) -> PromptGenerator:
    context = {
        "model": {
            "filename": p.sd_model.sd_checkpoint_info.filename,
            "title": p.sd_model.sd_checkpoint_info.title,
            "hash": p.sd_model.sd_checkpoint_info.hash,  
            "model_name": p.sd_model.sd_checkpoint_info.model_name,
        },
        "image": {
            "width": p.width,
            "height": p.height,
        },
        "parameters": {
            "steps": p.steps,
            "batch_size": p.batch_size,
            "num_batches": p.n_iter,
            "width": p.width,
            "height": p.height,
            "cfg_scale": p.cfg_scale,
            "sampler_name": p.sampler_name,
            "seed": p.seed,
        },
        "prompt": {
            "prompt": prompt,
            "negative_prompt": p.negative_prompt,
        }
    }

    generator = JinjaGenerator(prompt, wildcard_manager, context)
    return generator


# https://stackoverflow.com/a/241506
def strip_comments(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " " # note: a space and not an empty string
        else:
            return s
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, text)


class Script(scripts.Script):
    def _create_generator(
        self,
        original_prompt,
        original_seed,
        is_dummy=False,
        is_feeling_lucky=False,
        is_attention_grabber=False,
        min_attention=0.1,
        max_attention=0.5,
        enable_jinja_templates=False,
        is_combinatorial=False,
        is_magic_prompt=False,
        combinatorial_batches=1,
        magic_prompt_length=100,
        magic_temp_value=0.7,
        unlink_seed_from_prompt=constants.UNLINK_SEED_FROM_PROMPT,
    ):
        logger.debug(
            f"""
        Creating generator:
            original_prompt: {original_prompt}
            original_seed: {original_seed}
            is_dummy: {is_dummy}
            is_feeling_lucky: {is_feeling_lucky}
            enable_jinja_templates: {enable_jinja_templates}
            is_combinatorial: {is_combinatorial}
            is_magic_prompt: {is_magic_prompt}
            combinatorial_batches: {combinatorial_batches}
            magic_prompt_length: {magic_prompt_length}
            magic_temp_value: {magic_temp_value}
            unlink_seed_from_prompt: {unlink_seed_from_prompt}
            is_attention_grabber: {is_attention_grabber}
            min_attention: {min_attention}
            max_attention: {max_attention}

        """
        )

        if is_dummy:
            return DummyGenerator(original_prompt)
        elif is_feeling_lucky:
            generator = FeelingLuckyGenerator(original_prompt)
        elif enable_jinja_templates:
            generator = new_generation(original_prompt, self._p)
        else:
            generator = old_generation(
                original_prompt,
                is_combinatorial,
                combinatorial_batches,
                original_seed,
                unlink_seed_from_prompt,
            )

        if is_magic_prompt:
            generator = MagicPromptGenerator(
                generator, magic_prompt_length, magic_temp_value, seed=original_seed
            )

        if is_attention_grabber:
            generator = AttentionGenerator(generator, min_attention=min_attention, max_attention=max_attention)
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

        with gr.Group(elem_id="dynamic-prompting"):
            with gr.Accordion("Dynamic Prompts", open=False):
                is_enabled = gr.Checkbox(
                    label="Dynamic Prompts enabled",
                    value=True,
                    elem_id="dynamic-prompts-enabled",
                )

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

                with gr.Box():
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
                        label="I'm feeling lucky",
                        value=False,
                        elem_id="is-feelinglucky",
                    )

                with gr.Group():
                    is_attention_grabber = gr.Checkbox(
                        label="Attention grabber",
                        value=False,
                        elem_id="is-attention-grabber",
                    )

                    min_attention = gr.Slider(
                        label="Minimum attention",
                        value=1.1,
                        minimum=-1,
                        maximum=2,
                        step=0.1,
                    )

                    max_attention = gr.Slider(
                        label="Maximum attention",
                        value=1.5,
                        minimum=-1,
                        maximum=2,
                        step=0.1,
                    )

                write_prompts = gr.Checkbox(
                    label="Write prompts to file", value=False, elem_id="write-prompts"
                )

                no_image_generation = gr.Checkbox(
                    label="Don't generate images",
                    value=False,
                    elem_id="no-image-generation",
                )

                enable_comments = gr.Checkbox(
                    label="Enable comments",
                    value=False,
                    elem_id="enable-comments",
                )

                with gr.Accordion("Help", open=False):
                    info = gr.HTML(html)

                with gr.Group():
                    with gr.Accordion("Jinja2 templates", open=False):
                        enable_jinja_templates = gr.Checkbox(
                            label="Enable Jinja2 templates",
                            value=False,
                            elem_id="enable-jinja-templates",
                        )

                        with gr.Accordion("Help for Jinja2 templates", open=False):
                            jinja_info = gr.HTML(jinja_help)

                with gr.Group():
                    with gr.Accordion("Advanced options", open=False):
                        unlink_seed_from_prompt = gr.Checkbox(
                            label="Unlink seed from prompt",
                            value=False,
                            elem_id="unlink-seed-from-prompt",
                        )

                        disable_negative_prompt = gr.Checkbox(
                            label="Disable negative prompt",
                            value=False,
                            elem_id="disable-negative-prompt",
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
            is_attention_grabber,
            min_attention,
            max_attention,
            magic_prompt_length,
            magic_temp_value,
            use_fixed_seed,
            write_prompts,
            unlink_seed_from_prompt,
            disable_negative_prompt,
            enable_jinja_templates,
            no_image_generation,
            enable_comments,
        ]

    def process(
        self,
        p,
        info,
        is_enabled,
        is_combinatorial,
        combinatorial_batches,
        is_magic_prompt,
        is_feeling_lucky,
        is_attention_grabber,
        min_attention,
        max_attention,
        magic_prompt_length,
        magic_temp_value,
        use_fixed_seed,
        write_prompts,
        unlink_seed_from_prompt,
        disable_negative_prompt,
        enable_jinja_templates,
        no_image_generation,
        enable_comments,
    ):

        if not is_enabled:
            logger.debug("Dynamic prompts disabled - exiting")
            return p
        
        self._p = p

        fix_seed(p)

        original_prompt = p.all_prompts[0] if len(p.all_prompts) > 0 else p.prompt
        original_negative_prompt = (
            p.all_negative_prompts[0]
            if len(p.all_negative_prompts) > 0
            else p.negative_prompt
        )

        original_seed = p.seed
        num_images = p.n_iter * p.batch_size

        try:
            combinatorial_batches = int(combinatorial_batches)
            if combinatorial_batches < 1:
                combinatorial_batches = 1
        except (ValueError, TypeError):
            combinatorial_batches = 1

        if enable_comments:
            original_prompt = strip_comments(original_prompt)
            original_negative_prompt = strip_comments(original_negative_prompt)
        
        try:
            logger.debug("Creating positive generator")
            generator = self._create_generator(
                original_prompt,
                original_seed,
                is_feeling_lucky=is_feeling_lucky,
                is_attention_grabber=is_attention_grabber,
                enable_jinja_templates=enable_jinja_templates,
                is_combinatorial=is_combinatorial,
                is_magic_prompt=is_magic_prompt,
                combinatorial_batches=combinatorial_batches,
                magic_prompt_length=magic_prompt_length,
                magic_temp_value=magic_temp_value,
                is_dummy=False,
                unlink_seed_from_prompt=unlink_seed_from_prompt,
            )

            logger.debug("Creating negative generator")
            negative_prompt_generator = self._create_generator(
                original_negative_prompt,
                original_seed,
                is_feeling_lucky=is_feeling_lucky,
                is_attention_grabber=is_attention_grabber,
                enable_jinja_templates=enable_jinja_templates,
                is_combinatorial=is_combinatorial,
                is_magic_prompt=is_magic_prompt,
                combinatorial_batches=combinatorial_batches,
                magic_prompt_length=magic_prompt_length,
                magic_temp_value=magic_temp_value,
                is_dummy=disable_negative_prompt,
                unlink_seed_from_prompt=unlink_seed_from_prompt,
            )

            all_prompts = generator.generate(num_images)
            all_negative_prompts = negative_prompt_generator.generate(num_images)
            total_prompts = len(all_prompts)

            if len(all_negative_prompts) < total_prompts:
                all_negative_prompts = all_negative_prompts * (
                    total_prompts // len(all_negative_prompts) + 1
                )

            all_negative_prompts = all_negative_prompts[:total_prompts]

        except GeneratorException as e:
            logger.exception(e)
            all_prompts = [str(e)]
            all_negative_prompts = [str(e)]

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
                    Path(p.outpath_samples), slugify(original_prompt), suffix="csv"
                )
                prompt_writer.write_prompts(prompt_filename, original_prompt, original_negative_prompt, all_prompts, all_negative_prompts)
        except Exception as e:
            logger.error(f"Failed to write prompts to file: {e}")

        p.all_prompts = all_prompts
        p.all_negative_prompts = all_negative_prompts
        if no_image_generation:
            logger.debug("No image generation requested - exiting")
            # Need a minimum of batch size images to avoid errors
            p.batch_size = 1
            p.all_prompts = all_prompts[0:1]

        p.all_seeds = all_seeds

        p.prompt_for_display = original_prompt

        p.prompt = original_prompt
        p.seed = original_seed


wildcard_manager.ensure_directory()
