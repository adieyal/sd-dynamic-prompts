from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


def load_repositories(filename: str = "repositories.json") -> list[dict[str, str]]:
    tools_dir = get_tools_dir()
    repsitories_path = tools_dir / filename

    with open(repsitories_path) as f:
        return json.load(f)


def get_collections_dir() -> Path:
    current_path = Path.cwd()
    if current_path.name == "_tools":
        current_path = current_path.parent

    collections_dir = current_path / "collections"

    if not collections_dir.exists():
        print(
            "Could not find the collections directory. You should run this from the root of the repository",
        )
        exit(1)

    return collections_dir


def get_tools_dir() -> Path:
    current_path = Path.cwd()
    if current_path.name == "_tools":
        current_path = current_path.parent

    tools_dir = current_path / "_tools"

    if not tools_dir.exists():
        print(
            "Could not find the _tools directory. You should run this from the root of the repository",
        )
        exit(1)

    return tools_dir


def download_pantry(url: str, filename: str):
    collections_dir = get_collections_dir()
    filepath = collections_dir / filename

    try:
        with urllib.request.urlopen(url) as response:
            with open(filepath, "wb") as f:
                shutil.copyfileobj(response, f)
                print(f"Successfully downloaded {filename}")
    except urllib.error.HTTPError as e:
        print(f"Error downloading {filename}: {e.code} {e.reason}")


def download_directory(url: str, subdirectory: str = "", target_subdirectory: str = ""):
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
            tmp_file_path = tmp_file.name

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(tmp_file_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        found_subdirectory = False
        for root, dirs, _ in os.walk(tmp_dir):
            if subdirectory in dirs:
                found_subdirectory = True
                source_dir = os.path.join(root, subdirectory)
                collections_dir = get_collections_dir()
                target_dir = collections_dir / target_subdirectory
                if target_dir.exists():
                    overwrite = input(
                        f"The directory {target_dir} already exists. Overwrite? (y/n) ",
                    )
                    if overwrite.strip().lower() != "y":
                        print("Skipping directory copy.")
                        return
                    else:
                        shutil.rmtree(target_dir)
                shutil.copytree(source_dir, target_dir)
                print(f"Copied {source_dir} to {target_dir}")
                break

        if not found_subdirectory:
            print(
                f"Could not find the '{subdirectory}' subdirectory in the downloaded archive.",
            )

    os.remove(tmp_file_path)


def show_menu(repositories: list[dict[str, str]]) -> tuple[str, str, str]:
    repositories = [list(row.values()) for row in repositories]
    for index, (name, _, _, _) in enumerate(
        repositories,
    ):
        print(f"{index + 1}. {name}")
    while True:
        try:
            choice = int(input("Select a collection to download: "))
            if 1 <= choice <= len(repositories):
                return (
                    repositories[choice - 1][1],
                    repositories[choice - 1][2],
                    repositories[choice - 1][3],
                )
            else:
                print("Invalid choice, please try again.")
        except ValueError:
            print("Invalid choice, please try again.")


def download_and_copy(url: str, subdirectory: str = "", target_subdirectory: str = ""):
    if url.endswith((".json", ".yaml")):
        filename = url.split("/")[-1]
        download_pantry(url, filename)
    elif url.endswith(".zip"):
        download_directory(url, subdirectory, target_subdirectory)
    else:
        print(f"Unsupported file type: {url}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download collections from a given list.",
    )
    parser.add_argument(
        "--name",
        help="Specify the collection name to bypass the menu.",
        type=str,
    )
    return parser.parse_args()


def download_by_name(collection_name: str):
    repositories = load_repositories()
    repo = next(
        (repo for repo in repositories if repo["name"] == collection_name),
        None,
    )
    if repo:
        return repo["url"], repo["subdirectory"], repo["target_subdirectory"]
    else:
        print(f"Collection '{collection_name}' not found.")
        exit(1)


if __name__ == "__main__":
    repositories = load_repositories()
    args = parse_args()
    collection_name = args.name

    if collection_name:
        url, subdirectory, target_subdirectory = download_by_name(collection_name)
    else:
        url, subdirectory, target_subdirectory = show_menu(repositories)

    print(url)
    download_and_copy(url, subdirectory, target_subdirectory)
