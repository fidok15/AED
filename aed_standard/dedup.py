"""Deduplication of standard records from many sources (rules: CLAUDE.md, "Standard danych")."""
import base64
import difflib
import hashlib
import math
import re
import unicodedata
from collections import defaultdict

from . import schema as S
from .registry import SUBMISSION, load_registry
from .sources import WARSAW, haversine_m
from .validate import LAT, LON, serial_key

CANDIDATE_M = 50.0
AUTO_M = 15.0
# 0.7 chosen on the real 15-50 m pairs: 0.65 was "Arena Legionowo" vs OSM "Urząd Miasta Legionowo"
# (different places, only the town name shared); true pairs below 0.7 ("UM Miarki" 0.59) go to review.
AUTO_SIMILARITY = 0.7
# Cell sizes in degrees: 0.0005 deg lat ~ 55 m; 0.0008 deg lon >= 51 m up to lat 54.9.
CELL_LAT, CELL_LON = 0.0005, 0.0008

LICENCE_ORDER = S.enum("licencja")  # schema.json lists them from least to most restrictive
NOT_FILLED = {"id_aed", "status", "data_aktualizacji", "wprowadzajacy_typ", "wprowadzajacy_nazwa"} | {
    f["name"] for f in S.FIELDS if f.get("grupa") == "pochodzenie"}
STOPWORDS = {"defibrylator", "defibrylatory", "aed", "ul", "al", "pl", "im", "w", "nr", "i", "the", "ulica", "aleja"}


def make_id(zrodlo, zrodlo_id):
    digest = hashlib.sha1(("%s|%s" % (zrodlo, zrodlo_id)).encode("utf-8")).digest()
    return "AED-" + base64.b32encode(digest).decode("ascii")[:12]


_BY_ZRODLO = None


def _registered(rec):
    """Registry entry of the record's source, for records built outside sources.load_all (no meta fields)."""
    global _BY_ZRODLO
    if _BY_ZRODLO is None:
        _BY_ZRODLO = {s["zrodlo"]: s for s in load_registry()[0]}
    source = _BY_ZRODLO.get(rec["zrodlo"])
    if source is None:
        raise ValueError("Rekord ze źródła „%s” nie ma priorytetu: dodaj źródło do aed_standard/sources.json."
                         % rec["zrodlo"])
    return source


def priority(rec):
    """Lower is better: submission (seller/owner) 0, then the source's priority from sources.json."""
    if "_priority" in rec:
        rank = rec["_priority"]
    else:
        rank = 0 if rec["zrodlo"] == SUBMISSION else _registered(rec)["priority"]
    return (rank, rec["zrodlo"], rec["zrodlo_id"])


def copies_values(rec):
    """False for sources whose values must never be copied into another source's record (ODbL: OSM)."""
    if "_copy_values" in rec:
        return rec["_copy_values"]
    return rec["zrodlo"] == SUBMISSION or _registered(rec)["copy_values_on_merge"]


def normalize(text):
    text = re.sub(r"\baed ?\d+", " ", (text or "").casefold())  # Przemyśl: "Defibrylator (AED 9485) w ..."
    text = unicodedata.normalize("NFKD", text.replace("ł", "l"))
    text = "".join(ch if ch.isalnum() else " " for ch in text if not unicodedata.combining(ch))
    return " ".join(w for w in text.split() if w not in STOPWORDS)


def _ratio(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio() if a and b else 0.0


def similarity(a, b):
    """Name/address similarity 0..1: difflib ratio of normalised names, or of name + address when
    both records have a street (OSM rarely has addresses, so a missing address must not count against)."""
    score = _ratio(normalize(a.get("nazwa")), normalize(b.get("nazwa")))
    if a.get("nazwa_ulicy") and b.get("nazwa_ulicy"):
        full = lambda r: normalize(" ".join((r.get("nazwa") or "", r["nazwa_ulicy"], r.get("nr_budynku") or "")))
        score = max(score, _ratio(full(a), full(b)))
    return round(score, 3)


def classify(d, sim):
    """Spatial rule for a pair from different sources within CANDIDATE_M -> (auto_merge, powod)."""
    if d <= AUTO_M:
        return True, "odleglosc"
    if sim >= AUTO_SIMILARITY:
        return True, "odleglosc_i_podobienstwo"
    return False, "kandydat"


def serial_conflict(a, b):
    """a, b: sets of known serial identities (at most one each)."""
    return bool(a and b and a != b)


def find_candidates(record, others):
    """Probable duplicates of ONE record among `others`, with the batch rules and thresholds.

    -> [{"id_aed", "odleglosc_m", "podobienstwo", "powod", "auto"}], closest first. Same serial
    identity -> powod "numer_seryjny", auto True (same source: "konflikt_zrodel", auto False).
    Other records of the same source, records with a different known serial, and records farther
    than CANDIDATE_M are not returned.
    """
    # ponytail: linear scan (~20 ms on 19k records); use the grid from candidate_pairs if called in bulk.
    key = serial_key(record)
    has_pt = bool(record.get(LAT) and record.get(LON))
    out = []
    for o in others:
        okey = serial_key(o)
        same_source = o.get("zrodlo") == record.get("zrodlo")
        if same_source and not (key and key == okey):
            continue
        d = None
        if has_pt and o.get(LAT) and o.get(LON):
            d = haversine_m(float(record[LAT]), float(record[LON]), float(o[LAT]), float(o[LON]))
        same_serial = bool(key and key == okey)
        if not same_serial and (serial_conflict({key} - {None}, {okey} - {None}) or d is None or d > CANDIDATE_M):
            continue
        sim = similarity(record, o)
        auto, powod = (True, "numer_seryjny") if same_serial else classify(d, sim)
        if same_source:  # as in the batch: never merged within one source, sent to review
            auto, powod = False, "konflikt_zrodel"
        out.append({"id_aed": o.get("id_aed", ""), "odleglosc_m": None if d is None else round(d, 1),
                    "podobienstwo": sim, "powod": powod, "auto": auto})
    out.sort(key=lambda c: (c["odleglosc_m"] is None, c["odleglosc_m"] or 0, c["id_aed"]))
    return out


def candidate_pairs(records):
    """Pairs (i, j, distance_m) of records from different sources within CANDIDATE_M."""
    grid = defaultdict(list)
    pts = {}
    for i, r in enumerate(records):
        if r[LAT] and r[LON]:
            lat, lon = float(r[LAT]), float(r[LON])
            pts[i] = (lat, lon)
            grid[(int(math.floor(lat / CELL_LAT)), int(math.floor(lon / CELL_LON)))].append(i)
    out = []
    for (cy, cx), members in grid.items():
        near = [j for dy in (-1, 0, 1) for dx in (-1, 0, 1) for j in grid.get((cy + dy, cx + dx), ())]
        for i in members:
            for j in near:
                if j > i and records[i]["zrodlo"] != records[j]["zrodlo"]:
                    d = haversine_m(pts[i][0], pts[i][1], pts[j][0], pts[j][1])
                    if d <= CANDIDATE_M:
                        out.append((i, j, d))
    return out


def merge_cluster(members):
    """members sorted by (non-copying last, priority). -> merged record (primary's values, gaps from non-OSM members)."""
    primary = members[0]
    rec = {k: v for k, v in primary.items() if not k.startswith("_")}
    used = [primary]
    for other in members[1:]:
        if not copies_values(other):  # ODbL: never copy OSM values into another source's record
            continue
        filled = False
        for name in S.FIELD_NAMES:
            if name not in NOT_FILLED and not rec[name] and other[name]:
                rec[name] = other[name]
                filled = True
        if filled:
            used.append(other)
    rec["powiazane_zrodla"] = ";".join("%s:%s" % (m["zrodlo"], m["zrodlo_id"]) for m in members[1:])
    rec["licencja"] = max((m["licencja"] for m in used), key=LICENCE_ORDER.index)
    rec["id_aed"] = primary["id_aed"] or make_id(primary["zrodlo"], primary["zrodlo_id"])
    return rec


def deduplicate(records):
    """-> (merged_records, review_pairs, merge_edges).

    review_pairs: dicts with both records and odleglosc_m, podobienstwo, powod.
    merge_edges: (zrodlo_a, zrodlo_b, rule) for each accepted merge.
    """
    n = len(records)
    parent = list(range(n))
    sources = [{records[i]["zrodlo"]} for i in range(n)]
    serials = [{serial_key(r)} - {None} for r in records]  # a cluster holds at most one known serial identity

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    edges = []  # (sort_key, i, j, distance, similarity, rule)
    by_serial = defaultdict(list)
    for i, r in enumerate(records):
        key = serial_key(r)
        if key:
            by_serial[key].append(i)
    for idx in by_serial.values():
        for a in idx:
            for b in idx:
                if a < b:
                    edges.append(((0, 0.0), a, b, None, None, "numer_seryjny"))
    # OSM nodes that reference a Warsaw API id (tag ref:api-um-warszawa-pl) are an explicit link.
    warsaw = {r["zrodlo_id"]: i for i, r in enumerate(records) if r["zrodlo"] == WARSAW}
    for i, r in enumerate(records):
        j = warsaw.get(r.get("_ref_warszawa"))
        if j is not None:
            d = haversine_m(float(r[LAT]), float(r[LON]), float(records[j][LAT]), float(records[j][LON]))
            edges.append(((1, d), i, j, d, similarity(r, records[j]), "ref_warszawa"))
    review = []
    for i, j, d in candidate_pairs(records):
        sim = similarity(records[i], records[j])
        auto, rule = classify(d, sim)
        if auto:
            edges.append(((2, d), i, j, d, sim, rule))
        else:
            review.append((i, j, d, sim, rule))

    merged_edges = []
    for _key, i, j, d, sim, rule in sorted(edges, key=lambda e: e[0]):
        ri, rj = find(i), find(j)
        if ri == rj:
            continue
        if serial_conflict(serials[ri], serials[rj]):
            continue  # two different known serial numbers = two devices, even in one building
        if sources[ri] & sources[rj]:
            # One record per source in a cluster; edges are processed closest first, so the closest wins.
            review.append((i, j, d, sim, "konflikt_zrodel"))
            continue
        parent[rj] = ri
        sources[ri] |= sources[rj]
        serials[ri] |= serials[rj]
        merged_edges.append((records[i]["zrodlo"], records[j]["zrodlo"], rule))

    clusters = defaultdict(list)
    for i in range(n):
        clusters[find(i)].append(i)
    merged, cluster_id = [], {}
    for root, idx in clusters.items():
        # A record whose values may not be copied (ODbL) is never the primary, whatever its priority: it would turn
        # the merged record into ODbL and drop the other sources' device from the export.
        members = sorted((records[i] for i in idx), key=lambda r: (not copies_values(r), priority(r)))
        rec = merge_cluster(members)
        merged.append(rec)
        for i in idx:
            cluster_id[i] = rec["id_aed"]

    pairs = []
    for i, j, d, sim, reason in review:
        # Different known serials are proof of two devices: not offered for review.
        if find(i) == find(j) or serial_conflict(serials[find(i)], serials[find(j)]):
            continue
        pairs.append({"id_aed_a": cluster_id[i], "id_aed_b": cluster_id[j], "rekord_a": records[i], "rekord_b": records[j],
                      "odleglosc_m": None if d is None else round(d, 1), "podobienstwo": sim, "powod": reason})
    pairs.sort(key=lambda p: (p["odleglosc_m"] is None, p["odleglosc_m"] or 0, p["id_aed_a"], p["id_aed_b"]))
    merged.sort(key=lambda r: r["id_aed"])
    return merged, pairs, merged_edges
