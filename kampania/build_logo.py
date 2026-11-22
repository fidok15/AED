"""Build logo files (SVG, PNG, JPG, PDF) and the brand book PDF for "Opiekun AED".

Source of truth: kampania/logo/svg/*.svg exported from Figma (file "AED – koncepcje logo",
frame "Eksport · logo D (wybrane)" and components sygnet/D/*).

Usage: uv run --no-project --with playwright python kampania/build_logo.py
"""
import base64
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
LOGO = HERE / "logo"
CHROME = (
    "/Users/fidok/Library/Caches/ms-playwright/chromium_headless_shell-1248/"
    "chrome-headless-shell-mac-arm64/chrome-headless-shell"
)
NAVY = "#14274E"

# Visible artwork plus clear space of 1X on every side (X = side of one heart cell).
# lockup: cell 33.33 px, artwork x 3.33..956.5, y 23.33..176.67
# sygnet: cell 20 px, artwork x 2..118, y 14..106
VIEWBOX = {"lockup": (-30, -10, 1020, 220), "sygnet": (-18, -6, 156, 132)}
PX_WIDTH = {"lockup": 2040, "sygnet": 1024}


def crop_svg(path: Path) -> tuple[int, int]:
    """Set viewBox to artwork + clear space. Idempotent."""
    x, y, w, h = VIEWBOX[path.stem.split("-")[2]]
    svg = path.read_text()
    svg = re.sub(r"<svg [^>]*>", f'<svg width="{w}" height="{h}" viewBox="{x} {y} {w} {h}" fill="none" xmlns="http://www.w3.org/2000/svg">', svg, count=1)
    path.write_text(svg)
    return w, h


def render_logos(browser) -> None:
    for sub in ("png", "jpg", "pdf"):
        (LOGO / sub).mkdir(exist_ok=True)
    page = browser.new_page()
    for svg in sorted((LOGO / "svg").glob("opiekun-aed-*.svg")):
        w, h = crop_svg(svg)
        kind = svg.stem.split("-")[2]
        scale = PX_WIDTH[kind] / w
        pw, ph = round(w * scale), round(h * scale)
        bg = NAVY if "negatyw" in svg.stem else "#FFFFFF"
        html = f'<html><body style="margin:0"><img id="l" src="data:image/svg+xml;base64,{base64.b64encode(svg.read_bytes()).decode()}" style="display:block;width:{pw}px;height:{ph}px"></body></html>'
        page.set_viewport_size({"width": pw, "height": ph})
        page.set_content(html)
        page.wait_for_load_state("load")
        page.locator("#l").screenshot(path=str(LOGO / "png" / f"{svg.stem}.png"), omit_background=True)
        page.evaluate(f"document.body.style.background='{bg}'")
        page.locator("#l").screenshot(path=str(LOGO / "jpg" / f"{svg.stem}.jpg"), type="jpeg", quality=95)
        # PDF stays vector: Chromium embeds the SVG as paths.
        page.set_content(html.replace('style="margin:0"', f'style="margin:0;background:{bg}"').replace(f"width:{pw}px;height:{ph}px", f"width:{w}px;height:{h}px"))
        page.wait_for_load_state("load")
        page.pdf(path=str(LOGO / "pdf" / f"{svg.stem}.pdf"), width=f"{w}px", height=f"{h}px", print_background=True, page_ranges="1")
        print(svg.stem, f"{pw}x{ph}")
    page.close()


def render_book(browser) -> None:
    page = browser.new_page()
    page.goto((HERE / "ksiega-znaku" / "ksiega-znaku.html").resolve().as_uri())
    page.wait_for_load_state("networkidle")
    page.evaluate("document.fonts.ready")
    out = HERE / "opiekun-aed-ksiega-znaku.pdf"
    page.pdf(path=str(out), prefer_css_page_size=True, print_background=True)
    print(out, f"{out.stat().st_size / 1e6:.1f} MB")
    page.close()


if __name__ == "__main__":
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME if Path(CHROME).exists() else None)
        render_logos(browser)
        render_book(browser)
        browser.close()
