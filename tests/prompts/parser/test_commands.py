from unittest import mock
from prompts.parser.commands import SequenceCommand, LiteralCommand, VariantCommand, Command, WildcardCommand
import pytest

def gen_variant(vals):
    return [{"weight": [1], "val": LiteralCommand(v)} for v in vals]

@pytest.fixture
def literals() -> list[LiteralCommand]:
    return [LiteralCommand("hello"), LiteralCommand("world")]


class TestSequence:
    def test_length(self, literals: list[Command]):
        sequence = SequenceCommand(literals)
        assert len(sequence) == 2

    def test_getitem(self, literals: list[Command]):
        sequence = SequenceCommand(literals)
        assert sequence[0] == literals[0]
        assert sequence[1] == literals[1]

    def test_equality(self, literals: list[Command]):
        sequence = SequenceCommand(literals)
        assert sequence == literals


class TestLiteral:
    def test_prompts(self):
        command = LiteralCommand("test")
        prompts = list(command.prompts())
        assert len(prompts) == 1
        assert prompts[0] == "test"

    def test_equality(self, literals):
        l1 = LiteralCommand("hello")
        l2 = LiteralCommand("XXX")

        assert l1 == literals[0]
        assert l1 == "hello"
        assert l1 != l2
        assert l1 != "XXX"

    def test_combine_literal_commands(self, literals):
        l3 = literals[0] + literals[1]
        assert l3 == "hello world"

    def test_error_combining_incompatible_commands(self):
        with pytest.raises(TypeError):
            _ = LiteralCommand("Hello") + VariantCommand([LiteralCommand("world")])


class TestVariant:
    def test_length(self, literals: list[LiteralCommand]):
        variant_command = VariantCommand(literals)
        assert len(variant_command) == 2

    def test_getitem(self, literals: list[LiteralCommand]):
        variant_command = VariantCommand(literals)
        assert variant_command[0] == literals[0]
        assert variant_command[1] == literals[1]

    def test_combinations(self):
        literals = [
            "one", "two", "three"
        ]
        variant_command = VariantCommand(gen_variant(literals))
        combinations = list(variant_command._combinations(1))
        assert len(combinations) == 3
        assert combinations[0] == ["one"]
        assert combinations[1] == ["two"]
        assert combinations[2] == ["three"]

        combinations = list(variant_command._combinations(2))
        assert len(combinations) == 9
        assert combinations[0] == ["one", "one"]
        assert combinations[1] == ["one", "two"]
        assert combinations[2] == ["one", "three"]
        assert combinations[3] == ["two", "one"]
        assert combinations[4] == ["two", "two"]
        assert combinations[5] == ["two", "three"]
        assert combinations[6] == ["three", "one"]
        assert combinations[7] == ["three", "two"]
        assert combinations[8] == ["three", "three"]

    def test_range(self):
        literals = [
            "one", "two", "three"
        ]
        variant_command = VariantCommand(gen_variant(literals), min_bound=-1, max_bound=10)
        assert variant_command.min_bound == 1

        variant_command = VariantCommand(gen_variant(literals), min_bound=2, max_bound=1)
        assert variant_command.min_bound == 1
        assert variant_command.max_bound == 2
        
        
