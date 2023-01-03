from unittest import mock
from pathlib import Path

from prompts.wildcardmanager import WildcardManager, WildcardFile

class TestWildcardManager:
    def test_is_wildcard(self):
        wm = WildcardManager(Path("test_data/wildcards"))
        assert wm.is_wildcard("__test__")
        assert not wm.is_wildcard("test")


        
    def test_get_all_values(self):
        with mock.patch("prompts.wildcardmanager.WildcardManager.match_files") as mock_get_files:
            wildcard_files = [
                WildcardFile(Path("test1.txt")),
                WildcardFile(Path("test2.txt")),
            ]
            mock_get_files.return_value = wildcard_files

            wildcard_files[0].get_wildcards = mock.Mock(return_value={"red", "green"})
            wildcard_files[1].get_wildcards = mock.Mock(return_value={"green", "blue"})

            wm = WildcardManager(Path("test_data/wildcards"))
            assert wm.get_all_values("test") == ["blue", "green", "red"]

    def test_match_files_with_missing_wildcard(self):
        wm = WildcardManager(Path("test_data/wildcards"))
        assert wm.match_files("__invalid_wildcard__") == []

    def test_get_all_values_with_missing_wildcard(self):
        wm = WildcardManager(Path("test_data/wildcards"))
        assert wm.get_all_values("__invalid_wildcard__") == []
    