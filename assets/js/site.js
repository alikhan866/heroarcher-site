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

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function play(video) {
    var playing = video.play();
    if (playing && playing.catch) playing.catch(function () {});
  }

  // 3. The trailer, in two places: silently in the "fights alone" section
  //    while it is on screen (the captions are burned in; "Tap for sound"
  //    starts it over with sound), and with sound in a dialog from "Watch the
  //    trailer". Without this script the section shows a still with a play
  //    button and the link opens the video file.
  //
  //    Once the page has finished loading and the browser is idle, the video
  //    is fetched in the background, so both start at once. The page never
  //    waits for it. Only visitors on Data Saver or real 2G are spared the
  //    download (not "3g": Chrome reports that from latency alone, for many fine
  //    connections); they get the play button instead of the silent preview.
  (function () {
    var dialog = document.getElementById("trailer");
    var inline = document.querySelector("video[data-trailer-inline]");
    var opener = document.querySelector("a[data-trailer]");
    var url = opener ? opener.getAttribute("href") : "assets/video/trailer.mp4";
    var ready = null;      // object URL of the fetched video
    var fetching = null;   // AbortController of the background fetch
    var waiting = [];      // players waiting for the background copy

    function slowOrSaving() {
      var c = navigator.connection;
      return !!(c && (c.saveData || /2g$/.test(c.effectiveType || "")));
    }

    function settle() {
      var w = waiting;
      waiting = [];
      w.forEach(function (cb) { cb(ready || url); });
    }

    function preload() {
      if (ready || fetching || slowOrSaving() || !window.fetch || !window.AbortController) return;
      fetching = new AbortController();
      fetch(url, { signal: fetching.signal })
        .then(function (r) { return r.ok ? r.blob() : null; })
        .then(function (blob) {
          fetching = null;
          if (blob) ready = URL.createObjectURL(blob);
          settle();
        })
        .catch(function () { fetching = null; settle(); });
    }

    // the silent preview can wait for the background copy...
    function whenSource(cb) {
      if (ready || !fetching) cb(ready || url);
      else waiting.push(cb);
    }
    // ...a tap cannot: stream it now, and stop the background copy rather than
    // download it twice
    function sourceNow() {
      if (!ready && fetching) { fetching.abort(); fetching = null; settle(); }
      return ready || url;
    }

    // a browser that cannot play the fetched copy streams the file instead
    function fallBack(video) {
      video.addEventListener("error", function () {
        if (ready && video.src === ready) { video.src = url; play(video); }
      });
    }

    function whenIdle() {
      if ("requestIdleCallback" in window) window.requestIdleCallback(preload, { timeout: 3000 });
      else setTimeout(preload, 1500);
    }
    if (document.readyState === "complete") whenIdle();
    else window.addEventListener("load", whenIdle);

    // in the section
    if (inline) {
      fallBack(inline);
      var soundButton = document.querySelector("[data-trailer-sound]");
      var preview = !reduce && !slowOrSaving() && "IntersectionObserver" in window;
      if (preview) {
        var withSound = false, visible = false;
        inline.controls = false;
        inline.muted = true;
        inline.loop = true;
        if (soundButton) soundButton.hidden = false;
        new IntersectionObserver(function (entries) {
          entries.forEach(function (entry) {
            visible = entry.isIntersecting;
            if (!visible) { inline.pause(); return; }
            if (withSound) return; // with sound it plays only when asked
            whenSource(function (src) {
              if (!visible || withSound) return;
              if (!inline.getAttribute("src")) inline.src = src;
              play(inline);
            });
          });
        }, { threshold: 0.35 }).observe(inline);
        var soundOn = function () {
          if (withSound) return;
          withSound = true;
          if (!inline.getAttribute("src")) inline.src = sourceNow();
          inline.muted = false;
          inline.loop = false;
          inline.controls = true;
          inline.currentTime = 0;
          play(inline);
          if (soundButton) soundButton.hidden = true;
        };
        if (soundButton) soundButton.addEventListener("click", soundOn);
        inline.addEventListener("click", soundOn);
      } else {
        // controls only; the fetched copy if there is one by the time they press play
        inline.addEventListener("play", function () {
          if (ready && !inline.getAttribute("src")) { inline.src = ready; play(inline); }
        });
      }
    }

    // in the dialog
    if (!dialog || typeof dialog.showModal !== "function" || !opener) return;
    var video = dialog.querySelector("video");
    fallBack(video);
    opener.addEventListener("click", function (event) {
      event.preventDefault();
      if (inline) inline.pause();
      if (!video.getAttribute("src")) {
        video.poster = "assets/img/trailer-poster.webp";
        video.src = sourceNow();
      }
      if (video.ended) video.currentTime = 0;
      dialog.showModal();
      if (!reduce) play(video);
    });
    dialog.addEventListener("close", function () { if (!dialog.open) video.pause(); });
    dialog.querySelector("[data-trailer-close]").addEventListener("click", function () { dialog.close(); });
    // a tap outside the video closes it
    dialog.addEventListener("click", function (event) { if (event.target === dialog) dialog.close(); });
  })();
})();
