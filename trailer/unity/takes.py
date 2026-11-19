"""The trailer's takes: how each one is staged and what happens on which frame.

C# here is CodeDom C# 6 (no local functions, `out var` or tuples). In cues
`gm` is GameManager.I, `frame` is the frame about to be shown (the cue runs at
the end of the one before), `tap("Ability_Frost")` presses a HUD button and
`mark("what")` logs a sound event. A cue may shorten the take by setting
`lengthFrames`.
"""

# Every snippet starts with this: a veteran player (tutorial done, every chapter
# and ability open, codex seen), so no first-time card pops over a shot. Saving
# stays off apart from the one write below.
PRELUDE = r"""
DevFlags.NoSave = true;
var vd = MetaState.Data;
vd.tutorialDone = true; vd.tutorialPurseGiven = true; vd.tutorialStep = 99;
vd.chapterUnlocked = 4;
vd.chapterBestWave[0] = 50; vd.chapterBestWave[1] = 50; vd.chapterBestWave[2] = 50; vd.chapterBestWave[3] = 34;
vd.gearFirstDropGiven = true; vd.gearHintShown = true; vd.gearLostHintShown = true;
vd.totalRuns = 60; vd.bestWave = 50; vd.playSeconds = 0; vd.rateAsks = 3; vd.gems = 1840;
for (int si = 0; si < vd.seenEnemies.Length; si++) vd.seenEnemies[si] = true;
for (int si = 0; si < vd.seenElites.Length; si++) vd.seenElites[si] = true;
for (int si = 0; si < vd.seenPerks.Length; si++) vd.seenPerks[si] = true;
Unlocks.DevAll = true;
// a tutorial that began before this ran (a fresh play session boots without a save) is closed
foreach (var tut in UnityEngine.Object.FindObjectsByType<TutorialV2>(FindObjectsInactive.Include, FindObjectsSortMode.None))
    typeof(TutorialV2).GetMethod("FinishTutorial", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic).Invoke(tut, new object[] { true });
// GameManager.Awake reloads the save from disk on every scene load, so the veteran
// has to be ON disk: one deliberate write (the session's only one; the save family
// is deleted afterwards - there was none before)
DevFlags.NoSave = false; MetaState.Save(); DevFlags.NoSave = true;
System.Action<int[], int[]> dress = (bases, rar) =>
{
    vd.gear.Clear();
    for (int s = 0; s < vd.gearEquipped.Length; s++) vd.gearEquipped[s] = 0;
    for (int k = 0; k < bases.Length; k++)
    {
        var it = GearLoot.Make((GearCatalog.Rarity)rar[k], 0, 0, GearCatalog.SlotOf(bases[k]));
        it.baseId = bases[k]; it.stars = 2;
        Gear.AddToBag(it);
        Gear.Equip(it.id);
    }
    Gear.OnLoaded();
};
"""

# back to the menu: a surrender ends the run and reloads the scene
TO_MENU = r"""
// the runner re-plays its scenario after every scene load: forget it first
typeof(ScenarioRunner).GetProperty("Current").SetValue(null, null, null);
var gm0 = GameManager.I;
if (gm0 != null && gm0.State != GameState.Menu) { gm0.Surrender(); return "surrendered"; }
return "in menu";
"""

# the archer's look in the battle shots: war bow, oak quiver, hide cloak, leather hood
RANGER = "dress(new int[] { 2, 4, 10, 6 }, new int[] { 1, 1, 1, 1 });"


def spawn(kind, count=1, delay=0.0, angle=225, distance=1.3, every=0.0, hp=1.0, frozen=False):
    return dict(kind=kind, count=count, delay=delay, angle=angle, distance=distance, every=every, hp=hp, frozen=frozen)


def battle(chapter, wave, spawns=(), natural=True, dmg=9, rate=8, rng=3, hp=6, perks=(), extra="", look=RANGER):
    """C# that dresses the archer and starts a TestScenario run (ScenarioRunner)."""
    lines = [look,
             "var sc = ScriptableObject.CreateInstance<TestScenario>();",
             'sc.name = "trailer";',
             "sc.chapter = %d; sc.wave = %d; sc.naturalWaves = %s;" % (chapter, wave, "true" if natural else "false"),
             "sc.infiniteTowerHp = true; sc.infiniteEnemyHp = false; sc.infiniteEnergy = true; sc.levelUps = false;",
             "sc.build = TestScenario.TowerBuild.MySave;",
             "sc.damageLevel = %d; sc.fireRateLevel = %d; sc.rangeLevel = %d; sc.healthLevel = %d;" % (dmg, rate, rng, hp),
             "sc.perks = new System.Collections.Generic.List<PerkId>();"]
    for p in perks:
        lines.append("sc.perks.Add(PerkId.%s);" % p)
    lines.append("sc.spawns = new System.Collections.Generic.List<TestScenario.Spawn>();")
    for sp in spawns:
        lines.append(
            "sc.spawns.Add(new TestScenario.Spawn { kind = TestScenario.Kind.%s, count = %d, delay = %sf, angle = %sf, distance = %sf, repeatEvery = %sf, hpMult = %sf, frozen = %s });"
            % (sp["kind"], sp["count"], sp["delay"], sp["angle"], sp["distance"], sp["every"], sp["hp"], "true" if sp["frozen"] else "false"))
    lines.append(extra)
    lines.append("ScenarioRunner.Run(sc);")
    lines.append('return "run staged: ch %d wave %d";' % (chapter, wave))
    return "\n".join(lines)


def ready_for(chapter, wave):
    return ("return gm != null && gm.Playing && gm.SelectedChapter == %d && gm.waves != null && gm.waves.Wave >= %d"
            " && Time.timeSinceLevelLoad > 0.5f;" % (chapter, wave))


# energy topped up; the tower kept above 70% (the scenario's undying
# tower still shows every hit, and a near-empty HP bar reads as losing)
ENERGY = r"""
if (gm != null && gm.Playing) {
    gm.RefillEnergy();
    var tw = gm.tower;
    if (tw != null && tw.Hp < tw.MaxHp * 0.7f)
        typeof(Tower).GetProperty("Hp").SetValue(tw, tw.MaxHp * 0.7f, null);
}"""


def coins_at_start(n):
    return "if (frame == -1 && gm != null) gm.AddCoins(%d - gm.Coins);" % n


TAKES = {
    "test": dict(settle=10, length=90, cues=r"""if (frame == 30) tap("Ability_ArrowRain");"""),

    # 1-3: Emberwood. A goblin crowd closes in from every side, Arrow Rain lands on
    # it, the archer works through the rest while the coins climb, then Damage is
    # bought twice.
    "ember": dict(
        pre=TO_MENU,
        setup=battle(0, 17, spawns=[
            # loose groups walking in from the edges, not a ring
            spawn("Grunt", 4, 0.0, 200, 1.85), spawn("Grunt", 3, 0.2, 252, 1.7), spawn("Grunt", 4, 0.1, 318, 1.9),
            spawn("Grunt", 3, 0.4, 22, 1.75), spawn("Grunt", 4, 0.3, 78, 1.95), spawn("Grunt", 3, 0.5, 133, 1.8),
            spawn("Runner", 2, 1.4, 160, 1.9), spawn("Tank", 1, 0.6, 283, 1.8),
            # then a trickle, so the field never empties
            spawn("Grunt", 2, 4.0, 232, 1.85, every=3.6), spawn("Grunt", 2, 5.0, 41, 1.9, every=4.1),
            spawn("Grunt", 2, 6.4, 300, 1.8, every=3.9), spawn("Runner", 1, 6.2, 118, 1.9, every=4.7),
            spawn("Tank", 1, 8.0, 178, 1.8),
        ], dmg=12, rate=10, natural=False),
        ready=ready_for(0, 17), settle=60, length=780, keep=ENERGY,
        cues=coins_at_start(700) + r"""
if (frame == 150) tap("Ability_ArrowRain");
if (frame == 540) tap("Upgrade_Damage");
if (frame == 586) tap("Upgrade_Damage");
""",
    ),

    # 4: Frostpeak. A big pack; Frost Snare locks it, Lightning, Poison Cloud.
    "frost": dict(
        pre=TO_MENU,
        setup=battle(1, 6, dmg=14, rate=10, spawns=[
            spawn("Grunt", 6, 0.1, 205, 1.35), spawn("Grunt", 6, 0.1, 330, 1.35),
            spawn("Grunt", 5, 0.6, 95, 1.4), spawn("Runner", 4, 0.4, 260, 1.5), spawn("Tank", 1, 0.2, 30, 1.35),
        ]),
        ready=ready_for(1, 6), settle=40, length=420, keep=ENERGY,
        cues=coins_at_start(412) + r"""
if (frame == 80) tap("Ability_Frost");
if (frame == 165) tap("Ability_Lightning");
if (frame == 250) tap("Ability_Poison");
""",
    ),

    # 5a: the Storm Rod arcing through columns of the dead
    "storm": dict(
        pre=TO_MENU,
        setup=battle(2, 12, natural=False, dmg=8, perks=["Storm", "Storm", "Storm"], spawns=[
            spawn("Grunt", 1, 0.1 + 0.45 * i, 235, 1.35) for i in range(7)
        ] + [
            spawn("Grunt", 1, 0.3 + 0.45 * i, 305, 1.35) for i in range(7)
        ] + [spawn("Runner", 2, 1.0, 140, 1.4)],
            extra="sc.spawns.Add(new TestScenario.Spawn { kind = TestScenario.Kind.Grunt, count = 3, delay = 2f, angle = 60f, distance = 1.4f, repeatEvery = 2.5f });"),
        ready=ready_for(2, 12), settle=60, length=360, keep=ENERGY + r"""
if (gm != null && gm.Playing) { gm.zapInterval.level = 5; gm.chainCount.level = 2; }""",
        cues=coins_at_start(640),
    ),

    # 5b: the Ballista Frame's spear through a line
    "ballista": dict(
        pre=TO_MENU,
        setup=battle(0, 15, natural=False, dmg=9, perks=["Ballista", "Ballista", "Ballista"], spawns=[
            spawn("Grunt", 1, 0.1 + 0.3 * i, 210, 1.35) for i in range(6)
        ] + [spawn("Tank", 1, 0.2, 210, 1.55), spawn("Tank", 1, 1.5, 320, 1.4), spawn("Grunt", 4, 0.8, 90, 1.4)]),
        ready=ready_for(0, 15), settle=50, length=300, keep=ENERGY + r"""
if (gm != null && gm.Playing) gm.reload.level = 5;""",
        cues=coins_at_start(520),
    ),

    # 6-7: the boss. An ogre walks in and winds up on the tower; Mega Gust shoves it
    # and breaks the windup; Lightning; the archer finishes it. It drops a Great
    # Helm, the finger picks it up and the archer is wearing it on the deck.
    "boss": dict(
        pre=TO_MENU,
        setup=battle(0, 10, natural=False, dmg=12, rate=10, spawns=[
            spawn("Boss", 1, 0.2, 300, 0.65), spawn("Grunt", 3, 0.5, 205, 1.75), spawn("Grunt", 2, 2.5, 70, 1.8),
            spawn("Grunt", 2, 4.5, 245, 1.8),
        ]),
        ready=ready_for(0, 10), settle=50, length=1100, keep=ENERGY,
        cues=coins_at_start(355) + r"""
var bf2 = System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic;
Enemy boss = null;
foreach (var e in Enemy.Active) if (e != null && e.isBoss && e.Alive && e.gameObject.activeInHierarchy) boss = e;
if (frame == -1 && boss != null)
{
    // a boss the archer can finish inside the shot
    typeof(Enemy).GetField("maxHp", bf2).SetValue(boss, 180f);
    typeof(Enemy).GetField("hp", bf2).SetValue(boss, 180f);
}
if (st[1] == 0 && boss != null && boss.WindingUp) { st[0] = frame; st[1] = 1; notes.AppendLine("windup at " + frame); }
if (st[1] == 1 && frame == st[0] + 24) { tap("Ability_MegaGust"); st[1] = 2; }
if (st[1] == 2 && frame == st[0] + 100) { tap("Ability_Lightning"); st[1] = 3; notes.AppendLine("boss hp after gust " + (boss != null ? boss.CurrentHp.ToString("F0") : "dead")); }
if (st[1] == 3 && boss == null && st[2] == 0) { st[2] = frame; notes.AppendLine("boss dead at " + frame); }
// the boss's drop, swapped for the piece the trailer wants (spawned again on the spot)
if (st[2] > 0 && st[3] == 0 && GearDrop.Active.Count > 0)
{
    var d0 = GearDrop.Active[0];
    var ground = (Vector3)typeof(GearDrop).GetField("ground", bf2).GetValue(d0);
    GearDrop.Active.Remove(d0);
    UnityEngine.Object.Destroy(d0.gameObject);
    var helm = GearLoot.Make(GearCatalog.Rarity.Magic, 0, 0, (int)GearCatalog.Slot.Hood);
    helm.baseId = 8; helm.stars = 1;
    keepObj[0] = helm;
    var dn = GearDrop.Spawn(helm, ground, GearLoot.Source.Boss);
    keepObj[1] = dn;
    st[3] = frame;
}
var drop = keepObj[1] as GearDrop;
if (st[3] > 0 && st[4] == 0 && drop != null && drop.Landed && frame >= st[3] + 55)
{
    tapWorld(drop.transform.position, "pickup");
    drop.TryPickUp();
    st[4] = frame;
}
if (st[4] > 0 && st[5] == 0 && frame == st[4] + 34)
{
    var helm = keepObj[0] as GearItem;
    Gear.Equip(helm.id);
    GearAudio.PlayEquip();
    mark("equip");
    st[5] = frame;
    lengthFrames = frame + 120;
}
""",
    ),

    # 7b: the gear screen. The doll in the new helm; the Mail Cloak is tapped in the
    # bag and equipped, and the fur cloak becomes chain mail.
    "gear": dict(
        pre=TO_MENU,
        setup=r"""
dress(new int[] { 2, 5, 8, 10, 14, 16, 20, 23 }, new int[] { 1, 1, 1, 1, 0, 0, 1, 1 });
int[] bagBases = new int[] { 1, 6, 4, 9, 17, 19, 22, 7, 13 };
int[] bagRar = new int[] { 0, 1, 0, 1, 0, 1, 1, 0, 1 };
for (int k = 0; k < bagBases.Length; k++) { var it = GearLoot.Make((GearCatalog.Rarity)bagRar[k], 0, 0, GearCatalog.SlotOf(bagBases[k])); it.baseId = bagBases[k]; it.stars = k % 3; Gear.AddToBag(it); }
Gear.AddToBag(GearLoot.Make(GearCatalog.Rarity.Set, 0, 0, (int)GearCatalog.Slot.Cloak));
Gear.AddToBag(GearLoot.MakeUnique(0, 0));
var mail = GearLoot.Make(GearCatalog.Rarity.Magic, 0, 0, (int)GearCatalog.Slot.Cloak); mail.baseId = 11; mail.stars = 2; Gear.AddToBag(mail);
Gear.OnLoaded();
foreach (var t in Resources.FindObjectsOfTypeAll<Transform>()) if (t.name == "WelcomeModal" && t.gameObject.scene.IsValid()) t.gameObject.SetActive(false);
var pager = UnityEngine.Object.FindFirstObjectByType<MenuPager>();
int gi = -1; for (int i = 0; i < pager.pages.Length; i++) if (pager.pages[i] != null && pager.pages[i].name == "Page_Gear") gi = i;
pager.GoTo(gi);
if (GearScreenV2.I != null) GearScreenV2.I.Refresh();
return "gear page " + gi + ", mail cloak id " + mail.id;
""",
        ready='return GearScreenV2.I != null && Time.timeSinceLevelLoad > 2.5f;',
        settle=40, length=250,
        keep=r"""
// the first inventory row clear of the nav bar
foreach (var sr in UnityEngine.Object.FindObjectsByType<UnityEngine.UI.ScrollRect>(FindObjectsSortMode.None))
    if (sr.gameObject.name == "Scroll_Gear" && st[9] == 0) { sr.velocity = Vector2.zero; sr.content.anchoredPosition = new Vector2(sr.content.anchoredPosition.x, 190f); }
""",
        cues=r"""
if (frame == 50)
{
    foreach (var it in Gear.All) if (it.baseId == 11 && !Gear.IsEquipped(it.id)) { tap("Item" + it.id); break; }
}
if (frame == 120) { tapLabel("EQUIP"); mark("equip"); }
""",
    ),

    # 8: four lands, quick cuts
    "blizzard": dict(   # Frostpeak's 10th wave: the blizzard
        pre=TO_MENU,
        setup=battle(1, 10, dmg=14, rate=10, spawns=[
            spawn("Grunt", 5, 0.2, 210, 1.5), spawn("Grunt", 4, 0.4, 330, 1.6), spawn("Runner", 3, 0.6, 90, 1.7),
        ]),
        ready=ready_for(1, 10), settle=50, length=260, keep=ENERGY, cues=coins_at_start(388),
    ),
    "rise": dict(       # the Sunless Reach: Mummy Brutes fall and get back up
        pre=TO_MENU,
        setup=battle(2, 15, natural=False, dmg=14, rate=10, spawns=[
            spawn("Tank", 2, 0.1, 240, 0.8, hp=0.06), spawn("Tank", 1, 0.3, 300, 0.85, hp=0.05),
            spawn("Grunt", 4, 0.2, 150, 1.4), spawn("Grunt", 3, 0.5, 20, 1.5),
        ]),
        ready=ready_for(2, 15), settle=30, length=330, keep=ENERGY,
        cues=coins_at_start(902) + r"""
if (frame == 40) tap("Ability_Lightning");
foreach (var e in Enemy.Active) if (e != null && e.Rising && st[0] == 0) { st[0] = frame; notes.AppendLine("first rise at " + frame); }
""",
    ),
    "cinder": dict(     # Cinderdeep: magma hounds leave burning ground
        pre=TO_MENU,
        setup=battle(3, 15, natural=False, dmg=16, rate=10, spawns=[
            spawn("Runner", 4, 0.1, 205, 1.6), spawn("Runner", 4, 0.5, 325, 1.7), spawn("Runner", 3, 0.9, 95, 1.7),
            spawn("Grunt", 3, 0.3, 260, 1.5),
        ]),
        ready=ready_for(3, 15), settle=40, length=260, keep=ENERGY, cues=coins_at_start(1240),
    ),
    "nightmare": dict(  # the Nightmare lap: Emberwood again, darker
        pre=TO_MENU,
        setup=battle(4, 20, dmg=20, rate=12, spawns=[
            spawn("Grunt", 5, 0.1, 200, 1.6), spawn("Grunt", 4, 0.3, 320, 1.7), spawn("Tank", 1, 0.2, 90, 1.6),
        ]),
        ready=ready_for(4, 20), settle=50, length=220, keep=ENERGY, cues=coins_at_start(2310),
    ),

    # 2: no taps at all. A steady stream at an easy wave; the archer picks them off
    # and the coin counter ticks up with every kill.
    "alone": dict(
        pre=TO_MENU,
        setup=battle(0, 8, natural=False, dmg=12, rate=12, perks=["Multishot"], spawns=[
            spawn("Grunt", 3, 0.0, 250, 1.15), spawn("Grunt", 2, 0.2, 55, 1.2), spawn("Runner", 1, 0.4, 160, 1.4),
            spawn("Grunt", 2, 0.6, 30, 1.85, every=2.6), spawn("Grunt", 1, 1.1, 125, 1.8, every=2.2),
            spawn("Grunt", 2, 1.6, 215, 1.85, every=2.9), spawn("Grunt", 1, 2.0, 300, 1.8, every=2.4),
            spawn("Runner", 1, 2.6, 175, 1.9, every=3.7),
        ]),
        ready=ready_for(0, 8), settle=60, length=330, keep=ENERGY, cues=coins_at_start(214),
    ),

    # ---- stills for the website's screenshot rail (pick the frame afterwards) ----
    "still_storm": dict(   # the Storm Rod chaining through the dead, a full field
        pre=TO_MENU,
        setup=battle(2, 12, natural=True, dmg=10, rate=10, perks=["Storm", "Storm", "Storm"], spawns=[
            spawn("Grunt", 4, 0.1, 225, 1.25), spawn("Grunt", 4, 0.2, 315, 1.3), spawn("Grunt", 3, 0.3, 135, 1.35),
            spawn("Grunt", 3, 0.4, 40, 1.4), spawn("Runner", 2, 0.6, 270, 1.3),
            spawn("Grunt", 3, 3.0, 250, 1.4, every=3.0), spawn("Grunt", 3, 4.0, 15, 1.4, every=3.5),
        ]),
        ready=ready_for(2, 12), settle=60, length=480, keep=ENERGY + r"""
if (gm != null && gm.Playing) { gm.zapInterval.level = 5; gm.chainCount.level = 3; }""",
        cues=coins_at_start(640),
    ),
    "still_boss": dict(    # the Boss Ogre's SLAM windup, at its real health
        pre=TO_MENU,
        setup=battle(0, 10, natural=False, dmg=12, rate=10, spawns=[
            spawn("Boss", 1, 0.2, 300, 0.7), spawn("Grunt", 4, 0.4, 205, 1.3), spawn("Grunt", 3, 0.8, 60, 1.4),
            spawn("Grunt", 2, 2.5, 140, 1.5),
        ]),
        ready=ready_for(0, 10), settle=50, length=900, keep=ENERGY,
        cues=coins_at_start(355) + r"""
Enemy boss = null;
foreach (var e in Enemy.Active) if (e != null && e.isBoss && e.Alive && e.gameObject.activeInHierarchy) boss = e;
if (st[1] == 0 && boss != null && boss.WindingUp) { st[1] = frame; notes.AppendLine("windup at " + frame + " hp " + boss.CurrentHp.ToString("F0") + "/" + boss.MaxHp.ToString("F0")); lengthFrames = frame + 70; }
""",
    ),
}
