from itertools import permutations
from prompts.generators.jinjagenerator import RandomExtension, PermutationExtension
from unittest import mock

class TestRandomExtension:
    def test_choice(self):
        ext = RandomExtension(mock.MagicMock())

        with mock.patch('random.choice') as mock_choice:
            mock_choice.side_effect = "c"
            res = ext.choice("a", "b", "c")
            assert res == "c"

    def test_random(self):
        ext = RandomExtension(mock.MagicMock())

        with mock.patch('random.random') as mock_random:
            mock_random.return_value = 0.3
            res = ext.random()
            assert res == 0.3

    def test_randint(self):
        ext = RandomExtension(mock.MagicMock())

        with mock.patch('random.randint') as mock_random:
            mock_random.return_value = 7
            res = ext.randint(1, 10)
            assert res == 7

class TestPermutationExtension:
    def test_basic_permutation(self):
        ext = PermutationExtension(mock.MagicMock())
        res = ext.permutation(["one", "two", "three"], 2)

        assert len(res) == 6
        assert res[0] == ("one", "two" )
        assert res[1] == ("one", "three" )
        assert res[2] == ("two", "one" )
        assert res[3] == ("two", "three" )
        assert res[4] == ("three", "one" )
        assert res[5] == ("three", "two" )

    def test_permutation(self):
        ext = PermutationExtension(mock.MagicMock())
        res = ext.permutation(["one", "two", "three"], 1, 2)
        
        assert len(res) == 9
        assert res[0] == ("one", )
        assert res[1] == ("two", )
        assert res[2] == ("three", )
        assert res[3] == ("one", "two" )
        assert res[4] == ("one", "three" )
        assert res[5] == ("two", "one" )
        assert res[6] == ("two", "three" )
        assert res[7] == ("three", "one" )
        assert res[8] == ("three", "two" )

    

