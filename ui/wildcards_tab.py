from __future__ import annotations
import logging
import shutil
import random
import os
from modules import script_callbacks
import modules.scripts as scripts
import gradio as gr
import json
from pathlib import Path
from glob import glob

from send2trash import send2trash

from prompts.wildcardmanager import WildcardManager

logger = logging.getLogger(__name__)

wildcard_manager: WildcardManager

BASE_DIR = scripts.basedir()


def initialize(manager: WildcardManager):
    global tree_json
    global wildcard_manager

    wildcard_manager = manager
    tree_json = load_hierarchy()
    script_callbacks.on_ui_tabs(on_ui_tabs)


def load_hierarchy():
    hierarchy = wildcard_manager.get_wildcard_hierarchy()
    tree_json = format_json(hierarchy)
    return tree_json


def format_json(js):
    if js is None:
        return []

    tree = []

    leaves, hierarchy = js

    for leaf in leaves:
        tree.append({"name": leaf, "children": []})

    for key, val in hierarchy.items():
        branch = {"name": key, "children": format_json(val)}
        tree.append(branch)

    return tree


def on_ui_tabs():
    header_html = f"""
    <p>Manage wildcards for Dynamic Prompts</p>
    <ol>
        <li>1. Create your wildcard library by copying a collection using the dropdown below.</li>
        <li>2. Click on any of the files that appear in the tree to edit them.</li>
        <li>3. Use the wildcard in your script by typing the name of the file or copying the text from the Wildcards file text box</li>
        <li>4. Optional - add your own wildcards files to the {wildcard_manager._path} folder</li>
    </ol>
    """

    available_collections = [str(c) for c in wildcard_manager.get_collections()]
    with gr.Blocks() as wildcards_tab:
        with gr.Group(elem_id="dynamic-prompting"):
            with gr.Row():
                with gr.Column():
                    gr.HTML(header_html)
                    html = gr.HTML("", elem_id="html_id")
                    collection_dropdown = gr.Dropdown(
                        choices=available_collections,
                        type="value",
                        label="Select a collection",
                        elem_id="collection_dropdown",
                    )
                    with gr.Row():
                        collection_copy_button = gr.Button(
                            "Copy collection",
                            full_width=True,
                            elem_id="collection_copy_button",
                        )
                        overwrite_checkbox = gr.Checkbox(
                            label="Overwrite existing",
                            elem_id="overwrite_checkbox",
                            value=False,
                        )
                    with gr.Row():
                        load_tree = gr.Button(
                            "Refresh wildcards", elem_id="load_tree_button"
                        )
                        delete_tree = gr.Button(
                            "Delete all wildcards", elem_id="delete_tree_button"
                        )
                with gr.Column():
                    file_name = gr.Textbox(
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

        hidden_hierarchy = gr.Textbox(
            json.dumps(tree_json), elem_id="tree_textbox", visible=False
        )
        hidden_textbox = gr.Textbox("", elem_id="scratch_textbox", visible=False)

        hidden_action_button = gr.Button(
            "Action", elem_id="action_button", visible=False
        )

        load_tree.click(
            load_tree_callback,
            inputs=[],
            outputs=[hidden_textbox],
        )

        delete_tree.click(
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


def create_payload(action, result, payload):
    return json.dumps(
        {
            "action": action,
            "result": result,
            "payload": payload,
            "id": random.randint(0, 1000000),
        }
    )


def copy_collection_callback(overwrite_checkbox, collection):
    collection_paths = wildcard_manager.get_collection_dirs()
    if collection in collection_paths:
        collection_path = collection_paths[collection]
        for file in collection_path.glob("**/*"):
            if file.is_file():
                target_path = wildcard_manager._path / file.relative_to(collection_path)
                if not target_path.exists() or overwrite_checkbox:
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(file, target_path)

        return load_tree_callback()

    return create_payload("copy collection", "failed", json.dumps([]))


def load_tree_callback():
    hierarchy = load_hierarchy()

    return create_payload("load tree", "success", json.dumps(hierarchy))


def delete_tree_callback(confirm_delete):
    if confirm_delete == "True":
        send2trash(wildcard_manager._path)
        wildcard_manager._path.mkdir(parents=True, exist_ok=True)
        hierarchy = load_hierarchy()

        return create_payload("load tree", "success", json.dumps(hierarchy))

    return create_payload("delete tree", "failed", json.dumps([]))


def receive_tree_event(s):
    js = json.loads(s)
    values = wildcard_manager.get_all_values(js["name"])
    path = wildcard_manager.wildcard_to_path(js["name"])
    values = path.read_text()
    return values


def save_file_callback(js):
    try:
        wildcard_json = js
        js = json.loads(wildcard_json)

        if "wildcard" in js and "name" in js["wildcard"]:
            wildcard = js["wildcard"]["name"]
            path = wildcard_manager.wildcard_to_path(wildcard)

            contents = js["contents"]

            with path.open("w") as f:
                contents = contents.splitlines()
                for c in contents:
                    f.write(c.strip() + os.linesep)
    except Exception as e:
        logger.exception(e)
