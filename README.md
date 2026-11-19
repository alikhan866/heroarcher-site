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
assets/video             the gameplay loop, cut by trailer/make_trailer.py
trailer/                 the trailer: captions, recording driver, edit (PLAN.md)
CNAME                    tells GitHub Pages to serve heroarcher.com
app-ads.txt              AdMob publisher declaration
robots.txt, sitemap.xml, site.webmanifest, favicons, og-image.jpg
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

The "how it plays" section is a muted 9-second loop,
`assets/video/gameplay.mp4` (1080x1180, 30 fps, about 1.6 MB) with
`assets/img/gameplay-poster.webp`. Both are cut from the trailer recording by
`trailer/make_trailer.py`; `trailer/PLAN.md` says how that recording is made.
`site.js` plays the loop only while it is on screen.

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
3. **The gameplay loop** (see above) plays only while it is on screen, and
   shows controls instead of autoplaying for people who ask for reduced motion.
4. **The trailer.** "Watch the trailer" (under the Play button, and under the
   loop) opens `assets/video/trailer.mp4` (720x1280, 5 MB, cut by
   `trailer/make_trailer.py --web`) in a dialog, with sound and a Play button
   under it (`utm_content=trailer`). After the page has loaded and the browser
   is idle, the file is fetched in the background so a tap starts it at once;
   the page never waits for it, and visitors on Data Saver or 2G/3G are not
   made to download it. Without the script the links open the file itself.

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
