"""Position written in other ways than two WGS84 columns -> (lat, lon) in WGS84. Pure Python 3.8, no dependencies.

Planar systems used in Poland (GRS80 ellipsoid, transverse Mercator):
    PUWG 1992 (EPSG:2180)            central meridian 19°, scale 0.9993,   false easting 500 000, false northing -5 300 000
    PUWG 2000 (EPSG:2176-2179)       zones 5-8 = meridians 15°, 18°, 21°, 24°, scale 0.999923, false easting zone*10^6 + 500 000
    Web Mercator (EPSG:3857/102100)  ArcGIS services; spherical, R = 6 378 137 m
Inverse transverse Mercator: Krüger n-series to n^3 (L. Krüger 1912; as given in "Universal Transverse Mercator
coordinate system – From UTM coordinates to latitude and longitude", Wikipedia, and in C. F. F. Karney, "Transverse
Mercator with an accuracy of a few nanometers", J. Geodesy 85 (2011)). Error far below 1 mm inside Poland; WGS84 and
ETRF2000 (the frame of PUWG) differ by well under 1 m, which this module ignores.
"""
import math
import re

A, F = 6378137.0, 1 / 298.257222101   # GRS80
N_ = F / (2 - F)
A_ = A / (1 + N_) * (1 + N_ ** 2 / 4 + N_ ** 4 / 64)
BETA = (N_ / 2 - 2 * N_ ** 2 / 3 + 37 * N_ ** 3 / 96, N_ ** 2 / 48 + N_ ** 3 / 15, 17 * N_ ** 3 / 480)
DELTA = (2 * N_ - 2 * N_ ** 2 / 3 - 2 * N_ ** 3, 7 * N_ ** 2 / 3 - 8 * N_ ** 3 / 5, 56 * N_ ** 3 / 15)
LAT_PL, LON_PL = (48.9, 55.0), (14.0, 24.3)   # a little wider than the schema bounds; the validator has the last word


def in_pl(lat, lon):
    return LAT_PL[0] <= lat <= LAT_PL[1] and LON_PL[0] <= lon <= LON_PL[1]


def _inverse_tm(easting, northing, lon0, k0, e0, n0):
    xi = (northing - n0) / (k0 * A_)
    eta = (easting - e0) / (k0 * A_)
    xi2 = xi - sum(b * math.sin(2 * j * xi) * math.cosh(2 * j * eta) for j, b in enumerate(BETA, 1))
    eta2 = eta - sum(b * math.cos(2 * j * xi) * math.sinh(2 * j * eta) for j, b in enumerate(BETA, 1))
    chi = math.asin(math.sin(xi2) / math.cosh(eta2))
    lat = chi + sum(d * math.sin(2 * j * chi) for j, d in enumerate(DELTA, 1))
    return math.degrees(lat), lon0 + math.degrees(math.atan2(math.sinh(eta2), math.cos(xi2)))


def puwg1992(easting, northing):
    return _inverse_tm(easting, northing, 19.0, 0.9993, 500000.0, -5300000.0)


def puwg2000(easting, northing):
    zone = int(easting // 1000000)
    return _inverse_tm(easting, northing, 3.0 * zone, 0.999923, zone * 1000000.0 + 500000.0, 0.0)


def mercator(x, y):
    return math.degrees(2 * math.atan(math.exp(y / A)) - math.pi / 2), math.degrees(x / A)


# (name, test on (easting, northing), inverse). Ranges are those of Poland; they do not overlap between systems
# except 1992 with itself swapped, which is why the order of a pair is decided per file (see best_system).
SYSTEMS = (
    ("WGS84 (stopnie)", lambda e, n: in_pl(n, e), lambda e, n: (n, e)),
    ("PUWG 1992 (EPSG:2180)", lambda e, n: 100000 <= e <= 900000 and 100000 <= n <= 800000, puwg1992),
    ("PUWG 2000 (EPSG:2176–2179)", lambda e, n: 5 <= e // 1000000 <= 8 and 250000 <= e % 1000000 <= 750000
     and 5400000 <= n <= 6150000, puwg2000),
    ("Web Mercator (EPSG:3857)", lambda e, n: 1500000 <= e <= 2750000 and 6200000 <= n <= 7400000, mercator),
)
EPSG = {2180: 1, 2176: 2, 2177: 2, 2178: 2, 2179: 2, 3857: 3, 102100: 3, 900913: 3, 4326: 0}


def convert(system, e, n):
    """-> (lat, lon) inside Poland or None."""
    name, test, inverse = SYSTEMS[system]
    if not test(e, n):
        return None
    lat, lon = inverse(e, n)
    return (lat, lon) if in_pl(lat, lon) else None


def best_system(pairs, x_first=True):
    """pairs: [(a, b)] in the order written. -> (system, swapped) giving the most points in Poland, or None.
    swapped=False means a = easting (x, longitude). Ties: x_first decides (GIS order: x/easting first)."""
    best, best_hits = None, 0
    for system in range(len(SYSTEMS)):
        for swapped in ((False, True) if x_first else (True, False)):
            hits = sum(1 for a, b in pairs if convert(system, *((b, a) if swapped else (a, b))))
            if hits > best_hits:
                best, best_hits = (system, swapped), hits
    return best if best_hits else None


DMS_RE = re.compile(r"""^\s*([NSEW])?\s*(\d{1,3}(?:[.,]\d+)?)\s*[°º˚d:\s]\s*(?:(\d{1,2}(?:[.,]\d+)?)\s*['′’:\s]?\s*)?
                        (?:(\d{1,2}(?:[.,]\d+)?)\s*(?:["″”]|'')?)?\s*([NSEW])?\s*$""", re.X | re.I)


def dms(text):
    """52°13'47"N, 52° 13.78', N 52 13 47 -> (degrees, hemisphere letter or ''); None when not DMS."""
    m = DMS_RE.match(text or "")
    if not m or not re.search("[°º˚'′’\"″NSEWnsew]", text):   # bare numbers ("49.78 22.77") are not DMS
        return None
    deg, mins, secs = (float((g or "0").replace(",", ".")) for g in m.group(2, 3, 4))
    if mins >= 60 or secs >= 60:
        return None
    value = deg + mins / 60 + secs / 3600
    hemi = (m.group(1) or m.group(5) or "").upper()
    return (-value if hemi in "SW" and hemi else value), hemi


NUM = r"[-+]?\d+(?:[.,]\d+)?"
WKT_RE = re.compile(r"^\s*(?:SRID=(\d+);)?\s*POINT\s*Z?\s*\(\s*(%s)\s+(%s)(?:\s+%s)?\s*\)\s*$" % (NUM, NUM, NUM), re.I)
PAIR_RE = re.compile(r"^\s*[\[(]?\s*(%s)\s*[,; ]\s*(%s)(?:\s*[,; ]\s*%s)?\s*[\])]?\s*$" % (NUM, NUM, NUM))
DMS_SPLIT_RE = re.compile(r"^(.*?[NS])[\s,;]+(.*[EW].*)$|^(.*?[EW])[\s,;]+(.*[NS].*)$", re.I)


def _num(s):
    return float(s.replace(",", "."))


def point(text):
    """One cell holding a whole position -> (a, b, kind): kind 'xy' (WKT: x/easting first), 'latlon' (DMS with
    letters, already degrees) or 'pair' (two numbers, order unknown). None when the cell is not a position.
    A pair with a decimal comma needs another separator: '52,22 21,01' or '52,22; 21,01'."""
    text = (text or "").strip()
    if not text or len(text) > 80:
        return None
    m = WKT_RE.match(text)
    if m:
        return _num(m.group(2)), _num(m.group(3)), "xy"
    m = DMS_SPLIT_RE.match(text)
    if m:
        p, q = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        p, q = dms(p), dms(q)
        if p and q and p[1] and q[1]:
            lat, lon = (p[0], q[0]) if p[1] in "NS" else (q[0], p[0])
            return lat, lon, "latlon"
    m = PAIR_RE.match(text)   # greedy: "52,22 21,01" -> 52.22 and 21.01; "52.2,21.0" -> 52.2 and 21.0
    return (_num(m.group(1)), _num(m.group(2)), "pair") if m else None
