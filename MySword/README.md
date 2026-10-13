# MySword Interlinear Bible (Hebrew + Greek)

**File to download:** [`BIBhg.bbl.mybible`](BIBhg.bbl.mybible) — one module, all 66 books.

* Old Testament: every Hebrew word, with transliteration, Strong's number (`H…`), morphology, and the Berean English word ("-" where Berean has none).
* New Testament: every Greek word of the Berean Interlinear Bible, with transliteration, Strong's number (`G…`),
  morphology, Berean English. Textual-variant words are in italics.
* Verse numbering is KJV. Nehemiah 7:68 is empty because the Hebrew text does not have it.

## Install

1. Download `BIBhg.bbl.mybible` (open the file page on GitHub and use the download button).
2. Put it in MySword's Bible modules folder (the path is shown in MySword's settings), or open the file with MySword.
3. In MySword choose the Bible module **BIBhg**.

Not tested inside the MySword app (it was built and checked as a database only). If the layout looks wrong, open an issue with a screenshot.

## Rebuild

```
python3 build_interlinear.py
```

Sources: `../e-Sword/FINAL/BIB++.bbli.zip` (Greek) and `source/BHSA-8-layer-interlinear.csv.zip` (Hebrew).

## Licences

* Greek: Berean Interlinear Bible, © 2016 Bible Hub, free licence (berean.bible/licensing.htm).
* Hebrew: [Open Hebrew Bible Project](https://github.com/eliranwong/OpenHebrewBible) by Eliran Wong, **CC BY-NC 4.0**, built on ETCBC's BHS
  (non-commercial) and OpenScriptures Strong's numbers. **Non-commercial use only.** English on the Hebrew side is the Berean Study Bible, aligned word-by-word by that project.
