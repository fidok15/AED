"""Address -> position with the state geocoding service of GUGiK (Usługa Uniwersalnego Geokodowania, UUG).

Checked 22.11.2026 against https://services.gugik.gov.pl/uug/opis.html and live calls:
    GET https://services.gugik.gov.pl/uug/?request=GetAddress&address=Kraków, Bosacka 18&srid=4326
    -> {"type": "address" | "street" | "city", "results": {"1": {city, street, number, code, teryt (6 digits, gmina
        without its type digit), simc, ulic, x (lon), y (lat), accuracy, city_accuracy, ...}, ...} or null}
    GET ...?request=GetAddressReverse&location=POINT(lon lat)&srid=4326 -> the nearest address point within 100 m.
srid=4326 gives WGS84 directly (without it: EPSG:2180). No published limits; we pause between calls anyway.
Data: PRG address points, free of charge and without a licence (Prawo geodezyjne art. 40a ust. 2 pkt 1 lit. a,
art. 40c ust. 5); the source must be named (art. 40c ust. 3). Not OSM (CLAUDE.md, rule 3).

Only a match to the address point of the building is a position; a street axis or a town centre is not. Pure 3.8.
"""
import json
import re
import time
import urllib.parse
import urllib.request

URL = "https://services.gugik.gov.pl/uug/"
SOURCE_NOTE = "Położenie z geokodowania adresu (GUGiK, punkt adresowy budynku) – nie miejsce montażu urządzenia."
MIN_ACCURACY = 0.7   # live: "Kraków, os. Szkolne 27" -> 0.74 for the right point; the service's own floor is 0.4
LIMIT = 200          # addresses per conversion
PAUSE = 0.1          # seconds between calls
BUDGET = 40.0        # seconds per conversion: the request must end before the proxy's 60 s


def _fetch(params, timeout=10):
    url = URL + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "aed-konwerter"}), timeout=timeout) as r:
        return json.loads(r.read(2 ** 20).decode("utf-8"))


def _words(text):
    return re.findall(r"\w+", str(text or "").casefold())


def _label(r):
    return re.sub(r"\s+", " ", "%s, %s %s" % (r.get("city"), r.get("street") or "", r.get("number") or ""))


def _key(text):
    return re.sub(r"\s+", "", str(text or "")).casefold()


class Geocoder:
    """One per conversion: cache, pause, address limit and time budget. fetch(params) -> parsed JSON (tests swap it)."""

    def __init__(self, fetch=_fetch, limit=LIMIT, pause=PAUSE, budget=BUDGET):
        self.fetch, self.limit, self.pause, self.budget = fetch, limit, pause, budget
        self.cache, self.calls, self.start = {}, 0, None

    def _call(self, params):
        key = tuple(sorted(params.items()))
        if key in self.cache:
            return self.cache[key]
        if self.start is None:
            self.start = time.time()
        if self.calls >= self.limit:
            raise LookupError("przekroczono limit %d zapytań na jedną konwersję" % self.limit)
        if time.time() - self.start > self.budget:
            raise LookupError("przekroczono czas %d s na jedną konwersję" % self.budget)
        if self.calls:
            time.sleep(self.pause)
        self.calls += 1
        try:
            out = self.fetch(params)
        except Exception as ex:   # network, HTTP, JSON: the row stays without a position, the report says why
            raise LookupError("usługa GUGiK nie odpowiedziała (%s)" % ex.__class__.__name__)
        out = out if isinstance(out, dict) else {}
        self.cache[key] = out
        return out

    def address(self, city, street, number, postcode=""):
        """-> (result, None) with result = {lat, lon, teryt, simc, adres}, or (None, Polish reason)."""
        if not city:
            return None, "brak miejscowości"
        if not number:
            return None, "brak numeru budynku – dopasowanie do ulicy albo miejscowości nie jest położeniem urządzenia"
        query = "%s, %s %s" % (city, street, number) if street else "%s %s" % (city, number)
        try:
            out = self._call({"request": "GetAddress", "address": query, "srid": "4326"})
        except LookupError as ex:
            return None, str(ex)
        results = sorted((out.get("results") or {}).values(), key=lambda r: -float(r.get("accuracy") or 0))
        if out.get("type") != "address" or not results:
            return None, "usługa nie znalazła punktu adresowego „%s”" % query
        top = results[0]
        acc = float(top.get("accuracy") or 0)
        if len(results) > 1 and float(results[1].get("accuracy") or 0) >= acc:
            return None, "kilka punktów adresowych pasuje do „%s” w tym samym stopniu" % query
        # A street written without the first name or title ("Piłsudskiego" for "Marszałka Józefa Piłsudskiego") scores
        # low but ends with the same word; other low scores are not trusted.
        same_end = bool(street) and _words(street)[-1:] == _words(top.get("street"))[-1:]
        if _key(top.get("number")) != _key(number) or str(top.get("city_accuracy")) != "1" or \
                (acc < MIN_ACCURACY and not same_end):
            return None, "dopasowanie niepewne: „%s” → „%s”" % (query, _label(top))
        res, why = _safe(top)
        if res and postcode and top.get("code") and top["code"] != postcode:
            if acc < 1:
                return None, "kod pocztowy %s inny niż w punkcie adresowym „%s” (%s)" % (postcode, _label(top), top["code"])
            res["uwaga"] = "kod pocztowy w pliku %s, w punkcie adresowym %s – sprawdź" % (postcode, top["code"])
        return res, why

    def codes(self, lat, lon):
        """Nearest address point within 100 m of a position -> (result, None) or (None, reason); for TERC/SIMC only."""
        try:
            out = self._call({"request": "GetAddressReverse", "location": "POINT(%s %s)" % (lon, lat), "srid": "4326"})
        except LookupError as ex:
            return None, str(ex)
        results = list((out.get("results") or {}).values())
        if not results:
            return None, "brak punktu adresowego w promieniu 100 m"
        return _safe(results[0])


def _safe(r):
    try:
        return _result(r), None
    except LookupError as ex:
        return None, str(ex)


def _result(r):
    try:
        float(r["x"]), float(r["y"])
    except (KeyError, TypeError, ValueError):
        raise LookupError("niepoprawna odpowiedź usługi GUGiK")
    return {"lat": round(float(r["y"]), 7), "lon": round(float(r["x"]), 7), "teryt": r.get("teryt") or "",
            "simc": r.get("simc") or "", "miejscowosc": r.get("city") or "",
            "adres": _label(r)}
