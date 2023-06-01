/* global gradioApp, get_uiCurrentTabContent, onUiUpdate, onUiLoaded */
// prettier-ignore
const SDDP_HELP_TEXTS = {
  "sddp-disable-negative-prompt": "Don't use prompt magic on negative prompts.",
  "sddp-dynamic-prompts-enabled": "Complete documentation is available at https://github.com/adieyal/sd-dynamic-prompts. Please report any issues on GitHub.",
  "sddp-is-attention-grabber": "Add emphasis to a randomly selected keyword in the prompt.",
  "sddp-is-combinatorial": "Generate all possible prompt combinations.",
  "sddp-is-feelinglucky": "Generate random prompts from lexica.art (your prompt is used as a search query).",
  "sddp-is-fixed-seed": "Use the same seed for all prompts in this batch",
  "sddp-is-magicprompt": "Automatically update your prompt with interesting modifiers. (Runs slowly the first time)",
  "sddp-magic-prompt-model": "Note: Each model will download between 300mb and 1.4gb of data on first use.",
  "sddp-no-image-generation": "Disable image generation. Useful if you only want to generate text prompts. (1 image will still be generated to keep Auto1111 happy.).",
  "sddp-unlink-seed-from-prompt": "If this is set, then random prompts are generated, even if the seed is the same.",
  "sddp-write-prompts": "Write all generated prompts to a file",
  "sddp-write-raw-template": "Write template into image metadata.",
};

class SDDPTreeView {
  /**
   * @constructor
   * @property {object} handlers The attached event handlers
   * @property {object} data The JSON object that represents the tree structure
   * @property {Element} node The DOM element to render the tree in
   */
  constructor(data, node) {
    this.handlers = {};
    this.node = node;
    this.data = data;
    this.render();
  }

  /**
   * Renders the tree view in the DOM
   */
  render = () => {
    const container = this.node;
    container.innerHTML = "";
    this.data.forEach((item) => container.appendChild(this.renderNode(item)));
    [...container.querySelectorAll(".tree-leaf-text,.tree-expando")].forEach(
      (node) => node.addEventListener("click", this.handleClickEvent),
    );
  };

  renderNode = (item) => {
    const leaf = document.createElement("div");
    const content = document.createElement("div");
    const text = document.createElement("div");
    const expando = document.createElement("div");
    leaf.setAttribute("class", "tree-leaf");
    content.setAttribute("class", "tree-leaf-content");
    text.setAttribute("class", "tree-leaf-text");
    const { children, name, expanded } = item;
    text.textContent = name;
    expando.setAttribute("class", `tree-expando ${expanded ? "expanded" : ""}`);
    expando.textContent = expanded ? "-" : "+";
    content.appendChild(expando);
    content.appendChild(text);
    leaf.appendChild(content);
    if (children?.length > 0) {
      const childrenDiv = document.createElement("div");
      childrenDiv.setAttribute("class", "tree-child-leaves");
      children.forEach((child) => {
        childrenDiv.appendChild(this.renderNode(child));
      });
      if (!expanded) {
        childrenDiv.classList.add("hidden");
      }
      leaf.appendChild(childrenDiv);
    } else {
      expando.classList.add("hidden");
      content.setAttribute("data-item", JSON.stringify(item));
    }
    return leaf;
  };

  handleClickEvent = (event) => {
    const parent = (event.target || event.currentTarget).parentNode;
    const leaves = parent.parentNode.querySelector(".tree-child-leaves");
    if (leaves) {
      this.setSubtreeVisibility(
        parent,
        leaves,
        leaves.classList.contains("hidden"),
      );
    } else {
      this.emit("select", {
        target: event,
        data: JSON.parse(parent.getAttribute("data-item")),
      });
    }
  };

  /**
   * Expands/collapses by the expando or the leaf text
   * @param {Element} node The parent node that contains the leaves
   * @param {Element} leaves The leaves wrapper element
   * @param {boolean} visible Expand or collapse?
   * @param {boolean} skipEmit Skip emitting the event?
   */
  setSubtreeVisibility(node, leaves, visible, skipEmit = false) {
    leaves.classList.toggle("hidden", !visible);
    node.querySelector(".tree-expando").textContent = visible ? "+" : "-";
    if (skipEmit) {
      return;
    }
    this.emit(visible ? "expand" : "collapse", {
      target: node,
      leaves,
    });
  }

  on(name, callback, context = null) {
    const handlers = this.handlers[name] || [];
    handlers.push({ callback, context });
    this.handlers[name] = handlers;
  }

  off(name, callback) {
    this.handlers[name] = (this.handlers[name] || []).filter(
      (handle) => handle.callback !== callback,
    );
  }

  emit(name, ...args) {
    (this.handlers[name] || []).forEach((handle) => {
      window.setTimeout(() => {
        handle.callback.apply(handle.context, args);
      }, 0);
    });
  }
}

class SDDP_UI {
  constructor() {
    this.helpTextsConfigured = false;
    this.wildcardsLoaded = false;
    this.messageReadTimer = null;
    this.lastMessage = null;
    this.treeView = null;
  }

  configureHelpTexts() {
    if (this.helpTextsConfigured) {
      return;
    }
    // eslint-disable-next-line guard-for-in,no-restricted-syntax
    for (const elemId in SDDP_HELP_TEXTS) {
      const elem = gradioApp().getElementById(elemId);
      if (elem) {
        elem.setAttribute("title", SDDP_HELP_TEXTS[elemId]);
      } else {
        return; // Didn't find all elements...
      }
    }
    this.helpTextsConfigured = true;
  }

  getInboxMessageText() {
    return gradioApp().querySelector(
      "#sddp-wildcard-s2c-message-textbox textarea",
    )?.value;
  }

  formatPayload(payload) {
    return JSON.stringify({ ...payload, id: Math.floor(+new Date()) }, null, 2);
  }

  sendAction(payload) {
    const outbox = gradioApp().querySelector(
      "#sddp-wildcard-c2s-message-textbox textarea",
    );
    outbox.value = this.formatPayload(payload);
    // See https://github.com/AUTOMATIC1111/stable-diffusion-webui/commit/38b7186e6e3a4dffc93225308b822f0dae43a47d
    window.updateInput?.(outbox);
    gradioApp().querySelector("#sddp-wildcard-c2s-action-button").click();
  }

  requestWildcardTree() {
    gradioApp().querySelector("#sddp-wildcard-load-tree-button")?.click();
  }

  doReadMessage() {
    const messageText = this.getInboxMessageText();
    if (!messageText || this.lastMessage === messageText) {
      return;
    }
    this.lastMessage = messageText;
    const message = JSON.parse(messageText);
    const { action, success } = message;
    if (action === "load tree" && success) {
      this.setupTree(message.tree);
    } else if (action === "load file" && success) {
      this.loadFileIntoEditor(message);
    } else {
      console.warn("SDDP: Unknown message", message);
    }
  }

  setupTree(content) {
    let { treeView } = this;
    if (!this.treeView) {
      const treeDiv = gradioApp().querySelector("#sddp-wildcard-tree");
      if (treeDiv) {
        treeView = new SDDPTreeView(content, treeDiv);
        treeView.on("select", this.onSelectNode.bind(this), null);
        this.treeView = treeView;
      }
    } else {
      treeView.data = content;
      treeView.render();
    }
  }

  onSelectNode(node) {
    if (node.data?.name) {
      this.sendAction({
        action: "load file",
        name: node.data.name,
      });
    }
  }

  loadFileIntoEditor(message) {
    const editor = gradioApp().querySelector(
      "#sddp-wildcard-file-editor textarea",
    );
    const name = gradioApp().querySelector("#sddp-wildcard-file-name textarea");
    const saveButton = gradioApp().querySelector("#sddp-wildcard-save-button");
    const { contents, wrapped_name: wrappedName, can_edit: canEdit } = message;
    editor.value = contents;
    name.value = wrappedName;
    editor.readOnly = !canEdit;
    saveButton.disabled = !canEdit;

    // See https://github.com/AUTOMATIC1111/stable-diffusion-webui/commit/38b7186e6e3a4dffc93225308b822f0dae43a47d
    window.updateInput?.(editor);
    window.updateInput?.(name);
  }

  onWildcardManagerTabActivate() {
    if (!this.wildcardsLoaded) {
      this.requestWildcardTree();
      this.wildcardsLoaded = true;
    }
    if (!this.messageReadTimer) {
      this.messageReadTimer = setInterval(this.doReadMessage.bind(this), 120);
    }
  }

  onDeleteTreeClick() {
    // eslint-disable-next-line no-restricted-globals,no-alert
    const sure = confirm("Are you sure you want to delete all your wildcards?");
    return this.formatPayload({ action: "delete tree", sure });
  }

  onSaveFileClick() {
    const json = JSON.parse(this.getInboxMessageText());
    const contents = gradioApp().querySelector(
      "#sddp-wildcard-file-editor textarea",
    ).value;
    return this.formatPayload({
      action: "save wildcard",
      wildcard: json,
      contents,
    });
  }
}

const SDDP = new SDDP_UI();
window.SDDP = SDDP;

(
  window.onAfterUiUpdate || // sd-webui 1.3.0+
  window.onUiUpdate
)(() => {
  SDDP.configureHelpTexts();
  // Work around a bug in get_uiCurrentTabContent() and nested tabs
  // (can be replaced with get_uiCurrentTabContent() if
  // https://github.com/AUTOMATIC1111/stable-diffusion-webui/pull/10863 is merged)
  const currentVisibleTopLevelTab = gradioApp().querySelector(
    '#tabs > .tabitem[id^=tab_]:not([style*="display: none"])',
  );
  if (currentVisibleTopLevelTab?.id === "tab_sddp-wildcard-manager") {
    SDDP.onWildcardManagerTabActivate();
  }
});
