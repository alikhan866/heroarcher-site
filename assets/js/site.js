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

  // 3. The trailer player in "Your archer fights alone". It plays silently
  //    while it is on screen (the captions are burned in) and draws its own
  //    controls over the video: sound (the first tap starts it over from the
  //    top), play and pause (a tap on the video, or the big button when it is
  //    paused or done), full screen, and the progress bar (tap to jump).
  //    Without this script it is the browser's own player.
  //
  //    Once the page has finished loading and the browser is idle, the video is
  //    fetched in the background, so it starts at once. The page never waits
  //    for it. Only visitors on Data Saver or real 2G are spared the download
  //    (not "3g": Chrome reports that from latency alone, for many fine
  //    connections); they, and people who ask for reduced motion, get the play
  //    button instead of the silent preview.
  (function () {
    var frame = document.querySelector("[data-player]");
    if (!frame) return;
    var video = frame.querySelector("video");
    var source = video.querySelector("source");
    var url = source ? source.getAttribute("src") : "assets/video/trailer.mp4";
    var soundButton = frame.querySelector("[data-sound]");
    var playButton = frame.querySelector("[data-toggle]");
    var fullButton = frame.querySelector("[data-full]");
    var bar = frame.querySelector("[data-bar]");
    var fill = bar.querySelector("span");

    var ready = null;      // object URL of the fetched video
    var fetching = null;   // AbortController of the background fetch
    var waiting = [];      // callers waiting for the background copy

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

    function whenIdle() {
      if ("requestIdleCallback" in window) window.requestIdleCallback(preload, { timeout: 3000 });
      else setTimeout(preload, 1500);
    }
    if (document.readyState === "complete") whenIdle();
    else window.addEventListener("load", whenIdle);

    // the silent preview can wait for the background copy; a tap cannot, so it
    // streams the file and the background copy stops rather than load twice
    function load(now, then) {
      if (video.getAttribute("src")) { then(); return; }
      if (now && !ready && fetching) { fetching.abort(); fetching = null; settle(); }
      if (ready || !fetching) { video.src = ready || url; then(); return; }
      waiting.push(function (src) { if (!video.getAttribute("src")) video.src = src; then(); });
    }

    // a browser that cannot play the fetched copy streams the file instead
    video.addEventListener("error", function () {
      if (ready && video.src === ready) { video.src = url; play(video); }
    });

    // our controls replace the browser's
    video.controls = false;
    video.muted = true;
    video.loop = true;
    soundButton.hidden = false;
    bar.hidden = false;
    var canFull = !!(frame.requestFullscreen || frame.webkitRequestFullscreen || video.webkitEnterFullscreen);
    fullButton.hidden = !canFull;

    var heard = false;       // the sound has been turned on once
    var userPaused = false;  // paused by a tap, not by scrolling away
    var visible = false;

    function showPlay() { playButton.hidden = !video.paused; }
    // a refused play (Low Power Mode refuses even a silent one) leaves the button up
    function tryPlay() {
      var playing = video.play();
      if (playing && playing.catch) playing.catch(showPlay);
    }
    video.addEventListener("play", showPlay);
    video.addEventListener("pause", showPlay);
    video.addEventListener("ended", showPlay);

    function tick() {
      if (video.duration) fill.style.transform = "scaleX(" + Math.min(1, video.currentTime / video.duration) + ")";
      if (!video.paused) window.requestAnimationFrame(tick);
    }
    video.addEventListener("play", function () { window.requestAnimationFrame(tick); });
    video.addEventListener("seeked", tick);

    function start() {
      userPaused = false;
      load(true, function () {
        if (video.ended) video.currentTime = 0;
        tryPlay();
      });
    }
    function toggle() {
      if (video.paused) start();
      else { userPaused = true; video.pause(); }
    }
    video.addEventListener("click", toggle);
    playButton.addEventListener("click", start);

    soundButton.addEventListener("click", function () {
      var turnOn = video.muted;
      video.muted = !turnOn;
      video.loop = !turnOn; // with sound it plays through once and stops on the end card
      if (turnOn && !heard) {
        heard = true;
        soundButton.classList.add("is-round");
        load(true, function () { video.currentTime = 0; });
      }
      soundButton.setAttribute("aria-pressed", turnOn ? "true" : "false");
      soundButton.setAttribute("aria-label", turnOn ? "Turn the sound off" : "Turn the sound on");
      if (turnOn && video.paused) start();
    });

    bar.addEventListener("click", function (event) {
      if (!video.duration) return;
      var r = bar.getBoundingClientRect();
      video.currentTime = Math.max(0, Math.min(1, (event.clientX - r.left) / r.width)) * video.duration;
      tick();
      if (video.paused) start();
    });

    fullButton.addEventListener("click", function () {
      var d = document;
      if (d.fullscreenElement || d.webkitFullscreenElement) {
        (d.exitFullscreen || d.webkitExitFullscreen).call(d);
      } else if (frame.requestFullscreen) {
        var going = frame.requestFullscreen();
        if (going && going.catch) going.catch(function () {});
      } else if (frame.webkitRequestFullscreen) {
        frame.webkitRequestFullscreen();
      } else if (video.webkitEnterFullscreen) {
        video.webkitEnterFullscreen(); // iPhone: the system player
      }
    });

    var preview = !reduce && !slowOrSaving() && "IntersectionObserver" in window;
    if (!preview) { showPlay(); return; }
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        visible = entry.isIntersecting;
        if (!visible) { if (!video.paused) video.pause(); return; }
        if (userPaused || (heard && video.ended)) return;
        load(false, function () { if (visible && !userPaused) tryPlay(); });
      });
    }, { threshold: 0.35 }).observe(video);
  })();
})();
