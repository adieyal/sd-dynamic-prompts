"""
Import collections/nsp from https://github.com/WASasquatch/noodle-soup-prompts.

This script is intended to be run from the root of the repository;
it's best to delete the existing collections/nsp folder first to avoid
duplicate entries.

You would then import these via the WebUI to your wildcards collection.
"""
import collections
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)


def get_tag_group(tag):
    return tag.partition("-")[0]


def get_grouped_tags():
    pantry_url = "https://raw.githubusercontent.com/WASasquatch/noodle-soup-prompts/main/nsp_pantry.json"
    resp = requests.get(pantry_url)
    resp.raise_for_status()
    pantry = {tag.lower(): entries for (tag, entries) in resp.json().items()}
    grouped_tags = collections.defaultdict(list)
    for tag, entries in pantry.items():
        grouped_tags[get_tag_group(tag)].append((tag, entries))
    return grouped_tags


def main():
    count_files = 0
    current_path = Path.cwd()
    if current_path.name == "_tools":
        current_path = current_path.parent

    can_overwrite = None

    grouped_tags = get_grouped_tags()
    collections_dir = current_path / "collections"

    if not collections_dir.exists():
        print(
            "Could not find the collections directory. You should run this from the root of the repository",
        )
    else:
        for tag_group_name, tags_in_group in sorted(grouped_tags.items()):
            tag_group_name = (
                "nsp" if len(tags_in_group) == 1 else f"nsp-{tag_group_name}"
            )
            for tag, entries in sorted(tags_in_group):
                filename = collections_dir / f"./nsp/{tag_group_name}/{tag}.txt"
                filename.parent.mkdir(parents=True, exist_ok=True)

                if can_overwrite is None and filename.exists():
                    answer = input(
                        f"Skipping {filename} as it already exists. Should we overwrite existing files? (y/n)",
                    )
                    if answer.strip().lower() == "y":
                        can_overwrite = True
                    else:
                        can_overwrite = False

                if can_overwrite is None or can_overwrite is True:
                    count_files += 1
                    with filename.open("w", encoding="utf-8") as f:
                        for entry in sorted(entries):
                            try:
                                f.write(f"{entry}\n")
                            except UnicodeEncodeError:
                                logger.warning(f"Error writing {entry} to {filename}")

                    print(f"{filename}: {len(entries)} entries")

        print("")
        print(f"{count_files} files copied to {collections_dir}")
        if count_files > 0:
            print(
                "You should now import these via the WebUI to your wildcards collection using the Wildcards Manager tab.",
            )


if __name__ == "__main__":
    main()
