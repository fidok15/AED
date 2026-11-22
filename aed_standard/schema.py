"""Loads aed_standard/schema.json once. Everything about fields comes from here."""
import json
import os

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json")

with open(SCHEMA_PATH, encoding="utf-8") as _f:
    SCHEMA = json.load(_f)

FIELDS = SCHEMA["fields"]
FIELD_NAMES = [f["name"] for f in FIELDS]
BY_NAME = {f["name"]: f for f in FIELDS}
PROFILES = sorted(SCHEMA["profile_wymagalnosci"])
TRUE_VALUE = SCHEMA["wartosci_logiczne"]["prawda"]
FALSE_VALUE = SCHEMA["wartosci_logiczne"]["falsz"]
WEIGHTS = {f["name"]: f.get("waga", 0) for f in FIELDS}
# Fields kept in the registry but blank in every open export ("publiczne": false in schema.json).
HIDDEN_FIELDS = [f["name"] for f in FIELDS if f.get("publiczne", True) is False]
PUBLIC_FIELDS = [n for n in FIELD_NAMES if n not in HIDDEN_FIELDS]
# Date fields: "type": "date" (RRRR-MM-DD only) or a string with "dokladnosc_daty" (RRRR-MM-DD or RRRR-MM).
DATE_FIELDS = [f["name"] for f in FIELDS if f.get("type") == "date" or f.get("dokladnosc_daty")]
MONTH_DATE_FIELDS = [f["name"] for f in FIELDS if "miesiac" in f.get("dokladnosc_daty", ())]


# Old spellings accepted on input and turned into the dictionary value ("aliasy" in schema.json).
ALIASES = {f["name"]: f["aliasy"] for f in FIELDS if f.get("aliasy")}


def canonical(name, value):
    """The dictionary value for an accepted old spelling (status "aktywny" -> "zweryfikowany"); else unchanged."""
    return ALIASES.get(name, {}).get(value, value) if isinstance(value, str) else value


def canonical_record(record):
    return {k: canonical(k, v) for k, v in record.items()}


def public_fields():
    return list(PUBLIC_FIELDS)


def hidden_fields():
    return list(HIDDEN_FIELDS)


def weight(name, status=""):
    """Weight of a field in completeness; "waga_dla_statusu" overrides "waga" for that record status."""
    f = BY_NAME[name]
    return f.get("waga_dla_statusu", {}).get(status, f.get("waga", 0))


def required(profile):
    return list(SCHEMA["profile_wymagalnosci"][profile]["wymagane"])


def enum(name):
    return list(BY_NAME[name].get("constraints", {}).get("enum", []))


def blank_record():
    return {name: "" for name in FIELD_NAMES}
