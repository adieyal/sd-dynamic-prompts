from __future__ import annotations

import argparse
import json
import os
import re
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


def get_wildcard_dir() -> Path:
    current_path = Path.cwd()
    if current_path.name == "_tools":
        current_path = current_path.parent

    collections_dir = current_path / "wildcards"

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


def download_pantry(url: str, target_subdirectory: Path, filename: str):
    filepath = target_subdirectory / filename

    try:
        with urllib.request.urlopen(url) as response:
            with open(filepath, "wb") as f:
                shutil.copyfileobj(response, f)
                print(f"Successfully downloaded {filename}")
    except urllib.error.HTTPError as e:
        print(f"Error downloading {filename}: {e.code} {e.reason}")


def download_from_zip(url: str, destination_path: Path, root_directory: str = ""):
    with urllib.request.urlopen(url) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
            tmp_file_path = tmp_file.name

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(tmp_file_path, "r") as zip_ref:
            zip_ref.extractall(tmp_dir)

        found_subdirectory = False
        for root, dirs, _ in os.walk(tmp_dir):
            if root_directory in dirs:
                found_subdirectory = True
                source_dir = os.path.join(root, root_directory)
                if destination_path.exists():
                    overwrite = input(
                        f"The directory {destination_path} already exists. Overwrite? (y/n) ",
                    )
                    if overwrite.strip().lower() != "y":
                        print("Skipping directory copy.")
                        return
                    else:
                        shutil.rmtree(destination_path)
                shutil.copytree(source_dir, destination_path)
                print(f"Copied {source_dir} to {destination_path}")
                break

        if not found_subdirectory:
            print(
                f"Could not find the '{root_directory}' root_directory in the downloaded archive.",
            )

    os.remove(tmp_file_path)


def download_from_web(url: str, destination_path: str):
    """
    Currently limited to downloading pages that look like: https://rentry.org/NAIwildcards/raw
    """

    def download_text_file(url):
        with urllib.request.urlopen(url) as response:
            content = response.read().decode("utf-8")
        return content

    def extract_raw_urls(content):
        url_descriptions = []
        urls = re.findall(
            r"(\w[\w\s-]*)\s-\s(https?://(?:pastebin\.com|rentry\.org)/\S+)",
            content,
        )
        for description, url in urls:
            if "pastebin.com" in url:
                raw_url = url.replace("pastebin.com/", "pastebin.com/raw/")
            else:
                raw_url = url.rstrip("/") + "/raw"

            file_name = description.strip().replace(" ", "_").lower() + ".txt"
            url_descriptions.append((file_name, raw_url))

        return url_descriptions

    def download_and_save_files(url_descriptions, save_directory):
        for file_name, raw_url in url_descriptions:
            with urllib.request.urlopen(raw_url) as response:
                file_path = destination_path / file_name
                with open(file_path, "wb") as file:
                    shutil.copyfileobj(response, file)
                print(f"Downloaded and saved {file_name}")

    content = download_text_file(url)
    raw_urls = extract_raw_urls(content)
    download_and_save_files(raw_urls, destination_path)


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
                    repositories[choice - 1][1],  # url
                    repositories[choice - 1][2],  # root_directory
                    repositories[choice - 1][3],  # target_subdirectory
                )
            else:
                print("Invalid choice, please try again.")
        except ValueError:
            print("Invalid choice, please try again.")


def download_and_copy(url: str, root_directory, destination_path: Path):
    if url.endswith((".json", ".yaml")):
        filename = url.split("/")[-1]
        download_pantry(url, destination_path, filename)
    elif url.endswith(".zip"):
        download_from_zip(url, destination_path, root_directory)
    else:
        try:
            download_from_web(url, destination_path)
        except Exception as e:
            print(f"Error downloading file: {url}\n{e}")


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
        return repo["url"], repo["root_directory"], repo["target_subdirectory"]
    else:
        print(f"Collection '{collection_name}' not found.")
        exit(1)


if __name__ == "__main__":
    repositories = load_repositories()
    args = parse_args()
    collection_name = args.name

    if collection_name:
        url, root_directory, target_subdirectory = download_by_name(collection_name)
    else:
        url, root_directory, target_subdirectory = show_menu(repositories)

    destination_path = get_wildcard_dir() / target_subdirectory
    download_and_copy(url, root_directory, destination_path)
