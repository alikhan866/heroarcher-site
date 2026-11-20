# heroarcher.com

The landing page for **Hero Archer Tower Idle Defense**. Its one job is to get
visitors onto the Google Play listing:
https://play.google.com/store/apps/details?id=com.omarkhan.heroarcher

Plain HTML and CSS served by GitHub Pages. There is no framework and no build
step: edit a file, push, and it is live within a minute or two.

```
index.html               the landing page
privacy/index.html       privacy policy   (heroarcher.com/privacy/)
delete-account/index.html  data deletion  (heroarcher.com/delete-account/)
404.html                 not-found page
assets/css/site.css      all styles, mobile first
assets/js/site.js        optional extras (see below); the page works without it
assets/img, fonts       built from the game repo by tools/build_assets.py
assets/video             the trailer, cut by trailer/make_trailer.py
trailer/                 the trailer: captions, recording driver, edit (PLAN.md)
CNAME                    tells GitHub Pages to serve heroarcher.com
app-ads.txt              AdMob publisher declaration
robots.txt, sitemap.xml, site.webmanifest, favicons, og-image.jpg
llms.txt                 fact sheet for AI assistants (see "Search and AI answers")
f065e4...c3c4.txt        IndexNow key, used by tools/indexnow.py
```

## Preview locally

```
python -m http.server 8000
```

then open http://localhost:8000.

## Editing the copy

All text is in the HTML files. The wording comes from the game itself: the
tutorial cards (`TutorialV2.cs`), the codex (`EnemyCodex.cs`), the chapter data
and the Nightmare and Weekly Trial rules. The section labels ("Your archer
fights alone", "Waves and bosses", "The chapters", "The loop") are the
tutorial's own card titles. Keep it that way: specific, in the game's voice,
and no em dashes.

## After changing site.css, site.js or og-image.jpg

```
python tools/stamp_assets.py
```

Every page links them as `site.css?v=<hash>` and `site.js?v=<hash>`. GitHub
Pages lets browsers keep them for 10 minutes, so without a new stamp a visitor
can get the new page with the old styles and script. The link-preview image
is stamped too: WhatsApp and the rest cache it by its address. Run it before
committing.

## Search and AI answers (discoverability)

What the site gives search engines and AI assistants, and what to keep in step:

- **Structured data** in `index.html`'s `<head>`: the studio, the site, the game
  (`VideoGame` + `MobileApplication`, with screenshots, trailer, price, platform)
  and the FAQ. The **FAQ section** on the page and the `FAQPage` answers in the
  structured data must match word for word; change one, change both. Check with
  https://search.google.com/test/rich-results and https://validator.schema.org.
- **`llms.txt`**: a plain fact sheet for AI crawlers (what the game is, price,
  platform, modes, links). Update it when a chapter, mode or platform is added,
  and when the iPhone version ships.
- **`sitemap.xml`** lists every page plus the trailer as a video; bump `lastmod`
  on a page when its text changes.
- **IndexNow**: after a push that changes what a page says, run
  `python tools/indexnow.py` and Bing, ChatGPT search, Copilot and DuckDuckGo
  re-read the pages within minutes. The key file is
  `f065e41e63c11c5649b1ed4b4fdce3c4.txt`; keep it.
- **Google** does not take IndexNow. Verify the domain once in Search Console
  (https://search.google.com/search-console, "Domain" property, a `TXT` record
  at GoDaddy), submit `https://heroarcher.com/sitemap.xml`, and use "URL
  inspection > Request indexing" on the home page after big changes. Do the same
  in Bing Webmaster Tools (it can import the Search Console site in one click).
- The name "Hero Archer" is close to other archer games, so every page and
  listing pairs it with "idle tower defense" and Freeze Gaming. Keep doing that
  in new copy, posts and video descriptions.

## Rebuilding the art

```
python tools/build_assets.py ../Evil-archer
```

This rebuilds every image, both fonts, the favicons and the link-preview image
from the game repo (Pillow and fontTools with brotli are needed). The tower picture puts the archer on the tower at
the same spot the game's home screen does (`MenuArcherDoll.cs`).

`assets/img/google-play-badge.png` is Google's official badge from
https://play.google.com/intl/en_us/badges/ and is not generated. When it is
used, the footer line "Google Play and the Google Play logo are trademarks of
Google LLC." has to stay.

The "Your archer fights alone" section shows the trailer,
`assets/video/trailer.mp4` (720x1280, 60 fps, 5 MB) with
`assets/img/trailer-poster.webp`, cut by `trailer/make_trailer.py --web` from
the trailer recording; `trailer/PLAN.md` says how that recording is made.

## What site.js does

1. **Creator and campaign links.** Every Play link already tells Google Play
   it came from `utm_source=heroarcher.com` plus which button was tapped
   (`header`, `hero`, `final`). If someone arrives on a tagged link, those tags
   are passed to Play instead, so give each creator their own:

   ```
   https://heroarcher.com/?utm_source=youtube&utm_campaign=channelname
   ```

   Installs then show up per campaign in Play Console under
   User acquisition > Acquisition reports.
2. **iPhone visitors** see a line saying the game is Android only for now.
   Remove the `.ios-note` paragraph in `index.html` once the App Store version
   is out, and add an App Store link next to the Play one.
3. **The trailer player** in "Your archer fights alone". It plays silently
   while it is on screen (the captions are burned in) and draws its own
   controls over the video: "Tap for sound" (the first tap starts it over from
   the top, then it is a speaker icon), a tap on the video to pause or play, a
   big play button when it is paused or done, full screen (letterboxed, never
   cropped), and a progress bar to tap along. After the page has loaded and
   the browser is idle, the file is fetched in the background so it starts at
   once; the page never waits for it. Visitors on Data Saver or real 2G skip
   the download and get the play button instead of the silent preview (Chrome
   reports "3g" from latency alone, so that is no reason to skip), as do
   people who ask for reduced motion. Without the script it is the browser's
   own player.

## Domain setup (GoDaddy)

heroarcher.com is registered at GoDaddy. In GoDaddy, open the domain's DNS
settings, remove any parked or forwarding `A` records for `@`, and add:

| Type  | Name | Value                 |
|-------|------|-----------------------|
| A     | @    | 185.199.108.153       |
| A     | @    | 185.199.109.153       |
| A     | @    | 185.199.110.153       |
| A     | @    | 185.199.111.153       |
| AAAA  | @    | 2606:50c0:8000::153   |
| AAAA  | @    | 2606:50c0:8001::153   |
| AAAA  | @    | 2606:50c0:8002::153   |
| AAAA  | @    | 2606:50c0:8003::153   |
| CNAME | www  | alikhan866.github.io  |

Turn off GoDaddy domain forwarding if it is on. Once DNS has spread (minutes
to a few hours), tick **Enforce HTTPS** in the repo's Settings > Pages.

Recommended: verify the domain under GitHub (account) Settings > Pages >
Add a domain. GitHub gives a `TXT` record to add at GoDaddy, which stops
anyone else's repo from claiming heroarcher.com.

## Legal pages

`privacy/` and `delete-account/` carry the same text as the pages Play Console
currently links to, `alikhan866.github.io/heroarcher/privacy.html` and
`.../delete-account.html`. Those originals are untouched. When the policy
changes, change both, or point Play Console at the heroarcher.com versions and
turn the old ones into redirects.

If Play Console's developer website becomes heroarcher.com, AdMob reads
`app-ads.txt` from here; this repo already has the same line as the old site.
