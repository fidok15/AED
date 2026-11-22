"""Input formats of the converter, recognised by content (not by the file extension), each read into one table:
    (columns, [(row_number, {column: text}, geometry or None)], notes)
geometry is a GeoJSON Point {"type": "Point", "coordinates": [lon, lat]} when the format states degrees; any other
position (GML pos, ArcGIS x/y in a planar system) is left as text in a column, which konwerter.py reads with uklady.py.
Pure Python 3.8, standard library only. XML: no DOCTYPE/ENTITY (no external or nested entities); ZIP: bounded reads.
"""
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from . import xlsx

MAX_UNPACKED = 50 * 2 ** 20
LIST_KEYS = ("features", "data", "result", "results", "records", "items", "rows", "value", "elements", "list")
TITLES = {
    "csv": "CSV", "xlsx": "arkusz XLSX", "ods": "arkusz ODS (LibreOffice/OpenOffice)", "geojson": "GeoJSON",
    "json": "JSON (lista obiektów)", "arcgis": "JSON usługi ArcGIS (FeatureServer/MapServer)",
    "kml": "KML (np. Google Moje Mapy)", "kmz": "KMZ (spakowany KML, np. Google Moje Mapy)", "gpx": "GPX (punkty trasy)",
    "gml": "GML / WFS", "html": "tabela HTML (strona WWW)", "docx": "tabela w dokumencie Word (DOCX)",
}
NOT_MACHINE_READABLE = (
    "%s nie jest formatem odczytywalnym maszynowo – zadanie wymaga danych w CSV, XLSX, JSON, GeoJSON albo XML. "
    "Wyeksportuj tabelę z programu, w którym powstał dokument (arkusz → „Zapisz jako” CSV albo XLSX). Jeśli masz "
    "tylko wydruk lub skan, przepisz dane do wzorca wzorzec-aed.xlsx.")


class FormatError(ValueError):
    """Polish message for the provider."""


def local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def safe_xml(raw, what):
    upper = raw.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise FormatError("Plik %s zawiera niedozwolone deklaracje XML (DOCTYPE/ENTITY). Zapisz go ponownie bez nich." % what)
    try:
        return ET.fromstring(raw)
    except ET.ParseError as ex:
        raise FormatError("Pliku %s nie da się odczytać – uszkodzony XML (%s)." % (what, ex))


def zip_part(z, name, budget, what):
    """Bounded read of one member: budget is a one-item list of bytes still allowed after unpacking."""
    try:
        with z.open(name) as f:
            raw = f.read(budget[0] + 1)   # the size in the zip header may lie
    except (KeyError, zipfile.BadZipFile, RuntimeError, NotImplementedError, OSError):
        raise FormatError("Pliku %s nie da się rozpakować (uszkodzony albo zaszyfrowany)." % what)
    budget[0] -= len(raw)
    if budget[0] < 0:
        raise FormatError("Plik %s po rozpakowaniu jest większy niż %d MB." % (what, MAX_UNPACKED // 2 ** 20))
    return raw


# ---------- detection ----------

def detect(data, filename=""):
    """-> format key; raises FormatError with a Polish explanation for formats that are not read."""
    head = data[:2048].lstrip()
    low = head.lower()
    name = filename.lower()
    if data.startswith(b"%PDF"):
        raise FormatError(NOT_MACHINE_READABLE % "PDF")
    if data.startswith((b"\x89PNG", b"\xff\xd8\xff", b"GIF8", b"II*\x00", b"MM\x00*")):
        raise FormatError(NOT_MACHINE_READABLE % "Obraz (skan lub zdjęcie)")
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        raise FormatError("To stary plik Excel/Word (XLS/DOC). Otwórz go w arkuszu i zapisz jako „Skoroszyt programu "
                          "Excel (.xlsx)” albo „CSV UTF-8”, potem wgraj ponownie.")
    if data.startswith(b"PK\x03\x04"):
        try:
            names = set(zipfile.ZipFile(io.BytesIO(data)).namelist())
        except zipfile.BadZipFile:
            return "xlsx" if name.endswith(".xlsx") else "zip?"
        if "xl/workbook.xml" in names:
            return "xlsx"
        if "content.xml" in names and any(n == "mimetype" for n in names):
            return "ods"
        if "word/document.xml" in names:
            return "docx"
        if any(n.lower().endswith(".kml") for n in names):
            return "kmz"
        if any(n.lower().endswith(".shp") for n in names):
            raise FormatError("To spakowany plik Shapefile. Wyeksportuj warstwę (np. w QGIS) jako GeoJSON albo CSV "
                              "z kolumnami współrzędnych i wgraj ponownie.")
        raise FormatError("Archiwum ZIP nie zawiera arkusza, mapy KML ani dokumentu z tabelą. Rozpakuj je i wgraj sam plik.")
    text = _text_head(data)
    if text.startswith(("{", "[")):
        return "json"
    tl = text[:2048].lower()
    if tl.startswith("<?xml") or tl.startswith("<kml") or tl.startswith("<gpx") or re.match(r"<[\w]+:", tl):
        if "<kml" in tl:
            return "kml"
        if "<gpx" in tl:
            return "gpx"
        if "featurecollection" in tl or "<gml" in tl or "featuremember" in tl:
            return "gml"
        if "<html" in tl:
            return "html"
        raise FormatError("Rozpoznano plik XML, ale nie KML, GPX ani GML/WFS. Wyeksportuj dane jako CSV, XLSX albo GeoJSON.")
    if tl.startswith(("<!doctype html", "<html")) or "<table" in tl or (name.endswith((".html", ".htm")) and "<" in tl):
        return "html"
    return "csv"


def _text_head(data):
    for enc in ("utf-8-sig", "utf-16", "cp1250"):
        try:
            return data[:4096].decode(enc, errors="strict" if enc != "cp1250" else "replace").lstrip()
        except UnicodeDecodeError:
            continue
    return ""


# ---------- JSON ----------

def _flatten(obj, prefix, out):
    for k, v in obj.items():
        key = "%s.%s" % (prefix, k) if prefix else str(k)
        if isinstance(v, dict):
            _flatten(v, key, out)
        elif isinstance(v, list):
            out[key] = ", ".join(str(x) for x in v) if all(not isinstance(x, (dict, list)) for x in v) \
                else json.dumps(v, ensure_ascii=False)
        elif isinstance(v, bool):
            out[key] = "true" if v else "false"
        else:
            out[key] = "" if v is None else str(v)
        if len(out) > xlsx.MAX_COLUMNS:
            raise FormatError("Obiekty w pliku JSON mają więcej niż %d pól. Usuń zbędne pola." % xlsx.MAX_COLUMNS)
    return out


def _find_list(obj, depth=0):
    """The list of objects in a JSON document: the document itself, or a list under a known key, or the largest
    list of objects up to three levels down ({"result": {"records": [...]}} in CKAN)."""
    if isinstance(obj, list):
        return obj if obj and all(isinstance(x, dict) for x in obj) else None
    if not isinstance(obj, dict) or depth > 3:
        return None
    for k in LIST_KEYS:
        found = _find_list(obj.get(k), depth + 1)
        if found:
            return found
    lists = [x for x in (_find_list(v, depth + 1) for v in obj.values()) if x]
    return max(lists, key=len) if lists else None


def _geojson_point(g):
    """Point, MultiPoint or a Warsaw-style [[lon, lat]] -> Point with [lon, lat]; None otherwise."""
    if not isinstance(g, dict):
        return None
    c = g.get("coordinates")
    while isinstance(c, list) and c and isinstance(c[0], list):
        c = c[0]
    if g.get("type") in ("Point", "MultiPoint") and isinstance(c, list) and len(c) >= 2:
        return {"type": "Point", "coordinates": c[:2]}
    return None


def read_json(text):
    try:
        doc = json.loads(text)
    except ValueError as ex:
        raise FormatError("Pliku nie da się odczytać jako JSON (%s)." % ex)
    if isinstance(doc, dict) and isinstance(doc.get("features"), list) and doc["features"] \
            and isinstance(doc["features"][0], dict) and "attributes" in doc["features"][0]:
        return _arcgis(doc)
    items = _find_list(doc)
    if not items:
        raise FormatError("W pliku JSON nie ma listy obiektów (np. tablicy „features”, „data” albo „records”).")
    fmt = "geojson" if all("properties" in x or x.get("type") == "Feature" for x in items[:20]) else "json"
    rows, cols = [], {}
    for n, item in enumerate(items, start=1):
        geometry = None
        if fmt == "geojson":
            geometry = _geojson_point(item.get("geometry"))
            props = item.get("properties") if isinstance(item.get("properties"), dict) else {}
            row = _flatten(props, "", {})
            if geometry is None and item.get("geometry"):
                row["geometria"] = json.dumps(item["geometry"])
        else:
            row = _flatten(item, "", {})
        rows.append((n, row, geometry))
        for k in row:
            cols.setdefault(k, None)
    columns = sorted(cols) if fmt == "geojson" else list(cols)
    return fmt, columns, rows, []


def _arcgis(doc):
    sr = doc.get("spatialReference") or {}
    wkid = sr.get("latestWkid") or sr.get("wkid")
    rows, cols = [], {}
    for n, feat in enumerate(doc["features"], start=1):
        row = _flatten(feat.get("attributes") or {}, "", {})
        g = feat.get("geometry") or {}
        geometry = None
        if isinstance(g.get("x"), (int, float)) and isinstance(g.get("y"), (int, float)):
            if wkid == 4326:
                geometry = {"type": "Point", "coordinates": [g["x"], g["y"]]}
            else:   # x = easting in ArcGIS, whatever the system
                row["geometria"] = "SRID=%s;POINT(%r %r)" % (wkid, g["x"], g["y"])
        rows.append((n, row, geometry))
        for k in row:
            cols.setdefault(k, None)
    return "arcgis", list(cols), rows, ["Odczytano warstwę ArcGIS, układ współrzędnych: EPSG:%s." % wkid]


# ---------- XML: KML, GPX, GML ----------

class _Text(HTMLParser):
    """HTML -> text: block elements and <br> become line breaks."""
    BLOCKS = {"br", "p", "div", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "table"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def html_text(value):
    if "<" not in (value or ""):
        return (value or "").strip()
    p = _Text()
    p.feed(value)
    lines = [re.sub(r"\s+", " ", x).strip() for x in "".join(p.parts).split("\n")]
    return "; ".join(x for x in lines if x)


def _kml_rows(root):
    rows, cols = [], {}

    def walk(node, folder):
        for child in node:
            tag = local(child.tag)
            if tag in ("Folder", "Document"):
                name = child.find("{*}name")
                walk(child, (name.text or "").strip() if tag == "Folder" and name is not None else folder)
            elif tag == "Placemark":
                row = {"warstwa": folder} if folder else {}
                geometry = None
                for el in child.iter():
                    t = local(el.tag)
                    if t in ("name", "address", "phoneNumber") and el.text:
                        row.setdefault(t, el.text.strip())
                    elif t == "description":
                        row["description"] = html_text(el.text)
                    elif t == "Data" and el.get("name"):
                        v = el.find("{*}value")
                        row[el.get("name")] = html_text(v.text if v is not None else "")
                    elif t == "SimpleData" and el.get("name"):
                        row[el.get("name")] = html_text(el.text)
                    elif t == "coordinates" and geometry is None and el.text:
                        first = el.text.split()[0].split(",")   # lon,lat[,alt]; a line or polygon -> its first point
                        try:
                            geometry = {"type": "Point", "coordinates": [float(first[0]), float(first[1])]}
                        except (ValueError, IndexError):
                            pass
                rows.append((len(rows) + 1, row, geometry))
                for k in row:
                    cols.setdefault(k, None)
            else:
                walk(child, folder)
    walk(root, "")
    return list(cols), rows


def _gpx_rows(root):
    rows, cols = [], {}
    for wpt in root.iter():
        if local(wpt.tag) not in ("wpt", "rtept"):
            continue
        row = {}
        for el in wpt.iter():
            t = local(el.tag)
            if el is not wpt and el.text and el.text.strip() and not list(el):
                row.setdefault(t, html_text(el.text))
            if t == "link" and el.get("href"):
                row.setdefault("link", el.get("href"))
        try:
            geometry = {"type": "Point", "coordinates": [float(wpt.get("lon")), float(wpt.get("lat"))]}
        except (TypeError, ValueError):
            geometry = None
        rows.append((len(rows) + 1, row, geometry))
        for k in row:
            cols.setdefault(k, None)
    return list(cols), rows


def _gml_rows(root):
    """featureMember / member / wfs:member -> one row: leaf elements by local name; gml:pos / gml:coordinates as
    text in "geometria" (axis order and system decided later from the values; srsName kept when given)."""
    rows, cols = [], {}
    for m in root.iter():
        if local(m.tag) not in ("featureMember", "member", "featureMembers"):
            continue
        features = list(m) if local(m.tag) == "featureMembers" else [m]
        for feat in features:
            row, srs = {}, ""
            for el in feat.iter():
                t = local(el.tag)
                srs = el.get("srsName") or srs
                if t in ("pos", "coordinates") and el.text and "geometria" not in row:
                    pair = el.text.strip().split()[0] if t == "coordinates" else el.text.strip()
                    nums = re.split(r"[\s,]+", pair)[:2]
                    epsg = re.search(r"(\d{4,6})\D*$", srs)
                    row["geometria"] = ("SRID=%s;" % epsg.group(1) if epsg else "") + " ".join(nums)
                elif el is not feat and not list(el) and el.text and el.text.strip():
                    row.setdefault(t, html_text(el.text))
            rows.append((len(rows) + 1, row, None))
            for k in row:
                cols.setdefault(k, None)
    return list(cols), rows


# ---------- grids: HTML table, DOCX table, ODS ----------

class _Tables(HTMLParser):
    """All <table>s as lists of rows; a cell is a list of its text blocks (<p>, <br>, <h4>, <div>…)."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables, self.stack = [], []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.stack.append([])
        elif self.stack and tag == "tr":
            self.stack[-1].append([])
        elif self.stack and tag in ("td", "th") and self.stack[-1]:   # ponytail: colspan ignored (title rows only)
            self.stack[-1][-1].append([[]])
        elif self._cell() is not None and tag in _Text.BLOCKS:
            self._cell().append([])

    def _cell(self):
        return self.stack[-1][-1][-1] if self.stack and self.stack[-1] and self.stack[-1][-1] else None

    def handle_endtag(self, tag):
        if tag == "table" and self.stack:
            self.tables.append(self.stack.pop())

    def handle_data(self, data):
        cell = self._cell()
        if cell is not None:
            cell[-1].append(data)


def _blocks(cell):
    return [b for b in (re.sub(r"\s+", " ", "".join(parts)).strip() for parts in cell) if b]


def grid_from_blocks(table):
    """Rows of cells (each a list of text blocks) -> rows of strings. A column whose every filled cell has the same
    number (2-4) of blocks is split into that many columns (Kraków: name and address in one cell)."""
    rows = [[_blocks(c) for c in r] for r in table]
    width = max((len(r) for r in rows), default=0)
    split = {}
    for i in range(width):
        counts = {len(r[i]) for r in rows[1:] if i < len(r) and r[i]}
        if len(counts) == 1 and 2 <= next(iter(counts)) <= 4:
            split[i] = next(iter(counts))
    out = []
    for k, r in enumerate(rows):
        line = []
        for i in range(width):
            blocks = r[i] if i < len(r) else []
            if i in split:
                if k == 0 or len(blocks) != split[i]:   # header or odd cell: text in the first part
                    line += [" ".join(blocks)] + [""] * (split[i] - 1)
                else:
                    line += blocks
            else:
                line.append(" ".join(blocks))
        out.append(line)
    if split and out:   # name the extra parts after the header cell
        header, pos = out[0], 0
        for i in range(width):
            n = split.get(i, 1)
            for extra in range(1, n):
                header[pos + extra] = "%s (%d)" % (header[pos] or "Kolumna %d" % (i + 1), extra + 1)
            pos += n
    return out


def read_html(text):
    p = _Tables()
    p.feed(text)
    tables = [grid_from_blocks(t) for t in p.tables]
    tables = [t for t in tables if len(t) >= 2 and max(len(r) for r in t) >= 2]
    if not tables:
        raise FormatError("Na stronie HTML nie ma tabeli z danymi. Zapisz listę jako CSV albo XLSX.")
    best = max(tables, key=lambda t: len(t) * max(len(r) for r in t))
    notes = ["Odczytano największą tabelę strony (%d z %d tabel)." % (tables.index(best) + 1, len(tables))] \
        if len(tables) > 1 else []
    return best, notes


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_docx(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    root = safe_xml(zip_part(z, "word/document.xml", [MAX_UNPACKED], "DOCX"), "DOCX")
    tables = []
    for tbl in root.iter(W + "tbl"):
        rows = []
        for tr in tbl.findall(W + "tr"):
            rows.append([[["".join(t.text or "" for t in p.iter(W + "t"))] for p in tc.findall(W + "p")]
                         for tc in tr.findall(W + "tc")])
        tables.append(grid_from_blocks(rows))
    tables = [t for t in tables if len(t) >= 2]
    if not tables:
        raise FormatError("W dokumencie Word nie ma tabeli. Wpisz dane do wzorca wzorzec-aed.xlsx albo zapisz je jako CSV.")
    return max(tables, key=len), ["Odczytano tabelę z dokumentu Word (DOCX)."]


T = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}"
OFFICE = "{urn:oasis:names:tc:opendocument:xmlns:office:1.0}"
TEXT = "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"


def read_ods(data, max_cells):
    z = zipfile.ZipFile(io.BytesIO(data))
    root = safe_xml(zip_part(z, "content.xml", [MAX_UNPACKED], "ODS"), "ODS")
    table = next(root.iter(T + "table"), None)
    if table is None:
        raise FormatError("Plik ODS nie zawiera arkusza.")
    rows, total = [], 0
    for tr in table.iter(T + "table-row"):
        line = []
        for tc in tr:
            if local(tc.tag) not in ("table-cell", "covered-table-cell"):
                continue
            vt = tc.get(OFFICE + "value-type")
            value = tc.get(OFFICE + "date-value", "")[:10] if vt == "date" else \
                "\n".join("".join(p.itertext()) for p in tc.findall(TEXT + "p"))
            if vt in ("float", "percentage", "currency") and tc.get(OFFICE + "value"):
                value = tc.get(OFFICE + "value")
            rep = int(tc.get(T + "number-columns-repeated", "1") or 1)
            if value:   # repeated empty cells (often 1024 to the right) are not expanded
                if len(line) + rep > xlsx.MAX_COLUMNS:
                    raise FormatError("Arkusz ODS ma dane w więcej niż %d kolumnach." % xlsx.MAX_COLUMNS)
                line += [value] * rep
            else:
                line += [""] * min(rep, max(0, xlsx.MAX_COLUMNS - len(line)))
        while line and not line[-1]:
            line.pop()
        if line:
            reps = min(int(tr.get(T + "number-rows-repeated", "1") or 1), 10000)
            total += len(line) * reps
            if total > max_cells:
                raise FormatError("Arkusz ODS ma więcej niż %d komórek. Podziel plik." % max_cells)
            rows += [line] * reps
    return table.get(T + "name", ""), rows


def read_xml_format(fmt, data):
    """kml, kmz, gpx, gml -> (columns, rows, notes)."""
    if fmt == "kmz":
        z = zipfile.ZipFile(io.BytesIO(data))
        kml = next((n for n in z.namelist() if n.lower().endswith(".kml") and "/" not in n), None) or \
            next(n for n in z.namelist() if n.lower().endswith(".kml"))
        data, fmt = zip_part(z, kml, [MAX_UNPACKED], "KMZ"), "kml"
    root = safe_xml(data, fmt.upper())
    columns, rows = {"kml": _kml_rows, "gpx": _gpx_rows, "gml": _gml_rows}[fmt](root)
    if not rows:
        raise FormatError("Plik %s nie zawiera punktów (Placemark / wpt / featureMember)." % fmt.upper())
    return columns, rows, []
