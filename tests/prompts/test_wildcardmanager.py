from unittest import mock
from pathlib import Path

from prompts.wildcardmanager import WildcardManager, WildcardFile

class TestWildcardManager:
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