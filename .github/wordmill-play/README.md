# Wordmill web game: how it stays up to date

The game at `/wordmill/play/` is static. Only one thing changes by date: which day files and answers pages exist.

- `bundle.bin` (this folder): the app's whole puzzle calendar, zlib + xor. Built by `iOS/Wordmill/tools/build_web.py`
  in the Word repo. Not published under Jekyll (dot folder); if the site uses `.nojekyll` it is reachable, but not as
  plain text. Obfuscation only, not security.
- `daily.py`: Python 3 standard library. Writes `wordmill/play/data/<lang>/<yyyy-mm-dd>.json` for today-30 … today+2
  (obfuscated per day), the "answers" pages for the past days of that window, the answers index pages and
  `wordmill/play/sitemap.xml`; deletes files that left the window.
- `../workflows/wordmill-play.yml`: runs `daily.py` every day at 12:15 UTC and commits the result.

Manual run (also the fallback if Actions are off): `python3 .github/wordmill-play/daily.py --root .` then commit and push.
Day files reach two days ahead, so one missed run does no harm; after two missed days the page says
"today's puzzles aren't here yet".

GitHub turns off scheduled workflows in public repos after 60 days without repository activity. The daily commit
counts as activity, but if the workflow is ever disabled, re-enable it under Actions → Wordmill daily puzzles.
