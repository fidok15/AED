# Tech stack and feature feasibility for the AED data pipeline + emergency web app (HackNation 2026, "Misja AED – Dane na ratunek")

Reading conventions for the report writer:
- A plain citation means the claim was checked against that page during this research session (21 Nov 2026).
- **[not re-fetched]** means the claim comes from the researcher's prior knowledge of the linked official page and was NOT re-opened this session. Numbers carrying this tag (free-tier limits, versions) must be re-checked before being quoted as current.
- Everything under "Inferences" (including all hour estimates) is the researcher's judgement, not a sourced fact.

## 0. Which concrete stack should a small team use in a 24-hour hackathon?

### Takeaway
The dataset is small (tens of thousands of points at most), so the lowest-risk stack is "static files + one tiny write API": a Python/DuckDB pipeline that emits CSV + GeoJSON + `datapackage.json` + DCAT-AP-PL metadata, and a static MapLibre PWA that loads the GeoJSON directly; only crowd confirmations need a database (Supabase). Spend the saved time on the two things the jury will judge: data quality/publishability and a one-screen emergency mode.

### Cited Findings
- HackNation 2026 runs 21–22 November 2026 in Bydgoszcz, teams get 24 hours, there are 15 challenges, organisers are the Ministry of Digital Affairs / GovTech Polska / City of Bydgoszcz — [android.com.pl](https://android.com.pl/tech/1102093-druga-edycja-najwiekszego-w-polsce-hackathonu-wdrozeniowego-odbedzie-sie-21-22-listopada-w-bydgoszczy/), [chip.pl](https://www.chip.pl/2026/11/hacknation-wraca-do-bydgoszczy-w-dobe-powstana-pomysly-na-sprawniejsze-panstwo). The brief said 24–48 h; public sources say 24 h.
- An open-source Polish AED map on OSM data already exists: `openstreetmap-polska/aed-mapa` (archived 7 Apr 2024), superseded by `openaedmap-backend` / `openaedmap-frontend` (OpenAEDMap.org); the old site published ready exports `aed_poland.geojson`, `.csv`, `.ods` — [GitHub aed-mapa](https://redirect.github.com/openstreetmap-polska/aed-mapa), [OSM community thread](https://community.openstreetmap.org/t/mapa-aed-defibrylatory-drobna-nakladka-tematyczna-dla-polski/94736), [OSM wiki: AED data in Poland](https://wiki.osm.org/wiki/AED_data_in_Poland).
- MapLibre GL JS is at v6.x (6.6.0 released August 2026; v6 shipped about eight months after v5, which introduced globe mode); v5 was still receiving point releases (5.23.0 in April 2026) — [MapLibre newsletter Aug 2026](https://maplibre.org/news/2026-09-02-maplibre-newsletter-august-2026/), [MapLibre newsletter Jul 2026](https://maplibre.org/news/2026-08-02-maplibre-newsletter-jul-2026/), [MapLibre GL JS project page](https://maplibre.org/projects/gl-js/).
- OpenFreeMap serves vector basemap styles (e.g. `https://tiles.openfreemap.org/styles/liberty`, also bright/positron) usable directly as the MapLibre `style`; the quick-start mentions no API key; bulk offline download is limited to 3,000 tiles or 50 MB per download with max 4 parallel requests — [OpenFreeMap quick start](https://openfreemap.org/quick_start/).
- dane.gov.pl exposes a live JSON:API (`https://api.dane.gov.pl/1.4/datasets?q=...`), datasets carry licence (CC0 1.0, CC BY 4.0 seen), an openness score 1–5, formats and update frequency — [api.dane.gov.pl live response](https://api.dane.gov.pl/1.4/datasets?q=AED&per_page=10).

### Inferences
Recommended stack (boring on purpose; each line is "use X, skip Y because Z"):

| Block | Use | Skip (and why) |
|---|---|---|
| Pipeline language | Python 3.12 + `uv`, one script per source, `duckdb` + `pandas` | Airflow/Dagster/dbt: no scheduling needed in 24 h |
| OSM ingest | One Overpass query, cached to disk | Geofabrik + osmium/osm2pgsql/QLever: only needed if Overpass is down |
| Messy sources | `pandas.read_excel/read_csv/read_html`; LLM structured outputs for PDFs/BIP pages | Hand-written scrapers per city: too slow |
| Geocoding | GUGiK UUG (`services.gugik.gov.pl/uug`) | Self-hosted Nominatim/Pelias: hours of import; public Nominatim: 1 req/s + ODbL questions |
| Dedup | DuckDB spatial self-join (distance threshold in EPSG:2180) + `rapidfuzz` + union-find | Splink/dedupe: worth it only if labelled pairs/time exist |
| Validation + schema | Frictionless Table Schema (`datapackage.json`) + `frictionless validate` | Great Expectations: heavy setup for one table |
| Storage / serving | Static `aed.geojson` (+ CSV, XLSX) on GitHub Pages / Cloudflare Pages | PostGIS, PMTiles, FlatGeobuf: unnecessary below ~100k points |
| Write path | Supabase (Postgres + REST + RLS) for confirmations/reports only | Custom FastAPI/Hono server unless the LLM wizard needs a secret-holding proxy (then one small FastAPI or edge function) |
| Front end | Vite + React + TypeScript SPA, `vite-plugin-pwa`, MapLibre GL JS + OpenFreeMap | Next.js SSR (no SEO need in emergency flow), WebXR |
| UI kit | shadcn/ui on Radix primitives (or React Aria) + Tailwind | Building accessible dialogs/menus by hand |
| Routing | Deep link to the phone's native maps for turn-by-turn + in-app straight-line compass arrow; optional openrouteservice foot route line | Self-hosting OSRM/Valhalla |

- If the team already knows SvelteKit, it is an equally good choice; the decision should follow team familiarity, not benchmarks.
- Reusing OpenAEDMap/aed-mapa code is a legitimate accelerator but the team's differentiator must be the multi-source pipeline, "accessible now", verification and the provider wizard, since a plain OSM AED map already exists.

### Gaps
- The official text of the "Misja AED – Dane na ratunek" challenge was not found in web search, so the exact evaluation criteria and whether 48 h applies to any track could not be confirmed.
- Licences of OpenFreeMap styles/software were not stated on the quick-start page; the "no limits, no key" promise should be confirmed on [openfreemap.org](https://openfreemap.org/) before relying on it for the demo.
- The count of `emergency=defibrillator` objects in Poland was not retrieved (taginfo not queried), so the "small dataset" claim is an assumption to verify with the first Overpass run.

## 1. Data ingestion: OSM, city lists, and LLM extraction from messy documents

### Takeaway
One Overpass query gets all Polish OSM AEDs in seconds; tabular city files are a `pandas` one-liner each; PDFs and BIP HTML pages are best handled by sending the document to an LLM with a JSON-schema-constrained output, which costs cents for the whole corpus. The main operational risk is the overloaded public Overpass server, so cache the result once and keep a fallback endpoint.

### Cited Findings
- OSM tagging for AEDs: `emergency=defibrillator` with `opening_hours` (important), `access` (important; e.g. `access=customers`; `access=emergency` is deprecated), `phone`, `emergency:phone`, `defibrillator:location` (free text, important) and `defibrillator:location:<lang>`, `indoor`, `locked`, `level`, `level:ref`, `description`, `manufacturer`, `model`, `defibrillator:cabinet`; `defibrillator:code` exists but is flagged ambiguous; UK uses `ref:GB:the_circuit` to link to the national registry — [OSM wiki Tag:emergency=defibrillator](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator).
- Main public Overpass instance (`https://overpass-api.de/api/interpreter`) policy: "No more than 10,000 queries per day and download no more than 1 GB data per day", total processing time capped at 10 minutes/day, send a `User-Agent`/`Referer`, no parallel scripts, wait 30 s after HTTP 429/406; the wiki states "Nowadays this server is overloaded" — [OSM wiki Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API).
- Free alternatives without key: `https://overpass.private.coffee/api/interpreter` (no rate limit; notify for large-scale use), `https://maps.mail.ru/osm/tools/overpass/api/interpreter`; Overpass.ch has a free tier of 10k requests/month at 30 req/min with a key — [OSM wiki Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API).
- Ready-made Polish AED extracts from OSM (GeoJSON/CSV/ODS) were published by the OSM Polska AED map project — [GitHub aed-mapa](https://redirect.github.com/openstreetmap-polska/aed-mapa).
- Country extracts for offline processing are available from Geofabrik (Poland `.osm.pbf`, daily) — [Geofabrik Poland](https://download.geofabrik.de/europe/poland.html) **[not re-fetched]**; `osmium tags-filter` extracts by tag — [osmium-tool manual](https://osmcode.org/osmium-tool/manual.html) **[not re-fetched]**.
- LLM structured extraction (Claude API reference cached 3 Nov 2026): structured outputs via `output_config.format` / `client.messages.parse()` constrain the response to a JSON schema; PDFs are accepted as base64 `document` blocks up to 32 MB per request and 600 pages; the Message Batches API runs asynchronously at 50% cost; list prices per million tokens are Claude Haiku 5.5 $0.10 in / $0.50 out (prompts up to 100K tokens), Claude Sonnet 5.5 $2 / $10, Claude Opus 5.5 $4 / $20 — [Claude pricing](https://platform.claude.com/docs/en/about-claude/pricing), [Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), [Claude PDF support](https://platform.claude.com/docs/en/build-with-claude/pdf-support) (values taken from the Claude API reference bundled with the researcher's tooling; URLs **[not re-fetched]**).
- Citations (page-level provenance for PDFs) cannot be combined with `output_config.format` in the same request — same Claude API reference, [Claude citations](https://platform.claude.com/docs/en/build-with-claude/citations) **[not re-fetched]**.
- Local, non-LLM PDF table extraction options: `pdfplumber` (MIT) — [GitHub pdfplumber](https://github.com/jsvine/pdfplumber) **[not re-fetched]**; Docling (MIT, layout-aware PDF to Markdown/tables) — [GitHub docling](https://github.com/docling-project/docling) **[not re-fetched]**.

### Inferences
- Overpass query to use (returns nodes and the centroid of ways/relations):
  ```
  [out:json][timeout:120];
  area["ISO3166-1"="PL"][admin_level=2]->.pl;
  nwr["emergency"="defibrillator"](area.pl);
  out center tags;
  ```
  Run once, commit the JSON to the repo with the fetch timestamp; never call Overpass from the browser.
- Extraction pattern for PDFs/BIP pages: (1) download and store the raw file with URL + SHA-256 + fetch date (provenance), (2) send the whole document with a strict schema `{records:[{name, address_raw, city, location_description, opening_hours_raw, access_raw, contact, source_page}]}`, (3) never let the model invent coordinates, only transcribe, (4) geocode afterwards, (5) keep `extraction_method=llm` and lower the confidence score until a human or second source confirms.
- Cost estimate: 200 PDF pages at roughly 3k input tokens and 1k output tokens per page is about 0.6 M input + 0.2 M output tokens, i.e. about $0.16 on Haiku 5.5 or about $3.20 on Sonnet 5.5 at the list prices above; cost is negligible, so choose the model on accuracy for Polish tables, not price. Keep each request under 100K tokens on Haiku to stay in the lower price band.
- Latency: synchronous calls return in seconds per document and can be parallelised; the Batch API discount is irrelevant in 24 h because results arrive asynchronously.
- Scanned PDFs (images) should go straight to the LLM's vision path rather than a separate OCR stage; a separate Tesseract step is extra work with worse Polish diacritics handling in the researcher's experience.
- Any provider with JSON-schema structured outputs works; the pipeline should keep the LLM call behind one function so the provider can be swapped.

### Gaps
- No measurement was made of LLM extraction accuracy on real Polish municipal AED PDFs; the team should hand-check a sample of 30 records and report the error rate in the pitch.
- Tokens-per-PDF-page figures were not re-verified this session; the cost estimate is an order-of-magnitude figure.
- Whether QLever's public OSM SPARQL endpoint is a practical fallback was not investigated.

## 2. Normalisation and quality: geocoding, deduplication, opening hours, validation, confidence scoring

### Takeaway
Use the state geocoder (GUGiK UUG) for addresses, a distance-plus-fuzzy-name rule for deduplication, the OSM `opening_hours` grammar as the canonical format (evaluated with `opening_hours.js`), and a Frictionless Table Schema as the single source of truth for validation, the XLSX template and the published schema. The licence question (ODbL versus CC0/CC BY) must be decided before merging OSM records, because record-level conflation with OSM makes the result an ODbL derivative database.

### Cited Findings
Geocoding
- GUGiK Uniwersalna Usługa Geokodowania: `GET https://services.gugik.gov.pl/uug?request=GetAddress&address=Marki, Andersa 1`; also `GetAddressReverse` (`location=POINT(21.020 52.229)&srid=4326`), `GetLocation` (PRNG place names), `GetCity` (by 6-digit TERYT), `GetStreet` (by SIMC), `GetAddresses` (by SIMC + ULIC); input `srid` 4326 or 2180; optional `accuracy` 0.5–1.0 (default 0.6) and `exact_number`; responses are JSON — [UUG description](https://services.gugik.gov.pl/uug/opis.html), [UUG landing page](https://services.gugik.gov.pl/uug/).
- The UUG pages document no rate limit, quota, or licence terms; the service handled 12,900,995 requests in June 2026 (211 million since October 2019) — [UUG landing page](https://services.gugik.gov.pl/uug/).
- GUGiK publishes address data ("Adresy INSPIRE (AD)") on dane.gov.pl under CC BY 4.0, updated twice a year — [api.dane.gov.pl live response](https://api.dane.gov.pl/1.4/datasets?q=AED&per_page=10).
- Public Nominatim: maximum 1 request per second, no bulk geocoding, identify the application — [Nominatim usage policy](https://operations.osmfoundation.org/policies/nominatim/) **[not re-fetched]**. Photon (Apache-2.0) and Pelias (MIT) are self-hostable OSM geocoders — [GitHub photon](https://github.com/komoot/photon), [GitHub pelias](https://github.com/pelias/pelias) **[not re-fetched]**.

Licence mixing (OSM ODbL versus open government data)
- OSMF FAQ: a Derivative Database arises "where you adapt, modify, enhance, correct or extend our data"; a Collective Database is "a collection of otherwise independent databases which are assembled into a collective whole" and its non-OSM parts "you can license under any terms you like"; if you distribute OSM data or a Derivative Database "you must do so under the ODbL license"; a Produced Work (e.g. a map) may use any terms but must attribute and offer the underlying derivative database on request; attribution "© OpenStreetMap" linked to openstreetmap.org/copyright is always required — [OSMF Licence and Legal FAQ](https://osmfoundation.org/wiki/Licence/Licence_and_Legal_FAQ).
- OSMF community guidelines explain when a combination stays "collective" (independent layers that do not modify each other) versus "derivative" (features matched/merged/corrected against OSM) — [Collective Database Guideline](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Collective_Database_Guideline), [Geocoding Guideline](https://osmfoundation.org/wiki/Licence/Community_Guidelines/Geocoding_-_Guideline) **[not re-fetched]**.
- Licences observed on dane.gov.pl datasets include CC0 1.0, CC BY 4.0 and CC BY-NC-SA 4.0 — [api.dane.gov.pl live response](https://api.dane.gov.pl/1.4/datasets?q=AED&per_page=10).
- OSM Polska ran an organised import of Polish public AED data into OSM — [OSM wiki: AED data in Poland](https://wiki.osm.org/wiki/AED_data_in_Poland).

Deduplication
- Splink (UK Ministry of Justice) is MIT-licensed, version 4 is released, and runs probabilistic record linkage/deduplication in Python on a DuckDB backend — [Splink docs](https://moj-analytical-services.github.io/splink), [PyPI splink](https://pypi.org/project/splink). A downstream project notes Splink pulls in `python-igraph` (GPL-2.0) transitively — [GitHub vgi-match](https://github.com/Query-farm/vgi-match).
- Other building blocks: RapidFuzz (MIT) for fuzzy string scores — [GitHub RapidFuzz](https://github.com/rapidfuzz/RapidFuzz); `dedupe` (MIT, active-learning entity resolution) — [GitHub dedupe](https://github.com/dedupeio/dedupe); PostGIS `ST_ClusterDBSCAN(geom, eps, minpoints)` window function — [PostGIS docs](https://postgis.net/docs/ST_ClusterDBSCAN.html); H3 hexagonal index (Apache-2.0), resolution table with cell sizes — [H3 resolution table](https://h3geo.org/docs/core-library/restable/); DuckDB `spatial` extension (`ST_Distance`, `ST_Transform`, `ST_DWithin`) — [DuckDB spatial docs](https://duckdb.org/docs/extensions/spatial/overview) (all **[not re-fetched]**).

Opening hours and "accessible now"
- `opening_hours.js` (npm `opening_hours`) is LGPL-3.0-only since v3.4; API `new opening_hours(value, nominatim_object, mode)` where the Nominatim object carries `lat`, `lon`, `address.country_code`/`state` so that public holidays (PH) and school holidays (SH) resolve; `getState(date)`, `getUnknown(date)`, `getNextChange(date)`; Poland is among countries with PH definitions — [GitHub opening_hours.js](https://github.com/opening-hours/opening_hours.js).
- The grammar is specified on the OSM wiki (e.g. `Mo-Fr 08:00-16:00; Sa 09:00-13:00; PH off`, `24/7`) — [OSM wiki Key:opening_hours](https://wiki.openstreetmap.org/wiki/Key:opening_hours) **[not re-fetched]**.
- Why it matters: in Toronto, of 2,440 public cardiac arrests, 451 were within reach of a registered AED assuming 24/7 access but only 354 when building hours were applied, a 21.5% coverage loss, rising to 31.6% during evenings, nights and weekends; 74% of the 737 AED locations were not open 24 h and 29% were closed on weekends — Sun, Demirtas, Brooks, Morrison, Chan, JACC 2016 via [eScholarship copy](https://escholarship.org/uc/item/8mh548c3), [ScienceDaily summary](https://www.sciencedaily.com/releases/2016/08/160815185601.htm). (One press release gives 767 locations; the abstract figure is 737.)

Validation and schema publication
- Frictionless Framework (MIT) validates CSV/XLSX against a Table Schema / Data Package descriptor (`frictionless validate datapackage.json`) — [Frictionless framework](https://framework.frictionlessdata.io/), [Data Package standard: Table Schema](https://datapackage.org/standard/table-schema/) **[not re-fetched]**.
- Alternatives: Pandera (MIT, DataFrame schemas) — [Pandera docs](https://pandera.readthedocs.io/); Great Expectations (Apache-2.0) — [GitHub great_expectations](https://github.com/great-expectations/great_expectations); W3C CSV on the Web metadata — [CSVW primer](https://www.w3.org/TR/tabular-data-primer/); XLSX dropdown/data-validation rules can be generated with openpyxl — [openpyxl validation](https://openpyxl.readthedocs.io/en/stable/validation.html) (all **[not re-fetched]**).
- dane.gov.pl has a technical standard defining minimum requirements for published public data, and it discourages openness level 1 — [Standard techniczny (PDF)](https://dane.gov.pl/media/ckeditor/2020/06/16/standard-techniczny.pdf) (seen via search summary only).

### Inferences
- Licence strategy (most important design decision; needs a lawyer's confirmation):
  - Option A, "clean core": the dataset published to dane.gov.pl contains only official sources, provider uploads and the team's own crowd confirmations, licensed CC0 or CC BY 4.0. OSM AEDs are shown in the app as a separate layer with attribution and are exported separately under ODbL. OSM must then not be used to correct coordinates or attributes of core records.
  - Option B, "everything ODbL": conflate freely with OSM and publish the merged database under ODbL with attribution. Simpler technically and maximises completeness, but the ministry dataset is then share-alike, which may not fit the portal's usual CC0/CC BY practice.
  - Option A is the safer pitch for a government portal; show Option B as "community edition". Carry a per-record `source` and `licence` column either way so layers can be separated mechanically.
  - Geocoding core records with GUGiK UUG rather than Nominatim avoids any argument that coordinates are OSM-derived.
- Canonical record schema (keep close to OSM keys so export to OSM is trivial): `id` (stable UUID), `name`, `lat`, `lon`, `address`, `teryt_gmina`, `location_description`, `indoor`, `level`, `access` (yes/customers/private/permissive), `locked`, `opening_hours` (OSM syntax), `opening_hours_raw`, `operator`, `contact_phone`, `photo_url`, `source`, `source_url`, `source_record_id`, `osm_id` (optional), `last_verified_at`, `verification_count`, `confidence`, `status` (active/unverified/reported_missing/removed), `licence`.
- Dedup rule that is good enough: transform to EPSG:2180, self-join pairs within 50 m, score `rapidfuzz.token_set_ratio` on normalised name + address, merge when distance < 15 m, or < 50 m with name score above ~80; union-find the pairs; keep the record from the highest-trust source as master and retain all `source_record_id`s. Do not merge when both records carry different `level` or clearly different location descriptions (airports, malls and stations legitimately hold several AEDs). Emit a "possible duplicates" review list for 15–50 m pairs instead of auto-merging.
- Opening hours pipeline: LLM converts raw Polish text ("pn–pt 8–16, sob. 9–13", "całodobowo", "w godzinach pracy urzędu") into OSM syntax; validate by constructing `new opening_hours(...)` in a Node script; on parse failure keep the raw text and set `opening_hours` empty. UI state must be three-valued: open now / closed now (with "opens at ...") / unknown. Rank nearest AEDs by walking time with a penalty for "unknown" and exclude "closed", but always show the nearest closed one greyed out. LGPL is not a problem for an open-source repository.
- Publishing the schema next to an XLSX template: write one `aed.schema.json` (Table Schema, with `enum` constraints and Polish `title`/`description` per field); generate from it (a) `szablon_aed.xlsx` with header row, dropdown validation and a second sheet "Słownik pól", (b) Markdown/HTML documentation, (c) the validator used by the pipeline and by the provider wizard. One file, three artefacts.
- Confidence/freshness score (transparent and explainable, no ML): `confidence = source_trust × freshness × corroboration`, where `source_trust` is a constant per source class (e.g. device operator upload 0.9, municipal register 0.8, OSM with recent `check_date` 0.7, LLM-extracted PDF 0.5, anonymous report 0.3), `freshness = 0.5 ^ (months_since_last_verified / 12)`, and `corroboration` rises with the number of independent sources or on-site confirmations (e.g. `1 − 0.5^(n+1)`). A "reported missing" event multiplies by a strong penalty until re-confirmed. Display as three badges (verified / unverified / stale), not a number.

### Gaps
- UUG response field names, whether results include TERYT/SIMC codes, and any fair-use limit are undocumented on the pages read; test with 100 addresses early.
- Whether dane.gov.pl accepts ODbL as a selectable licence for a dataset was not confirmed.
- The exact CSV formatting rules of the dane.gov.pl technical standard (encoding, separators, coordinate columns) were not read in full.
- No source was found for an established, validated AED-record confidence model; the scoring formula above is a proposal.
- TERYT API access conditions (registration requirement) were not checked — [GUS TERYT API](https://api.stat.gov.pl/Home/TerytApi) **[not re-fetched]**.

## 3. Storage and back end: database choice, API, DCAT-AP metadata and exports

### Takeaway
At this data volume a database is optional for reading: serve versioned static CSV/GeoJSON files and generate the metadata at build time. Use a hosted Postgres (Supabase) only for the write path (confirmations, reports, provider uploads), and express metadata in DCAT-AP-PL 2.1.0, the profile dane.gov.pl itself documents.

### Cited Findings
- DCAT-AP-PL is the Polish application profile of DCAT-AP "used to describe the data recorded in Polish data portals (e.g. dane.gov.pl)"; current version 2.1.0, published 31 May 2022; namespace `https://api.dane.gov.pl/ns/dcatappl#` — [DCAT-AP-PL 2.1.0](https://dane.gov.pl/dcat-ap-pl/), [DCAT-AP-PL introduction](https://dane.gov.pl/dcat-ap-pl/introduction/), [DCAT-AP-PL namespaces](https://dane.gov.pl/dcat-ap-pl/namespaces/).
- dane.gov.pl's API is JSON:API (version string 1.4) with `dataset` objects holding title, institution, formats, `license_name`, openness scores, update frequency and modified date — [api.dane.gov.pl live response](https://api.dane.gov.pl/1.4/datasets?q=AED&per_page=10).
- An EU webinar deck lists `https://api.dane.gov.pl/catalog` as the portal's catalogue endpoint and notes that only metadata, not data, is published automatically in harvesting — [data.europa.eu webinar slides](https://data.europa.eu/sites/default/files/course/20230120_data.europa.eu_webinar_automatic%20data%20publishing.pdf) (via search summary).
- An official "instruction for preparing the XML file" for feeding dane.gov.pl exists (2025, written for property developers' price data), which shows the portal ingests provider-hosted XML feeds — [dane.gov.pl XML feeding instruction (PDF)](https://assets.basehub.com/9f5f0c1c/c1aa71c8f576c4373a5fb048d901eaff/dane.gov.plinstrukcjazasilaniaxmldladeweloperow1.0.620251121v2.pdf) (via search summary; not opened).
- Static-file geodata formats: PMTiles (single-file tile archive read over HTTP range requests, BSD-3) — [Protomaps PMTiles docs](https://docs.protomaps.com/pmtiles/); FlatGeobuf (BSD-2, spatially indexed, streamable) — [flatgeobuf.org](https://flatgeobuf.org/) (both **[not re-fetched]**).
- Supabase offers hosted Postgres with the PostGIS extension, auto-generated REST and row-level security; free plan limits (2 projects, 500 MB database, pausing after a week of inactivity) — [Supabase pricing](https://supabase.com/pricing), [Supabase PostGIS guide](https://supabase.com/docs/guides/database/extensions/postgis) **[not re-fetched]**.
- API frameworks: FastAPI (MIT, automatic OpenAPI) — [FastAPI](https://fastapi.tiangolo.com/); Hono (MIT, runs on edge runtimes) — [Hono](https://hono.dev/) **[not re-fetched]**.

### Inferences
- Decision table: static GeoJSON (choose this for reads) / Supabase Postgres+PostGIS (choose for writes and nearest-neighbour RPC if wanted) / DuckDB spatial (pipeline only) / SQLite-SpatiaLite (no advantage here) / PMTiles or FlatGeobuf (only if points exceed roughly 100k or the basemap must be self-hosted).
- "Open API" for free: publish `/aed.geojson`, `/aed.csv`, `/aed.xlsx`, `/aed.schema.json`, `/datapackage.json`, `/dcat.jsonld` as static URLs with CORS and a dated version path (`/v/2026-11-22/...`); document them in an `openapi.yaml`. Nearest-AED computation happens client-side (haversine over the array; trivial for tens of thousands of points).
- DCAT metadata: generate `dcat.jsonld` with `rdflib` (or hand-written JSON-LD) containing one `dcat:Dataset` (title, description, keywords, publisher, `dct:license`, `dct:accrualPeriodicity`, `dct:spatial` Poland, `dct:modified`) and one `dcat:Distribution` per format with `dcat:downloadURL`, `dct:format`, `dcat:mediaType`. Demonstrating a file that validates against DCAT-AP-PL is a strong "ready for dane.gov.pl" proof even if the team cannot actually publish to the portal during the hackathon.
- Aim for openness level 3+ (CSV/GeoJSON) and add JSON-LD for a higher score, since the portal displays openness per resource.

### Gaps
- No official dane.gov.pl provider manual describing the harvester types (CKAN, XML, DCAT-AP endpoint) and their exact formats was found; the XML instruction found is for a different data domain. The team should ask the challenge mentors which feeding path is expected.
- The mandatory/recommended property lists of DCAT-AP-PL classes were not extracted (the "Classes" page was not read).
- A search of the dane.gov.pl API for `q=AED` returned 70 loose matches and the first page contained no AED dataset; whether any AED dataset is already on the portal is covered by the Polish-data researcher, not here.
- Supabase free-tier numbers were not re-verified.

## 4. Front end and map: library, tiles, clustering, PWA/offline, geolocation and compass, routing, framework, design system

### Takeaway
MapLibre GL JS with OpenFreeMap tiles and built-in GeoJSON clustering covers the map with no keys or accounts; the emergency flow should work even without the map (list + distance + compass arrow from cached points). Compass heading on iOS needs an explicit permission prompt from a tap, and web AR is not available on iPhones, so a 2D arrow is the portable choice.

### Cited Findings
- MapLibre GL JS: current major is v6 (6.6.0 in August 2026), open source (BSD-3-Clause), supports globe and 3D terrain — [MapLibre newsletter Aug 2026](https://maplibre.org/news/2026-09-02-maplibre-newsletter-august-2026/), [MapLibre GL JS project page](https://maplibre.org/projects/gl-js/).
- Clustering is built into MapLibre GeoJSON sources (`cluster: true`), implemented with supercluster (ISC) — [MapLibre cluster example](https://maplibre.org/maplibre-gl-js/docs/examples/cluster/), [GitHub supercluster](https://github.com/mapbox/supercluster) **[not re-fetched]**.
- Tile sources: OpenFreeMap (style URL, no key mentioned, offline bulk download capped at 3,000 tiles/50 MB) — [OpenFreeMap quick start](https://openfreemap.org/quick_start/); Protomaps is a self-hosted model (one PMTiles file on your own storage, no vendor quota) — [Protomaps FAQ](https://protomaps.com/faq); Stadia Maps free tier is reported as 200,000 credits/month and restricted to non-commercial use, MapTiler free tier reported as limited to non-commercial use — [Stadia: what does a free map API cost](https://stadiamaps.com/learn/what-does-a-free-map-api-cost/), [Stadia service limits](https://docs.stadiamaps.com/limits) (secondary/competitor sources; figures unconfirmed on vendor pricing pages).
- Compass: `DeviceOrientationEvent.requestPermission()` must be called from a user gesture (transient activation), resolves to `"granted"`/`"denied"`, works only in secure contexts and is "limited availability" (not Baseline); where the function does not exist, no permission is needed; absolute heading on other browsers comes from the `deviceorientationabsolute` event — [MDN DeviceOrientationEvent.requestPermission](https://developer.mozilla.org/en-US/docs/Web/API/DeviceOrientationEvent/requestPermission_static).
- iOS Safari exposes heading as `webkitCompassHeading` — [Apple DeviceOrientationEvent docs](https://developer.apple.com/documentation/webkitjs/deviceorientationevent) **[not re-fetched]**.
- WebXR `immersive-ar` is not supported in iOS Safari (supported in Chrome on AR-capable Android phones) — [TestMu WebXR browser guide, updated May 2026](https://www.testmuai.com/learning-hub/webxr-compatible-browsers/), [WebKit WebXR tracking bug](https://bugs.webkit.org/show_bug.cgi?id=208988) (secondary source plus tracker; Apple's current position not confirmed from a primary release note).
- Routing services: openrouteservice per-request restrictions are isochrones max 5 locations and 10 intervals per request, foot range up to 20 h; matrix up to 3,500 location pairs; directions up to 50 waypoints — [openrouteservice hosted API restrictions](https://giscience.github.io/openrouteservice/hosted-api-restrictions). Free-plan daily quotas are listed on the HeiGIT account site — [HeiGIT plans](https://account.heigit.org/info/plans) (redirect target; not read).
- Other routers: OSRM demo server usage policy — [OSRM API usage policy](https://github.com/Project-OSRM/osrm-backend/wiki/Api-usage-policy); FOSSGIS-hosted Valhalla demo with isochrones — [GitHub valhalla](https://github.com/valhalla/valhalla); GraphHopper free plan — [GraphHopper pricing](https://www.graphhopper.com/pricing/) (all **[not re-fetched]**).
- Native handoff for turn-by-turn walking: Google Maps URL scheme `https://www.google.com/maps/dir/?api=1&destination=LAT,LON&travelmode=walking` — [Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started); Apple Maps `https://maps.apple.com/?daddr=LAT,LON&dirflg=w` — [Apple Map Links](https://developer.apple.com/library/archive/featuredarticles/iPhoneURLScheme_Reference/MapLinks/MapLinks.html) **[not re-fetched]**.
- PWA/offline: service worker via Workbox / `vite-plugin-pwa` — [vite-plugin-pwa](https://vite-pwa-org.netlify.app/), [Workbox](https://developer.chrome.com/docs/workbox); Screen Wake Lock API keeps the screen on during guidance — [MDN Screen Wake Lock API](https://developer.mozilla.org/en-US/docs/Web/API/Screen_Wake_Lock_API); the Vibration API is not available in Safari — [MDN Vibration API](https://developer.mozilla.org/en-US/docs/Web/API/Vibration_API) (all **[not re-fetched]**).
- Accessible component foundations: Radix Primitives (MIT) — [Radix](https://www.radix-ui.com/primitives); React Aria (Apache-2.0) — [React Aria](https://react-spectrum.adobe.com/react-aria/); shadcn/ui (MIT, copy-in components on Radix) — [shadcn/ui](https://ui.shadcn.com/) **[not re-fetched]**.
- A "GOV.PL Design System" is referenced by the government's architecture pages as the guideline set portals on gov.pl follow, but no public component library or Figma kit was found; GOV.UK Design System is MIT-licensed with coded, documented components — [gov.pl: bloki budowlane rozwiązań](https://www.gov.pl/web/ia/bloki-budowlane-rozwiazan), [GOV.UK Design System](https://design-system.service.gov.uk/).

### Inferences
- MapLibre versus Leaflet: choose MapLibre (vector tiles, rotation to heading, smooth clustering, keyless OpenFreeMap styles). Pin the exact version; if examples or AI assistants produce v4/v5-era code, check the v6 migration notes rather than debugging blindly.
- Offline design: precache the app shell and `aed.geojson` (stale-while-revalidate) with the service worker; do not try to precache basemap tiles (OpenFreeMap's bulk limits and time). Offline fallback screen is the list of nearest AEDs with distance, bearing arrow, address and location description, which needs no tiles at all. Cache API is enough; IndexedDB is unnecessary.
- Compass arrow implementation: bearing from user to AED (great-circle formula) minus device heading; on iOS show a "Włącz kompas" button that calls `requestPermission()`; on Android listen to `deviceorientationabsolute`; always show a non-motion fallback text ("120 m, kierunek północny wschód, ul. Długa 5, hol główny"), which also satisfies WCAG 2.5.4.
- Routing: for the demo, the in-app view shows straight-line distance × ~1.3 as walking estimate and one "Prowadź" button that opens native maps in walking mode. An in-app ORS foot route polyline is a nice-to-have (1–2 h) and needs an API key held in a proxy or accepted as public for the demo.
- Polish Geoportal WMTS (orthophoto) can be offered as an optional raster layer for "which building entrance" context, but must be tested for Web Mercator support first.
- Design language: with no public GOV.PL component kit found, use shadcn/ui and mimic gov.pl visual conventions (typography, blue/white, plain language) rather than claiming compliance with a system that could not be inspected.

### Gaps
- Daily request quotas of the free openrouteservice plan, FOSSGIS Valhalla/OSRM public servers and GraphHopper were not verified.
- Whether GUGiK WMTS services expose an EPSG:3857 tile matrix usable directly in MapLibre was not checked.
- Leaflet's current major version and status in late 2026 were not checked.
- iOS PWA behaviour details (push only after "Add to Home Screen", storage eviction) were not re-verified.
- No public GOV.PL design system component library was located; mentors may have an internal one.

## 5. Emergency-mode UX and WCAG 2.2 AA specifics for a map app

### Takeaway
Published trials suggest that an AED-finder app alone does not reliably beat having no app, while simple spoken direction does, so the emergency mode must behave like a dispatcher: zero setup, one screen, call 112 first, then one unambiguous instruction to the nearest AED that is open now. WCAG 2.2 AA is achievable if the map is treated as an enhancement over a fully accessible list view.

### Cited Findings
Evidence on apps under stress
- AED G-MAP pilot randomised simulation (Neves Briard et al., Prehospital Emergency Care 2019; 52 volunteers, three arms): median time to shock was 10:00 with no assistance, 9:44 with a geolocation app, and 5:23 with verbal direction to the nearest AED; the verbal arm differed significantly from both others (p ≤ 0.01) — [PubMed 30111222](https://www.pubmed.gov/30111222/) (the search summary matched this record to the trial by design and authors; confirm against the article).
- A randomised trial of a mobile AED map found the map shortened travel distance but not retrieval time; 86% (18/21) of controls versus 50% (11/22) of map users reported difficulty finding the AED (the 43-participant design matches Sakai et al., Resuscitation 2011, by the researcher's recollection) — [PMC6303130](https://pmc.ncbi.nlm.nih.gov/articles/PMC6303130) (source of the summary not individually confirmed).
- In a Japanese simulation, an alerting app (AED-SOS) cut time from recognition to AED delivery to 133.6 s versus 202.2 s without it — [PMC8633074](https://pmc.ncbi.nlm.nih.gov/articles/PMC8633074) (via search summary).
- A review of CPR/first-aid apps for laypersons found very few follow BLS guidelines with acceptable usability; cognitive aids can reduce stress when decisions must be made fast; one app ("Defi Now!") includes a compression metronome with spoken breath cues and a confirm step before dialling the emergency number — [JMIR 2014;16(3):e89](https://jmir.org/2014/3/e89/PDF), [JMIR mHealth 2018;6(11):e190](https://mhealth.jmir.org/2018/11/e190), [PMC3978555](https://pmc.ncbi.nlm.nih.gov/articles/PMC3978555).
- The OSM wiki itself instructs to call emergency services immediately before trying to locate an AED — [OSM wiki Tag:emergency=defibrillator](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator).
- Resuscitation guidelines specify chest compressions at 100–120 per minute — [ERC Guidelines](https://cprguidelines.eu/), [AHA CPR & ECC guidelines](https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines) **[not re-fetched]**.

WCAG 2.2
- WCAG 2.2 is a W3C Recommendation (current edition dated 12 December 2024) — [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- 2.5.8 Target Size (Minimum), AA: "The size of the target for pointer inputs is at least 24 by 24 CSS pixels", with exceptions for spacing, equivalent control, inline, user-agent control and essential; the Understanding document says map pins fall under "essential" because pin position mirrors place position, and strongly encourages an equivalent alternative — [Understanding SC 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
- Other criteria directly relevant to this app: 1.4.3 Contrast (4.5:1 text), 1.4.11 Non-text Contrast (3:1 for UI components/graphics), 1.4.10 Reflow, 1.3.4 Orientation (do not lock portrait), 2.5.1 Pointer Gestures (single-pointer alternative to pinch/path gestures), 2.5.7 Dragging Movements (AA, new in 2.2), 2.5.4 Motion Actuation (functions driven by device motion need a UI alternative and must be disableable), 2.4.11 Focus Not Obscured (AA, new in 2.2), 2.3.3 Animation from Interactions (AAA) — [WCAG 2.2](https://www.w3.org/TR/WCAG22/).
- Polish law: the Act of 4 April 2019 on digital accessibility of public entities' websites and mobile apps sets WCAG 2.1 AA (via EN 301 549) as the bar for the public sector; no source showed WCAG 2.2 adopted into Polish law as of November 2026 — [W3C WAI policies: Poland](https://www.w3.org/WAI/policies/poland/), [gov.pl dostępność cyfrowa](https://www.gov.pl/web/dostepnosc-cyfrowa).

### Inferences
- Emergency-mode screen sequence (each screen has one primary action, minimum 56–64 px high full-width buttons, 18 px+ text, high contrast, no login, no cookie wall, no onboarding):
  1. Landing: two buttons only, "ZADZWOŃ 112" (`<a href="tel:112">`) and "ZNAJDŹ AED". No confirm dialog on the 112 link, because the phone's dialler already acts as the confirmation step.
  2. Nearest AED: name, distance in metres and minutes, "otwarte teraz" badge, location description and photo, large arrow, buttons "Prowadź" (native maps) and "Następny AED". Auto-selected; the user never has to read a map.
  3. If two people are present: "Ty uciskaj, druga osoba biegnie po AED" plus "Udostępnij lokalizację AED" (Web Share).
  4. CPR helper: metronome at 110 bpm with audio click, flashing visual and optional vibration (Android only), and spoken prompts via `speechSynthesis` in Polish.
- The trial evidence argues for (a) spoken, dispatcher-like guidance and (b) removing every step between opening the link and seeing a direction. It also supports pitching integration with dispatch (the dispatcher reads the nearest open AED from the same dataset) as the higher-impact use of the data.
- Metronome implementation: schedule clicks with the Web Audio API clock (not `setInterval`) to avoid drift; start only after a tap because browsers block audio autoplay; respect `prefers-reduced-motion` for the visual pulse while keeping the audio.
- WCAG checklist specific to maps: list view with identical information and actions as the first-class alternative (covers 1.1.1 and the 2.5.8 pin exception); on-screen zoom and pan buttons (2.5.1, 2.5.7); full keyboard operation with visible focus (2.1.1, 2.4.7, 2.4.11); status changes announced via `aria-live` ("Najbliższy AED: 120 metrów"); colour never the only carrier of open/closed (1.4.1) so pair with icon + text; contrast of pins against the basemap 3:1 (1.4.11); do not lock orientation (1.3.4); compass arrow has a text fallback and off switch (2.5.4); reflow at 320 px (1.4.10); `lang` attributes for PL/EN/UK strings (3.1.1, 3.1.2).
- Targeting WCAG 2.2 AA exceeds the current Polish legal minimum (WCAG 2.1 AA) and is worth stating explicitly in the pitch; run axe/Lighthouse and one VoiceOver/TalkBack pass and show the result.
- Multilingual: PL default, EN and UK via a small JSON dictionary (the emergency flow has about 20 strings); follow `navigator.language`, with a visible switch. No i18n framework needed.

### Gaps
- No peer-reviewed human-factors guideline specifically quantifying button size or step count for bystander emergency apps was found; the sizes above are design judgement beyond the WCAG minimum.
- Nielsen Norman Group material on stress/emergency UX was not retrieved.
- The attribution of the "distance but not time" trial to Sakai et al. 2011 is from memory; the exact article should be confirmed.
- Whether EN 301 549 v4 (expected to reference WCAG 2.2) has been published or adopted was not established.
- Polish 112 specifics (SMS/app alternatives for deaf users such as Alarm112) were not researched.

## 6. Innovative features: feasibility, how to build quickly, risks, effort and demo impact

### Takeaway
The best innovation-per-hour bets are: three-state "accessible now" filtering, QR/NFC one-tap verification without login, the self-service provider wizard that outputs a dane.gov.pl-ready package, and a coverage-gap map with recommended placements for one city. AR, wallet passes, wearables, SMS and real IoT hardware are poor fits for 24 hours and should appear only as roadmap slides or mocked data.

### Cited Findings
- Optimisation of AED placement is an established operations-research problem: the JACC 2016 Toronto study's spatiotemporal optimisation model (accounting for opening hours) achieved a 25.3% relative increase in actual coverage versus a spatial-only approach — [Sun et al. 2016, eScholarship](https://escholarship.org/uc/item/8mh548c3). The approach has been replicated outside Toronto — [Spatiotemporal AED optimization is generalizable (Aalborg repository)](https://vbn.aau.dk/ws/files/301324733/Spatiotemporal_AED_optimization_is_generalizable.pdf). Earlier foundational work used the maximal covering location problem for public AEDs — Chan et al., Circulation 2013, [doi:10.1161/CIRCULATIONAHA.113.001953](https://www.ahajournals.org/doi/10.1161/CIRCULATIONAHA.113.001953) **[not re-fetched]**.
- Related OR work on drone-delivered AEDs (Boutilier et al., Circulation 2017): on 53,702 Toronto-region arrests, 81 bases and 100 drones were needed to beat median 911 response by 3 minutes; an integrated network needed 39.5% fewer bases and 30.0% fewer drones — [PMC5516537](https://pmc.ncbi.nlm.nih.gov/articles/PMC5516537).
- Solver: PySAL `spopt.locate.MCLP` maximises demand covered within a service distance/time for a fixed number of facilities and can be built from a precomputed cost matrix (`MCLP.from_cost_matrix(cost_matrix, weights, service_radius, p_facilities)`) and solved with a PuLP solver — [spopt MCLP API](https://pysal.org/spopt/generated/spopt.locate.MCLP.html), [spopt MCLP notebook](https://pysal.org/spopt/notebooks/mclp.html).
- Demand data: GUS published Census 2021 resident counts on a 1 km grid for download via the Geostatistics Portal — [GUS Geostatistics Portal news](https://portal.geo.stat.gov.pl/en/news/data-on-residents-in-a-kilometre-grid-census-2021-available-for-download/); the JRC GHS-POP R2023A global population grid is available at 100 m with open, anonymous access — [JRC Data Catalogue GHS-POP](https://data.jrc.ec.europa.eu/dataset/2ff68a52-5b5b-4a22-8f40-c41da8332cfe), [GHSL GHS-POP 2023 page](https://human-settlement.emergency.copernicus.eu/ghs_pop2023.php).
- Isochrones: openrouteservice allows 5 locations per isochrone request with foot ranges up to 20 h — [openrouteservice restrictions](https://giscience.github.io/openrouteservice/hosted-api-restrictions).
- Web AR: `immersive-ar` unavailable in iOS Safari — [TestMu WebXR guide](https://www.testmuai.com/learning-hub/webxr-compatible-browsers/).
- Web NFC (reading/writing tags from JavaScript) is limited to Chrome on Android — [MDN Web NFC API](https://developer.mozilla.org/en-US/docs/Web/API/Web_NFC_API) **[not re-fetched]**.
- Anti-abuse building block: Cloudflare Turnstile, a free CAPTCHA alternative — [Cloudflare Turnstile docs](https://developers.cloudflare.com/turnstile/) **[not re-fetched]**.
- MCP: open protocol with official SDKs for exposing tools/data to LLM clients — [modelcontextprotocol.io](https://modelcontextprotocol.io/) **[not re-fetched]**.
- LLM vision and structured outputs for photo checks and conversational reports use the same API surface as in section 1 — [Claude structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) **[not re-fetched]**.
- The UK links OSM objects to its national AED registry via `ref:GB:the_circuit`, a precedent for a stable national AED identifier printed on stickers — [OSM wiki Tag:emergency=defibrillator](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator).
- LoRaWAN community network for cabinet telemetry: The Things Network fair-use policy — [TTN duty cycle / fair use](https://www.thethingsnetwork.org/docs/lorawan/duty-cycle/) **[not re-fetched]**.

### Inferences
Effort assumes one developer already set up with the core stack; "impact" is the researcher's guess at jury effect.

| Feature | Quick build recipe | Effort (h) | Demo impact | Dependencies | Main risk |
|---|---|---|---|---|---|
| "Accessible now" three-state filter and ranking | `opening_hours.js` on normalised hours; open/closed/unknown badges; rank by walk time | 2–3 | High | Section 2 hours normalisation | Wrong hours give false "open"; show "unknown" honestly |
| Compass arrow + "last 50 m" card | Bearing minus heading; card with photo, floor, location description | 2–3 | High | Geolocation, iOS permission button | Magnetometer inaccuracy indoors; keep text fallback |
| WebXR AR guidance | Skip; Android-only | 6–10 | Medium | AR-capable Android device | Does not run on iPhones, demo fragility |
| QR/NFC sticker, one-tap confirm without login | Sticker encodes `https://app/a/{id}`; plain NDEF URL tags open natively on phones, no Web NFC needed; page shows two buttons "Jest i działa" / "Zgłoś problem"; write to Supabase | 3–4 | High (physical prop on stage) | Supabase table, stable IDs | Spam; mitigate below |
| Anti-vandalism trust scoring | Weight confirmations by geofence (within ~100 m), per-device token and rate limit, Turnstile on reports; a single negative report flags for review, never deletes | 2–3 | Medium | Confirm endpoint | Over-engineering; keep to simple weights |
| Photo verification with a vision model | Upload photo, model returns `{aed_visible, cabinet_type, sign_visible, expiry_text, confidence}`; store as evidence | 3–4 | High | LLM key behind a proxy function | Misread expiry dates; label "AI-read, unverified" and keep the photo |
| Provider wizard (upload → validate → dane.gov.pl package) | Browser parses XLSX/CSV (SheetJS/PapaParse), LLM suggests column mapping, validate against Table Schema, geocode gaps via UUG, show row-level errors, download CSV + `datapackage.json` + DCAT-AP-PL JSON-LD | 6–10 | Very high for a ministry jury | Schema, UUG, dedup function | Scope creep; ship validation + export first, mapping assistance second |
| Coverage-gap analysis + recommended placements | One city: population grid cells as demand, existing open-now AEDs as supply, cost matrix by distance (or ORS foot isochrones), `spopt` MCLP for k new sites; render white spots and top-k candidates; show day versus night | 5–8 | Very high | Population grid, AED set with hours | Candidate-site realism; restrict candidates to public buildings from OSM |
| Embeddable widget | `?embed=1&lat=&lon=&z=` mode plus copy-paste `<iframe allow="geolocation">` snippet | 1 | Medium | Front end | None significant |
| Open API + MCP server | Static endpoints + `openapi.yaml`; MCP server with `nearest_aed(lat, lon, at_time)` and `coverage_at(lat, lon)` | 2–3 | Medium-high (novel, cheap) | Published dataset | Jury unfamiliarity; demo in an assistant in 30 seconds |
| Voice guidance | `speechSynthesis` reading distance/direction in Polish | 1–2 | Medium | Emergency screen | Voice availability varies by device |
| Conversational reporting via LLM | Free text or dictated report converted to a structured report record | 3–4 | Medium | LLM proxy | Speech recognition is unreliable across browsers; accept typed text |
| Guardian reminders | Scheduled email with magic link "AED nadal sprawny? Tak/Nie" updating `last_verified_at` | 2–3 (email) | Medium | Guardian contact field | SMS needs a paid gateway; show as roadmap |
| Web Share of AED location | `navigator.share({title, text, url})` | 0.5 | Low-medium | None | None |
| Wallet passes, widgets, wearables | Roadmap slide only | 6+ each | Low in demo | Developer accounts, certificates | Account approval time |
| IoT cabinet telemetry | Simulated webhook posting "door opened / battery low" to the status table; architecture slide for LoRaWAN/NB-IoT | 1–2 (mock) | Medium | Status table | Real hardware is out of scope |

- Suggested 24 h allocation for a 4-person team: pipeline + schema + exports (person A, ~10 h), emergency PWA (person B, ~10 h), wizard + verification (person C, ~10 h), coverage analysis + pitch/demo data (person D, ~8 h), leaving buffer for integration and accessibility checks.
- QR confirmation design: the QR/NFC payload is just the AED URL. Scanning it at the cabinet is itself weak proof of presence; combine with an optional location check and count confirmations from distinct devices. Printing a few stickers for the demo makes the feature tangible.
- Coverage-gap shortcut if time is short: skip network isochrones; use straight-line distance with a detour factor and a brisk-walk speed, report "share of residents within N minutes round trip of an AED that is open now", and compare day versus night. The day/night contrast reproduces the Toronto finding on Polish data, which is a strong, evidence-backed story.
- The national stable AED identifier (UUID in the dataset, printed on the sticker, cross-referenced to OSM where the licence strategy allows) is itself worth presenting as an innovation, mirroring the UK registry link.

### Gaps
- No source was found evaluating QR/NFC bystander verification or crowd trust-scoring specifically for AED registries; the design is by analogy to general crowdsourcing practice.
- Licence terms for the GUS 1 km census grid and the exact GHS-POP licence name were not confirmed (access is open; check the terms before redistribution of derived products).
- Accuracy of vision models on Polish AED cabinet photos and expiry labels is untested.
- Apple/Google Wallet, home-screen widget and wearable integration requirements were not researched in this session.
- Costs and onboarding time of Polish SMS gateways and NB-IoT connectivity were not researched.
- Chan et al. 2013 details are cited from memory of the paper; quote numbers only after opening it.
