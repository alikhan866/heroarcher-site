"""Record one trailer take in the open Unity editor.

    python trailer/unity/record.py <take> [<take> ...]

Needs the editor in play mode with the MCP-for-Unity HTTP bridge on
127.0.0.1:8080 (Window > MCP for Unity). Each take in takes.py is a setup
snippet (stage the run) plus the driver (driver.cs.tmpl) with that take's
ready test, per-frame keepers and cues. Frames land in
trailer/build/takes/<take>/f_00000.jpg.., the game's own sound in audio.f32
(float32, interleaved), and every simulated tap in taps.txt.
"""
import json
import os
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import takes as T  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, "..", "build", "takes")).replace("\\", "/")
URL = "http://127.0.0.1:8080/mcp"
_sid = None
FLIP = True  # ScreenCapture into a RenderTexture comes out upside down on D3D


def _post(body, timeout=120):
    global _sid
    req = urllib.request.Request(URL, data=json.dumps(body).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json, text/event-stream")
    if _sid:
        req.add_header("Mcp-Session-Id", _sid)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        _sid = r.headers.get("mcp-session-id") or _sid
        raw = r.read().decode("utf-8", "replace")
    for line in raw.splitlines():
        if line.startswith("data:"):
            m = json.loads(line[5:])
            if m.get("id") == 2:
                return m
    return None


def execute(code):
    global _sid
    if _sid is None:
        _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
               "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "rec", "version": "1"}}})
        _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    m = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
               "params": {"name": "execute_code", "arguments": {"action": "execute", "code": code, "safety_checks": False}}})
    text = m["result"]["content"][0]["text"]
    d = json.loads(text)
    if not d.get("success"):
        raise RuntimeError(json.dumps(d, indent=1)[:4000])
    return d["data"].get("result")


MENU_READY = ('return GameManager.I != null && GameManager.I.State == GameState.Menu'
              ' && Time.timeSinceLevelLoad > 1.5f ? "ok" : "wait";')


def build(spec):
    src = open(os.path.join(HERE, "driver.cs.tmpl"), encoding="utf-8").read()
    for k, v in {"TAKE": spec["name"], "SETTLE": str(spec.get("settle", 30)), "LENGTH": str(spec["length"]),
                 "OUTDIR": OUT, "KEEP": spec.get("keep", ""), "READY": spec.get("ready", "return gm != null && gm.Playing;"),
                 "CUES": spec.get("cues", ""), "FLIP": "true" if FLIP else "false"}.items():
        src = src.replace("@@" + k + "@@", v)
    return src


def record(name):
    spec = dict(T.TAKES[name])
    spec["name"] = name
    t0 = time.time()
    if spec.get("pre"):
        print(" ", execute(T.PRELUDE + spec["pre"]))
        # wait for the reloaded menu to settle (a surrender reloads the scene)
        for _ in range(60):
            time.sleep(1)
            if execute(MENU_READY) == "ok":
                break
        time.sleep(1)
    if spec.get("setup"):
        print(" ", execute(T.PRELUDE + spec["setup"]))
    print(" ", execute(build(spec)))
    done = os.path.join(OUT, name, "done.txt")
    while not os.path.exists(done):
        time.sleep(2)
        if time.time() - t0 > 1800:
            raise RuntimeError("take timed out")
    meta = open(os.path.join(OUT, name, "meta.txt")).read()
    taps = open(os.path.join(OUT, name, "taps.txt")).read()
    kinds = {}
    for line in open(os.path.join(OUT, name, "events.txt")).read().splitlines():
        if line.strip():
            k = line.split()[1]
            kinds[k] = kinds.get(k, 0) + 1
    print("  done in %.0fs\n  %s\n  events %s\n  taps:\n%s" % (time.time() - t0, meta.replace("\n", " | "), kinds, taps))


if __name__ == "__main__":
    for n in sys.argv[1:]:
        print("take", n)
        record(n)
