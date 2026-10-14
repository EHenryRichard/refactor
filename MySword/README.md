# Hebrew & Greek Interlinear (BSB Tables) for MySword

**Files to download:**

* [`BIBhg.bbl.mybible`](BIBhg.bbl.mybible) — the interlinear Bible, all 66 books.
* [`BIBhg-morph.dct.mybible`](BIBhg-morph.dct.mybible) — morphology dictionary (3,818 codes, Berean's own descriptions, each followed by a plain-English explanation of every part: tense, voice, mood, case, Hebrew stem, prefixes, pronoun suffixes). Needed for the parsing popups. Codes with "+" are also filed with a space, because MySword looks them up that way.
* [`BIBhg-strongs.dct.mybible`](BIBhg-strongs.dct.mybible) — Strong's Hebrew & Greek dictionary (BIBhgs) for the
  Strong's number popups. Covers every Strong's number used in the Bible. Rebuild with `build_strongs.py`.
* [`BIBhg-thayer.dct.mybible`](BIBhg-thayer.dct.mybible) — **Thayer's Greek & BDB Hebrew Lexicon** (BIBhgt): Thayer's
  unabridged for Greek Strong's numbers; Brown-Driver-Briggs (then Strong's) for Hebrew numbers. In a Strong's popup, switch the dictionary to
  BIBhgt. Rebuild with `build_thayer.py`.
* [`BSBs.bbl.mybible`](BSBs.bbl.mybible) — **BSB+**: the Berean Standard Bible in normal English reading order,
  each word tagged with its Strong's number and parsing (hidden or shown with MySword's Strong's/morphology toggles;
  tap a word to open BIBhgs/BIBhgm). Includes BSB headings, footnotes and supplied words in italics.
  Rebuild with `build_bsb.py`.
* [`BIBhg-concordance.dct.mybible`](BIBhg-concordance.dct.mybible) — BSB English concordance (BIBhgc): every
  English word, every verse it occurs in, with a short context line. Rebuild with `build_concordance.py`.

Built only from Berean's own **BSB Translation Tables** (bereanbible.com):

* Old Testament: every Hebrew/Aramaic word, with transliteration, Strong's number (`H…`), morphology, and the
  Berean Standard Bible English for that word.
* New Testament: every Greek word, with transliteration, Strong's number (`G…`), morphology, and the Berean
  Standard Bible English for that word.
* A literal English gloss for each word (teal line, above the BSB English) from STEPBible's Translators Amalgamated
  Hebrew OT and Greek NT (TAHOT/TAGNT, CC BY 4.0, STEPBible.org / Tyndale House Cambridge), matched to the Berean
  words by spelling (443,403 of 443,626 words). Sources in `source/stepbible/` (STEPBible-Data commit 93ec362).
* Words with no English counterpart of their own (e.g. the Hebrew object marker) show "-", as in Berean's tables.
* Verse numbering is KJV-style (31,102 verses). Verses the Berean text leaves out (e.g. Matthew 17:21) are empty.
  Nehemiah 7:68 has English only, as in the Berean table.

## Install

1. Download both files (open each file page on GitHub and use the download button).
2. Put `BIBhg.bbl.mybible` in MySword's Bible modules folder and `BIBhg-morph.dct.mybible` in its dictionaries folder (the paths are shown in MySword's settings), or open each file with MySword.
3. In MySword choose the Bible module **BIBhg**. Tapping a morphology code should show Berean's description.

Strong's numbers use whichever Strong's dictionary you have installed in MySword (not included here).

Not tested inside the MySword app (it was built and checked as a database only). If the layout looks wrong, open an issue with a screenshot.

## Rebuild

```
python3 build_interlinear.py
```

Source files: `source/bsb_OT.tsv.zip` and `source/bsb_NT.tsv.zip` (the Berean tables, split by testament and zipped).

## Source and licence

The Holy Bible, Berean Standard Bible, BSB is produced in cooperation with Bible Hub, Discovery Bible,
OpenBible.com, and the Berean Bible Translation Committee. This text of God's Word has been dedicated to the
public domain (Berean terms and conditions, 30 April 2023: "All uses are freely permitted").

This module is an independent adaptation, not an official Berean product. It differs from the official text in
presentation (Hebrew/Greek word order, "vvv" shown as "-", verse labels removed), so per Berean's request it does
not carry the Berean name.

### Strong's dictionary (`BIBhg-strongs.dct.mybible`)

* Hebrew: James Strong, *A Concise Dictionary of the Words in the Hebrew Bible* (1894, public domain); e-text by
  David Instone-Brewer and David Troidl; JSON edition © 2010 Open Scriptures, **CC-BY-SA 3.0**. Because of this,
  the Strong's dictionary module is shared under CC-BY-SA (keep this credit if you redistribute it).
* Greek: James Strong, *A Concise Dictionary of the Words in the Greek Testament* (public domain); XML edition 1.4
  by Ulrik Petersen (public domain), plus Berean's short Greek definitions (public domain) from
  `../MyBible/dictionary/Berean_StrongNoDictionary.csv`.
* Sources: `source/strongs/` (from the `strongs` 1.0.2 npm package, github.com/openscriptures/strongs).

### English concordance (`BIBhg-concordance.dct.mybible`)

* Source: Berean's **BSB Concordance - xlsx** (berean.bible, Study Tools, 2nd printing), `bsb_concordance.xlsx`,
  52,051,537 bytes, SHA-256 `01a888e221cdfb652b19e2791e82b5a7141beb703d54661b8819ff49d89580d3`. Stored as
  tab-separated text in `source/concordance/bsb_concordance.tsv.zip` (columns A–I, unchanged cell values).
* 14,782 words, 726,744 occurrences; every reference matches a verse in BIBhg. Word counts agree with the BSB
  Translation Tables to within 0.03% (e.g. Lord 7,603 vs 7,606), as the concordance follows an earlier printing.
* Very common words ("The", "And", "Of" …) have very large entries (up to ~4 MB) and may open slowly.
* The verse-link format (`VERSE_LINK` in `build_concordance.py`) has not yet been tested in MySword.

### Thayer's lexicon (`BIBhg-thayer.dct.mybible`)

* Greek: Joseph Henry Thayer, *A Greek-English Lexicon of the New Testament* (1889, public domain), unabridged.
  Source: e-Sword lexicon `thayers_unabridged.lexi` from biblesupport.com (theWord module by Rob Sauers),
  SHA-256 `26376143c2fe36cbf65c4b27ad43ec8d9a81c779386f2881f451f5ee2a06e0c9`, stored zipped in `source/thayer/`.
* The source's Hebrew words are in an old Windows-1255 font encoding; they are converted to Unicode Hebrew.
  Bible references become verse links (same format as the concordance; not yet tested in MySword). References to
  the Apocrypha stay plain text.
* Hebrew numbers open BDB: Brown, Driver, Briggs, *A Hebrew and English Lexicon of the Old Testament* (1906, public
  domain), abridged e-text from the Open Scriptures Hebrew Lexicon (github.com/openscriptures/HebrewLexicon, commit
  21c9add, CC BY 4.0), `source/bdb/HebrewLexicon.zip`; matched to Strong's numbers by its LexicalIndex.xml (8,673 of
  8,674 numbers). Below it, Strong's Hebrew (same source and CC-BY-SA licence as `BIBhg-strongs.dct.mybible`).
