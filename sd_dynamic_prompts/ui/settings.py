from modules import shared


def on_ui_settings():
    section = "dynamicprompts", "Dynamic Prompts"
    shared.opts.add_option(
        key="dp_ignore_whitespace",
        info=shared.OptionInfo(
            False,
            label="Ignore whitespace in prompts: All newlines, tabs, and multiple spaces are replaced by a single space",
            section=section,
        ),
    )
    shared.opts.add_option(
        key="dp_write_raw_template",
        info=shared.OptionInfo(
            False,
            label="Save template to metadata: Write prompt template into the PNG metadata",
            section=section,
        ),
    )
    shared.opts.add_option(
        key="dp_write_prompts_to_file",
        info=shared.OptionInfo(
            False,
            label="Write prompts to file: Create a new .txt file for every batch containing the prompt template as well as the generated prompts.",
            section=section,
        ),
    )
    shared.opts.add_option(
        key="dp_parser_variant_start",
        info=shared.OptionInfo(
            "{",
            label="String to use as left bracket for parser variants, .e.g {variant1|variant2|variant3}",
            section=section,
        ),
    )
    shared.opts.add_option(
        key="dp_parser_variant_end",
        info=shared.OptionInfo(
            "}",
            label="String to use as right bracket for parser variants, .e.g {variant1|variant2|variant3}",
            section=section,
        ),
    )
    shared.opts.add_option(
        key="dp_parser_wildcard_wrap",
        info=shared.OptionInfo(
            "__",
            label="String to use as wrap for parser wildcard, .e.g __wildcard__",
            section=section,
        ),
    )
