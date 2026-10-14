"""Build a MySword Strong's-keyed dictionary with Thayer's Greek lexicon for the BIBhg interlinear.

Greek numbers (G1-G5624) open Thayer's Unabridged Greek-English Lexicon; Hebrew numbers (H1-H8674) open
Strong's Hebrew, so every number tapped in BIBhg finds an entry.

Input:
  source/thayer/thayers_unabridged.lexi.zip   e-Sword lexicon from biblesupport.com (theWord module by Rob Sauers)
  source/strongs/...                          Strong's Hebrew, as used by build_strongs.py
Output:
  BIBhg-thayer.dct.mybible

Usage: python3 build_thayer.py [outfile]
"""
import html, os, re, sqlite3, sys, tempfile, zipfile

import build_strongs

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BIBhg-thayer.dct.mybible")
VERSE_LINK = "<a href='#b{b}.{c}.{v}'>{label}</a>"  # same format as build_concordance.py

BOOKS = ("Gen Exo Lev Num Deu Jos Jdg Rth 1Sa 2Sa 1Ki 2Ki 1Ch 2Ch Ezr Neh Est Job Psa Pro Ecc Son Isa Jer Lam "
         "Eze Dan Hos Joe Amo Oba Jon Mic Nah Hab Zep Hag Zec Mal Mat Mar Luk Joh Act Rom 1Co 2Co Gal Eph Php "
         "Col 1Th 2Th 1Ti 2Ti Tit Phm Heb Jas 1Pe 2Pe 1Jn 2Jn 3Jn Jud Rev").split()
BOOK_NO = {b: i + 1 for i, b in enumerate(BOOKS)}  # Apocrypha (Wis, Sir, 1Ma ...) and the few broken ">Ki" refs stay plain text
LATIN_RUN = re.compile("[\u00c0-\u00ff]+")
HEB_CHAR = re.compile("[\u0590-\u05ff]")
LEGACY_RUN = re.compile("[\u00c0-\u00ff\u0370-\u03ff](?:[\u00c0-\u00ff\u0370-\u03ff ]*[\u00c0-\u00ff\u0370-\u03ff])?")


def read_lexicon():
    with zipfile.ZipFile(os.path.join(HERE, "source", "thayer", "thayers_unabridged.lexi.zip")) as z, \
            tempfile.TemporaryDirectory() as tmp:
        path = z.extract("thayers_unabridged.lexi", tmp)
        c = sqlite3.connect(path)
        rows = c.execute("select Topic, Definition from Lexicon").fetchall()
        c.close()
    return rows


def hebrew(run):
    # the module's Hebrew is Windows-1255 bytes shown as Latin-1 (or, in a few entries, as Greek Windows-1253)
    for cp in ("latin-1", "cp1253"):
        try:
            h = run.encode(cp).decode("cp1255")
        except UnicodeError:
            continue
        chars = h.replace(" ", "")
        if len(chars) >= 2 and len(HEB_CHAR.findall(h)) == len(chars):
            return "<span class='hb'>%s</span>" % h
    return run


def ref(m):
    label = m.group(1)
    r = re.fullmatch(r"(\w{3}) (\d+):(\d+)(?:-\d+)?", label)
    if not r or r.group(1) not in BOOK_NO:
        return label
    return VERSE_LINK.format(b=BOOK_NO[r.group(1)], c=r.group(2), v=r.group(3), label=label)


def convert(d):
    d = re.sub(r"</?(?:grk|heb)>", "", d)  # theWord font switches; they often split words
    d = re.sub(r"<span>(.*?)</span>", lambda m: LEGACY_RUN.sub(lambda r: hebrew(r.group(0)), html.unescape(m.group(1))), d)
    d = re.sub(r"<span style=\"\" lang=\"[^\"]*\">(.*?)</span>", r"\1", d)
    d = re.sub(r"<ref>([^<]*)</ref>", ref, d)
    d = d.replace("<blu>", "<span class='gk'>").replace("</blu>", "</span>")
    d = d.replace("<red>", "<span class='rd'>").replace("</red>", "</span>")
    # spell out the remaining entities as characters, but keep the markup characters escaped
    d = re.sub(r"&(?!(?:lt|gt|amp|quot);)#?\w+;", lambda m: html.unescape(m.group(0)), d)
    # a few Hebrew words sit outside those spans; only Latin-1 runs here, as the Greek is real Greek
    return re.sub(r"(?<=>)[^<]+", lambda m: LATIN_RUN.sub(lambda r: hebrew(r.group(0)), m.group(0)), d)


INFO = """<h2>Thayer's Greek Lexicon (BIBhg)</h2>
<p>Strong's-numbered dictionary for the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg.</p>
<p>Greek: Joseph Henry Thayer, A Greek-English Lexicon of the New Testament (1889, public domain), unabridged;
e-text from the theWord module by Rob Sauers (e-Sword edition, biblesupport.com).</p>
<p>Hebrew: James Strong, A Concise Dictionary of the Words in the Hebrew Bible (1894, public domain);
e-text by David Instone-Brewer and David Troidl; JSON edition &copy; 2010 Open Scriptures, CC-BY-SA 3.0.
This dictionary module is therefore shared under CC-BY-SA.</p>"""
CSS = "span.gk {color:Midnightblue;font-weight:bold;} span.rd {color:DarkRed;} span.hb {direction:rtl;unicode-bidi:isolate;font-size:115%;}"


def main():
    greek = [(k, convert(d)) for k, d in read_lexicon()]
    rows = list(build_strongs.hebrew()) + greek
    if os.path.exists(OUT):
        os.remove(OUT)
    c = sqlite3.connect(OUT)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "Thayer's Greek Lexicon (BIBhg)", "BIBhgt", INFO, INFO, "Joseph Henry Thayer", 1, "1.0",
        "2026-10-14 00:00:00", "2026-10-14 00:00:00", CSS, 0))
    c.executemany("insert into Dictionary values (?,?)", rows)
    c.execute("create index idx_word on Dictionary (word)")
    c.commit()
    c.execute("vacuum")
    c.close()
    print("thayer dictionary: %d greek + %d hebrew entries -> %s (%.1f MB)"
          % (len(greek), len(rows) - len(greek), OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
