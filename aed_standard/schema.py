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


def required(profile):
    return list(SCHEMA["profile_wymagalnosci"][profile]["wymagane"])


def enum(name):
    return list(BY_NAME[name].get("constraints", {}).get("enum", []))


def blank_record():
    return {name: "" for name in FIELD_NAMES}
