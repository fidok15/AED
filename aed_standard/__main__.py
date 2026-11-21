"""CLI.

    python3 -m aed_standard build [--raw datasets/raw] [--out datasets/out]
    python3 -m aed_standard validate FILE.csv --profil sprzedaz|publikacja [--json]

`validate` prints a Polish report, or with --json the report dict documented in
aed_standard/validate.py (plus "plik"); exit code 1 when the file has errors.
"""
import argparse
import json
import os
import sys

from .build import build_registry, write_outputs
from .schema import PROFILES
from .validate import format_report, validate_csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m aed_standard")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build", help="zbuduj zbiór krajowy z surowych źródeł")
    b.add_argument("--raw", default=os.path.join(ROOT, "datasets", "raw"))
    b.add_argument("--out", default=os.path.join(ROOT, "datasets", "out"))
    v = sub.add_parser("validate", help="sprawdź plik CSV")
    v.add_argument("file")
    v.add_argument("--profil", required=True, choices=PROFILES)
    v.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "build":
        records, pairs, report = build_registry(args.raw)
        for name in write_outputs(args.out, records, pairs, report):
            print(os.path.join(args.out, name))
        print("Rejestr: %d rekordów, eksport dane.gov.pl: %d, do przeglądu: %d"
              % (len(records), report["eksport_dane_gov_pl"]["rekordy"], len(pairs)))
        for error in report["bledy_zrodel"]:
            print("! " + error)
        return 0
    if args.cmd == "validate":
        with open(args.file, "rb") as f:
            _records, report = validate_csv(f.read(), args.profil)
        if args.json:
            report = dict(report, plik=os.path.basename(args.file))
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(format_report(report, os.path.basename(args.file)))
        return 0 if report["poprawny"] else 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
