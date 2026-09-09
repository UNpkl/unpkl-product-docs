(function () {
  function commandText(button) {
    var row = button.closest(".unpkl-docs-cmd");
    if (!row) {
      return "";
    }
    var field = row.querySelector(".unpkl-docs-cmd__text");
    if (!field) {
      return "";
    }
    return field.value !== undefined ? field.value : field.textContent || "";
  }

  function markCopied(button) {
    button.classList.add("is-copied");
    var label = button.querySelector(".unpkl-docs-cmd__copy-label");
    if (!label) {
      return;
    }
    var previous = label.textContent;
    label.textContent = "Copied";
    window.setTimeout(function () {
      button.classList.remove("is-copied");
      label.textContent = previous;
    }, 2000);
  }

  function fallbackCopy(text) {
    return new Promise(function (resolve, reject) {
      var textarea = document.createElement("textarea");
      textarea.value = text;
      textarea.setAttribute("readonly", "");
      textarea.style.cssText =
        "position:fixed;top:0;left:0;width:2em;height:2em;padding:0;" +
        "border:none;outline:none;background:transparent";
      document.body.appendChild(textarea);
      textarea.focus();
      textarea.select();
      try {
        if (document.execCommand("copy")) {
          resolve();
        } else {
          reject(new Error("execCommand failed"));
        }
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(textarea);
      }
    });
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopy(text);
      });
    }
    return fallbackCopy(text);
  }

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".unpkl-docs-cmd__copy");
    if (!button || button.getAttribute("onclick")) {
      return;
    }

    var text = commandText(button);
    if (!text) {
      return;
    }

    event.preventDefault();
    copyText(text)
      .then(function () {
        markCopied(button);
      })
      .catch(function () {
        /* clipboard unavailable */
      });
  });
})();
