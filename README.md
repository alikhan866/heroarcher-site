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
assets/img, fonts, video built from the game repo by tools/build_assets.py
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

The "how it plays" section shows a still (Arrow Rain in Frostpeak) for now.
The old store recording, `docs/release/store-assets/gameplay-1080x1920.mp4`,
has enemies in it that do not belong in that wave, so it is not used. When a
new recording exists, put a short muted loop in `assets/video/gameplay.mp4`
and swap the `<img>` in the `.clip` figure for:

```html
<video data-clip muted loop playsinline preload="none" width="540" height="590"
       poster="assets/img/gameplay-poster.webp" aria-label="...">
  <source src="assets/video/gameplay.mp4" type="video/mp4">
</video>
```

`site.js` already plays it only while it is on screen.

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
3. **A gameplay clip**, when there is one (see above), plays only while it is
   on screen, and shows controls instead of autoplaying for people who ask
   for reduced motion.

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
