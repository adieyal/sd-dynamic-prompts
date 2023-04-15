from __future__ import annotations

import json
import logging
import random
import shutil
import traceback
from pathlib import Path

import gradio as gr
import modules.scripts as scripts
from dynamicprompts.wildcards import WildcardManager
from dynamicprompts.wildcards.collection import WildcardTextFile
from dynamicprompts.wildcards.tree import WildcardTreeNode
from modules import script_callbacks
from send2trash import send2trash

from sd_dynamic_prompts.element_ids import make_element_id

COPY_COLLECTION_ACTION = "copy collection"
LOAD_FILE_ACTION = "load file"
LOAD_TREE_ACTION = "load tree"
MESSAGE_PROCESSING_ACTION = "message processing"

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
        with gr.Group():
            with gr.Row():
                with gr.Column():
                    gr.HTML(header_html)
                    gr.HTML("", elem_id=make_element_id("wildcard-tree"))
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
                            elem_id=make_element_id("wildcard-load-tree-button"),
                        )
                        delete_tree_button = gr.Button(
                            "Delete all wildcards",
                            elem_id=make_element_id("wildcard-delete-tree-button"),
                        )
                with gr.Column():
                    gr.Textbox(
                        "",
                        elem_id=make_element_id("wildcard-file-name"),
                        interactive=False,
                        label="Wildcards file",
                    )
                    gr.Textbox(
                        "",
                        elem_id=make_element_id("wildcard-file-editor"),
                        lines=10,
                        interactive=True,
                        label="File editor",
                    )
                    save_button = gr.Button(
                        "Save wildcards",
                        full_width=True,
                        elem_id=make_element_id("wildcard-save-button"),
                    )

        # Hidden scratch textboxes and button for communication with JS bits.
        client_to_server_message_textbox = gr.Textbox(
            "",
            elem_id=make_element_id("wildcard-c2s-message-textbox"),
            visible=False,
        )
        server_to_client_message_textbox = gr.Textbox(
            "",
            elem_id=make_element_id("wildcard-s2c-message-textbox"),
            visible=False,
        )
        client_to_server_message_action_button = gr.Button(
            "Action",
            elem_id=make_element_id("wildcard-c2s-action-button"),
            visible=False,
        )

        # Handle the frontend sending a message
        client_to_server_message_action_button.click(
            handle_message,
            inputs=[client_to_server_message_textbox],
            outputs=[server_to_client_message_textbox],
        )

        refresh_wildcards_button.click(
            refresh_wildcards_callback,
            inputs=[],
            outputs=[server_to_client_message_textbox],
        )

        delete_tree_button.click(
            delete_tree_callback,
            _js="SDDP.onDeleteTreeClick",
            inputs=[client_to_server_message_textbox],
            outputs=[server_to_client_message_textbox],
        )

        save_button.click(
            save_file_callback,
            _js="SDDP.onSaveFileClick",
            inputs=[client_to_server_message_textbox],
            outputs=[server_to_client_message_textbox],
        )

        collection_copy_button.click(
            copy_collection_callback,
            inputs=[overwrite_checkbox, collection_dropdown],
            outputs=[server_to_client_message_textbox],
        )

    return ((wildcards_tab, "Wildcards Manager", "sddp-wildcard-manager"),)


def create_payload(*, action: str, success: bool, **rest) -> str:
    return json.dumps(
        {
            "id": random.randint(0, 1000000),
            "action": action,
            "success": success,
            **rest,
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

    return create_payload(
        action=COPY_COLLECTION_ACTION,
        success=False,
    )


def refresh_wildcards_callback():
    wildcard_manager.clear_cache()
    return create_payload(
        action=LOAD_TREE_ACTION,
        success=True,
        tree=get_wildcard_hierarchy_for_json(),
    )


def delete_tree_callback(confirm_delete):
    if confirm_delete == "True":
        send2trash(wildcard_manager.path)
        wildcard_manager.path.mkdir(parents=True, exist_ok=True)
        return refresh_wildcards_callback()
    return create_payload(action="delete tree", success=False)


def handle_message(event_str: str) -> str:
    try:
        event = json.loads(event_str)
        if event["action"] == LOAD_FILE_ACTION:
            return handle_load_wildcard(event)
        raise ValueError(f"Unknown event: {event}")
    except Exception as e:
        traceback.print_exc()
        return create_payload(
            action=MESSAGE_PROCESSING_ACTION,
            success=False,
            message=f"Error processing message: {e}",
        )


def handle_load_wildcard(event: dict) -> str:
    name = event["name"]
    wf = wildcard_manager.get_file(name)
    if isinstance(wf, WildcardTextFile):
        # For text files, just return the raw text.
        contents = wf.read_text()
        can_edit = True
    else:
        # Otherwise, return a preview of the values,
        # with a header to indicate that the file can't be edited.
        values = "\n".join(wf.get_values())
        contents = f"# File can't be edited\n{values}"
        can_edit = False

    return create_payload(
        action=LOAD_FILE_ACTION,
        success=True,
        contents=contents,
        can_edit=can_edit,
        name=name,
        wrapped_name=wildcard_manager.to_wildcard(name),
    )


def save_file_callback(event_str: str):
    try:
        event = json.loads(event_str)
        wf = wildcard_manager.get_file(event["wildcard"]["name"])
        if isinstance(wf, WildcardTextFile):
            wf.write_text(event["contents"].strip())
        else:
            raise Exception("Can't save non-text files")
        return handle_load_wildcard({"name": event["wildcard"]["name"]})
    except Exception as e:
        logger.exception(e)
