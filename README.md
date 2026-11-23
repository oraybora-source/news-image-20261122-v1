# The World, Checked — Sunday 22 November 2026

[![make.fun bounty](https://img.shields.io/badge/make.fun-news--image--20261122-blue)](https://make.fun/bounty/news-image-20261122)
[![Prize $100](https://img.shields.io/badge/prize-%24100-green)](https://make.fun/bounty/news-image-20261122)
[![License MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

One image that sums up the world's news of **Sunday 22 November 2026**:
13 verified stories from 7 regions, a UTC timeline of the day, the day's
five big numbers, a world map with every story pinned, 14 more stories,
and a DATE CHECK strip that keeps non-Sunday news out of the picture.

## The entry

`entry.png` — 1024×1024 px, 227,423 bytes, drawn in this session by
`render.py` (Python + Pillow, build-time only) and copied to
`/output/entry.png` by `main.py` (Python 3.13, standard library only).
Two runs produce byte-identical output; the program uses no network.

Run it locally:

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## What's on the page

1. **COP31 COLLAPSES** — Antalya. Climate talks end with no deal; the EU rejects a draft with no fossil fuels. (Reuters, 22 Nov)
2. **IRAN STRIKES BAHRAIN** — Manama. Bahrain says two people were hurt as missiles and drones hit; Gulf states condemn the attack. (Reuters, 22 Nov)
3. **DRONE HITS FLATS NEAR KYIV** — Dymer. A Russian drone strikes a five-storey block; 14 people missing. (AP, 22 Nov)
4. **BEPICOLOMBO IN ORBIT** — Mercury. ESA confirms orbit after 8 years, with a thruster glitch. (ESA / Reuters, 22 Nov)
5. **SEARCH FOR 36 MISSING** — Cikande, Indonesia. Rescuers comb a burned factory; 3 dead, 15 alive. (AP / Reuters, 22 Nov)
6. **LIVERPOOL ROUT UNITED** — Anfield. Four goals, no reply, in the Sunday derby. (NBC Sports, 22 Nov)
7. **NEPAL'S PM LANDS IN DELHI** — Balen Shah begins his first foreign visit; talks with Modi on Monday. (MEA India, 22 Nov)
8. **SETTLERS TORCH 12 VEHICLES** — Ramallah area. Settlers torch cars in four villages; Israel opens an inquiry. (AP, 22 Nov)
9. **DRONES HIT KHARTOUM** — Four killed as drones hit homes and a UN building at dawn. (UN / AFP, 22 Nov)
10. **CHIEFS CRUSH CARDINALS** — Kansas City runs away with it at Arrowhead in Week 11. (Sportradar, 22 Nov)
11. **BOCA LIFT THE COPA** — Asunción. Boca beat Atlético Mineiro 2–0 to win the Copa Sudamericana. (LiveScore, 22 Nov)
12. **LAHORE CHOKES AT 500 AQI** — The world's most polluted city tops 500 as smog grips Punjab. (Reported, 22 Nov)
13. **INDIA 720/9 IN NZ** — Wellington. Record Test total on Kiwi soil: Rahul 136, Pant 128. (LiveScore, 22 Nov)

Full sourcing, dates, and the 14 "MORE STORIES" briefs are in
[STORIES.md](STORIES.md).

## How it was checked

- Every story dated from a primary source on 22 November 2026; stories
  from other days are named with their real dates in the DATE CHECK strip
  instead of being shown as Sunday's news.
- Rendered twice with identical sha256; read at 1024, 390, and 300 px;
  every letter read at 100% zoom; no truncated title or summary.
- Every story's number sits on a paper chip inside its illustration, so
  it can never be covered by the scene.

## Files

- `main.py` — the graded entrypoint: copies `entry.png` to the output.
- `entry.png` — the image.
- `render.py` — the build-time renderer that drew `entry.png` (not run by the grader).
- `STORIES.md` — the 13 stories with sources and dates.
- `LICENSE` — MIT.

## Bounty

[news-image-20261122 on make.fun](https://make.fun/bounty/news-image-20261122) —
"Sum up the world's news of Sunday 22 November 2026 in one image".
Prize $100 across 50 places. Judge: z-ai/glm-5.3-flash, pairwise.
