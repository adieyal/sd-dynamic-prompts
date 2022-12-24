from prompts import constants


class TestParsing:
    def test_parse_combinations(self, generator):
        quantity, _, options, weights = generator._parse_combinations("bread|butter")
        assert quantity == (
            constants.DEFAULT_NUM_COMBINATIONS,
            constants.DEFAULT_NUM_COMBINATIONS,
        )
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("2$$bread|butter")
        assert quantity == (2, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "1-2$$bread|butter"
        )
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "2-1$$bread|butter"
        )
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "1-$$bread|butter"
        )
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "-1$$bread|butter"
        )
        assert quantity == (0, 1)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "2$$and$$bread|butter"
        )
        assert quantity == (2, 2)
        assert options == ["bread", "butter"]
        assert weights == [1.0, 1.0]

        quantity, _, options, weights = generator._parse_combinations("")
        assert quantity == (1, 1)
        assert options == [""]
        assert weights == [1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "3::bread|2::butter"
        )
        assert quantity == (1, 1)
        assert options == ["bread", "butter"]
        assert weights == [3.0, 2.0]

        quantity, _, options, weights = generator._parse_combinations(
            "1.3::bread|butter"
        )
        assert quantity == (1, 1)
        assert options == ["bread", "butter"]
        assert weights == [1.3, 1.0]

        quantity, _, options, weights = generator._parse_combinations(
            "1-2$$2.5::bread|butter"
        )
        assert quantity == (1, 2)
        assert options == ["bread", "butter"]
        assert weights == [2.5, 1.0]

    def test_joiner(self, generator):
        _, joiner, _, _ = generator._parse_combinations("bread|butter")
        assert joiner == constants.DEFAULT_COMBO_JOINER

        _, joiner, _, _ = generator._parse_combinations("2$$bread|butter")
        assert joiner == constants.DEFAULT_COMBO_JOINER

        _, joiner, _, _ = generator._parse_combinations("2$$and$$bread|butter")
        assert joiner == "and"

        _, joiner, _, _ = generator._parse_combinations("")
        assert joiner == ","

        _, joiner, _, _ = generator._parse_combinations("2$$|$$bread|butter")
        assert joiner == "|"

    def test_photographers(self, generator):
        quantity, joiner, options, weights = generator._parse_combinations(
            "2-4$$|$$a|b|c"
        )
