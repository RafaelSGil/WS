function horizontalScroll(event) {
  // Get the horizontal scroll position
  var container = document.querySelector(".container-card");
  var currentScrollLeft = container.scrollLeft;

  // Set the scroll amount
  container.scrollLeft += event.deltaY;

  // Prevent the default scroll behavior
  event.preventDefault();
}
