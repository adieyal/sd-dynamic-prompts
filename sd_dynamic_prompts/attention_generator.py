from dynamicprompts.generators.attentiongenerator import AttentionGenerator

from sd_dynamic_prompts.special_syntax import (
    append_chunks,
    remove_a1111_special_syntax_chunks,
)


class SpecialSyntaxAwareAttentionGenerator(AttentionGenerator):
    """
    Attention generator that is aware of A1111 special syntax (LoRA, hypernet, etc.).
    """

    def _add_emphasis(self, prompt: str) -> str:
        prompt, special_chunks = remove_a1111_special_syntax_chunks(prompt)
        prompt = super()._add_emphasis(prompt)
        return append_chunks(prompt, special_chunks)
