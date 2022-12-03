from __future__ import annotations
import logging
from modules import script_callbacks
import gradio as gr
import json
from pathlib import Path

from prompts.wildcardmanager import WildcardManager

logger = logging.getLogger(__name__)

wildcard_manager: WildcardManager


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
    <p>This is a work in progress. Please <a href="https://github.com/adieyal/sd-dynamic-prompts/issues">report</a> any bugs.</p>
    <br>
    <p>If you don't see any wildcards here, make sure you place wildcard files ending in .txt in a folder called "{wildcard_manager._path}". The collections folder contains thousands of wildcards which you can use or modify.</p>
    """
    with gr.Blocks() as wildcards_tab:
        with gr.Group(elem_id="dynamic-prompting"):
            with gr.Row():
                with gr.Column():
                    gr.HTML(header_html)
                    html = gr.HTML("", elem_id="html_id")
                    load_tree = gr.Button("Load", full_width=True, elem_id="load_tree_button")
                with gr.Column():
                    file_edit_box = gr.Textbox(
                        "", elem_id="file_edit_box_id", lines=10, interactive=True
                    )
                    save_button = gr.Button("Save wildcards", full_width=True)

        hidden_hierarchy = gr.Textbox(
            json.dumps(tree_json), elem_id="tree_textbox", visible=False
        )
        hidden_textbox = gr.Textbox(
            "", elem_id="scratch_textbox", visible=False
        )

        hidden_action_button = gr.Button(
            "Action", elem_id="action_button", visible=False
        )

        load_tree.click(
            load_tree_callback, _js="setupTree", inputs=[hidden_hierarchy], outputs=[hidden_textbox],
        )

        hidden_action_button.click(
            receive_tree_event,
            _js="receiveTreeEvent",
            inputs=[hidden_textbox],
            outputs=[file_edit_box],
        )

        save_button.click(
            save_file_callback, _js="saveFile", inputs=[file_edit_box], outputs=[hidden_textbox]
        )

    return ((wildcards_tab, "Wildcards Manager", "wildcards_tab"),)

def load_tree_callback(js):
    hierarchy = load_hierarchy()

    return json.dumps(hierarchy)

def receive_tree_event(s):
    s = s.replace("'", '"')
    js = json.loads(s)
    values = wildcard_manager.get_all_values(js["name"])
    path = wildcard_manager.wildcard_to_path(js["name"])
    values = path.read_text()
    return values


def save_file_callback(js):
    try:
        wildcard_json = js.replace("'", '"')
        js = json.loads(wildcard_json)

        if "wildcard" in js and "name" in js["wildcard"]:
            wildcard = js["wildcard"]["name"]
            path = wildcard_manager.wildcard_to_path(wildcard)

            contents=js["contents"]

            with path.open("w") as f:
                f.write(contents)
    except Exception as e:
        logger.exception(e)

