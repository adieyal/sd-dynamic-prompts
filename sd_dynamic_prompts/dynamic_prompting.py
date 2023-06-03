from __future__ import annotations

import logging
import math
from functools import lru_cache
from pathlib import Path
from string import Template

import dynamicprompts
import gradio as gr
import modules.scripts as scripts
import torch
from dynamicprompts.generators.promptgenerator import GeneratorException
from dynamicprompts.parser.parse import ParserConfig
from dynamicprompts.wildcards import WildcardManager
from modules import devices
from modules.processing import fix_seed
from modules.shared import opts

from sd_dynamic_prompts import __version__, callbacks
from sd_dynamic_prompts.element_ids import make_element_id
from sd_dynamic_prompts.generator_builder import GeneratorBuilder
from sd_dynamic_prompts.helpers import (
    generate_prompts,
    get_magicmodels_path,
    get_seeds,
    load_magicprompt_models,
    should_freeze_prompt,
)
from sd_dynamic_prompts.pnginfo_saver import PngInfoSaver
from sd_dynamic_prompts.prompt_writer import PromptWriter

VERSION = __version__

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

is_debug = getattr(opts, "is_debug", False)

if is_debug:
    logger.setLevel(logging.DEBUG)

base_dir = Path(scripts.basedir())
magicprompt_models_path = get_magicmodels_path(base_dir)


def get_wildcard_dir() -> Path:
    wildcard_dir = getattr(opts, "wildcard_dir", None)
    if wildcard_dir is None:
        wildcard_dir = base_dir / "wildcards"
    wildcard_dir = Path(wildcard_dir)
    try:
        wildcard_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        logger.exception(f"Failed to create wildcard directory {wildcard_dir}")
    return wildcard_dir


def _get_effective_prompt(prompts: list[str], prompt: str) -> str:
    return prompts[0] if prompts else prompt


device = devices.device
# There might be a bug in auto1111 where the correct device is not inferred in some scenarios
if device.type == "cuda" and not device.index:
    device = torch.device("cuda:0")

loaded_count = 0


@lru_cache(maxsize=1)
def _get_install_error_message() -> str | None:
    try:
        from sd_dynamic_prompts.version_tools import get_dynamicprompts_install_result

        get_dynamicprompts_install_result().raise_if_incorrect()
    except RuntimeError as rte:
        return str(rte)
    except Exception:
        logger.exception("Failed to get dynamicprompts install result")
    return None


class Script(scripts.Script):
    def __init__(self):
        global loaded_count

        loaded_count += 1

        # This is a hack to make sure that the script is only loaded once
        # Auto1111 calls the script twice, once for the txt2img and once for img2img
        # These callbacks should only be registered once.

        # When the Reload UI button in the settings tab is pressed, the script is loaded twice again
        # Therefore we only register callbacks every second time the script is loaded
        self._pnginfo_saver = PngInfoSaver()
        self._prompt_writer = PromptWriter()
        self._wildcard_manager = WildcardManager(get_wildcard_dir())

        if loaded_count % 2 == 0:
            return

        callbacks.register_pnginfo_saver(self._pnginfo_saver)
        callbacks.register_prompt_writer(self._prompt_writer)
        callbacks.register_on_infotext_pasted(self._pnginfo_saver)
        callbacks.register_settings()
        callbacks.register_wildcards_tab(self._wildcard_manager)

    def title(self):
        return f"Dynamic Prompts v{VERSION}"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        install_message = _get_install_error_message()
        correct_lib_version = bool(not install_message)

        html_path = base_dir / "helptext.html"
        html = Template(html_path.read_text("utf-8")).substitute(
            WILDCARD_DIR=self._wildcard_manager.path,
            VERSION=VERSION,
            LIB_VERSION=dynamicprompts.__version__,
        )

        jinja_html_path = base_dir / "jinja_help.html"
        jinja_help = jinja_html_path.read_text("utf-8")

        with gr.Group(elem_id=make_element_id("dynamic-prompting")):
            title = "Dynamic Prompts"
            if not correct_lib_version:
                title += " [incorrect installation]"
            with gr.Accordion(title, open=False):
                is_enabled = gr.Checkbox(
                    label="Dynamic Prompts enabled",
                    value=correct_lib_version,
                    interactive=correct_lib_version,
                    elem_id=make_element_id("dynamic-prompts-enabled"),
                )

                if not correct_lib_version:
                    gr.HTML(
                        f"""<span class="warning sddp-warning">Dynamic Prompts is not installed correctly</span>.
                        {install_message}""",
                    )

                with gr.Group(visible=correct_lib_version):
                    is_combinatorial = gr.Checkbox(
                        label="Combinatorial generation",
                        value=False,
                        elem_id=make_element_id("is-combinatorial"),
                    )

                    max_generations = gr.Slider(
                        label="Max generations (0 = all combinations - the batch count value is ignored)",
                        minimum=0,
                        maximum=1000,
                        step=1,
                        value=0,
                        elem_id=make_element_id("max-generations"),
                    )

                    combinatorial_batches = gr.Slider(
                        label="Combinatorial batches",
                        minimum=1,
                        maximum=10,
                        step=1,
                        value=1,
                        elem_id=make_element_id("combinatorial-times"),
                    )

                with gr.Accordion("Prompt Magic", open=False):
                    with gr.Group():
                        try:
                            magicprompt_models = load_magicprompt_models(
                                magicprompt_models_path,
                            )
                            default_magicprompt_model = (
                                opts.dp_magicprompt_default_model
                                if hasattr(opts, "dp_magicprompt_default_model")
                                else magicprompt_models[0]
                            )
                            is_magic_model_available = True
                        except IndexError:
                            logger.warning(
                                f"The magicprompts config file at {magicprompt_models_path} does not contain any models.",
                            )

                            magicprompt_models = []
                            default_magicprompt_model = ""
                            is_magic_model_available = False

                        is_magic_prompt = gr.Checkbox(
                            label="Magic prompt",
                            value=False,
                            elem_id=make_element_id("is-magicprompt"),
                            interactive=is_magic_model_available,
                        )

                        magic_prompt_length = gr.Slider(
                            label="Max magic prompt length",
                            value=100,
                            minimum=30,
                            maximum=300,
                            step=10,
                            interactive=is_magic_model_available,
                        )

                        magic_temp_value = gr.Slider(
                            label="Magic prompt creativity",
                            value=0.7,
                            minimum=0.1,
                            maximum=3.0,
                            step=0.10,
                            interactive=is_magic_model_available,
                        )

                        magic_model = gr.Dropdown(
                            magicprompt_models,
                            value=default_magicprompt_model,
                            multiselect=False,
                            label="Magic prompt model",
                            elem_id=make_element_id("magic-prompt-model"),
                            interactive=is_magic_model_available,
                        )

                        magic_blocklist_regex = gr.Textbox(
                            label="Magic prompt blocklist regex",
                            value="",
                            elem_id=make_element_id("magic-prompt-blocklist-regex"),
                            placeholder=(
                                "Regular expression pattern for blocking terms out of the generated prompt. Applied case-insensitively. "
                                'For instance, to block both "purple" and "interdimensional", you could use the pattern "purple|interdimensional".'
                            ),
                            interactive=is_magic_model_available,
                        )

                    is_feeling_lucky = gr.Checkbox(
                        label="I'm feeling lucky",
                        value=False,
                        elem_id=make_element_id("is-feelinglucky"),
                    )

                    with gr.Group():
                        is_attention_grabber = gr.Checkbox(
                            label="Attention grabber",
                            value=False,
                            elem_id=make_element_id("is-attention-grabber"),
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

                    disable_negative_prompt = gr.Checkbox(
                        label="Don't apply to negative prompts",
                        value=True,
                        elem_id=make_element_id("disable-negative-prompt"),
                    )

                with gr.Accordion("Need help?", open=False):
                    gr.HTML(html)

                with gr.Group():
                    with gr.Accordion("Jinja2 templates", open=False):
                        enable_jinja_templates = gr.Checkbox(
                            label="Enable Jinja2 templates",
                            value=False,
                            elem_id=make_element_id("enable-jinja-templates"),
                        )

                        with gr.Accordion("Help for Jinja2 templates", open=False):
                            gr.HTML(jinja_help)

                with gr.Group():
                    with gr.Accordion("Advanced options", open=False):
                        gr.HTML(
                            "Some settings have been moved to the settings tab. Find them in the Dynamic Prompts section.",
                        )

                        unlink_seed_from_prompt = gr.Checkbox(
                            label="Unlink seed from prompt",
                            value=False,
                            elem_id=make_element_id("unlink-seed-from-prompt"),
                        )

                        use_fixed_seed = gr.Checkbox(
                            label="Fixed seed",
                            value=False,
                            elem_id=make_element_id("is-fixed-seed"),
                        )

                        gr.Checkbox(
                            label="Write raw prompt to image",
                            value=False,
                            visible=False,  # For some reason, removing this line causes Auto1111 to hang
                            elem_id=make_element_id("write-raw-template"),
                        )

                        no_image_generation = gr.Checkbox(
                            label="Don't generate images",
                            value=False,
                            elem_id=make_element_id("no-image-generation"),
                        )

                gr.Checkbox(
                    label="Write prompts to file",
                    value=False,
                    elem_id=make_element_id("write-prompts"),
                    visible=False,  # For some reason, removing this line causes Auto1111 to hang
                )

        return [
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
            unlink_seed_from_prompt,
            disable_negative_prompt,
            enable_jinja_templates,
            no_image_generation,
            max_generations,
            magic_model,
            magic_blocklist_regex,
        ]

    def process(
        self,
        p,
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
        unlink_seed_from_prompt,
        disable_negative_prompt,
        enable_jinja_templates,
        no_image_generation,
        max_generations,
        magic_model,
        magic_blocklist_regex: str | None,
    ):
        if not is_enabled:
            logger.debug("Dynamic prompts disabled - exiting")
            return p

        ignore_whitespace = opts.dp_ignore_whitespace

        self._pnginfo_saver.enabled = opts.dp_write_raw_template
        self._prompt_writer.enabled = opts.dp_write_prompts_to_file
        self._limit_jinja_prompts = opts.dp_limit_jinja_prompts
        self._auto_purge_cache = opts.dp_auto_purge_cache
        magicprompt_batch_size = opts.dp_magicprompt_batch_size

        parser_config = ParserConfig(
            variant_start=opts.dp_parser_variant_start,
            variant_end=opts.dp_parser_variant_end,
            wildcard_wrap=opts.dp_parser_wildcard_wrap,
        )

        fix_seed(p)

        # Save original prompts before we touch `p.prompt`/`p.hr_prompt` etc.
        original_prompt = _get_effective_prompt(p.all_prompts, p.prompt)
        original_negative_prompt = _get_effective_prompt(
            p.all_negative_prompts,
            p.negative_prompt,
        )
        hr_fix_enabled = getattr(p, "enable_hr", False)

        # all_hr_prompts (and the other hr prompt related stuff)
        # is only available in AUTOMATIC1111 1.3.0+, but might not be in forks.
        # Assume that if all_hr_prompts is available, the other hr prompt related stuff is too.
        if hr_fix_enabled and hasattr(p, "all_hr_prompts"):
            original_hr_prompt = _get_effective_prompt(p.all_hr_prompts, p.hr_prompt)
            original_negative_hr_prompt = _get_effective_prompt(
                p.all_hr_negative_prompts,
                p.hr_negative_prompt,
            )
        else:
            # If hr fix is not enabled, the HR prompts are effectively the same as the normal prompts
            original_hr_prompt = original_prompt
            original_negative_hr_prompt = original_negative_prompt

        original_seed = p.seed
        num_images = p.n_iter * p.batch_size

        if is_combinatorial:
            if max_generations == 0:
                num_images = None
            else:
                num_images = max_generations

        combinatorial_batches = int(combinatorial_batches)
        if self._auto_purge_cache:
            self._wildcard_manager.clear_cache()

        try:
            logger.debug("Creating generator")

            generator_builder = (
                GeneratorBuilder(
                    self._wildcard_manager,
                    ignore_whitespace=ignore_whitespace,
                    parser_config=parser_config,
                )
                .set_is_feeling_lucky(is_feeling_lucky)
                .set_is_attention_grabber(
                    is_attention_grabber,
                    min_attention,
                    max_attention,
                )
                .set_is_jinja_template(
                    enable_jinja_templates,
                    limit_prompts=self._limit_jinja_prompts,
                )
                .set_is_combinatorial(is_combinatorial, combinatorial_batches)
                .set_is_magic_prompt(
                    is_magic_prompt=is_magic_prompt,
                    magic_model=magic_model,
                    magic_prompt_length=magic_prompt_length,
                    magic_temp_value=magic_temp_value,
                    magic_blocklist_regex=magic_blocklist_regex,
                    batch_size=magicprompt_batch_size,
                    device=device,
                )
                .set_is_dummy(False)
                .set_unlink_seed_from_prompt(unlink_seed_from_prompt)
                .set_seed(original_seed)
                .set_context(p)
                .set_freeze_prompt(should_freeze_prompt(p))
            )

            generator = generator_builder.create_generator()

            if disable_negative_prompt:
                generator_builder.disable_prompt_magic()
                negative_generator = generator_builder.create_generator()
            else:
                negative_generator = generator

            all_seeds = None
            if num_images and not unlink_seed_from_prompt:
                p.all_seeds, p.all_subseeds = get_seeds(
                    p,
                    num_images,
                    use_fixed_seed,
                    is_combinatorial,
                    combinatorial_batches,
                )
                all_seeds = p.all_seeds

            all_prompts, all_negative_prompts = generate_prompts(
                generator,
                negative_generator,
                original_prompt,
                original_negative_prompt,
                num_images,
                all_seeds,
            )

        except GeneratorException as e:
            logger.exception(e)
            all_prompts = [str(e)]
            all_negative_prompts = [str(e)]

        updated_count = len(all_prompts)
        p.n_iter = math.ceil(updated_count / p.batch_size)

        if num_images != updated_count:
            p.all_seeds, p.all_subseeds = get_seeds(
                p,
                updated_count,
                use_fixed_seed,
                is_combinatorial,
                combinatorial_batches,
            )

        if updated_count > 1:
            logger.info(
                f"Prompt matrix will create {updated_count} images in a total of {p.n_iter} batches.",
            )

        self._prompt_writer.set_data(
            positive_template=original_prompt,
            negative_template=original_negative_prompt,
            positive_prompts=all_prompts,
            negative_prompts=all_negative_prompts,
        )

        p.all_prompts = all_prompts
        p.all_negative_prompts = all_negative_prompts
        if no_image_generation:
            logger.debug("No image generation requested - exiting")
            # Need a minimum of batch size images to avoid errors
            p.batch_size = 1
            p.all_prompts = all_prompts[0:1]

        p.prompt_for_display = original_prompt
        p.prompt = original_prompt

        if hr_fix_enabled:
            p.all_hr_prompts = (
                all_prompts
                if original_prompt == original_hr_prompt
                else len(all_prompts) * [original_hr_prompt]
            )
            p.all_hr_negative_prompts = (
                all_negative_prompts
                if original_negative_prompt == original_negative_hr_prompt
                else len(all_negative_prompts) * [original_negative_hr_prompt]
            )
