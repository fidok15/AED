# AED location data, registries, apps and innovations in advanced Asian countries (Japan, South Korea, Singapore, Taiwan, Hong Kong/China) — state as of November 2026

Research date: 2026-11-21. Reliability markers used below:
- **[fetched]** = I read the primary page/PDF itself.
- **[snippet]** = fact comes from a search-engine summary of the linked page; the page was not opened in full. Treat as probable, re-verify before quoting a number in a pitch.

---

## Japan: who runs the AED maps, how data is collected/verified, what fields are published, is there an open-data standard?

### Takeaway
Japan has no mandatory national AED register: the "official" map (Japan Foundation for Emergency Medicine, 財団全国AEDマップ) is a voluntary owner-registration system whose records visibly age, so it publishes a per-record **freshness/accuracy grade (A–D, colour-coded)**; alongside it the Nihon AED Foundation runs a **gamified crowdsourced map** (AED N@VI / team ASUKA) with two-person confirmation and auto-expiry of unverified entries. The Digital Agency publishes a **22-field national schema for municipal AED open data** (自治体標準オープンデータセット「AED設置箇所一覧」), which is the single most directly transferable artefact for a dane.gov.pl dataset.

### Cited Findings

**Scale and the core data problem**
- Cumulative AED sales in Japan reached about 1.63 million units, of which public-access (PAD) units were 84% (about 1.37 million; exact PAD cumulative 1,373,798); 100,794 new PAD units were placed in 2023; cumulative registered disposals 357,758. [fetched] — [MHLW research grant report R5 (FY2023), Sakamoto group](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- The number of AEDs actually installed is **not known** in Japan; ~690,000 as of end-December 2023 is an estimate derived from sales minus service life, "not reflecting real installation information". There is "no nationwide compulsory registration system". [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- In the Japan Foundation for Emergency Medicine national AED map, records registered 8+ years ago "greatly exceed half" of all records; given AED service life (average 7.9 years across 7 makers/19 models), most of those are presumed not properly usable. [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- Manufacturers' capture rate of disposals (share of out-of-life AEDs formally registered as scrapped) was 59.4% overall, ranging 39%–100% by manufacturer. [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- The report expects AEDs with built-in communications (online status monitoring) to eventually solve both live-status and disposal tracking; several manufacturers are actively selling them. [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- 1 in 343 AEDs delivered a shock (2022 statistics). [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)

**Official map: 財団全国AEDマップ (Japan Foundation for Emergency Medicine, 日本救急医療財団)**
- Describes itself as the only registration-type nationwide AED map, based on an MHLW notice; explicitly not user-submitted. Each AED ships with a registration form; owners consent to publication; updates/disposals go via the seller or the foundation. Site copyright 2015. [fetched] — [qqzaidanmap.jp](https://www.qqzaidanmap.jp/)
- **Accuracy grade per pin (精度 A/B/C/D)**: derived from (a) whether pad and battery expiry dates were entered and (b) years since installation. A = pad+battery data entered (blue pin, currently managed). Without pad/battery data: B if <4 years since install, C at 4–6 years, D at 6–8 years. Pin colour shifts blue → yellow → red → grey at 2/4/6-year marks. Since April 2018, entering pad/battery expiry dates maintains or restores the grade. [fetched] — [qqzaidanmap.jp](https://www.qqzaidanmap.jp/)
- Fields shown per AED: facility name, registration number, location description (building + position), prefecture, address, facility type, public-use conditions, usable days and hours, year-round operation flag, hours notes, other notes, whether a maintenance person is assigned, installation date, accuracy class. [fetched] — [qqzaidanmap.jp](https://www.qqzaidanmap.jp/)
- The map renewal (adding map view and usable hours to what had been only a list of registrants) was designed and built by the startup Coaido, which also proposed sharing the database with municipalities; nationwide sharing with local governments was achieved. [fetched, article dated 2018-01-11] — [INTERNET Watch](https://internet.watch.impress.co.jp/docs/column/chizu3/1100451.html)
- A 2015 MHLW notice arranged for the foundation to hand registration data to local governments where the owner had consented. [snippet] — [MHLW notice hosted by Kanagawa Pref.](https://www.pref.kanagawa.jp/documents/102438/27nentuuti.pdf)
- The foundation's map is also offered as a smartphone app ("QQMAP") showing the A (blue) / B (yellow) / C (red) / D (grey) classes. [snippet] — [App Store: QQMAP](https://apps.apple.com/jp/app/qqmap/id1254388098)

**Crowdsourced + gamified map: AED N@VI → 救命サポーターアプリ team ASUKA (Nihon AED Zaidan / 日本AED財団)**
- App first released 2021-06-29 as AED N@VI; renamed "team ASUKA" on 2022-09-29; latest version seen 2.1.15 (2024-12-23); 36 ratings, 3.1/5 on the Japanese App Store. [fetched] — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854)
- Verification rules: (1) users can post or verify AED info **only within a set radius of their phone's current location** (geofenced edits); (2) an AED appears on the public map **only after at least two volunteers confirm it**; (3) listings not re-verified within a set period are **removed**. [fetched] — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854)
- Gamification: points for contributions feed a national ranking and a "gacha" for collectible characters; a promotion/quiz system; badges (v2.1.0, 2023-02); lifesaver-supporter certificate; AED image registration is mentioned in version notes. [fetched] — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854)
- Other features: route to nearest AED, address search on the 119-call screen (v2.1.5, 2023-06), embedded training app "Liv" (2024-01). [fetched] — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854)
- The listing cites an estimated 600,000 AEDs deployed in Japan. [snippet] — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854)

**Responder-activation apps tied to 119 dispatch**
- **AED GO** (Kyoto University-linked research system): when a 119 dispatcher suspects cardiac arrest, pre-registered volunteers near the scene get a push with the incident location and nearby public AEDs; participation is voluntary. Running in Owariasahi (Aichi), Kashiwa (Chiba) and Nara. [fetched/snippet] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf); [App Store: AED GO](https://apps.apple.com/jp/app/id1163968947)
- Original Owariasahi pilot ran October 2015–March 2016: the dispatch centre tablet sent an SOS with location and nearby AED info to residents' phones. [snippet] — [FDMA](https://www.fdma.go.jp/publication/ugoki/items/2901_30.pdf)
- **Honest outcome data (FY2023)**: Owariasahi 40 activations, volunteers acted in 29; Kashiwa 43 activations, volunteers acted in 10; Nara 47 eligible cases, 11 activations, 0 volunteer actions. **In no case did a volunteer beat the ambulance or was the AED used.** Stated cause: too few active registered volunteers. Planned fixes: in-app ranking that visualises one's activity, recruiting large organisations, and an event-type version for Expo 2025 Osaka-Kansai. [fetched] — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf)
- Earlier FDMA-funded evaluation: system activated in 133 usable cases; reasons for non-activation included AEDs locked inside facilities, unsafe scenes, bystanders not wanting volunteers; growing the volunteer base remained an issue. [snippet] — [FDMA, Kyoto 2018 results](https://www.fdma.go.jp/mission/develop/items/H30_seika_kyoto.pdf)
- A Kyoto University pilot-study protocol covers Owariasahi and Kashiwa from November 2015 to March 2026. [snippet] — [Kyoto Univ. PDF](https://yobou.med.kyoto-u.ac.jp/wp-content/uploads/2023/01/AED要請アプリケーション導入効果の検証（パイロット研究）.pdf)
- **Coaido119** (Coaido Inc., grew out of a 2013 hackathon app "AED SOS"): bystander sends an SOS with location, video, audio and chat to nearby trained people and facility staff. Signature feature **"AED Area Call" (AEDエリアコール)**: landline numbers of AED-holding buildings are pre-registered with coordinates; on SOS, nearby facilities are **phoned simultaneously with an automated voice message giving the location** (built on the Twilio API; international patent pending at the time). GPS can be manually corrected and a floor added. Pilot from August 2017 in Ikebukuro (Toshima Ward), using the foundation's AED data checked by the ward. As of January 2018 no real cardiac-arrest SOS had been sent. [fetched, 2018 article] — [INTERNET Watch](https://internet.watch.impress.co.jp/docs/column/chizu3/1100451.html)

**Open-data standard: 自治体標準オープンデータセット「AED設置箇所一覧」(Digital Agency)**
- "AED installation locations" is one of the datasets in the Digital Agency's municipal standard open dataset list; the programme was renamed from 推奨データセット (Recommended Dataset) to 自治体標準オープンデータセット on 2023-03-31. [snippet] — [Digital Agency](https://www.digital.go.jp/resources/open_data/municipal-standard-data-set-test)
- **Full field list (22 fields)** from the data item definition document [fetched, PDF text extracted; copy hosted by BODIK — the canonical version is on digital.go.jp]: — [データ項目定義書（AED設置箇所一覧）](https://data.bodik.jp/dataset/599132da-b451-47c0-9a6e-2ca65b899bcd/resource/5bfd47e5-6fa4-418c-8962-04cbf8b84409/download/cusers00000241downloadsdatadefinitionaed.pdf)

  | # | Field | Meaning | Format / example |
  |---|---|---|---|
  | 1 | 都道府県コード又は市区町村コード | code of the local government managing the record | 6 half-width digits, zero-padded (423084) |
  | 2 | NO | unique ID within that government | 10 digits, zero-padded (0000022200) |
  | 3 | 都道府県名 | prefecture name | string |
  | 4 | 市区町村名 | municipality name | string |
  | 5 | 名称 | name of building where AED is | string |
  | 6 | 名称_カナ | name in katakana | full-width kana |
  | 7 | 住所 | address, unabbreviated from prefecture down | string |
  | 8 | 方書 | address supplement (building/floor) | "○○ビル1階" |
  | 9 | 緯度 | latitude | WGS, decimal, 6 decimals (32.828706) |
  | 10 | 経度 | longitude | (129.84851) |
  | 11 | 設置位置 | exact position inside the site | "1階事務室" (1F office) |
  | 12 | 電話番号 | site phone | hyphen-separated |
  | 13 | 内線番号 | extension | digits |
  | 14 | 法人番号 | corporate number of the AED owner | 13 digits |
  | 15 | 団体名 | owner organisation name | string |
  | 16 | 利用可能曜日 | usable weekdays | "月火水木金" |
  | 17 | 開始時間 | opening time | hh:mm (09:00) |
  | 18 | 終了時間 | closing time | hh:mm (18:00) |
  | 19 | 利用可能日時特記事項 | exceptions (holidays, year-end) | free text |
  | 20 | 小児対応設備の有無 | paediatric capability yes/no | "有" |
  | 21 | URL | source page | URI |
  | 22 | 備考 | notes | free text |

- ID governance rules in the same document: IDs must be unique per government and **never reused, including IDs of deleted records**; IDs persist across dataset renames/yearly re-releases; retired records are fully deleted; system-dependent characters are banned. [fetched] — [definition document](https://data.bodik.jp/dataset/599132da-b451-47c0-9a6e-2ca65b899bcd/resource/5bfd47e5-6fa4-418c-8962-04cbf8b84409/download/cusers00000241downloadsdatadefinitionaed.pdf)
- Real datasets conforming to it: Machida City; Koto Ward and several other Tokyo municipalities served through the Tokyo Metropolitan open-data API platform. [snippet] — [Machida open data](https://opendata.city.machida.tokyo.jp/en/dataset/shisetsu_aed); [Tokyo API catalogue, Koto Ward](https://spec.api.metro.tokyo.lg.jp/spec/t131083d0000000027-d26151caf1370dd6c31d8931a2d8d189-0?lang=en)
- The government data catalogue lists "日本全国AEDマップ" among its "Open Data 100" case studies (CC-BY material) — a civic aggregation of municipal AED open data. [snippet] — [data.e-gov.go.jp](https://data.e-gov.go.jp/data/en/dataset/digi_20220315_0062/resource/d9ecdf66-25f5-4c23-a410-e8080ac0bcf6)

**24h access via convenience stores (municipality–chain agreements)**
- Shinjuku Ward signed an agreement with FamilyMart and Lawson (announced 2025-07-01) to place AEDs in 50 stores (42 FamilyMart, 8 Lawson). [snippet] — [Shinjuku Ward](https://www.city.shinjuku.lg.jp/whatsnew/pub/2025/0701-01.html)
- Bunkyo Ward's rationale: its 252 AEDs in ward facilities are mostly usable only during opening hours, hence convenience-store placement. [snippet] — [Bunkyo Ward](https://www.city.bunkyo.lg.jp/b003/p007905.html)
- Kashiwa publishes a list of 24h convenience stores holding AEDs; staff only hand the device over, they do not operate it; not all stores participate. [snippet] — [Kashiwa City](https://www.city.kashiwa.lg.jp/kyukyu/fdk/anshinjoho/aed/201.html)
- Okinawa examples: Naha placed AEDs in 118 convenience stores (one was used in a rescue and lent out 3 times on request); Okinawa City covered all 43 24h stores; Yaese all 10, with the town owning maintenance. [snippet] — [Ryukyu Shimpo](https://ryukyushimpo.jp/news/prentry-199909.html); [Ryukyu Shimpo (Yaese)](https://ryukyushimpo.jp/news/prentry-241376.html)
- Owariasahi has had an anyone-anytime AED in every convenience store since May 2014 (the same city that hosts the AED GO pilot). [snippet] — [FDMA](https://www.fdma.go.jp/publication/ugoki/items/2901_30.pdf)

**Survival impact (peer-reviewed)**
- All-Japan Utstein Registry 2005–2013: of 43,762 bystander-witnessed VF arrests of cardiac origin, 4,499 (10.3%) received public-access defibrillation; 1-month favourable neurological outcome 38.5% with PAD vs 18.2% without (adjusted OR after propensity matching 1.99); survivors attributable to PAD rose from 6 in 2005 to 201 in 2013. [snippet] — [Kitamura et al., NEJM 2016;375:1649](https://ir.library.osaka-u.ac.jp/repo/ouka/all/78401/NewEnglJMed_375_17_1649.pdf); [Osaka University summary](https://resou.osaka-u.ac.jp/en/research/2016/20161027_2)

### Inferences
- Japan's lesson for a Polish aggregator is that **freshness must be a first-class, visible attribute**: an owner-registration register with no expiry rule decays until most records are stale. The foundation's A–D grade (computed from "pad/battery dates present" + "age of record") is a cheap, explainable trust score that can be computed from any source dataset with a date column.
- The team ASUKA rule set (geofenced edits + two independent confirmations + auto-expiry) is a complete, simple anti-vandalism protocol for crowdsourced verification and maps directly onto a "confirm this AED is here" button.
- The AED GO results show responder-alerting fails without responder density; a hackathon team should present alerting as an integration hook, not as the core value. The core value is trustworthy location + availability data.
- The Digital Agency schema is deliberately minimal (no pad/battery expiry, no photo, no indoor floor field beyond free text). The richer fields live in the foundation map (expiry, maintenance person, access conditions). A Polish schema could combine both.
- Coaido's "Area Call" (auto-phoning the landline of the building that holds the AED) solves the problem that the AED is behind a reception desk and nobody near it has the app — it needs only a phone number field per AED.

### Gaps
- Current registered count in the foundation's national AED map: not stated on the site; the MHLW report has a figure (図表5) I could not extract as numbers.
- Number of AEDs / users in AED N@VI / team ASUKA: no figure found.
- MySOS: no source retrieved in this session on its AED features — unverified.
- Vending-machine-mounted AEDs and koban (police box) / railway-station placement: searches returned nothing citable; I cannot confirm scale or operators.
- Whether the foundation map exposes a public API or bulk download: not mentioned on the site; terms of use not read.
- Status of the Expo 2025 Osaka event-type AED GO deployment and its results: only the plan (written in FY2023) was found.
- Coaido119's status after 2018 (still operating? national rollout?) not verified.
- I could not fetch the canonical digital.go.jp copy of the definition document to confirm the BODIK-hosted version is the latest revision.

---

## South Korea: E-Gen map/app, legal obligations, data.go.kr API, smart-city/map integrations, video dispatcher guidance, IoT cabinets

### Takeaway
Korea couples a **legal duty** (mandatory installation in listed facility types, a named manager, inspection at least monthly, and since 2025 fines for not reporting inspection results) with a **single national register run by the National Medical Center (NEMC/E-Gen)** that is exposed as a free, licence-unrestricted **open REST API including a radius query and a full-data dump**. On top of that, 119 dispatchers switch callers to **video calls** for CPR coaching, with observational evidence of better outcomes.

### Cited Findings

**Open API (the model for a national AED API)**
- "국립중앙의료원_전국 자동심장충격기(AED) 정보 조회 서비스", dataset ID 15000652, provider National Medical Center (응급의료정보화팀). Base URL `https://apis.data.go.kr/B552657/AEDInfoInqireService`. REST, XML responses, free, **no restriction on scope of use**, update cycle listed as **real-time**; registered 2017-03-16, last modified 2026-07-15. [fetched] — [data.go.kr 15000652](https://www.data.go.kr/data/15000652/openapi.do)
- Three operations: (1) AED management info by 시도/시군구 (province/district); (2) **AED location lookup by longitude/latitude within a radius**; (3) **FullData download** of every AED (paged with pageNo/numOfRows). [fetched] — [data.go.kr 15000652](https://www.data.go.kr/data/15000652/openapi.do)
- Response fields: `rnum`, `org` (installing organisation), `buildAddress` (detailed address), `buildPlace` (place inside building, e.g. "consultation room"), `sido`, `gugun`, `manager` (manager name), `managerTel`, `clerkTel` (organisation phone), `mfg` (manufacturer), `model`, `SERIAL_NUM`, `wgs84Lon`, `wgs84Lat`, `zipcode1`, `zipcode2`, plus paging (`totalCount`, etc.). [fetched] — [data.go.kr 15000652](https://www.data.go.kr/data/15000652/openapi.do)
- The description says opening-hours information is included but the documented field list on the page shows no hours fields; the portal warns location and operating hours are for reference and may differ from reality. [fetched] — [data.go.kr 15000652](https://www.data.go.kr/data/15000652/openapi.do)
- Numerous local-government AED file datasets also sit on data.go.kr (e.g. Incheon facilities corporation). [snippet] — [data.go.kr example](https://www.data.go.kr/data/15151686/fileData.do)

**Legal framework**
- Emergency Medical Service Act Art. 47-2 (duty to equip listed facilities with CPR emergency equipment) and Art. 62 (administrative fines). Enforcement Rule Art. 38-3: the facility operator must appoint a manager, **inspect at least once a month**, provide user training and keep management records. [snippet, municipal guidance] — [Gunsan City AED management guidance](https://www.gunsan.go.kr/_cms/board/eFileDownload/161/1379153/16ae1a5f60127c0fb862a468baa88119)
- Fine for not installing where mandatory (example: ships of 20 tons or more): 500,000 / 750,000 / 1,000,000 KRW for 1st/2nd/3rd violation. [snippet, 2023 municipal notice] — [Gunsan City](https://www.gunsan.go.kr/_cms/board/eFileDownload/161/671056/2f649c2014a2fc60d80420b5fdf1e7e3)
- From **17 August 2025**, failure to conduct/report AED inspection results can draw a fine of up to 3 million KRW (reported by Pocheon City). [snippet, press] — [Asia Economy, 2025-03-05](https://www.asiae.co.kr/en/article/2025030516195942771)
- A bill introduced in September 2026 would require AEDs and similar equipment to be installed/stored in **always-accessible locations**. [snippet] — [DailyMedi](https://dailymedi.com/news/news_view.php?wr_id=940045)
- Local scale examples: Busan had 4,431 AEDs as of June 2025 (3,021 in legally obliged facilities, 1,410 in non-obliged places); Yeonggwang County ran a comprehensive inspection of its 130 AEDs from 2025-12-04 after poor-management cases surfaced; Yangcheon-gu inspected 520 AEDs (Feb 2026). [snippet] — [Busan City](https://www.busan.go.kr/eng/ai-translated-press-releases/1691467); [Asia Economy](https://www.asiae.co.kr/en/article/2025121113300825770); [Herald](https://www.heraldk.com/article/2026020918320218447)

**Citizen-facing discovery**
- Official channels for finding an AED are the Ministry of Health and Welfare "응급의료정보제공" (Emergency Medical Information) app for Android/iOS and the NEMC web AED search; AED data comes from the central emergency medical centre's database. [snippet] — [korea.kr policy news](https://www.korea.kr/news/policyNewsView.do?newsId=148940165); [App Store](https://apps.apple.com/us/app/id385668523)

**IoT / remote monitoring**
- Xcure "XAFE" outdoor smart AED storage box: IoT remote management lets operators check the AED's working state without site visits; master distribution deal with People Multi (Aug 2025). Context: after the 2022 Itaewon disaster, outdoor AED installation spread across public and private sectors. [snippet] — [Asia Economy, 2025-08-25](https://www.asiae.co.kr/en/article/2025082510260823772)
- SK C&C launched (Oct 2023) an integrated control service that monitors AEDs and surrounding devices in/around buildings in real time via IoT, with AED manufacturers. [snippet] — [Daum/press, 2023-10-24](https://v.daum.net/v/20231024153901209)
- CU Medical markets an AED remote management system ("AED at a glance") that is selling internationally. [snippet, headline only] — [Asia Economy, 2025-04-10](https://www.asiae.co.kr/en/article/2025041009523257823)

**Video-call dispatcher-assisted CPR (119)**
- Seoul's protocol: dispatcher starts chest-compression coaching by voice, then switches to a video call to correct posture; guideline distributed to 119 call centres nationwide in 2020. [snippet] — [Asia Economy, 2020-06-25](https://www.asiae.co.kr/en/article/2020062523461795690)
- Seoul retrospective cohort 2018–2019 (bystander-witnessed adult OHCA, presumed cardiac): video-instructed vs audio-instructed DA-CPR — survival to discharge 27.1% (105/387) vs 12.3% (211/1,722), adjusted OR 1.81 (95% CI 1.33–2.46); good neurological recovery adjusted OR 2.11 (1.48–3.01). Observational. An earlier study on 2017 cases did not show a significant adjusted benefit. [snippet] — [Scientific Reports 2021](https://link.springer.com/10.1038/s41598-021-95077-5)

### Inferences
- Korea's API design is the closest template for what the Polish team should publish: one base service with (a) by-administrative-unit query, (b) lat/lon + radius query, (c) full dump, licence unrestricted, plus the manager/phone/model/serial fields that make maintenance follow-up possible.
- Korea shows the regulatory route to freshness (monthly inspection + reporting + fines) — relevant to the Ministry audience as a policy recommendation, while the app can implement the soft version: a "last inspected" date per AED and a monthly reminder/one-tap confirmation for the registered manager.
- The mismatch between the dataset description (hours included) and the documented fields is a cautionary example: availability hours are the field most often missing or unreliable even in a mature national register.
- Publishing manager name and phone in an open API is a Korean choice that would raise GDPR questions in Poland; an institutional phone number (as in Japan's schema) is the safer equivalent.

### Gaps
- National total of registered AEDs in E-Gen for 2025/2026: not found.
- Kakao Map / Naver Map integration of AED layers: no source found confirming or denying it.
- Seoul smart-city platform integration of AED status: not found.
- Text of the 2025 amendment on inspection-reporting fines was not read in the statute itself; relies on one press report of a municipal announcement.
- Evidence that IoT cabinets feed status into the national register (as opposed to vendor dashboards): not found.
- Whether the API really lacks opening-hours fields or the portal page simply omits them: needs a live API call with a service key.

---

## Singapore: myResponder, national AED registry, AED-on-Wheels, HDB lift-lobby AEDs, DARE, OneMap; measured outcomes

### Takeaway
Singapore runs the most integrated system of the group: a **joint SCDF + Singapore Heart Foundation national registry ("Registry for AED Integration", >11,000 AEDs)** feeds the **myResponder** app, which the 995 dispatch centre uses to alert over 250,000 registered community first responders, with a 2024 redesign that sizes the alert radius by the responder's travel mode and treats **moving vehicles (taxis, private-hire cars, postal/courier vans, public buses) as mobile AEDs**. Outcomes are reported as counts (52,000+ responses, 150+ survivors with responder involvement) rather than as a demonstrated rise in the national survival rate.

### Cited Findings

**myResponder and the responder network**
- Save-A-Life Initiative and the first myResponder launched in 2015: alerts to community first responders (CFRs) near a cardiac arrest plus a live map of public AEDs. Minor-fire alerts added in 2018. Upgraded version by SCDF and HTX in 2024. [fetched] — [International Fire & Safety Journal](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)
- CFRs grew from about 3,000 (2015) to over 204,000 (Jan 2025), more than 246,300 (Nov 2025) and over 250,000 (Dec 2025). [fetched/snippet] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community); [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/); [MHA speech, 2025](https://www.mha.gov.sg/media-room/newsroom/responders-partners-volunteers-appreciation-event-2025/)
- Cumulative to late 2025: CFRs responded to over 52,000 cardiac-arrest and minor-fire cases; more than 150 (IFSJ: "over 157") cardiac-arrest victims survived with CFR involvement. [fetched] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community); [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)
- **Alert radius by travel mode**: original design 400 m; the 2024 upgrade lets a CFR choose foot / bicycle / vehicle, with 800 m for cyclists and up to 1.5 km for drivers. [fetched, trade press] — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)
- **"Respond Together" (2024)**: responders see each other's positions, chat in-app, and send photos/videos to SCDF's Operations Centre. Dispatcher video-call guidance is described as a planned feature. [fetched] — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)
- More than 3,000 out-of-hospital cardiac arrests occur in Singapore annually. [fetched] — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)
- SCDF received the Singapore Good Design Mark Gold Award on 25 Nov 2025 for myResponder. [fetched] — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/)

**Registry and open data**
- More than 11,000 registered AEDs in the national registry; the Registry for AED Integration is jointly managed by SCDF and the Singapore Heart Foundation and is what myResponder uses to route CFRs to the nearest AED. [fetched] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community)
- data.gov.sg hosts an SCDF "AED Locations" dataset (data as of Dec 2024, last updated 2024-12-19, queryable through the datastore_search API) and a separate GeoJSON dataset of publicly accessible AEDs (last updated 2025-11-13); SCDF points users to myResponder for current locations. [snippet] — [data.gov.sg AED Locations](https://data.gov.sg/datasets/d_e8934d28896a1eceecfe86f42dd3c077/view); [data.gov.sg GeoJSON](https://data.gov.sg/datasets/d_4e6b82c58a8a832f6f1fee5dfa6d47ea/view)

**Fixed AED density: HDB lift lobbies**
- Over 5,400 AEDs were installed under the Save-A-Life Initiative, mostly at HDB (public housing) lift lobbies and private condominiums; the stated planning ratio was one AED for every two to three blocks. [snippet; dates of the replies not confirmed] — [MHA written reply on Save-A-Life effectiveness](https://www.mha.gov.sg/media-room/newsroom/written-reply-to-parliamentary-question-on-the-effectiveness-of-the-save-a-life-initiative-by-mr-k-shanmugam-minister-for-home-affairs-and-minister-for-law/)

**Mobile AEDs: AED-on-Wheels / AED-on-Buses**
- AED-on-Wheels started in 2015 with 100 SMRT taxis (Temasek Foundation); 50 HDT Singapore Taxi vehicles added Nov 2019 (with Singapore Heart Foundation); 50 Grab private-hire vehicles from 28 Jan 2021; ComfortDelGro later; Singapore Post joined March 2023; Ninja Van also named as a partner. [fetched/snippet] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community); [Temasek Foundation](https://www.temasekfoundation.org.sg/programmes-s/SMRT-Temasek-Foundation-AED-on-Wheels); [SCDF Grab launch](https://www.scdf.gov.sg/home/about-scdf/media-room/latest-happenings/newsarticledetail/launch-of-the-singapore-civil-defence-force-grab-aed-on-wheels-programme-on-28-january-2021); [MHA speech, HDT launch 2019](https://www.mha.gov.sg/media-room/newsroom/launch-of-the-hdt-singapore-taxi---singapore-heart-foundation-aed-on-wheels-programme---speech-by-mr-amrin-amin-senior-parliamentary-secretary-ministry-of-home-affairs-and-ministry-of-health/)
- The programme now totals **543 vehicles**; trained AED-on-Wheels drivers have responded to **1,293 myResponder cases**. [fetched, late 2025] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community)
- **AED-on-Buses**: launched 8 Nov 2024 with 53 SBS Transit buses on routes 138, 268 and 851 plus three patrol cars; Tower Transit joined 28 Oct 2025 with 52 buses on routes 78, 79 and 98. Mechanism: the app tells a CFR that **an AED is on an approaching bus**; the responder flags the bus at the nearest stop and takes the AED. [fetched] — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community); [Tower Transit](https://www.towertransit.sg/media/52-tower-transit-buses-to-be-equipped-with-aeds)
- SMRT taxi drivers had arrived on scene in 149 cardiac-arrest cases as of September 2019. [snippet] — [MHA speech, 2019](https://www.mha.gov.sg/media-room/newsroom/launch-of-the-hdt-singapore-taxi---singapore-heart-foundation-aed-on-wheels-programme---speech-by-mr-amrin-amin-senior-parliamentary-secretary-ministry-of-home-affairs-and-ministry-of-health/)

**National outcomes**
- OHCA survival to discharge: 4.1% (2014) → 6.5% (2016); 5.9% (2018) → 6.2% (2019) → 4.3% (2020) → 3.8% (2021). [snippet] — [Singapore OHCA Data Report 2011–2021](https://www.myheart.org.sg/wp-content/uploads/2024/10/OHCA-Data-Report-2011-2021.pdf); [MHA written reply](https://www.mha.gov.sg/media-room/newsroom/written-reply-to-parliamentary-question-on-the-effectiveness-of-the-save-a-life-initiative-by-mr-k-shanmugam-minister-for-home-affairs-and-minister-for-law/)

### Inferences
- The transferable ideas are architectural: (1) one registry with two co-owners (emergency service + heart NGO) that is the single source for the dispatch centre, the app and open data; (2) AEDs modelled as **entities with a possibly moving position** (vehicle AEDs, bus routes) rather than only fixed points; (3) alert radius computed from travel mode, i.e. reachability in time, not a fixed circle.
- "AED on an approaching bus" can be imitated with public-transport GTFS-realtime feeds: any Polish city that publishes vehicle positions could flag AED-equipped vehicles.
- Singapore's published national survival rate fell in 2020–2021 (pandemic years) despite the growing network, so the team should not claim that apps alone raise national survival; use the response/survivor counts and the Japanese/Korean cohort evidence instead.
- The open dataset on data.gov.sg is a periodic snapshot while the live registry sits behind the app — the opposite of Korea's real-time open API. For dane.gov.pl the Korean/Taiwanese (daily refresh) pattern is the stronger precedent.

### Gaps
- DARE programme (Dispatcher-Assisted first REsponder): only a 2018 MOH speech link surfaced; no details or numbers retrieved.
- OneMap AED theme/layer: not confirmed in this session.
- Field schema of the data.gov.sg AED datasets: not retrieved.
- How AEDs enter and are re-verified in the Registry for AED Integration (owner self-registration? audits?): not found.
- Delivery-rider participation specifically (as opposed to courier/postal vans): not confirmed.
- OHCA survival data after 2021 and any study isolating myResponder's effect on survival: not found.
- The 800 m / 1.5 km radii come from trade press, not from an SCDF document.

---

## Taiwan: MOHW public AED registry and open data, "AED safe place" certification, apps and LINE integrations

### Takeaway
Taiwan's Ministry of Health and Welfare runs a national registry (公共場所AED急救資訊網, tw-aed.mohw.gov.tw) whose full content is republished as an **open dataset that auto-updates daily** with **structured weekday / Saturday / Sunday opening-hours fields and an "open 24/7 to the public" flag**; a staff-training-based **"AED安心場所" (AED Safe Place) certification** gives venues a public badge; and an NGO-run **LINE official account ("聽見AED")** connected to the national fire dispatch alerts 31,000+ volunteers without requiring a separate app.

### Cited Findings

**Registry and open dataset**
- National dataset "AED位置資訊" (data.gov.tw ID 12063), source MOHW Department of Medical Affairs; **automatically updated daily since 15 January 2022**; available as CSV and ODF from MOHW. [snippet] — [data.gov.tw 12063](https://data.gov.tw/en/datasets/12063); [MOHW DOMA download page](https://dep.mohw.gov.tw/DOMA/cp-2710-41728-106.html)
- Field list (Chinese originals): 場所名稱 (venue name); 場所縣市 (county/city); 場所區域 (district); 場所地址 (address); 場所分類 (venue category); 場所類型 (venue type); 其他類型 (other type); 場所描述 (venue description); AED放置地點 (where the AED is placed); AED地點描述 (description of the AED spot); 地點LAT; 地點LNG; 全年全天開放大眾使用 (open to the public all day all year, flag); 周一至周五起 / 周一至周五迄 (Mon–Fri from/to); 周六起 / 周六迄 (Sat from/to); 周日起 / 周日迄 (Sun from/to); 開放使用時間備註 (hours notes); 開放時間緊急連絡電話 (emergency contact phone during open hours). The English portal page additionally shows a Location ID and an AED ID. [snippet] — [NCHC mirror of dataset 12063](https://scidm.nchc.org.tw/en/rating/dataset/best_wish12063/4); [data.gov.tw 12063](https://data.gov.tw/en/datasets/12063)
- Local datasets vary: **New Taipei City's dataset includes battery and electrode-pad expiry dates**, per-day open/close fields (e.g. `mon_stime`, `mon_dtime`) and both TWD97 and WGS84 coordinates; Tainan mirrors the national hour fields (updated yearly); Hualien and Yilan publish slimmer sets without structured hours. [snippet] — [New Taipei 125699](https://data.gov.tw/dataset/125699); [Tainan 143323](https://data.gov.tw/dataset/143323); [Hualien 148153](https://data.gov.tw/dataset/148153); [Yilan 136353](https://data.gov.tw/dataset/136353)
- Registry counts quoted in MOHW press releases: 7,384 registered AEDs and 3,423 certified safe places; an earlier release gave 6,672 registered (of an estimated 10,000+ nationwide) and 2,795 certified. **Both releases are undated in my results and likely several years old.** [snippet] — [MOHW](https://mohw.gov.tw/cp-16-20744-1.html); [MOHW](https://mohw.gov.tw/cp-16-9761-1.html)

**AED Safe Place certification**
- A venue with an AED where 70% of staff have completed AED training may apply to the municipal/county health authority for certification. [snippet] — [Regulations on AEDs in public places, law.moj.gov.tw](https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=L0020182)

**Apps and LINE**
- **聽見AED (LINE@ platform)**, run by the NGO 台灣愛陌生安全推廣協會: shows AED locations across Taiwan and notifies nearby "guardian heroes"; connected to the national disaster/fire command centre since August 2024; 31,169+ guardians enrolled; credited with 27 lives saved in a little over a year; the organisers want AEDs listed on Google Maps. [snippet, Oct 2025 article] — [UDN](https://udn.com/news/story/7266/9108974)
- **全民急救AED app**: built by MOHW with the Taiwan Society of Emergency Medicine; linked directly to the MOHW registry; nearest-AED search, no-dial emergency reporting, first-aid material. [snippet] — [MOHW](https://mohw.gov.tw/cp-2704-20744-1.html)
- **急救先鋒 app** (National Fire Agency, Ministry of the Interior): registered citizens are summoned at the moment 119 dispatches an ambulance. [snippet] — [App Store](https://apps.apple.com/tw/app/%E6%80%A5%E6%95%91%E5%85%88%E9%8B%92/id6446128142)
- **全民守護者 app** (Taipei City Fire Department and partners): shows nearest AED and notifies nearby volunteers on a 119 call; reported as Taipei-only. **視訊119 app** lets dispatchers see the scene by video. [snippet] — [TVBS Health](https://health.tvbs.com.tw/medical/316877)

### Inferences
- Taiwan's hour model (24/7 flag + three day-groups with from/to + free-text note + phone valid during open hours) is a pragmatic middle ground between Japan's single weekday-string/one-interval model and full OSM `opening_hours` syntax; it is easy for facility managers to fill in and easy to turn into an "open now" filter.
- New Taipei shows that consumable expiry dates can be published as open data at municipal level — a precedent for adding optional `battery_expiry` / `pads_expiry` fields to a Polish schema.
- The LINE approach removes the install barrier that starves AED GO in Japan: volunteers join through a messenger they already use. The Polish analogue would be a WhatsApp/Messenger/Telegram bot or web push from a PWA rather than a native app.
- A "Safe Place" badge (AED + trained staff share) is a cheap incentive layer and a filterable attribute on the map.

### Gaps
- tw-aed.mohw.gov.tw refused the connection during this session, so registry features, current counts and registration/inspection workflow are unverified first-hand.
- Current (2025–2026) number of registered AEDs and certified venues: not found.
- Inspection frequency and any penalties under the Taiwanese regulation: not read.
- Technical design of the 聽見AED LINE bot (location sharing, how dispatch triggers it): not found.

---

## Hong Kong and mainland China (notable items only)

### Takeaway
Hong Kong's Fire Services Department runs a small but cleanly open registry (CARE) with a **no-auth, trilingual CSV API** and unusually explicit **access-restriction fields**; in mainland China, Shenzhen links its 120 dispatch to consumer platforms (Tencent's WeChat-based 企鹅急救, and from 2026 Meituan delivery riders carrying AEDs).

### Cited Findings

**Hong Kong — CARE (Centralized AED Registry for Emergency, "AED搵得到")**
- FSD announced the "AED Anywhere for Anyone" programme and launched CARE on 22 June 2021. [snippet] — [HK Government press release](https://www.info.gov.hk/gia/general/202106/22/P2021062100622p.htm)
- By end of 2025 the platform listed more than 4,000 AEDs; FSD installed 130+ AEDs at its own premises for public use and fitted AEDs to 700+ of its vehicles and vessels. (An older press figure was about 2,700.) [snippet] — [FSD Review 2025](https://www.hkfsd.gov.hk/images/review_25/sc/11_emergency_preparedness_education.pdf); [The Standard](https://www.thestandard.com.hk/news/article/213731/More-AEDs-installed-at-bus-regulators-kiosks-in-various-districts)
- **Open API** (spec v1.0, 28 Jan 2022): `GET https://es.hkfsd.gov.hk/aed_api/export_aed.php?lang=EN|TC|SC`, CSV, UTF-8, **no authentication**; also listed on data.gov.hk. [fetched, PDF text extracted] — [FSD AED Location Data Specification](https://www.hkfsd.gov.hk/datagovhk/data_dictionaries/DD_CARE_chi.pdf); [data.gov.hk](https://data.gov.hk/en-data/dataset/hk-fsd-fsd1-fsdaedapi)
- Fields: AED name; AED address; detailed location of the AED installed; latitude; longitude (WGS84); **whether the AED can be used by anyone (Yes/No)**; **person allowed to operate** (Anyone / Staff Only / Trained Personnel Only / Trained Staff Only); **person who has access** (Anyone / Staff Only / Accompanied By Staff Only / Teaching And Non-Teaching Staff / Trained Staff Only); **ground level category (Street Level / Non-Street Level)**; service hour remark; AED brand; AED model; AED remark. [fetched] — [FSD AED Location Data Specification](https://www.hkfsd.gov.hk/datagovhk/data_dictionaries/DD_CARE_chi.pdf)

**Mainland China — Shenzhen**
- Callers to 120 can be connected with six internet platforms; dispatchers see, on Tencent's 企鹅急救 (Penguin First Aid) platform, the number and distribution of dispatchable volunteers and AEDs near an incident; the WeChat mini-program supports video links so a volunteer fetching an AED can talk with the dispatcher and the caller en route. [snippet; the sz.gov.cn page failed to load when fetched] — [Shenzhen Government Online](https://www.sz.gov.cn/en_szgov/news/latest/content/post_12896743.html)
- The Tencent platform is reported to be connected to 120 dispatch systems in 10+ cities, linking about 30,000 AEDs and 1 million first-aid volunteers (national figures, press-reported). [snippet] — [ifeng Tech](https://tech.ifeng.com/c/8ufzPIINmTP)
- July 2026: Shenzhen launched a "5-minute social first-aid circle" AED delivery project — Tencent provides the dispatch platform and Meituan plugs its instant-delivery rider network into the city's emergency system; first phase to train 2,000 Shenzhen riders in AED delivery, 500 of them certified in first aid. [snippet; attribution to this exact URL not verified] — [Science and Technology Daily, 2026-07-15](https://www.stdaily.com/web/gdxw/2026-07/15/content_547790.html)
- 城安应急 app (Shenzhen Urban Public Safety and Technology Institute): one-tap SOS plus a map dynamically showing volunteers and AEDs within 1 km. [snippet] — [App Store](https://apps.apple.com/us/app/%E5%9F%8E%E5%AE%89%E5%BA%94%E6%80%A5/id1536085015?uo=4)

### Inferences
- Hong Kong's access fields answer the question bystanders actually have ("can I, a stranger, take it, and is it at street level?") better than any other schema found; they are trivial to add as enums.
- A no-key CSV endpoint with a `lang` parameter is the lowest-friction open-data design in the set and a good model for a multilingual Polish export (PL/EN/UA).
- Shenzhen's rider model is Singapore's AED-on-Wheels taken to gig-economy scale: the AED travels to the patient via whoever is already moving nearby.

### Gaps
- Shenzhen-specific AED and volunteer counts, and any outcome data for the Tencent/Meituan schemes: not found.
- The Shenzhen government article could not be read directly (connection reset); details rest on the search summary.
- Whether CARE has a verification/expiry process for entries: not found.

---

## Cross-cutting innovations (drones, convenience stores/vehicles, IoT cabinets, indoor/AR navigation, dispatch integration, wearables, gamification, multilingual)

### Takeaway
The innovations with real deployments in Asia are (1) **dispatch-integrated volunteer alerting**, (2) **AEDs on moving vehicles and in 24h retail**, (3) **explicit data-freshness mechanics** (grades, two-person confirmation, expiry, daily refresh), (4) **video links to dispatchers**, and (5) **IoT self-reporting cabinets**; drone delivery in Asia is still at the test/modelling stage, and I found no evidence of AR or indoor-navigation-to-AED or wearable integration in these countries.

### Cited Findings
- **Dispatch → volunteer alerting with nearest-AED routing**: Singapore myResponder (250,000+ responders, 52,000+ responses) — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/); Japan AED GO (3 cities, no ambulance-beating case in FY2023) — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf); Taiwan 急救先鋒 and 聽見AED — [App Store](https://apps.apple.com/tw/app/%E6%80%A5%E6%95%91%E5%85%88%E9%8B%92/id6446128142), [UDN](https://udn.com/news/story/7266/9108974); Shenzhen/Tencent — [Shenzhen Government Online](https://www.sz.gov.cn/en_szgov/news/latest/content/post_12896743.html).
- **Travel-mode-aware alert radius** (foot / bicycle 800 m / car 1.5 km): Singapore 2024 — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/).
- **Responder coordination** (see other responders, chat, send photo/video to the operations centre): Singapore "Respond Together" — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/).
- **Mobile AEDs**: Singapore 543 vehicles + 105 buses on six routes, app notifies of an AED on an approaching bus — [SCDF story](https://www.scdf.gov.sg/home/about-scdf/media-room/our-stories/storyarticledetail/on-the-road-together--embarking-on-the-lifesaving-journey-with-scdf-s-partners-and-the-community); Hong Kong 700+ FSD vehicles/vessels — [FSD Review 2025](https://www.hkfsd.gov.hk/images/review_25/sc/11_emergency_preparedness_education.pdf); Shenzhen Meituan riders (2026) — [Science and Technology Daily](https://www.stdaily.com/web/gdxw/2026-07/15/content_547790.html).
- **24h retail as AED hosts**: Japanese municipality–convenience-store agreements (Shinjuku 50 stores from 2025; Naha 118; Owariasahi all stores since 2014) — [Shinjuku Ward](https://www.city.shinjuku.lg.jp/whatsnew/pub/2025/0701-01.html), [Ryukyu Shimpo](https://ryukyushimpo.jp/news/prentry-199909.html), [FDMA](https://www.fdma.go.jp/publication/ugoki/items/2901_30.pdf).
- **Auto-phoning the AED's host building** on SOS (Twilio-based "AED Area Call"): Coaido119, Japan, 2017 — [INTERNET Watch](https://internet.watch.impress.co.jp/docs/column/chizu3/1100451.html).
- **Freshness/trust mechanics**: A–D accuracy grade with colour-coded pins (Japan foundation map) — [qqzaidanmap.jp](https://www.qqzaidanmap.jp/); geofenced edits + two confirmations + auto-removal (team ASUKA) — [App Store](https://apps.apple.com/jp/app/id1567351854); daily automatic open-data refresh (Taiwan) — [data.gov.tw](https://data.gov.tw/en/datasets/12063); real-time API (Korea) — [data.go.kr](https://www.data.go.kr/data/15000652/openapi.do); legally required monthly inspection with reporting fines (Korea) — [Asia Economy](https://www.asiae.co.kr/en/article/2025030516195942771).
- **Gamified data collection**: points, national ranking, gacha characters, badges, quizzes (team ASUKA) — [App Store](https://apps.apple.com/jp/app/id1567351854); planned activity ranking to raise volunteer activity (AED GO) — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf).
- **IoT self-reporting AEDs/cabinets**: Korea (Xcure XAFE outdoor box, SK C&C integrated control, CU Medical remote management) — [Asia Economy](https://www.asiae.co.kr/en/article/2025082510260823772), [Daum](https://v.daum.net/v/20231024153901209), [Asia Economy](https://www.asiae.co.kr/en/article/2025041009523257823); Japan's MHLW research group names connected AEDs as the route to a real-time national picture — [MHLW R5 report](https://mhlw-grants.niph.go.jp/system/files/download_pdf/2023/202308050A.pdf).
- **Video to dispatcher**: Korea video-instructed DA-CPR, nationwide guideline 2020, adjusted OR 1.81 for survival to discharge in Seoul cohort — [Scientific Reports 2021](https://link.springer.com/10.1038/s41598-021-95077-5); Taiwan 視訊119 — [TVBS](https://health.tvbs.com.tw/medical/316877); Shenzhen WeChat mini-program video link — [Shenzhen Government Online](https://www.sz.gov.cn/en_szgov/news/latest/content/post_12896743.html); Singapore planned — [IFSJ](https://internationalfireandsafetyjournal.com/myresponder-scdf-network/).
- **Messenger-native delivery instead of a dedicated app**: LINE (Taiwan 聽見AED) — [UDN](https://udn.com/news/story/7266/9108974); WeChat mini-program (China) — [Shenzhen Government Online](https://www.sz.gov.cn/en_szgov/news/latest/content/post_12896743.html).
- **Access and level metadata**: Hong Kong enums for who may access/operate and street-level vs non-street-level — [FSD data specification](https://www.hkfsd.gov.hk/datagovhk/data_dictionaries/DD_CARE_chi.pdf); Japan's 設置位置 (exact position, e.g. "1F office") and paediatric-capability flag — [definition document](https://data.bodik.jp/dataset/599132da-b451-47c0-9a6e-2ca65b899bcd/resource/5bfd47e5-6fa4-418c-8962-04cbf8b84409/download/cusers00000241downloadsdatadefinitionaed.pdf).
- **Multilingual**: Hong Kong API returns EN / Traditional Chinese / Simplified Chinese via a `lang` parameter — [FSD data specification](https://www.hkfsd.gov.hk/datagovhk/data_dictionaries/DD_CARE_chi.pdf). By contrast team ASUKA is Japanese-only — [App Store](https://apps.apple.com/jp/app/id1567351854).
- **Drones**: Japan has tested AED delivery by drone at a golf course near Chiba, with the caller requesting an AED through a smartphone app; Japanese trials have typically used manually piloted aircraft. [snippet; article undated in my results] — [tech360.tv](https://www.tech360.tv/japan-tests-aed-delivery-drones-revolutionizing-emergency-response-golf-courses)

### Inferences
- Across all five jurisdictions the weakest data field is the same: **real availability right now** (hours, locked building, staff-only). Systems that address it do so with structured hours (Taiwan), access enums (Hong Kong), 24h hosts (Japanese convenience stores, Singapore lift lobbies) or mobile AEDs (Singapore, Shenzhen). An app that ranks AEDs by "reachable and accessible now" rather than by straight-line distance would be differentiated against every system reviewed here.
- No reviewed system publishes a per-record provenance trail (which source, when last confirmed, by whom) as open data; Japan's grade is the nearest. For an aggregator merging scattered Polish sources this is the natural unique feature.
- Gamification is used for data collection in Japan, but the published evidence is on feature existence, not on effect size; it should be pitched as an engagement hypothesis.

### Gaps
- AR or indoor navigation to an AED: no deployment found in any of the countries.
- Wearable integration (smartwatch fall/arrest detection linked to AED/responder systems): nothing found.
- Drone AED pilots in Korea, Taiwan and Singapore: the search summary mentioned a Taipei/New Taipei base-location optimisation study on 2019 data and two Korean publications in a scoping review, but I could not tie those claims to specific URLs, so they are not listed as findings.
- Vending-machine AEDs in Japan: not confirmed.
- Outcome evidence for convenience-store AED programmes and for IoT cabinets: not found.

---

## Feasibility of each innovation as a 24–48h hackathon web-app feature, and the data it needs

### Takeaway
Most data-quality innovations (freshness grade, crowd confirmation, "open now", access enums, multilingual export, standard schema + API) are fully buildable in a weekend from existing open data; responder alerting, video dispatch, mobile AEDs and IoT can only be shown as mocked demos because they depend on dispatch-centre or hardware integration.

### Cited Findings
- Reference schemas available to copy field-by-field: Japan 22 fields — [definition document](https://data.bodik.jp/dataset/599132da-b451-47c0-9a6e-2ca65b899bcd/resource/5bfd47e5-6fa4-418c-8962-04cbf8b84409/download/cusers00000241downloadsdatadefinitionaed.pdf); Korea API fields and three operations — [data.go.kr](https://www.data.go.kr/data/15000652/openapi.do); Taiwan hour fields — [NCHC mirror](https://scidm.nchc.org.tw/en/rating/dataset/best_wish12063/4); Hong Kong access enums and no-auth CSV endpoint — [FSD data specification](https://www.hkfsd.gov.hk/datagovhk/data_dictionaries/DD_CARE_chi.pdf).
- Reference rules available to copy: accuracy grade — [qqzaidanmap.jp](https://www.qqzaidanmap.jp/); two-confirmation / geofence / expiry — [App Store: team ASUKA](https://apps.apple.com/jp/app/id1567351854); ID never reused — [definition document](https://data.bodik.jp/dataset/599132da-b451-47c0-9a6e-2ca65b899bcd/resource/5bfd47e5-6fa4-418c-8962-04cbf8b84409/download/cusers00000241downloadsdatadefinitionaed.pdf).

### Inferences
Feasibility ratings are my own assessment, not sourced.

| Idea (origin) | 24–48h feasibility | Data / tech needed |
|---|---|---|
| Unified schema = Japan's 22 fields + Taiwan hours + HK access enums + optional pad/battery expiry (New Taipei) | High — it is a mapping table plus ETL | Source datasets; column mapping; stable ID rule (never reuse) |
| Freshness grade A–D with coloured pins (Japan foundation) | High — one function over `last_verified`, `installed_at`, presence of expiry dates | Any date column per record; fall back to dataset publication date |
| "Open now / accessible to me" filter and ranking (Taiwan + HK) | High | Structured hours (parse free text with rules or an LLM offline), access enum, street-level flag |
| Crowd confirmation: "I see it / it's gone" with geofence + 2-confirmation rule + auto-expiry (team ASUKA) | High for the mechanism; needs no login for a demo | Browser Geolocation API; a small table of confirmations |
| Photo of the AED spot attached to a confirmation | Medium-high | File upload + storage; moderation out of scope |
| Gamified leaderboard / badges for verifiers (team ASUKA) | Medium — simple points table; cosmetic depth is optional | Confirmation events with a pseudonymous user ID |
| Open API in the Korean shape: by region, by lat/lon radius, full dump; CSV with `lang` param (HK) | High | Spatial index (PostGIS or in-memory); static export for dane.gov.pl |
| Per-record provenance (source, date, confidence) published in the dataset | High — by-product of the ETL | Keep source ID and fetch timestamp per row |
| Deduplication across overlapping sources | Medium — distance + name similarity threshold | Coordinates, names; manual review list for ambiguous pairs |
| Route to nearest *available* AED, with walking time | High | Routing API (OSRM/Valhalla on OSM); availability from hours |
| Travel-mode-aware reach (foot / bike / car isochrones; Singapore) | Medium | Isochrone API |
| "Call the building" button / auto-call host landline (Coaido Area Call) | Button: high. Automated simultaneous voice calls: medium (telephony API, cost, consent) | Phone number per AED |
| Messenger/web-push alerting of nearby volunteers (Taiwan LINE, Singapore) | Low-medium — demo with web push to test devices only; real use needs dispatch integration | Volunteer positions, consent, a trigger source |
| Mobile AEDs on buses/taxis (Singapore) | Low-medium — mock with one GTFS-realtime feed and a hand-made list of "AED-equipped" vehicles | Vehicle positions; operator list of equipped vehicles (does not exist yet) |
| Manager monthly check reminder + one-tap "inspected" (Korea's legal model, soft version) | Medium | Manager contact per AED; email/SMS sender |
| Coverage-gap map (where no AED is reachable in N minutes, by time of day) | Medium-high — strong for the Ministry audience | Population grid + AED hours + isochrones |
| IoT cabinet status feed | Low — simulate with a fake device posting heartbeat JSON | Vendor APIs, none public |
| Video link to dispatcher | Out of scope — needs the dispatch centre | — |
| Drone delivery | Out of scope beyond a slide | — |

- Suggested differentiating bundle, given what no reviewed Asian system does in one place: aggregated dataset with **per-record provenance + computed freshness grade + structured availability/access**, exposed through a Korea-style open API and a map that ranks by "reachable and usable now", with a team-ASUKA-style confirmation loop feeding the grade back into the open dataset.

### Gaps
- I did not check which of these fields exist in current Polish sources (that is another researcher's scope), so the "data needed" column states requirements, not availability.
- No source quantifies how much crowd confirmation or gamification improves AED data accuracy; effect sizes are unknown.
