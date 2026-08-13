(function () {
  var input = document.getElementById("receipt");
  var preview = document.getElementById("preview");
  if (!input || !preview) return;
  input.addEventListener("change", function () {
    var file = input.files && input.files[0];
    if (!file) {
      preview.classList.add("hidden");
      return;
    }
    var url = URL.createObjectURL(file);
    preview.src = url;
    preview.classList.remove("hidden");
  });
})();
