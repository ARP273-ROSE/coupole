"""Corps du Système solaire : noms français et anglais, et comment chaque archive les nomme.

SIMBAD ne connaît pas les planètes (« jupiter » y est introuvable) : un corps du Système solaire se cherche par
**nom de cible**, jamais par position (il bouge).  Noms tels que les archives les écrivent, vérifiés le 12 octobre
2026 : MAST ``target_name`` en capitales avec suffixes (« JUPITER », « JUPITER-MAPS », « SATURN-MAPS ») et
``mtflag = 1`` (cible mobile) ; OPUS ``target`` en anglais (« Jupiter », « Enceladus », table
``meta/mults/target.json``) ; Atlas du PDS ``TARGET_NAME`` en minuscules (« jupiter », « io », « europa »).
"""
from __future__ import annotations

import unicodedata

# (anglais, français, type, parent, autres noms) — l'anglais est le nom envoyé aux archives
_TABLE = (
    ('Sun', 'Soleil', 'etoile', '', ()),
    ('Mercury', 'Mercure', 'planete', '', ()),
    ('Venus', 'Vénus', 'planete', '', ()),
    ('Earth', 'Terre', 'planete', '', ()),
    ('Moon', 'Lune', 'satellite', 'Earth', ()),
    ('Mars', 'Mars', 'planete', '', ()),
    ('Phobos', 'Phobos', 'satellite', 'Mars', ()),
    ('Deimos', 'Déimos', 'satellite', 'Mars', ()),
    ('Ceres', 'Cérès', 'naine', '', ()),
    ('Vesta', 'Vesta', 'asteroide', '', ()),
    ('Jupiter', 'Jupiter', 'planete', '', ()),
    ('Io', 'Io', 'satellite', 'Jupiter', ()),
    ('Europa', 'Europe', 'satellite', 'Jupiter', ()),
    ('Ganymede', 'Ganymède', 'satellite', 'Jupiter', ()),
    ('Callisto', 'Callisto', 'satellite', 'Jupiter', ()),
    ('Amalthea', 'Amalthée', 'satellite', 'Jupiter', ()),
    ('Himalia', 'Himalia', 'satellite', 'Jupiter', ()),
    ('Saturn', 'Saturne', 'planete', '', ()),
    ('Mimas', 'Mimas', 'satellite', 'Saturn', ()),
    ('Enceladus', 'Encelade', 'satellite', 'Saturn', ()),
    ('Tethys', 'Téthys', 'satellite', 'Saturn', ()),
    ('Dione', 'Dioné', 'satellite', 'Saturn', ()),
    ('Rhea', 'Rhéa', 'satellite', 'Saturn', ()),
    ('Titan', 'Titan', 'satellite', 'Saturn', ()),
    ('Hyperion', 'Hypérion', 'satellite', 'Saturn', ()),
    ('Iapetus', 'Japet', 'satellite', 'Saturn', ()),
    ('Phoebe', 'Phœbé', 'satellite', 'Saturn', ('Phoebé',)),
    ('Janus', 'Janus', 'satellite', 'Saturn', ()),
    ('Epimetheus', 'Épiméthée', 'satellite', 'Saturn', ()),
    ('Pan', 'Pan', 'satellite', 'Saturn', ()),
    ('Saturn Rings', 'Anneaux de Saturne', 'anneaux', 'Saturn', ('anneaux', 'rings')),
    ('Jupiter Rings', 'Anneaux de Jupiter', 'anneaux', 'Jupiter', ('j rings',)),
    ('Uranus', 'Uranus', 'planete', '', ()),
    ('Miranda', 'Miranda', 'satellite', 'Uranus', ()),
    ('Ariel', 'Ariel', 'satellite', 'Uranus', ()),
    ('Umbriel', 'Umbriel', 'satellite', 'Uranus', ()),
    ('Titania', 'Titania', 'satellite', 'Uranus', ()),
    ('Oberon', 'Obéron', 'satellite', 'Uranus', ()),
    ('Uranus Rings', 'Anneaux d\'Uranus', 'anneaux', 'Uranus', ()),
    ('Neptune', 'Neptune', 'planete', '', ()),
    ('Triton', 'Triton', 'satellite', 'Neptune', ()),
    ('Nereid', 'Néréide', 'satellite', 'Neptune', ()),
    ('Neptune Rings', 'Anneaux de Neptune', 'anneaux', 'Neptune', ()),
    ('Pluto', 'Pluton', 'naine', '', ()),
    ('Charon', 'Charon', 'satellite', 'Pluto', ()),
)

# noms MAST : capitales ; les noms courts (≤ 4 lettres) ne sont pris qu'exactement ou suivis d'un séparateur
MAST_NOMS = {'Saturn Rings': ('SATURN-RING',), 'Jupiter Rings': ('JUPITER-RING',), 'Uranus Rings': ('URANUS-RING',),
             'Neptune Rings': ('NEPTUNE-RING',), 'Moon': ('MOON',)}
# Atlas du PDS (JunoCam) : « j rings »
PDS_NOMS = {'Jupiter Rings': 'j rings'}


def normaliser(texte: str) -> str:
    """Minuscules, sans accents ni ligatures, sans espaces, tirets ni apostrophes : « Phœbé » → « phoebe »."""
    t = (texte or '').strip().lower().replace('œ', 'oe').replace('æ', 'ae')
    t = ''.join(c for c in unicodedata.normalize('NFKD', t) if not unicodedata.combining(c))
    return ''.join(c for c in t if c.isalnum())


class Corps(dict):
    """{'en', 'fr', 'type', 'parent'} ; `nom(langue)`."""

    def nom(self, langue: str = 'fr') -> str:
        return self['fr'] if langue == 'fr' else self['en']


CORPS: list[Corps] = [Corps(en=en, fr=fr, type=ty, parent=pa, autres=autres) for en, fr, ty, pa, autres in _TABLE]
_INDEX: dict[str, Corps] = {}
for _c in CORPS:
    for _n in (_c['en'], _c['fr']) + tuple(_c['autres']):
        _INDEX.setdefault(normaliser(_n), _c)


def reconnaitre(texte: str) -> Corps | None:
    """Le corps nommé (français ou anglais, casse et accents indifférents), sinon None."""
    return _INDEX.get(normaliser(texte))


def suggestions(debut: str, langue: str = 'fr', n: int = 8) -> list[str]:
    """Noms de corps qui commencent par `debut` (sans casse ni accents), dans la langue demandée d'abord."""
    d = normaliser(debut)
    if not d:
        return []
    out = []
    for c in CORPS:
        for nom in (c.nom(langue), c.nom('en' if langue == 'fr' else 'fr')):
            if normaliser(nom).startswith(d) and nom not in out:
                out.append(nom)
                break
    return out[:n]


def noms_mast(c: Corps) -> tuple[str, ...]:
    return MAST_NOMS.get(c['en'], (c['en'].upper(),))


def condition_mast(c: Corps) -> str:
    """Condition ADQL sur ``target_name`` (cible mobile) : « JUPITER », « JUPITER-MAPS », « JUPITER2 »… ; pour un nom
    court (IO), seulement exact ou suivi de « - » ou « + » (sinon « IO » prendrait « IONOSPHERE »)."""
    morceaux = []
    for n in noms_mast(c):
        n = n.replace("'", "''")
        if len(n) <= 4:
            morceaux += ["target_name = '%s'" % n, "target_name LIKE '%s-%%'" % n, "target_name LIKE '%s+%%'" % n]
        else:
            morceaux.append("target_name LIKE '%s%%'" % n)
    return '(%s)' % ' OR '.join(morceaux)


def nom_opus(c: Corps) -> str:
    return c['en']


def nom_pds(c: Corps) -> str:
    return PDS_NOMS.get(c['en'], c['en'].lower())
