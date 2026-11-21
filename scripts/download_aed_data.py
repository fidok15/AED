"""Download raw data about Polish AED defibrillators from all known public sources.

Sources:
- dane.gov.pl: every resource of the AED datasets listed in aed_standard/sources.json (via API 1.4),
- OpenAEDMap (OpenStreetMap data, ODbL): country export for Poland,
- Warsaw open data API (requires a free token in WARSAW_API_TOKEN, read from the environment or the .env file
  in the repository root; without it only the API docs are saved).

Files land in datasets/raw/<source>/ and datasets/raw/manifest.json describes each download.

Usage: python3 scripts/download_aed_data.py
"""

import hashlib
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "datasets" / "raw"
USER_AGENT = "AED-open-data-research/1.0"
TIMEOUT = 120

DANE_GOV_API = "https://api.dane.gov.pl/1.4"
REGISTRY_PATH = ROOT / "aed_standard" / "sources.json"  # which dane.gov.pl datasets to fetch: entries with "dane_gov_pl"


def dane_gov_datasets(path):
    """-> {dataset_id: (directory slug = registry id, set of resource ids or None = all resources)}."""
    with open(path, encoding="utf-8") as f:
        sources = json.load(f)["sources"]
    return {s["dane_gov_pl"]["dataset_id"]: (s["id"], set(s["dane_gov_pl"]["resources"]) if "resources" in s["dane_gov_pl"] else None)
            for s in sources if "dane_gov_pl" in s}

OPENAEDMAP_URL = "https://openaedmap.org/api/v1/countries/PL.geojson"

WARSAW_API_URL = "https://dane.um.warszawa.pl/api/action/get_scb_lokalizacja_defibrylatorow"
WARSAW_DOC_URLS = {
    "api_parametry.json": "https://dane.um.warszawa.pl/files/scb_lokalizacja_defibrylatorow_pa.json",
    "api_przyklady.json": "https://dane.um.warszawa.pl/files/scb_lokalizacja_defibrylatorow_pw.json",
}


def load_dotenv(path=ROOT / ".env"):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and not key.strip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def fetch(url, data=None, headers=None):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, **(headers or {})})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read(), response.headers.get_content_type()


def fetch_json(url):
    body, _ = fetch(url)
    return json.loads(body)


def save(path, content, entry, manifest):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    manifest.append({
        **entry,
        "file": str(path.relative_to(OUT_DIR)),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })
    print(f"  saved {path.relative_to(ROOT)} ({len(content)} B)")


def download_dane_gov(manifest, errors):
    for dataset_id, (slug, aed_resource_ids) in dane_gov_datasets(REGISTRY_PATH).items():
        print(f"dane.gov.pl dataset {dataset_id} ({slug})")
        try:
            dataset = fetch_json(f"{DANE_GOV_API}/datasets/{dataset_id}")["data"]
            resources = fetch_json(f"{DANE_GOV_API}/datasets/{dataset_id}/resources")["data"]
        except Exception as error:
            errors.append(f"dane.gov.pl {dataset_id}: {error}")
            continue
        attributes = dataset["attributes"]
        save(OUT_DIR / "dane_gov_pl" / slug / "dataset_metadata.json",
             json.dumps(dataset, ensure_ascii=False, indent=2).encode(),
             {"source": "dane.gov.pl", "dataset_id": dataset_id, "kind": "metadata",
              "url": f"{DANE_GOV_API}/datasets/{dataset_id}"},
             manifest)
        for resource in resources:
            if aed_resource_ids and int(resource["id"]) not in aed_resource_ids:
                continue
            resource_attributes = resource["attributes"]
            url = resource_attributes.get("link") or resource_attributes.get("download_url")
            extension = (resource_attributes.get("format") or "bin").lower()
            path = OUT_DIR / "dane_gov_pl" / slug / f"resource_{resource['id']}.{extension}"
            entry = {
                "source": "dane.gov.pl",
                "dataset_id": dataset_id,
                "dataset_title": attributes.get("title"),
                "resource_id": int(resource["id"]),
                "resource_title": resource_attributes.get("title"),
                "data_date": resource_attributes.get("data_date"),
                "license": attributes.get("license_name"),
                "url": url,
            }
            try:
                content, content_type = fetch(url)
            except Exception as error:
                errors.append(f"dane.gov.pl resource {resource['id']} ({url}): {error}")
                continue
            if content_type == "text/html":
                errors.append(f"dane.gov.pl resource {resource['id']} ({url}): link points to an HTML page, not data")
                continue
            save(path, content, entry, manifest)


def download_openaedmap(manifest, errors):
    print("OpenAEDMap (OpenStreetMap)")
    try:
        content, _ = fetch(OPENAEDMAP_URL)
    except Exception as error:
        errors.append(f"OpenAEDMap: {error}")
        return
    save(OUT_DIR / "openaedmap" / "PL.geojson", content,
         {"source": "openaedmap.org", "url": OPENAEDMAP_URL,
          "license": "ODbL 1.0 (© OpenStreetMap contributors)"},
         manifest)


def download_warsaw(manifest, errors):
    print("Warsaw open data API")
    for name, url in WARSAW_DOC_URLS.items():
        try:
            content, _ = fetch(url)
        except Exception as error:
            errors.append(f"Warsaw docs {url}: {error}")
            continue
        save(OUT_DIR / "warszawa_api" / name, content,
             {"source": "dane.um.warszawa.pl", "kind": "api documentation", "url": url}, manifest)
    token = os.environ.get("WARSAW_API_TOKEN")
    if not token:
        errors.append("Warsaw API: WARSAW_API_TOKEN not set, AED data skipped (register at dane.um.warszawa.pl)")
        return
    try:
        content, _ = fetch(WARSAW_API_URL, data=b"{}",
                           headers={"Authorization": token, "Content-Type": "application/json"})
    except Exception as error:
        errors.append(f"Warsaw API: {error}")
        return
    save(OUT_DIR / "warszawa_api" / "defibrylatory.json", content,
         {"source": "dane.um.warszawa.pl", "url": WARSAW_API_URL, "license": "CC BY 4.0"}, manifest)


def main():
    load_dotenv()
    manifest, errors = [], []
    download_dane_gov(manifest, errors)
    download_openaedmap(manifest, errors)
    download_warsaw(manifest, errors)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(
        json.dumps({"files": manifest, "errors": errors}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\n{len(manifest)} files saved, {len(errors)} problems")
    for error in errors:
        print(f"  ! {error}")


if __name__ == "__main__":
    main()
