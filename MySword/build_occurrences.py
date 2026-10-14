"""Build a MySword word-occurrence dictionary for the BIBhg interlinear, like Bible Hub's Englishman's Concordance.

For each Strong's number: how often it occurs, the BSB English renderings with their counts, the Hebrew/Greek forms,
then every verse where it occurs (Bible order) with the form used there, its parsing and its BSB English.
Input: the same Berean tables as build_interlinear.py.

Usage: python3 build_occurrences.py [outfile]
"""
import os, re, sqlite3, sys, unicodedata
from collections import Counter, defaultdict

from build_concordance import SHORT, VERSE_LINK
from build_interlinear import (BOOK_NO, GRK_SORT, HEB_SORT, MORPH, STR_GRK, STR_HEB, TEXT, VERSE_ID, VERSE_SEQ,
                               clean, english, esc, read_rows)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "BIBhg-occurrences.dct.mybible")


def occurrences(rows, greek):
    # Strong's key -> [(book, chapter, verse, form, parsing, BSB English)] in Bible and word order
    sort_col, strong_col, prefix = (GRK_SORT, STR_GRK, "G") if greek else (HEB_SORT, STR_HEB, "H")
    refs, words = {}, defaultdict(list)
    for r in rows:
        seq = int(r[VERSE_SEQ])
        if r[VERSE_ID].strip():
            refs[seq] = r[VERSE_ID].strip()
        sn, form = clean(r[strong_col]), unicodedata.normalize("NFC", clean(r[TEXT]))  # one spelling per form
        if sn.isdigit() and form:
            words[seq].append((float(r[sort_col]), sn, form, r))
    out = defaultdict(list)
    for seq in sorted(words):
        m = re.fullmatch(r"(.+) (\d+):(\d+)", refs[seq])
        b, c, v = BOOK_NO[m.group(1)], int(m.group(2)), int(m.group(3))
        for _, sn, form, r in sorted(words[seq], key=lambda w: w[0]):
            mp = re.sub(r"\s*\|\s*", "+", clean(r[MORPH])).replace(" ", "")
            out["%s%d" % (prefix, int(sn))].append((b, c, v, form, mp, english(r) or "-"))
    return out


def rendering(eng):
    # the English without the verse's punctuation and quote marks, for counting ("world.”" -> "world")
    e = re.sub(r"[.,;:!?\u2014\u2018\u2019\u201c\u201d\"()]", "", eng)
    e = re.sub(r"\s+", " ", e).strip().lower()
    return e or "-"


def counted(counter):
    return ", ".join("%s (%d)" % (esc(w), n) for w, n in counter.most_common())


def render(key, occ, hebrew):
    verses = len({(b, c, v) for b, c, v, *_ in occ})
    renderings = Counter(rendering(e) for *_, e in occ)
    forms = Counter(f for _, _, _, f, _, _ in occ)
    form_span = "<span class='hb'>%s</span>" if hebrew else "<span class='gk'>%s</span>"
    h = ["<p><b>%s</b>: %d occurrence%s in %d verse%s</p>" % (key, len(occ), "" if len(occ) == 1 else "s",
                                                              verses, "" if verses == 1 else "s"),
         "<p><b>BSB English:</b> %s</p>" % counted(renderings),
         "<p><b>Forms:</b> %s</p>" % ", ".join(form_span % "%s (%d)" % (esc(f), n) for f, n in forms.most_common()),
         "<hr><p>"]
    for b, c, v, form, mp, eng in occ:
        h.append("%s %s <i>%s</i> &ndash; %s<br>" % (
            VERSE_LINK.format(b=b, c=c, v=v, label="%s %d:%d" % (SHORT[b - 1], c, v)),
            form_span % esc(form), esc(mp), esc(eng)))
    h.append("</p>")
    return "".join(h)


INFO = """<h2>Word Occurrences (BIBhg)</h2>
<p>Every place each Strong's number occurs in the Hebrew &amp; Greek Interlinear (BSB Tables), BIBhg, like an
Englishman's concordance: number of occurrences, the BSB English renderings and Hebrew/Greek forms with their counts,
then each verse with the form, parsing and BSB English used there.</p>
<p>Source: BSB Translation Tables, berean.bible (public domain). Not an official Berean product.</p>"""
CSS = ("span.gk {color:#6E9BCB;font-weight:600;} span.hb {color:#6E9BCB;font-weight:600;direction:rtl;"
       "unicode-bidi:isolate;} i {color:#9AA36E;font-size:85%;}")


def main():
    data = {}
    data.update(occurrences(read_rows("bsb_OT.tsv.zip"), greek=False))
    data.update(occurrences(read_rows("bsb_NT.tsv.zip"), greek=True))
    if os.path.exists(OUT):
        os.remove(OUT)
    c = sqlite3.connect(OUT)
    c.executescript("""
CREATE TABLE details (title TEXT, abbreviation TEXT, description TEXT, comments TEXT, author TEXT, strong INTEGER,
 version TEXT, versiondate DATETIME, publishdate TEXT, CustomCSS TEXT, morphology BOOL);
CREATE TABLE Dictionary (word, data);
""")
    c.execute("insert into details values (?,?,?,?,?,?,?,?,?,?,?)", (
        "Word Occurrences (BIBhg)", "BIBhgo", INFO, INFO, "Berean Bible Translation Committee (source data)", 1,
        "1.0", "2026-10-14 00:00:00", "2026-10-14 00:00:00", CSS, 0))
    c.executemany("insert into Dictionary values (?,?)",
                  ((k, render(k, occ, k.startswith("H"))) for k, occ in sorted(data.items())))
    c.execute("create index idx_word on Dictionary (word)")
    c.commit()
    c.execute("vacuum")
    c.close()
    print("occurrences: %d Strong's numbers, %d occurrences -> %s (%.1f MB)"
          % (len(data), sum(len(o) for o in data.values()), OUT, os.path.getsize(OUT) / 1e6))


if __name__ == "__main__":
    main()
