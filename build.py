#!/usr/bin/env python3
"""Regenerate index.html (the deployed page) from the pristine export.

The export is a single bundled HTML file whose real document lives as an escaped
JSON string inside a <script type="__bundler/template"> tag. This script edits
that inner document: sets the page title and injects mobile.css into its <head>.

Idempotent: re-running always rebuilds from SOURCE, so re-exporting the design
tool's file and running this again picks up the new content and re-applies the
mobile layer. Usage: python3 build.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
SOURCE = HERE / "Ann Mutheu Portfolio.html"
CSS = HERE / "mobile.css"
OUT = HERE / "index.html"
TITLE = "Ann Mutheu — Portfolio"
MARKER = "/* injected: mobile.css */"


def escape_for_template(css: str) -> str:
    """Match the bundler's escaping for text embedded in the template string."""
    css = css.replace("\\", "\\\\").replace('"', '\\"')
    css = css.replace("\n", "\\n")
    # The bundler escapes forward slashes in closing tags to avoid breaking out
    # of the surrounding <script> element.
    return css.replace("</", "<\\u002F")


def main() -> int:
    for f in (SOURCE, CSS):
        if not f.exists():
            sys.exit(f"missing required file: {f}")

    html = SOURCE.read_text(encoding="utf-8")
    css = CSS.read_text(encoding="utf-8")

    # 1. Outer document title (the browser tab / search-result headline).
    html, n_outer = re.subn(
        r"<title>.*?</title>", f"<title>{TITLE}</title>", html, count=1
    )

    # 2. The inner document has no <title> of its own, and once the bundle
    #    renders, its head replaces the outer one — leaving document.title
    #    empty in the browser tab. So insert one rather than substitute.
    title_tag = f"<title>{TITLE}<\\u002Ftitle>"

    # 2b. Icons. Absolute paths, since the site is served from the domain root.
    #     Without these the browser falls back to auto-requesting /favicon.ico.
    icons = "".join(
        [
            '<link rel=\\"icon\\" href=\\"/favicon.svg\\" type=\\"image/svg+xml\\">',
            '<link rel=\\"icon\\" href=\\"/favicon.ico\\" sizes=\\"48x48\\">',
            '<link rel=\\"apple-touch-icon\\" href=\\"/apple-touch-icon.png\\">',
            # Tints the browser chrome on Android to match the site's ground.
            '<meta name=\\"theme-color\\" content=\\"#10201C\\">',
        ]
    )

    # 3. Inject the stylesheet as the last thing in the inner <head>, so it
    #    follows the page's own <style> blocks in source order.
    block = (
        f"{title_tag}\\n{icons}\\n"
        f"<style>{MARKER}\\n{escape_for_template(css)}<\\u002Fstyle>\\n"
        f"<\\u002Fhead>"
    )
    if "<\\u002Fhead>" not in html:
        sys.exit("could not find the inner </head> — bundler format changed?")
    html = html.replace("<\\u002Fhead>", block, 1)

    # 4. Mirror the icons into the outer <head>. The bundle replaces this head
    #    at runtime, but crawlers and anything not executing JS only ever see
    #    the outer document.
    outer_icons = icons.replace('\\"', '"')
    html = html.replace("</head>", f"{outer_icons}\n</head>", 1)

    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.name}  ({OUT.stat().st_size:,} bytes)")
    print(f"  title set: outer={n_outer} inner=1 (inserted)")
    print(f"  injected {len(css):,} bytes of mobile.css")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
