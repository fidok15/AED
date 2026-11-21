"""Harvester feed files for dane.gov.pl: the CSV version, zasilanie.xml and zasilanie.md5 in a directory served over HTTPS.

    python -m aed_service.feed --out backend/statics/aed --url https://api.mcod.local/static/aed

AED_FEED_DIR and AED_FEED_URL (both set) make the scheduled cycle rewrite the files after every run.
Old CSV versions stay in the directory.
"""
import argparse
import datetime
import os

import aed_standard

FEED_DIR = os.environ.get("AED_FEED_DIR", "")
FEED_URL = os.environ.get("AED_FEED_URL", "")


def write_feed(csv_bytes, out_dir, base_url):
    """Write the feed for csv_bytes; returns the written file names. The data date is the day the CSV version appeared."""
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, aed_standard.feed.csv_file_name(csv_bytes))
    exists = os.path.exists(csv_path)
    data_date = datetime.date.fromtimestamp(os.path.getmtime(csv_path)) if exists else datetime.date.today()
    files = aed_standard.feed_files(csv_bytes, base_url, data_date)
    for name, content in files.items():
        path = os.path.join(out_dir, name)
        if path == csv_path and exists:
            continue
        with open(path + ".tmp", "wb") as f:
            f.write(content)
        os.replace(path + ".tmp", path)
    return list(files)


def main(argv=None):
    from .app import open_db, publication_csv

    ap = argparse.ArgumentParser(prog="python -m aed_service.feed")
    ap.add_argument("--out", required=True, help="katalog serwowany przez HTTPS")
    ap.add_argument("--url", required=True, help="publiczny adres HTTPS tego katalogu")
    args = ap.parse_args(argv)
    conn = open_db()
    try:
        for name in write_feed(publication_csv(conn), args.out, args.url):
            print(os.path.join(args.out, name))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
