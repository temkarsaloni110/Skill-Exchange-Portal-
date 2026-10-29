document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".flash").forEach(function (message) {
    setTimeout(function () {
      message.style.transition = "opacity .4s";
      message.style.opacity = "0";
      setTimeout(function () { message.remove(); }, 450);
    }, 3500);
  });

  const messageBox = document.querySelector(".message-form textarea");
  if (messageBox) {
    messageBox.addEventListener("keydown", function (event) {
      // Enter sends; Shift+Enter adds a new line.
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        if (messageBox.value.trim()) messageBox.form.requestSubmit();
      }
    });
  }
});
