from __future__ import annotations

from dynamicprompts.generators import (
    BatchedCombinatorialPromptGenerator,
    CombinatorialPromptGenerator,
    DummyGenerator,
    FeelingLuckyGenerator,
    JinjaGenerator,
    PromptGenerator,
    RandomPromptGenerator,
)
from dynamicprompts.parser.parse import default_parser_config

from sd_dynamic_prompts.frozenprompt_generator import FrozenPromptGenerator
from sd_dynamic_prompts.utils import get_logger

logger = get_logger(__name__)


class GeneratorBuilder:
    def __init__(
        self,
        wildcard_manager,
        parser_config=default_parser_config,
        ignore_whitespace=False,
    ):
        self._wildcard_manager = wildcard_manager

        self._is_dummy = False
        self._should_freeze_prompt = False
        self._is_feeling_lucky = False
        self._is_jinja_template = False
        self._is_combinatorial = False
        self._is_magic_prompt = False
        self._is_attention_grabber = False

        self._combinatorial_batches = 1
        self._magic_model = None
        self._magic_prompt_length = 100
        self._magic_temp_value = 0.7
        self._magic_blocklist_regex = None
        self._min_attention = 1.1
        self._max_attention = 1.5
        self._device = 0
        self._ignore_whitespace = ignore_whitespace
        self._unlink_seed_from_prompt = False
        self._seed = -1
        self._context = None
        self._parser_config = parser_config

    def log_configuration(self):
        logger.debug(
            f"""
        Creating generator:
            is_dummy: {self._is_dummy}
            is_feeling_lucky: {self._is_feeling_lucky}
            enable_jinja_templates: {self._is_jinja_template}
            is_combinatorial: {self._is_combinatorial}
            is_magic_prompt: {self._is_magic_prompt}
            combinatorial_batches: {self._combinatorial_batches}
            magic_prompt_length: {self._magic_prompt_length}
            magic_temp_value: {self._magic_temp_value}
            magic_blocklist_regex: {self._magic_blocklist_regex}
            is_attention_grabber: {self._is_attention_grabber}
            min_attention: {self._min_attention}
            max_attention: {self._max_attention}

        """,
        )

    def set_is_dummy(self, is_dummy=True):
        self._is_dummy = is_dummy
        return self

    def set_is_feeling_lucky(self, is_feeling_lucky=True):
        self._is_feeling_lucky = is_feeling_lucky
        return self

    def set_is_attention_grabber(
        self,
        is_attention_grabber=True,
        min_attention=1.1,
        max_attention=1.5,
    ):
        self._is_attention_grabber = is_attention_grabber
        self._min_attention = min_attention
        self._max_attention = max_attention
        return self

    def set_is_jinja_template(self, is_jinja_template=True, limit_prompts=False):
        self._is_jinja_template = is_jinja_template
        self._limit_jinja_prompts = limit_prompts

        return self

    def set_is_combinatorial(self, is_combinatorial=True, combinatorial_batches=1):
        self._is_combinatorial = is_combinatorial
        self._combinatorial_batches = combinatorial_batches
        return self

    def set_is_magic_prompt(
        self,
        is_magic_prompt=True,
        magic_model=None,
        magic_prompt_length=100,
        magic_temp_value=0.7,
        device=0,
        magic_blocklist_regex: str | None = None,
        batch_size=1,
    ):
        if not magic_model:
            self._is_magic_prompt = False
            return self

        self._magic_model = magic_model
        self._magic_prompt_length = magic_prompt_length
        self._magic_temp_value = magic_temp_value
        self._magic_blocklist_regex = magic_blocklist_regex
        self._is_magic_prompt = is_magic_prompt
        self._magic_batch_size = batch_size
        self._device = device

        return self

    def set_unlink_seed_from_prompt(self, unlink_seed_from_prompt=True):
        self._unlink_seed_from_prompt = unlink_seed_from_prompt
        return self

    def set_seed(self, seed):
        self._seed = seed
        return self

    def set_freeze_prompt(self, should_freeze: bool):
        self._should_freeze_prompt = should_freeze
        return self

    def set_context(self, context):
        self._context = context
        return self

    def disable_prompt_magic(self):
        self.set_is_attention_grabber(False)
        self.set_is_magic_prompt(False)
        self.set_is_feeling_lucky(False)

        return self

    def create_generator(self):
        if self._is_dummy:
            return DummyGenerator()

        elif self._is_feeling_lucky:
            generator = FeelingLuckyGenerator()

        elif self._is_jinja_template:
            generator = self.create_jinja_generator(self._context)
        else:
            generator = self.create_basic_generator()

        if self._is_magic_prompt:
            from dynamicprompts.generators.magicprompt import MagicPromptGenerator

            generator = MagicPromptGenerator(
                generator,
                model_name=self._magic_model,
                device=self._device,
                max_prompt_length=self._magic_prompt_length,
                temperature=self._magic_temp_value,
                seed=self._seed,
                blocklist_regex=self._magic_blocklist_regex,
                batch_size=self._magic_batch_size,
            )

        if self._is_attention_grabber:
            try:
                from sd_dynamic_prompts.attention_generator import (
                    SpecialSyntaxAwareAttentionGenerator,
                )

                generator = SpecialSyntaxAwareAttentionGenerator(
                    generator,
                    min_attention=self._min_attention,
                    max_attention=self._max_attention,
                )
            except ImportError as ie:
                logger.error(f"Not using AttentionGenerator: {ie}")

        if self._should_freeze_prompt:
            generator = FrozenPromptGenerator(generator)
        return generator

    def create_basic_generator(
        self,
    ) -> PromptGenerator:
        if self._is_combinatorial:
            prompt_generator = CombinatorialPromptGenerator(
                self._wildcard_manager,
                parser_config=self._parser_config,
                ignore_whitespace=self._ignore_whitespace,
            )
            prompt_generator = BatchedCombinatorialPromptGenerator(
                prompt_generator,
                batches=self._combinatorial_batches,
            )
        else:
            prompt_generator = RandomPromptGenerator(
                self._wildcard_manager,
                seed=self._seed,
                parser_config=self._parser_config,
                unlink_seed_from_prompt=self._unlink_seed_from_prompt,
                ignore_whitespace=self._ignore_whitespace,
            )

        return prompt_generator

    def create_jinja_generator(self, p) -> PromptGenerator:
        original_prompt = p.all_prompts[0] if len(p.all_prompts) > 0 else p.prompt
        original_negative_prompt = (
            p.all_negative_prompts[0]
            if len(p.all_negative_prompts) > 0
            else p.negative_prompt
        )
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
                "prompt": original_prompt,
                "negative_prompt": original_negative_prompt,
            },
        }

        generator = JinjaGenerator(
            self._wildcard_manager,
            context,
            limit_prompts=self._limit_jinja_prompts,
            ignore_whitespace=self._ignore_whitespace,
        )
        return generator
