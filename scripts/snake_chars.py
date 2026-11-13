"""Turn the plain snk snake into one that changes character on every loop.

The snk SVG is colored through CSS variables on :root (--cs for the snake,
--c1..--c4 for the contribution squares) and loops every N ms. This script
adds a palette animation that is six loops long, so the colors (and a small
name label) switch exactly when the snake starts over.

Usage: python snake_chars.py <dir with snake.svg and snake-dark.svg>
"""

import re
import sys
from pathlib import Path
from xml.dom import minidom

# name, snake color, then contribution squares from light to strong
CHARACTERS = [
    ("Ado", "#4c6ef5", ["#bac8ff", "#91a7ff", "#5c7cfa", "#3b5bdb"]),
    ("Hatsune Miku", "#1fb5ab", ["#b8ece8", "#7ddcd5", "#39c5bb", "#1f8f88"]),
    ("9Lana", "#a06bf0", ["#f7c6e3", "#ec9bd0", "#b47be8", "#7c4dcc"]),
    ("Trafalgar Law", "#e6b800", ["#fff3b0", "#ffe066", "#f5c518", "#b8860b"]),
    ("Bocchi", "#ec6fa2", ["#fde0ec", "#f9b8d3", "#f48fb1", "#d6578a"]),
    ("Kasane Teto", "#e11d48", ["#fecdd3", "#fda4af", "#fb7185", "#be123c"]),
]

EPS = 0.01


def pct(value):
    return f"{value:.2f}".rstrip("0").rstrip(".") + "%"


def build_css(loop_ms):
    count = len(CHARACTERS)
    total_ms = loop_ms * count
    step = 100 / count
    frames = []
    for i, (_, snake, dots) in enumerate(CHARACTERS):
        start = i * step
        end = (i + 1) * step - EPS
        marks = f"{pct(start)},{pct(end)}"
        frames.append(
            f"{marks}{{--cs:{snake};--c1:{dots[0]};--c2:{dots[1]};"
            f"--c3:{dots[2]};--c4:{dots[3]}}}"
        )
    css = [f"@keyframes pal{{{''.join(frames)}}}"]
    css.append(f":root{{animation:pal {total_ms}ms linear infinite}}")
    css.append(
        ".nm{font:600 12px ui-sans-serif,system-ui,-apple-system,Segoe UI,"
        "Helvetica,Arial,sans-serif;fill:var(--cs);opacity:0;"
        f"animation:none {total_ms}ms linear infinite}}"
    )
    for i in range(count):
        start = i * step
        end = (i + 1) * step - EPS
        keys = []
        if i == 0:
            keys.append("0%{opacity:1}")
        else:
            keys.append(f"0%,{pct(start - EPS)}{{opacity:0}}")
            keys.append(f"{pct(start)}{{opacity:1}}")
        keys.append(f"{pct(end)}{{opacity:1}}")
        keys.append(f"{pct(end + EPS)},100%{{opacity:0}}")
        css.append(f"@keyframes n{i}{{{''.join(keys)}}}")
        css.append(f".nm.n{i}{{animation-name:n{i}}}")
    return "".join(css)


def build_labels():
    return "".join(
        f'<text class="nm n{i}" x="0" y="-14">{name}</text>'
        for i, (name, _, _) in enumerate(CHARACTERS)
    )


def convert(source, target):
    svg = source.read_text(encoding="utf-8")
    found = re.search(r"animation:none (\d+)ms", svg)
    if not found:
        raise SystemExit(f"{source}: loop length not found")
    loop_ms = int(found.group(1))
    if "</style>" not in svg or not svg.rstrip().endswith("</svg>"):
        raise SystemExit(f"{source}: unexpected structure")
    svg = svg.replace("</style>", build_css(loop_ms) + "</style>", 1)
    svg = svg.rstrip()[: -len("</svg>")] + build_labels() + "</svg>"
    minidom.parseString(svg.encode("utf-8"))
    target.write_text(svg, encoding="utf-8")
    print(f"{target.name}: {loop_ms} ms per loop, {len(svg)} bytes")


def main():
    folder = Path(sys.argv[1])
    convert(folder / "snake.svg", folder / "snake-chars.svg")
    convert(folder / "snake-dark.svg", folder / "snake-chars-dark.svg")


if __name__ == "__main__":
    main()
