# MySword Interlinear Bible (Hebrew + Greek)

**Files to download:**

* [`BIBhg.bbl.mybible`](BIBhg.bbl.mybible) — the interlinear Bible, all 66 books.
* [`BIBhg-morph.dct.mybible`](BIBhg-morph.dct.mybible) — morphology dictionary (3,818 codes, Berean's own descriptions). Needed for the parsing popups.

Built only from Berean's own **BSB Translation Tables** (bereanbible.com):

* Old Testament: every Hebrew/Aramaic word, with transliteration, Strong's number (`H…`), morphology, and the
  Berean Standard Bible English for that word.
* New Testament: every Greek word, with transliteration, Strong's number (`G…`), morphology, and the Berean
  Standard Bible English for that word.
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
unfoldingWord, Bible Aquifer, OpenBible.com, and the Berean Bible Translation Committee. The Berean Bible
states: "This text of God's Word has been dedicated to the public domain." Check bereanbible.com for the terms
that apply to the Hebrew and Greek tables themselves.
