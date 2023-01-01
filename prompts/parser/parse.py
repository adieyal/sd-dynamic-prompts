from __future__ import annotations

import pyparsing as pp
from typing import cast
import logging

from .commands import SequenceCommand, LiteralCommand, VariantCommand, WildcardCommand

logger = logging.getLogger(__name__)

real_num1 = pp.Combine(pp.Word(pp.nums) + "." + pp.Word(pp.nums))
real_num2 = pp.Combine(pp.Word(pp.nums) + ".")
real_num3 = pp.Combine("." + pp.Word(pp.nums))
real_num4 = pp.Word(pp.nums)

real_num = real_num1 | real_num2 | real_num3 | real_num4

def parse_bound_expr(expr, max_options):
    lbound = 1
    ubound = max_options
    separator = ","

    if expr is None:
        return lbound, ubound, separator
    expr = expr[0]

    if "range" in expr:
        rng = expr["range"]
        if "exact" in rng:
            lbound = ubound = rng["exact"]
        else:
            if "lower" in expr["range"]:
                lbound = int(expr["range"]["lower"])
            if "upper" in expr["range"]:
                ubound = int(expr["range"]["upper"])

    if "separator" in expr:
        separator = expr["separator"][0]

    return lbound, ubound, separator

class ActionBuilder:
    def __init__(self, wildcard_manager):
        self._wildcard_manager = wildcard_manager

    def get_literal_class(self):
        return LiteralCommand

    def get_wildcard_class(self):
        return WildcardCommand

    def get_variant_class(self):
        return VariantCommand

    def get_sequence_class(self):
        return SequenceCommand

    def get_prompt_editing_class(self):
        return self.get_sequence_class()

    def get_prompt_alternating_class(self):
        return self.get_sequence_class()

    def get_prompt_editing_action(self):
        return lambda x, y, tokens: self.get_prompt_editing_class()(tokens)

    def get_prompt_alternating_action(self):
        return lambda x, y, tokens: self.get_prompt_editing_class()(tokens)

    def get_wildcard_action(self, token):
        return self.get_wildcard_class()(self._wildcard_manager, token)

    def get_variant_action(self, token):
        parts = token[0].as_dict()
        variants = parts["variants"]
        variants = [{"weight": v["weight"], "val": v["val"]} for v in variants]
        if "bound_expr" in parts:
            min_bound, max_bound, sep = parse_bound_expr(
                parts["bound_expr"], max_options=len(variants)
            )
            command = self.get_variant_class()(variants, min_bound, max_bound, sep)
        else:
            command = self.get_variant_class()(variants)

        return command

    def get_literal_action(self, token):
        s = " ".join(token)
        return self.get_literal_class()(s)


class Parser:
    def __init__(self, builder: ActionBuilder):
        self._builder = builder
        prompt = self._configure_parser(self._builder)
        self._prompt = prompt
        
    @property
    def prompt(self):
        return self._prompt

    def parse(self, prompt: str) -> SequenceCommand:
        tokens = self.prompt.parse_string(prompt, parse_all=True)
        return cast(SequenceCommand, tokens[0])

    def _enable_comments(self, prompt):
        prompt.ignore("#" + pp.restOfLine)
        prompt.ignore("//" + pp.restOfLine)
        prompt.ignore(pp.c_style_comment)

    def _configure_range(self):
        hyphen = pp.Suppress("-")
        variant_delim = pp.Suppress("$$")

        separator = pp.Word(pp.alphanums + " ", exclude_chars="$").leave_whitespace()("separator")
        bound = pp.common.integer
        bound_range1 = bound("exact")
        bound_range2 = bound("lower") + hyphen
        bound_range3 = hyphen + bound("upper")
        bound_range4 = bound("lower") + hyphen + bound("upper")

        bound_range = pp.Group(
            bound_range4 | bound_range3 | bound_range2 | bound_range1
        )
        bound_expr = pp.Group(
            bound_range("range")
            + variant_delim
            + pp.Opt(separator + variant_delim, default=",")("separator")
        )

        return bound_expr

    def _configure_wildcard(self):
        wildcard_enclosure = pp.Suppress("__")
        wildcard = (wildcard_enclosure + ... + wildcard_enclosure)("wildcard")

        return wildcard

    def _configure_literal_sequence(self):
        non_literal_chars = r"{}()|:$\[\]"
        wildcard_enclosure = pp.Suppress("__")

        literal = pp.Regex(rf"[^{non_literal_chars}\s]+")("literal")
        # literal_sequence = pp.Forward()

        literal_sequence1 = pp.OneOrMore(~wildcard_enclosure + literal)
        literal_sequence_square = pp.Word("[") + literal_sequence1 + pp.Word("]")
        literal_sequence_round = pp.Word("(") + literal_sequence1 + pp.Word(")")
        literal_sequence_round2 = pp.Word("(") + literal_sequence1 + pp.Word(":") + real_num + pp.Word(")")

        def join_literal_sequence(s, l, tokens):
            chars = "[]():"
            s = " ".join([str(t) for t in tokens])
            for c in chars:
                s = s.replace(f" {c}", c)
                s = s.replace(f"{c} ", c)

            return s

        literal_sequence_square = literal_sequence_square.set_parse_action(join_literal_sequence)
        literal_sequence_round = literal_sequence_round.set_parse_action(join_literal_sequence)
        literal_sequence_round2 = literal_sequence_round2.set_parse_action(join_literal_sequence)
        
        literal_sequence = pp.OneOrMore(literal_sequence1 | literal_sequence_square | literal_sequence_round | literal_sequence_round2)
        
        return  literal_sequence("literal_sequence")

    def _configure_extra(self, prompt):
        prompt_alternating = self._configure_prompt_alternating_words(prompt)
        prompt_editing = self._configure_prompt_editing(prompt)
        return  prompt_editing | prompt_alternating

    def _configure_prompt_alternating_words(self, prompt):
        left_bracket, right_bracket = map(pp.Word, "[]")
        pipe = pp.Word("|")
        chars = pp.Regex(r"[^\]|]*")

        literals = [left_bracket, right_bracket, pipe]
        for l in literals:
            l.set_parse_action(self._builder.get_literal_action)

        prompt_alternating = left_bracket + prompt + pp.OneOrMore(pipe + prompt) + right_bracket
        pa =  prompt_alternating.set_parse_action(self._builder.get_prompt_alternating_action())

        return pa

    def _configure_prompt_editing(self, prompt):
        left_bracket, right_bracket = map(pp.Word, "[]")
        colon = pp.Word(":")

        literals = [left_bracket, right_bracket, colon, real_num]
        for l in literals:
            l.set_parse_action(self._builder.get_literal_action)

        prompt_editing = left_bracket + prompt + colon + prompt + colon + real_num + right_bracket
        pe = prompt_editing.set_parse_action(self._builder.get_prompt_editing_action())
        
        return pe


    def _configure_weight(self):
        weight_delim = pp.Suppress("::")
        weight = (pp.common.real | pp.common.integer) + weight_delim

        return weight

    def _configure_variants(self, literal_sequence, bound_expr, prompt):
        weight_delim = pp.Suppress("::")

        left_brace, right_brace = map(pp.Suppress, "{}")
        weight = pp.common.integer + weight_delim
        
        variant_option = prompt
        variant = pp.Group(pp.Opt(weight, default=1)("weight") + variant_option("val"))
        variants_list = pp.Group(pp.delimited_list(variant, delim="|"))

        variants = (
            left_brace
            + pp.Group(pp.Opt(bound_expr)("bound_expr") + variants_list("variants"))
            + right_brace
        )

        return variants


    def _configure_parser(self, builder: ActionBuilder):
        bound_expr = self._configure_range()

        prompt = pp.Forward()
        wildcard = self._configure_wildcard()
        literal_sequence = self._configure_literal_sequence()
        variants = self._configure_variants(literal_sequence, bound_expr, prompt)
        extras = self._configure_extra(prompt)
        
        chunk = (extras | variants | wildcard | literal_sequence)

        prompt <<= pp.ZeroOrMore(chunk)("prompt")
        
        self._enable_comments(prompt)

        wildcard.set_parse_action(builder.get_wildcard_action)
        variants.set_parse_action(builder.get_variant_action)
        literal_sequence.set_parse_action(builder.get_literal_action)

        prompt.set_parse_action(
            lambda s, loc, token: builder.get_sequence_class()(token.as_list())
        )

        return prompt


