#!/usr/bin/env python3
"""Build the phone reading version of the GreatLife training manual.

    python3 tools/build_reader.py "<manual>.docx"

Writes, in the repo root:
    manual-reader.html      the reading page (text re-wraps to fit a phone)
    manual-reader/          pictures from the Word file (cover, charts)

How it works: pandoc turns the Word file into HTML, then this script
  - drops the Word file's typed Table of Contents and its
    "Back to Contents" / "Return to Index" links (the page makes its own),
  - gives every Heading 1 an id the Training page can link to
    (Section 15 -> #section-15, Appendix A -> #appendix-a, Foreword -> #foreword),
  - builds a tap-friendly Contents list and a "Contents" link under each heading,
  - wraps tables so a wide worksheet scrolls sideways inside its own box
    instead of pushing the whole page off the screen,
  - pours it all into the page template (tools/reader_template.html).

Needs: pandoc, python3 with beautifulsoup4 + lxml.
Re-run it whenever the manual's Word file changes, then push the results.
"""
import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString

REPO = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "reader_template.html"
OUT_HTML = REPO / "manual-reader.html"
OUT_MEDIA = REPO / "manual-reader"

BACKLINK_RE = re.compile(r"(back to contents|return to (the )?index|back to (the )?index)", re.I)
TOC_RE = re.compile(r"^\s*table of contents\s*$", re.I)
FOREWORD_RE = re.compile(r"^\s*forew?ord\b|^\s*forward\b", re.I)


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


def heading_id(text, used):
    t = clean(text)
    m = re.match(r"(section|appendix)\s+([0-9]+|[a-z])\b", t, re.I)
    if m:
        base = f"{m.group(1).lower()}-{m.group(2).lower()}"
    elif FOREWORD_RE.match(t):
        base = "foreword"
    else:
        base = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "part"
    hid, n = base, 2
    while hid in used:
        hid, n = f"{base}-{n}", n + 1
    used.add(hid)
    return hid


def short_label(text):
    """'SECTION 15 — 7-Day Follow-Up Call Sequence' -> ('Section 15', '7-Day Follow-Up Call Sequence')."""
    t = clean(text)
    def tidy(s):
        letters = [c for c in s if c.isalpha()]
        mostly_caps = letters and sum(c.isupper() for c in letters) / len(letters) > 0.7
        return s.title() if mostly_caps else s

    m = re.match(r"((?:section|appendix)\s+(?:[0-9]+|[a-z]))\s*[—–:\-]+\s*(.*)$", t, re.I)
    if m:
        return m.group(1).title(), tidy(m.group(2))
    if FOREWORD_RE.match(t):
        return "", "Foreword"
    return "", tidy(t)


def convert(docx):
    work = Path(tempfile.mkdtemp())
    media_dir = work / "media"
    subprocess.run(
        ["pandoc", str(docx), "-f", "docx", "-t", "html5", "--wrap=none",
         f"--extract-media={media_dir}", "-o", str(work / "body.html")],
        check=True,
    )
    soup = BeautifulSoup((work / "body.html").read_text(encoding="utf-8"), "lxml")
    body = soup.body or soup

    # 1. Remove "Back to Contents" / "Return to Index" links and their empty paragraphs.
    for a in body.find_all("a"):
        if BACKLINK_RE.search(a.get_text(" ")):
            parent = a.parent
            a.decompose()
            if parent and parent.name in ("p", "div") and not clean(parent.get_text()) and not parent.find("img"):
                parent.decompose()

    # 2. Split into: cover (before first h1), typed TOC (dropped), and sections.
    cover, sections, current, in_toc = [], [], None, False
    for node in list(body.children):
        if isinstance(node, NavigableString):
            if not node.strip():
                continue
        if getattr(node, "name", None) == "h1":
            in_toc = bool(TOC_RE.match(node.get_text()))
            if in_toc:
                current = None
                continue
            current = {"h1": node, "nodes": []}
            sections.append(current)
            continue
        if in_toc:
            continue
        (current["nodes"] if current else cover).append(node)

    if not sections:
        sys.exit("No Heading 1 sections found — is this the right Word file?")

    # 3. Pictures: copy into manual-reader/ and point <img> there.
    if OUT_MEDIA.exists():
        shutil.rmtree(OUT_MEDIA)
    img_map = {}
    for img in soup.find_all("img"):
        src = img.get("src", "")
        p = Path(src)
        if p.exists():
            OUT_MEDIA.mkdir(exist_ok=True)
            name = img_map.get(src) or f"img{len(img_map) + 1}{p.suffix.lower()}"
            if src not in img_map:
                shutil.copy(p, OUT_MEDIA / name)
                img_map[src] = name
            img["src"] = f"manual-reader/{name}"
        for attr in ("style", "width", "height"):
            img.attrs.pop(attr, None)
        img["loading"] = "lazy"
        if not img.get("alt"):
            img["alt"] = ""

    # 4. Tables: let wide worksheets scroll inside their own box.
    for table in soup.find_all("table"):
        for attr in ("style", "width"):
            table.attrs.pop(attr, None)
        for col in table.find_all(["col", "colgroup"]):
            col.decompose()
        wrap = soup.new_tag("div", attrs={"class": "table-wrap"})
        table.wrap(wrap)

    # 5. Build section HTML + Contents list.
    used, toc_items, parts = set(), [], []
    for sec in sections:
        title_text = sec["h1"].get_text(" ")
        hid = heading_id(title_text, used)
        num, name = short_label(title_text)
        toc_items.append(
            f'<li><a href="#{hid}">'
            + (f'<span class="toc-num">{html.escape(num)}</span>' if num else "")
            + f'<span class="toc-name">{html.escape(name)}</span></a></li>'
        )
        inner = "".join(str(n) for n in sec["nodes"])
        parts.append(
            f'<section class="part" id="{hid}">\n'
            f'<h2>{"<span class=sec-num>" + html.escape(num) + "</span>" if num else ""}{html.escape(name)}</h2>\n'
            f'<a class="to-contents" href="#contents">▲ Contents</a>\n'
            f"{inner}\n</section>"
        )

    cover_html = "".join(str(n) for n in cover)
    page = TEMPLATE.read_text(encoding="utf-8")
    page = (page.replace("{{COVER}}", cover_html)
                .replace("{{CONTENTS}}", "\n".join(toc_items))
                .replace("{{SECTIONS}}", "\n".join(parts)))
    OUT_HTML.write_text(page, encoding="utf-8")
    shutil.rmtree(work, ignore_errors=True)
    print(f"Wrote {OUT_HTML.name}: {len(sections)} sections, {len(img_map)} pictures")
    for item in toc_items:
        print("  ", re.sub(r"<[^>]+>", " ", item).strip())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    convert(Path(sys.argv[1]))
