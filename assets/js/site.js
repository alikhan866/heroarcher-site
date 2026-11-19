/* Hero Archer, heroarcher.com. Four small jobs, all optional: the page works
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

  // 3. The gameplay clip plays only while it is on screen, and not at all for
  //    people who ask for reduced motion (they get the controls instead).
  (function () {
    var clip = document.querySelector("video[data-clip]");
    if (!clip) return;
    if (reduce || !("IntersectionObserver" in window)) {
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

  // 4. The trailer. Any a[data-trailer] opens it in a dialog, playing with sound
  //    (without this script those links open the video file). Once the page has
  //    finished loading and the browser is idle, the video is fetched in the
  //    background, so a tap starts it at once. The page itself never waits for
  //    it, and visitors on Data Saver or a 2G/3G connection are not made to
  //    download it unasked.
  (function () {
    var dialog = document.getElementById("trailer");
    var openers = document.querySelectorAll("a[data-trailer]");
    if (!dialog || typeof dialog.showModal !== "function" || !openers.length) return;
    var video = dialog.querySelector("video");
    var url = openers[0].getAttribute("href");
    var poster = "assets/img/trailer-poster.webp";
    var ready = null;      // object URL of the fetched video
    var fetching = null;   // AbortController of the background fetch

    function slowOrSaving() {
      var c = navigator.connection;
      return !!(c && (c.saveData || /(^|slow-)2g|3g/.test(c.effectiveType || "")));
    }

    function preload() {
      if (ready || fetching || slowOrSaving() || !window.fetch || !window.AbortController) return;
      fetching = new AbortController();
      fetch(url, { signal: fetching.signal })
        .then(function (r) { return r.ok ? r.blob() : null; })
        .then(function (blob) {
          fetching = null;
          if (blob && !video.getAttribute("src")) ready = URL.createObjectURL(blob);
        })
        .catch(function () { fetching = null; });
    }

    function whenIdle() {
      if ("requestIdleCallback" in window) window.requestIdleCallback(preload, { timeout: 3000 });
      else setTimeout(preload, 1500);
    }
    if (document.readyState === "complete") whenIdle();
    else window.addEventListener("load", whenIdle);

    function open(event) {
      event.preventDefault();
      if (!video.getAttribute("src")) {
        // not fetched yet: stream it instead of downloading it twice
        if (fetching) { fetching.abort(); fetching = null; }
        video.poster = poster;
        video.src = ready || url;
      }
      if (video.ended) video.currentTime = 0;
      dialog.showModal();
      if (!reduce) {
        var playing = video.play();
        if (playing && playing.catch) playing.catch(function () {});
      }
    }
    openers.forEach(function (link) { link.addEventListener("click", open); });

    // a browser that cannot play the fetched copy streams the file instead
    video.addEventListener("error", function () {
      if (ready && video.src === ready) { video.src = url; video.play().catch(function () {}); }
    });
    dialog.addEventListener("close", function () { if (!dialog.open) video.pause(); });
    dialog.querySelector("[data-trailer-close]").addEventListener("click", function () { dialog.close(); });
    // a tap outside the video closes it
    dialog.addEventListener("click", function (event) { if (event.target === dialog) dialog.close(); });
  })();
})();
