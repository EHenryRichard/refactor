#!/usr/bin/env python3
"""Build a MySword interlinear Bible module (Hebrew OT + Greek NT).

Inputs (both inside this repo):
  ../e-Sword/FINAL/BIB++.bbli.zip       Berean Interlinear Bible, Greek NT
  source/BHSA-8-layer-interlinear.csv.zip  Hebrew OT, 8-layer interlinear
Output:
  BIBhg.bbl.mybible   (SQLite; copy into MySword's modules folder)

Usage: python3 build_interlinear.py [outfile]
"""
import csv, io, os, re, sqlite3, sys, zipfile
from collections import OrderedDict
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BIBhg.bbl.mybible")
csv.field_size_limit(10**9)


def esc(s):
    # module markup uses <...>, so literal text must not contain raw angle brackets
    return escape(s, quote=False)


def greek_verses():
    z = zipfile.ZipFile(os.path.join(HERE, "..", "e-Sword", "FINAL", "BIB++.bbli.zip"))
    name = next(n for n in z.namelist() if n.endswith(".bbli") and "__MACOSX" not in n)
    tmp = os.path.join(HERE, ".tmp_bib.bbli")
    with open(tmp, "wb") as f:
        f.write(z.read(name))
    c = sqlite3.connect(tmp)
    word = re.compile(
        r"<INT><grk>(.*?)</grk> <sup><font color='gray'>(.*?)</font></sup><sup>\|</sup>"
        r"<num>(G\d+)</num><sup>\|</sup><not>(.*?)</not><sup>\|</sup><sup><red>(.*?)</red></sup><int>")
    out, nwords = OrderedDict(), 0
    token = re.compile(r"<var>|</var>|<not>[a-z]</not>|" + word.pattern)
    for b, ch, v, text in c.execute("select Book,Chapter,Verse,Scripture from Bible order by 1,2,3"):
        parts, in_var = [], False
        # textual-variant words are italic in the Berean convention; footnote letters are dropped
        rest = token.sub(lambda m: "", text)
        assert not rest.strip(), (b, ch, v, rest[:80])
        for m in token.finditer(text):
            t = m.group(0)
            if t == "<var>":
                in_var = True
            elif t == "</var>":
                in_var = False
            elif m.group(1) is not None:
                gk, tl, strong, morph, en = m.groups()
                en = esc(en)
                if in_var:
                    en = "<i>%s</i>" % en
                parts.append("「<Xg>%s</Xg><Xt>%s</Xt><W%s><WT%s><Xe>%s</Xe>」"
                             % (esc(gk), esc(tl), strong, esc(morph), en))
        assert parts and not in_var, (b, ch, v)
        nwords += len(parts)
        out[(b, ch, v)] = " ".join(parts)
    c.close(); os.remove(tmp)
    return out, nwords


def hebrew_verses():
    z = zipfile.ZipFile(os.path.join(HERE, "source", "BHSA-8-layer-interlinear.csv.zip"))
    name = next(n for n in z.namelist() if n.endswith(".csv") and "__MACOSX" not in n)
    rd = csv.reader(io.TextIOWrapper(z.open(name), encoding="utf-8", newline=""),
                    delimiter="\t", quoting=csv.QUOTE_NONE)
    next(rd)
    out, nwords = OrderedDict(), 0
    tag = re.compile(r"<[^>]+>")
    for r in rd:
        m = re.match(r"〔\d+｜(\d+)｜(\d+)｜(\d+)〕", r[1])
        key = tuple(map(int, m.groups()))
        heb = tag.sub("", r[2]).strip()
        translit, morph, gloss = r[3].strip(), r[8].strip(), r[10].strip()
        # original Strong's only; H9000+ are Tyndale prefix pseudo-entries MySword has no entry for
        strongs = [s for s in r[7].split("_") if re.fullmatch(r"H\d+", s) and int(s[1:]) < 9000]
        w = "「<Xh>%s</Xh>" % esc(heb)
        if translit:
            w += "<Xt>%s</Xt>" % esc(translit)
        w += "".join("<W%s>" % s for s in strongs)
        if morph:
            w += "<WT%s>" % esc(morph)
        w += "<Xe>%s</Xe>」" % esc(gloss)
        out.setdefault(key, []).append(w)
        nwords += 1
    return OrderedDict((k, "<Xr>%s</Xr>" % " ".join(v)) for k, v in out.items()), nwords


RULES = [
    ("「", "<span class='w'>"),
    ("」", "</span>"),
    ("<Xr>(.*?)</Xr>", "<div class='hbv'>$1</div>"),
    ("<Xh>(.*?)</Xh>", "<span class='hb'>$1</span>"),
    ("<Xg>(.*?)</Xg>", "<span class='gk'>$1</span>"),
    ("<Xt>(.*?)</Xt>", "<br><span class='tl'>$1</span>"),
    ("<Xe>(.*?)</Xe>", "<br><span class='en'>$1</span>"),
]
CSS = """span.w {display:inline-block;text-align:center;vertical-align:top;margin:0 5px 8px 5px;}
span.gk {font-size:135%;color:Midnightblue;font-weight:bold;}
span.hb {font-size:150%;color:Midnightblue;font-weight:bold;direction:rtl;}
span.tl {font-size:75%;color:Gray;font-style:italic;}
span.en {font-size:85%;color:IndianRed;font-weight:bold;}
div.hbv {direction:rtl;text-align:right;}"""

DESC = """<h2>Berean Interlinear Bible &mdash; Hebrew &amp; Greek</h2>
<p>Every word of the Old Testament (Hebrew) and New Testament (Greek) with transliteration,
Strong's number, morphology and an English gloss. Tap a Strong's number or morphology code
for the lookup.</p>
<p><b>Greek NT:</b> Berean Interlinear Bible &copy; 2016 by Bible Hub (berean.bible), free licence.<br>
<b>Hebrew OT:</b> Biblia Hebraica Stuttgartensia text and morphology from ETCBC; Strong's numbers from
OpenScriptures via the Berean project; alignment by Eliran Wong's Open Hebrew Bible project
(CC BY-NC 4.0, github.com/eliranwong/OpenHebrewBible). Hebrew glosses are ETCBC glosses.
<b>Non-commercial use only.</b></p>
<p>Verse numbering is KJV (Nehemiah 7:68 has no Hebrew text).</p>"""


def build():
    gk, ng = greek_verses()
    hb, nh = hebrew_verses()
    if os.path.exists(OUT):
        os.remove(OUT)
    c = sqlite3.connect(OUT)
    c.executescript("""
CREATE TABLE Details (Title NVARCHAR(255), Description TEXT, Abbreviation NVARCHAR(50), Comments TEXT,
 Version TEXT, VersionDate DATETIME, PublishDate DATETIME, Publisher TEXT, Author TEXT, Creator TEXT,
 Source TEXT, EditorialComments TEXT, Language NVARCHAR(3), RightToLeft BOOL, OT BOOL, NT BOOL,
 Strong BOOL, VerseRules TEXT, CustomCSS TEXT);
CREATE TABLE Bible (Book INTEGER, Chapter INTEGER, Verse INTEGER, Scripture TEXT);
""")
    c.execute("insert into Details values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        "Berean Interlinear Bible (Hebrew & Greek)", DESC, "BIBhg", DESC, "1.0",
        "2026-10-12 00:00:00", "2026-10-12 00:00:00", "Bible Hub / ETCBC / OpenScriptures",
        "Bible Hub; ETCBC; OpenScriptures; Eliran Wong", "BibleBento Berean-remix",
        "https://github.com/EHenryRichard/refactor", None, "eng", 0, 1, 1, 1,
        "\n".join("%s\t%s" % r for r in RULES), CSS))
    rows = [(b, ch, v, t) for d in (hb, gk) for (b, ch, v), t in d.items()]
    rows.sort(key=lambda r: r[:3])
    c.executemany("insert into Bible values (?,?,?,?)", rows)
    c.execute("create index idx_bible on Bible(Book,Chapter,Verse)")
    c.commit(); c.execute("vacuum"); c.close()
    print("verses: hebrew %d (%d words), greek %d (%d words) -> %s (%.1f MB)"
          % (len(hb), nh, len(gk), ng, OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    build()
