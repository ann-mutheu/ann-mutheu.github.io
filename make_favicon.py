#!/usr/bin/env python3
"""Generate the favicon set from the SVG sources. Run only when the icon design
changes; the outputs are committed, so a normal `python3 build.py` does not
need this (or rsvg-convert) to run.

Sizes carry different artwork on purpose. A two-letter serif monogram turns to
mush at 16px, so:
    16px        -> single "A"      (favicon-16.svg)
    32px, 48px  -> "AM" monogram   (favicon-small.svg, squared-off letterforms)
    SVG, 180px  -> "AM" + rule     (favicon.svg, the full design)
Only one size is ever shown at a time, so the variation is invisible in use.

Requires rsvg-convert (brew install librsvg). Usage: python3 make_favicon.py
"""
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FULL = HERE / "favicon.svg"          # AM + accent rule
SMALL = HERE / "favicon-small.svg"   # AM, heavier, no rule
TINY = HERE / "favicon-16.svg"       # single A
ICO_PARTS = [(16, TINY), (32, SMALL), (48, SMALL)]


def render(svg: Path, size: int) -> bytes:
    if not svg.exists():
        sys.exit(f"missing {svg.name}")
    r = subprocess.run(
        ["rsvg-convert", "-w", str(size), "-h", str(size), str(svg)],
        capture_output=True,
    )
    if r.returncode != 0:
        sys.exit(f"rsvg-convert failed on {svg.name}: {r.stderr.decode().strip()}")
    return r.stdout


def build_ico(parts: list[tuple[int, bytes]]) -> bytes:
    """Assemble a multi-size .ico. Entries hold PNG data rather than BMP, which
    every browser since IE11 reads and which keeps alpha intact."""
    header = struct.pack("<HHH", 0, 1, len(parts))
    offset = len(header) + 16 * len(parts)
    entries, blobs = b"", b""
    for size, png in parts:
        entries += struct.pack(
            "<BBBBHHII",
            size if size < 256 else 0,  # 0 encodes 256
            size if size < 256 else 0,
            0,   # palette count
            0,   # reserved
            1,   # colour planes
            32,  # bits per pixel
            len(png),
            offset,
        )
        blobs += png
        offset += len(png)
    return header + entries + blobs


def main() -> int:
    ico = build_ico([(s, render(svg, s)) for s, svg in ICO_PARTS])
    (HERE / "favicon.ico").write_bytes(ico)
    (HERE / "apple-touch-icon.png").write_bytes(render(FULL, 180))
    (HERE / "icon-512.png").write_bytes(render(FULL, 512))

    for f in ("favicon.ico", "apple-touch-icon.png", "icon-512.png"):
        print(f"  {f:24} {(HERE / f).stat().st_size:>7,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
