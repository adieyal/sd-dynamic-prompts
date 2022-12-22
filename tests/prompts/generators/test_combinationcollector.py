from unittest import mock
import pytest

from prompts.generators.randomprompt import CombinationCollector, CombinationSelector, MAX_SELECTION_ITERATIONS


class TestCombinationSelector:
    def test_collect_one(self):
        selector = mock.Mock()
        selector.pick.return_value = ["a"]

        collector = CombinationCollector(selector)
        collected = collector.collect(1)
        assert len(collected) == 1
        assert collected[0] == "a"

    def test_collect_multiple(self):
        selector = mock.Mock()
        return_values = [["a"], ["b"], ["a"]] + ["a"] * MAX_SELECTION_ITERATIONS
        selector.pick.side_effect = return_values

        collector = CombinationCollector(selector)
        collected = collector.collect(3)
        assert len(collected) == 2
        assert collected[0] == "a"
        assert collected[1] == "b"

    def test_collect_with_range(self):
        selector = mock.Mock()
        selector.pick.side_effect = [["a"], ["b"], ["a"]]

        collector = CombinationCollector(selector)

        with mock.patch("random.randint", return_value=2):
            collected = collector.collect((2, 3))
            assert len(collected) == 2
            assert collected[0] == "a"
            assert collected[1] == "b"

    def test_without_duplicates(self):
        selector = mock.Mock()
        selector.pick.side_effect = [["a"], ["a"], ["b"]]

        collector = CombinationCollector(selector)
        collected = collector.collect(2, duplicates=False)
        assert len(collected) == 2
        assert collected[0] == "a"
        assert collected[1] == "b"

    def test_raises_exception_when_not_enough_options(self):
        selector = mock.Mock()
        selector.pick.return_value = ["a"]

        collector = CombinationCollector(selector)
        collected = collector.collect(2, duplicates=False)
        assert len(collected) == 1

        collector.collect(2, duplicates=True)
