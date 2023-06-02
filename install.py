if __name__ == "__main__":
    try:
        from sd_dynamic_prompts.version_tools import install_requirements
    except ImportError:
        # This patching shouldn't be necessary, but who knows... See issue #486.
        import os
        import sys

        extension_dir = os.path.dirname(os.path.abspath(__file__))
        if extension_dir not in sys.path:
            sys.path.insert(0, extension_dir)
        from sd_dynamic_prompts.version_tools import install_requirements

    install_requirements()
