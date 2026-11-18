/* Hero Archer, heroarcher.com. Three small jobs, all optional: the page works
   without this file. */
(function () {
  "use strict";

  var PLAY = "https://play.google.com/store/apps/details?id=com.omarkhan.heroarcher";

  // 1. Campaign tags. Links already carry utm_source=heroarcher.com and their
  //    placement. If the visitor arrived on a tagged link (a creator's
  //    heroarcher.com/?utm_source=youtube&utm_campaign=name), hand those tags
  //    to Google Play instead, so Play Console credits the install to them.
  var incoming = new URLSearchParams(window.location.search);
  if (incoming.has("utm_source") || incoming.has("utm_campaign")) {
    document.querySelectorAll("a[data-play]").forEach(function (link) {
      var ref = new URLSearchParams();
      ref.set("utm_source", incoming.get("utm_source") || "heroarcher.com");
      ref.set("utm_medium", incoming.get("utm_medium") || "website");
      ["utm_campaign", "utm_term"].forEach(function (key) {
        if (incoming.get(key)) ref.set(key, incoming.get(key));
      });
      ref.set("utm_content", incoming.get("utm_content") || link.getAttribute("data-play"));
      link.href = PLAY + "&referrer=" + encodeURIComponent(ref.toString());
    });
  }

  // 2. iPhone and iPad visitors get a line saying the game is Android only
  //    for now. iPadOS reports itself as a Mac, so check for touch as well.
  var ua = navigator.userAgent;
  var isIOS = /iPad|iPhone|iPod/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1);
  if (isIOS) {
    document.querySelectorAll("[data-ios-only]").forEach(function (el) {
      el.hidden = false;
    });
  }

  // 3. The gameplay clip plays only while it is on screen, and not at all for
  //    people who ask for reduced motion (they get the controls instead).
  var clip = document.querySelector("video[data-clip]");
  if (!clip) return;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduce.matches || !("IntersectionObserver" in window)) {
    clip.controls = true;
    return;
  }
  clip.muted = true;
  new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        var playing = clip.play();
        if (playing && playing.catch) playing.catch(function () {});
      } else {
        clip.pause();
      }
    });
  }, { threshold: 0.25 }).observe(clip);
})();
