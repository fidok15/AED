"""XML feed for the dane.gov.pl harvester (XSD 1.13, "DATA SOURCES" in the portal admin panel).

The portal downloads `zasilanie.xml` and the `zasilanie.md5` next to it, then creates or updates the dataset and its
resource by `extIdent`. It downloads a resource file again only when the resource URL changes, so every CSV version
gets its own file name derived from its content. Metadata come from schema.json key `zbior_dane_gov_pl`.
"""
import hashlib
import xml.etree.ElementTree as ET

from .schema import SCHEMA

XSD_VERSION = "1.13"
NAMESPACE = "urn:otwarte-dane:harvester:" + XSD_VERSION
XML_NAME = "zasilanie.xml"
MD5_NAME = "zasilanie.md5"


def _text(parent, tag, value):
    el = ET.SubElement(parent, tag)
    el.text = value
    return el


def _translated(parent, tag, texts):
    el = ET.SubElement(parent, tag)
    for lang in ("polish", "english"):
        if texts.get(lang):
            _text(el, lang, texts[lang])


def _flags(parent, flags):
    for name, value in flags.items():
        _text(parent, name, "true" if value else "false")


def harvester_xml(csv_url, data_date):
    """XSD 1.13 document describing the national dataset with one CSV resource at csv_url (https)."""
    meta = SCHEMA["zbior_dane_gov_pl"]
    ET.register_namespace("p", NAMESPACE)
    root = ET.Element("{%s}datasets" % NAMESPACE)
    ds = ET.SubElement(root, "dataset", status="published")
    _text(ds, "extIdent", meta["ext_ident"])
    _translated(ds, "title", meta["tytul"])
    _translated(ds, "description", meta["opis"])
    _text(ds, "updateFrequency", meta["czestotliwosc"])
    categories = ET.SubElement(ds, "categories")
    for code in meta["kategorie"]:
        _text(categories, "category", code)
    resources = ET.SubElement(ds, "resources")
    res_meta = meta["zasob"]
    res = ET.SubElement(resources, "resource", status="published")
    _text(res, "extIdent", res_meta["ext_ident"])
    _text(res, "url", csv_url)
    _translated(res, "title", res_meta["tytul"])
    _translated(res, "description", res_meta["opis"])
    _text(res, "availability", "local")
    _text(res, "dataDate", data_date.isoformat())
    _flags(res, res_meta["flagi"])
    tags = ET.SubElement(ds, "tags")
    for lang, values in meta["tagi"].items():
        for value in values:
            _text(tags, "tag", value).set("lang", lang)
    _flags(ds, meta["flagi"])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def csv_file_name(csv_bytes):
    return "aed_dane_gov_pl-%s.csv" % hashlib.md5(csv_bytes).hexdigest()[:12]


def feed_files(csv_bytes, base_url, data_date):
    """-> {file name: bytes}: the CSV version, zasilanie.xml and zasilanie.md5, to be served under base_url (https)."""
    csv_name = csv_file_name(csv_bytes)
    xml = harvester_xml(base_url.rstrip("/") + "/" + csv_name, data_date)
    return {csv_name: csv_bytes, XML_NAME: xml, MD5_NAME: (hashlib.md5(xml).hexdigest() + "\n").encode("ascii")}
