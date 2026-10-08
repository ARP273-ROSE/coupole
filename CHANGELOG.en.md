# Changelog

French version (reference): [CHANGELOG.md](CHANGELOG.md).

## 0.1.0 — 8 October 2026

First release.

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
