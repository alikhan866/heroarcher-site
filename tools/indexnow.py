"""Tell Bing (and the other IndexNow engines) that pages changed.

    python tools/indexnow.py            every URL in sitemap.xml
    python tools/indexnow.py /privacy/  just these paths

Run it after a push that changes what a page says. Bing's index feeds Bing
itself, ChatGPT search, Copilot, DuckDuckGo and Yahoo, and IndexNow gets a page
re-read in minutes instead of whenever the crawler comes back. Google does not
use IndexNow: for Google, submit the sitemap once in Search Console and it
re-reads it on its own.

The key is the file <key>.txt at the site root; it proves we own the site. It
is not a secret (anyone can read it), but keep it: a new key means the old
submissions stop counting until Bing reads the new file.
"""
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOST = "heroarcher.com"
KEY = "f065e41e63c11c5649b1ed4b4fdce3c4"

if not os.path.exists(os.path.join(ROOT, KEY + ".txt")):
    raise SystemExit("the key file %s.txt is missing from the site root" % KEY)

if len(sys.argv) > 1:
    urls = ["https://%s/%s" % (HOST, p.lstrip("/")) for p in sys.argv[1:]]
else:
    with open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8") as f:
        urls = re.findall(r"<loc>([^<]+)</loc>", f.read())

body = json.dumps({
    "host": HOST,
    "key": KEY,
    "keyLocation": "https://%s/%s.txt" % (HOST, KEY),
    "urlList": urls,
}).encode()
req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
                             headers={"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=30) as r:
    # 200 = taken, 202 = taken, key check pending
    print(r.status, "for", len(urls), "URLs:", ", ".join(urls))
