# Best-in-class AED registries, locator apps, responder-alert systems and hardware/data innovations — Europe, North America, Australia/NZ (state as of 21 Nov 2026)

Scope note: Asia and Poland are covered by other researchers and are deliberately excluded. Figures are dated explicitly. Numbers marked "own query" were computed by me on 21 Nov 2026 against the public Géo'DAE open-data resource through the data.gouv.fr tabular API; they are reproducible from the cited URL but are not published statistics.

---

## 1. UK: BHF "The Circuit", DefibFinder, GoodSAM

### Takeaway
The Circuit is the clearest Western template for a "one registry, many consumers" architecture: a named human "Guardian" per device, a mandatory 3-monthly email status check, an explicit binary readiness status, and machine sync into every ambulance dispatch system within 60 seconds. It reached about 124,000 registered defibrillators by October 2026, but registration is still voluntary and its operators themselves say data quality depends on tens of thousands of humans answering emails.

### Cited Findings

**Governance, launch, scale**
- The Circuit was built by the British Heart Foundation (BHF) with the Association of Ambulance Chief Executives, the UK ambulance services, Resuscitation Council UK and St John Ambulance. BHF invited ambulance services in 2018; West Midlands and Scottish Ambulance Service went live July/August 2019; rollout to all 14 UK ambulance services completed September 2022. — [O'Sullivan et al., Resuscitation Plus 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Before The Circuit (2015 Warwick feasibility study) only about 32,000 of an estimated 100,000 UK AEDs were known to ambulance services, with "no formal processes in place to update the data and in some cases the data were several years old". — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- As of 31 Dec 2023: 82,108 AEDs registered by a named Guardian (64,478 England, 7,410 Scotland, 7,162 Wales, 3,058 Northern Ireland); 55,235 Guardians; 453 organisation accounts; about 54% of registered AEDs were previously unknown to ambulance services. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- 100,000th defibrillator registered in 2024; 124,000 registered as of October 2026. — [BHF, Restart a Heart Day 2026](https://www.bhf.org.uk/what-we-do/news-from-the-bhf/news-archive/2026/october/restart-a-heart-day-2026-building-a-nation-of-lifesavers)
- BHF reported in July 2026 that over 120,000 defibrillators are registered but are not evenly distributed ("defibrillator deserts"). — [BHF, July 2026](https://www.bhf.org.uk/what-we-do/news-from-the-bhf/news-archive/2026/july/uk-defibrillator-deserts-2026)
- Registration is not mandatory in the UK (unlike France and Italy); "it is likely that tens of thousands of AEDs in the UK remain unregistered". — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Funding: BHF sole funder 2018 to April 2023; since April 2023 NHS England, Resuscitation Council UK and St John Ambulance co-fund. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

**Guardian model and freshness mechanism**
- A "Guardian" is the individual responsible for looking after an AED; the owner (e.g. a supermarket chain) can differ from the Guardian (local store staff). Guardians must create an account before registering; afterwards they "receive regular automated emails every 3 months prompting them to update their record". — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Reminders are email only, every three months; pad-expiry emails are sent separately; email notifications cannot be turned off. For organisation accounts, escalation emails go to the organisation administrator when a Guardian does not complete required status checks. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- Statuses: "Emergency Ready" (deployable) versus removed from service (Guardian uses "Remove from service" with a reason; ambulance service then will not send anyone to it). — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- Post-use loop: when the ambulance service marks a defib as deployed, the Guardian gets an email, must check that the device is back and consumables are replaced, then log in and set status back to Emergency Ready. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- A Primary Guardian can invite Supporting Guardians ("Ask for support"); Guardians can consent to be contacted by other Guardians. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- Emergency readiness is snapshotted at noon each day; on 31 Dec 2023, 87% were emergency-ready and 13% out of service. 71.4% were classed publicly accessible, the rest restricted access (only people with access to the building). — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

**Data fields**
- Registration collects: address, location and surroundings; brand, model, serial number; times and dates when the defib is accessible plus date ranges when it is not (e.g. closures); pad expiry dates; confirmation that the device shows its ready signal; cabinet access code if applicable; a map marker when there is no postal address (phone boxes, posts, fences). — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- The FAQ states that old "location codes" are obsolete and recommends writing a what3words address plus a contact number on the cabinet. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- Only fixed-location AEDs are registered; mobile AEDs carried by police/fire first responders are not. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Bulk upload for organisations uses an Excel template; mandatory columns are Guardian email, location name, postcode and first address line; records move through states Draft (Not Nominated), Draft (Nominated), Action Required, Potential Duplicate, Pending, Registered; duplicates are flagged by matching postcode. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- The system is designed to prevent bots from registering AEDs; it runs on Microsoft Azure SQL (Azure UK South), is UK GDPR compliant and ISO 27001 aligned; ambulance administrators get Power BI reports. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

**Feed to ambulance services**
- The database synchronises with ambulance computer-aided dispatch (CAD); a newly registered AED is on every ambulance service CAD within 60 seconds, versus up to three weeks of manual upload before. Three CAD vendors are integrated (Cleric, MIS Emergency Systems, Hexagon). — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- CAD searches a radius of 200–1,600 m (minimum 200 m in all 14 services) for AEDs in emergency-ready status; the call handler then asks a second bystander to fetch it, giving location details and, if needed, the cabinet unlock code verbally. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- From go-live to 31 Dec 2023 ambulance services reported 113,811 AED "deployments" (a bystander sent to fetch one). Services in England and Wales can see each other's AED data across boundaries. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

**Public face: DefibFinder**
- DefibFinder (defibfinder.uk) shows the ten nearest AEDs to a postcode, only where the Guardian consents; 95.7% of Guardians consent. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Changes usually appear on DefibFinder within about an hour; some (e.g. decommissioning) update overnight. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- OpenStreetMap has a UK-only key `ref:GB:the_circuit` holding the 32-character Circuit ID, i.e. a documented cross-reference between the volunteer map and the official registry. — [OSM wiki](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator)

**GoodSAM (UK)**
- GoodSAM alerts the closest available verified responders; if nobody accepts, the alert passes to the next nearest; responders are directed to the nearest defibrillator. — [GoodSAM Cardiac](https://goodsamapp.org/cardiac)
- London/East Midlands observational study (Eur Heart J Acute Cardiovasc Care, 2022): survival was higher when an alert was accepted than when none was sent (reported as roughly doubled chance of survival); the study did not measure what responders did on scene. — [NIHR Evidence alert](https://evidence.nihr.ac.uk/alert/more-people-survived-cardiac-arrest-first-aiders-goodsam-alert/)
- AACE published a national framework to strengthen GoodSAM cardiac responder alerting across the UK, with a focus on responder support after incidents (date not confirmed in my retrieval). — [AACE](https://aace.org.uk/?p=20262261)
- RCUK's 2025 "Systems saving lives" guideline says systems that dispatch first responders should be linked to AED registries (i.e. The Circuit), and ambulance services should implement and evaluate dispatcher-assisted public-access AED systems linked to registries. — [RCUK 2025 Guidelines](https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/systems-saving-lives-guidelines)

### Inferences
- The three transferable Circuit mechanisms are: (a) a named accountable person per device, (b) a readiness status that expires socially (quarterly prompt plus escalation to the organisation), and (c) a deployment-triggered "please re-check" loop that closes the gap after each real use. All three are implementable with email/SMS and no hardware.
- The record-state machine used for bulk upload (Draft, Action Required, Potential Duplicate, Pending, Registered) is a ready-made model for a national aggregator ingesting heterogeneous sources: imported records can exist in the registry before a responsible person has claimed and confirmed them.
- Per-record consent to public display (95.7% opt-in) shows that a dual-visibility model (dispatch sees everything; public sees consented subset) costs very little coverage.
- The Circuit is not published as open data; its public face is a lookup tool. A Polish open dataset on dane.gov.pl would go further than the UK on openness.

### Gaps
- Table 2 of the Circuit paper (full list of data fields) and the supplementary email process flow were not machine-readable in the full text I retrieved; the field list above comes from the public FAQ.
- The FAQ does not say whether a defibrillator is automatically downgraded if a Guardian ignores reminders; I could not confirm an auto-expiry rule.
- No public API or bulk download of The Circuit data was found.
- No source found confirming a production GoodSAM-to-Circuit data integration; the Circuit paper only describes sharing data with responder-alert platforms as "an evolution of the programme".
- Current UK-wide GoodSAM responder counts not found.

---

## 2. Denmark: Hjertestarter.dk (TrygFonden) and Hjerteløber

### Takeaway
Denmark has the oldest national AED registry (2007, in all dispatch centres since 2010) and the highest density of app-dispatched volunteers (61,540 active, about 1,020 per 100,000, mid-2026); 72% of its roughly 26,400 registered AEDs are accessible around the clock. Its own research shows why 24/7 access is the key data field — and the 2026 HeartRunner randomised trial is a sobering result: activation doubled bystander defibrillation but did not improve 30-day survival where ambulances arrive in about 7 minutes.

### Cited Findings
- Denmark became the first country with a national AED registry in 2007; it has been available to all five national Emergency Medical Dispatch Centres since 2010. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- The Danish AED Network is run with TrygFonden and is integrated with EMS dispatch centres, which can direct responders to the nearest AED; volunteers are alerted through the TrygFonden Hjerteløber app. — [hjertestarter.dk (English)](https://www.hjertestarter.dk/english)
- 26,393 AEDs registered in TrygFonden's Hjertestarter-Netværk as of September 2025, of which 18,970 (72%) are accessible 24/7; in March 2025 the figures were 25,956 and 18,565 (72%). — [TrygFonden status, Sept 2025](https://hjertestarter.dk/-/media/files/tal-og-fakta-om-hjerteloeber/250930-trygfonden-hjerteloeber-status-september-2025.pdf)
- A Danish news article (date not confirmed in my retrieval) citing hjertestarter.dk reports just under 5,000 AEDs located in companies and reachable only in opening hours, and 1,542 locked in or protected by a lock/access code. — [sn.dk](https://www.sn.dk/art6624098/koebenhavn-kommune/indland/nye-anbefalinger-skal-sikre-bedre-adgang-til-hjertestartere)
- Registration is done by the owner/responsible person online and is described as taking about 10 minutes; registered AEDs become visible to dispatch centres on a 1-1-2 call; owners are urged to mount units outdoors so they work around the clock. — [TrygFonden flyer](https://edit.hjertestarter.dk/-/media/downloads/ny-flyer--register-din-hjertestarter.pdf)
- 61,540 active hjerteløbere as of 30 June 2026 (about 1,020 per 100,000 inhabitants). "Active" means the system can locate the volunteer from a recently updated position. — [TrygFonden status, June 2026](https://edit.hjertestarter.dk/-/media/files/tal-og-fakta-om-hjerteloeber/260630-trygfonden-hjerteloeber-status-juni-2026.pdf)
- Volunteers must be 18+; no special competencies are required; the figure equals about 1.3% of Danish adults. — [The Local, Aug 2026](https://www.thelocal.dk/20260818/what-are-denmarks-heart-runners-and-how-can-you-register-as-one)
- Copenhagen registry study (Karlsson et al., Resuscitation 2019): of 2,500 arrests, 22.6% (566) were covered by a registered AED within 200 m route distance, but fewer than 50% of those AEDs (276) were accessible at the time of arrest; offices, schools and sports facilities each lost more than 50% of coverage. Bystander defibrillation tripled and 30-day survival nearly doubled when the nearest AED was accessible versus inaccessible. — [Karlsson et al. 2019](https://research.regionh.dk/da/publications/automated-external-defibrillator-accessibility-is-crucial-for-bys/)
- Bornholm physical audit (Resuscitation 2022): of registered AEDs inspected, 181 (81.9%) were publicly accessible and functional; 40 (18.1%) were not, mainly because of expired electrodes, failed self-tests or accessibility problems. — [PubMed 35618078](https://pubmed.ncbi.nlm.nih.gov/35618078/)
- HeartRunner randomised trial (Capital Region of Denmark; presented at ESC Congress, 31 Aug 2026): 2,060 suspected OHCA calls randomised 1:1 to volunteer activation plus standard response versus standard response. 30-day survival: 15% vs 17% where estimated responder arrival was under 3 minutes (0–358 m; p=0.42), 13% vs 14% in the 3–9 minute stratum (360–1,080 m; p=0.43). In the 3–9 minute stratum bystander CPR rose from 75% to 86% and bystander defibrillation from 6% to 14% (both p<0.0001). No safety concerns. Ambulance response time in the area was about 7 minutes. Funded by Novo Nordisk Foundation and TrygFonden. — [ESC press release](https://www.escardio.org/news/press/press-releases/activation-of-community-first-responders-did-not-improve-short-term-survival-after-cardiac-arrest/)

### Inferences
- Denmark publishes "share of AEDs accessible 24/7" as a headline KPI next to the raw count. A Polish dataset could adopt the same two-number framing (registered vs. reachable right now).
- The HeartRunner result suggests responder apps add most value where EMS is slow (rural areas), which is an argument for prioritising data quality and outdoor 24/7 access in low-density regions rather than treating a responder app as a universal fix.
- Danish dispatch-distance bands (about 360 m ≈ 3 min; about 1,080 m ≈ 9 min) are usable defaults for "is there a reachable AED" map logic.

### Gaps
- I found no public description of the Hjertestarter.dk data model, of owner reminder/verification rules, or of an open-data/API offering.
- The exact AED count for 2026 was not found (latest confirmed: September 2025).
- A search snippet attributed "5,636 active hjerteløbere" to the March 2026 status report, which conflicts with 61,540 in June 2026; I could not open the PDF to resolve it and treat it as a parsing error.
- No peer-reviewed HeartRunner publication found yet (only the ESC presentation).

---

## 3. Continental Europe: Netherlands, Sweden, DACH, France, Italy

### Takeaway
France is the only large Western country with a legally mandatory, schema-defined, openly published national AED dataset (Géo'DAE: 192,453 records on 21 Nov 2026, refreshed several times a day), and its schema is the best starting template for dane.gov.pl — but its own data shows the weak spots of declaration-without-verification (60% of records carry an "Mo-Su off" opening-hours value, only 4% have a photo). Sweden demonstrates the strictest freshness rule (confirm every 6 months or be deleted), the Netherlands the densest responder network, and Germany what fragmentation looks like.

### Cited Findings

**France — Géo'DAE (legal obligation + open data + schema)**
- Géo'DAE is the national AED database created under the law of 28 June 2018 on cardiac defibrillators; all AED operators ("exploitants") must declare their devices and characteristics via geodae.atlasante.fr. The Arrêté of 29 Oct 2019 (JO 13 Nov 2019) governs operation; its annexes 1–3 define which fields are public vs. restricted, and only public fields are released as open data. — [data.gouv.fr dataset page](https://www.data.gouv.fr/fr/datasets/geodae-base-nationale-des-defibrillateurs/)
- Publisher Atlasanté; Licence Ouverte 2.0; CSV (about 77–81 MB) and JSON (about 210–220 MB); dataset created 30 Sep 2021; declared update frequency "severalTimesADay"; CSV last modified 21 Nov 2026 11:00 UTC. — [data.gouv.fr dataset page](https://www.data.gouv.fr/fr/datasets/geodae-base-nationale-des-defibrillateurs/); [dataset API metadata](https://www.data.gouv.fr/api/1/datasets/geodae-base-nationale-des-defibrillateurs/)
- The schema ("schema-dae", title "DAE") is a Frictionless Table Schema authored by the Ministère des Solidarités et de la Santé, legal source Décret n° 2018-1259 of 27 Dec 2018; created 2020-01-01; current version 1.0.8, last modified 2026-03-20; listed in the national schema catalogue under the label "Socle Commun des Données Locales"; ships valid/invalid example CSVs and custom SIREN/SIRET validators. — [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json); [GitLab repo](https://gitlab.com/arsante/atlasante/schema-dae)
- Schema v1.0.8 has 45 fields, 16 of them required: `nom`, `lat_coor1`, `long_coor1`, `acc`, `acc_lib`, `tel1`, `etat_fonct`, `fab_rais`, `modele`, `num_serie`, `dermnt`, `expt_siren`, `expt_rais`, `expt_tel1`, `expt_email`, `dispo_horaires`. — [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json)
- Full field list of v1.0.8, grouped (R = required) — [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json):
  - Identity and position: `nom` (R, name given to the AED); `lat_coor1` (R, number, -90..90); `long_coor1` (R, number, -180..180; national reference system or WGS 84, decimal point).
  - Address: `adr_num` (street number); `adr_voie` (street type and name); `com_cp` (postcode, 5 digits); `com_insee` (INSEE commune code); `com_nom` (commune name).
  - Access: `acc` (R, enum `Intérieur` / `Extérieur`); `acc_lib` (R, boolean, free access); `acc_pcsec` (boolean, security post present); `acc_acc` (boolean, public reception desk present); `dae_mobile` (boolean, fixed vs mobile device); `acc_etg` (floor, e.g. "0 ou -1"); `acc_complt` (free text, e.g. "at the end of the corridor, in a recess on the right").
  - Photos: `photo1`, `photo2` (URL to jpg/png/gif; wide shot recommended so the device is visible in its surroundings; must be free of rights).
  - Availability: `dispo_horaires` (R; "formatted according to the OpenStreetMap opening_hours standard", regex-validated, e.g. `Mo-Fr 08:00-18:00; Sa 09:00-12:00`, `24/7`, `OFF`, `PH ...`); `disp_complt` (free-text availability complement).
  - Site contact: `tel1` (R, E.164 with French prefixes), `tel2`, `site_email`.
  - Lifecycle/status: `date_instal` (ISO date); `etat` (enum `Actif` / `A supprimer` / `Non identifié`); `etat_fonct` (R, enum `En fonctionnement` / `Hors service` / `Supprimé définitivement` / `Absent momentanément` / `Inconnu`).
  - Device: `fab_siren`, `fab_rais` (R, manufacturer); `modele` (R); `num_serie` (R, unique constraint); `id_euro` (European Unique Device Identifier, UDI).
  - Consumables: `lc_ped` (boolean, paediatric electrodes present); `dtpr_lcped` (paediatric pad expiry); `dtpr_lcad` (adult pad expiry); `dtpr_bat` (battery expiry).
  - Maintenance: `mnt_siren`, `mnt_rais` (maintainer); `freq_mnt` (maintenance frequency, free text ≤255 chars); `dispsurv` (boolean, remote monitoring device present); `dermnt` (R, date of last maintenance).
  - Operator: `expt_siren` (R), `expt_siret`, `expt_rais` (R), `expt_tel1` (R), `expt_tel2`, `expt_email` (R).
- Schema evolution: v1.0.7 (last modified 2024-07-01, 46 fields) expressed availability as two pipe-separated enumerations — `disp_j` (7j/7, lundi … dimanche, jours fériés, événements, non renseigné) and `disp_h` (heures ouvrables, heures de nuit, 24h/24, non renseigné). v1.0.8 replaced both with the single OSM-syntax `dispo_horaires`. — [schema.json v1.0.7](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.7/schema.json); [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json)
- The published open-data CSV (columns prefixed `c_`) omits restricted fields (phones, emails, manufacturer, model, serial number, UDI, maintainer) and adds registry-side columns not in the declaration schema: `c_etat_valid` (validation state), `c_xy_precis` (geocoding precision score), `c_id_adr` (national address-base ID), `c_maj_don` (date data last updated), `c__edit_datemaj` (edit timestamp), `c_doublon` (duplicate flag), `c_application_provenance`, `c_srid_origin`, `the_geom`. — [Géo'DAE CSV via tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?page_size=1)
- Own query, 21 Nov 2026 — size and structure: 192,453 records; 37,068 `Extérieur` (19.3%) vs 155,385 `Intérieur` (80.7%); `acc_lib` true for 120,863 (62.8%); 4,788 flagged mobile (2.5%). — [tabular API, group-by `c_acc`](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_acc__groupby&gid__count)
- Own query — availability: `c_dispo_horaires` = `24/7` for 38,516 records (20.0%); of the 37,068 outdoor AEDs, 27,857 (75%) are 24/7; 116,371 records (60.5%) carry the value `Mo-Su off`. — [tabular API, 24/7 filter](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_dispo_horaires__exact=24/7&page_size=1)
- Own query — validation and status: `c_etat_valid` = `validées` 177,436 (92.2%), `en attente de validation` 14,800 (7.7%), `mises en doute` (doubted) 39; `c_etat_fonct` = `En fonctionnement` 191,215 (99.4%), `Absent momentanément` 746, `Hors service` 325, `Supprimé définitivement` 120, `Inconnu` 47; 5,298 records (2.8%) flagged as duplicates. — [tabular API, group-by `c_etat_valid`](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_etat_valid__groupby&gid__count)
- Own query — freshness and completeness: data last updated (`c_maj_don`) before 2024 for 37,004 records (19.2%), on/after 1 Jan 2026 for 88,291 (45.9%), empty for 17,661 (9.2%); last maintenance (`c_dermnt`) more than two years old for 77,082 (40.1%); battery expiry filled for 80,763 (42%), of which 16,699 (20.7%) are already past; adult pad expiry filled for 85,621 (44.5%), of which 24,091 (28.1%) are past; `c_photo1` filled for 8,526 (4.4%); floor filled for 64,509 (33.5%); access note filled for 93,959 (48.8%); remote monitoring (`c_dispsurv`) true for 6,624 (3.4% of all records). — [tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_dispsurv__groupby&gid__count)

**France — Staying Alive and SAUV Life (responder apps)**
- Staying Alive (AEDMAP / Association RMC-BFM): press kit of January 2025 reports a community of 380,000 "citoyens sauveteurs" and coverage of 88 metropolitan départements. — [Staying Alive press kit, Jan 2025](https://stayingalive.org/wp/wp-content/uploads/2025/01/202501-Dossier-de-Presse.pdf)
- A July 2025 Staying Alive flyer distributed by CHU Tours cites 80,000 interventions, 250,000 defibrillators and 420,000 citizen responders (promotional figures; mapping of numbers to labels should be re-checked). — [Staying Alive flyer](https://www.chu-tours.fr/wp-content/uploads/2026/06/Staying-alive-Flyer_A5_Vert_Juillet_2025_App.pdf)
- A national-population evaluation of the app exists: "What to expect from a smartphone dispatch application for out-of-hospital cardiac arrest in a national population?" — [PubMed 41205856](https://pubmed.ncbi.nlm.nih.gov/41205856/)
- SAUV Life has been deployed across France since 2018 and was reported as deployed in 21 SAMU dispatch centres at the time of the article. — [Le Quotidien du Médecin](https://www.lequotidiendumedecin.fr/hopital/urgences/citoyens-sauveteurs-sauv-life-appli-deployee-dans-21-samu)

**Sweden — Hjärtstartarregistret, SMS-livräddare/Heartrunner, Everdrone**
- The registry (Sveriges hjärtstartarregister, run by the Swedish Resuscitation Council, HLR-rådet) requires the responsible person to confirm the record every six months via an emailed link (or "Mina Sidor" → "Validera"). — [HLR-rådet, "Validera hjärtstartare" 2019](https://www.hlr.nu/wp-content/uploads/2019/11/Validera-hjärtstartare_2019.pdf)
- If confirmation is missing, reminders are sent; after the third reminder (sent after 14 days) the AED is removed from the registry. 3,345 AEDs were removed in 2024. — [HSREG annual report 2024](https://www.hlr.nu/wp-content/uploads/2025/02/HSREG-arsrapport-2024.pdf)
- In 2023, 3,662 AEDs were removed, 2,818 of them for missing confirmation; the report notes the emails easily drown among other mail, that confirmation may need to be more frequent than six-monthly, and that a new SMS-based process was planned for 2025. — [HSREG annual report 2023](https://www.hlr.nu/wp-content/uploads/2024/10/Arsrapport-2023-Sveriges-hjartstartarregister.pdf)
- Registry size reported as about 18,500 (2021) and 22,700 (2023); the total number of AEDs in Sweden is estimated between 35,000 and 50,000, with media reporting that only about a third are registered. — [Läkartidningen](https://lakartidningen.se/vetenskap/allt-fler-hjartstartare-i-samhallet-men-fa-anvands/); [SVT](https://www.svt.se/nyheter/lokalt/stockholm/bara-en-tredjedel-av-alla-hjartstartare-ar-registrerade); [Sveriges Radio](https://sverigesradio.se/artikel/7064659)
- OpenStreetMap documents a key `ref:hjartstartarregistret.se` linking OSM nodes to registry IDs. — [OSM wiki (sv)](https://wiki.openstreetmap.org/Sv:Key:ref:hjartstartarregistret.se)
- SAMBA randomised trial (Stockholm and Västra Götaland; 947 OHCA patients; JAMA Cardiology): dispatching app volunteers to fetch AEDs did not significantly raise overall AED attachment, because 59% of all AEDs were attached by lay people not using the app (high baseline plus crossover). — [JAMA Cardiology](https://jamanetwork.com/journals/jamacardiology/fullarticle/10.1001/jamacardio.2022.4362)
- Everdrone / Karolinska / SOS Alarm / Region Västra Götaland: 2020 pilot — drones launched for 12 of 53 suspected-arrest alerts and delivered an AED in 11. — [Karolinska Institutet](https://news.ki.se/drones-delivered-defibrillators-to-patients-with-suspected-cardiac-arrests)
- Lancet Digital Health study (21 Apr 2021 – 31 May 2022; service area about 200,000 people; 58 AED deliveries): in 55 cases with both times recorded the drone-delivered AED arrived before the ambulance in 37 (67%), median lead 3 min 14 s. — [Karolinska Institutet, Nov 2023](https://news.ki.se/drones-enabled-the-use-of-defibrillators-before-ambulance-arrival); [Everdrone/Cision](https://news.cision.com/se/everdrone-ab/r/everdrone-first-on-scene-validated-by-study-in-lancet-digital-health,c4155427)
- The programme is operational in 2026: a drone-delivered AED was used in a suspected cardiac arrest in Borås on 19 July 2026 under Västra Götaland's emergency drone programme, where drones are dispatched automatically alongside ambulances. — [Air Cargo Week](https://aircargoweek.com/drone-delivered-aed-used-in-life-saving-cardiac-arrest-response-in-sweden/)

**Netherlands — HartslagNu**
- HartslagNu annual report for 2024: 243,232 registered citizen responders and 25,119 active AEDs. — [HartslagNu Jaarverslag 2024](https://hartslagnu.nl/wp-content/uploads/2025/12/20251125_Jaarverslag-2024.pdf)
- National coverage allowing resuscitation within 6 minutes everywhere in the Netherlands was reported as achieved in 2021. — [NOS](https://nos.nl/artikel/2408416-reanimeren-binnen-6-minuten-nu-mogelijk-in-heel-nederland)
- The HartslagNu database records when each AED is available and whether a PIN is needed to open the cabinet; responders asked to fetch an AED receive the exact location and, if needed, the PIN through the app. — [HartslagNu](https://hartslagnu.nl/) (statement surfaced from the operator site by search; exact sub-page not confirmed)
- Terms and conditions (v1.1, 25 Nov 2025): registering an AED is voluntary, but the deployability of a registered AED is the registrant's responsibility. — [HartslagNu Algemene Voorwaarden](https://hartslagnu.nl/wp-content/uploads/2026/06/20251125_AlgemeneVoorwaarden-HsN_v1.1_DEF-2.pdf)
- A 2023 user-committee report noted 375 AEDs marked "Inactief" without a clear reason, many of which were in fact available, and that devices bought more than ten years ago are not automatically removed. — [HartslagNu KBG report, Jan 2023](https://hartslagnu.nl/wp-content/uploads/2023/06/Verslag-KBG-230131.pdf)
- A 2026 health-budget amendment released a one-off €1.5 million for more AEDs and citizen responders, noting "white spots" mainly in vulnerable neighbourhoods. — [Tweede Kamer, kst-36800-XVI-69](https://zoek.officielebekendmakingen.nl/kst-36800-XVI-69.pdf)
- Volunteers have run street searches for unregistered AEDs in Amsterdam. — [NH Nieuws](https://www.nhnieuws.nl/nieuws/353411/speuren-naar-niet-geregistreerde-aeds-in-amsterdam-kan-mensenlevens-redden)
- An OSM-based Dutch viewer, OpenAED.nl, exists. — [OSM wiki](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator)

**Germany, Austria, Switzerland**
- Germany has no nationwide responder-alert system; the apps are not interconnected and often work only locally. — [ZDFheute](https://www.zdfheute.de/ratgeber/gesundheit/ersthelfer-app-first-responder-system-100.html)
- A Bundestag paper counts about eleven such software systems, including Mobile Retter, Corhelper and Region der Lebensretter. — [Bundestag Drucksache 21/901](https://dserver.bundestag.de/btd/21/009/2100901.pdf)
- Mobile Retter figures differ by source and date: "over 5,000 active responders and more than 7,000 deployments" (Bertelsmann Stiftung, undated) versus "over 20,000 active and over 37,000 deployments" (consumer health site, undated). — [Bertelsmann Stiftung](https://www.bertelsmann-stiftung.de/de/unsere-projekte/smart-country/gute-beispiele/64); contradicted by [Shop Apotheke magazine](https://www.shop-apotheke.com/magazin/e-health/m-health/ersthelfer-app/)
- A German retrospective study evaluated outcomes with the Corhelper app (Scientific Reports, 2024). — [Springer](https://link.springer.com/10.1038/s41598-024-81263-8)
- Switzerland: Defikarte.ch is a free, fully open-source app built directly on OpenStreetMap data for finding and recording AEDs (covering Switzerland and Liechtenstein); its author chose OSM so the map benefits from community maintenance instead of manual upkeep. — [SIRMED/Defikarte presentation](https://www.paraplegie.ch/sites/default/files/2021-03/sirmed_defikarte.ch_.pdf); [App Store](https://apps.apple.com/at/app/defikarte-ch/id1549569525?l=en-GB)
- Switzerland: "Momentum" is the first-responder alerting app used by cantons; the 144 dispatch centre alerts volunteers, and responders from participating cantons can be alerted nationally when near an incident in another canton. — [Kanton Basel-Stadt](https://www.bs.ch/themen/sicherheit-und-demokratie/milizdienst/first-responder-0)
- Swiss national dataset (Dec 2024): 14,446 AEDs, of which 5,666 accessible 24 hours and 8,780 (about 61%) with restricted hours. — [Swiss Medical Weekly 2025](https://smw.ch/index.php/smw/article/download/4928/6554/32002)

**Italy**
- Law 116 of 4 Aug 2021 (in force 28 Aug 2021) introduces registration of AEDs with the 118 emergency dispatch centres and provides for a national application that geolocates AEDs. — [Normattiva](https://www.normattiva.it/eli/id/2021/08/13/21G00126/ORIGINAL)
- Implementation is regional: e.g. Sardinia's AREUS set up a new regional AED registry under the law, and Quotidiano Sanità reporting (c. 2025) notes the national app was still not available about four years after the law. — [Quotidiano Sanità](https://www.quotidianosanita.it/regioni-e-asl/arresto-cardiaco-improvviso-areus-istituisce-il-nuovo-registro-regionale-dae-della-sardegna/)
- Local guidance (AUSL Modena) says every installed device must be registered on the national or regional portal. — [AUSL Modena decalogue](https://www.ausl.mo.it/media/Decalogo-Comuni-cardioprotetti.pdf)
- EuReCa Three: out-of-hospital cardiac arrest survival 7.5% across Europe, 6.6% in Italy. — [Quotidiano Sanità](https://www.quotidianosanita.it/studi-e-analisi/arresto-cardiaco-fuori-dall-ospedale-sopravvivenza-del-in-ue-in-italia-lo-studio-eureca-three/)

### Inferences
- Géo'DAE's schema is the closest thing to an off-the-shelf standard for a government AED dataset: it is a validated Table Schema, uses stable machine-readable enums, separates public from restricted fields by regulation, and (since March 2026) encodes hours in OSM `opening_hours` syntax, which makes it directly interoperable with OpenStreetMap tooling. A Polish schema could be published as a near-superset with documented mappings to both.
- The French numbers also show what a legal obligation alone does not deliver: 60.5% of records hold `Mo-Su off` (almost certainly a migration artefact of the old "non renseigné" values rather than devices that are never available — this is my inference, not documented), only 20% are explicitly 24/7, 4% have photos, and 99.4% self-report "in operation" while 21–28% of filled battery/pad expiry dates are already past. Self-declared status without re-confirmation drifts.
- The French published file contains useful "registry-side" quality columns (validation state, duplicate flag, geocoding precision, last-update date). Exposing such provenance/quality metadata per record is cheap and is a differentiator for an aggregator of scattered Polish sources.
- Sweden is the only system found with a hard expiry rule (unconfirmed → deleted). It costs roughly 3,000+ records a year out of about 22,000 and the operator itself judges email too weak a channel; a softer variant (unconfirmed → flagged "stale" and down-ranked, not deleted) may keep coverage while staying honest.
- Germany and Italy show the failure mode Poland is trying to escape: many regional/vendor silos, no shared dataset.

### Gaps
- Austria (Lebensretter app in Vienna, Definetz / Defi-Kataster) and Germany's "Region der Lebensretter" and KATRETTER: no reliable figures or mechanism descriptions found in this pass.
- I could not confirm from a primary source the reported court ruling in a dispute between Staying Alive and SAUV Life over reuse of the AED database (surfaced in a search snippet only); if true it is a cautionary tale about licensing AED data, but treat as unverified.
- I did not retrieve the French decree obliging public-access buildings to install AEDs, nor any sanction regime for non-declaration; neither is asserted above.
- Whether Sweden's SMS confirmation process went live in 2025–2026 is unconfirmed; no 2025/2026 registry count found.
- A search summary described a Swedish study finding that owners of unregistered AEDs were often unaware of the national registry or found registration difficult; I could not pin it to a specific paper, so it is not listed as a finding.
- HartslagNu owner re-confirmation cadence and current 24/7 share not found (an older NOS figure of about 70% 24h-available could not be dated).
- No peer-reviewed Everdrone outcome data after the 2023 Lancet Digital Health paper was found.
- Content of Italy's DPCM of 23 Oct 2024 (listed among results) was not read.

---

## 4. USA/Canada: PulsePoint/NEAR, Avive, MyHeartMap, drones

### Takeaway
North America has no mandatory registry; the innovation is in crowdsourcing and in connected hardware. PulsePoint's NEAR registry lets anyone add an AED from a phone and alerts AED owners when their device is needed nearby; Avive's cellular/GPS AEDs are literally dispatched by 911 through RapidSOS; and the 2012 MyHeartMap Challenge remains the reference proof that a gamified contest can map a city's AEDs in weeks.

### Cited Findings

**PulsePoint AED / National Emergency AED Registry (NEAR)**
- The PulsePoint AED app registers AEDs into NEAR so their location is known to responders and 911 telecommunicators; NEAR is hosted by the PulsePoint Foundation. — [PulsePoint NEAR](https://www.pulsepoint.org/near-registry)
- PulsePoint's AED page lists 175,600 "Alertable AEDs" (undated figure on the page). — [PulsePoint AED](https://pulsepoint.org/pulsepoint-aed)
- "AED Needed" alerts: in communities using PulsePoint Respond, AED owners/responsible parties can receive real-time alerts when their registered AED is needed nearby (911-initiated AED response). — [PulsePoint AED-needed alerts](https://www.pulsepoint.org/aed-needed-alerts)
- The registry also manages co-located resources: bleeding control kits, naloxone and epinephrine, shown to telecommunicators. — [PulsePoint AED registry factsheet](https://www.pulsepoint.org/fyi/PulsePoint_AED_Registry_Factsheet.pdf)
- Registry entries support community-submitted AED images, and the management tooling flags incomplete records for the agency to fix. — [PulsePoint "Top ways to improve your AED registry"](https://pulsepoint.org/top-ways-to-improve-your-aed-registry)
- Dispatch access is through integrations with protocol/CAD partners such as PowerPhone; RapidSOS and the PulsePoint Foundation announced a partnership on 15 Sept 2026 to connect 911 directly to the registry. — [PulsePoint news (NEAR tag)](https://www.pulsepoint.org/news/tag/near-registry)
- PulsePoint and ZOLL announced a partnership on 4 Dec 2025 to accelerate growth of the national registry. — [Business Wire](https://www.businesswire.com/news/home/20251204983667/en)
- The "Anyone Can Register" campaign (launched February 2026) recruits volunteers, manufacturers and owners to add local AEDs via the PulsePoint AED app or the short URL AED.new. — [EMS1](https://www.ems1.com/aed/new-anyone-can-register-campaign-aims-to-map-every-aed-in-the-nation)
- A CARES–NEAR pilot links real cardiac-arrest event data with verified AED location data. — [PulsePoint news](https://www.pulsepoint.org/news/tag/aed-registry)

**Avive Connect AED and "4 Minute City / 4 Minute Community"**
- The Avive Connect AED has Wi-Fi, cellular and GPS; each device reports health, status and location to a dashboard daily during its nightly self-test. REALConnect monitors battery life, pad expiration, self-tests and device condition. — [Avive maintenance features](https://avive.life/features/aed-maintenance/); [Avive REALConnect](https://www.avive.life/realconnect)
- Pricing model: device purchased outright, first year of REALConnect included, then $199 per year. — [Avive store](https://store.avive.life/products/avive-connect-aed-1)
- Connectivity also enables a "lost mode" and alerts to 911 when the AED is in use. — [Avive blog](https://www.avive.life/blog/aed-wifi)
- Through RapidSOS, Avive says its platform integrates with more than 90% of US 911 call centres; the telecommunicator dispatches EMS and simultaneously activates nearby Avive devices, which alarm and show the incident location. — [Avive 4 Minute Community](https://avive.life/4-minute-city/); [RapidSOS blog](https://rapidsos.com/blog/dispatching-aeds-like-first-responders-how-avive-rapidsos-are-transforming-emergency-cardiac-response/)
- First documented save: Cumberland County, PA, 16 July 2024 — a volunteer dispatched by 911 arrived with an Avive Connect AED and resuscitated the patient before EMS arrived. — [Avive case study](https://www.avive.life/customer-stories/cumberland)
- Forsyth County, GA save timeline: 4 minutes from AED dispatch to power-on, 58 seconds from activation to pads placed, 1 min 24 s from pads to shock. — [Avive save story](https://www.avive.life/customer-stories/forsyth-county-save)
- Carrollton, TX (over 100 Avive AEDs city-wide): in a September 2025 night call, 12 devices were alerted and 5 people responded. — [Avive news](https://www.avive.life/news/carrollton-tx-save)
- North Augusta, SC joined on 17 Feb 2026 with 50 devices placed with CPR-trained volunteers. — [Avive news](https://www.avive.life/news/north-augusta-sc-avive-4-minute-community-program)
- These results are vendor case reports; "4 Minute City" is the older programme name and "4 Minute Community" the current one. — [Avive 4 Minute Community](https://avive.life/4-minute-city/)

**MyHeartMap Challenge (University of Pennsylvania, 2012)**
- A crowdsourcing contest in Philadelphia in early 2012 (described as six to eight weeks): more than 350 teams and individuals reported more than 1,500 AEDs in about 800 unique buildings; two co-winners each found more than 400 AEDs and each received $9,000. — [Penn Medicine](https://www.pennmedicine.org/news/news-releases/2012/may/two-winners-take-grand-prize-i); [WHYY](https://whyy.org/articles/more-than-1000-defibrillators-found-during-philadelphia-search-challenge)
- Devices were most often in gyms (19%), schools (16%) and offices (11%); many were "stashed away in basements or closets". A prior canvass of 1,420 buildings found 88% had no AED. — [Penn Medicine](https://www.pennmedicine.org/news/news-releases/2012/may/two-winners-take-grand-prize-i)
- The resulting registry held 2,559 AEDs, of which 852 unique devices came from the challenge. — [PMC4748177](https://pmc.ncbi.nlm.nih.gov/articles/PMC4748177/)

**Registry completeness and device readiness (US)**
- North Carolina (Prehospital Emergency Care, 2005): the state EMS database held only 99 of 552 (18%) public-access defibrillation sites identified by the study. — [Prehosp Emerg Care](https://informahealthcare.com/doi/abs/10.1080/10903120590961969)
- A US standardised-testing study (Seattle and Suffolk County sites) found 21% of AEDs failed at least one phase of testing and noted wide variability in how AEDs are registered and maintained. — [EurekAlert](https://www.eurekalert.org/news-releases/683084)

**Drone delivery**
- Duke-led programme: first US drone AED deliveries on real 911 calls in Clemmons, Forsyth County, North Carolina, reported November 2025; goal is to raise bystander AED use from 1–4% of arrests to more than 30%. — [Duke Today](https://today.duke.edu/2025/11/us-first-drones-deliver-aeds-north-carolina-county)
- Canada (Peel Region / Caledon, Drone Delivery Canada): phase one was a 911-call simulation with a 100% success rate and faster response than an ambulance. — [AirMed&Rescue](https://www.airmedandrescue.com/latest/news/ddc-completes-phase-one-drone-borne-aed)
- A Virginia county joined an AED drone-delivery study in 2026. — [DroneLife, Aug 2026](https://dronelife.com/2026/08/03/va-county-takes-part-in-study-on-delivering-aeds-to-patients/)

**Responder alerting research**
- ALARM randomised trial (AHA release, 2026): "smart alerting" — sending alerts only to a small circle around the scene — increased the chance that a volunteer arrived before EMS; survival effect not yet shown. — [AHA Newsroom](https://newsroom.heart.org/news/selective-smartphone-alerts-helped-improve-bystander-response-time-for-cardiac-arrest)

### Inferences
- PulsePoint's two-sided notification is a distinctive feature no European registry in this review offers: the registry notifies the AED's owner (not only volunteers) when the device is needed, turning every registered contact into a potential deliverer.
- The contest format (small prize pool, weeks not months, photo proof) is a proven bootstrap for the "long tail" of unknown AEDs and fits a hackathon narrative; MyHeartMap contributed a third of the final Philadelphia registry.
- Registering co-located emergency equipment (bleeding kits, naloxone) in the same schema is a cheap extension of an AED dataset.
- Avive demonstrates the end state where readiness and location are telemetry, not declarations; a registry schema should therefore reserve fields for "source of status = device telemetry" and "last heartbeat".

### Gaps
- No public documentation of the full PulsePoint/NEAR data-field list or of how submitted photos are verified was found; the "175,600" count is undated.
- No independent (non-vendor) outcome evaluation of Avive's 911-dispatched AED model was found.
- No peer-reviewed time-saved results for the Duke/Forsyth or Peel drone programmes were found; the Duke team's "about four minutes" is an estimate.
- Avive FDA approval date and incident-data fields were not retrieved.

---

## 5. Australia / New Zealand

### Takeaway
Australasia has converged on GoodSAM as both responder app and state AED registry (South Australia, NSW, Victoria; St John in New Zealand since 2018), with the best non-European outcome evidence (37% higher adjusted odds of survival when a responder beats the ambulance). The instructive negative case is Heart of the Nation: its national app and AED register were closed in 2025 and owners sent back to state registries.

### Cited Findings
- South Australia: the SA AED Register is hosted on the GoodSAM platform and is described as the only AED registry integrated with Triple Zero (000) in the state. — [SA Ambulance Service](https://saambulance.sa.gov.au/what-we-do/aed-register)
- New South Wales: the state AED registry was added to the GoodSAM app so responders can see whether an AED is near a patient; over 4,300 AEDs registered as of August 2024. — [NSW Health, Aug 2024](https://www.health.nsw.gov.au/news/Pages/20240814_00.aspx)
- NSW launched a public AED map on Restart a Heart Day, October 2025. — [NSW Health, Oct 2025](https://www.health.nsw.gov.au/news/Pages/20251016_00.aspx)
- Victoria: publicly accessible registered AEDs are visible to GoodSAM responders via Ambulance Victoria's registry. — [Ambulance Victoria](https://www.ambulance.vic.gov.au/register-my-aed)
- Victorian cohort (Med J Aust 2025; 9,196 OHCAs): survival to hospital discharge was 37% more likely (risk-adjusted) when smartphone-activated volunteer responders arrived before EMS; no association when they arrived after. The authors could not determine whether the GoodSAM responder or another bystander performed CPR/defibrillation. — [MJA 2025](https://www.mja.com.au/journal/2025/222/10/smartphone-activated-volunteer-responders-and-survival-discharge-after-out)
- FIRST trial (Ambulance Victoria and St John New Zealand): a multicentre cluster randomised trial equipping frequent GoodSAM responders with an ultraportable defibrillator (CellAED) to test 30-day survival; under way in 2026. — [Ambulance Victoria](https://www.ambulance.vic.gov.au/first)
- GoodSAM treats mobile AEDs (carried in kits or cars) as a responder category alongside fixed registry entries. — [GoodSAM locator map](https://goodsamapp.org/locatorMap)
- New Zealand: GoodSAM has been used by St John since 2018. — [St John NZ](https://www.stjohn.org.nz/first-aid/lifesaving-apps/goodsam/)
- New Zealand: "AED Locations" (aedlocations.co.nz; app developed by Abletech; founder Gareth Jenkin) is a free GPS locator; additions are submitted by contacting the operator. — [App Store NZ](https://apps.apple.com/nz/app/aed-locations/id424094430); [Healthify NZ](https://www.healthify.nz/aed-locations-app)
- A local business article puts AED Locations at over 9,000 AEDs mapped nationwide (secondary source). — [Business North Harbour](https://businessnh.org.nz/aed-locations-in-aucklands-north-shore-a-community-lifeline/)
- Heart of the Nation (founded 2020 by former Yellow Wiggle Greg Page) became a Heart Foundation programme on 1 June 2025; its app and National AED Register "have now closed"; AEDs with its tracking technology continue to work via supplier Inauro; owners are directed to state registries. — [Heart Foundation](https://www.heartfoundation.org.au/heart-of-the-nation); [Heart Foundation (retired programme page)](https://www.heartfoundation.org.au/about-us/our-programs/heart-of-the-nation-retired)
- A 2023 Philips survey reported almost three-quarters of Australians were unaware of nearby AED locations. — [Philips Australia](https://www.philips.com.au/a-w/about/news/archive/standard/news/press/2023/20231016-research-finds-almost-three-quarters-of-australians-unaware-of-nearby-aed-locations-on-world-restart-a-heart-day.html)

### Inferences
- A charity-run national register competing with dispatch-integrated state registries did not survive; the durable asset is the registry the emergency number actually uses. For Poland this supports anchoring the dataset in a government portal and making apps consumers of it, not owners of it.
- Treating "mobile AED carried by a person" as a first-class entity (GoodSAM; also `dae_mobile` in France) is an emerging pattern that a new schema should allow for.

### Gaps
- No Australia-wide registry or count exists/was found; state figures other than NSW (2024) were not retrieved.
- St John NZ's own AED registry process and current AED Locations data-maintenance rules were not found; whether AED Locations is crowdsourced is unconfirmed.
- FIRST trial results are not yet available.

---

## 6. Hardware / IoT: connected cabinets, connected AEDs, NFC/QR check tags

### Takeaway
Three hardware generations coexist: "dumb" AEDs checked by humans (the vast majority), retrofit monitors/cabinets that report door-open, removal and status-light state over cellular IoT, and natively connected AEDs (Avive) that self-report daily and can be dispatched. Cheap NFC/QR tags that open a pre-filled check form are the low-cost bridge and already exist commercially.

### Cited Findings
- Ositech Connected4Life monitored cabinet: sensors report door opening and AED removal; supports local or remote arming, locking and unlocking; EMS dispatchers can remotely trigger the cabinet's light and audio so bystanders can find it; 24/7 readiness monitoring. — [Ositech](https://www.ositech.com/?p=2949)
- Readiness Systems AED Sentinel: a retrofit monitor that photographs the AED's status indicator and detects cabinet/case opening, sending email/SMS alerts on status change, access events and upcoming battery/pad replacement; connects automatically over cellular IoT SIM. — [Readiness Systems brochure](https://mma.prnewswire.com/media/2201944/AEDSentinel_fromReadinessSystems6_23.pdf); [Hologram case study](https://hologram.io/blog/innovators-of-things-using-iot-to-make-sure-aeds-are-always-ready-for-an-emergency)
- CardiAct Connect: keypad-locked cabinet with optional online monitoring, camera, climate control and telephone. — [MedShop Australia](https://www.medshop.com.au/products/aed-cabinet-with-monitoring-telephone-emergency-defibrillator-storage-system-cardiact-connect)
- Patents describe cabinet door sensors plus temperature, humidity and audio sensing with a wireless link to a monitoring server. — [US 11756403](https://image-ppubs.uspto.gov/dirsearch-public/print/downloadPdf/11756403)
- Avive Connect AED: daily self-test report of health, status and location over cellular/Wi-Fi/GPS; alerts to 911 when in use. — [Avive](https://avive.life/features/aed-maintenance/)
- HeartSafe SMART Tag (UK, 2017 guide): a tag on the cabinet carrying both NFC and QR; tapping or scanning opens the check report with the cabinet location pre-filled, so the checker does no data entry. — [HeartSafe SMART Tag guide](https://www.fornhamallsaintsparish.gov.uk/assets/Parish-Council/Meetings/Associated-Papers/Sept-2017-meeting/HeartSafe-SMART-Tag-PAD-Reporting-System-V1.1-Feb17.pdf)
- Inspection apps using QR/barcode scans to open a device record, log the check with photos and schedule reminders: ReadiCheck, Orca Scan. — [ReadiCheck](https://play.google.com/store/apps/details?id=com.readicheck); [Orca Scan](https://orcascan.com/solutions/aed-inspection-software-3a0f96fb)
- Dispatcher-given unlock codes are standard practice: UK call handlers read out the cabinet code; Dutch responders receive the PIN in-app. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004); [HartslagNu](https://hartslagnu.nl/) (operator site; exact sub-page not confirmed)
- Guideline position on locks (2025): locking AEDs with a key or code may delay access; if locks are used because of real vandalism risk, dispatchers must be able to give clear, quick unlocking instructions. The ERC BLS 2025 public-comment draft says AEDs should be in unlocked cabinets and available 24/7. — [RCUK 2025 Guidelines](https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/systems-saving-lives-guidelines); [ERC BLS 2025 draft](https://cprguidelines.eu/assets/other-documents/ERC-BLS-Guideline-2025-V3.0-public-comments.pdf)
- The French schema has a boolean for remote monitoring (`dispsurv`); only 6,624 of 192,453 records (3.4%) declare it (own query, 21 Nov 2026). — [Géo'DAE tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_dispsurv__groupby&gid__count)
- The Circuit's authors expect that "smart AEDs will reduce the dependency on human intervention and that some data fields (emergency readiness, geo-location) will be captured automatically". — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

### Inferences
- With about 3% of French AEDs remotely monitored, telemetry cannot be the primary freshness mechanism for a national dataset in the 2020s; it should be an optional, higher-trust source alongside human confirmation.
- An NFC/QR sticker encoding the registry ID is the cheapest hardware intervention: it turns a status check into one tap, proves physical presence at the device, and can double as the public "report a problem / I saw it" entry point. No registry reviewed here offers this natively as a public feature — a differentiation opportunity.
- Remote-activated cabinet light/sound (Ositech) addresses the "cannot find it inside the building" failure and could be approximated in software by photos, floor level and indoor directions.

### Gaps
- No independent evaluation of connected cabinets' effect on readiness or retrieval time was found; product claims are vendor-sourced.
- No European vendor telemetry platforms were reviewed in this pass (results skewed to North American/Australian products).
- No open, vendor-neutral telemetry protocol or API standard for AED status was found.

---

## 7. Evidence: biggest real-world failure points and effect of responder apps

### Takeaway
The dominant, quantified failure is temporal inaccessibility: between roughly half and three-quarters of registered AEDs are not reachable around the clock, which removes 20–50% of nominal coverage exactly when most arrests occur. Next come registry incompleteness (often only a third of devices registered) and device unreadiness (about 13–21% not ready on inspection). Responder apps reliably raise bystander CPR and defibrillation, but the first large randomised trial (2026) showed no survival gain in a fast-EMS urban area.

### Cited Findings

**Not accessible at the time of arrest**
- Toronto (J Am Coll Cardiol 2016): of 767 AED locations, 73.5% were not open 24 hours and 28.6% were closed on weekends; counting only AEDs accessible at the time, coverage fell 21.5% overall and 31.6% for evening, night and weekend arrests. 61% of arrests happened in evenings, nights and weekends. — [ACC press release](https://www.acc.org/about-acc/press-releases/2016/08/15/13/56/aed-accessibility-a-barrier-during-cardiac-arrest); [University of Toronto](https://news.engineering.utoronto.ca/many-life-saving-defibrillators-behind-locked-doors-off-hours-study-finds/)
- Toronto time-of-day breakdown (AHA 2015 abstract): versus assumed 24/7 access, coverage was reduced by 8% in the daytime, 28% in the evening and 48% at night. — [Medical News Today release](https://www.medicalnewstoday.com/releases/302048)
- Copenhagen (2019): fewer than 50% of AEDs covering an arrest were accessible at the time; accessibility tripled bystander defibrillation and nearly doubled 30-day survival. — [Karlsson et al. 2019](https://research.regionh.dk/da/publications/automated-external-defibrillator-accessibility-is-crucial-for-bys/)
- Share of registered AEDs with 24/7 access by country: Denmark 72% (Sept 2025); Switzerland about 39% (5,666 of 14,446, Dec 2024); France 20% explicitly `24/7` (own query, Nov 2026, with a large "unknown-like" block). UK: 71.4% "publicly accessible" (a different measure: public vs restricted, not hours). — [TrygFonden](https://hjertestarter.dk/-/media/files/tal-og-fakta-om-hjerteloeber/250930-trygfonden-hjerteloeber-status-september-2025.pdf); [Swiss Medical Weekly](https://smw.ch/index.php/smw/article/download/4928/6554/32002); [Géo'DAE tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_dispo_horaires__exact=24/7&page_size=1); [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- A Swedish insurer's 2020s analysis was headlined "every second locality lacks an AED in the evening". — [If Skadeförsäkring press release](https://via.tt.se/pressmeddelande/3333719/varannan-tatort-saknar-hjartstartare-kvallstid?publisherId=391729)

**Registry out of date or incomplete**
- UK 2015: about 32,000 of an estimated 100,000 AEDs registered; data several years old in places. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Sweden: about a third of AEDs registered. — [SVT](https://www.svt.se/nyheter/lokalt/stockholm/bara-en-tredjedel-av-alla-hjartstartare-ar-registrerade)
- North Carolina 2005: 18% of identified sites were in the state database. — [Prehosp Emerg Care](https://informahealthcare.com/doi/abs/10.1080/10903120590961969)
- Netherlands: 375 AEDs wrongly sitting in "inactive" status (2023). — [HartslagNu KBG report](https://hartslagnu.nl/wp-content/uploads/2023/06/Verslag-KBG-230131.pdf)

**Device not ready**
- UK: 13% of registered AEDs out of service on the 31 Dec 2023 snapshot. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)
- Bornholm, Denmark: 18.1% of registered AEDs not functional/accessible on inspection (expired electrodes, failed self-test, access problems). — [PubMed 35618078](https://pubmed.ncbi.nlm.nih.gov/35618078/)
- US sites: 21% failed at least one test phase. — [EurekAlert](https://www.eurekalert.org/news-releases/683084)

**Hard to find / low use**
- Philadelphia: many AEDs were in basements or closets where people "wouldn't think to look". — [Penn Medicine](https://www.pennmedicine.org/news/news-releases/2012/may/two-winners-take-grand-prize-i)
- Public-access AEDs are used in fewer than 3% of OHCAs (ILCOR 2022 statement summary); bystander AED use in the US is 1–4%. — [ILCOR statement, PubMed 35164535](https://pubmed.ncbi.nlm.nih.gov/35164535/); [Duke Today](https://today.duke.edu/2025/11/us-first-drones-deliver-aeds-north-carolina-county)
- New Zealand: only 6% of OHCA patients receive defibrillation from a community responder. — [AUT repository](https://openrepository.aut.ac.nz/bitstreams/d3ca3a50-b5fe-415f-b998-1263c734ae6c/download)

**Distance**
- Operational search radii: UK CAD 200–1,600 m; Danish trial strata 0–358 m (<3 min) and 360–1,080 m (3–9 min); Copenhagen coverage definition ≤200 m route distance. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004); [ESC press release](https://www.escardio.org/news/press/press-releases/activation-of-community-first-responders-did-not-improve-short-term-survival-after-cardiac-arrest/); [Karlsson et al. 2019](https://research.regionh.dk/da/publications/automated-external-defibrillator-accessibility-is-crucial-for-bys/)
- Drones beat the ambulance in 67% of deliveries with a median 3 min 14 s lead (Sweden 2021–22). — [Karolinska Institutet](https://news.ki.se/drones-enabled-the-use-of-defibrillators-before-ambulance-arrival)

**Effect of responder apps on survival**
- HeartRunner RCT (Denmark, ESC 2026): no difference in 30-day survival (15% vs 17%; 13% vs 14%), despite bystander defibrillation rising from 6% to 14% and CPR from 75% to 86% in the 3–9 min stratum; investigators point to very short ambulance times (about 7 min). — [ESC press release](https://www.escardio.org/news/press/press-releases/activation-of-community-first-responders-did-not-improve-short-term-survival-after-cardiac-arrest/)
- SAMBA RCT (Sweden): no significant difference in AED attachment. — [JAMA Cardiology](https://jamanetwork.com/journals/jamacardiology/fullarticle/10.1001/jamacardio.2022.4362)
- Observational: Victoria — 37% higher adjusted odds of survival to discharge when the responder arrived before EMS; UK GoodSAM — about doubled survival when an alert was accepted. — [MJA 2025](https://www.mja.com.au/journal/2025/222/10/smartphone-activated-volunteer-responders-and-survival-discharge-after-out); [NIHR alert](https://evidence.nihr.ac.uk/alert/more-people-survived-cardiac-arrest-first-aiders-goodsam-alert/)
- ILCOR's 2022 statement concludes no single strategy suffices; it recommends a multi-layered approach including AED registration, signage, dispatch integration and mobile apps. — [RCUK summary of ILCOR statement](https://www.resus.org.uk/node/12478)

### Inferences
- Because night/weekend accessibility is the largest measured loss, the single most valuable app feature is a truthful "reachable right now" filter driven by structured hours, with indoor/locked devices visibly demoted outside hours.
- The contrast between randomised (neutral) and observational (positive) responder-app evidence means survival claims for a new app should be made cautiously; process metrics (time to AED, share of arrests with an accessible AED within 200–400 m) are defensible KPIs.
- A national open dataset enables the coverage-gap analytics several countries already use for policy (UK "defibrillator deserts", Dutch "white spots").

### Gaps
- No study quantifying how often a bystander fails to find an AED inside a building, or how often a locked cabinet/unknown code blocks retrieval, was found; evidence is anecdotal.
- No recent pooled meta-analysis (2024–2026) of responder apps was retrieved.
- The exact survival figures in Karlsson 2019 and the publication status of HeartRunner need the full texts.

---

## 8. Which mechanisms keep AED data current best

### Takeaway
No head-to-head trial compares freshness mechanisms, but operator data ranks them plausibly: automatic telemetry is the most reliable yet covers only a few percent of devices; periodic owner confirmation works at scale when it is frequent (3–6 months), escalated and consequential; event-triggered checks after each dispatch close the most dangerous gap; pure one-off declaration (France) decays visibly; crowdsourcing is excellent for discovery but unproven for ongoing status.

### Cited Findings
- Quarterly email confirmation plus organisation-level escalation plus a deployment-triggered re-check, with a daily readiness snapshot: 87% emergency-ready across 82,108 devices (UK, Dec 2023). The operators still call human dependence their main data-quality challenge. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004); [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions)
- Six-monthly confirmation with hard expiry: after a third reminder (14 days) the record is deleted; 2,818 of 3,662 removals in 2023 were for non-confirmation; the operator notes emails get lost, considers a shorter cycle and planned SMS. — [HSREG annual report 2023](https://www.hlr.nu/wp-content/uploads/2024/10/Arsrapport-2023-Sveriges-hjartstartarregister.pdf); [HSREG annual report 2024](https://www.hlr.nu/wp-content/uploads/2025/02/HSREG-arsrapport-2024.pdf)
- Mandatory declaration without periodic re-confirmation: France has the largest registry (192,453) but 19% of records were last updated before 2024, 40% show a last maintenance more than two years ago, and 21–28% of filled battery/pad expiry dates are in the past while 99.4% still read "in operation" (own query, 21 Nov 2026). — [Géo'DAE tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_etat_fonct__groupby&gid__count)
- Expiry-date fields with automatic notices: The Circuit emails Guardians when pads expire; Avive REALConnect tracks battery and pad expiry automatically. — [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions); [Avive REALConnect](https://www.avive.life/realconnect)
- Automatic telemetry: daily self-test, status and location upload (Avive); camera-read status indicator and door events (AED Sentinel). — [Avive](https://avive.life/features/aed-maintenance/); [Readiness Systems](https://mma.prnewswire.com/media/2201944/AEDSentinel_fromReadinessSystems6_23.pdf)
- Crowdsourced discovery: MyHeartMap added 852 unique devices to a 2,559-device registry in weeks; PulsePoint's "Anyone Can Register" (2026) lets non-owners add AEDs with photos; Defikarte.ch relies on OSM community maintenance. — [PMC4748177](https://pmc.ncbi.nlm.nih.gov/articles/PMC4748177/); [EMS1](https://www.ems1.com/aed/new-anyone-can-register-campaign-aims-to-map-every-aed-in-the-nation); [SIRMED/Defikarte](https://www.paraplegie.ch/sites/default/files/2021-03/sirmed_defikarte.ch_.pdf)
- Registry-side quality flags: France publishes validation state, a "mises en doute" (doubted) state and a duplicate flag per record; The Circuit holds "Potential Duplicate" and "Action Required" states; PulsePoint flags incomplete records for agencies. — [Géo'DAE tabular API](https://tabular-api.data.gouv.fr/api/resources/edb6a9e1-2f16-4bbf-99e7-c3eb6b90794c/data/?c_etat_valid__groupby&gid__count); [The Circuit FAQ](https://thecircuit.uk/frequently-asked-questions); [PulsePoint](https://pulsepoint.org/top-ways-to-improve-your-aed-registry)
- Physical audits remain the ground truth: Bornholm inspection found 18% of registered AEDs unusable. — [PubMed 35618078](https://pubmed.ncbi.nlm.nih.gov/35618078/)
- Low-friction registration is used as a selling point: Denmark describes owner registration as taking about ten minutes. — [TrygFonden flyer](https://edit.hjertestarter.dk/-/media/downloads/ny-flyer--register-din-hjertestarter.pdf)

### Inferences
- A layered "freshness score" per record is the natural synthesis and is not offered publicly by any reviewed registry: combine source trust (telemetry > owner confirmation > crowd confirmation > imported legacy), recency of last confirmation, and consumable expiry dates into a visible confidence level, and publish `last_verified_at` and `verification_method` as open-data columns.
- Channel matters: both Sweden (emails "drown") and the UK (email-only, cannot be disabled) point to adding SMS/push and one-tap confirmation links or NFC/QR scans to raise response rates.
- Soft expiry (stale flag, down-ranking, exclusion from "verified" filter) avoids Sweden's coverage loss while keeping the dataset honest; dispatch-grade consumers can filter on verified only.
- Crowd "I saw it / it's gone / it's locked" reports with photo evidence are best treated as signals that trigger an owner re-check rather than as authoritative edits — mirroring France's "mises en doute" state.

### Gaps
- No controlled comparison of reminder cadence or channel on registry accuracy was found.
- No evidence on reliability of crowdsourced status confirmations (as opposed to crowdsourced discovery) was found.
- Response rates to The Circuit's quarterly emails are not published in the sources retrieved.

---

## 9. International data standards and shared schemas

### Takeaway
There is no international or EU-level AED data standard. The two de facto references are OpenStreetMap's `emergency=defibrillator` tagging and France's Géo'DAE Table Schema — and since March 2026 they share the same opening-hours syntax. Guidelines (ILCOR 2022, ERC/RCUK 2025) say registries must exist and be linked to dispatch, but do not define fields.

### Cited Findings
- OSM tagging for `emergency=defibrillator` (node near the device). Recommended companion keys: `opening_hours` (when accessible); `access` (e.g. `customers`; `access=emergency` is deprecated, emergency access is implied); `phone` (party responsible for the device); `emergency:phone`; `defibrillator:location` (free-text placement, with language variants such as `defibrillator:location:en`); `indoor=yes/no`; `locked` (by code or key); `defibrillator:code`; `level` and `level:ref` (floor, when indoor); `description`; `manufacturer`; `model`; `defibrillator:cabinet` (`vertical_door`, `horizontal_door`, `twist`, `mechanical`, `no`), `defibrillator:cabinet:manufacturer`, `defibrillator:cabinet:colour`. — [OSM wiki](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator)
- OSM carries cross-reference keys to national registries: `ref:GB:the_circuit` (UK) and `ref:hjartstartarregistret.se` (Sweden). — [OSM wiki](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator); [OSM wiki (sv)](https://wiki.openstreetmap.org/Sv:Key:ref:hjartstartarregistret.se)
- OSM-based AED tools listed on the wiki: OpenAEDMap (web, iOS, Android), MapComplete "aed" theme, Defikarte.ch (CH/LI), OpenAED.nl (NL), and community mapping drives (UK Quarterly Project Q4 2020 and Q2 2024; France Project of the Month Sept 2020). — [OSM wiki](https://wiki.openstreetmap.org/wiki/Tag:emergency%3Ddefibrillator)
- France's schema-dae is a Frictionless Table Schema (JSON) with regex and enum constraints, example files, semantic versioning (1.0.7 → 1.0.8) and publication in the national schema catalogue schema.data.gouv.fr; `dispo_horaires` is explicitly "formatted according to the OpenStreetMap opening_hours standard". — [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json)
- The French schema includes the European Unique Device Identifier (`id_euro`, "IUD européen") as an optional device key. — [schema.json v1.0.8](https://schema.data.gouv.fr/schemas/atlasante/schema-dae/1.0.8/schema.json)
- ILCOR scientific statement on public-access defibrillation (Brooks et al., 2022, Circulation/Resuscitation): AED registries can inform the public and dispatchers of AED locations; recommends a multi-layered strategy including registration, signage, optimised placement/housing, dispatch integration and mobile apps. — [PubMed 35164535](https://pubmed.ncbi.nlm.nih.gov/35164535/); [RCUK summary](https://www.resus.org.uk/node/12478)
- ILCOR's 2024 evidence update maintained the recommendation to implement public-access defibrillation programmes (strong recommendation, low-certainty evidence). — [ILCOR BLS EvUps 2024](https://www.ilcor.org/uploads/Appendix-B1-BLS-EvUps-2024.pdf)
- ERC Guidelines 2025 "Systems Saving Lives" (Resuscitation 2025;215 Suppl 1, DOI 10.1016/j.resuscitation.2025.110821) and the UK adaptation: first-responder dispatch systems should be linked to AED registries; ambulance services should implement dispatcher-assisted public-access AED systems linked to registries. — [RCUK 2025 Systems saving lives](https://www.resus.org.uk/professional-library/2025-resuscitation-guidelines/systems-saving-lives-guidelines); [ERC 2025 draft for public comment](https://cprguidelines.eu/assets/other-documents/ERC-Guidelines-2025-Systems-Saving-Lives_final-for-public-comments.pdf)
- The Circuit paper lists the minimum information a registry should capture: location, emergency-readiness status, expiry date and contact information of the responsible person. — [O'Sullivan et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11382004)

### Inferences
- Field-level convergence across OSM, Géo'DAE and The Circuit suggests a practical common core for a Polish schema: stable ID; coordinates; structured address; indoor/outdoor; floor; free-text placement; photo URL; `opening_hours` in OSM syntax; public vs restricted access; locked yes/no (code held only in the restricted, dispatch-facing layer); operational status enum; responsible organisation; last maintenance; pad/battery expiry; mobile vs fixed; remote monitoring yes/no; plus provenance columns (source, validation state, duplicate flag, last verified date and method).
- Publishing the schema itself as a versioned, machine-validated artefact (as France does) and documenting an OSM tag mapping and an OSM `ref:PL:*`-style cross-reference key would make the Polish dataset immediately reusable by existing tools (OpenAEDMap, MapComplete, routing apps) and would be a concrete "first in Central Europe" claim — subject to verification by the Poland researcher.
- Two-tier publication (open fields vs. dispatch-only fields such as codes and personal contacts) is the established pattern in both France (by decree annex) and the UK (by consent).

### Gaps
- No EU-level initiative, directive or common schema for AED registries was found in this research; absence of evidence, not proof of absence.
- No ISO/CEN/HL7 standard for AED location data was found; no schema.org type specific to AEDs was checked.
- The final published wording of the ERC 2025 guideline on 24/7 availability and unlocked cabinets was only seen in the public-comment draft and the UK adaptation.
- OSM usage counts for `emergency=defibrillator` (taginfo) were not retrieved.
