"""
Import collections/nsp from https://github.com/WASasquatch/noodle-soup-prompts.

This script is intended to be run from the root of the repository;
it's best to delete the existing collections/nsp folder first to avoid
duplicate entries.

You would then import these via the WebUI to your wildcards collection.
"""
import collections
import requests
import os


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
    grouped_tags = get_grouped_tags()

    for tag_group_name, tags_in_group in sorted(grouped_tags.items()):
        tag_group_name = "nsp" if len(tags_in_group) == 1 else f"nsp-{tag_group_name}"
        for tag, entries in sorted(tags_in_group):
            filename = f"./collections/nsp/{tag_group_name}/{tag}.txt"
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, "w", encoding="utf-8") as f:
                for entry in sorted(entries):
                    f.write(f"{entry}\n")
            print(f"{filename}: {len(entries)} entries")


if __name__ == "__main__":
    main()
