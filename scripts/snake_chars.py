"""Turn the plain snk snake into one that changes character on every loop.

The snk SVG is colored through CSS variables on :root (--cs for the snake,
--c1..--c4 for the contribution squares) and loops every N ms. This script
adds a palette animation that is six loops long, so the colors switch exactly
when the snake starts over. It can also pin a small accessory of each
character to the snake: the accessory reuses the keyframes of a snake segment
so it follows it, and it is only visible during its character's loop.

Usage: python snake_chars.py <dir with snake.svg and snake-dark.svg>
"""

import math
import re
import sys
from pathlib import Path
from xml.dom import minidom

# snake color, then contribution squares from light to strong
CHARACTERS = [
    ("Ado", "#4c6ef5", ["#bac8ff", "#91a7ff", "#5c7cfa", "#3b5bdb"]),
    ("Hatsune Miku", "#1fb5ab", ["#b8ece8", "#7ddcd5", "#39c5bb", "#1f8f88"]),
    ("9Lana", "#a06bf0", ["#f7c6e3", "#ec9bd0", "#b47be8", "#7c4dcc"]),
    ("Trafalgar Law", "#e6b800", ["#fff3b0", "#ffe066", "#f5c518", "#b8860b"]),
    ("Bocchi", "#ec6fa2", ["#fde0ec", "#f9b8d3", "#f48fb1", "#d6578a"]),
    ("Kasane Teto", "#e11d48", ["#fecdd3", "#fda4af", "#fb7185", "#be123c"]),
]

EPS = 0.01
OUTLINE = "#6b7280"


def pct(value):
    return f"{value:.2f}".rstrip("0").rstrip(".") + "%"


# Accessories are drawn in the 16x16 cell of the segment they follow.


def flower():
    petals = []
    for k in range(5):
        angle = math.radians(-90 + 72 * k)
        cx = 8 + 2.7 * math.cos(angle)
        cy = 8 + 2.7 * math.sin(angle)
        petals.append(
            f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="2.3" fill="#ffffff" '
            f'stroke="{OUTLINE}" stroke-width=".5"/>'
        )
    return "".join(petals) + '<circle cx="8" cy="8" r="1.7" fill="#ffd43b"/>'


def twin_tails(color, tie):
    tails = []
    for cx in (-1.8, 17.8):
        tails.append(
            f'<ellipse cx="{cx}" cy="10" rx="2.8" ry="10" fill="{color}" '
            f'stroke="{OUTLINE}" stroke-width=".4"/>'
            f'<circle cx="{cx}" cy="0.8" r="1.5" fill="{tie}"/>'
        )
    return "".join(tails)


def fluffy_hat():
    puffs = [(3.5, 3.5, 4.2), (8, 1.5, 4.8), (12.5, 3.5, 4.2), (8, 4.5, 4.4)]
    shapes = [
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" '
        f'stroke="{OUTLINE}" stroke-width=".5"/>'
        for x, y, r in puffs
    ]
    # drawn again without stroke so the puffs merge into one hat
    shapes += [
        f'<circle cx="{x}" cy="{y}" r="{r - 0.4}" fill="#ffffff"/>'
        for x, y, r in puffs
    ]
    shapes.append('<circle cx="10.6" cy="1.4" r="1.4" fill="#e45cae"/>')
    shapes.append('<circle cx="7.4" cy="0.9" r="1.3" fill="#4fb3e8"/>')
    return "".join(shapes)


def sword():
    return (
        '<line x1="-8" y1="21" x2="23" y2="-10" stroke="#6b7280" '
        'stroke-width="2.6" stroke-linecap="round"/>'
        '<line x1="-8" y1="21" x2="23" y2="-10" stroke="#eef2f7" '
        'stroke-width="1.2" stroke-linecap="round"/>'
        '<line x1="-8" y1="21" x2="-3.5" y2="16.5" stroke="#22252b" '
        'stroke-width="2.8" stroke-linecap="round"/>'
        '<line x1="-5.3" y1="14.8" x2="-1.7" y2="18.4" stroke="#ffd23f" '
        'stroke-width="1.4" stroke-linecap="round"/>'
    )


def hair_clips():
    return (
        f'<rect x="0.6" y="0.2" width="3.8" height="3.8" rx=".8" fill="#ffd23f" '
        f'stroke="{OUTLINE}" stroke-width=".4"/>'
        f'<rect x="5" y="0.2" width="3.8" height="3.8" rx=".8" fill="#3b9cff" '
        f'stroke="{OUTLINE}" stroke-width=".4"/>'
    )


def drills(color):
    shapes = []
    for side in (-1, 1):
        base = -2.2 if side < 0 else 18.2
        for k, (dy, r) in enumerate([(7, 3.4), (11.5, 2.8), (15.2, 2.1), (18, 1.4)]):
            cx = base + side * (0.7 if k % 2 else -0.7)
            shapes.append(
                f'<circle cx="{cx:.1f}" cy="{dy}" r="{r}" fill="{color}" '
                f'stroke="{OUTLINE}" stroke-width=".4"/>'
            )
    return "".join(shapes)


# one accessory per character, in the same order as CHARACTERS:
# (segment it follows, drawing)
ACCESSORIES = [
    (1, flower()),
    (0, twin_tails("#39c5bb", "#ff6b9d")),
    (0, fluffy_hat()),
    (0, sword()),
    (0, hair_clips()),
    (0, drills("#e11d48")),
]


def slot(i):
    count = len(CHARACTERS)
    step = 100 / count
    return i * step, (i + 1) * step - EPS


def build_css(loop_ms, accessories):
    count = len(CHARACTERS)
    total_ms = loop_ms * count
    frames = []
    for i, (_, snake, dots) in enumerate(CHARACTERS):
        start, end = slot(i)
        frames.append(
            f"{pct(start)},{pct(end)}{{--cs:{snake};--c1:{dots[0]};--c2:{dots[1]};"
            f"--c3:{dots[2]};--c4:{dots[3]}}}"
        )
    css = [f"@keyframes pal{{{''.join(frames)}}}"]
    css.append(f":root{{animation:pal {total_ms}ms linear infinite}}")
    if accessories:
        css.append(
            f".ac{{opacity:0;animation-duration:{loop_ms}ms,{total_ms}ms;"
            "animation-timing-function:linear;animation-iteration-count:infinite}"
        )
        for i, (segment, _) in enumerate(ACCESSORIES):
            start, end = slot(i)
            keys = []
            if i == 0:
                keys.append("0%{opacity:1}")
            else:
                keys.append(f"0%,{pct(start - EPS)}{{opacity:0}}")
                keys.append(f"{pct(start)}{{opacity:1}}")
            keys.append(f"{pct(end)}{{opacity:1}}")
            keys.append(f"{pct(end + EPS)},100%{{opacity:0}}")
            css.append(f"@keyframes o{i}{{{''.join(keys)}}}")
            css.append(f".ac.a{i}{{animation-name:s{segment},o{i}}}")
    return "".join(css)


def build_accessories():
    return "".join(
        f'<g class="ac a{i}">{drawing}</g>'
        for i, (_, drawing) in enumerate(ACCESSORIES)
    )


def convert(source, target, accessories):
    svg = source.read_text(encoding="utf-8")
    found = re.search(r"animation:none (\d+)ms", svg)
    if not found:
        raise SystemExit(f"{source}: loop length not found")
    loop_ms = int(found.group(1))
    if "</style>" not in svg or not svg.rstrip().endswith("</svg>"):
        raise SystemExit(f"{source}: unexpected structure")
    svg = svg.replace("</style>", build_css(loop_ms, accessories) + "</style>", 1)
    if accessories:
        svg = svg.rstrip()[: -len("</svg>")] + build_accessories() + "</svg>"
    minidom.parseString(svg.encode("utf-8"))
    target.write_text(svg, encoding="utf-8")
    print(f"{target.name}: {loop_ms} ms per loop, {len(svg)} bytes")


def main():
    folder = Path(sys.argv[1])
    for base, light in (("snake", ""), ("snake-dark", "-dark")):
        source = folder / f"{base}.svg"
        convert(source, folder / f"snake-chars{light}.svg", False)
        convert(source, folder / f"snake-acc{light}.svg", True)


if __name__ == "__main__":
    main()
