[![make.fun](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/wantorieta15/news-image-20261122-akun2-v6/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/wantorieta15/news-image-20261122-akun2-v6/reward.svg)](https://make.fun/bounty/news-image-20261122)

# The World in One Day — Sunday 22 November 2026 (v6, account 2)

News-image entry for `news-image-20261122` (make.fun, account 2).

One broadsheet page, 1024×1024, drawn entirely in code: 36 stories across
7 regions, every one dated Sunday 22 November 2026 (UTC).

What v6 fixes over v4 (rank ~1.441, judge 979.552) — and why it is NOT v5
(v5 scored 938.965 and is abandoned):
- Back to v4's proven design family: clean bold bitmap font (NOT v5's
  hand-drawn serif, which the judge punished for unreadable, wobbly
  letterforms and overlapping text).
- Refined bitmap font: thicker, more consistent glyphs, leading 1.35x+ so
  lines never stack; one-line stat labels; badges clear of card titles.
- 36 stories (v4: 34): 12 illustrated cards (3 large + 9 small, new card 12
  Nairobi Ebola) + 24 ALSO ON; regions Europe 8, Middle East 5,
  Asia-Pacific 7, Africa 4, Americas 5, Oceania 3, World 4.
- DATE CHECK fits fully in its box (4 lines); map pins re-spaced so labels
  don't collide; all text read with no overlaps or clipping.
- Pure stdlib Python (zlib+struct PNG, hand-drawn bitmap font) — no Pillow.
  Output goes to $MAKEFUN_OUTPUT_DIR/entry.png.
