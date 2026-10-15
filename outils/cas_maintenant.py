#!/usr/bin/env python3
"""Génère tests/maintenant_cas.json : cas de parité de « Maintenant » (Python ↔ TypeScript), fuseaux et heures
d'été compris.  python3 outils/cas_maintenant.py [CHEMIN_DE_COUPOLE_WEB]  (recopie aussi le fichier au web)."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))

from coupole.modules.anim import maintenant as M  # noqa: E402

INSTANTS = [
    '2026-10-25T00:59:59Z',   # Paris : 02:59:59 heure d'été (UTC+2), dernière seconde
    '2026-10-25T01:00:00Z',   # Paris : 02:00:00 heure d'hiver (UTC+1)
    '2026-03-29T00:59:00Z', '2026-03-29T01:00:00Z',   # passage à l'heure d'été
    '2026-12-31T23:30:00Z',   # jour de l'an à Paris, pas encore à Londres
    '2026-12-31T10:59:00Z', '2026-12-31T11:00:00Z',   # jour de l'an à Auckland (UTC+13)
    '2026-07-15T12:00:00Z', '2026-01-15T12:00:00Z',
    '2028-02-29T18:00:00Z',   # 29 février
    '2026-11-01T05:59:00Z', '2026-11-01T06:00:00Z',   # New York repasse en heure d'hiver
    '2026-04-05T13:59:00Z', '2026-04-05T14:00:00Z',   # Auckland repasse en heure d'hiver
    '2026-10-15T07:20:00Z',
]
FUSEAUX = ['Europe/Paris', 'Europe/London', 'Pacific/Auckland', 'America/St_Johns', 'Asia/Kathmandu', 'America/New_York',
           'Australia/Lord_Howe', 'Pacific/Chatham', 'Asia/Kolkata', 'UTC', 'Pas/Un_Fuseau']


def ms(iso):
    return int(datetime.fromisoformat(iso.replace('Z', '+00:00')).timestamp() * 1000)


def main() -> int:
    cas = []
    for iso in INSTANTS:
        for tz in FUSEAUX:
            i = M.instant(ms(iso), tz)
            js, hs = M.heure_solaire(i, M.meridien_du_fuseau(i))
            js2, hs2 = M.heure_solaire(i, 2.35)
            cas.append({
                'iso': iso, 'tz': tz, 'ms': i.ms, 'tz_retenu': i.tz, 'decalage': i.decalage, 'decalage_standard': i.decalage_standard,
                'local': list(i.local), 'tu': list(i.tu), 'jj': i.jj,
                'jour_local': M.jour_index(i.local[1], i.local[2]), 'jour_tu': M.jour_tu(i),
                'meridien': M.meridien_du_fuseau(i), 'solaire_meridien': [js, hs], 'solaire_paris': [js2, hs2],
                'tsl_paris': M.tsl_heures(i.jj, 2.35), 'annee_decimale': M.annee_decimale(i), 'elongation_lune': M.elongation_lune(i.jj),
                'texte_fr': M.texte_heure(i, 'fr'), 'texte_en': M.texte_heure(i, 'en'),
                'date_fr': M.texte_date(i, 'fr'), 'date_en': M.texte_date(i, 'en'),
            })
    libelles = [[m, M.libelle_decalage(m)] for m in (0, 60, 120, -150, 345, 780, -210, 825, -600, 30)]
    jours = [[m, j, M.jour_index(m, j)] for m, j in ((1, 1), (2, 28), (2, 29), (3, 1), (12, 31), (10, 25))]
    texte = json.dumps({'format': 'coupole-maintenant-cas', 'version': 1, 'cas': cas, 'libelles': libelles, 'jours': jours}, ensure_ascii=False, indent=1) + '\n'
    (ICI / 'tests' / 'maintenant_cas.json').write_text(texte, encoding='utf-8')
    if len(sys.argv) > 1:
        (Path(sys.argv[1]) / 'tests' / 'references' / 'maintenant_cas.json').write_text(texte, encoding='utf-8')
    print(len(cas), 'cas')
    return 0


if __name__ == '__main__':
    sys.exit(main())
