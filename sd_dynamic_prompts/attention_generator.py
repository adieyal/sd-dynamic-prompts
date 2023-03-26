import re

from dynamicprompts.generators.attentiongenerator import AttentionGenerator

# A1111 special syntax (LoRA, hypernet, etc.)
A1111_SPECIAL_SYNTAX_RE = re.compile(r"\s*<[^>]+>")


def remove_a1111_special_syntax_chunks(s: str) -> tuple[str, list[str]]:
    """
    Remove A1111 special syntax chunks from a string and return the string and the chunks.
    """
    chunks: list[str] = []

    def put_chunk(m):
        chunks.append(m.group(0))
        return ""

    return re.sub(A1111_SPECIAL_SYNTAX_RE, put_chunk, s), chunks


def append_chunks(s: str, chunks: list[str]) -> str:
    """
    Append (A1111 special syntax) chunks to a string.
    """
    if not chunks:
        return s
    return f"{s}{''.join(chunks)}"


class SpecialSyntaxAwareAttentionGenerator(AttentionGenerator):
    """
    Attention generator that is aware of A1111 special syntax (LoRA, hypernet, etc.).
    """

    def _add_emphasis(self, prompt: str) -> str:
        prompt, special_chunks = remove_a1111_special_syntax_chunks(prompt)
        prompt = super()._add_emphasis(prompt)
        return append_chunks(prompt, special_chunks)
