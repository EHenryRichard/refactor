"""Build a MySword Strong's-tagged English Bible (BSB+) from Berean's BSB Translation Tables.

English in BSB reading order; each English word is followed by the Strong's number (<WH…>/<WG…>) and
morphology (<WT…>) of the Hebrew/Greek word it translates, so MySword can hide them and open BIBhgs/BIBhgm on tap.
Input: the same source/bsb_OT.tsv.zip and source/bsb_NT.tsv.zip as build_interlinear.py.

Usage: python3 build_bsb.py [outfile]
"""
import os, re, sqlite3, sys
from collections import defaultdict
from build_interlinear import (BOOK_NO, END_Q, BEG_Q, ENGLISH, MORPH, PNC, STR_GRK, STR_HEB, VERSE_ID,
                               VERSE_SEQ, clean, esc, read_rows)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BSBs.bbl.mybible")
BSB_SORT, HDG, FOOTNOTE, END_TEXT = 2, 13, 21, 22

# MySword/GBF markup: <TS>…<Ts> heading, <RF>…<Rf> footnote, <FI>…<Fi> italic (words the translators supplied).
def supplied(s):
    return re.sub(r"\[([^\]]*)\]", r"<FI>\1<Fi>", s)


def italics(s):
    # footnote <i>…</i> -> <FI>…<Fi>; a few Berean footnotes have a stray </i> or <i>, which are dropped
    out, open_ = [], False
    for part in re.split(r"(</?i>)", s):
        if part == "<i>":
            if not open_:
                out.append("<FI>"); open_ = True
        elif part == "</i>":
            if open_:
                out.append("<Fi>"); open_ = False
        else:
            out.append(part)
    return "".join(out) + ("<Fi>" if open_ else "")


def build_testament(rows, greek):
    strong_col, wtag = (STR_GRK, "WG") if greek else (STR_HEB, "WH")
    refs, verses = {}, defaultdict(list)
    for r in rows:
        seq = int(r[VERSE_SEQ])
        if r[VERSE_ID].strip():
            refs[seq] = r[VERSE_ID].strip()
        verses[seq].append(r)
    out, ntags = {}, 0
    for seq, rs in verses.items():
        if seq not in refs:
            continue  # padding only
        m = re.fullmatch(r"(.+) (\d+):(\d+)", refs[seq])
        key = (BOOK_NO[m.group(1)], int(m.group(2)), int(m.group(3)))
        parts = []
        for r in sorted(rs, key=lambda r: float(r[BSB_SORT])):
            for h in re.findall(r"<p class=\|(?:sub)?hdg\|>(.*?)(?=<p |$)", r[HDG]):
                if clean(h):
                    parts.append("<TS>%s<Ts>" % esc(clean(h)))
            eng = clean(r[ENGLISH])
            if eng in ("vvv", "-"):
                eng = ""
            eng = re.sub(r"\bvvv\b", "", eng).strip()
            text = clean(r[BEG_Q].strip() + eng + r[PNC].strip() + r[END_Q].strip() + r[END_TEXT].strip())
            tags = ""
            sn = clean(r[strong_col])
            if sn.isdigit():
                tags += "<%s%s>" % (wtag, sn)
                ntags += 1
                mp = re.sub(r"\s*\|\s*", "+", clean(r[MORPH])).replace(" ", "")
                if mp:
                    tags += "<WT%s>" % esc(mp)
            if text:
                parts.append(supplied(esc(text)) + tags)
            elif tags and parts:
                parts[-1] += tags  # untranslated word: tag the preceding English
            elif tags:
                parts.append(tags)
            fn = re.sub(r"\s+", " ", re.sub(r"<(?!/?i>)[^>]+>", "", r[FOOTNOTE])).strip()
            if fn:
                parts[-1] += "<RF>%s<Rf>" % italics(fn)
        if not parts:
            continue  # verse the BSB omits (e.g. Matthew 17:21)
        out[key] = re.sub(r"\s+([,.;:!?’”)])", r"\1", " ".join(parts))
    return out, ntags


DESC = """<h2>BSB+ &mdash; Berean Standard Bible with Strong's numbers</h2>
<p>The Berean Standard Bible in normal English reading order. Each English word carries the Strong's number and
parsing of the Hebrew/Greek word it translates: turn Strong's/morphology display off in MySword to read plain
text, and tap a word to open it in BIBhgs (Strong's) or BIBhgm (morphology).</p>
<p>Source: BSB Translation Tables, berean.bible. The Holy Bible, Berean Standard Bible, BSB is produced in
cooperation with Bible Hub, Discovery Bible, OpenBible.com, and the Berean Bible Translation Committee. This text
of God's Word has been dedicated to the public domain. Not an official Berean product.</p>"""


def main():
    ot, nh = build_testament(read_rows("bsb_OT.tsv.zip"), greek=False)
    nt, ng = build_testament(read_rows("bsb_NT.tsv.zip"), greek=True)
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
        "BSB+ (Strong's-tagged Berean Standard Bible)", DESC, "BSBs", DESC, "1.0",
        "2026-10-13 00:00:00", "2026-10-13 00:00:00", "Independent adaptation (not an official Berean product)",
        "Berean Bible Translation Committee (source data)", "build_bsb.py",
        "https://berean.bible", None, "eng", 0, 1, 1, 1, None, None))
    rows = sorted((b, ch, v, t) for d in (ot, nt) for (b, ch, v), t in d.items())
    c.executemany("insert into Bible values (?,?,?,?)", rows)
    c.execute("create index idx_bible on Bible(Book,Chapter,Verse)")
    c.commit(); c.execute("vacuum"); c.close()
    print("BSB+: %d verses, %d Hebrew + %d Greek Strong's tags -> %s (%.1f MB)"
          % (len(rows), nh, ng, OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
