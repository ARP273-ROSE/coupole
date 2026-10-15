#!/usr/bin/env python3
"""Génère tests/recherche_cas.json : cas de parité du moteur de recherche commun (Python ↔ TypeScript).

    python3 outils/cas_recherche.py [CHEMIN_DE_COUPOLE_WEB]

Trois familles de cas, rejouées par tests/test_recherche.py (ici) et tests/unit/recherche.test.ts (Coupole Web) :
- « unitaires » : normaliser, mots, racine, termes, distance, surligner, extrait ;
- « corpus » : un petit corpus inventé, des recherches, les résultats complets (genre, id, mots trouvés, points) ;
- « reel » : les vrais contenus (questions, fiches, tables, images, 94 animations, 24 modules) ; pour chaque
  recherche, les 8 premiers résultats et les points : le web, qui construit son index de son côté avec les mêmes
  données, doit trouver exactement les mêmes.
Avec le chemin de Coupole Web, le fichier y est aussi recopié (tests/references/recherche_cas.json).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ICI))

from coupole.modules.anim.classe import contenu, recherche as R  # noqa: E402

MOTS = ['Saisons', 'seasons', 'Galaxies', 'galaxie', 'galaxy', 'Planètes', 'planets', 'masses', 'Masse', 'classes',
        'spectraux', 'cieux', 'Vénus', 'axis', 'lois', 'Éclipses', 'série', 'series', 'bodies', 'Kepler’s', 'œil',
        'Straße', 'H₂O', '2026', 'phase', 'des', 'Lune', 'eaux']
DISTANCES = [('kepler', 'kelper', 2), ('saison', 'season', 2), ('saison', 'season', 1), ('parallaxe', 'paralax', 2),
             ('orbit', 'orbite', 1), ('abc', 'xyz', 1), ('spectre', 'specter', 2), ('lune', 'lnue', 1), ('', 'abc', 3)]
TEXTES = ['La troisième loi de Kepler relie la période et le demi-grand axe.', 'Simulateur des saisons',
          'Kepler’s third law: P² ∝ a³ — Œuvres complètes', 'Éclipses de Lune et de Soleil']

CORPUS = [
    {'g': 'animation', 'id': 'seasons', 't': {'fr': 'Simulateur des saisons', 'en': 'Seasons Simulator'},
     'o': 'Seasons and Ecliptic Simulator', 'k': {'fr': 'seasons Le Soleil', 'en': 'The Sun'},
     'r': {'fr': 'Inclinaison de l’axe de la Terre et durée du jour.', 'en': 'Tilt of Earth’s axis and length of day.'}},
    {'g': 'fiche', 'id': 'kepler3', 't': {'fr': 'Troisième loi de Kepler', 'en': 'Kepler’s third law'},
     'k': {'fr': 'période demi-grand axe orbite', 'en': 'period semi-major axis orbit'},
     'r': {'fr': 'Le carré de la période est proportionnel au cube du demi-grand axe.', 'en': 'The square of the period is proportional to the cube of the semi-major axis.'}},
    {'g': 'animation', 'id': 'keplerslaws', 't': {'fr': 'Lois de Kepler', 'en': 'Kepler’s Laws'}, 'o': 'Planetary Orbit Simulator',
     'k': {'fr': 'keplerslaws Orbites', 'en': 'Orbits'}, 'r': {'fr': 'Les trois lois des orbites.', 'en': 'The three laws of orbits.'}},
    {'g': 'question', 'id': 'q_eclipse', 't': {'fr': 'Éclipse de Lune', 'en': 'Lunar Eclipse'}, 'm': ['lunarcycles'],
     'k': {'fr': '', 'en': ''}, 'r': {'fr': 'Pourquoi la Lune devient-elle rouge pendant une éclipse totale ?', 'en': 'Why does the Moon turn red during a total eclipse?'}},
    {'g': 'table', 'id': 'galaxies', 't': {'fr': 'Galaxies proches', 'en': 'Nearby galaxies'}, 'k': {'fr': 'Voie lactée Andromède', 'en': 'Milky Way Andromeda'},
     'r': {'fr': 'Distances et masses des galaxies du Groupe local.', 'en': 'Distances and masses of Local Group galaxies.'}},
    {'g': 'image', 'id': 'm31', 't': {'fr': 'La galaxie d’Andromède', 'en': 'The Andromeda Galaxy'}, 'k': {'fr': 'M31 spirale', 'en': 'M31 spiral'},
     'r': {'fr': 'Une galaxie spirale à 2,5 millions d’années-lumière.', 'en': 'A spiral galaxy 2.5 million light-years away.'}},
    {'g': 'module', 'id': 'lunarcycles', 't': {'fr': 'Les cycles de la Lune', 'en': 'Lunar Cycles'}, 'o': 'Lunar Cycles', 'k': {'fr': 'lunarcycles', 'en': ''}},
    {'g': 'module', 'id': 'galaxies', 't': {'fr': 'Galaxies', 'en': 'Galaxies'}, 'o': 'Galaxies', 'k': {'fr': 'galaxies', 'en': ''}},
    {'g': 'fiche', 'id': 'parallaxe', 't': {'fr': 'Parallaxe', 'en': 'Parallax'}, 'k': {'fr': 'distance étoiles parsec', 'en': 'distance stars parsec'},
     'r': {'fr': 'Le déplacement apparent d’une étoile proche quand la Terre tourne autour du Soleil.', 'en': 'The apparent shift of a nearby star as Earth orbits the Sun.'}},
    {'g': 'question', 'id': 'q_spectre', 't': {'fr': 'Spectres des étoiles', 'en': 'Stellar Spectra'}, 'm': ['light'],
     'k': {'fr': 'raies classes spectrales', 'en': 'lines spectral classes'}, 'r': {'fr': 'Quelle étoile est la plus chaude ?', 'en': 'Which star is hottest?'}},
]
REQUETES_CORPUS = ['seasons', 'saisons', 'Saison', 'SAISONS', 'Kepler’s third law', 'troisieme loi de kepler', 'kepler',
                   'kelper', 'keplr', 'galaxy', 'galaxies', 'Andromede', 'andromeda galaxy', 'lunar eclipse', 'éclipse lune',
                   'eclipe', 'parallax', 'paralaxe', 'parsec', 'spectral classes', 'classe spectrale', 'sai', 'or', 'the',
                   'de la', 'm31', '2,5', 'xyzzy', '', '   ', 'orbits laws', 'Lunar Cycles', 'cycles lune', 'étoile chaude',
                   'hottest star', 'demi grand axe', 'semi major axis', 'seasons simulator']

REQUETES_REELLES = ['seasons', 'saisons', 'Kepler’s third law', 'troisième loi de Kepler', 'kepler', 'kelper', 'parallax',
                    'paralaxe', 'parallaxe spectroscopique', 'spectroscopic parallax', 'phases of the moon',
                    'phases de la lune', 'lunar phases', 'eclipse', 'éclipses', 'galaxies', 'galaxy rotation',
                    'rotation galaxie', 'black body', 'corps noir', 'wien', 'doppler', 'redshift', 'décalage vers le rouge',
                    'hubble', 'exoplanets', 'exoplanètes', 'transit', 'retrograde', 'rétrograde', 'sun', 'Soleil',
                    'hr diagram', 'diagramme HR', 'binary stars', 'étoiles binaires', 'tides', 'marées', 'antikythera',
                    'anticythère', 'orion', 'telescope', 'télescope', 'light', 'lumière', 'cosmology', 'cosmologie',
                    'big bang', 'dark matter', 'matière noire', 'scale', 'échelle', 'sidereal day', 'jour sidéral',
                    'celestial sphere', 'sphère céleste', 'equinox', 'équinoxe', 'solstice', 'zodiac', 'constellations',
                    'neutron star', 'étoile à neutrons', 'supernova', 'stellar evolution', 'évolution stellaire',
                    'mars', 'jupiter', 'comets', 'comètes', 'atmosphere', 'greenhouse', 'effet de serre', 'density',
                    'masse volumique', 'scientific notation', 'notation scientifique', 'spectre', 'spectrum',
                    'spectra', 'kirchoff', 'kirchhoff', 'ccd', 'magnitude', 'luminosity', 'luminosité', 'orbits',
                    'orbite', 'gravity', 'gravitation', 'moon', 'lune', 'introductory concepts', 'notions de base',
                    'planetary orbit simulator', 'seasons and ecliptic simulator', 'simulateur des saisons']


def resume(r):
    return {'g': r['doc']['g'], 'id': r['doc']['id'], 'n': r['n'], 'score': r['score'], 'mots': r['mots']}


def main() -> int:
    cas = {'format': 'coupole-recherche-cas', 'version': 1, 'moteur': R.FORMAT}
    cas['unitaires'] = {
        'normaliser': [[m, R.normaliser(m)] for m in MOTS],
        'mots': [[t, R.mots(t)] for t in TEXTES],
        'racine': [[w, R.racine(w)] for w in [x for m in MOTS for x in R.mots(m)]],
        'termes': [[q, R.termes(q)] for q in REQUETES_CORPUS[:30]],
        'distance': [[a, b, k, R.distance(a, b, k)] for a, b, k in DISTANCES],
        'surligner': [[t, sorted({w for w in R.mots(t)[:3]}), [list(x) for x in R.surligner(t, set(R.mots(t)[:3]))]] for t in TEXTES],
        'extrait': [[t * 4, ['saisons', 'kepler'], 60, R.extrait(t * 4, {'saisons', 'kepler'}, 60)] for t in TEXTES],
    }
    idx = R.Index(CORPUS)
    cas['corpus'] = {'documents': CORPUS, 'requetes': [[q, [resume(r) for r in idx.chercher(q)]] for q in REQUETES_CORPUS]}
    reel = contenu.index()
    cas['reel'] = {'documents': len(reel.docs), 'vocabulaire': len(reel.vocab),
                   'requetes': [[q, [resume(r) for r in reel.chercher(q, 8)]] for q in REQUETES_REELLES]}
    texte = json.dumps(cas, ensure_ascii=False, indent=1) + '\n'
    (ICI / 'tests' / 'recherche_cas.json').write_text(texte, encoding='utf-8')
    if len(sys.argv) > 1:
        (Path(sys.argv[1]) / 'tests' / 'references' / 'recherche_cas.json').write_text(texte, encoding='utf-8')
    print(len(reel.docs), 'documents,', len(reel.vocab), 'mots ;', len(REQUETES_CORPUS), '+', len(REQUETES_REELLES), 'recherches')
    return 0


if __name__ == '__main__':
    sys.exit(main())
