# Hero Archer trailer

Status: **made** (2026-11-19), re-recorded 2026-11-20 in the Frostpeak Slate UI, **re-recorded
and re-cut 2026-11-22** from game main e8fa6063 (the readable item card, the merge animation,
painted spells, death clips and marks, the battle pass, tower skins). Omar: "a little longer,
especially the equipment part ... the user needs some time to actually process what's going on".
The finished files:

| File | For | Shape |
|---|---|---|
| `trailer/build/out/trailer-1080x1920.mp4` (also in the game repo, `docs/release/store-assets/`) | TikTok, YouTube Shorts, Reels, creators | 9:16, 54.8 s, 60 fps, Emberwood music (its boss theme under the boss) + the game's sound, captions burned in, -14 LUFS |
| `assets/video/trailer.mp4` + `assets/img/trailer-poster.webp` | the site's player, in the "fights alone" section | 720x1280, 60 fps, 7.8 MB |

## The cut (2026-11-22)

| Time | Footage | Caption |
|---|---|---|
| 0:00 | Emberwood: goblin groups close in on the tower from every side | THE FOREST IS CRAWLING |
| 0:02.5 | No taps: the archer picks off a steady stream, coins tick up per kill | YOUR ARCHER FIGHTS ALONE |
| 0:05.8 | Damage bought twice | SPEND THEM |
| 0:08.3 | Arrow Rain; Frostpeak: Frost Snare, Lightning, Poison Cloud (proposal 59's painted spells and sounds) | EIGHT ABILITIES |
| 0:13.0 | Storm Rod down a column of the dead; the Ballista spear through a line | ONE CONTRAPTION PER RUN |
| 0:16.4 | Boss Ogre: SLAM, Mega Gust, BROKEN, Lightning (the boss theme comes in) | EVERY 5TH WAVE, A BOSS |
| 0:19.3 | Its Great Helm dropped, picked up and worn (push in) | BOSSES DROP LOOT |
| 0:22.1 | The gear screen: a swipe to the bag, the set cloak's card held 2.7 s, EQUIP, a swipe back to the doll in it | DRESS YOUR ARCHER |
| 0:28.5 | A Long Bow with two copies: its card, MERGE 3, the MERGE THREE sheet, the full 4.8 s merge | MERGE THREE INTO ONE |
| 0:37.1 | The home screen, the pass's chip, the sheet mid-season, three rewards claimed | A NEW PASS EVERY MONTH |
| 0:42.5 | Frostforged on the tower in Emberwood (push in) | A TOWER SKIN EVERY MONTH |
| 0:45.5 | Frostpeak's blizzard, a Mummy Brute rising, Cinderdeep's hounds, the Nightmare lap | FOUR LANDS, 50 WAVES EACH |
| 0:51.3 | End card | GOOD HUNTING, HERO |

New in the takes: `gearcard` (drives GearMergeFx.Seek frame by frame, so the merge plays at its
real 4.8 s although batchmode frames run slower than the wall clock; "swipe" events draw a thumb
in the edit), `pass` (level 13, not 30: a ready skin card draws CLAIM over the skin's name, a
game bug to fix before a pass take at level 30) and `skin`. The pass state lives in PRELUDE.

## The first cut (2026-11-19)

Everything is real gameplay from the current build, staged with the game's own
Scenarios tool so each shot is repeatable and only the enemies a shot asks for
appear. A finger ring marks every tap; nothing on screen happens without one
except the archer, the contraptions and the enemies.

## The cut

| Time | Footage | Caption |
|---|---|---|
| 0:00 | Emberwood: goblin groups close in on the tower from every side | THE FOREST IS CRAWLING |
| 0:02.5 | No taps: the archer picks off a steady stream, coins tick up per kill | YOUR ARCHER FIGHTS ALONE / Every kill pays coins |
| 0:06 | Damage bought twice in the run panel, 8.7 to 9.9 | SPEND THEM / Damage first is never wrong |
| 0:08 | Arrow Rain on the bunched crowd; Frostpeak: Frost Snare, Lightning on a yeti, Poison Cloud | EIGHT ABILITIES / Pick your moment |
| 0:12 | Storm Rod arcing down a column of the dead; Ballista spear through a line of goblins | ONE CONTRAPTION PER RUN / Storm Rod, Ballista, Barracks and more |
| 0:15 | Boss Ogre: SLAM windup, Mega Gust, BROKEN, Lightning kills it | EVERY 5TH WAVE, A BOSS / Break the windup before the axe falls |
| 0:18 | Its drop, a Great Helm, picked up and worn on the deck (push in); the gear screen, a set cloak equipped | DRESS YOUR ARCHER / Boss loot shows up on your archer |
| 0:23 | Frostpeak blizzard, a Mummy Brute rising again, Cinderdeep magma hounds, the Nightmare lap | FOUR LANDS, 50 WAVES EACH / Then the Nightmare lap |
| 0:28 | End card: logo, the archer on the tower, dusk valley | GOOD HUNTING, HERO / Free on Google Play |

## How it was recorded

**2026-11-20 re-record: batchmode, no editor.** `python trailer/unity/batch.py
<game-worktree> <take> ...` generates the same takes and driver into a PlayMode test
in a game worktree (its own productName; never commit the generated file) and runs
`Unity -batchmode -runTests`. The world camera draws into a portrait RT with the HUD
canvases moved onto it; see batch.py's header for why. All eleven takes in one run
took 4.5 minutes. Frame pacing came out at an 18-22 ms median (other Unity jobs
were running), so effects on unscaled time (damage numbers, button squash) play a
little quicker than in the editor takes. The boss cut is retimed from the take's
logged events (meta.txt, events.txt). The editor path below still works.

**2026-11-19: the open editor.**

Nothing was added to the game project. The open editor is driven through the
MCP-for-Unity bridge (`http://127.0.0.1:8080/mcp`, its `execute_code` tool,
which compiles C# 6 in memory), so there is no recompile and nothing to commit
in the game repo.

```
trailer/unity/takes.py        every take: staging (a TestScenario), per-frame keepers, cues
trailer/unity/driver.cs.tmpl  the per-take coroutine: capture, taps, sound events
trailer/unity/record.py       python trailer/unity/record.py ember frost ...
```

- **Picture.** `Time.captureDeltaTime` fixes the game clock at 1/60 s a frame
  and the editor is paced at 60 fps, so what the game animates on unscaled time
  (damage numbers, button squash, camera shake) keeps its real speed. Frames go
  screen -> RenderTexture -> AsyncGPUReadback -> JPEG on a worker thread.
  The Game view is switched to 1080x1920 for the session and back to the
  Simulator after.
- **Sound.** `AudioRenderer` returns no samples in this editor, so each take
  logs its sound events (bow shots, death cries by voice family, zaps, ballista,
  gear drop, pickup and equip, plus every tap) and `make_trailer.py` rebuilds
  the track from the game's own clips at the game's volumes and +/-8% pitch.
  The announcer says each ability's name, as in the game.
- **A veteran player.** `GameManager.Awake` reloads the save from disk on every
  scene load, so the takes write one save (tutorial done, everything unlocked,
  codex seen) and keep saving off otherwise. The save family is deleted after
  the session, as CLAUDE.md asks. HUD callout cards are held back during takes.
- Requirements: the editor in play mode, the Game view visible, and the bridge
  running (Window > MCP for Unity).

## Editing

```
python trailer/captions.py ../Evil-archer          # caption cards + end card
python trailer/make_trailer.py ../Evil-archer      # trailer + the site's copy (about 3 min)
python trailer/make_trailer.py ../Evil-archer --web    # the site's copy only
```

`make_trailer.py` holds the cut list (take, in, out, caption) at the top. It
draws the tap rings, the push in on the helm, the caption fades, the end card
dissolve, mixes the rebuilt sound under `music_ch1_emberwood.wav` (at the
game's 0.55) and normalises to -14 LUFS. Output is limited-range BT.709
yuv420p H.264, which every platform and browser plays as intended.

A 16:9 cut for a YouTube or Play listing video can come from the same takes:
the field is the top 1260 px of every frame.
