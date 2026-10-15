"""Recherche bilingue — moteur commun à Coupole Web et à Coupole (bureau).

Portage ligne pour ligne de `coupole-web/src/contenu/recherche.ts` (mêmes noms en snake_case, mêmes nombres
entiers) ; sans dépendance ni entrée-sortie.  Cas de parité : `tests/recherche_cas.json` (produit par
`outils/cas_recherche.py`), rejoué par `tests/test_recherche.py` ici et par `tests/unit/recherche.test.ts` au web.

Règles (identiques des deux côtés) :
- un document = {g, id, t: {fr, en}, o: titre d'origine, k: {fr, en} mots-clés, r: {fr, en} texte, m: [modules]} ;
  les deux langues sont indexées ensemble : une recherche en anglais ou en français trouve le même document, qui
  s'affiche ensuite dans la langue de l'interface ;
- normalisation : minuscules, sans accents (U+0300–U+036F retirés après décomposition), œ → oe, æ → ae, ß → ss ;
  mots = suites de lettres et de chiffres ;
- racine (pluriels simples, français et anglais) : -aux → -al, -eux → -eu, -ies → -y, -s final retiré (sauf -ss,
  -us, -is), puis -e final retiré et -y final → -i (mots de plus de 3 lettres) : saisons ≈ saison, galaxies ≈ galaxie
  ≈ galaxy ≈ galaxi, planètes ≈ planets, masses ≈ mass ;
- mots vides (articles, prépositions…) ignorés quand la recherche contient autre chose, ainsi que les lettres
  isolées (« Kepler's » → kepler) ;
- un mot cherché correspond à un mot de l'index : même racine (10 points), début du mot (8 points, 2 lettres au
  moins), petite faute (distance d'édition avec transpositions, sur les racines : 1 faute dès 4 lettres → 7 points,
  2 fautes dès 8 lettres → 5 points) ; points multipliés par le poids du champ : titre (et titre d'origine) 3,
  mots-clés 2, texte 1 ; meilleur champ retenu pour chaque mot cherché ;
- phrase : +12 si la recherche entière est un titre, +6 si elle est contenue dans un titre (mots entiers) ;
- couverture : + 6 × (mots du titre trouvés) / (mots du titre), division entière, meilleur titre (un titre court
  entièrement trouvé passe devant un long titre qui contient le mot en passant) ;
- au moins la moitié des mots cherchés doivent être trouvés (arrondi au-dessus) ; tri : nombre de mots trouvés,
  points, genre (module, animation, question, fiche, table, image), identifiant.
"""
from __future__ import annotations

import re
import unicodedata

FORMAT = 'coupole-recherche/1'
ORDRE_GENRES = ('module', 'animation', 'question', 'fiche', 'table', 'image')
POIDS = {'titre': 3, 'cles': 2, 'texte': 1}
EXACT, DEBUT, FAUTE1, FAUTE2 = 10, 8, 7, 5
BONUS_TITRE, BONUS_DANS_TITRE, COUVERTURE = 12, 6, 6

MOTS_VIDES = frozenset('''
a au aux avec ce ces cet cette d dans de des du elle en et il l la le les leur leurs ne on ou par pas pour qu que
qui sa se ses son sont sur un une y
an and are as at be by for from how in is it its of on or the this that to what when which why with
'''.split())

_SEP = re.compile(r'[\W_]+')
_MOT = re.compile(r'[^\W_]+')
_NOMBRE = re.compile(r'[0-9]+')


def normaliser(s: str) -> str:
    s = unicodedata.normalize('NFD', s.lower())
    s = ''.join(c for c in s if not '̀' <= c <= 'ͯ')
    return s.replace('œ', 'oe').replace('æ', 'ae').replace('ß', 'ss')


def mots(s: str) -> list:
    return [m for m in _SEP.split(normaliser(s)) if m]


def racine(w: str) -> str:
    if len(w) <= 3 or _NOMBRE.fullmatch(w):
        return w
    if w.endswith('aux') and len(w) > 4:
        w = w[:-3] + 'al'
    elif w.endswith('eux') and len(w) > 4:
        w = w[:-1]
    elif w.endswith('ies') and len(w) > 4:
        w = w[:-3] + 'y'
    elif w.endswith('s') and not w.endswith(('ss', 'us', 'is')):
        w = w[:-1]
    if len(w) > 3 and w.endswith('e'):
        w = w[:-1]
    if len(w) > 3 and w.endswith('y'):
        w = w[:-1] + 'i'
    return w


def distance(a: str, b: str, borne: int) -> int:
    """Distance d'édition avec transpositions adjacentes (OSA) ; borne + 1 dès qu'elle dépasse la borne."""
    la, lb = len(a), len(b)
    if abs(la - lb) > borne:
        return borne + 1
    prec2 = None
    prec = list(range(lb + 1))
    for i in range(1, la + 1):
        cour = [i] + [0] * lb
        mini = i
        for j in range(1, lb + 1):
            c = 0 if a[i - 1] == b[j - 1] else 1
            v = min(prec[j] + 1, cour[j - 1] + 1, prec[j - 1] + c)
            if prec2 is not None and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                v = min(v, prec2[j - 2] + 1)
            cour[j] = v
            if v < mini:
                mini = v
        if mini > borne:
            return borne + 1
        prec2, prec = prec, cour
    return prec[lb] if prec[lb] <= borne else borne + 1


def termes(q: str) -> list:
    """Mots cherchés : sans mots vides ni lettres isolées s'il reste autre chose ; sans doublon."""
    tous = mots(q)
    utiles = [w for w in tous if w not in MOTS_VIDES and (len(w) > 1 or _NOMBRE.fullmatch(w))]
    out = []
    for w in (utiles or tous):
        if w not in out:
            out.append(w)
    return out


def _bi(v, lg):
    if isinstance(v, dict):
        return str(v.get(lg) or '')
    return '' if v is None else str(v)


class Index:
    """Index d'un ensemble de documents (voir le module).  `docs` est gardé tel quel (résultats)."""

    def __init__(self, docs: list):
        self.docs = list(docs)
        self.vocab = {}            # mot normalisé → [racine, {numéro du document: poids du meilleur champ}]
        self.titres = []           # titres normalisés (mots joints par une espace), pour la phrase
        for n, d in enumerate(self.docs):
            champs = (
                ('titre', ' '.join([_bi(d.get('t'), 'fr'), _bi(d.get('t'), 'en'), str(d.get('o') or '')])),
                ('cles', ' '.join([_bi(d.get('k'), 'fr'), _bi(d.get('k'), 'en')])),
                ('texte', ' '.join([_bi(d.get('r'), 'fr'), _bi(d.get('r'), 'en')])),
            )
            for champ, texte in champs:
                p = POIDS[champ]
                for w in mots(texte):
                    e = self.vocab.get(w)
                    if e is None:
                        e = self.vocab[w] = [racine(w), {}]
                    if e[1].get(n, 0) < p:
                        e[1][n] = p
            self.titres.append([mots(x) for x in (_bi(d.get('t'), 'fr'), _bi(d.get('t'), 'en'), str(d.get('o') or '')) if x])

    def correspondances(self, terme: str) -> list:
        """[(mot de l'index, points)] pour un mot cherché."""
        r = racine(terme)
        num = _NOMBRE.fullmatch(terme) is not None
        borne = 0 if num or len(terme) < 4 else (1 if len(terme) < 8 else 2)
        out = []
        for w, (rw, _) in self.vocab.items():
            if rw == r:
                pts = EXACT
            elif len(terme) >= 2 and w.startswith(terme):
                pts = DEBUT
            elif borne:
                d = distance(r, rw, borne)
                pts = 0 if d > borne else FAUTE1 if d == 1 else FAUTE2
            else:
                pts = 0
            if pts:
                out.append((w, pts))
        return out

    def chercher(self, q: str, limite: int = 0) -> list:
        """Résultats triés : [{doc, n, score, mots}] (mots : mots normalisés de l'index trouvés, pour surligner)."""
        ts = termes(q)
        if not ts:
            return []
        par_doc = {}               # numéro → [points par terme, mots trouvés]
        for k, t in enumerate(ts):
            for w, pts in self.correspondances(t):
                for n, poids in self.vocab[w][1].items():
                    e = par_doc.get(n)
                    if e is None:
                        e = par_doc[n] = [[0] * len(ts), set()]
                    if pts * poids > e[0][k]:
                        e[0][k] = pts * poids
                    e[1].add(w)
        minimum = (len(ts) + 1) // 2
        phrase = ' '.join(mots(q))
        res = []
        for n, (points, trouves) in par_doc.items():
            nb = sum(1 for p in points if p)
            if nb < minimum:
                continue
            score = sum(points)
            titres = [' '.join(t) for t in self.titres[n]]
            if any(t == phrase for t in titres):
                score += BONUS_TITRE
            elif phrase and any((' ' + phrase + ' ') in (' ' + t + ' ') for t in titres):
                score += BONUS_DANS_TITRE
            score += max([COUVERTURE * sum(1 for w in t if w in trouves) // len(t) for t in self.titres[n] if t] or [0])
            res.append({'doc': self.docs[n], 'n': nb, 'score': score, 'mots': sorted(trouves)})
        res.sort(key=lambda x: (-x['n'], -x['score'], _ordre(x['doc'].get('g')), str(x['doc'].get('id'))))
        return res[:limite] if limite else res


def _ordre(g) -> int:
    return ORDRE_GENRES.index(g) if g in ORDRE_GENRES else len(ORDRE_GENRES)


def surligner(texte: str, trouves) -> list:
    """Découpe `texte` en [(morceau, surligné)] : un mot est surligné si sa forme normalisée est dans `trouves`."""
    trouves = set(trouves)
    out, i = [], 0
    for m in _MOT.finditer(texte):
        if normaliser(m.group()) in trouves:
            if m.start() > i:
                out.append((texte[i:m.start()], False))
            out.append((m.group(), True))
            i = m.end()
    if i < len(texte):
        out.append((texte[i:], False))
    return out


def extrait(texte: str, trouves, longueur: int = 160) -> str:
    """Passage de `texte` (≈ longueur caractères) autour du premier mot trouvé, avec « … » aux coupures."""
    if len(texte) <= longueur:
        return texte
    trouves = set(trouves)
    debut = 0
    for m in _MOT.finditer(texte):
        if normaliser(m.group()) in trouves:
            debut = max(0, m.start() - longueur // 3)
            break
    if debut:
        k = texte.find(' ', debut)
        debut = k + 1 if 0 <= k < debut + 20 else debut
    fin = min(len(texte), debut + longueur)
    if fin < len(texte):
        k = texte.rfind(' ', debut, fin)
        fin = k if k > debut + longueur // 2 else fin
    return ('…' if debut else '') + texte[debut:fin].strip() + ('…' if fin < len(texte) else '')
