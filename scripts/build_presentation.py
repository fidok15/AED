"""Build the jury deck docs/prezentacja/misja-aed.pptx from docs/prezentacja/slajdy.json.

    uv run --with python-pptx python scripts/build_presentation.py            # build + check
    uv run --with python-pptx python scripts/build_presentation.py --liczby   # list number placeholders

Slide text lives in slajdy.json; this file only does layout. Numbers in the text are
placeholders filled from datasets/out/raport.json, aed_standard/schema.json and the
publication CSV (hard rule 10). A missing screenshot becomes a visible
"Zrzut do uzupełnienia" box; add the file and rerun.
"""
import csv
import json
import math
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "docs/prezentacja/slajdy.json"
OUT = ROOT / "docs/prezentacja/misja-aed.pptx"

FONT = "Arial"
INK = RGBColor(0x1B, 0x1B, 0x1B)      # 16.8:1 on white
MUTED = RGBColor(0x4D, 0x4D, 0x4D)    # 8.4:1 on white
ACCENT = RGBColor(0x00, 0x52, 0xA5)   # 7.6:1 on white; white on it 7.6:1
TINT = RGBColor(0xE8, 0xEE, 0xF7)     # box fill, ink on it 14.6:1
GREY = RGBColor(0xF2, 0xF2, 0xF2)
LINE = RGBColor(0xBF, 0xBF, 0xBF)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

W, H = 13.333, 7.5
MX = 0.6                     # side margin
BODY_TOP, BODY_BOTTOM = 2.0, 6.7


# ---------- numbers (rule 10: only from our own outputs) ----------

def pl(n):
    if isinstance(n, float):
        return f"{n:.1f}".replace(".", ",")
    return f"{n:,}".replace(",", " ")


def numbers():
    rap = json.loads((ROOT / "datasets/out/raport.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "aed_standard/schema.json").read_text(encoding="utf-8"))
    src = {s["id"]: s["zrodlo"] for s in json.loads((ROOT / "aed_standard/sources.json").read_text(encoding="utf-8"))["sources"]}
    with open(ROOT / "datasets/out/aed_dane_gov_pl.csv", encoding="utf-8") as f:
        export = list(csv.DictReader(f))
    per = rap["rekordy_na_zrodlo"]
    reasons = rap["eksport_dane_gov_pl"]["powody_wykluczenia"]
    komp = rap["kompletnosc_srednia"]
    n = {
        "rejestr": rap["rejestr_rekordy"],
        "polaczenia": rap["polaczenia"]["razem"],
        "r_odleglosc": rap["polaczenia"]["reguly"]["odleglosc"],
        "r_podobienstwo": rap["polaczenia"]["reguly"]["odleglosc_i_podobienstwo"],
        "r_ref": rap["polaczenia"]["reguly"]["ref_warszawa"],
        "przeglad": rap["do_przegladu"]["razem"],
        "przeglad_kandydat": rap["do_przegladu"]["powody"]["kandydat"],
        "przeglad_konflikt": rap["do_przegladu"]["powody"]["konflikt_zrodel"],
        "niepotwierdzone": rap["statusy"].get("niepotwierdzony", 0),
        "osm_przed": per[src["openstreetmap"]]["przed"],
        "osm_po": per[src["openstreetmap"]]["po"],
        "eksport": rap["eksport_dane_gov_pl"]["rekordy"],
        "wykl_prywatny": reasons["dostep prywatny"],
        "komp_rejestr": komp["rejestr"],
        "komp_eksport": komp["eksport_dane_gov_pl"],
        "eksport_warszawa": sum(r["zrodlo"] == src["warszawa"] for r in export),
        "eksport_z_godzinami": sum(bool(r["godziny_dostepu"]) for r in export),
        "liczba_pol": len(schema["fields"]),
        "liczba_profili": len(schema["profile_wymagalnosci"]),
        # merge of the Legionowo list with the ministry export, reproduced from tests/test_wykaz.py
        "wykaz_wejscie": 805, "wykaz_polaczenia": 24, "wykaz_wynik": 781,
    }
    for sid in ("warszawa", "krosno", "marki", "przemysl", "legionowo"):
        n[sid] = per[src[sid]]["po"]
    return {k: pl(v) for k, v in n.items()}, rap, src


# ---------- text helpers ----------

def style_run(run, size, color=INK, bold=False):
    run.font.name, run.font.size, run.font.color.rgb, run.font.bold = FONT, Pt(size), color, bold


def add_runs(p, text, size, color=INK, bold=False):
    """Text with **bold** fragments."""
    for i, part in enumerate(text.split("**")):
        if part:
            r = p.add_run()
            r.text = part
            style_run(r, size, color, bold or i % 2 == 1)


def set_bullet(p, size, numbered=False):
    pPr = p._p.get_or_add_pPr()
    ind = Pt(size * (1.5 if numbered else 1.1))
    pPr.set("marL", str(int(ind)))
    pPr.set("indent", str(-int(ind)))
    clr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", str(ACCENT))
    if numbered:
        etree.SubElement(pPr, qn("a:buFont")).set("typeface", FONT)
        etree.SubElement(pPr, qn("a:buAutoNum")).set("type", "arabicPeriod")
    else:
        etree.SubElement(pPr, qn("a:buChar")).set("char", "•")


def lines_needed(text, size, width_in, indent_in=0.0):
    # ponytail: average-glyph-width estimate (0.47 em for Arial); good enough to catch overflow, not exact
    per_line = max(1, int((width_in - indent_in) * 72 / (size * 0.47)))
    return sum(max(1, math.ceil(len(chunk) / per_line)) for chunk in text.replace("**", "").split("\n"))


def text_height(items, size, width_in, gap_pt, bullet=True):
    indent = size * 1.5 / 72 if bullet else 0
    lines = sum(lines_needed(t, size, width_in, indent) for t in items)
    return (lines * size * 1.2 + gap_pt * max(0, len(items) - 1)) / 72 + 0.1


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tb, tf


def bullets(slide, items, x, y, w, h, numbered=False, size=20, min_size=12):
    gap = 10
    while size > min_size and text_height(items, size, w, gap) > h:
        size -= 1
        gap = max(4, gap - 1)
    if text_height(items, size, w, gap) > h:
        print(f"  UWAGA: tekst może nie zmieścić się w polu ({items[0][:40]}…)")
    _, tf = textbox(slide, x, y, w, h)
    for i, t in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(0 if i == 0 else gap)
        p.line_spacing = 1.1
        set_bullet(p, size, numbered)
        add_runs(p, t, size)
    return size


def set_alt(shape, alt):
    shape._element.xpath("./*[1]/p:cNvPr")[0].set("descr", alt)


# ---------- visuals ----------

def placeholder(slide, x, y, w, h, label, alt):
    box = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    box.fill.solid()
    box.fill.fore_color.rgb = GREY
    box.line.color.rgb = ACCENT
    box.line.width = Pt(1.25)
    box.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    for m in ("margin_left", "margin_right"):
        setattr(tf, m, Inches(0.1))
    size = 14 if w > 2.5 else 9
    lines = label.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        style_run(p.add_run(), size if i else size + 1, INK, bold=(i == 0))
        p.runs[0].text = line
    set_alt(box, alt)
    return box


def picture(slide, spec, x, y, w, h):
    """Fit a (cropped) screenshot into the box, top-centred. Returns used height."""
    path = ROOT / spec["plik"]
    if not path.exists():
        placeholder(slide, x, y, w, h, "Zrzut do uzupełnienia:\n" + spec["plik"], "Puste miejsce na zrzut: " + spec["alt"])
        return h
    pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y))
    pw, ph = pic.image.size
    x0, y0, x1, y1 = spec.get("kadr", [0, 0, pw, ph])
    pic.crop_left, pic.crop_right = x0 / pw, 1 - x1 / pw
    pic.crop_top, pic.crop_bottom = y0 / ph, 1 - y1 / ph
    rw, rh = x1 - x0, y1 - y0
    scale = min(w / rw, h / rh)
    dw, dh = rw * scale, rh * scale
    pic.left, pic.top = Inches(x + (w - dw) / 2), Inches(y)
    pic.width, pic.height = Inches(dw), Inches(dh)
    pic.line.color.rgb = LINE
    pic.line.width = Pt(0.75)
    set_alt(pic, spec["alt"])
    return dh


def logo(slide, cfg, x, y, w, h, spec):
    path = ROOT / cfg["logo"] if cfg.get("logo") else None
    if path and path.exists():
        return picture(slide, {"plik": cfg["logo"], "alt": "Logo akcji " + (cfg.get("nazwa_akcji") or "")}, x, y, w, h)
    placeholder(slide, x, y, w, h, "Miejsce na logo akcji\nlogo i hasło projektuje zespół", spec["alt"])
    return h


def caption_size(w):
    return 12 if w > 2.5 else 10.5


def caption_height(text, w):
    size = caption_size(w)
    return (lines_needed(text, size, w) + 1) * size * 1.25 / 72  # +1 line: captions run narrow


def caption(slide, text, x, y, w):
    size = caption_size(w)
    _, tf = textbox(slide, x, y, w, caption_height(text, w))
    add_runs(tf.paragraphs[0], text, size, MUTED)


def chart_exclusions(slide, rap, x, y, w, h, spec):
    labels = {
        "licencja ODbL 1.0 (dane OpenStreetMap)": "licencja ODbL (OSM)",
        "profil publikacja – brak_wymaganego: miejscowosc": "brak miejscowości",
        "profil publikacja – brak_wymaganego: nazwa": "brak nazwy",
        "dostep prywatny": "dostęp prywatny",
        "profil publikacja – brak_wymaganego: szerokosc_geograficzna": "brak współrzędnych",
    }
    rows = [(labels[k], v) for k, v in rap["eksport_dane_gov_pl"]["powody_wykluczenia"].items() if k in labels]
    rows.sort(key=lambda r: r[1])  # bar charts draw bottom-up
    data = CategoryChartData()
    data.categories = [r[0] for r in rows]
    data.add_series("Rekordy wykluczone", [r[1] for r in rows])
    gf = slide.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(x), Inches(y), Inches(w), Inches(h), data)
    ch = gf.chart
    ch.has_legend = False
    ch.font.name, ch.font.size, ch.font.color.rgb = FONT, Pt(12), INK
    plot = ch.plots[0]
    plot.gap_width = 60
    plot.series[0].format.fill.solid()
    plot.series[0].format.fill.fore_color.rgb = ACCENT
    plot.has_data_labels = True
    plot.data_labels.number_format = "# ##0"
    plot.data_labels.number_format_is_linked = False
    plot.data_labels.font.size = Pt(12)
    ch.value_axis.visible = False
    ch.value_axis.has_major_gridlines = False
    ch.category_axis.format.line.color.rgb = LINE
    set_alt(gf, spec["alt"] + " " + "; ".join(f"{a}: {pl(b)}" for a, b in reversed(rows)) + ".")
    return h


def table(slide, header, rows, x, y, w, h, alt, size=13, first_col=0.3):
    shape = slide.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = shape.table
    tbl.horz_banding = False
    rest = (w * (1 - first_col)) / (len(header) - 1)
    for i, col in enumerate(tbl.columns):
        col.width = Inches(w * first_col if i == 0 else rest)
    for r, values in enumerate([header] + rows):
        for c, v in enumerate(values):
            cell = tbl.cell(r, c)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TINT if r == 0 else WHITE
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.04)
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if c == 0 or not v[:1].isdigit() else PP_ALIGN.RIGHT
            add_runs(p, v, size, INK, bold=(r == 0))
    set_alt(shape, alt)
    return h


def coverage_table(slide, rap, src, x, y, w, h, spec):
    fields = [("godziny_dostepu", "Godziny dostępu"), ("dostep", "Dostęp"), ("producent", "Producent"),
              ("numer_seryjny", "Numer seryjny"), ("data_waznosci_baterii", "Ważność baterii")]
    per, cov, komp = rap["rekordy_na_zrodlo"], rap["pokrycie_pol"], rap["kompletnosc_srednia"]["zrodla"]
    local = [src[s] for s in ("krosno", "marki", "przemysl", "legionowo")]
    groups = [
        ("4 zbiory samorządowe (" + ", ".join(f"{s.capitalize().replace('Przemysl', 'Przemyśl')} {per[src[s]]['przed']}" for s in ("krosno", "marki", "przemysl", "legionowo")) + ")", local),
        ("API Warszawy", [src["warszawa"]]),
        ("OpenStreetMap", [src["openstreetmap"]]),
    ]
    rows = []
    for label, ids in groups:
        n = sum(per[i]["przed"] for i in ids)
        cells = [label, pl(n)]
        for f, _ in fields:
            share = sum(cov[i].get(f, 0) * per[i]["przed"] for i in ids) / n * 100
            cells.append(f"{pl(round(share, 1))}%".replace(",0%", "%"))
        ks = sorted(komp[i] for i in ids)
        cells.append(pl(ks[0]) if len(ks) == 1 else f"{pl(ks[0])}–{pl(ks[-1])}")
        rows.append(cells)
    header = ["Źródło", "Rekordów"] + [f[1] for f in fields] + ["Śr. kompletność"]
    alt = spec["alt"] + " " + " ".join(f"{r[0]}: " + ", ".join(f"{hd} {v}" for hd, v in zip(header[1:], r[1:])) + "." for r in rows)
    return table(slide, header, rows, x, y, w, h, alt, size=14, first_col=0.3)


def box(group, x, y, w, h, text, fill=TINT, color=INK, line=ACCENT, size=13, dashed=False):
    s = group.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.color.rgb = line
    s.line.width = Pt(1.25)
    if dashed:
        s.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.08)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, line_text in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        add_runs(p, line_text, size if i == 0 else size - 2, color, bold=(i == 0))
    return s


def arrow(group, x1, y1, x2, y2, color=ACCENT):
    c = group.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = color
    c.line.width = Pt(1.75)
    ln = c.line._get_or_add_ln()
    etree.SubElement(ln, qn("a:tailEnd")).set("type", "triangle")


def schema_solution(slide, x, y, w, h, spec):
    g = slide.shapes.add_group_shape()
    lw, bh, gap = 3.55, 0.85, 0.18
    inputs = [
        ("Kanał 1: wykazy w portalu\nsamorząd, instytucja, firma – zasób CSV „Wykaz AED”", False),
        ("Mapper istniejących źródeł\nzbiory samorządów, API Warszawy, OSM – stan początkowy", True),
        ("Kanał 2: sprzedawca i zarządca\nzgłoszenie → naklejka QR → potwierdzenie miejsca", False),
    ]
    mid = []
    for i, (t, dashed) in enumerate(inputs):
        by = y + i * (bh + gap)
        box(g, x, by, lw, bh, t, fill=WHITE if dashed else TINT, line=MUTED if dashed else ACCENT, size=13, dashed=dashed)
        mid.append(by + bh / 2)
    chain = ["Standard AED\nschema.json", "Walidacja\nbłędy po polsku", "Deduplikacja\nnr seryjny, odległość, nazwa",
             "Wykaz krajowy w portalu\nzbiór ministerstwa: tabela, mapa, API"]
    cx0, cgap = x + lw + 0.7, 0.35
    cw = (x + w - cx0 - cgap * 3) / 4
    ch, cy = 1.25, y + 0.475
    for i, t in enumerate(chain):
        last = i == len(chain) - 1
        box(g, cx0 + i * (cw + cgap), cy, cw, ch, t, fill=ACCENT if last else TINT, color=WHITE if last else INK, size=14)
        if i:
            arrow(g, cx0 + i * (cw + cgap) - cgap, cy + ch / 2, cx0 + i * (cw + cgap), cy + ch / 2)
    for i, m in enumerate(mid):
        arrow(g, x + lw, m - (0.15 if i == 2 else 0), cx0, cy + ch / 2 + (i - 1) * 0.3, MUTED if inputs[i][1] else ACCENT)
    fy = mid[2] - 0.3  # loop box level with channel 2, so the return arrow is horizontal and crosses nothing
    box(g, cx0, fy, x + w - cx0, 0.6,
        "Pętla zwrotna: prośba o potwierdzenie po 183 dniach, przypomnienie 60 dni przed końcem ważności baterii i elektrod",
        fill=WHITE, size=12)
    arrow(g, cx0, fy + 0.4, x + lw, fy + 0.4)
    set_alt(g, spec["alt"])
    return h


def schema_dga(slide, x, y, w, h, spec):
    g = slide.shapes.add_group_shape()
    rows = [
        ("DGA\njuż w portalu", ["Flaga zasobu\n„chronione dane”", "Walidacja kolumn\nw panelu", "Zadanie dzienne\n03:30",
                               "Zasób zbiorczy\nw zbiorze MC", "GET\n/dga-aggregated"], GREY, MUTED),
        ("AED\nnasz fork", ["Flaga zasobu\n„Wykaz AED”", "Walidacja standardem\nAED, po polsku", "Zadanie dzienne 03:45\nlub create_main_aed_resource",
                           "Zasób „Krajowy\nwykaz AED”", "GET /aed-aggregated\n+ publiczny raport"], TINT, ACCENT),
    ]
    lab, gap, rh, rg = 1.35, 0.28, 0.85, 0.25
    bw = (w - lab - gap * 4) / 5
    for r, (label, steps, fill, line) in enumerate(rows):
        ry = y + r * (rh + rg)
        _, tf = textbox(slide, x, ry, lab - 0.1, rh, MSO_ANCHOR.MIDDLE)
        for i, t in enumerate(label.split("\n")):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            add_runs(p, t, 15 if i == 0 else 12, ACCENT if r else MUTED, bold=(i == 0))
        for i, t in enumerate(steps):
            bx = x + lab + i * (bw + gap)
            box(g, bx, ry, bw, rh, t, fill=fill, line=line, size=12)
            if i:
                arrow(g, bx - gap, ry + rh / 2, bx, ry + rh / 2, line)
    set_alt(g, spec["alt"])
    return h


BLOCKS = {"wykres_wykluczen": chart_exclusions, "tabela_pokrycia": coverage_table}


def visual(slide, spec, cfg, rap, src, x, y, w, h):
    """One visual (screenshot, logo, chart, table, schema) with its caption. Returns used height."""
    cap = spec.get("podpis")
    ih = h - (caption_height(cap, w) + 0.08 if cap else 0)
    kind = spec.get("blok")
    if "plik" in spec:
        used = picture(slide, spec, x, y, w, ih)
    elif spec.get("logo"):
        used = logo(slide, cfg, x, y, w, ih, spec)
    elif kind == "tabela":
        used = min(ih, 0.5 * (len(spec["wiersze"]) + 1))  # rows grow to fit; caption goes under the estimate
        table(slide, spec["naglowek"], spec["wiersze"], x, y, w, used, spec["alt"] + " " +
              " ".join(" – ".join(r) + "." for r in spec["wiersze"]), size=12, first_col=0.36)
    elif kind == "schemat_rozwiazania":
        used = schema_solution(slide, x, y, w, ih, spec)
    elif kind == "schemat_dga":
        used = schema_dga(slide, x, y, w, ih, spec)
    else:
        used = BLOCKS[kind](slide, rap, src, x, y, w, ih, spec) if kind == "tabela_pokrycia" else BLOCKS[kind](slide, rap, x, y, w, ih, spec)
    if cap:
        caption(slide, cap, x, y + used + 0.08, w)
    return used


def visuals(slide, items, layout, cfg, rap, src, x, y, w, h):
    n = len(items)
    if layout == "siatka":
        cols = 3 if n > 4 else 2
        rows = math.ceil(n / cols)
        cw, chh = (w - 0.2 * (cols - 1)) / cols, (h - 0.15 * (rows - 1)) / rows
        for i, it in enumerate(items):
            visual(slide, it, cfg, rap, src, x + (i % cols) * (cw + 0.2), y + (i // cols) * (chh + 0.15), cw, chh)
    elif layout == "kolumna" or (layout is None and any("blok" in it for it in items)):
        hh = (h - 0.2 * (n - 1)) / n
        for i, it in enumerate(items):
            visual(slide, it, cfg, rap, src, x, y + i * (hh + 0.2), w, hh)
    else:  # wiersz
        cw = (w - 0.2 * (n - 1)) / n
        for i, it in enumerate(items):
            visual(slide, it, cfg, rap, src, x + i * (cw + 0.2), y, cw, h)


# ---------- slides ----------

def fill(obj, nums):
    if isinstance(obj, str):
        return obj.format_map(nums)
    if isinstance(obj, list):
        return [fill(o, nums) for o in obj]
    if isinstance(obj, dict):
        return {k: (v if k in ("plik", "logo") else fill(v, nums)) for k, v in obj.items()}
    return obj


def set_title(slide, text, x, y, w, h, size, color=INK):
    t = slide.shapes.title
    t.left, t.top, t.width, t.height = Inches(x), Inches(y), Inches(w), Inches(h)
    tf = t.text_frame
    tf.clear()
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    while size > 20 and lines_needed(text, size, w) * size * 1.25 / 72 > h:
        size -= 1
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    p.line_spacing = 1.05
    add_runs(p, text, size, color, bold=True)


def footer(slide, cfg, s, i, total):
    _, tf = textbox(slide, MX, 6.95, 10.6, 0.35, MSO_ANCHOR.MIDDLE)
    add_runs(tf.paragraphs[0], s.get("zrodlo") or cfg["stopka"], 10, MUTED)
    _, tf = textbox(slide, W - MX - 1.2, 6.95, 1.2, 0.35, MSO_ANCHOR.MIDDLE)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    add_runs(p, f"{i} / {total}", 11, MUTED, bold=True)


def title_slide(slide, cfg, s, rap, src):
    name = cfg.get("nazwa_akcji")
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.22), Inches(H))  # single accent edge
    band.fill.solid()
    band.fill.fore_color.rgb = ACCENT
    band.line.fill.background()
    set_alt(band, "")
    _, tf = textbox(slide, MX, 0.6, 6.4, 0.4)
    add_runs(tf.paragraphs[0], "Misja AED – Dane na ratunek · HackNation 2026", 14, ACCENT, bold=True)
    title = f"{name}: wykaz AED w dane.gov.pl" if name else cfg["tytul_roboczy"]
    set_title(slide, title, MX, 1.15, 6.6, 2.4, 34)
    y = 3.65
    if cfg.get("haslo"):
        _, tf = textbox(slide, MX, y, 6.4, 0.5)
        add_runs(tf.paragraphs[0], f"„{cfg['haslo']}”", 20, ACCENT, bold=True)
        y += 0.6
    _, tf = textbox(slide, MX, y, 6.4, 0.9)
    add_runs(tf.paragraphs[0], s["podtytul"], 18, INK)
    bullets(slide, ["W pakiecie: " + "; ".join(s["punkty"]) + "."], MX, y + 1.0, 6.4, 0.95, size=15)
    logo(slide, cfg, MX, 5.75, 2.6, 0.95, {"alt": "Miejsce na logo akcji – logo projektuje zespół."})
    visual(slide, s["wizualne"][0], cfg, rap, src, 7.5, 1.15, W - MX - 7.5, 5.3)


def content_slide(slide, cfg, s, rap, src):
    _, tf = textbox(slide, MX, 0.42, 9, 0.35)
    add_runs(tf.paragraphs[0], s.get("sekcja", "").upper(), 13, ACCENT, bold=True)
    set_title(slide, s["tytul"], MX, 0.8, W - 2 * MX, 1.05, 30)
    top = BODY_TOP
    if s.get("blok_u_gory"):
        b = s["blok_u_gory"]
        visual(slide, b, cfg, rap, src, MX, top, W - 2 * MX, b["wysokosc"])
        top += b["wysokosc"] + 0.25
    items, vis = s.get("punkty", []), s.get("wizualne", [])
    full = W - 2 * MX
    if vis and s.get("uklad") != "pelny":
        tw = full * s.get("podzial", 0.47)
        bullets(slide, items, MX, top, tw, BODY_BOTTOM - top, s.get("numerowane", False), size=18)
        vx = MX + tw + 0.45
        visuals(slide, vis, s.get("uklad_wizualnych"), cfg, rap, src, vx, top, W - MX - vx, BODY_BOTTOM - top)
    elif s.get("kolumny") == 2:
        half = math.ceil(len(items) / 2)
        cw = (full - 0.5) / 2
        size = min(bullets(slide, items[:half], MX, top, cw, BODY_BOTTOM - top, size=16),
                   16)
        bullets(slide, items[half:], MX + cw + 0.5, top, cw, BODY_BOTTOM - top, size=size, min_size=size)
    else:
        bullets(slide, items, MX, top, full * 0.85, BODY_BOTTOM - top, s.get("numerowane", False), size=20)


def build():
    nums, rap, src = numbers()
    cfg = json.loads(CONTENT.read_text(encoding="utf-8"))
    slides = fill(cfg["slajdy"], nums)
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(W), Inches(H)
    layout = prs.slide_layouts[5]  # "Title Only": real title placeholder for screen readers
    for i, s in enumerate(slides, 1):
        slide = prs.slides.add_slide(layout)
        (title_slide if s.get("typ") == "tytulowy" else content_slide)(slide, cfg, s, rap, src)
        footer(slide, cfg, s, i, len(slides))
        slide.notes_slide.notes_text_frame.text = s.get("notatki", "")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"Zapisano {OUT.relative_to(ROOT)} ({len(slides)} slajdów)")


# ---------- check ----------

def check():
    prs = Presentation(OUT)
    sw, sh = prs.slide_width, prs.slide_height
    problems, missing = [], []
    for i, slide in enumerate(prs.slides, 1):
        title = slide.shapes.title
        if title is None or not title.text_frame.text.strip():
            problems.append(f"slajd {i}: pusty tytuł")
        if not slide.notes_slide.notes_text_frame.text.strip():
            problems.append(f"slajd {i}: brak notatek")
        pics = 0
        for sh_ in slide.shapes:
            if sh_.left < 0 or sh_.top < 0 or sh_.left + sh_.width > sw + 10 or sh_.top + sh_.height > sh + 10:
                problems.append(f"slajd {i}: „{sh_.name}” wychodzi poza slajd")
            el = sh_._element.xpath("./*[1]/p:cNvPr")
            descr = el[0].get("descr", "") if el else ""
            if sh_.shape_type == 13:  # picture
                pics += 1
                if not descr:
                    problems.append(f"slajd {i}: obraz bez tekstu alternatywnego")
            if sh_.has_text_frame and "Zrzut do uzupełnienia" in sh_.text_frame.text:
                missing.append(f"slajd {i}: " + sh_.text_frame.text.split("\n")[1])
            if sh_.has_text_frame and sh_.text_frame.text.strip() and sh_.shape_type != 1:
                sizes = [r.font.size.pt for p in sh_.text_frame.paragraphs for r in p.runs if r.font.size]
                if sizes:
                    paras = [p.text for p in sh_.text_frame.paragraphs]
                    need = text_height(paras, max(sizes), Emu(sh_.width).inches, 4, bullet=False)
                    if need > Emu(sh_.height).inches + 0.35:
                        problems.append(f"slajd {i}: tekst „{paras[0][:30]}…” może wychodzić poza pole "
                                        f"({need:.2f} > {Emu(sh_.height).inches:.2f} in)")
        print(f"  slajd {i:2}: {pics} obraz(y) – {title.text_frame.text[:70] if title else '?'}")
    print(f"Slajdów: {len(prs.slides)}")
    print("Zrzuty do uzupełnienia:" if missing else "Wszystkie zrzuty są na miejscu.")
    for m in missing:
        print("  " + m)
    for p in problems:
        print("  PROBLEM: " + p)
    return not problems


if __name__ == "__main__":
    if "--liczby" in sys.argv:
        for k, v in numbers()[0].items():
            print(f"{{{k}}} = {v}")
        sys.exit(0)
    build()
    sys.exit(0 if check() else 1)
