# Changelog

French version (reference): [CHANGELOG.md](CHANGELOG.md).

## 0.1.10 — 9 October 2026

**Processing works towards a folder on a network share.** Kevin's output folder is on the NAS (SMB share mounted
by cifs on Manjaro): downloading new images, *Download everything* or reorganising into that folder failed.

- **Cause (reproduced on a real Samba server, default cifs mount)**: SQLite cannot write through SMB byte-range
  locks — « database is locked » after 60 s, 0-byte state database. Read-only access (ownership, new images,
  anomalies) and file copies worked.
- **Local working database**: on a share (cifs, nfs, sshfs, gvfs, kio-fuse; smbfs on macOS; UNC or network drive on
  Windows), or when SQLite cannot write within 3 s, the state database is kept in the user's cache folder (one per
  output folder) and **copied back to the share every 30 s**, at the end of the session, on stop and on cancel:
  consistent snapshot, `PRAGMA integrity_check`, copy into a temporary file on the share read back and compared
  (SHA-256), then replaced in one go. No lock is ever taken on the share: no orphan lock is possible, and the NAS or
  another computer always see a complete database. Log and status bar: « Folder on a network share: local working
  database, copied back to the share every 30 s ».
- **At startup**: a newer database on the share (processed elsewhere) is taken over; writes not copied back after a
  crash are copied. **Two writers** (two computers, or the NAS): nothing is overwritten, Coupole warns and offers a
  **merge** (most advanced status wins: converted > duplicate > failed), both original databases are kept; command
  line `coupole ohp merge --dest FOLDER`.
- Ownership, new images and anomalies read the working database when it is up to date (no page-by-page reading over
  the network). `coupole ohp metadata --rewrite` also updates the state database on a share.
- Manuals: section « Output folder on a network share » (Linux, macOS, Windows), troubleshooting; OHP Bank help.
  Audit: `docs/AUDIT2_2026-10.md` § 10; reproducible Samba bench `outils/audit2/samba/`.

## 0.1.9 — 9 October 2026

**The Quality module starts at once on a network share, astronomy programs really open our files, and PixInsight
finds focal length and pixel.** Feedback from Kevin (Manjaro, 0.1.8, folder on an SMB share).

- **Endless « Listing the folder… » on an SMB share: cause found and measured.** On a real Samba share mounted by the
  kernel cifs client, SQLite cannot write through SMB byte-range locks (« database is locked »): the measurement cache
  was opened three times on the share before the first measurement, 30 s of waiting each — 90.4 s of listing for 831
  XISF, and no cache in the end (0-byte file, found on the NAS). The cache is never written on a share any more (the
  user's cache folder; an old cache on the share is read; local fallback within 3 s if a local database is locked).
- **Listing as a stream**: measuring starts with the first stack found, while the listing goes on (« 1,234 files
  found in 56 stacks… », *Stop* immediate). No file opened while listing, size and date taken from the folder
  listing (at most one `stat` per image); in a Coupole output only the stack folders are read (`INDEX_LOTS.csv`,
  otherwise the state database copied in one block); 32 reading threads on a share. Large folder: the sample is
  measured first and the question (sample or everything) is asked without stopping, with a duration taken from the
  images already measured. Measured on the real share: 92.7 s before the first measurement (10 ms latency) → full
  listing in 0.24–0.57 s, first result in 0.2–0.6 s; at 20 ms: 0.57–1.05 s.
- **Column titles never truncated** (« étoiles mesurées » showed as « toiles mesurée »): every section keeps at least
  its title's width, full title as tooltip, in every table (tested at 100, 150 and 200 %). OHP bank tab tooltips on
  each tab (it stayed displayed over the « Astrometric solution » group).
- **Cosmology**: side by side, the table takes the width of its columns (the « value » column is no longer cut) and
  the curves the rest; stacked, all rows when there is room, curves of at least 300 px. *View > Cosmology layout*:
  automatic (1,550 / 1,450 px hysteresis), side by side or stacked, kept with each layout's splitter position.
  Unambiguous **units**: km s⁻¹ Mpc⁻¹, km s⁻¹, mag arcsec⁻² (CSV and cp1252 console: `km s^-1 Mpc^-1`).
- **Compatibility checked, not assumed**: Siril 1.2.x does not read XISF; 1.4.0 and 1.4.4 (official AppImages, real
  test) read all our codecs bit for bit but keep ADU floats outside their [0, 1] range; N.I.N.A. 3.2 does not
  decompress zstd and maps any float to [0, 1] without reading `bounds` (white image); ASTAP only reads uncompressed
  XISF; PixInsight (PCL code) unchanged. « Who reads what » table in the manuals and under the format list.
- **New « XISF compatible with N.I.N.A. and Siril » format** (`--format xisf16`): UInt16 with a 1,000 ADU pedestal
  (`PEDESTAL`), zlib+sh compression like N.I.N.A. Loss measured on 66 bank exposures: rounding ≤ 0.5 ADU, background
  mean changed by at most 0.014 ADU, 0.012 % of pixels clipped high; without the pedestal, a 10-s exposure with an
  over-subtracted background lost 99.75 % of its pixels. The PixInsight default does not change.
- **Opening an image**: double-click an owned image (OHP bank, Quality) → system application; right-click → *Open
  with* (only installed programs that really read this file, the others greyed with the reason) and *Open file
  location* (file selected: Explorer, Finder, Dolphin/Nautilus through D-Bus). Objects: *Open the target folder*,
  *Show this object's stacks*.
- **Owned ≠ stackable together**: « stacks » column and breakdown by field, instrument and filter in the tooltip
  (« 840 images sorted into 9 stacks: field 1 T120: B 200 · V 300 · R 300; … »).
- **Focal length and pixel for PixInsight and N.I.N.A.**: `FOCALLEN` matched to the measured scale (7,234.1 mm instead
  of 7,200 for the T120, old value in HISTORY) and `Instrument:Sensor:XPixelSize`, `Instrument:Camera:XBinning`…
  properties (what ImageSolver reads, checked in PixInsight's code); Stacks tab: « For PixInsight / N.I.N.A. » box
  (focal length, effective pixel, binning, scale, field, centre, Copy buttons), hideable focal/pixel/scale columns,
  same values in `LOT.txt`; `coupole ohp metadata FOLDER --rewrite` completes already converted files without
  touching the pixels.
- **ASTAP guide**: the official page's « zipped D80 » link is dead (D80 only exists as .exe, .pkg and .deb); outside
  Debian, safe extraction from the `.deb` (checked on the real package); Arch/Manjaro: nothing on the PATH, GTK2
  graphical `astap` not in the official repositories, `astap_cli` is enough (and Coupole now prefers it everywhere);
  a continuous-integration test checks every link for every system.
- Three small test files for testers in `tests/donnees/` (default XISF, compatible XISF, FITS).

## 0.1.8 — 9 October 2026

**The real system file manager, and seeing at a glance what you already own.** Feedback from Manjaro (KDE Plasma,
standalone package 0.1.7, output folder on a NAS).

- **Native file dialogs on Linux**: the standalone package bundles its own Qt, which cannot load the desktop plugin
  installed on the system; the « Output folder » dialog fell back to Qt's, in English and without the system places
  (the NAS mounted in Dolphin could not be reached). At startup, before the application is created and unless the
  user set something (`QT_QPA_PLATFORMTHEME`), Coupole checks in under a second whether the **XDG portal** is
  available with a backend able to choose files, and uses it: Dolphin on KDE, Files on GNOME. Otherwise, on a GTK
  desktop, the GTK dialog; otherwise Qt's dialog, translated, its sidebar listing home folders, `/media`, `/mnt`,
  `/run/media/$USER`, the shares opened in the file manager (gvfs) and cifs, nfs, sshfs mounts. Real test in a
  container (Xvfb, session bus, `xdg-desktop-portal`): the dialog opens in `xdg-desktop-portal-kde` on KDE and
  `xdg-desktop-portal-gtk` on GNOME, attached to Coupole's window. Windows and macOS keep their native dialog
  (Explorer, Finder): no setting disables it. Every file choice goes through a single module (`gui/fichiers.py`),
  with the parent window.
- **Preferences > File dialogs**: *System* (default) or *Qt*, in case the portal is broken on someone's machine;
  bilingual, with tooltip.
- **Texts provided by Qt in French** (standard buttons, context menus of fields, fallback dialog): `qtbase_fr`
  catalogue loaded, reloaded on every language change; the two labels Qt 6 does not translate yet (« Look in »,
  « Files of type ») are completed by the application. Packages keep the `libqxdgdesktopportal` and `libqgtk3`
  plugins and the translations: the build fails if they are missing (Linux, macOS, Windows), and the `.deb` is
  checked in a bare container.
- **Folder on a NAS**: manuals and screen help explain how to pick a share (Linux: gvfs, kio-fuse, cifs/nfs; macOS:
  Connect to Server; Windows: network drive or UNC path). UNC paths fixed: the state database was opened through a
  SQLite URI `file://server/…` that SQLite rejects (non-empty authority); long paths `\\?\UNC\…`; gvfs and
  kio-fuse mounts recognised as network shares.
- **What you own, visible in the object list**: a marker at the start of each row in the legend's colours (green
  check: everything owned, left-out duplicates included; half disc: partly; orange triangle: at least one failure;
  arrow: nothing), object name in the same colour (contrast ≥ 4.5 in both themes), tooltip « 12 owned / 12 · 0 to
  download · 0 failed · 3 duplicate(s) left out ». The « owned » column follows the name (instead of being out of view
  on the right; an order chosen by hand is kept, the original pre-0.1.8 order is migrated) and sorts by state. The
  legend, with the « partly » state, sits below both lists.
- **Ownership summary** in the inventory line (for instance « owned: 7,625 (+ 220 duplicates left out), failed: 0, to download:
  0 »); **empty lists explain themselves** in their centre: « Pick one or more objects… », « Everything is already
  downloaded in … »; at first start, the first object is selected.
- **Changing the output folder** re-reads its ownership in the background (a stale result is ignored) and the status
  bar says so (« Ownership recomputed: N images found in … »).
- **Linux package launcher**: `Coupole.sh` follows symbolic links (links to links included, without `readlink -f`,
  missing from macOS before 12.3); a link `~/.local/bin/coupole` failed (« …/.local/bin/python/bin/python3: no such
  file »). `installer.sh` creates that link itself and reports a `~/.local/bin` missing from the `PATH`; the launcher
  of an already installed package is repaired by the application at startup (updates only replace `app/`).
- Tests: `test_dialogues_systeme.py` (+27, some Linux- or Windows-only: theme decision per desktop, portal probe, preference, parented native or
  Qt dialog, Qt translations, package pruning, UNC URI, gvfs path, real UNC on Windows, launcher through a link and a
  link to a link, launcher repair, installer), `test_catalogue_possession.py` (+16: aggregated states, sorting by
  state, markers and colours, columns, empty lists, summary, folder change).

## 0.1.7 — 9 October 2026

**Fix for an intermittent crash** (the application stopped abruptly, about one time in five in the most exposed
test series, apparently never at the same place).

- **Cause**: Python's garbage collector, which frees objects linked by circular references, ran in whichever thread
  happened to be allocating memory — often a worker thread (inventory loading, probes, map tiles). A closed window
  held only by such circular references was then destroyed **by that worker thread**, while the interface thread
  was still serving the timers of its widgets: a timer of the OHP bank panel read a field that had already been
  destroyed (“wrapped C/C++ object of type QLineEdit has been deleted”), and PyQt6 then stops the process.
- **Fix**: automatic collection is replaced by a collection at a fixed rate (every 100 ms) in the interface thread
  (`coupole/gui/fil_graphique.py`); every Qt object is now destroyed in that thread. Full collections are bounded (at
  most one every 10 s and 2 % of the time) so that the interface never freezes.
- Closed OHP bank panel: its pending display steps and timers are stopped. Deferred saving of the settings: an
  unexpected error is logged, never fatal.
- **Permanent guard in the tests**: a test fails if a display method is called outside the interface thread, if Qt
  reports an object handled from another thread, or if the garbage collector runs outside the interface thread
  (`COUPOLE_GARDE_FIL=1` also enables it in the application).
- Tests: `test_fil_graphique.py` (+6), which reproduce the exact order of the crash (closed window, then a worker
  thread allocating) and fail on 0.1.6. Budget of the loading test at ten times the bank raised to 1.2 s on
  continuous integration (×3 the slowest measurement seen: 0.39 s on macOS); 0.3 s locally.

## 0.1.6 — 9 October 2026

**Settings kept from one session to the next**: everything set on screen and every typed path comes back at the next
start (manual, “Saved settings” section).

- **Window**: size, position, screen, maximised state; safeguards: unplugged screen or position outside the screens →
  window centred again, size larger than the screen → brought back onto it (compatible with the adaptive interface,
  at 100, 150 and 200 %). Size of every dialog (and tab of the Preferences).
- **Layout**: module shown, tab of the OHP bank, splitters, width and order of the columns, sort column and direction
  of every table (columns keep fitting their contents until you choose their widths).
- **OHP bank**: search, type, telescope, “new”, “to check”, “missing only”, “without doubtful dates” boxes, night,
  filter, chosen objects (restored once the inventory is loaded), anomaly and sky-map filters. Processing tab: output
  folder kept **as soon as it is changed** (no longer only when a processing starts), format, language of names,
  “keep duplicates”, “keep FITS”, ASTAP mode, “check quality”; a folder changed in the Preferences is followed by the
  tab.
- **Image quality**: analysed folder, sample mode and N. **Spectra and series**: folder of the open dialog,
  **Recent** menu (10 files, a missing file is greyed out), axis. **Cosmology**: parameter set, custom parameters
  (kept even when going back to Planck), Ωk, z, SH0ES option, and a new **curve scale** (distances logarithmic or
  linear). **Sites and times**: chosen site, zoom and centre of the map, “online map”.
- **File dialogs**: each one opens again in the last folder used (CSV exports, reorganisation, ASTAP, report…).
- A single mechanism (`core/etat_interface.py`, `gui/memoire.py`): versioned `interface.json` next to
  `reglages.json`; **deferred, grouped** writing (at most once every 2 s, plus once on closing), atomic, only when
  something changed — never one write per keystroke; tolerant reading (missing key, wrong type, out-of-range value →
  default; unreadable file set aside); path existence checked in the background (an absent network share does not
  block start-up). Nothing dangerous to replay is kept: a processing never restarts on its own.
- **Reset**: Preferences > “Reset the layout” (immediate, settings untouched) and `coupole --reinitialiser-interface`
  (`--reset-interface`).
- Tests: `test_reglages_conserves.py` (+11) — two successive windows find every element again; corrupt or wrongly
  typed settings → defaults; off-screen position, missing screen, maximised window; no disk write while typing (then a
  single grouped one); reset. Every test starts from a blank layout.

## 0.1.5 — 9 October 2026

The two slow spots left by the second audit (`docs/AUDIT2_2026-10.md`, § 8), measured at ten times the bank
(80,000 rows); nothing displayed changes (sort orders identical to 0.1.4 on the real bank and at ×10; cells,
anomalies, sky map and batches identical).

- **Loading without freezes**: longest silence of the GUI thread while loading **0.55–0.8 s → 55–66 ms** at 80,000
  rows (0.16 s → 40 ms on the bank). It was no longer a GUI-thread computation but GIL contention: sky map,
  anomalies and ownership ran in three threads while the tables were first painted, and every Qt-to-Python callback
  waited for the GIL. They are now computed one after the other by the loading thread, before the inventory is
  handed over; display then happens in short steps; loading starts 0.2 s after the window is first painted (catalogue
  ready ~0.2 s later than before).
- **Sorting by site time and by flags**: integer keys computed once at load time (in the background), numpy sort:
  **0.66–0.78 s → 50–60 ms** at 80,000 rows; every column of the image table now has a fast key (40–80 ms at 80,000
  rows), and the double sort requested by `QTableView.sortByColumn` is no longer done twice.
- "Select all" without a filter no longer walks the inventory (the already sorted list is reused as is).
- Tests: `test_echelle.py` (+4) — real loading of 80,000 rows with no silence > 100 ms (×3 budget), sorting the site
  time / flags columns < 150 ms (×3), every fast key equal to the order of the cells on the real bank, numpy sort
  identical to `sorted`.

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
