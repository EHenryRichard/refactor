#!/usr/bin/env python3
"""Build a MySword interlinear Bible module (Hebrew OT + Greek NT) from Berean's BSB Translation Tables.

Input  (Berean "BSB Translation Tables", tsv):
  source/bsb_OT.tsv.zip   Genesis-Malachi
  source/bsb_NT.tsv.zip   Matthew-Revelation
Input  (STEPBible TAHOT/TAGNT, CC BY 4.0): literal word glosses
  source/stepbible/*.txt.zip
Output:
  BIBhg.bbl.mybible   (SQLite; copy into MySword's modules folder)

Usage: python3 build_interlinear.py [outfile]
"""
import csv, difflib, io, os, re, sqlite3, sys, unicodedata, zipfile
from collections import Counter, OrderedDict, defaultdict
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BIBhg.bbl.mybible")
csv.field_size_limit(10**9)

# column positions in the Berean tables
HEB_SORT, GRK_SORT, VERSE_SEQ, LANG, TEXT, TRANSLIT, MORPH = 0, 1, 3, 4, 5, 7, 8
STR_HEB, STR_GRK, VERSE_ID, BEG_Q, ENGLISH, PNC, END_Q = 10, 11, 12, 17, 18, 19, 20

BOOK_LIST = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel",
    "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job",
    "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel",
    "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai",
    "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians",
    "2 Corinthians", "Galatians", "Ephesians", "Philippians", "Colossians", "1 Thessalonians",
    "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", "2 Peter",
    "1 John", "2 John", "3 John", "Jude", "Revelation"]
BOOK_NO = {n: i + 1 for i, n in enumerate(BOOK_LIST)}

TAG = re.compile(r"<[^>]+>")


def esc(s):
    # module markup uses <...>, so literal text must not contain raw angle brackets
    return escape(s, quote=False)


def read_rows(zipname):
    z = zipfile.ZipFile(os.path.join(HERE, "source", zipname))
    name = next(n for n in z.namelist() if n.endswith(".tsv") and "__MACOSX" not in n)
    rd = csv.reader(io.TextIOWrapper(z.open(name), encoding="utf-8", newline=""),
                    delimiter="\t", quoting=csv.QUOTE_NONE)
    next(rd)
    return [r + [""] * (23 - len(r)) for r in rd]


def clean(s):
    s = re.sub(r"<span class=\|reftext\|>.*?</span>", "", s)  # Berean's in-text verse labels (e.g. Psalm 23 "1")
    return re.sub(r"\s+", " ", TAG.sub("", s)).strip()


def english(r):
    # BSB word, with the BSB punctuation and quote marks that belong to it.
    # "vvv" is Berean's placeholder for a word whose sense is carried by a neighbouring word.
    e = clean(r[ENGLISH])
    if not e:
        return ""
    e = re.sub(r"\bvvv\b", "-", e)
    return clean(r[BEG_Q].strip() + e + r[PNC].strip() + r[END_Q].strip())


STEP_FILES = ["TAHOT_Gen-Deu", "TAHOT_Jos-Est", "TAHOT_Job-Sng", "TAHOT_Isa-Mal", "TAGNT_Mat-Jhn", "TAGNT_Act-Rev"]
STEP_ROW = re.compile(r"([1-3]?[A-Z][a-z]+)\.(\d+)\.(\d+)[^#\t]*#\d+=")


def skeleton(word, greek):
    # spelling used to match a STEPBible word to a Berean word: letters only, no vowels or accents
    if greek:
        w = "".join(ch for ch in unicodedata.normalize("NFD", word) if "\u03b1" <= ch.lower() <= "\u03c9")
        return w.lower().replace("\u03c2", "\u03c3")
    return "".join(ch for ch in word if "\u05d0" <= ch <= "\u05ea")


def read_literal():
    # (book, chapter, verse) -> [(skeleton, literal English)], in Hebrew/Greek word order, English verse numbering
    out, books = defaultdict(list), []
    for name in STEP_FILES:
        greek = name.startswith("TAGNT")
        z = zipfile.ZipFile(os.path.join(HERE, "source", "stepbible", name + ".txt.zip"))
        for line in io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8-sig"):
            m = STEP_ROW.match(line)
            if not m:
                continue
            if m.group(1) not in books:
                books.append(m.group(1))
            f = line.rstrip("\n").split("\t")
            word = f[1].split(" (")[0] if greek else f[1]
            gloss = re.sub(r"\{[^}]*\}", "", f[2] if greek else f[3]).replace("/", " ").replace("<", "[").replace(">", "]")
            gloss = re.sub(r"\s+", " ", gloss).strip()
            # Psalm titles are verse 0 in STEPBible but part of verse 1 in the Berean tables
            out[(len(books), int(m.group(2)), max(int(m.group(3)), 1))].append((skeleton(word, greek), gloss))
    assert len(books) == 66, books
    return out


def match_literal(words, step, greek):
    # pair each Berean word with the STEPBible word of the same spelling, in order; same-length gaps pair up in turn
    ours = [skeleton(text, greek) for text in words]
    theirs = [w for w, _ in step]
    found = {}
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ours, theirs, autojunk=False).get_opcodes():
        if op == "equal" or (op == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                found[i1 + k] = step[j1 + k][1]
    return found


MORPH_DESC = defaultdict(Counter)  # <WT> code -> {Berean's plain-English parsing: count}, for the morphology dictionary


LITERAL_STATS = Counter()


def build_testament(rows, greek, literal):
    sort_col, strong_col, wtag, cls = (GRK_SORT, STR_GRK, "WG", "Xg") if greek else (HEB_SORT, STR_HEB, "WH", "Xh")
    refs, words = {}, defaultdict(list)
    for r in rows:
        seq = int(r[VERSE_SEQ])
        if r[VERSE_ID].strip():
            refs[seq] = r[VERSE_ID].strip()
        eng = english(r)
        text = clean(r[TEXT])
        if not text and not eng:
            continue  # padding row, or a stray morphology fragment with no word
        words[seq].append((float(r[sort_col]), r, text, eng))
    out, nwords = OrderedDict(), 0
    for seq in sorted(words):
        m = re.fullmatch(r"(.+) (\d+):(\d+)", refs[seq])
        key = (BOOK_NO[m.group(1)], int(m.group(2)), int(m.group(3)))
        parts = []
        ordered = sorted(words[seq], key=lambda w: w[0])
        texts = [text for _, _, text, _ in ordered]
        lit = match_literal(texts, literal.get(key, []), greek)
        if len(lit) < len(texts):
            # the two sources sometimes split verses differently (e.g. 2 Corinthians 13:12-14); look next door too
            b, ch, v = key
            near = literal.get((b, ch, v - 1), []) + literal.get(key, []) + literal.get((b, ch, v + 1), [])
            wider = match_literal(texts, near, greek)
            if len(wider) > len(lit):
                lit = wider
        LITERAL_STATS["words"] += len(ordered)
        LITERAL_STATS["matched"] += len(lit)
        for i, (_, r, text, eng) in enumerate(ordered):
            lt = esc(lit[i]) if i in lit else "&nbsp;"  # keeps the rows lined up when a word has no gloss
            tl = clean(r[TRANSLIT])
            sn = clean(r[strong_col])
            sn = "<%s%s>" % (wtag, sn) if sn.isdigit() else ""
            mp = re.sub(r"\s*\|\s*", "+", clean(r[MORPH])).replace(" ", "")
            if mp:
                desc = [d.strip() for d in clean(r[MORPH + 1]).split("|") if d.strip()]
                if desc:
                    MORPH_DESC[mp]["|".join(desc)] += 1
                mp = "<WT%s>" % esc(mp)
            if greek:
                # one small table per word: every part gets its own row, whatever MySword does to the text inside
                w = "【<Xg>%s</Xg><Xu>%s</Xu>%s<Xm>%s<Xk>%s</Xk><Xf>%s</Xf>】" % (
                    esc(text), esc(tl), sn, mp, lt, esc(eng or "-"))
            else:
                w = "「"
                if text:
                    w += "<%s>%s</%s>" % (cls, esc(text), cls)
                if tl:
                    w += "<Xt>%s</Xt>" % esc(tl)
                w += "%s%s<Xl>%s</Xl><Xe>%s</Xe>」" % (sn, mp, lt, esc(eng or "-"))
            parts.append(w)
            nwords += 1
        body = " ".join(parts)
        out[key] = ("<Xn>%s</Xn>" if greek else "<Xr>%s</Xr>") % body
    return out, nwords


RULES = [
    ("「", "<span class='w'>"),
    ("」", "</span>"),
    ("<Xr>(.*?)</Xr>", "<div class='hbv'>$1</div>"),
    ("<Xn>(.*?)</Xn>", "<div class='gkv'>$1</div>"),
    ("<Xh>(.*?)</Xh>", "<span class='hb'>$1</span>"),
    # Greek word box: a table with one row per part (Greek, transliteration, Strong's, parsing, English)
    ("【", "<table class='gw'><tr><td class='gk'>"),
    ("<Xg>(.*?)</Xg>", "$1</td></tr><tr><td class='tl'>"),
    ("<Xu>(.*?)</Xu>", "$1</td></tr><tr><td class='ln'>"),
    ("<Xm>", "</td></tr><tr><td class='ln'>"),
    ("<Xk>(.*?)</Xk>", "</td></tr><tr><td class='lt'>$1"),
    ("<Xf>(.*?)</Xf>", "</td></tr><tr><td class='en'>$1"),
    ("】", "</td></tr></table>"),
    ("<Xt>(.*?)</Xt>", "<span class='tl'>$1</span>"),
    ("<Xl>(.*?)</Xl>", "<span class='lt'>$1</span>"),
    ("<Xe>(.*?)</Xe>", "<span class='en'>$1</span>"),
]
CSS = """/* each part is its own block inside the word box; MySword drops <br> in verse text */
span.w {display:inline-block;text-align:center;vertical-align:top;margin:0 6px 10px 6px;}
span.hb {display:block;font-size:150%;color:Midnightblue;font-weight:bold;direction:rtl;}
span.tl {display:block;direction:ltr;unicode-bidi:isolate;font-size:75%;color:Gray;font-style:italic;}
span.lt {display:block;direction:ltr;unicode-bidi:isolate;font-size:80%;color:DarkCyan;}
span.en {display:block;direction:ltr;unicode-bidi:isolate;font-size:85%;color:IndianRed;font-weight:bold;}
div.hbv {direction:rtl;text-align:right;}
div.gkv {direction:ltr;text-align:left;}
span.w a {display:block;font-size:70%;line-height:1.25;}
table.gw {display:inline-table;border-collapse:collapse;vertical-align:top;margin:0 6px 10px 6px;}
table.gw td {text-align:center;padding:0;}
td.gk {font-size:135%;color:Midnightblue;font-weight:bold;}
td.tl {font-size:75%;color:Gray;font-style:italic;}
td.ln {font-size:70%;line-height:1.25;}
td.lt {font-size:80%;color:DarkCyan;}
td.en {font-size:85%;color:IndianRed;font-weight:bold;}"""

DESC = """<h2>Hebrew &amp; Greek Interlinear (BSB Tables)</h2>
<p>Every word of the Old Testament (Hebrew/Aramaic) and New Testament (Greek) with transliteration,
Strong's number, morphology and the Berean Standard Bible English for that word ("-" where the Berean
text has no English counterpart). Tap a Strong's number or morphology code for the lookup.</p>
<p>Source: BSB Translation Tables, berean.bible. This is an independent adaptation, not an official Berean
product: words are in Hebrew/Greek order and the "vvv" placeholder is shown as "-".</p>
<p>The Holy Bible, Berean Standard Bible, BSB is produced in cooperation with Bible Hub, Discovery Bible,
OpenBible.com, and the Berean Bible Translation Committee. This text of God's Word has been dedicated to the
public domain.</p>
<p>Literal word glosses (teal line): STEPBible.org, Translators Amalgamated Hebrew OT (TAHOT) and Greek NT (TAGNT),
CC BY 4.0, Tyndale House Cambridge. Matched to the Berean words by spelling.</p>
<p>Verse numbering is KJV-style (31,102 verses). Verses the Berean text omits (e.g. Matthew 17:21) are empty.</p>"""


def build_morphology_dictionary(path):
    if os.path.exists(path):
        os.remove(path)
    c = sqlite3.connect(path)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    info = ("Parsing codes for the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg. "
            "Descriptions are from the BSB Translation Tables, berean.bible. Not an official Berean product.")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "Interlinear Morphology Codes (BSB Tables)", "BIBhgm", info, info, "Berean Bible Translation Committee (source data)", 0, "2.0",
        "2026-10-13 00:00:00", "2026-10-13 00:00:00", "b {color:Midnightblue;}", 1))
    # a few codes carry different descriptions on different rows in Berean's tables; keep the most common
    disputed = sum(1 for v in MORPH_DESC.values() if len(v) > 1)
    entries = []
    for code, v in sorted(MORPH_DESC.items()):
        desc = v.most_common(1)[0][0].split("|")
        entries.append((code, "<b>%s</b><br>%s" % (esc(code), "<br>".join(esc(d) for d in desc))))
    c.executemany("insert into Dictionary values (?,?)", entries)
    c.execute("create index idx_dict on Dictionary(word)")
    c.commit(); c.execute("vacuum"); c.close()
    print("morphology dictionary: %d codes (%d with conflicting descriptions in the source) -> %s (%.1f KB)"
          % (len(MORPH_DESC), disputed, path, os.path.getsize(path) / 1e3))


def build():
    literal = read_literal()
    hb, nh = build_testament(read_rows("bsb_OT.tsv.zip"), greek=False, literal=literal)
    gk, ng = build_testament(read_rows("bsb_NT.tsv.zip"), greek=True, literal=literal)
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
        "Hebrew & Greek Interlinear (BSB Tables)", DESC, "BIBhg", DESC, "2.0",
        "2026-10-13 00:00:00", "2026-10-13 00:00:00", "Independent adaptation (not an official Berean product)",
        "Berean Bible Translation Committee (source data)", "build_interlinear.py",
        "https://berean.bible", None, "eng", 0, 1, 1, 1,
        "\n".join("%s\t%s" % r for r in RULES), CSS))
    rows = [(b, ch, v, t) for d in (hb, gk) for (b, ch, v), t in d.items()]
    rows.sort(key=lambda r: r[:3])
    c.executemany("insert into Bible values (?,?,?,?)", rows)
    c.execute("create index idx_bible on Bible(Book,Chapter,Verse)")
    c.commit(); c.execute("vacuum"); c.close()
    build_morphology_dictionary(os.path.join(os.path.dirname(OUT), "BIBhg-morph.dct.mybible"))
    print("literal glosses: %d of %d words" % (LITERAL_STATS["matched"], LITERAL_STATS["words"]))
    print("verses: hebrew %d (%d words), greek %d (%d words) -> %s (%.1f MB)"
          % (len(hb), nh, len(gk), ng, OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    build()
