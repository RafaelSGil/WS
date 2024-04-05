document.addEventListener("DOMContentLoaded", function () {
  const toggleTextElements = document.querySelectorAll(".toggle-text");
  toggleTextElements.forEach(function (element) {
    element.addEventListener("click", function () {
      this.classList.toggle("show-all-text");
    });
  });
});
