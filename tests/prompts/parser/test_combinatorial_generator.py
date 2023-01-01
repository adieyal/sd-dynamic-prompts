from unittest import mock

import pytest


from prompts.parser.combinatorial_generator import (
    CombinatorialSequenceCommand,
    CombinatorialVariantCommand,
    CombinatorialWildcardCommand,
    CombinatorialGenerator,
)
from prompts.parser.commands import LiteralCommand


@pytest.fixture
def wildcard_manager():
    return mock.Mock()

@pytest.fixture
def generator(wildcard_manager) -> CombinatorialGenerator:
    return CombinatorialGenerator(wildcard_manager)


def gen_variant(vals):
    return [{"weight": [1], "val": LiteralCommand(v)} for v in vals]


class TestLiteralCommand:
    def test_iter_with_no_next(self):
        command = LiteralCommand("test")
        prompts = list(command.prompts())
        assert len(prompts) == 1
        assert prompts[0] == "test"

    def test_iter_with_next(self):
        command1 = LiteralCommand("one")
        command2 = LiteralCommand("two")
        command3 = LiteralCommand("three")
        sequence = CombinatorialSequenceCommand([command1, command2, command3])

        prompts = list(sequence.prompts())
        assert len(prompts) == 1
        assert prompts[0] == "one two three"

    def test_prompts(self):
        command = LiteralCommand("test")
        assert list(command.prompts()) == ["test"]

    def test_get_prompt(self):
        command = LiteralCommand("test")
        assert command.get_prompt() == "test"

class TestVariantCommand:
    def test_empty_variant(self):
        command = CombinatorialVariantCommand([])
        prompts = list(command.prompts())
        assert len(prompts) == 0

    def test_single_variant(self):
        command = CombinatorialVariantCommand(gen_variant(["one"]))
        prompts = list(command.prompts())

        assert len(prompts) == 1
        assert prompts[0] == "one"

    def test_multiple_variant(self):
        variants = gen_variant(["one", "two", "three"])
        command = CombinatorialVariantCommand(variants)

        prompts = list(command.prompts())
        assert len(prompts) == 3
        assert prompts[0] == "one"
        assert prompts[1] == "two"
        assert prompts[2] == "three"

    def test_variant_with_literal(self):
        variants = gen_variant(["one", "two", "three"])
        command1 = CombinatorialVariantCommand(variants)

        command2 = LiteralCommand("circles and squares")
        sequence = CombinatorialSequenceCommand([command1, command2])

        prompts = list(sequence.prompts())
        assert len(prompts) == 3
        assert prompts[0] == "one circles and squares"
        assert prompts[1] == "two circles and squares"
        assert prompts[2] == "three circles and squares"

    def test_two_variants(self):
        variants1 = gen_variant(["red", "green"])
        variants2 = gen_variant(["circles", "squares", "triangles"])

        command1 = CombinatorialVariantCommand(variants1)
        command2 = CombinatorialVariantCommand(variants2)
        sequence = CombinatorialSequenceCommand([command1, command2])

        prompts = list(sequence.prompts())
        assert len(prompts) == 6
        assert prompts[0] == "red circles"
        assert prompts[1] == "red squares"
        assert prompts[2] == "red triangles"
        assert prompts[3] == "green circles"
        assert prompts[4] == "green squares"
        assert prompts[5] == "green triangles"

    def test_varied_prompt(self):
        variants1 = gen_variant(["red", "green"])
        variants2 = gen_variant(["circles", "squares", "triangles"])

        command1 = CombinatorialVariantCommand(variants1)
        command2 = CombinatorialVariantCommand(variants2)
        command3 = LiteralCommand("are")
        command4 = LiteralCommand("cool")
        sequence = CombinatorialSequenceCommand(
            [command1, command2, command3, command4]
        )

        prompts = list(sequence.prompts())

        assert len(prompts) == 6
        assert prompts[0] == "red circles are cool"
        assert prompts[1] == "red squares are cool"
        assert prompts[2] == "red triangles are cool"
        assert prompts[3] == "green circles are cool"
        assert prompts[4] == "green squares are cool"
        assert prompts[5] == "green triangles are cool"

    def test_combo(self):
        variants = gen_variant(["red", "green", "blue"])
        command = CombinatorialVariantCommand(variants, 2, 2)
        prompts = list(command.prompts())
        assert len(prompts) == 6
        assert prompts[0] == "red,green"
        assert prompts[1] == "red,blue"
        assert prompts[2] == "green,red"
        assert prompts[3] == "green,blue"
        assert prompts[4] == "blue,red"
        assert prompts[5] == "blue,green"

    def test_combo_different_bounds(self):
        variants = gen_variant(["red", "green", "blue"])
        command = CombinatorialVariantCommand(variants, 1, 2)
        prompts = list(command.prompts())
        assert len(prompts) == 9
        assert prompts[0] == "red"
        assert prompts[1] == "green"
        assert prompts[2] == "blue"
        assert prompts[3] == "red,green"
        assert prompts[4] == "red,blue"
        assert prompts[5] == "green,red"
        assert prompts[6] == "green,blue"
        assert prompts[7] == "blue,red"
        assert prompts[8] == "blue,green"

    def test_custom_sep(self):
        variants = gen_variant(["red", "green", "blue"])
        command = CombinatorialVariantCommand(variants, 2, 2, " and ")
        prompts = list(command.prompts())
        assert len(prompts) == 6
        assert prompts[0] == "red and green"
        assert prompts[1] == "red and blue"
        assert prompts[2] == "green and red"
        assert prompts[3] == "green and blue"
        assert prompts[4] == "blue and red"
        assert prompts[5] == "blue and green"


#     def test_prompt_editing(self):
#         variants = gen_variant(["red", "green", "[dog|cat]"])
#         command = VariantCommand(variants)
#         prompts = list(command.prompts())
#         assert len(prompts) == 3
#         assert prompts[0] == "red"
#         assert prompts[1] == "green"
#         assert prompts[2] == "[dog|cat]"


class TestWildcardsCommand:
    def test_basic_wildcard(self, wildcard_manager):
        with mock.patch.object(
            wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            command = CombinatorialWildcardCommand(wildcard_manager, ["colours"])
            prompts = list(command.prompts())
            assert len(prompts) == 3
            assert prompts[0] == "red"
            assert prompts[1] == "green"
            assert prompts[2] == "blue"

            wildcard_manager.get_all_values.assert_called_once_with("colours")

            

    def test_wildcard_with_literal(self, wildcard_manager):
        with mock.patch.object(
            wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            command1 = CombinatorialWildcardCommand(wildcard_manager, ["colours"])
            command2 = LiteralCommand("are")
            command3 = LiteralCommand("cool")
            sequence = CombinatorialSequenceCommand([command1, command2, command3])
            
            prompts = list(sequence.prompts())
            assert len(prompts) == 3
            assert prompts[0] == "red are cool"
            assert prompts[1] == "green are cool"
            assert prompts[2] == "blue are cool"
            wildcard_manager.get_all_values.assert_called_once_with("colours")

    def test_wildcard_with_variant(self, wildcard_manager):
        with mock.patch.object(
            wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            command1 = CombinatorialWildcardCommand(wildcard_manager, "colours")
            command2 = CombinatorialVariantCommand(gen_variant(["circles", "squares"]))
            sequence = CombinatorialSequenceCommand([command1, command2])

            prompts = list(sequence.prompts())

            assert len(prompts) == 6
            assert prompts[0] == "red circles"
            assert prompts[1] == "red squares"
            assert prompts[2] == "green circles"
            assert prompts[3] == "green squares"
            assert prompts[4] == "blue circles"
            assert prompts[5] == "blue squares"

    def test_variant_nested_in_wildcard(self, wildcard_manager):
        with mock.patch.object(
            wildcard_manager, "get_all_values", return_value=["{red|pink}", "green", "blue"]
        ):
            wildcard_command = CombinatorialWildcardCommand(wildcard_manager, "colours")
            sequence = CombinatorialSequenceCommand([wildcard_command])

            prompts = list(sequence.prompts())

            assert len(prompts) == 4
            assert prompts[0] == "red"
            assert prompts[1] == "pink"
            assert prompts[2] == "green"
            assert prompts[3] == "blue"

    def test_wildcard_nested_in_wildcard(self, wildcard_manager):
        with mock.patch.object(
            wildcard_manager, "get_all_values", side_effect=[
                ["__other_colours__", "green", "blue"],
                ["red", "pink", "yellow"]
            ]
        ):
            wildcard_command = CombinatorialWildcardCommand(wildcard_manager, "colours")
            sequence = CombinatorialSequenceCommand([wildcard_command])

            prompts = list(sequence.prompts())

            assert len(prompts) == 5
            assert prompts[0] == "red"
            assert prompts[1] == "pink"
            assert prompts[2] == "yellow"
            assert prompts[3] == "green"
            assert prompts[4] == "blue"

class TestCombinatorialSequenceCommand:
    def test_prompts(self):
        command1 = LiteralCommand("A")
        command2 = LiteralCommand("sentence")
        sequence = CombinatorialSequenceCommand([command1, command2])

        prompts = list(sequence.prompts())
        assert len(prompts) == 1
        assert prompts[0] == "A sentence"

    def test_custom_separator(self):
        command1 = LiteralCommand("A")
        command2 = LiteralCommand("sentence")
        sequence = CombinatorialSequenceCommand([command1, command2], separator="")

        prompts = list(sequence.prompts())
        assert len(prompts) == 1
        assert prompts[0] == "Asentence"

class TestCombinatorialGenerator:
    def test_empty(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("", 5)
        assert len(prompts) == 0

    def test_literals(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A literal sentence", 5)
        assert len(prompts) == 1

    def test_variants(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A red {square|circle}", 5)
        assert len(prompts) == 2
        assert prompts[0] == "A red square"
        assert prompts[1] == "A red circle"
        

    def test_two_variants(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A {red|green} {square|circle}", 5)
        assert len(prompts) == 4
        assert prompts[0] == "A red square"
        assert prompts[1] == "A red circle"
        assert prompts[2] == "A green square"
        assert prompts[3] == "A green circle"

        prompts = generator.generate_prompts("A {red|green} {square|circle}", 2)
        assert len(prompts) == 2
        assert prompts[0] == "A red square"
        assert prompts[1] == "A red circle"

    def test_combination_variants(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A {2$$red|green|blue} square", 10)
        assert len(prompts) == 6
        assert prompts[0] == "A red,green square"
        assert prompts[1] == "A red,blue square"
        assert prompts[2] == "A green,red square"
        assert prompts[3] == "A green,blue square"
        assert prompts[4] == "A blue,red square"
        assert prompts[5] == "A blue,green square"

    def test_combination_variants_range(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A {1-2$$red|green|blue} square", 10)
        assert len(prompts) == 9
        assert prompts[0] == "A red square"
        assert prompts[1] == "A green square"
        assert prompts[2] == "A blue square"
        assert prompts[3] == "A red,green square"
        assert prompts[4] == "A red,blue square"
        assert prompts[5] == "A green,red square"
        assert prompts[6] == "A green,blue square"
        assert prompts[7] == "A blue,red square"
        assert prompts[8] == "A blue,green square"

    def test_combination_variants_with_separator(self, generator: CombinatorialGenerator):
        prompts = generator.generate_prompts("A {2$$ and $$red|green|blue} square", 10)
        assert len(prompts) == 6
        assert prompts[0] == "A red and green square"
        assert prompts[1] == "A red and blue square"
        assert prompts[2] == "A green and red square"
        assert prompts[3] == "A green and blue square"
        assert prompts[4] == "A blue and red square"
        assert prompts[5] == "A blue and green square"

    def test_variants_with_larger_range_than_choices(self, generator: CombinatorialGenerator):
        shapes = ["square", "circle"]
        with mock.patch("prompts.parser.random_generator.random") as mock_random:
            mock_random.randint.return_value = 3
            mock_random.choices.side_effect = [shapes]
            prompts = generator.generate_prompts("A red {3$$square|circle}", 1)

            assert len(prompts) == 0

    def test_wildcards(self, generator: CombinatorialGenerator):
        with mock.patch.object(
            generator._wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            prompts = generator.generate_prompts("A __colours__ {square|circle}", 6)
            assert len(prompts) == 6
            assert prompts[0] == "A red square"
            assert prompts[1] == "A red circle"
            assert prompts[2] == "A green square"
            assert prompts[3] == "A green circle"
            assert prompts[4] == "A blue square"
            assert prompts[5] == "A blue circle"
            generator._wildcard_manager.get_all_values.assert_called_once_with("colours")

    def test_nested_wildcard(self, generator: CombinatorialGenerator):
        with mock.patch.object(
            generator._wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            prompts = generator.generate_prompts("{__colours__}", 6)
            assert len(prompts) == 3

    def test_nested_wildcard_with_range(self, generator: CombinatorialGenerator):
        with mock.patch.object(
            generator._wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            prompts = generator.generate_prompts("{2$$__colours__}", 6)
            assert len(prompts) == 6
            assert prompts[0] == "red,green"
            assert prompts[1] == "red,blue"
            assert prompts[2] == "green,red"
            assert prompts[3] == "green,blue"
            assert prompts[4] == "blue,red"
            assert prompts[5] == "blue,green"

    def test_nested_wildcard_with_range_and_literal(self, generator: CombinatorialGenerator):
        with mock.patch.object(
            generator._wildcard_manager, "get_all_values", return_value=["red", "green", "blue"]
        ):
            prompts = generator.generate_prompts("{2$$__colours__|black}", 20)
            assert len(prompts) == 12
            assert prompts[0] == "red,green"
            assert prompts[1] == "red,blue"
            assert prompts[2] == "green,red"
            assert prompts[3] == "green,blue"
            assert prompts[4] == "blue,red"
            assert prompts[5] == "blue,green"
            assert prompts[6] == "red,black"
            assert prompts[7] == "green,black"
            assert prompts[8] == "blue,black"
            assert prompts[9] == "black,red"
            assert prompts[10] == "black,green"
            assert prompts[11] == "black,blue"

    def test_prompt_editing(self, generator: CombinatorialGenerator):
        prompts = [
            "A [start prompt:end prompt:0.25] example",
            "A [start prompt|end prompt|0.25] example",
        ]
        for p in prompts:
            new_prompts = list(generator.generate_prompts(p, 2))
            assert len(new_prompts) == 1
            assert new_prompts[0] == p