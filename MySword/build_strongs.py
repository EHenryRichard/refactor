"""Build a MySword Strong's dictionary (Hebrew + Greek) for the BIBhg interlinear.

Input:
  source/strongs/strongs-hebrew-dictionary.js.zip   Strong's Hebrew, Open Scriptures JSON (CC-BY-SA)
  source/strongs/strongsgreek.xml.zip               Strong's Greek, Ulrik Petersen XML 1.4 (public domain)
  ../MyBible/dictionary/Berean_StrongNoDictionary.csv  Berean short Greek definitions (public domain)

Usage: python3 build_strongs.py [outfile]
"""
import json, os, re, sqlite3, sys, zipfile
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BIBhg-strongs.dct.mybible")
SRC = os.path.join(HERE, "source", "strongs")


def read_zip(name):
    z = zipfile.ZipFile(os.path.join(SRC, name))
    return z.read(z.namelist()[0]).decode("utf-8-sig")


def esc(s):
    return escape(re.sub(r"\s+", " ", s or "").strip(), quote=False)


def entry(lemma, xlit, pron, berean, derivation, definition, kjv):
    h = "<p><b>%s</b>" % esc(lemma)
    if xlit:
        h += " &nbsp;<i>%s</i>" % esc(xlit)
    if pron:
        h += " &nbsp;(%s)" % esc(pron)
    h += "</p>"
    for label, text in (("Berean", berean), ("Derivation", derivation), ("Strong's", definition), ("KJV", kjv)):
        if text and text.strip():
            h += "<p><b>%s:</b> %s</p>" % (label, esc(text))
    return h


def hebrew():
    t = read_zip("strongs-hebrew-dictionary.js.zip")
    d = json.loads(t[t.index("{"):t.rindex("}") + 1])
    for k, v in d.items():
        yield k, entry(v.get("lemma"), v.get("xlit"), v.get("pron"), None,
                       v.get("derivation"), v.get("strongs_def"), v.get("kjv_def"))


def greek():
    berean = {}
    with open(os.path.join(HERE, "..", "MyBible", "dictionary", "Berean_StrongNoDictionary.csv"), encoding="utf-8") as f:
        for line in f:
            k, _, v = line.rstrip("\n").partition("\t")
            berean[k] = v
    x = read_zip("strongsgreek.xml.zip")
    lemmas = {int(n): g for n, g in re.findall(r'<entry strongs="(\d+)">.*?<greek [^>]*unicode="([^"]*)"', x, re.S)}

    def text(body, tag):
        m = re.search(r"<%s>(.*?)</%s>" % (tag, tag), body, re.S)
        if not m:
            return ""
        s = re.sub(r'<strongsref language="GREEK" strongs="0*(\d+)"/>',
                   lambda r: "G%s (%s)" % (r.group(1), lemmas.get(int(r.group(1)), "")), m.group(1))
        s = re.sub(r'<strongsref language="HEBREW" strongs="0*(\d+)"/>', r"H\1", s)
        return re.sub(r"<[^>]+>", "", s)

    for n, body in re.findall(r'<entry strongs="(\d+)">(.*?)</entry>', x, re.S):
        k = "G%d" % int(n)
        if "<greek " not in body:
            continue  # numbers Strong left unassigned (G2717, G3203-G3302)
        g = re.search(r'<greek [^>]*unicode="([^"]*)"[^>]*translit="([^"]*)"', body)
        p = re.search(r'<pronunciation strongs="([^"]*)"', body)
        yield k, entry(g.group(1) if g else "", g.group(2) if g else "", p.group(1) if p else "",
                       berean.get(k), text(body, "strongs_derivation"), text(body, "strongs_def"),
                       text(body, "kjv_def").lstrip(":-"))


INFO = """<h2>Strong's Hebrew &amp; Greek Dictionary (BIBhg)</h2>
<p>Definitions for the Strong's numbers in the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg.</p>
<p>Hebrew: James Strong, A Concise Dictionary of the Words in the Hebrew Bible (1894, public domain);
e-text by David Instone-Brewer and David Troidl; JSON edition &copy; 2010 Open Scriptures, CC-BY-SA 3.0.
This dictionary module is therefore shared under CC-BY-SA.</p>
<p>Greek: James Strong, A Concise Dictionary of the Words in the Greek Testament (1890, public domain);
XML edition 1.4 by Ulrik Petersen (public domain). "Berean" lines: Berean Bible short definitions
(public domain). Not an official Berean product.</p>"""


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    c = sqlite3.connect(OUT)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "Strong's Hebrew & Greek Dictionary (BIBhg)", "BIBhgs", INFO, INFO, "James Strong", 1, "1.0",
        "2026-10-13 00:00:00", "2026-10-13 00:00:00", "b {color:Midnightblue;}", 0))
    rows = list(hebrew()) + list(greek())
    c.executemany("insert into Dictionary values (?,?)", rows)
    c.execute("create index idx_word on Dictionary (word)")
    c.commit()
    c.execute("vacuum")
    c.close()
    print("strong's dictionary: %d entries -> %s (%.1f MB)" % (len(rows), OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
