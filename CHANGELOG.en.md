# Changelog

French version (reference): [CHANGELOG.md](CHANGELOG.md).

## 0.1.4 — 9 October 2026

Second performance audit, under real use and at full scale (`docs/AUDIT2_2026-10.md`): every function that can take
time was timed on the whole bank (7,625 XISF), on a simulated network share (2 ms per access) and, for the interface,
at ten times the bank (80,000 rows). 33 findings, all fixed; no computed result changed.

- **Large lists stay smooth**: sorting uses one key per row in the model (not pairwise Python comparisons: 4 s →
  0.1–0.2 s for 80,000 images, 0.3–0.5 s → 0.05 s on the bank); **lazy** image table (cells computed for the rows shown
  only): “select all” 2.5 s → 0.06–0.37 s at 80,000 images, 0.48 → 0.04 s on the bank; table headers no longer walk
  every row at each drawing after “select all” (0.77 s → 0.02 s, identical rendering); changing the theme only
  recomputes colours (1 s → 0.02 s; 7.4 s at 80,000 rows); catalogue filter in one pass; selection debounced.
- **Nothing slow on the GUI thread**: stack index, estimate (free space included), ownership and per-object counts,
  sky-map points computed in the background; sky map: hovering 14 ms → 0.1 ms; world map: tile decoding capped at
  30 ms per drawing, LRU cache; spectrum plot: hovering 30 ms → 1 ms; CSV export in the background; medoids and field
  grouping in numpy (0.63 and 0.67 s → 0.07 and 0.09 s, identical results).
- **Network share (NAS)**: state database committed at most once per second (instead of 3 times per image: 7.7 s →
  0.07 s for 100 writes), JOURNAL.txt written in batches, duplicates recorded in one pass (12.5 s → 0.06 s); final
  sorting with nothing to move **60.7 s → 1.5 s** (LOT.txt and INDEX_LOTS.csv rewritten only when they changed, no
  more `stat` per file nor full walk); 48 images to a destination on the share: 20.3 → 4.9 s.
- **Reorganise**: no more walk through the inventory for each file (61 million comparisons), headers read by several
  processes, **progress shown and Stop** (interface and command line); whole bank: 243 → 57 s (bound by disk reads).
- **Quality**: a single (parallel) walk of the folder, sizes and dates read in parallel, cache read in one query, the
  dialog's plan reused by the engine: starting again on the already measured bank over a share **72 s → 2 s**;
  QUALITE.csv rewritten at most every 5 s and at the end of a stack (not after each image: O(n²) bytes per stack);
  cache committed in batches. **Fix**: the table sorted FWHM, background, SNR… as text.
- **Fixes**: the new-images check opened the destination database for writing; reading pixel duplicates for the
  anomaly report could raise an exception.
- Tests: +21 (`tests/test_echelle.py`, tolerant time budgets and exact counters: writes, commits, reads per image);
  measurement tools in `outils/audit2/`.

## 0.1.3 — 9 October 2026

- Build: the v0.1.2 release run failed on an apostrophe that slipped into a comment of the `.deb` test
  (`release.yml`); no change to the application. The 0.1.3 assets are those expected for 0.1.2.

## 0.1.2 — 9 October 2026

- **`.deb` package: `ca-certificates` dependency added.** The bundled interpreter (static OpenSSL) reads the certificate
  authorities from `/etc/ssl/certs`: on a minimal system without that package every HTTPS connection failed silently
  (update check, SIMBAD, JPL) — found by trying `coupole maj` in a bare Ubuntu container. The package test in
  `release.yml` now checks an HTTPS connection from the bundled interpreter.

## 0.1.1 — 9 October 2026

- **Debian/Ubuntu package** (`coupole_0.1.1_amd64.deb`, `_arm64.deb`, and stable names `coupole-linux-amd64.deb` /
  `-arm64.deb`) built by `build_deb.py` from the standalone Linux package: files under `/opt/coupole`,
  `/usr/bin/coupole` command (interface without argument, command line with), menu entry, icons, man page, GPL-3
  `copyright`, Qt system dependencies resolved by apt (checked with `ldd` and by installing in bare Ubuntu 22.04 and
  24.04 containers). A `.deb` installation does not update through the archive: Coupole announces the new version
  and points to the Release's `.deb` (*Download the package* button, `coupole update`). `release.yml` builds the
  `.deb`, tries it in a bare container, attaches it to the Release, then **keeps a single Release online** (previous
  ones and their tags are deleted once the new one is complete, as well as the build artifacts); automatic updates
  rely on `releases/latest` and stable names.
- **Lighter Linux/macOS packages**: python-build-standalone « stripped » interpreter (−320 MB unpacked: libpython
  219 MB and a 102 MB binary of debug symbols), Tcl/Tk, headers and orphan Qt plugins removed;
  `Coupole-0.1.1-linux.tar.gz`: 229 → 137 MB; `.deb`: 106 MB.
- **Dark theme by default**; *View > Appearance* menu (checkable *Light* / *Dark* entries, Ctrl+Shift+D toggles)
  applied at once and saved, in sync with the Preferences; a user who had chosen the light theme keeps it. Manual
  screenshots regenerated in dark.
- **OHP bank — what you already own**: from `_traitement/etat.sqlite` (read again in the background when opening,
  after each run and whenever the folder changes), marker and soft colour per image (owned, duplicate left out,
  failed, to download; contrast ≥ 4.5 in both themes; tooltip with status, date and local file), *owned* column
  « 120 / 300 » with mini bar and marker (complete / partial / none) per object, sortable; *To download only* box;
  estimate counting only the missing images; legend; Stacks tab: *complete / incomplete* column;
  `coupole ohp inventory --missing [--json]` and `possedee`, `statut_local`, `fichier_local` columns in the CSV of
  `ohp list`.
- **Cosmology**: redshift slider under the z field (logarithmic scale from 0.001 to 1100, marks per decade) moving
  the curve marker and updating the table live by interpolation on the curve grid (every quantity is now computed
  on it), exact computation on release, field and slider in sync, arrows = fine step. **Fix**: the curves did not
  follow the window when resized while sitting under the table (the panel, taller than the scroll area, kept its
  hinted height): half of the visible height now goes to them.
- **Sharp OpenStreetMap map on dense screens** (Windows at 125–150 %, Mac Retina): tiles of the next zoom level drawn
  at half size (« @2x » equivalent), smoothing on; the map was previously upscaled by the system and looked
  pixelated.
- **Image quality — speed and resume**: 3.7 × faster measurement (1.21 → 0.33 s per T120 image: vectorised Moffat
  model, analytic derivatives, 120 stars per image); measurements in parallel processes (machine plan, economy
  mode, limit; at most 3 on a network folder, detected and announced), free interface, immediate stop; each image
  written at once to `QUALITE.csv` (atomic); `_traitement/qualite.sqlite` cache by (path, size, date): starting
  again redoes nothing, closing then reopening resumes; above 200 images, a sample of 5 per stack is offered (or
  everything, with the duration estimated on 3 images); progress with time left and rate;
  `coupole quality --sample N | --all | --processes N`. **Fix**: on some real stars the fit overflowed
  (`OverflowError`) and stopped the measurement of the image.
- **My computer**: the « GPU computing » line no longer mentions CuPy (nothing to install: no function uses the
  card for now); the detail for developers is in the tooltip and CONTRIBUTING.
- Tests: +37 (ownership, Quality engine on 300 simulated XISF, slider, resizing, dense tiles, Appearance menu,
  `.deb` case of the updater).

## 0.1.0 — 8 October 2026

First release.

- **Audit follow-up** (§ 10 of the report, proposals applied): the Sun altitude used by the « local time written by
  mistake » check is computed in a single astropy call and cached per (site, UTC minute) in each conversion process
  (13.2 → 2.5 ms of CPU per exposure on a series of 20 s exposures, 33 → 13 ms on an isolated image; overall rate
  unchanged, network-bound); on Windows, each conversion process puts itself in a « kill on close » *job object*: on
  cancellation the ASTAP it launched dies immediately with it instead of finishing alone (up to 4 min) — silent
  fallback if the API refuses, Linux and macOS unchanged (signal); when free space at the destination is tight, the
  queue of waiting FITS (2 × conversions + downloads) is **reduced automatically** (never below conversions + 1), with a
  message and a log line, instead of refusing the job. Deliberately not applied: persistent HTTP connections (gain
  < 1 %) and memory budget 500 → 400 MB per conversion (caution: ASTAP adds its own process).
- **Full audit** (`docs/AUDIT_2026-10.md`, French): performance (window shown in 0.42 s instead of 1.51 s: astropy,
  scipy and SEP no longer load before display; peak memory of an IRIS 4096² conversion down from 573 to 365 MB; one
  HTTP request per image instead of two; progress aggregated at 10 Hz), parallelism (manual limit bounded by
  memory; cancellation that terminates conversion processes and ASTAP; a crashed process is survived; closing stops
  and waits for every thread), robustness (corrupt settings set aside; atomic writes everywhere; full disk,
  unwritable folder, damaged FITS and XISF, unknown time zone, cut network tested; Qt signals protected against
  destroyed widgets; freeze watchdog and native crash tested), security (HTTPS required for the remote sources file
  and the collection point; update archive checked: zip slip, symbolic links, bomb; reports bounded to 64 kB,
  computer name masked; safe folder names; no file overwritten when sorting; pip-audit clean), cross-platform
  (Windows cp1252 console; Windows locales; macOS menu roles; long paths), bilingualism (language leak test).
  **Fix**: with « Keep duplicates », an image with identical pixels was deleted instead of kept (and vice versa).
- **OHP bank — Download everything**: the whole bank (≈ 8,000 images, 78 GB → ≈ 30 GB as XISF) with volume,
  estimated duration at the rate cap and free space shown before confirmation; folder asked on first use
  (`Documents/Coupole/OHP_DU_ECU` proposed); resume after a cut or a close; **pause / resume**; end report;
  `coupole ohp all`.
- **Readable log** `_traitement/JOURNAL.txt` (UTC timestamps, bilingual, rotation), « Open the log » button.
- **Reorganise**: sorts files already converted by Coupole (elsewhere, older layout) into the stack tree — moved,
  never copied nor overwritten, logged; `coupole ohp reorganise`.
- **New images in the bank**: check at startup (at most once a day, adjustable, can be disabled) of the TAP inventory
  against the local copy; banner « N new images (M objects, X GB) since … — Download now? / Later / Show »; never a
  download without consent; `coupole ohp new [--download]`.
- **Cosmology**: model list never cut; curves below the table when space is short (SH0ES column always visible
  without scrolling).
- **Cosmology** (new module): from redshift to line-of-sight and transverse comoving, luminosity, angular diameter
  and light-travel distances, lookback time, age at z and present age, E(z) and H(z), distance modulus, scale in kpc
  per arcsecond, comoving volume, three recession velocities; Planck 2018 by default (1σ uncertainty with the
  H₀–Ωm correlation, SH0ES comparison), Planck 2015, WMAP 9, « textbook » ΛCDM, custom set (H₀, Ωm, Ωk);
  out-of-range values refused with an explanation; an object's redshift requested from SIMBAD; distance curves;
  CSV export; `coupole cosmo` command line. Computation core taken from the same author's « cosmologie-redshift »
  calculator, **checked before integration** against astropy and an independent SageMath integration (z from 10⁻⁸
  to 1100, flat and curved universes): no bug, deviation ≤ 3·10⁻⁶ on distances, ≤ 2·10⁻⁵ on ages. Comoving volume:
  series expansion at very small z in curved universes, where astropy's formula loses all its digits (wrong, even
  negative, volume).
- **Online record** (OHP bank, reusable by other modules): SIMBAD (type, coordinates, magnitudes, parallax,
  measured distance, radial velocity and redshift, angular size, spectral and morphological types, identifiers,
  SIMBAD, Aladin Lite and NED links), Sesame fallback, JPL Small-Body Database for small bodies (orbit class,
  elements, diameter, albedo, rotation); optional and never blocking (background thread, 8 s timeout, one request per
  object, 30-day dated cache, offline fallback to the last known record); chosen identifier always shown; « send
  this redshift to the Cosmology module ». Addresses in `sources.json`.
- **Every screen**: interface adapted from 1024×600 (or 1366×768 at 150 %) to 4K, with no truncation or overflow:
  sizes capped to the screen, scrolling content, wrapping text, flexible rows of filters and settings, module bar
  reduced to icons below 1,100 px, exact fractional scaling; checked by tests at 6 screen sizes and at 150/200 %.
- **Fix**: closing the world map while a tile was downloading could crash Python.
- **Appearance**: Coupole's own style, colours and font, independent of the computer's settings (system dark mode,
  GTK/KDE themes, font size); light or dark theme chosen in Preferences; soft colours (off-white, charcoal, slate
  blue) and rounded corners; text/background WCAG contrast ≥ 4.5 checked by a test.

- **Core**: PyQt6 interface and complete command line, French and English everywhere (system language detection,
  forced choice), tooltips on every widget; automatically discovered modules (shipped, installed, or dropped into the
  settings folder); hardware detection (system, processor, cores, memory, disk, graphics card) and adapted
  parallelism; configurable service addresses (sources file, forced values, published file with shape check and
  domain allow-list); anonymous incident reports with consent; automatic package updates from GitHub Releases; PDF
  manual and per-screen help.
- **OHP image bank**: TAP inventory (cache, shipped snapshot, new items flagged); catalogue of 166 objects (JSON
  classification table, rules, optional online resolution, grouping by position, recorded corrections); polite,
  resumable downloads; pixel-fingerprint duplicates; astrometric solution check (consistency, optional ASTAP); headers
  fixed with HISTORY, conditional and idempotent position fix; XISF, lossless compressed FITS and float32 FITS output;
  stackable sets, bilingual `LOT.txt`, `INDEX_LOTS.csv`, `journal.csv`; anomaly report; sky map. Matches the 7-8
  October 2026 reference processing (identical pixels and headers on the real test).
- **Image quality** (optional, SEP): FWHM and ellipticity (Moffat fit, 3 × 3 map), background, noise, gradient,
  residual, saturation, trails, sampling; validated on synthetic images.
- **Spectra and series**: FITS (WCS axis, radio cubes, tables) and CSV reading, radio velocity.
- **Sites and times**: OHP, Meudon, Paris (MPC constants), added sites, OpenStreetMap map, UTC and local time.
- **My computer**: diagnosis (example module).
- **Distribution**: Windows (embedded Python + Inno Setup), macOS (.app, .dmg) and Linux (archive + installer)
  packages, `install.sh` / `install.ps1` / `install.bat` scripts, `pipx`/`pip`.
