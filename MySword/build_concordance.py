"""Build a MySword English concordance (dictionary module) from Berean's BSB Concordance.

Input:
  source/concordance/bsb_concordance.tsv.zip
    Berean "BSB Concordance - xlsx" (bsb_concordance.xlsx, 52,051,537 bytes,
    SHA-256 01a888e221cdfb652b19e2791e82b5a7141beb703d54661b8819ff49d89580d3), saved as tab-separated text:
    columns A-I of Sheet1 (Sort, Book, Chap, Word, Occ, Total, Entry, Verse, Context), title and header rows dropped.
    Re-create it from a new xlsx with:  python3 build_concordance.py --from-xlsx bsb_concordance.xlsx

Usage: python3 build_concordance.py [outfile]
"""
import csv, io, os, re, sqlite3, sys, zipfile
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "source", "concordance", "bsb_concordance.tsv.zip")
OUT = os.path.join(HERE, "BIBhg-concordance.dct.mybible")

# MySword verse link inside dictionary HTML. NOT YET VERIFIED ON A PHONE: if tapping a reference does nothing,
# this is the one line to change. Fields: b = book number (1-66), c = chapter, v = verse.
VERSE_LINK = "<a href='#b{b}.{c}.{v}'>{label}</a>"

ABBR = ("Gen Exo Lev Num Deu Jos Jdg Rut 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Sos Isa Jer Lam Eze "
        "Dan Hos Joe Amo Oba Jon Mic Nah Hab Zep Hag Zec Mal Mat Mar Luk Joh Act Rom 1Co 2Co Gal Eph Php Col 1Th "
        "2Th 1Ti 2Ti Tts Phm Heb Jam 1Pe 2Pe 1Jo 2Jo 3Jo Jde Rev").split()
NAMES = ("Genesis Exodus Leviticus Numbers Deuteronomy Joshua Judges Ruth 1_Samuel 2_Samuel 1_Kings 2_Kings "
         "1_Chronicles 2_Chronicles Ezra Nehemiah Esther Job Psalms Proverbs Ecclesiastes Song_of_Solomon Isaiah "
         "Jeremiah Lamentations Ezekiel Daniel Hosea Joel Amos Obadiah Jonah Micah Nahum Habakkuk Zephaniah Haggai "
         "Zechariah Malachi Matthew Mark Luke John Acts Romans 1_Corinthians 2_Corinthians Galatians Ephesians "
         "Philippians Colossians 1_Thessalonians 2_Thessalonians 1_Timothy 2_Timothy Titus Philemon Hebrews James "
         "1_Peter 2_Peter 1_John 2_John 3_John Jude Revelation").split()
SHORT = ("Gen Ex Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song Isa "
         "Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke John Acts Rom 1Cor "
         "2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude "
         "Rev").split()
BOOK = {k.lower(): i + 1 for i, k in enumerate(ABBR)}
BOOK.update({k.lower(): i + 1 for i, k in enumerate(NAMES)})
BOOK.update({"1 joh": 62, "2 joh": 63, "3 joh": 64, "psalm": 19})  # 1-3 John appear as "1 Joh 1:10"


def ref(v):
    # "Gen 32:15", "1 Joh 1:10", "Lev_26:5", "1_Corinthians_11:18"
    m = re.fullmatch(r"(.+?)[ _](\d+):(\d+)", v.strip())
    b = BOOK.get(m.group(1).lower()) or BOOK.get(m.group(1).replace(" ", "_").lower())
    if not b:
        raise ValueError("unknown book in %r" % v)
    return b, int(m.group(2)), int(m.group(3))


def from_xlsx(path):
    import openpyxl
    out = os.path.join(os.path.dirname(SRC), "bsb_concordance.tsv")
    ws = openpyxl.load_workbook(path, read_only=True).worksheets[0]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        for i, r in enumerate(ws.iter_rows(values_only=True)):
            if i >= 2:
                w.writerow(["" if c is None else str(c) for c in r[:9]])
    print("wrote", out, "- zip it as", SRC)


def read_entries():
    z = zipfile.ZipFile(SRC)
    rd = csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding="utf-8"), delimiter="\t",
                    quoting=csv.QUOTE_NONE)
    entry = None
    for r in rd:
        if r[6]:
            if entry:
                yield entry
            m = re.fullmatch(r"(.+) \((\d+) Occurrences?\)", r[6])
            entry = [m.group(1), int(m.group(2)), []]
        else:
            entry[2].append((int(r[0]), ref(r[7]), r[8]))
    if entry:
        yield entry


def render(word, total, occ):
    h = ["<p><b>%s</b> &mdash; %d occurrence%s</p>" % (escape(word), total, "" if total == 1 else "s")]
    book = None
    for _, (b, c, v), ctx in sorted(occ):
        if b != book:
            if book:
                h.append("</p>")
            h.append("<p><b>%s</b><br>" % NAMES[b - 1].replace("_", " "))
            book = b
        label = "%s %d:%d" % (SHORT[b - 1], c, v)
        h.append("%s %s<br>" % (VERSE_LINK.format(b=b, c=c, v=v, label=label), escape(ctx)))
    h.append("</p>")
    return "".join(h)


INFO = """<h2>BSB English Concordance (BIBhgc)</h2>
<p>Every English word of the Berean Standard Bible with every verse it occurs in and a short context line.
Companion to the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg.</p>
<p>Source: BSB Concordance, berean.bible (Study Tools, 2nd printing). The Holy Bible, Berean Standard Bible, BSB is
produced in cooperation with Bible Hub, Discovery Bible, OpenBible.com, and the Berean Bible Translation Committee.
This text of God's Word has been dedicated to the public domain. Not an official Berean product.</p>"""


def main(out):
    rows, refs = [], 0
    for word, total, occ in read_entries():
        if len(occ) != total:
            raise ValueError("%s: header says %d, found %d" % (word, total, len(occ)))
        rows.append((word, render(word, total, occ)))
        refs += total
    if os.path.exists(out):
        os.remove(out)
    c = sqlite3.connect(out)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "BSB English Concordance (BIBhgc)", "BIBhgc", INFO, INFO, "Berean Bible Translation Committee (source data)",
        0, "1.0", "2026-10-13 00:00:00", "2026-10-13 00:00:00", "b {color:Midnightblue;}", 0))
    c.executemany("insert into Dictionary values (?,?)", rows)
    c.execute("create index idx_word on Dictionary (word)")
    c.commit()
    c.execute("vacuum")
    c.close()
    print("concordance: %d words, %d occurrences -> %s (%.1f MB)" % (len(rows), refs, out, os.path.getsize(out) / 1e6))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--from-xlsx"]:
        from_xlsx(sys.argv[2])
    else:
        main(sys.argv[1] if len(sys.argv) > 1 else OUT)
