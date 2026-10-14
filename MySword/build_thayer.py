"""Build a MySword Strong's-keyed dictionary with Thayer's Greek and BDB Hebrew lexicons for the BIBhg interlinear.

Greek numbers (G1-G5624) open Thayer's Unabridged Greek-English Lexicon; Hebrew numbers (H1-H8674) open
Brown-Driver-Briggs, followed by the Strong's Hebrew entry, so every number tapped in BIBhg finds an entry.

Input:
  source/thayer/thayers_unabridged.lexi.zip   e-Sword lexicon from biblesupport.com (theWord module by Rob Sauers)
  source/bdb/HebrewLexicon.zip                 BDB and its Strong's index, Open Scriptures HebrewLexicon (CC BY 4.0)
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


OSIS = ("Gen Exod Lev Num Deut Josh Judg Ruth 1Sam 2Sam 1Kgs 2Kgs 1Chr 2Chr Ezra Neh Esth Job Ps Prov Eccl Song "
        "Isa Jer Lam Ezek Dan Hos Joel Amos Obad Jonah Mic Nah Hab Zeph Hag Zech Mal Matt Mark Luke John Acts Rom "
        "1Cor 2Cor Gal Eph Phil Col 1Thess 2Thess 1Tim 2Tim Titus Phlm Heb Jas 1Pet 2Pet 1John 2John 3John Jude "
        "Rev").split()
OSIS_NO = {b: i + 1 for i, b in enumerate(OSIS)}


def bdb_ref(m):
    r = re.fullmatch(r"(\w+)\.(\d+)\.(\d+)", m.group(1))
    if not r or r.group(1) not in OSIS_NO:
        return m.group(2)  # a few references in the source are malformed; keep the printed text
    return VERSE_LINK.format(b=OSIS_NO[r.group(1)], c=r.group(2), v=r.group(3), label=m.group(2))


def bdb_html(entry):
    e = re.sub(r"<status[^>]*>.*?</status>|<page[^>]*/>", "", entry, flags=re.S)
    e = re.sub(r"<entry[^>]*>|</entry>", "", e)
    e = re.sub(r'<ref r="([^"]*)"[^>]*>([^<]*)</ref>', bdb_ref, e)
    e = re.sub(r"<ref[^>]*>([^<]*)</ref>", r"\1", e)
    e = re.sub(r"<w[^>]*>", "<span class='hb'>", e).replace("</w>", "</span>")
    e = e.replace("<def>", "<span class='df'>").replace("</def>", "</span>")
    e = re.sub(r"</?(?:pos|foreign|em|asp)[^>]*>", lambda m: "</i>" if m.group(0).startswith("</") else "<i>", e)
    e = re.sub(r"<stem>(.*?)</stem>", r"<b class='st'>\1</b>", e)
    e = re.sub(r'<sense[^>]*\bn="([^"]*)"[^>]*>', r"<div class='sn'><b>\1.</b> ", e)
    e = re.sub(r"<sense[^>]*>", "<div class='sn'>", e).replace("</sense>", "</div>")
    return re.sub(r"\s+", " ", e).strip()


def read_bdb():
    # Strong's number -> BDB entries rendered as HTML, via the lexical index
    with zipfile.ZipFile(os.path.join(HERE, "source", "bdb", "HebrewLexicon.zip")) as z:
        bdb = z.read("BrownDriverBriggs.xml").decode("utf-8")
        index = z.read("LexicalIndex.xml").decode("utf-8")
    entries = {m.group(1): m.group(0) for m in re.finditer(r'<entry id="([^"]+)".*?</entry>', bdb, re.S)}
    out = {}
    for attrs in re.findall(r"<xref ([^>]*)/>", index):
        a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
        if a.get("strong", "").isdigit() and a.get("bdb") in entries:
            html = bdb_html(entries[a["bdb"]])
            out.setdefault("H%d" % int(a["strong"]), [])
            if html not in out["H%d" % int(a["strong"])]:
                out["H%d" % int(a["strong"])].append(html)
    return out


def hebrew_entries():
    bdb = read_bdb()
    for k, strongs in build_strongs.hebrew():
        h = "".join("<div class='bdb'>%s</div>" % b for b in bdb.get(k, []))  # div: senses are blocks
        if h:
            h = "<p class='hd'>BDB</p>" + h + "<hr><p class='hd'>Strong's</p>"
        yield k, h + strongs


INFO = """<h2>Thayer's Greek &amp; BDB Hebrew Lexicon (BIBhg)</h2>
<p>Strong's-numbered dictionary for the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg.</p>
<p>Greek: Joseph Henry Thayer, A Greek-English Lexicon of the New Testament (1889, public domain), unabridged;
e-text from the theWord module by Rob Sauers (e-Sword edition, biblesupport.com).</p>
<p>Hebrew: Brown, Driver, Briggs, A Hebrew and English Lexicon of the Old Testament (1906, public domain); abridged
e-text from the Open Scriptures Hebrew Lexicon (BrownDriverBriggs.xml, LexicalIndex.xml), CC BY 4.0.
Each Hebrew entry also gives Strong's Hebrew: James Strong, A Concise Dictionary of the Words in the Hebrew Bible (1894, public domain);
e-text by David Instone-Brewer and David Troidl; JSON edition &copy; 2010 Open Scriptures, CC-BY-SA 3.0.
This dictionary module is therefore shared under CC-BY-SA.</p>"""
CSS = ("span.gk {color:#6E9BCB;font-weight:600;} span.rd {color:#C98A7A;} "
       "span.hb {direction:rtl;unicode-bidi:isolate;font-size:115%;color:#6E9BCB;} span.df {color:#B8875E;} "
       "b.st {color:#9AA36E;} div.sn {margin-left:1em;} p.hd {color:#8F8F8F;font-size:85%;margin-bottom:0;} div.bdb {margin:0.5em 0;}")


def main():
    greek = [(k, convert(d)) for k, d in read_lexicon()]
    rows = list(hebrew_entries()) + greek
    if os.path.exists(OUT):
        os.remove(OUT)
    c = sqlite3.connect(OUT)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "Thayer's Greek & BDB Hebrew Lexicon (BIBhg)", "BIBhgt", INFO, INFO, "Thayer; Brown, Driver, Briggs", 1, "1.1",
        "2026-10-14 00:00:00", "2026-10-14 00:00:00", CSS, 0))
    c.executemany("insert into Dictionary values (?,?)", rows)
    c.execute("create index idx_word on Dictionary (word)")
    c.commit()
    c.execute("vacuum")
    c.close()
    print("thayer/bdb dictionary: %d greek + %d hebrew entries -> %s (%.1f MB)"
          % (len(greek), len(rows) - len(greek), OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
