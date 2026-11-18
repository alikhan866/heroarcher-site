# Hero Archer trailer

Status: **waiting on the balance sweep** (`fullgame_19_11_2026`, running in the
open editor). Recording needs new dev scripts, and adding scripts recompiles the
editor and would kill the sweep. Everything below that does not need Unity is
ready.

## What gets made

| File | For | Shape |
|---|---|---|
| `trailer-1080x1920.mp4` | TikTok, YouTube Shorts, Reels, creators, the site | 9:16, ~35 s, game music + game sound, subtitles burned in |
| `gameplay-loop.mp4` | the site's "how it plays" figure | 1080x1180 crop, ~10 s, muted, no subtitles, loops cleanly |

Both come from one recording session. A 16:9 cut for a YouTube / Play listing
video can be made from the same footage later.

## Shot list

Captions are rendered by `captions.py` (gold Lilita One headline, cream
Baloo 2 line, the store screenshots' style). Every shot is staged with the
game's Scenarios tool (`Tools > Scenarios`, `TestScenario`), so it is
repeatable and nothing wanders in that should not be there.

| # | Time | On screen | Staging | Caption |
|---|---|---|---|---|
| 1 | 0:00 | A goblin wave closes on the tower from every side; Arrow Rain lands as they bunch up | Emberwood, wave ~20, natural waves, infinite energy, Arrow Rain at 1.5 s | THE FOREST IS CRAWLING |
| 2 | 0:03 | The archer firing on their own, goblins dropping, the coin counter climbing | same take, later | YOUR ARCHER FIGHTS ALONE / Every kill pays coins |
| 3 | 0:07 | Damage bought twice in the run panel; the damage numbers jump | director buys Damage x2 | SPEND THEM / Damage first is never wrong |
| 4 | 0:10 | Frost Snare locks a pack, Lightning Strike, then Poison Cloud | Frostpeak, a big pack, infinite energy | EIGHT ABILITIES / Pick your moment |
| 5 | 0:15 | Storm Rod arcing down a column of raiders; a Ballista bolt through a line | Necropolis with the Storm Rod perk; second take with Ballista Frame | ONE CONTRAPTION PER RUN / Storm Rod, Ballista, Barracks and more |
| 6 | 0:19 | Boss ogre walks in and winds up; Mega Gust shoves it and breaks the windup | Emberwood wave 5, one Boss spawn, Mega Gust during the windup | EVERY 5TH WAVE, A BOSS / Break the windup before the axe falls |
| 7 | 0:24 | The boss drops gear; cut to the gear screen with the archer wearing it | boss kill take + gear screen | DRESS YOUR ARCHER / Boss loot shows up on your archer |
| 8 | 0:27 | Three quick cuts: a Frostpeak blizzard, the Necropolis dead getting back up, Cinderdeep lava wolves | three short takes | FOUR LANDS, 50 WAVES EACH / Then the Nightmare lap |
| 9 | 0:31 | End card: logo, the archer on the tower, dusk valley | `09_end.png` | GOOD HUNTING, HERO / Free on Google Play |

Music: `Assets/Audio/Music/music_ch1_emberwood.wav` under everything, faded
out over the end card; the game's own sound effects from the recording,
mixed under it. Most people watch these muted, so the captions carry it.

## Recording, once the sweep is done

1. **Unity MCP for this folder.** The bridge (`http://127.0.0.1:8080/mcp`) is
   registered in `~/.claude.json` under the project's old path,
   `C:/Users/HP/Evil-archer`, so sessions opened in `Desktop/Evil-archer` do
   not get it. Register it again for the new path and start a new session.
2. **Recorder.** Add Unity Recorder (`com.unity.recorder`, editor only, never
   ships in a build) and record the Game view at 1080x1920, 60 fps, with audio.
3. **Director.** A dev-only script in `Assets/Dev` that, per shot, starts the
   shot's TestScenario and fires abilities, buys upgrades and spawns the boss
   on cue, so every take is the same and abilities land when the crowd is
   tight. One scenario asset per shot in `Assets/Dev/Scenarios/Trailer/`.
4. Record every shot with a second of handle on each side. Watch for enemies
   from another chapter turning up: the old store clip had them, and if the
   current build does it too, that is a game bug.
5. Back up the save family before play, restore it after (CLAUDE.md lists the
   files and PlayerPrefs keys).

## Editing

`make_trailer.py` (next) trims the takes, overlays the caption cards with short
fades, lays the music under the game audio, adds the end card and exports both
files with ffmpeg (the copy bundled with imageio-ffmpeg has libass,
freetype and xfade).

```
python trailer/captions.py ../Evil-archer   # caption cards + preview
python trailer/make_trailer.py               # after recording
```
