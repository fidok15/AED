"""First worksheet of an .xlsx file as rows of strings, with the standard library only (zipfile + ElementTree).

Shared strings, inline strings, numbers, booleans; a number in a cell with a date format becomes RRRR-MM-DD.
Guards: total unpacked size is capped (zip bomb), parts must be UTF-8 and may not declare a DOCTYPE or entities.
Pure Python 3.8.
"""
import datetime
import io
import posixpath
import re
import zipfile
import xml.etree.ElementTree as ET

M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
REL = "{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"
# Built-in number formats that show a date (ECMA-376 18.8.30); 18-21 and 45-47 are time only.
DATE_FORMAT_IDS = set(range(14, 18)) | {22} | set(range(27, 37)) | set(range(50, 59))


class XlsxError(ValueError):
    """Unreadable or unsafe file; the message is Polish."""


def _col(ref):
    letters = re.match(r"[A-Z]*", ref or "").group()
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(node):
    """Text of <si> or <is>: plain <t>, or the runs <r><t> (phonetic <rPh> skipped)."""
    if node is None:
        return ""
    parts = node.findall(M + "t") or node.findall(M + "r/" + M + "t")
    return "".join(t.text or "" for t in parts)


def _is_date_format(code):
    code = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", code)   # quoted text, [colour]/[$-415] blocks, escapes
    return bool(re.search(r"[yd]", code, re.I))


def _number(text):
    f = float(text)
    return str(int(f)) if f.is_integer() and abs(f) < 1e15 else repr(f)


def read_rows(data, max_unpacked):
    """-> (sheet_name, rows): rows are lists of strings, empty cells as ''."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise XlsxError("Pliku nie da się otworzyć jako XLSX. Zapisz go w arkuszu jako „Skoroszyt programu Excel (.xlsx)” albo jako CSV.")
    budget = [max_unpacked]

    def part(name):
        try:
            info = z.getinfo(name)
        except KeyError:
            return None
        try:
            with z.open(info) as f:
                raw = f.read(budget[0] + 1)   # bounded read: the size in the zip header may lie
        except (zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError):
            raise XlsxError("Pliku XLSX nie da się rozpakować (uszkodzony, zaszyfrowany albo nietypowo spakowany).")
        budget[0] -= len(raw)
        if budget[0] < 0:
            raise XlsxError("Plik XLSX po rozpakowaniu jest większy niż %d MB. Zapisz pierwszy arkusz jako CSV."
                            % (max_unpacked // 2 ** 20))
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            raise XlsxError("Plik XLSX ma nietypowe kodowanie wewnętrzne. Zapisz go ponownie albo jako CSV.")
        if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:   # no DTD, so no external or nested entities
            raise XlsxError("Plik XLSX zawiera niedozwolone deklaracje XML (DOCTYPE). Zapisz go ponownie w arkuszu.")
        try:
            return ET.fromstring(raw)
        except ET.ParseError:
            raise XlsxError("Plik XLSX ma uszkodzoną część %s. Zapisz go ponownie w arkuszu." % name)

    wb = part("xl/workbook.xml")
    if wb is None:
        raise XlsxError("W pliku XLSX nie ma skoroszytu (xl/workbook.xml).")
    pr = wb.find(M + "workbookPr")
    base = datetime.date(1904, 1, 1) if pr is not None and pr.get("date1904") in ("1", "true") else datetime.date(1899, 12, 30)
    sheet = wb.find(M + "sheets/" + M + "sheet")
    name = sheet.get("name", "") if sheet is not None else ""
    target = "worksheets/sheet1.xml"
    rels = part("xl/_rels/workbook.xml.rels")
    if rels is not None and sheet is not None:
        for rel in rels.iter(REL):
            if rel.get("Id") == sheet.get(R_ID):
                target = rel.get("Target") or target
    path = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join("xl", target))
    ws = part(path)
    if ws is None:
        raise XlsxError("W pliku XLSX nie ma pierwszego arkusza.")

    sst = part("xl/sharedStrings.xml")
    shared = [_text(si) for si in sst.iter(M + "si")] if sst is not None else []
    dates = set()
    styles = part("xl/styles.xml")
    if styles is not None:
        custom = {n.get("numFmtId"): n.get("formatCode", "") for n in styles.iter(M + "numFmt")}
        xfs = styles.find(M + "cellXfs")
        for i, xf in enumerate(xfs.findall(M + "xf") if xfs is not None else []):
            fid = xf.get("numFmtId", "0")
            if (fid.isdigit() and int(fid) in DATE_FORMAT_IDS) or _is_date_format(custom.get(fid, "")):
                dates.add(str(i))

    rows = []
    for row in ws.iter(M + "row"):
        cells = {}
        for pos, c in enumerate(row.findall(M + "c")):
            t, v = c.get("t", "n"), c.find(M + "v")
            text = v.text if v is not None and v.text is not None else ""
            if t == "s":
                value = shared[int(text)] if text.isdigit() and int(text) < len(shared) else ""
            elif t == "inlineStr":
                value = _text(c.find(M + "is"))
            elif t == "b":
                value = "TRUE" if text == "1" else "FALSE" if text == "0" else ""
            elif t == "e":   # #N/A, #REF! and the like are not data
                value = ""
            elif t == "str" or not text:
                value = text
            else:
                try:
                    value = (base + datetime.timedelta(days=int(float(text)))).isoformat() if c.get("s") in dates \
                        else _number(text)
                except (ValueError, OverflowError):
                    value = text
            col = _col(c.get("r"))
            cells[col if col >= 0 else pos] = value
        if cells:
            width = max(cells) + 1
            rows.append([cells.get(i, "") for i in range(width)])
    return name, rows
