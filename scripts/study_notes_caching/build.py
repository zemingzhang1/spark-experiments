# -*- coding: utf-8 -*-
"""Build notes/Caching_Study_Notes.pdf from spark/4_caching.ipynb."""
import base64
import html as htmllib
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pylibs"))

import content          # noqa: E402
import typed            # noqa: E402
from pypdf import PdfReader, PdfWriter   # noqa: E402

REPO = r"F:\Projects\spark-experiments"
NB = os.path.join(REPO, "spark", "4_caching.ipynb")
RUN = os.path.join(REPO, "notes", "caching_run")
OUTPDF = os.path.join(REPO, "notes", "Caching_Study_Notes.pdf")
WORK = os.path.join(HERE, "work")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PY = os.path.join(REPO, ".venv", "Scripts", "python.exe")
os.makedirs(WORK, exist_ok=True)

FONT_B64 = base64.b64encode(
    open(os.path.join(HERE, "assets", "Caveat.ttf"), "rb").read()).decode()
DAG_B64 = base64.b64encode(
    open(os.path.join(RUN, "dag_before_after.png"), "rb").read()).decode()

HAND_CSS = """
@font-face { font-family: 'Hand'; src: url(data:font/ttf;base64,__FONT__) format('truetype'); }
@page { size: Letter; margin: 0.5in; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.jp-InputPrompt, .jp-OutputPrompt { display: none !important; }
pre, .jp-RenderedText pre { white-space: pre-wrap !important; word-break: break-word;
  font-size: 9.2px !important; line-height: 1.3 !important; }
.jp-Cell { margin-bottom: 2px !important; padding: 0 !important; }
.jp-Notebook { padding: 0 !important; }
body { font-size: 12px; }
.hn { font-family: 'Hand', cursive; color: #1f4fb5; font-size: 19px; line-height: 1.25;
  background: transparent; border: 2px solid #e8c547; border-radius: 3px 14px 4px 12px;
  padding: 6px 16px 10px; margin: 4px 0 18px 60px; transform: rotate(-0.35deg);
  break-inside: avoid; }
.hn.def { margin-left: 0; }
.hn-t { font-size: 25px; font-weight: 700; color: #b5179e;
  text-decoration: underline wavy #e9a6d9; text-underline-offset: 4px; margin: 2px 0 4px; }
.hn ul { margin: 2px 0 4px; padding-left: 18px; } .hn li { margin: 2px 0; }
.hn p { margin: 3px 0; }
.hn .cd { font-family: 'Hand'; font-weight: 700; color: #0b3a8c; background: #e8efff;
  padding: 0 3px; border-radius: 3px; }
.hn .to { color: #d62828; font-weight: 700; }
.tip { color: #c1121f; margin-top: 4px; font-size: 19px; }
.bdg { font-family: 'Hand'; color: #d62828; font-weight: 700; font-size: 17px; margin-left: 1px; }
.circ { border: 2px solid #d62828; border-radius: 48% 52% 45% 55% / 60% 45% 55% 40%;
  padding: 0 3px; margin: 0 1px; }
.arwrow { display: flex; align-items: flex-end; gap: 6px; margin: -2px 0 0 -6px; }
.arwlab { color: #d62828; font-size: 18px; }
.hn table, .hn tr, .hn td, .hn th { background: transparent !important; font-size: 19px !important; }
.ht { border-collapse: collapse; margin: 6px 0; }
.ht th { color: #b5179e; text-align: left; padding: 2px 14px 2px 4px;
  border-bottom: 1.5px solid #e9a6d9; }
.ht td { padding: 1px 14px 1px 4px; border-bottom: 1px dashed #e9d98a; vertical-align: top; }
.ht th:first-child { color: #2a9d5c; } .ht th:last-child { color: #d62828; }
.hn table.wide { width: 100% !important; table-layout: fixed; }
.hn table.wide td, .hn table.wide th { font-size: 16px !important; overflow-wrap: anywhere; }
.sk { display: block; margin: 6px 0 2px; }
.skt { font-family: 'Hand'; font-size: 15px; fill: #1f4fb5; }
""".replace("__FONT__", FONT_B64)

TYPED_CSS = """
@page { size: Letter; margin: 0.5in; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #222; font-size: 11.5px;
  line-height: 1.45; margin: 0; }
h1 { font-size: 20px; color: #1a2a5a; margin: 0 0 2px; }
.lead { color: #666; margin-bottom: 10px; font-size: 11px; }
.sec { border: 1px solid #c9ced8; border-left: 4px solid #3b5bb5; padding: 8px 12px 6px;
  margin: 0 0 10px; break-inside: avoid; }
h2 { font-size: 14px; color: #1a2a5a; margin: 0 0 5px; }
h3 { font-size: 12px; margin: 6px 0 2px; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 6px; font-size: 11px; }
th, td { border: 1px solid #d5d9e0; padding: 3px 6px; text-align: left; vertical-align: top; }
th { background: #eef1f7; color: #1a2a5a; }
code { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; font-size: 10.5px;
  background: #f1f3f7; padding: 0 3px; border-radius: 2px; color: #233a85; }
pre { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; font-size: 10px;
  background: #f6f7fa; border: 1px solid #dde1e8; padding: 6px 8px; margin: 4px 0 6px;
  white-space: pre; line-height: 1.35; overflow: hidden; }
.one { border-left: 3px solid #2a9d5c; background: #f3faf6; padding: 4px 8px; margin: 5px 0 2px; }
.warn { border-left: 3px solid #b3261e; background: #fdf0ef; color: #7a1b14;
  padding: 4px 8px; margin: 5px 0 2px; }
.say { border-left: 3px solid #3b5bb5; background: #eef2fb; padding: 4px 8px;
  margin: 5px 0 2px; font-style: italic; }
.rule { border: 2.5px solid #b3261e; background: #fdf0ef; color: #b3261e; padding: 8px 12px;
  font-size: 15px; font-weight: bold; text-align: center; }
.rule small { display: block; font-size: 11px; font-weight: normal; margin-top: 3px;
  color: #7a1b14; }
.hl { color: #b3261e; font-weight: bold; }
.cols { display: flex; gap: 8px; } .cols > div { flex: 1; min-width: 0; }
.fig { border: 1px dashed #c9ced8; padding: 4px 6px 2px; margin: 4px 0 6px; }
.newpage { break-before: page; }
.sec.flow { break-inside: auto; }
ol { margin: 3px 0 3px 0; padding-left: 18px; } li { margin: 1px 0; }
"""

LAND_CSS = """
@font-face { font-family: 'Hand'; src: url(data:font/ttf;base64,__FONT__) format('truetype'); }
@page { size: Letter landscape; margin: 0.38in; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'Hand', cursive; color: #1f4fb5; font-size: 18px; margin: 0; }
h1 { font-family: 'Hand'; font-size: 30px; color: #b5179e;
  text-decoration: underline wavy #e9a6d9; text-underline-offset: 5px; margin: 0 0 2px; }
.lead { font-size: 18px; color: #1f4fb5; margin: 0 0 8px; }
table.land { width: 100%; table-layout: fixed; border-collapse: collapse;
  border: 2px solid #e8c547; }
table.land th { font-size: 19px; color: #b5179e; text-align: left; padding: 4px 8px;
  border-bottom: 1.5px solid #e9a6d9; }
table.land td { font-size: 17px; padding: 5px 8px; border-bottom: 1px dashed #e9d98a;
  vertical-align: top; overflow-wrap: anywhere; }
table.land tr { break-inside: avoid; }
table.land col:nth-child(1) { width: 14%; }
td:first-child { color: #0b3a8c; font-weight: 700; }
code { font-family: 'Hand'; font-weight: 700; color: #0b3a8c; background: #e8efff;
  padding: 0 3px; border-radius: 3px; }
.chip { display: inline-block; font-size: 14px; color: #2a9d5c; }
.skt { font-family: 'Hand'; font-size: 14px; fill: #1f4fb5; }
.foot { font-size: 18px; color: #c1121f; margin-top: 8px; }
""".replace("__FONT__", FONT_B64)

COLGROUP = ('<colgroup><col style="width:17%"><col style="width:24%">'
            '<col style="width:25%"><col style="width:34%"></colgroup>')


# ------------------------------------------------------------- 1. notebook --
def patched_notebook():
    nb = json.load(io.open(NB, encoding="utf-8"))
    cells = nb["cells"]
    # explain(True) prints four plans; for these notes only the physical one earns
    # its page. Trim cells 8 and 9 down to it.
    for idx in (8, 9):
        for o in cells[idx].get("outputs", []):
            txt = "".join(o.get("text", []))
            a = txt.rfind("== Physical Plan ==")
            if a > 0:
                o["text"] = ["[parsed / analyzed / optimized plans trimmed - "
                             "see spark/2_reading_query_plans.ipynb]\n\n"] + [txt[a:]]
    for idx in sorted(content.AFTER, reverse=True):
        keys = content.AFTER[idx]
        if isinstance(keys, str):
            keys = [keys]
        for k in reversed(keys):
            cells.insert(idx + 1, {"cell_type": "markdown", "metadata": {},
                                   "source": ["NOTEPH%sEND" % k]})
    p = os.path.join(WORK, "patched.ipynb")
    io.open(p, "w", encoding="utf-8").write(json.dumps(nb))
    return p


def to_html(ipynb):
    out = os.path.join(WORK, "main_raw")
    subprocess.check_call([PY, "-I", "-m", "nbconvert", "--to", "html",
                           "--output", out, ipynb],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out + ".html"


def add_circles(h):
    marks = [(m.start(), m.group(1)) for m in
             re.finditer(r"NOTEPH(\w+)END", h)]
    missing = []
    for i, (pos, key) in enumerate(marks):
        if key not in content.CIRCLES:
            continue
        start = marks[i - 1][0] if i else 0
        region = h[start:pos]
        anchor = region.rfind("== Physical Plan ==")
        if anchor < 0:
            anchor = 0
        head, tail = h[:start + anchor], h[start + anchor:pos]
        rest = h[pos:]
        for token, num in content.CIRCLES[key]:
            esc = htmllib.escape(token, quote=False)
            if esc in tail:
                tail = tail.replace(
                    esc, '<span class="circ">%s</span>%s'
                         % (esc, content.badge(num)), 1)
            else:
                missing.append((key, token))
        h = head + tail + rest
        marks = [(m.start(), m.group(1)) for m in re.finditer(r"NOTEPH(\w+)END", h)]
    for k, t in missing:
        print("  !! circle token not found [%s]: %s" % (k, t[:70]))
    return h


def build_main():
    h = io.open(to_html(patched_notebook()), encoding="utf-8").read()
    h = add_circles(h)
    for key, note_html in content.HAND.items():
        h, n = re.subn(r"<p>NOTEPH%sEND</p>" % key, lambda m: note_html, h)
        if not n:
            print("  !! placeholder not replaced:", key)
    h = re.sub(r"NOTEPH\w+END", "", h)
    h = h.replace("</head>", "<style>%s</style></head>" % HAND_CSS)
    p = os.path.join(WORK, "main.html")
    io.open(p, "w", encoding="utf-8").write(h)
    return p


def build_typed():
    h = ("<!doctype html><html><head><meta charset='utf-8'><style>%s</style></head>"
         "<body>%s</body></html>" % (TYPED_CSS, typed.typed_body(DAG_B64)))
    p = os.path.join(WORK, "typed.html")
    io.open(p, "w", encoding="utf-8").write(h)
    return p


def build_land():
    body = typed.LANDSCAPE_BODY.replace('<table class="land">',
                                        '<table class="land">' + COLGROUP)
    h = ("<!doctype html><html><head><meta charset='utf-8'><style>%s</style></head>"
         "<body>%s</body></html>" % (LAND_CSS, body))
    p = os.path.join(WORK, "landscape.html")
    io.open(p, "w", encoding="utf-8").write(h)
    return p


def print_pdf(html_path, pdf_name, landscape=False):
    pdf = os.path.join(WORK, pdf_name)
    if os.path.exists(pdf):
        os.remove(pdf)
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--run-all-compositor-stages-before-draw", "--virtual-time-budget=15000",
           "--print-to-pdf=" + pdf, url]
    if landscape:
        cmd.insert(-1, "--landscape")
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return pdf


def merge(main_pdf, typed_pdf, land_pdf):
    w = PdfWriter()
    for p in PdfReader(main_pdf).pages:
        w.add_page(p)
    for p in PdfReader(land_pdf).pages:
        w.add_page(p)
    for p in PdfReader(typed_pdf).pages:
        w.add_page(p)
    with open(OUTPDF, "wb") as f:
        w.write(f)
    return len(PdfReader(OUTPDF).pages)


if __name__ == "__main__":
    print("building notebook pages ...")
    m = print_pdf(build_main(), "main.pdf")
    print("building typed pages ...")
    t = print_pdf(build_typed(), "typed.pdf")
    print("building landscape page ...")
    l = print_pdf(build_land(), "landscape.pdf", landscape=True)
    for p in (m, t, l):
        print("  %-14s %d pages" % (os.path.basename(p), len(PdfReader(p).pages)))
    n = merge(m, t, l)
    print("merged -> %s  (%d pages)" % (OUTPDF, n))
