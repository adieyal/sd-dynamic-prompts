from __future__ import annotations

import json
import logging
import random
import shutil
from pathlib import Path
from typing import Any

import gradio as gr
import modules.scripts as scripts
from dynamicprompts.wildcards import WildcardManager
from dynamicprompts.wildcards.collection import WildcardTextFile
from dynamicprompts.wildcards.tree import WildcardTreeNode
from modules import script_callbacks
from send2trash import send2trash

logger = logging.getLogger(__name__)

wildcard_manager: WildcardManager

collections_path = Path(scripts.basedir()) / "collections"


def get_collection_dirs() -> dict[str, Path]:
    """
    Get a mapping of name -> subdirectory path for the extension's collections/ directory.
    """
    return {
        str(pth.relative_to(collections_path)): pth
        for pth in collections_path.iterdir()
        if pth.is_dir()
    }


def initialize(manager: WildcardManager):
    global wildcard_manager
    wildcard_manager = manager
    script_callbacks.on_ui_tabs(on_ui_tabs)


def _format_node_for_json(
    wildcard_manager: WildcardManager,
    node: WildcardTreeNode,
) -> list[dict]:
    collections = [
        {
            "name": node.qualify_name(coll),
            "wrappedName": wildcard_manager.to_wildcard(node.qualify_name(coll)),
            "children": [],
        }
        for coll in sorted(node.collections)
    ]
    child_items = [
        {"name": name, "children": _format_node_for_json(wildcard_manager, child_node)}
        for name, child_node in sorted(node.child_nodes.items())
    ]
    return [*collections, *child_items]


def get_wildcard_hierarchy_for_json():
    return _format_node_for_json(wildcard_manager, wildcard_manager.tree.root)


def on_ui_tabs():
    header_html = f"""
    <p>Manage wildcards for Dynamic Prompts</p>
    <ol>
        <li>Create your wildcard library by copying a collection using the dropdown below.</li>
        <li>Click on the files that appear in the tree to edit them.</li>
        <li>Use the wildcard in your script by typing the name of the file or copying the text from the Wildcards file text box</li>
        <li>Optional - add your own wildcards files to the {wildcard_manager.path} folder</li>
    </ol>
    """

    with gr.Blocks() as wildcards_tab:
        with gr.Group(elem_id="dynamic-prompting"):
            with gr.Row():
                with gr.Column():
                    gr.HTML(header_html)
                    gr.HTML("", elem_id="html_id")
                    collection_dropdown = gr.Dropdown(
                        choices=sorted(get_collection_dirs()),
                        type="value",
                        label="Select a collection",
                    )
                    with gr.Row():
                        collection_copy_button = gr.Button(
                            "Copy collection",
                            full_width=True,
                        )
                        overwrite_checkbox = gr.Checkbox(
                            label="Overwrite existing",
                            value=False,
                        )
                    with gr.Row():
                        refresh_wildcards_button = gr.Button(
                            "Refresh wildcards",
                            elem_id="load_tree_button",
                        )
                        delete_tree_button = gr.Button(
                            "Delete all wildcards",
                            elem_id="delete_tree_button",
                        )
                with gr.Column():
                    gr.Textbox(
                        "",
                        elem_id="file_name_id",
                        interactive=False,
                        label="Wildcards file",
                    )
                    file_edit_box = gr.Textbox(
                        "",
                        elem_id="file_edit_box_id",
                        lines=10,
                        interactive=True,
                        label="File editor",
                    )
                    save_button = gr.Button("Save wildcards", full_width=True)

        hidden_textbox = gr.Textbox("", elem_id="scratch_textbox", visible=False)

        hidden_action_button = gr.Button(
            "Action",
            elem_id="action_button",
            visible=False,
        )

        refresh_wildcards_button.click(
            refresh_wildcards_callback,
            inputs=[],
            outputs=[hidden_textbox],
        )

        delete_tree_button.click(
            delete_tree_callback,
            _js="deleteTree",
            inputs=[hidden_textbox],
            outputs=[hidden_textbox],
        )

        hidden_action_button.click(
            receive_tree_event,
            _js="receiveTreeEvent",
            inputs=[hidden_textbox],
            outputs=[file_edit_box],
        )

        save_button.click(
            save_file_callback,
            _js="saveFile",
            inputs=[file_edit_box],
            outputs=[hidden_textbox],
        )

        collection_copy_button.click(
            copy_collection_callback,
            inputs=[overwrite_checkbox, collection_dropdown],
            outputs=[hidden_textbox],
        )

    return ((wildcards_tab, "Wildcards Manager", "wildcards_tab"),)


def create_payload(action: str, result: str, payload: Any = None):
    return json.dumps(
        {
            "action": action,
            "result": result,
            "payload": payload,
            "id": random.randint(0, 1000000),
        },
    )


def copy_collection_callback(overwrite_checkbox, collection):
    collection_paths = get_collection_dirs()
    if collection in collection_paths:
        collection_path = collection_paths[collection]
        for file in collection_path.glob("**/*"):
            if file.is_file():
                target_path = (
                    wildcard_manager.path
                    / collection
                    / file.relative_to(collection_path)
                )
                if not target_path.exists() or overwrite_checkbox:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(file, target_path)

        return refresh_wildcards_callback()

    return create_payload("copy collection", "failed")


def refresh_wildcards_callback():
    wildcard_manager.clear_cache()
    return create_payload(
        "load tree",
        "success",
        json.dumps(get_wildcard_hierarchy_for_json()),
    )


def delete_tree_callback(confirm_delete):
    if confirm_delete == "True":
        send2trash(wildcard_manager.path)
        wildcard_manager.path.mkdir(parents=True, exist_ok=True)
        return refresh_wildcards_callback()
    return create_payload("delete tree", "failed")


def receive_tree_event(event_str: str):
    try:
        event = json.loads(event_str)
        wf = wildcard_manager.get_file(event["name"])
        if isinstance(wf, WildcardTextFile):
            # For text files, just return the raw text.
            return wf.read_text()
        # Otherwise, return a preview of the values,
        # with a header to indicate that the file can't be edited.
        values = "\n".join(wf.get_values())
        return f"# File can't be edited\n{values}"
    except Exception as e:
        logger.exception(e)
        return "# Failed to load file"


def save_file_callback(event_str: str):
    try:
        event = json.loads(event_str)
        wf = wildcard_manager.get_file(event["wildcard"]["name"])
        if isinstance(wf, WildcardTextFile):
            wf.write_text(event["contents"].strip())
        else:
            raise Exception("Can't save non-text files")
        return refresh_wildcards_callback()
    except Exception as e:
        logger.exception(e)
