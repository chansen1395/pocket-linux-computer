# Research — the offline content pack ("trove")

Verified 2026-10-16 (every URL below was fetched: HTTP 200/206 with the stated size, or the listing page visibly
shows the file). Items that could not be fetched are marked **unverified**. Sizes are decimal (1 MB = 10^6 B).

Two tiers: **v0** = fits the 64 GB microSD (target ≤ 25 GB, see the list at the end); **2 TB** = everything else.
Everything lands under `/data/` (`kiwix/`, `docs/`, `books/`, `maps/`, `models/`).

## Readers on the device (all in Debian trixie arm64, verified on packages.debian.org)

| Content | Reader | Package / install |
|---|---|---|
| `.zim` | `kiwix-serve` on `http://127.0.0.1:8090` (any browser, also Pocket TUI's "Knowledge" tab); `kiwix` desktop if wanted | `kiwix-tools 3.7.0-1.1` (`apt`), `kiwix 2.4.1`; prebuilt newer `kiwix-tools_linux-aarch64-3.8.2.tar.gz` (20.5 MB) from `https://download.kiwix.org/release/kiwix-tools/` |
| PDF | `zathura` (console/keyboard) or `okular` (desktop) | `zathura 0.5.11-1`, `okular 25.04.2` |
| EPUB | `foliate` | `foliate 3.3.0` (package `4.~really3.3.0-1`) |
| HTML doc trees (Python docs, Debian docs) | browser via `file://` or the same nginx that serves Pocket TUI | — |
| Dictionary | `dict word` (dictd + GCIDE + WordNet, fully offline), `goldendict-ng` GUI | `dictd 1.13.1`, `dict-gcide 0.48.5`, `dict-wn 3.0-39`, `goldendict-ng 25.06.0` |
| `tldr` pages | `tldr <cmd>` (tealdeer caches pages locally after one `tldr --update`) | `tealdeer 1.7.2` |
| Maps | CoMaps / Organic Maps (Flatpak), browser + MapLibre page, `mapscii` in a terminal — see §4 | — |

Serve the ZIMs (one library file, survives new ZIMs being added):

```sh
sudo apt install -y kiwix-tools
kiwix-manage /data/kiwix/library.xml add /data/kiwix/*.zim
kiwix-serve --port=8090 --library /data/kiwix/library.xml      # http://127.0.0.1:8090/
```

## 1. Kiwix ZIMs (`https://download.kiwix.org/zim/<folder>/<file>`)

Current filenames read from the directory listings on 2026-10-16; byte sizes from `Content-Length`; every file has a
`<file>.sha256` sidecar next to it (used in the manifest). License: Wikimedia projects CC BY-SA 4.0; iFixit
CC BY-NC-SA 3.0; Stack Exchange CC BY-SA 4.0; Appropedia CC BY-SA; ArchWiki GFDL 1.3; DevDocs = each project's own
free doc license; `zimgit-*` are Kiwix-curated collections of free/PD documents (license varies per document).

### 1a. Encyclopedia and medicine

| Name (catalog title) | Folder | Current file | Size | Tier | Notes |
|---|---|---|---|---|---|
| Simple English Wikipedia, with pictures | `wikipedia` | `wikipedia_en-simple_all_maxi_2026-09.zim` | 3.12 GB | 2 TB | note the **hyphen** `en-simple`; `_maxi` = pictures |
| Simple English Wikipedia, no pictures | `wikipedia` | `wikipedia_en-simple_all_nopic_2026-09.zim` | 1.09 GB | **v0** | also `_mini` (intros only) 530 MB |
| "Best of Wikipedia" (top articles, full text + pictures) | `wikipedia` | `wikipedia_en_top_maxi_2026-09.zim` | 6.99 GB | **v0** | `_nopic` 2.75 GB, `_mini` 297 MB |
| English Wikipedia, all articles, intro only, no pictures | `wikipedia` | `wikipedia_en_all_mini_2026-09.zim` | 14.39 GB | 2 TB | the "every article exists" option if v0 budget is raised |
| English Wikipedia, all articles, no pictures | `wikipedia` | `wikipedia_en_all_nopic_2026-06.zim` | 52.69 GB | 2 TB | |
| English Wikipedia, all articles, with pictures | `wikipedia` | `wikipedia_en_all_maxi_2026-08.zim` | 127.42 GB | 2 TB | the 2 TB headline item |
| **WikiMed** medical encyclopedia (was `wikimed_en_all_maxi`; now lives under the wikipedia folder) | `wikipedia` | `wikipedia_en_medicine_maxi_2026-10.zim` | 1.86 GB | **v0** | `_nopic` 1.05 GB |
| Post Disaster Resource Library | `other` | `zimgit-post-disaster_en_2024-05.zim` | 645 MB | **v0** | |
| Medical Library | `other` | `zimgit-medicine_en_2024-08.zim` | 70 MB | **v0** | |
| Water Treatment Library | `other` | `zimgit-water_en_2024-08.zim` | 21 MB | **v0** | |
| A Library of Knots | `other` | `zimgit-knots_en_2024-08.zim` | 28 MB | **v0** | |
| Food for Preppers | `other` | `zimgit-food-preparation_en_2025-04.zim` | 98 MB | **v0** | |
| Appropedia (appropriate tech, water, energy, building) | `other` | `appropedia_en_all_maxi_2026-02.zim` | 582 MB | **v0** | |
| TruePrepper (site scrape) | `other` | `trueprepper.com_en_all_2026-05.zim` | 1.42 GB | 2 TB | © TruePrepper, distributed via the Kiwix library; personal use |
| Wikibooks (first aid, cookbook, survival, electronics…) | `wikibooks` | `wikibooks_en_all_maxi_2026-04.zim` | 6.18 GB | 2 TB | `_nopic` 3.51 GB |
| Wikivoyage | `wikivoyage` | `wikivoyage_en_all_maxi_2026-09.zim` | 1.07 GB | **v0** | `_nopic` 260 MB |
| iFixit repair guides | `ifixit` | `ifixit_en_all_2025-12.zim` | 3.57 GB | **v0** | |
| Wiktionary, English | `wiktionary` | `wiktionary_en_all_nopic_2026-08.zim` | 9.16 GB | 2 TB | **no `_maxi` exists**; only `nopic` |
| Wiktionary, Simple English | `wiktionary` | `wiktionary_en_simple_all_nopic_2026-04.zim` | 26 MB | **v0** | plus `dict-gcide`/`dict-wn` for a real dictionary |
| ArchWiki | `other` | `archlinux_en_all_maxi_2026-07.zim` | 36 MB | **v0** | |
| OpenStreetMap wiki | `other` | `openstreetmap-wiki_en_all_nopic_2026-07.zim` | 478 MB | 2 TB | |
| CrashCourse (videos) | `other` | `crashcourse_en_all_2026-05.zim` | 21 GB | 2 TB | license **unverified** |
| Khan Academy (videos, 2023) | `other` | `khanacademy_en_all_2023-03.zim` | 168 GB | 2 TB | CC BY-NC-SA; stale (2023) |
| **WikiHow** | — | — | — | — | **gone**: `/zim/wikihow/` is 404 and nothing matches in the Kiwix catalog on 2026-10-16 |
| Hesperian ZIM | — | — | — | — | none exists; use the Hesperian PDFs in §2 |

### 1b. Project Gutenberg

No "mobile"/small subset exists any more; Kiwix now splits Gutenberg by Library of Congress class (`gutenberg_en_lcc-<class>`).
All in folder `gutenberg`. Public domain (US).

| File | Size | Tier | Class |
|---|---|---|---|
| `gutenberg_en_all_2025-11.zim` | 221.25 GB | 2 TB | everything (the 2023-08 one is 72 GB) |
| `gutenberg_en_lcc-r_2026-03.zim` | 1.9 GB | 2 TB | R = Medicine (historical) |
| `gutenberg_en_lcc-s_2026-03.zim` | 4.2 GB | 2 TB | S = Agriculture |
| `gutenberg_en_lcc-t_2026-03.zim` | 12 GB | 2 TB | T = Technology |
| `gutenberg_en_lcc-q_2026-03.zim` | 17 GB | 2 TB | Q = Science |
| `gutenberg_en_lcc-g_2026-03.zim` | 7.5 GB | 2 TB | G = Geography/recreation |
| `gutenberg_en_lcc-pr_2026-03.zim` / `-ps` | 16.15 GB / 16.02 GB | 2 TB | British / American literature |
| `gutenberg_en_lcc-pz_2026-03.zim` | 18 GB | 2 TB | juvenile |

v0 gets ~35 hand-picked EPUBs instead (§5).

### 1c. Stack Exchange (`stack_exchange` folder, `<site>.stackexchange.com_en_all_<date>.zim`)

| Site | Current file | Size | Tier |
|---|---|---|---|
| raspberrypi | `raspberrypi.stackexchange.com_en_all_2026-08.zim` | 298 MB | **v0** |
| outdoors | `outdoors.stackexchange.com_en_all_2026-08.zim` | 141 MB | **v0** |
| medicalsciences | `medicalsciences.stackexchange.com_en_all_2026-02.zim` | 61 MB | **v0** |
| ham | `ham.stackexchange.com_en_all_2026-08.zim` | 76 MB | **v0** |
| arduino | `arduino.stackexchange.com_en_all_2026-07.zim` | 259 MB | **v0** |
| 3dprinting | `3dprinting.stackexchange.com_en_all_2026-02.zim` | 120 MB | **v0** |
| cooking | `cooking.stackexchange.com_en_all_2026-07.zim` | 237 MB | **v0** |
| gardening | `gardening.stackexchange.com_en_all_2026-08.zim` | 927 MB | **v0** |
| lifehacks | `lifehacks.stackexchange.com_en_all_2026-08.zim` | 49 MB | **v0** |
| sustainability | `sustainability.stackexchange.com_en_all_2026-08.zim` | 28 MB | **v0** |
| diy (home improvement) | `diy.stackexchange.com_en_all_2026-08.zim` | 2.06 GB | 2 TB (first add-on if space) |
| electronics | `electronics.stackexchange.com_en_all_2026-08.zim` | 4.21 GB | 2 TB |
| unix | `unix.stackexchange.com_en_all_2026-08.zim` | 1.31 GB | 2 TB |
| askubuntu / serverfault | `askubuntu.com_en_all_2026-06.zim` 2.6 GB / `serverfault.com_en_all_2026-02.zim` 1.5 GB | | 2 TB |
| mechanics / bicycles / security / physics | 340 MB / 491 MB / 439 MB / 1.7 GB (2026-08) | | 2 TB |
| stackoverflow | `stackoverflow.com_en_all_2026-07.zim` | 107 GB | 2 TB |

### 1d. DevDocs programming references (`devdocs` folder, all tiny)

v0 set (42.8 MB total): `devdocs_en_python_2026-08.zim` 4.4 MB, `_bash_2026-10` 0.6, `_c_2026-10` 1.4, `_cpp_2026-10` 8.0,
`_git_2026-10` 1.6, `_docker_2026-10` 1.8, `_sqlite_2026-10` 3.5, `_html_2026-10` 1.7, `_css_2026-10` 2.7,
`_javascript_2026-10` 2.6, `_gnu-make_2026-10` 0.6, `_cmake_2026-08` 2.6, `_rust_2026-10` 6.2, `_go_2026-10` 1.7,
`_node_2026-08` 1.4, `_nginx_2026-10` 0.8, `_zsh_2026-10` 0.8, `_jq_2026-10` 0.4. Hundreds more exist (kotlin,
openjdk 14 MB, matplotlib 32 MB, numpy, pandas, postgresql, redis, typescript, vue, react-native…).

## 2. Medical, survival and preparedness documents (PDF → zathura/okular)

| Document | Status / license | URL | Size | Tier |
|---|---|---|---|---|
| **Hesperian — Where There Is No Doctor** (2025 printing), as 32 section PDFs | © Hesperian. Hesperian itself offers the section PDFs free on its languages site and asks "those who can afford to … purchase the full book" ($29.95). Its open-copyright policy allows non-commercial copying but **digital redistribution needs written permission** → keep on the device only, do not mirror. | `https://hesperian.org/wp-content/uploads/pdf/en_wtnd_2025/en_wtnd_2025_<sec>.pdf`, `<sec>` ∈ `fm toc int 01…23 gp info gloss resc indx bm` (Hesperian asks that links point at `https://languages.hesperian.org/pages/en/pdf.html`) | ~0.36–0.52 MB each, ≈ 15 MB total (3 measured, rest estimated) | **v0** |
| **Hesperian — Where There Is No Dentist** (2024), 14 section PDFs | same | `https://hesperian.org/wp-content/uploads/pdf/en_dent_2024/en_dent_2024_<sec>.pdf`, `<sec>` ∈ `fm 01…12 bm` | ≈ 0.25 MB each, ≈ 4 MB | **v0** |
| **ATP 4-02.11 — Casualty Response, Tactical Combat Casualty Care, and First Aid** (23 Mar 2026; supersedes TC 4-02.1) | US Army, public domain | `https://armypubs.army.mil/epubs/DR_pubs/DR_a/ARN46159-ATP_4-02.11-000-WEB-1.pdf` | 12.67 MB | **v0** |
| TC 4-02.1 First Aid (2016, C2 2018) — superseded | public domain; no longer listed on armypubs; third-party mirror | `https://ciehub.info/ref/TC/4-02x1_2018.pdf` (mirror) | 1.63 MB | optional |
| **ATP 3-50.21 — Survival** (18 Sep 2018; the current Army survival manual) | public domain | `https://armypubs.army.mil/epubs/DR_pubs/DR_a/pdf/web/ARN12086_ATP%203-50x21%20FINAL%20WEB%202.pdf` | 23.77 MB | **v0** |
| FEMA **Are You Ready? An In-depth Guide to Citizen Preparedness** | public domain | `https://www.ready.gov/sites/default/files/2021-11/are-you-ready-guide.pdf` | 4.23 MB | **v0** |
| Ready.gov emergency supply checklist | public domain | `https://www.ready.gov/sites/default/files/2021-02/ready_checklist.pdf` | 0.15 MB | **v0** |
| **Oregon OEM — Be 2 Weeks Ready toolkit** (Cascadia-oriented) | Oregon state publication, free | `https://www.oregon.gov/oem/Documents/B2WR-Complete-Tool-Kit-EN.pdf` (units also split: `B2WR-Unit-<1-8>-Module-EN.pdf`) | 40.39 MB | **v0** |
| Oregon OEM Emergency Pocket Planner (2023) | same | `https://www.oregon.gov/oem/Documents/OEM_Pocket-Planner-ENGLISH_2023.pdf` | 0.28 MB | **v0** |
| American Red Cross **Wilderness and Remote First Aid — Emergency Reference Guide** (rev. 2014) | © Red Cross, hosted free on redcross.org; personal use, no redistribution | `https://www.redcross.org/content/dam/redcross/training-services/no-index/wilderness-remote-first-aid-erg.pdf` | 5.22 MB | **v0** |
| CDC **Make Water Safe During an Emergency** fact sheet (28 Aug 2024) | public domain; listed on the CDC page, but **cdc.gov returns 403 to non-browser clients** → download in a browser | `https://www.cdc.gov/water-emergency/media/pdfs/make-water-safe-during-emergency-p.pdf` (page: `https://www.cdc.gov/water-emergency/communication-resources/fact-sheet-making-water-safe-during-an-emergency.html`) | 714 KB | manual |
| WHO Guidelines for drinking-water quality, 4th ed. + 1st/2nd addenda | CC BY-NC-SA 3.0 IGO | `https://iris.who.int/bitstreams/69c17edd-ee26-425b-9d34-33799377e886/download` (handle 10665/352532) — **unverified**: IRIS serves a bot-check page to scripts | ~10 MB | manual |
| USDA **Complete Guide to Home Canning** (2015), guides 1–7 | US Government work, public domain (hosted by NCHFP/UGA) | `https://nchfp.uga.edu/papers/guide/GUIDE0<n>_HomeCan_rev0715.pdf`, n = 1…7 | 3.79 / 1.10 / 0.98 / 2.01 / 1.36 / 3.17 / 1.30 MB | **v0** |
| NOLS Wilderness Medicine, SAS Survival Handbook, Red Cross First Aid/CPR/AED manual, Merck Manual | **not free** — not listed | | | |

## 3. Radio references

| Document | License | URL | Size | Tier |
|---|---|---|---|---|
| **ARRL US Amateur Radio Bands chart**, color 8.5×11 | © ARRL, offered as a free download on `arrl.org/graphical-frequency-allocations` | `https://www.arrl.org/files/file/Regulatory/Band%20Chart/Hambands4_Color_11x8_5.pdf` (11×17: `Hambands4_Color_17x11.pdf` 0.62 MB; B/W: `Hambands4_BW_11x8_5.pdf` 0.38 MB) | 1.09 MB | **v0** |
| **47 CFR Part 97** (Amateur Radio Service), 2025 edition | public domain | `https://www.govinfo.gov/content/pkg/CFR-2025-title47-vol5/pdf/CFR-2025-title47-vol5-part97.pdf` | 0.36 MB | **v0** |
| **47 CFR Part 95** (Personal Radio Services: FRS §95.563, GMRS §95.1763, MURS §95.2763 — the channel tables) | public domain | `https://www.govinfo.gov/content/pkg/CFR-2025-title47-vol5/pdf/CFR-2025-title47-vol5-part95.pdf` | 0.46 MB | **v0** |
| FCC FRS / GMRS / MURS pages | public domain; **fcc.gov returns 403 to scripts** (also to WebFetch) → save from a browser | `https://www.fcc.gov/wireless/bureau-divisions/mobility-division/{family-radio-service-frs,general-mobile-radio-service-gmrs,multi-use-radio-service-murs}` | small | manual |
| NOAA Weather Radio — Oregon station list and county coverage | public domain, HTML (save with "Web page, complete") | `https://www.weather.gov/nwr/stations?State=OR`, `https://www.weather.gov/nwr/counties` | small | manual |

Inline quick tables (from 47 CFR 95 and weather.gov/nwr; keep in Pocket TUI's radio tab too):

| Service | Channels / frequencies (MHz) | Power / license |
|---|---|---|
| FRS/GMRS 1–7 | 462.5625 .5875 .6125 .6375 .6625 .6875 .7125 | FRS 2 W; GMRS 5 W |
| FRS/GMRS 8–14 | 467.5625 .5875 .6125 .6375 .6625 .6875 .7125 | 0.5 W, narrowband |
| FRS/GMRS 15–22 | 462.5500 .5750 .6000 .6250 .6500 .6750 .7000 .7250 | FRS 2 W; GMRS up to 50 W, repeater inputs +5 MHz (467.550–467.725) |
| FRS vs GMRS | FRS license-free (≤2 W, fixed antenna); GMRS needs an FCC license (no exam, $35/10 yr, covers family) | |
| MURS | 151.820 151.880 151.940 154.570 154.600 | 2 W ERP, license-free |
| NOAA WX | 162.400 162.425 162.450 162.475 162.500 162.525 162.550 | receive only |

## 4. Maps (Oregon / Pacific NW, Linux arm64, no phone)

Findings (verified 2026-10-16):

| Question | Answer |
|---|---|
| Organic Maps on Linux arm64? | **Yes**: Flathub `app.organicmaps.desktop` 2026.05.28-2, arches `x86_64, aarch64` (Flathub API). Debian has `organicmaps` in sid only (not trixie). The project's FAQ says the Linux desktop app "is mostly used for development purposes". Map regions are downloaded **in-app** (zoom to the area → download icon, bottom right); no CLI. |
| CoMaps (community fork) on Linux arm64? | **Yes**: Flathub `app.comaps.comaps` 2026.10.05, arches `x86_64, aarch64`, 84 MB download; releases on Codeberg. Same in-app download model. More actively released than Organic Maps' desktop build. |
| GPS in the desktop app? | **unverified** (FAQ only documents manual start/end points). The device's `gpsd` fix can always be shown on the browser map below. |
| Geofabrik Oregon | `https://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf` **254.5 MB** (ODbL). Washington 364.7 MB, Idaho 129.6 MB, California 1.33 GB, `us-west-latest` 3.42 GB. |
| Protomaps free downloads | Daily planet builds, free, ODbL: `https://build.protomaps.com/YYYYMMDD.pmtiles` (e.g. `20261015.pmtiles` = **138.9 GB**, verified). You never download the whole thing: `pmtiles extract` pulls only the bbox via HTTP range requests. CLI: go-pmtiles **v1.31.2**, Linux arm64 build verified (15.8 MB). |
| Tile server | Not needed: a `.pmtiles` file is read directly by the browser via the `pmtiles://` protocol from any static server with Range support. (`tileserver-gl-light` needs Node ≥ 20 — trixie has 20.19 — but PMTiles support is not stated in its README → unverified; skip.) `pmtiles serve /data/maps` also exists (z/x/y tiles on :8080). |
| Terminal viewer | `mapscii` (npm) renders from a local file with `--tile_source /path/file.mbtiles` (option verified in `main.js`; the bundled style targets the 2016 osm2vectortiles schema). Build an OpenMapTiles-schema `.mbtiles` from the Geofabrik PBF with `tilemaker` (3.0.0 in trixie). Rendering with tilemaker output **unverified**; treat as a toy. |

**Recommended v0 path: CoMaps (Flatpak) for the full app, plus the Geofabrik PBF kept on disk.**
It is the only option that gives offline search, routing and a touch UI without writing code. The browser map
(Protomaps) is the v1 path for Pocket TUI integration and the GPS overlay; both share nothing, so they can coexist.

```sh
# v0 — CoMaps (or Organic Maps) via Flatpak, aarch64
sudo apt install -y flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
flatpak install -y flathub app.comaps.comaps            # alt: app.organicmaps.desktop
flatpak run app.comaps.comaps
#   in the app: zoom to Oregon, click the download icon (bottom right); repeat for Washington/Idaho.
#   Needs internet once; data lives in the Flatpak's ~/.var/app/app.comaps.comaps/ (size ≈ 0.5–1 GB, estimate).

# keep the raw OSM data too (routing experiments, tilemaker, osmium 1.18 in trixie)
curl -L -o /data/maps/oregon-latest.osm.pbf https://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf

# v1 — browser map from a Protomaps extract (no tile server)
curl -L -o /tmp/pmtiles.tgz https://github.com/protomaps/go-pmtiles/releases/download/v1.31.2/go-pmtiles_1.31.2_Linux_arm64.tar.gz
sudo tar -C /usr/local/bin -xzf /tmp/pmtiles.tgz pmtiles
pmtiles extract https://build.protomaps.com/20261015.pmtiles /data/maps/oregon.pmtiles \
    --bbox=-124.8,41.9,-116.4,46.4          # Oregon + margin; est. 0.5–1.5 GB (measure)
#   Pacific NW (OR+WA+ID): --bbox=-124.9,41.9,-111.0,49.1 ; add --maxzoom=12 for a small "overview" file
mkdir -p /data/maps/web && cd /data/maps/web
curl -L -o maplibre-gl.js  https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.js     # 6.x ships ESM only; 5.24.0 UMD verified
curl -L -o maplibre-gl.css https://unpkg.com/maplibre-gl@5.24.0/dist/maplibre-gl.css
curl -L -o pmtiles.js      https://unpkg.com/pmtiles@4.5.0/dist/pmtiles.js
curl -L -o basemaps.js     https://unpkg.com/@protomaps/basemaps@5.7.2/dist/basemaps.js
curl -L -o assets.zip      https://github.com/protomaps/basemaps-assets/archive/refs/heads/main.zip && unzip -q assets.zip   # fonts + sprites, offline
cd /data/maps && python3 -m http.server 8081       # or an nginx location with Range support
```

`/data/maps/web/index.html` (from the Protomaps MapLibre docs; not yet tested on the Pi):

```html
<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="maplibre-gl.css">
<style>html,body,#map{margin:0;height:100%}</style><div id="map"></div>
<script src="maplibre-gl.js"></script><script src="pmtiles.js"></script><script src="basemaps.js"></script>
<script>
  const protocol = new pmtiles.Protocol(); maplibregl.addProtocol("pmtiles", protocol.tile);
  const map = new maplibregl.Map({ container: "map", center: [-122.68, 45.52], zoom: 10, style: {
    version: 8,
    glyphs: "http://localhost:8081/web/basemaps-assets-main/fonts/{fontstack}/{range}.pbf",
    sprite: "http://localhost:8081/web/basemaps-assets-main/sprites/v4/light",
    sources: { protomaps: { type: "vector", url: "pmtiles://http://localhost:8081/oregon.pmtiles",
               attribution: "© OpenStreetMap" } },
    layers: basemaps.layers("protomaps", basemaps.namedFlavor("light"), { lang: "en" }) } });
  // GPS overlay: poll gpsd (e.g. a tiny /gps JSON endpoint from the pocket MCP/CLI) and move a marker.
</script>
```

## 5. Ebooks (EPUB → foliate)

**Standard Ebooks** (public-domain texts, SE's own work CC0): the direct link must carry `?source=download`
(without it the server returns a "Your download has started" HTML page). Pattern:
`https://standardebooks.org/ebooks/<author>/<title>[/<translator>]/downloads/<author>_<title>[_<translator>].epub?source=download`.
Never crawl SE (its nav contains an IP-ban honeypot); fetch only listed URLs. Jules Verne *Twenty Thousand Leagues* returns 451 (legal removal).

| Title (path after `/ebooks/`) | Size |
|---|---|
| `jane-austen/pride-and-prejudice` | 0.83 MB |
| `mary-shelley/frankenstein` | 0.69 |
| `bram-stoker/dracula` | 0.63 |
| `herman-melville/moby-dick` | 1.17 |
| `charles-dickens/a-tale-of-two-cities` · `charles-dickens/great-expectations` | 0.82 · 1.00 |
| `mark-twain/the-adventures-of-huckleberry-finn` · `mark-twain/the-adventures-of-tom-sawyer` | 0.81 · 0.70 |
| `arthur-conan-doyle/the-adventures-of-sherlock-holmes` | 0.74 |
| `h-g-wells/the-war-of-the-worlds` · `h-g-wells/the-time-machine` | 0.80 · 0.54 |
| `oscar-wilde/the-picture-of-dorian-gray` | 0.63 |
| `jack-london/the-call-of-the-wild` · `robert-louis-stevenson/treasure-island` | 0.48 · 0.72 |
| `lewis-carroll/alices-adventures-in-wonderland/john-tenniel` (illustrated) | 18.40 |
| `charlotte-bronte/jane-eyre` · `emily-bronte/wuthering-heights` | 0.93 · 0.82 |
| `alexandre-dumas/the-count-of-monte-cristo/chapman-and-hall` | 1.66 |
| `sun-tzu/the-art-of-war/lionel-giles` · `marcus-aurelius/meditations/george-long` | 0.59 · 0.73 |
| `henry-david-thoreau/walden` · `homer/the-odyssey/william-cullen-bryant` | 1.00 · 0.98 |
| `f-scott-fitzgerald/the-great-gatsby` · `louisa-may-alcott/little-women` | 0.44 · 1.00 |
| `edgar-allan-poe/short-fiction` · `jerome-k-jerome/three-men-in-a-boat` | 1.28 · 0.69 |
| `daniel-defoe/the-life-and-adventures-of-robinson-crusoe` · `kenneth-grahame/the-wind-in-the-willows` | 0.67 · 0.85 |

**Project Gutenberg** (public domain; `https://www.gutenberg.org/ebooks/<id>.epub3.images` or `.epub.noimages`; the
robot-access policy asks scripts to go slowly — use `wget -w 2` — or use a mirror):

| id | Title | EPUB3 size |
|---|---|---|
| 1342 | Pride and Prejudice | 24.8 MB (`.epub.noimages` 0.56 MB) |
| 84 / 2701 / 345 | Frankenstein / Moby-Dick / Dracula | 0.47 / 0.81 / 0.60 MB |
| 11 / 16 | Alice in Wonderland / Peter Pan | 0.19 / 0.39 MB |
| 1661 / 244 | Adventures of Sherlock Holmes / A Study in Scarlet | 0.38 / 0.39 MB |
| 98 / 1400 | A Tale of Two Cities / Great Expectations | 7.9 / 14.4 MB |
| 76 / 120 | Huckleberry Finn / Treasure Island | 16.0 / 49.5 MB (heavily illustrated; prefer SE) |
| 2600 / 2554 / 28054 | War and Peace / Crime and Punishment / Brothers Karamazov | 1.83 / 0.78 / 1.16 MB |
| 1232 / 1080 / 1952 | The Prince / A Modest Proposal / The Yellow Wallpaper | 0.37 / 0.26 / 0.23 MB |
| 35 / 36 / 43 / 174 / 5200 / 64317 | Time Machine / War of the Worlds / Jekyll & Hyde / Dorian Gray / Metamorphosis / Great Gatsby | 0.31 / 0.29 / 0.30 / 0.46 / 0.32 / 0.35 MB |

## 6. Software references

| Reference | How | Size | License |
|---|---|---|---|
| man pages | already local; add `manpages-posix 2017a-2` (non-free section) for POSIX | — | — |
| `tldr` pages | `apt install tealdeer` then `tldr --update` (cache in `~/.cache/tealdeer`); or the archive `https://github.com/tldr-pages/tldr/releases/latest/download/tldr-pages.en.zip` (3.37 MB; all languages `tldr.zip` 21.1 MB) | 3.4 MB | CC BY 4.0 |
| Python 3.13 docs (trixie's Python) | `apt install python3-doc` (3.13.5, HTML in `/usr/share/doc/python3/html`) **or** `https://docs.python.org/3.13/archives/python-3.13-docs-html.tar.bz2` (8.07 MB; note `/3/archives/...` is 404 — use the versioned path) | 8.1 MB | PSF |
| Debian Reference | `apt install debian-reference-en` (2.127) or `https://www.debian.org/doc/manuals/debian-reference/debian-reference.en.pdf` | 1.37 MB | GPL-2+ |
| Debian Administrator's Handbook | `apt install debian-handbook` (11.20220922, HTML) or EPUB `http://debian-handbook.info/download/stable/debian-handbook.epub` (5.92 MB; the `.pdf` URL is 404) | 5.9 MB | GPL-2+ / CC BY-SA 3.0 |
| Raspberry Pi documentation (AsciiDoc source of raspberrypi.com/documentation) | `git clone --depth 1 https://github.com/raspberrypi/documentation` (default branch `master`; repo ≈ 1.1 GB with history, so shallow-clone) or `https://github.com/raspberrypi/documentation/archive/refs/heads/master.tar.gz` (size not reported by GitHub). Read `.adoc` with `bat`/`glow`, or build with `make` (asciidoctor). `www.raspberrypi.com/documentation` itself 403s scripted mirroring. | ~0.3 GB (est.) | CC BY-SA 4.0 |
| ArchWiki | ZIM `archlinux_en_all_maxi_2026-07.zim` (36 MB) — Debian has **no** `arch-wiki-docs` package | 36 MB | GFDL 1.3 |
| DevDocs | §1d ZIMs | 43 MB | mixed |
| Kernel docs | `https://www.kernel.org/doc/html/latest/` (mirror with wget if wanted; or `apt install linux-doc`) | — | GPL-2 |

## 7. Could not verify / deliberately excluded

- **WHO** IRIS PDFs (bot-check page), **CDC** and **FCC** sites (403 to scripts), **FAS** mirrors (`irp.fas.org` answers 202 + challenge), `archive.org` (503 during research), Organic Maps CDN listing (`cdn.organicmaps.app/maps/` 403) — all marked above.
- **armypubs.army.mil** serves an HTML stub to `HEAD`; `GET` with a browser User-Agent works (verified 206/`%PDF` with the sizes above). The manifest notes this.
- Hesperian section sizes: 3 of 46 measured; the totals are estimates.
- Deliberately left out: military combat and weapons handbooks (this repository keeps to first-aid, survival and preparedness material).
- Not free, therefore not listed: SAS Survival Handbook, NOLS Wilderness Medicine, Red Cross First Aid/CPR/AED manual, the full "Where There Is No Doctor" PDF ($29.95), Merck Manual.

# v0 download list

Target ≤ 25 GB. **Manifest total: 21.14 GB** (Kiwix 18.34 GB, models 2.36 GB, docs 0.14 GB, books 0.05 GB, maps 0.25 GB)
plus ≈ 1 GB of CoMaps in-app regions → **≈ 22.1 GB**. First add-on if space allows: `diy.stackexchange` (+2.06 GB).
Machine-readable copy with sha256: `provision/config/knowledge/trove-manifest.txt`.

| URL | Dest under `/data/` | Size |
|---|---|---|
| `https://download.kiwix.org/zim/wikipedia/wikipedia_en_top_maxi_2026-09.zim` | `kiwix/` | 6,991 MB |
| `https://download.kiwix.org/zim/wikipedia/wikipedia_en-simple_all_nopic_2026-09.zim` | `kiwix/` | 1,095 MB |
| `https://download.kiwix.org/zim/wikipedia/wikipedia_en_medicine_maxi_2026-10.zim` | `kiwix/` | 1,864 MB |
| `https://download.kiwix.org/zim/ifixit/ifixit_en_all_2025-12.zim` | `kiwix/` | 3,571 MB |
| `https://download.kiwix.org/zim/wikivoyage/wikivoyage_en_all_maxi_2026-09.zim` | `kiwix/` | 1,071 MB |
| `https://download.kiwix.org/zim/other/appropedia_en_all_maxi_2026-02.zim` | `kiwix/` | 582 MB |
| `https://download.kiwix.org/zim/other/zimgit-post-disaster_en_2024-05.zim` | `kiwix/` | 645 MB |
| `https://download.kiwix.org/zim/other/zimgit-medicine_en_2024-08.zim` | `kiwix/` | 70 MB |
| `https://download.kiwix.org/zim/other/zimgit-water_en_2024-08.zim` | `kiwix/` | 21 MB |
| `https://download.kiwix.org/zim/other/zimgit-knots_en_2024-08.zim` | `kiwix/` | 28 MB |
| `https://download.kiwix.org/zim/other/zimgit-food-preparation_en_2025-04.zim` | `kiwix/` | 98 MB |
| `https://download.kiwix.org/zim/other/archlinux_en_all_maxi_2026-07.zim` | `kiwix/` | 36 MB |
| `https://download.kiwix.org/zim/wiktionary/wiktionary_en_simple_all_nopic_2026-04.zim` | `kiwix/` | 26 MB |
| `https://download.kiwix.org/zim/stack_exchange/{raspberrypi 2026-08, outdoors 2026-08, medicalsciences 2026-02, ham 2026-08, arduino 2026-07, 3dprinting 2026-02, cooking 2026-07, gardening 2026-08, lifehacks 2026-08, sustainability 2026-08}.stackexchange.com_en_all_<date>.zim` | `kiwix/` | 2,196 MB |
| `https://download.kiwix.org/zim/devdocs/devdocs_en_{python 2026-08, bash, c, cpp, git, docker, sqlite, html, css, javascript, gnu-make, cmake 2026-08, rust, go, node 2026-08, nginx, zsh, jq}_<date>.zim` (date 2026-10 unless noted) | `kiwix/` | 43 MB |
| `https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf` | `models/llm/` | 1,117 MB |
| `https://huggingface.co/bartowski/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf` | `models/llm/` | 808 MB |
| `https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.Q8_0.gguf` | `models/embed/` | 146 MB |
| `https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin` + `ggml-tiny.en.bin` | `models/whisper/` | 148 + 78 MB |
| `https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx` + `.onnx.json` | `models/piper/` | 63 MB |
| ATP 4-02.11, ATP 3-50.21 (armypubs, §2) | `docs/medical/`, `docs/survival/` | 12.7 + 23.8 MB |
| Hesperian WTND (32 files) + WTN Dentist (14 files) (§2) | `docs/medical/hesperian/` | ≈ 19 MB |
| Red Cross WRFA ERG, FEMA Are You Ready + checklist, Oregon B2WR toolkit + pocket planner, USDA canning guides 1–7 | `docs/medical/`, `docs/prep/`, `docs/food/` | 5.2 + 4.4 + 40.7 + 13.7 MB |
| ARRL band chart (2 files), 47 CFR Part 97, 47 CFR Part 95 | `docs/radio/` | 1.7 + 0.4 + 0.5 MB |
| Debian Reference PDF, Debian Handbook EPUB, Python 3.13 HTML docs, tldr-pages.en.zip | `docs/linux/` | 1.4 + 5.9 + 8.1 + 3.4 MB |
| 28 Standard Ebooks EPUBs (§5, `?source=download`) + 8 Gutenberg EPUBs | `books/` | 46 MB |
| `https://download.geofabrik.de/north-america/us/oregon-latest.osm.pbf` | `maps/` | 255 MB |
| CoMaps in-app: Oregon (+ Washington) | Flatpak data dir | ≈ 1,000 MB (estimate) |
