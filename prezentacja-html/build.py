"""Build prezentacja.html: index.html with every image and font inlined as data URI.

Usage: python3 prezentacja-html/build.py
The result is one file that opens offline in any browser (double-click).
"""
import base64
import mimetypes
import re
from pathlib import Path

HERE = Path(__file__).parent
MIME = {".woff2": "font/woff2", ".gif": "image/gif", ".png": "image/png", ".jpg": "image/jpeg"}


def data_uri(path: Path) -> str:
    mime = MIME.get(path.suffix) or mimetypes.guess_type(path.name)[0]
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def main() -> None:
    html = (HERE / "index.html").read_text(encoding="utf-8")

    fonts_css = HERE / "assets/fonts/fonts.css"
    css = re.sub(r"url\((.*?)\)", lambda m: f"url({data_uri(fonts_css.parent / m.group(1))})", fonts_css.read_text())
    html = html.replace('<link rel="stylesheet" href="assets/fonts/fonts.css">', f"<style>{css}</style>")

    html = re.sub(r'src="((?:\.\./|assets/)[^"]+)"', lambda m: f'src="{data_uri(HERE / m.group(1))}"', html)
    assert 'src="../' not in html and 'src="assets/' not in html, "unresolved asset"

    out = HERE / "prezentacja.html"
    out.write_text(html, encoding="utf-8")
    print(out, f"{out.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
