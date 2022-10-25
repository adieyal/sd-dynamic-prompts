onUiUpdate(function(){
  check_collapsibles();
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