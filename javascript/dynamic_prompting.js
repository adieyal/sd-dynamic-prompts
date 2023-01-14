sddp_loaded = false
sddp_wildcards_loaded = false
sddp_ui = null

onUiUpdate(function () {
  if (!sddp_loaded) {
    gradioApp().getElementById("dynamic-prompts-enabled").append("Complete documentation is available at https://github.com/adieyal/sd-dynamic-prompts. Please report any issues on GitHub.")
    gradioApp().getElementById("is-combinatorial").append("Generate all possible prompts up to a maximum of Batch count * Batch size)")
    gradioApp().getElementById("is-magicprompt").append("Automatically update your prompt with interesting modifiers. (Runs slowly the first time)")
    gradioApp().getElementById("is-feelinglucky").append("Generate random prompts from lexica.art (your prompt is used as a search query).")
    gradioApp().getElementById("is-fixed-seed").append("Use the same seed for all prompts in this batch")
    gradioApp().getElementById("write-prompts").append("Write all generated prompts to a file")
    gradioApp().getElementById("unlink-seed-from-prompt").append("If this is set, then random prompts are generated, even if the seed is the same.")
    gradioApp().getElementById("disable-negative-prompt").append("Don't use prompt magic on negative prompts.")
    gradioApp().getElementById("no-image-generation").append("Disable image generation. Useful if you only want to generate text prompts.")
    gradioApp().getElementById("is-attention-grabber").append("Add emphasis to a randomly selected keyword in the prompt.")
    gradioApp().getElementById("write-raw-template").append("Write template into image metadata.")

    sddp_ui = new SDDPUI()
    sddp_loaded = true;
  }
})

onUiTabChange(function (x) {
  if (!sddp_wildcards_loaded && uiCurrentTab.innerText =='Wildcards Manager') {
      gradioApp().querySelector("#load_tree_button").click()
      sddp_wildcards_loaded = true;
  }
})

class SDDPUI {
  constructor() {
    this._scratch = gradioApp().querySelector("#scratch_textbox textarea")
    this._tree_textbox = gradioApp().querySelector("#tree_textbox textarea")
    this._timeout = setInterval(this._onTick.bind(this), 500)
    this._last_message = null
    this._tree = null
  }

  _onTick() {
    let msg = this._scratch.value
    if (msg != "") {
      msg = JSON.parse(msg)
      if (msg.id != this._last_message) {
        this._last_message = msg.id;
        if (msg.action == "load tree" && msg.result == 'success') {
          let tree_js = JSON.parse(msg.payload)
          this.setupTree(tree_js)
        }
      }
    }
  }

  setupTree(json) {
    if (this._tree == null) {
      let treeDiv = gradioApp().querySelector("#html_id")
      this._tree = new TreeView(json, treeDiv)
      this._tree.on('select', function (x) { nodeSelected(x) });
    } else {
      this._tree.data = json
      this._tree.render()
    }
  }

  deleteTree() {
    let response = confirm("Are you sure you want to delete all your wildcards?")
    return response
  }
}

function nodeSelected(x) {
  if (x["data"] != undefined) {
    gradioApp().querySelector("#scratch_textbox textarea").value = JSON.stringify(x["data"], null, 2)
    gradioApp().querySelector("#action_button").click()
  }
}

function receiveTreeEvent(x) {
  let js = gradioApp().querySelector("#scratch_textbox textarea").value
  let json = JSON.parse(js)
  let filenameElement = gradioApp().querySelector("#file_name_id textarea")
  filenameElement.value = json["name"]

  return JSON.stringify(json)
}

function deleteTree() {
  return sddp_ui.deleteTree()
}

function saveFile(x) {
  let js = gradioApp().querySelector("#scratch_textbox textarea").value
  let json = JSON.parse(js)
  let contents = gradioApp().querySelector("#file_edit_box_id textarea").value

  return JSON.stringify({
    "wildcard": json,
    "contents": contents
  })
}
