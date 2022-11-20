sddp_loaded = false

onUiUpdate(function(){
  if (!sddp_loaded) {
    check_collapsibles();
    gradioApp().getElementById("is-combinatorial").append("Generate all possible prompts up to a maximum of Batch count * Batch size)")
    gradioApp().getElementById("is-magicprompt").append("Automatically update your prompt with interesting modifiers. (Runs slowly the first time)")
    gradioApp().getElementById("is-feelinglucky").append("Generate random prompts from lexica.art (your prompt is used as a search query).")
    gradioApp().getElementById("is-fixed-seed").append("Use the same seed for all prompts in this batch")
    gradioApp().getElementById("write-prompts").append("Write all generated prompts to a file")
    gradioApp().getElementById("unlink-seed-from-prompt").append("If this is set, then random prompts are generated, even if the seed is the same.")
    gradioApp().getElementById("disable-negative-prompt").append("Useful for I'm feeling lucky and Magic Prompt. If this is set, then negative prompts are not generated.")
    gradioApp().getElementById("no-image-generation").append("Disable image generation. Useful if you only want to generate text prompts.")
    gradioApp().getElementById("is-attention-grabber").append("Add emphasis to a randomly selected keyword in the prompt.")
    sddp_loaded = true;
  }
})

function check_collapsibles() {
  var coll = gradioApp().querySelectorAll(".collapsible")
  for (var i = 0; i < coll.length; i++) {
    coll[i].addEventListener("click", function() {
      this.classList.toggle("active");
      var content = this.nextElementSibling;
      if (content.style.display === "block") {
        content.style.display = "none";
        this.style.borderBottomStyle = "solid";
        this.style.borderRadius = "8px"
      } else {
        content.style.display = "block";
        this.style.borderBottomStyle = "none";
        this.style.borderRadius = "8px 8px 0px 0px"
      }
    });
  }
}