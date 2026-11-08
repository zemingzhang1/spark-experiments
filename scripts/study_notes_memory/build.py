# -*- coding: utf-8 -*-
"""Build notes/Memory_Management_Study_Notes.pdf.

Source material is the memory-management video plus the two boards that already
live in this repo (docs/images/memory_management.png and unified_memory.png).
There is no notebook for this chapter, so the "main" pages are the two boards
with a handwritten layer on top, printed with headless Chrome and merged with
the typed extra-notes pages.
"""
import base64
import io
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pylibs"))

import boards           # noqa: E402
import hand             # noqa: E402
import typed            # noqa: E402
from pypdf import PdfReader, PdfWriter      # noqa: E402
from PIL import Image                       # noqa: E402

REPO = os.path.dirname(os.path.dirname(HERE))
IMGDIR = os.path.join(REPO, "docs", "images")
OUTPDF = os.path.join(REPO, "notes", "Memory_Management_Study_Notes.pdf")
WORK = os.path.join(HERE, "work")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FONT = os.path.join(os.path.dirname(HERE), "study_notes_caching", "assets",
                    "Caveat.ttf")
os.makedirs(WORK, exist_ok=True)

FONT_B64 = base64.b64encode(open(FONT, "rb").read()).decode()


def b64(path):
    return base64.b64encode(open(path, "rb").read()).decode()


def crops():
    """Slice unified_memory.png into the five panels boards.py annotates."""
    src = Image.open(os.path.join(IMGDIR, "unified_memory.png")).convert("RGB")
    out = {}
    for name, box in boards.CROPS.items():
        p = os.path.join(WORK, name + ".png")
        src.crop(box).save(p)
        out[name] = b64(p)
    return out


# --------------------------------------------------------------------- CSS --
HAND_CSS = """
@font-face { font-family: 'Hand'; src: url(data:font/ttf;base64,__FONT__) format('truetype'); }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font-family: 'Hand', cursive; color: #1f4fb5; }

/* ---- annotated board ---- */
.board { position: relative; width: 89%; margin: 0 auto; line-height: 0; }
.board img { width: 100%; display: block; }
.an { position: absolute; font-family: 'Hand', cursive; color: #1f4fb5;
  font-size: 15.5px; line-height: 1.12; letter-spacing: .1px; }
.an.red, .an .red, .red { color: #d62828; }
.an b { font-weight: 700; color: #0b3a8c; }
.an.red b { color: #d62828; }
.an i { font-style: italic; color: #2a9d5c; }
.ring { position: absolute; border: 2.2px solid #d62828;
  border-radius: 48% 52% 45% 55% / 60% 45% 55% 40%; box-sizing: border-box; }
.circ { border: 2px solid #d62828; border-radius: 48% 52% 45% 55% / 60% 45% 55% 40%;
  padding: 0 4px; margin: 0 1px; color: #d62828; }
.ptitle { font-family: 'Hand'; font-size: 27px; font-weight: 700; color: #b5179e;
  text-decoration: underline wavy #e9a6d9; text-underline-offset: 4px;
  margin: 0 0 2px; line-height: 1.1; }
.psub { font-size: 17px; color: #1f4fb5; margin: 0 0 6px; line-height: 1.15; }
.foot { font-family: 'Hand'; font-size: 16px; color: #c1121f; line-height: 1.15;
  margin-top: 4px; }
.hn.wide1 { margin-top: 6px; }
.ht.cmp td, .ht.cmp th { width: 50% !important; }

/* ---- handwritten note boxes ---- */
.hn { font-family: 'Hand', cursive; color: #1f4fb5; font-size: 18px;
  line-height: 1.22; background: transparent; border: 2px solid #e8c547;
  border-radius: 3px 14px 4px 12px; padding: 5px 14px 8px; margin: 4px 0 10px 60px;
  transform: rotate(-0.35deg); break-inside: avoid; }
.hn.def { margin-left: 0; }
.hn.tight { margin-bottom: 6px; padding: 4px 14px 6px; }
.hn-t { font-size: 23px; font-weight: 700; color: #b5179e;
  text-decoration: underline wavy #e9a6d9; text-underline-offset: 4px;
  margin: 1px 0 3px; }
.hn-t2 { font-size: 18px; font-weight: 700; color: #b5179e; margin: 0 0 1px;
  line-height: 1.1; }
.hn ul { margin: 1px 0 2px; padding-left: 16px; } .hn li { margin: 1px 0; }
.hn p { margin: 2px 0; }
.hn .cd, .cd { font-family: 'Hand'; font-weight: 700; color: #0b3a8c;
  background: #e8efff; padding: 0 3px; border-radius: 3px; }
.tip { color: #c1121f; margin-top: 3px !important; font-size: 18px; }
.hn table, .hn tr, .hn td, .hn th { background: transparent !important; }
.ht { border-collapse: collapse; margin: 4px 0 2px; }
.ht th { color: #b5179e; text-align: left; padding: 1px 12px 1px 3px;
  border-bottom: 1.5px solid #e9a6d9; font-size: 17px; }
.ht td { padding: 1px 12px 1px 3px; border-bottom: 1px dashed #e9d98a;
  vertical-align: top; font-size: 17px; line-height: 1.14; }
.ht th:first-child { color: #2a9d5c; }
.ht.wide { width: 100%; table-layout: fixed; }
.ht.wide td, .ht.wide th { overflow-wrap: anywhere; }
.ht.wide td:first-child, .ht.wide th:first-child { width: 20%; }
.ht.calc td:first-child, .ht.calc th:first-child { width: 26%; }
.ht.calc td:nth-child(2), .ht.calc th:nth-child(2) { width: 46%; }
.sk { display: block; margin: 4px 0 0; }
.skt { font-family: 'Hand'; font-size: 14px; fill: #1f4fb5; }

/* ---- board 2: cropped panels + notes ---- */
.b2head { font-family: 'Hand'; font-size: 26px; font-weight: 700; color: #b5179e;
  text-decoration: underline wavy #e9a6d9; text-underline-offset: 4px;
  margin: 0 0 4px; }
table.b2 { width: 100%; table-layout: fixed; border-collapse: collapse;
  margin-bottom: 6px; }
table.b2 tr { break-inside: avoid; }
table.b2 td { vertical-align: middle; padding: 3px 2px;
  border-bottom: 1px dashed #e9d98a; }
table.b2 td.pic { width: 54%; line-height: 0; }
table.b2 td.pic img { max-width: 100%; display: block; }
table.b2 td.note { width: 46%; font-size: 15.5px; line-height: 1.14;
  padding-left: 10px; }
table.b2 td.note ul { margin: 1px 0 0; padding-left: 15px; }
table.b2 td.note li { margin: 1px 0; }
""".replace("__FONT__", FONT_B64)

TYPED_CSS = """
@page { size: Letter; margin: 0.5in; }
* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: 'DejaVu Sans', Arial, sans-serif; color: #222; font-size: 11.5px;
  line-height: 1.45; margin: 0; }
h1 { font-size: 20px; color: #1a2a5a; margin: 0 0 2px; }
.lead { color: #666; margin-bottom: 10px; font-size: 11px; }
.sec { border: 1px solid #c9ced8; border-left: 4px solid #3b5bb5;
  padding: 8px 12px 6px; margin: 0 0 10px; break-inside: avoid; }
h2 { font-size: 14px; color: #1a2a5a; margin: 0 0 5px; }
h3 { font-size: 12px; margin: 7px 0 2px; color: #333; }
table { border-collapse: collapse; width: 100%; margin: 4px 0 6px; font-size: 10.5px; }
th, td { border: 1px solid #d5d9e0; padding: 3px 6px; text-align: left;
  vertical-align: top; }
th { background: #eef1f7; color: #1a2a5a; }
code { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; font-size: 10px;
  background: #f1f3f7; padding: 0 3px; border-radius: 2px; color: #233a85; }
pre { font-family: 'DejaVu Sans Mono', 'Consolas', monospace; font-size: 9.6px;
  background: #f6f7fa; border: 1px solid #dde1e8; padding: 6px 8px; margin: 4px 0 6px;
  white-space: pre; line-height: 1.35; overflow: hidden; }
pre.py { background: #f4f7f4; border-color: #d7e2d7; }
.one { border-left: 3px solid #2a9d5c; background: #f3faf6; padding: 4px 8px;
  margin: 6px 0 2px; }
.warn { border-left: 3px solid #b3261e; background: #fdf0ef; color: #7a1b14;
  padding: 4px 8px; margin: 5px 0 2px; }
.say { border-left: 3px solid #3b5bb5; background: #eef2fb; padding: 4px 8px;
  margin: 4px 0 2px; font-style: italic; }
.rule { border: 2.5px solid #b3261e; background: #fdf0ef; color: #b3261e;
  padding: 7px 12px; font-size: 14px; font-weight: bold; text-align: center;
  margin-bottom: 6px; }
.rule small { display: block; font-size: 10.5px; font-weight: normal;
  margin-top: 3px; color: #7a1b14; }
.hl { color: #b3261e; font-weight: bold; }
.newpage { break-before: page; }
ol, ul { margin: 3px 0; padding-left: 18px; } li { margin: 1px 0; }
"""

PAGE1 = """
<div class="ptitle">Spark Memory Management &mdash; executor layout</div>
<div class="psub">one executor, <span class="cd">--executor-memory 10G</span>,
every default left alone &middot; base board:
<span class="cd">docs/images/memory_management.png</span></div>
__BOARD1__
__SKETCH__
"""

PAGE2 = """
<div class="ptitle">Reading the layout</div>
__REGIONS__
"""


def html(css, body, page_css=""):
    return ("<!doctype html><html><head><meta charset='utf-8'><style>%s\n%s"
            "</style></head><body>%s</body></html>" % (css, page_css, body))


def write(name, text):
    p = os.path.join(WORK, name)
    io.open(p, "w", encoding="utf-8").write(text)
    return p


def print_pdf(html_path, pdf_name, landscape=False):
    pdf = os.path.join(WORK, pdf_name)
    if os.path.exists(pdf):
        os.remove(pdf)
    url = "file:///" + html_path.replace("\\", "/")
    cmd = [CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
           "--no-pdf-header-footer", "--print-to-pdf-no-header",
           "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=20000", "--print-to-pdf=" + pdf, url]
    if landscape:
        cmd.insert(-1, "--landscape")
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return pdf


def merge(parts):
    w = PdfWriter()
    for p in parts:
        for page in PdfReader(p).pages:
            w.add_page(page)
    with open(OUTPDF, "wb") as f:
        w.write(f)
    return len(PdfReader(OUTPDF).pages)


if __name__ == "__main__":
    board_b64 = b64(os.path.join(IMGDIR, "memory_management.png"))
    crop_b64 = crops()

    print("board 1 (landscape) ...")
    p1 = print_pdf(write("p1.html", html(
        HAND_CSS,
        PAGE1.replace("__BOARD1__", boards.board1(board_b64))
             .replace("__SKETCH__", hand.page1_extra()),
        "@page { size: Letter landscape; margin: 0.32in 0.38in; }")),
        "p1.pdf", landscape=True)

    print("board 2 + handwritten pages (portrait) ...")
    p2 = print_pdf(write("p2.html", html(
        HAND_CSS,
        PAGE2.replace("__REGIONS__", hand.page2())
        + '<div style="break-before:page"></div>'
        + boards.board2(crop_b64),
        "@page { size: Letter; margin: 0.45in 0.5in; }")), "p2.pdf")

    print("typed pages ...")
    p3 = print_pdf(write("typed.html", html(TYPED_CSS, typed.typed_body())),
                   "typed.pdf")

    for p in (p1, p2, p3):
        print("  %-12s %d pages" % (os.path.basename(p), len(PdfReader(p).pages)))
    n = merge([p1, p2, p3])
    print("merged -> %s  (%d pages)" % (OUTPDF, n))
