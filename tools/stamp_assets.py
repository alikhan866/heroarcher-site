"""Stamp the stylesheet and script links with a hash of their contents.

    python tools/stamp_assets.py

GitHub Pages lets browsers keep CSS and JS for 10 minutes, and the file names
never change, so after a push a visitor can get the new page with the old
styles and script. Every page links them as site.css?v=<hash>; run this after
changing either file (before committing) and the link changes with the file.
"""
import glob
import hashlib
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ASSETS = {"site.css": "assets/css/site.css", "site.js": "assets/js/site.js"}

stamps = {}
for name, path in ASSETS.items():
    with open(os.path.join(ROOT, path), "rb") as f:
        stamps[name] = hashlib.sha256(f.read()).hexdigest()[:10]

pages = [p for p in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True) if "trailer" + os.sep + "build" not in p]
for page in pages:
    with open(page, "rb") as f:
        html = f.read()
    out = html
    for name, stamp in stamps.items():
        pattern = re.compile(rb"(" + re.escape(name.encode()) + rb")(\?v=[0-9a-f]+)?(?=[\"'])")
        out = pattern.sub(rb"\1?v=" + stamp.encode(), out)
    if out != html:
        with open(page, "wb") as f:  # bytes in, bytes out: line endings untouched
            f.write(out)
        print("  stamped", os.path.relpath(page, ROOT))
print("  " + ", ".join("%s?v=%s" % kv for kv in stamps.items()))
