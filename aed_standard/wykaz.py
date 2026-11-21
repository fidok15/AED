"""Wykaz AED: a provider's list of AEDs published as a resource on dane.gov.pl, and the merge of all such
lists into one national list. Modelled on the portal's DGA list (backend/mcod/resources/dga_utils.py):
each provider publishes its own list, the portal checks it and merges all lists into one resource.

Pure Python 3.8, no dependencies. Used by the portal backend (backend/mcod/aed/aed_utils.py).

source (dict) describes the resource a list was read from:
    {"zrodlo": "dane.gov.pl/<dataset id>", "zasob": <resource id>, "tytul": str, "instytucja": str,
     "licencja": "CC0 1.0" | "CC BY 4.0", "data_aktualizacji": "RRRR-MM-DD", "priority": int}
"""
from collections import Counter

from . import schema as S
from .build import publication_export, publication_reasons
from .dedup import LICENCE_ORDER, deduplicate, make_id
from .sources import ODBL, OSM
from .validate import ERROR, WARNING, completeness, issue, validate_csv, validate_records

PROFILE = "publikacja"
# Columns the portal fills when the provider leaves them out (schema: "wypelnia": "system").
SYSTEM = {f["name"] for f in S.FIELDS if f.get("wypelnia") == "system"}
DEFAULT_STATUS = "niepotwierdzony"  # nobody responsible confirmed the device in the national register yet
DEFAULT_ENTERED_BY = "import"
MAX_PROBLEMS = 20  # per list in the public report; the count of all problems is reported too


def _source_report(source, status, rows=0, accepted=0, problems=()):
    problems = sorted(problems, key=lambda p: (p["wiersz"] is not None, p["wiersz"] or 0, p["pole"] or ""))
    return {
        "zasob": source.get("zasob"),
        "tytul": source.get("tytul", ""),
        "instytucja": source.get("instytucja", ""),
        "zrodlo": source["zrodlo"],
        "status": status,  # przyjety | czesciowo | odrzucony
        "wiersze": rows,
        "przyjete": accepted,
        "problemy": list(problems[:MAX_PROBLEMS]),
        "problemy_razem": len(problems),
    }


def rejected(source, message, code="odczyt"):
    """Report for a list that could not be read at all (e.g. the link does not answer)."""
    return _source_report(source, "odrzucony", problems=[issue(None, None, ERROR, code, message)])


def _from_osm(values):
    # A link to an OSM node in powiazane_zrodla is allowed (CLAUDE.md, rule 3); OSM values are not.
    return values.get("zrodlo") == OSM or values.get("licencja") == ODBL


def read_wykaz(data, source, today=None):
    """Read one provider's list (CSV bytes). -> (records, report).

    records: rows without errors, every schema column present, system columns filled in from `source`.
    A file-level error (encoding, separator, unknown or missing column, licence) rejects the whole list;
    a row with an error is skipped and named in the report. The provider's own id_aed is kept.
    """
    licence = source.get("licencja")
    if licence not in S.enum("licencja") or licence == ODBL:
        allowed = ", ".join(x for x in S.enum("licencja") if x != ODBL)
        return [], rejected(source, "Licencja zbioru („%s”) nie pozwala włączyć wykazu do zbioru krajowego. "
                                    "Dozwolone licencje: %s." % (licence or "brak", allowed), "licencja")
    raw, first = validate_csv(data, PROFILE, today)
    file_errors = [p for p in first["problemy"] if p["wiersz"] is None and p["poziom"] == ERROR and p["pole"] not in SYSTEM]
    if file_errors:
        return [], _source_report(source, "odrzucony", first["podsumowanie"]["wiersze"], 0, file_errors)

    problems = [p for p in first["problemy"] if p["wiersz"] is not None and p["kod"] != "brak_wymaganego"]
    filled = []
    for n, rec in enumerate(raw, start=1):
        values = {f: (rec.get(f) or "").strip() for f in S.FIELD_NAMES}
        if _from_osm(values):
            problems.append(issue(n, "zrodlo", ERROR, "dane_osm",
                                  "Wiersz pochodzi z OpenStreetMap (licencja ODbL 1.0), a takich danych nie łączymy z danymi "
                                  "otwieranymi przez ministerstwo. Usuń wiersz albo podaj dane z własnej ewidencji."))
        values["zrodlo"] = source["zrodlo"]
        values["zrodlo_id"] = values["zrodlo_id"] or "%s:%d" % (source.get("zasob"), n)
        values["id_aed"] = values["id_aed"] or make_id(values["zrodlo"], values["zrodlo_id"])
        # The dataset's licence, or the row's own when it is more restrictive (e.g. a CC BY row in a CC0 dataset).
        # An unknown row licence stays, so validation names it.
        row_licence = values["licencja"]
        values["licencja"] = (max(licence, row_licence, key=LICENCE_ORDER.index) if row_licence in LICENCE_ORDER
                              else row_licence or licence)
        values["status"] = values["status"] or DEFAULT_STATUS
        values["data_aktualizacji"] = values["data_aktualizacji"] or source.get("data_aktualizacji", "")
        values["wprowadzajacy_typ"] = values["wprowadzajacy_typ"] or DEFAULT_ENTERED_BY
        values["wprowadzajacy_nazwa"] = source.get("instytucja", "")
        values["powiazane_zrodla"] = ""  # filled by deduplication
        values["kompletnosc"] = str(completeness(values))
        filled.append(values)
    problems += validate_records(filled, PROFILE, today)["problemy"]

    unique = {}
    for p in problems:
        unique.setdefault((p["wiersz"], p["pole"], p["kod"]), p)
    problems = list(unique.values())
    bad = {p["wiersz"] for p in problems if p["poziom"] == ERROR}
    records = []
    for n, values in enumerate(filled, start=1):
        if n not in bad:
            values["_priority"] = source.get("priority", 1)
            values["_copy_values"] = True
            records.append(values)
    status = "przyjety" if records and not bad else "czesciowo" if records else "odrzucony"
    return records, _source_report(source, status, len(filled), len(records), problems)


def merge_wykazy(items, today=None):
    """Merge many lists. items: [(source, data_bytes_or_None, read_error_or_None)].

    -> (national, review_pairs, report). national: deduplicated records that meet the publication profile
    (no private devices, no ODbL); write it with build.to_csv(). A rejected list does not stop the others.
    """
    reports, records, ids = [], [], set()
    for source, data, error in items:
        if data is None:
            reports.append(rejected(source, error or "Nie udało się odczytać pliku zasobu."))
            continue
        recs, rep = read_wykaz(data, source, today)
        for n, rec in enumerate(recs, start=1):
            if rec["id_aed"] in ids:
                old = rec["id_aed"]
                rec["id_aed"] = make_id(rec["zrodlo"], rec["zrodlo_id"])
                attempt = 1
                while rec["id_aed"] in ids:  # the replacement may collide too (same zrodlo_id repeated)
                    attempt += 1
                    rec["id_aed"] = make_id(rec["zrodlo"], "%s#%d" % (rec["zrodlo_id"], attempt))
                rep["problemy"].append(issue(None, "id_aed", WARNING, "powtorzony_id_aed",
                                             "Identyfikator %s występuje już w innym wykazie albo wyżej w tym wykazie; "
                                             "nadano identyfikator %s." % (old, rec["id_aed"])))
                rep["problemy_razem"] += 1
            ids.add(rec["id_aed"])
        records += recs
        reports.append(rep)

    merged, pairs, edges = deduplicate(records)
    for r in merged:
        r["kompletnosc"] = str(completeness(r))
    national = publication_export(merged)
    skipped = Counter(reason for r in merged for reason in publication_reasons(r))
    report = {
        "wykazy": reports,
        "wykazy_razem": len(reports),
        "wykazy_przyjete": sum(1 for r in reports if r["status"] != "odrzucony"),
        "rekordy_z_wykazow": len(records),
        "rekordy_po_deduplikacji": len(merged),
        "polaczenia": len(edges),
        "do_przegladu": len(pairs),
        "rekordy_w_wykazie_krajowym": len(national),
        "pominiete_przy_publikacji": dict(skipped.most_common()),
        "kompletnosc_srednia": round(sum(int(r["kompletnosc"]) for r in national) / float(len(national)), 1) if national else 0,
    }
    return national, pairs, report
