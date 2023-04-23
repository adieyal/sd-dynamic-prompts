from download_collections import download_and_copy, download_by_name

if __name__ == "__main__":
    url, subdirectory, target_subdirectory = download_by_name("Noodlesoup Prompts")
    download_and_copy(url, subdirectory, target_subdirectory)
