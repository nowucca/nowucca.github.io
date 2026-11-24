// nowucca.com news brief: per-story share controls.
// Without JS each story has a <details> menu of plain share links.
// With JS: touch devices that support the Web Share API get the native share sheet;
// everyone else gets the menu plus a "Copy link" button. Only one menu is open at a time.
(function () {
  var coarse = window.matchMedia && matchMedia("(pointer: coarse)").matches;
  var canShare = typeof navigator.share === "function";
  var shares = document.querySelectorAll("details.share");

  function data(d) {
    return { title: d.dataset.title, text: d.dataset.title, url: d.dataset.url };
  }

  function copy(d, btn) {
    var url = d.dataset.url;
    var done = function () {
      btn.textContent = "Link copied";
      setTimeout(function () { btn.textContent = "Copy link"; }, 1800);
    };
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(url).then(done, function () { fallback(url); done(); });
    } else { fallback(url); done(); }
  }

  function fallback(url) {
    var t = document.createElement("textarea");
    t.value = url; t.setAttribute("readonly", ""); t.style.position = "fixed"; t.style.opacity = "0";
    document.body.appendChild(t); t.select();
    try { document.execCommand("copy"); } catch (e) {}
    document.body.removeChild(t);
  }

  shares.forEach(function (d) {
    var btn = d.querySelector("button.copy");
    if (btn) {
      btn.hidden = false;
      btn.addEventListener("click", function () { copy(d, btn); });
    }
    if (canShare && coarse) {
      d.querySelector("summary").addEventListener("click", function (ev) {
        ev.preventDefault();
        navigator.share(data(d)).catch(function (err) {
          // Cancelled is fine; any other failure falls back to the menu.
          if (err && err.name !== "AbortError") d.open = true;
        });
      });
    }
    d.addEventListener("toggle", function () {
      if (!d.open) return;
      shares.forEach(function (o) { if (o !== d) o.open = false; });
    });
  });

  document.addEventListener("click", function (ev) {
    shares.forEach(function (d) { if (d.open && !d.contains(ev.target)) d.open = false; });
  });
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    shares.forEach(function (d) {
      if (d.open) { d.open = false; d.querySelector("summary").focus(); }
    });
  });
})();
