/* SuccessHiway phone helpers for the self-hosted PDF.js viewer.
   Loaded by viewer.html. No changes to PDF.js itself.

   1. On phones/tablets (840px wide or less) the Contents (outline) panel
      covers the page. After the reader taps a section in Contents, close the
      panel so the section's text is showing.
   2. Label the sidebar button "Contents" on small screens (see viewer.css),
      so readers can find their way back to the list.
   3. If the phone restores this viewer from its back/forward cache, the PDF
      engine behind it has been shut down and the viewer looks frozen.
      Reload it so it works again. */
(function () {
  "use strict";

  var PHONE_WIDTH = 840;

  function isSmallScreen() {
    return window.innerWidth <= PHONE_WIDTH;
  }

  function whenAppReady(callback) {
    var tries = 0;
    (function wait() {
      var app = window.PDFViewerApplication;
      if (app && app.initializedPromise) {
        app.initializedPromise.then(function () { callback(app); });
      } else if (tries++ < 200) {
        setTimeout(wait, 50);
      }
    })();
  }

  whenAppReady(function (app) {
    var outline = document.getElementById("outlineView");
    if (!outline) return;
    outline.addEventListener("click", function (evt) {
      var link = evt.target.closest ? evt.target.closest("a") : null;
      if (!link || !isSmallScreen()) return;
      // Let PDF.js jump to the section first, then close the panel.
      setTimeout(function () {
        if (app.pdfSidebar && app.pdfSidebar.isOpen) app.pdfSidebar.close();
      }, 150);
    });
  });

  window.addEventListener("pageshow", function (evt) {
    if (evt.persisted) window.location.reload();
  });
})();
