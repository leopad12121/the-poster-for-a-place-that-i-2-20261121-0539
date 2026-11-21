# the-poster-for-a-place-that-i-2-20261121-0539
[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/leopad12121/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/leopad12121/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

**VELMARA — Where Two Suns Set.** A vintage travel poster for an island that
does not exist, drawn entirely in code: a red-banded lighthouse on a rocky
headland, two suns sinking over snow-capped ridges, a glittering sun path
across the sea, sailboats, seabirds, and the place name set large in a cream
title band.

## The place

Velmara is an island in no atlas. It has two suns, so every evening is a
double sunset: one sun sinks behind the mountains while the smaller one still
hangs high in a violet sky. The lighthouse on the headland keeps the only
harbour, and the evenings there are the longest anyone has measured.

## Run it

Pure Python 3.13 standard library — no network, no third-party packages, no
randomness, no timestamps. The output is fully deterministic.

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 -P -s main.py
# writes /tmp/out/entry.png — 1024x1024 PNG, 24,062 bytes
```

Run it twice and the bytes are identical.

## How it is drawn

`main.py` renders the poster with a small vector canvas (rectangles, lines,
polygons, circles, ellipses, alpha blending), a 5x7 bitmap font for the
lettering, and a hand-rolled PNG encoder (`zlib` + `struct`, filter 0).
The sky is a five-stop sunset gradient; the sea is a second gradient with a
deterministic glitter path under the big sun; the mountains are layered
ridge polygons with snow caps; the lighthouse, boats, birds, stars and
clouds are all drawn from fixed coordinates, so the poster never changes
between runs.

## License

MIT — see [LICENSE](LICENSE).
