"""Formules mathématiques : un petit analyseur pour les formules écrites en texte simple dans les textes de Coupole
(« F = G M₁ M₂ / R² », « b = √(a² − c²) », « f₀ / (1 − v_r / c) »…) et un moteur de mise en page maison en QPainter
(fractions empilées, exposants, indices, radicaux, parenthèses extensibles, variables d'une lettre en italique
mathématique), avec la police STIX Two Math (SIL OFL 1.1) embarquée en sous-ensemble.  Ni matplotlib, ni LaTeX.

Grammaire (du moins au plus liant) : relation (= ∝ ≈ < > ≤ ≥) ; somme (+ − ±) ; quotient (« a b / c d » : tout le
produit de gauche sur tout le produit de droite) ; produit (juxtaposition, × ·) ; « a/b » collé lie plus fort que
« a b / c d » espacé ; facteur avec exposants (²³⁴⁻ⁿ… ou ^x) et indices (₀₁₂… ou _x) ; primaire : nombre,
identificateur, (…), √facteur.  R☉, M⊕ : le symbole est un indice.

Même analyseur et mêmes règles que Coupole Web (src/noyau/formule.ts), pour un rendu identique.

Mise en page : ``mise_en_page(s, taille_px)`` rend une liste de primitives (textes, traits) mise en cache ;
``dessiner(p, x, y, s)`` les peint dans la couleur du stylo courant ; ``html(s, …)`` rend une image en ligne pour les
textes riches de Qt (descriptions, valeurs, aide), et ``enrichir(texte)`` y remplace les formules reconnues."""
from __future__ import annotations

import base64
import functools
import html as _html
import re
from pathlib import Path

# ==================================================================== analyse
EXPOSANTS = {'⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9',
             '⁻': '−', '⁺': '+', 'ⁿ': 'n', 'ⁱ': 'i'}
INDICES = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
           '₊': '+', '₋': '−', 'ₐ': 'a', 'ₑ': 'e', 'ₒ': 'o', 'ₓ': 'x', 'ₙ': 'n', 'ₚ': 'p', 'ₛ': 's', 'ₜ': 't'}
MOTS = ('asin', 'acos', 'atan', 'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'max', 'min', 'TSL', 'LST', 'TU', 'UT')
RELATIONS = frozenset('=∝≈<>≤≥≠≡→')
SYMBOLES_DROITS = frozenset('☉⊕*')
_LETTRE = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿΑ-Ωα-ωϑϕϵ☉⊕*]')
_ESPACES = '    '


class Jeton:
    __slots__ = ('k', 'v', 'esp')

    def __init__(self, k, v):
        self.k, self.v, self.esp = k, v, False


def jetons(s: str) -> list:
    out = []
    car = list(s)
    i = 0
    espace = False

    def pousser(j):
        nonlocal espace
        j.esp = espace
        espace = False
        out.append(j)

    while i < len(car):
        c = car[i]
        if c in _ESPACES:
            espace = True
            i += 1
            continue
        if c.isdigit() and c in '0123456789':
            # nombre : chiffres, séparateur décimal, espaces fines de milliers, unités d'angle collées (° ′ ″)
            v = c
            i += 1
            while i < len(car):
                d = car[i]
                suite = car[i + 1] if i + 1 < len(car) else ''
                if d in '0123456789':
                    v += d
                elif d in ',.' and suite in '0123456789' and suite:
                    v += d
                elif d in '  ' and re.match(r'^[0-9]{3}(?![0-9])', ''.join(car[i + 1:i + 5])):
                    v += ' '
                elif d in '°′″':
                    v += d
                else:
                    break
                i += 1
            pousser(Jeton('nb', v))
            continue
        if c in EXPOSANTS:
            v = ''
            while i < len(car) and car[i] in EXPOSANTS:
                v += EXPOSANTS[car[i]]
                i += 1
            pousser(Jeton('sup', v))
            continue
        if c in INDICES:
            v = ''
            while i < len(car) and car[i] in INDICES:
                v += INDICES[car[i]]
                i += 1
            pousser(Jeton('sub', v))
            continue
        if c in '☉⊕' and out and out[-1].k == 'id':
            pousser(Jeton('sub', c))                    # R☉, M⊕ : le symbole est un indice
            i += 1
            continue
        if c in '^_':
            i += 1
            v = ''
            if i < len(car) and car[i] == '(':
                n = 0
                while i < len(car):
                    d = car[i]
                    i += 1
                    if d == '(':
                        n += 1
                    elif d == ')':
                        n -= 1
                        if n == 0:
                            break
                    if not (d == '(' and n == 1):
                        v += d
            elif c == '_' and i + 1 < len(car) and re.match(r'[A-Za-zα-ωΑ-Ω]', car[i]) and \
                    re.match(r'[A-Za-zα-ωΑ-Ω]', car[i + 1]):
                # indice d'un mot entier (λ_max, f_obs, a_int) : un seul identificateur, en romain
                while i < len(car) and re.match(r'[A-Za-zα-ωΑ-Ω]', car[i]):
                    v += car[i]
                    i += 1
            else:
                v = car[i] if i < len(car) else ''
                i += 1
            pousser(Jeton('sup' if c == '^' else 'sub', v))
            continue
        if c in '([' or (c == '|' and not any(j.k == 'ouv' and j.v == '|' for j in out)):
            pousser(Jeton('ouv', c))
            i += 1
            continue
        if c in ')]|':
            pousser(Jeton('ferm', c))
            i += 1
            continue
        if c == '√':
            pousser(Jeton('racine', c))
            i += 1
            continue
        if _LETTRE.match(c):
            reste = ''.join(car[i:])
            mot = next((m for m in MOTS if reste.startswith(m) and not re.match(r'[A-Za-z]', reste[len(m):len(m) + 1])),
                       None)
            if mot:
                pousser(Jeton('id', mot))
                i += len(mot)
            else:
                pousser(Jeton('id', c))
                i += 1
            continue
        pousser(Jeton('op', '−' if c == '-' else '×' if c == '*' else c))
        i += 1
    return out


# Nœuds : tuples ('rangee', [..]), ('id', v), ('nb', v), ('op', v), ('frac', n, d), ('sup', b, s), ('sub', b, s),
# ('subsup', b, i, s), ('racine', e), ('paren', e, o, f)
def _sans_paren(n):
    return n[1] if n[0] == 'paren' and n[2] == '(' else n


def _sous_formule(s: str):
    if re.fullmatch(r'[−+]?[0-9]+', s):
        return ('nb', s)
    if len(s) == 1 and not s.isdigit():
        return ('op', '∗') if s == '*' else ('id', s)
    # un mot (max, obs, int…) : un identificateur droit, pas un produit de lettres en italique
    if re.fullmatch(r'[A-Za-zα-ωΑ-Ω]{2,}', s):
        return ('id', s)
    return analyser(s)


class _Analyseur:
    def __init__(self, j):
        self.j, self.i = j, 0

    def voir(self, k=0):
        return self.j[self.i + k] if self.i + k < len(self.j) else None

    def analyser(self):
        n = self.relation()
        reste = [n]
        while self.i < len(self.j):
            t = self.j[self.i]
            self.i += 1
            reste.append((t.k if t.k in ('nb', 'id') else 'op', t.v))
        return n if len(reste) == 1 else ('rangee', reste)

    def _op(self, ensemble):
        t = self.voir()
        return t is not None and t.k == 'op' and t.v in ensemble

    def relation(self):
        e = []
        if self._op(RELATIONS):
            e.append(('op', self.j[self.i].v))
            self.i += 1
        e.append(self.somme())
        while self._op(RELATIONS):
            e.append(('op', self.j[self.i].v))
            self.i += 1
            if self.debut_facteur() or (self.voir() is not None and self.voir().k == 'op'):
                e.append(self.somme())
        return e[0] if len(e) == 1 else ('rangee', e)

    def somme(self):
        e = []
        while self._op('−+±∓'):
            e.append(('op', self.j[self.i].v))
            self.i += 1
        e.append(self.quotient())
        while self._op('−+±∓'):
            e.append(('op', self.j[self.i].v))
            self.i += 1
            if self.debut_facteur():
                e.append(self.quotient())
        return e[0] if len(e) == 1 else ('rangee', e)

    def quotient(self):
        n = self.produit()
        while self._op('/'):
            self.i += 1
            if not self.debut_facteur():
                break
            d = self.produit()
            n = ('frac', _sans_paren(n), _sans_paren(d))
        return n

    def debut_facteur(self):
        t = self.voir()
        return t is not None and (t.k in ('nb', 'id', 'ouv', 'racine') or (t.k == 'op' and t.v in 'ΔΣ∂∇'))

    def _debut_facteur_a(self, k):
        t = self.j[k] if k < len(self.j) else None
        return t is not None and t.k in ('nb', 'id', 'ouv', 'racine')

    def _colle_a(self, k):
        t = self.j[k] if k < len(self.j) else None
        return t is not None and not t.esp

    def produit(self):
        colle = [self._colle_a(self.i)]
        e = [self.facteur()]
        while True:
            t = self.voir()
            if (t is not None and t.k == 'op' and t.v == '/' and not t.esp and self._colle_a(self.i + 1)
                    and self._debut_facteur_a(self.i + 1)):
                # « a/b » collé : le groupe collé de gauche sur le groupe collé de droite
                self.i += 1
                k = len(e) - 1
                while k > 0 and colle[k]:
                    k -= 1
                num = e[k:]
                del e[k:]
                prem = colle[k] if k < len(colle) else False
                del colle[k:]
                den = [self.facteur()]
                while self.debut_facteur() and self._colle_a(self.i):
                    den.append(self.facteur())
                e.append(('frac', _sans_paren(num[0] if len(num) == 1 else ('rangee', num)),
                          _sans_paren(den[0] if len(den) == 1 else ('rangee', den))))
                colle.append(prem)
            elif t is not None and t.k == 'op' and t.v in '×·⋅':
                self.i += 1
                e.append(('op', '·' if t.v == '⋅' else t.v))
                colle.append(False)
                if self.debut_facteur():
                    colle.append(False)
                    e.append(self.facteur())
            elif self.debut_facteur():
                colle.append(self._colle_a(self.i))
                e.append(self.facteur())
            else:
                break
        return e[0] if len(e) == 1 else ('rangee', e)

    def facteur(self):
        b = self.primaire()
        while True:
            t = self.voir()
            if t is not None and t.k == 'sub':
                self.i += 1
                s = _sous_formule(t.v)
                u = self.voir()
                if u is not None and u.k == 'sup':
                    self.i += 1
                    b = ('subsup', b, s, _sous_formule(u.v))
                else:
                    b = ('sub', b, s)
            elif t is not None and t.k == 'sup':
                self.i += 1
                b = ('sup', b, _sous_formule(t.v))
            else:
                break
        return b

    def primaire(self):
        t = self.voir()
        self.i += 1
        if t is None:
            return ('rangee', [])
        if t.k in ('nb', 'id'):
            return (t.k, t.v)
        if t.k == 'racine':
            return ('racine', _sans_paren(self.facteur()))
        if t.k == 'ouv':
            e = self.relation()
            f = self.voir()
            fe = {'(': ')', '[': ']'}.get(t.v, '|')
            if f is not None and f.k == 'ferm':
                self.i += 1
                fe = f.v
            return ('paren', e, t.v, fe)
        return ('op', t.v)


@functools.lru_cache(maxsize=512)
def analyser(s: str):
    """Arbre d'une formule écrite en texte simple."""
    return _Analyseur(jetons(s)).analyser()


def _est_fonction(n) -> bool:
    return (n[0] == 'id' and n[1] in MOTS) or (n[0] == 'sub' and n[1][0] == 'id' and n[1][1] in MOTS)


def _droit(v: str) -> bool:
    return len(v) > 1 or 'Α' <= v <= 'Ω' or v in SYMBOLES_DROITS


# Italique mathématique (Unicode, bloc « Mathematical Alphanumeric Symbols ») : la police STIX Two Math a les vrais
# dessins italiques des lettres, au lieu d'un oblique calculé.
def italique(c: str) -> str:
    if c == 'h':
        return 'ℎ'
    if 'A' <= c <= 'Z':
        return chr(0x1D434 + ord(c) - ord('A'))
    if 'a' <= c <= 'z':
        return chr(0x1D44E + ord(c) - ord('a'))
    if 'α' <= c <= 'ω':
        return chr(0x1D6FC + ord(c) - ord('α'))
    return {'ϑ': '\U0001D717', 'ϕ': '\U0001D719', 'ϵ': '\U0001D716'}.get(c, c)


# ==================================================================== police
POLICE_FICHIER = Path(__file__).resolve().parent / 'donnees' / 'stix-two-math.otf'
_famille = None


def famille() -> str:
    """Famille de la police mathématique embarquée (chargée une fois), ou celle de l'application à défaut."""
    global _famille
    if _famille is None:
        _famille = ''
        try:
            from PyQt6.QtGui import QFontDatabase
            i = QFontDatabase.addApplicationFont(str(POLICE_FICHIER))
            fam = QFontDatabase.applicationFontFamilies(i) if i >= 0 else []
            _famille = fam[0] if fam else ''
        except Exception:
            _famille = ''
    return _famille


def _police(taille_px: float):
    from PyQt6.QtGui import QFont
    f = QFont(famille()) if famille() else QFont()
    f.setPixelSize(max(1, int(round(taille_px))))
    f.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    return f


@functools.lru_cache(maxsize=64)
def _metriques(taille_px: int):
    from PyQt6.QtGui import QFontMetricsF
    return QFontMetricsF(_police(taille_px))


# ==================================================================== mise en page
# Une boîte : (largeur, montée, descente, primitives) ; primitives en coordonnées relatives au début de la ligne de
# base : ('t', x, y, taille_px, texte, italique_synthétique, echelle_x, echelle_y) et ('l', [(x, y), …], épaisseur).
def _mesure(s: str, t: float, ital: bool):
    tp = int(round(t))
    fm = _metriques(tp)
    synth = False
    if ital:
        it = ''.join(italique(c) for c in s)
        if famille() and all(fm.inFontUcs4(ord(c)) for c in it):
            s = it
        else:
            synth = True
    w = fm.horizontalAdvance(s) + (t * 0.06 if synth else 0)
    return (w, t * 0.72, t * 0.22, [('t', 0.0, 0.0, tp, s, synth, 1.0, 1.0)])


def _decale(prims, dx, dy):
    out = []
    for q in prims:
        if q[0] == 't':
            out.append(('t', q[1] + dx, q[2] + dy) + q[3:])
        else:
            out.append(('l', [(x + dx, y + dy) for x, y in q[1]], q[2]))
    return out


def _boite(n, t: float):
    k = n[0]
    if k == 'id':
        v = n[1]
        return _mesure('∗' if v == '*' else v, t, not _droit(v))
    if k == 'nb':
        return _mesure(n[1], t, False)
    if k == 'op':
        v = n[1]
        espace = t * 0.22 if (v in RELATIONS or v in '−+±×∓') else t * 0.06
        w, a, d, pr = _mesure(v, t, False)
        return (w + 2 * espace, a, d, _decale(pr, espace, 0))
    if k == 'rangee':
        x = 0.0
        asc, desc, prims = t * 0.72, t * 0.22, []
        e = n[1]
        for i, x_n in enumerate(e):
            w, a, d, pr = _boite(x_n, t)
            if _est_fonction(x_n):
                av = t * 0.17 if i > 0 else 0.0
                ap = t * 0.17 if i < len(e) - 1 else 0.0
                pr = _decale(pr, av, 0)
                w += av + ap
            prims += _decale(pr, x, 0)
            x += w
            asc, desc = max(asc, a), max(desc, d)
        return (x, asc, desc, prims)
    if k == 'frac':
        tn = max(9.0, t * 0.82)
        wn, an, dn, pn = _boite(n[1], tn)
        wd, ad, dd, pd = _boite(n[2], tn)
        w = max(wn, wd) + t * 0.3
        axe = t * 0.3
        ep = max(1.0, t * 0.06)
        prims = _decale(pn, (w - wn) / 2, -axe - t * 0.12 - dn) + _decale(pd, (w - wd) / 2, -axe + t * 0.12 + ad)
        prims.append(('l', [(t * 0.08, -axe), (w - t * 0.08, -axe)], ep))
        return (w, axe + an + dn + t * 0.12, -axe + ad + dd + t * 0.12, prims)
    if k in ('sup', 'sub', 'subsup'):
        wb, ab, db, pb = _boite(n[1], t)
        ts = max(8.0, t * 0.68)
        s = _boite(n[2], ts) if k == 'sup' else (_boite(n[3], ts) if k == 'subsup' else None)
        i = _boite(n[2], ts) if k in ('sub', 'subsup') else None
        w = wb + max(s[0] if s else 0.0, i[0] if i else 0.0) + t * 0.04
        prims = list(pb)
        if s:
            prims += _decale(s[3], wb + t * 0.02, -t * 0.42)
        if i:
            prims += _decale(i[3], wb + t * 0.02, t * 0.2)
        return (w, max(ab, t * 0.42 + s[1] if s else 0.0), max(db, t * 0.2 + i[2] if i else 0.0), prims)
    if k == 'racine':
        we, ae, de, pe = _boite(n[1], t)
        signe = t * 0.62
        haut = -ae - t * 0.08
        prims = _decale(pe, signe, 0)
        prims.append(('l', [(t * 0.04, -t * 0.3), (t * 0.2, -t * 0.36), (t * 0.36, de * 0.7),
                            (signe - t * 0.06, haut), (signe + we + t * 0.06, haut)], max(1.0, t * 0.06)))
        return (signe + we + t * 0.1, ae + t * 0.16, de, prims)
    if k == 'paren':
        we, ae, de, pe = _boite(n[1], t)
        wo, _, _, po = _mesure(n[2], t, False)
        wf, _, _, pf = _mesure(n[3], t, False)
        ky = max(1.0, (ae + de) / (t * 0.95))
        kx = min(1.3, ky)
        milieu = -(ae - de) / 2

        def echelle(prims, x0):
            # le glyphe de la parenthèse est agrandi autour du milieu de son contenu (parenthèses extensibles)
            out = []
            for q in prims:
                out.append(('t', x0 + q[1] * kx, milieu + t * 0.25 * ky, q[3], q[4], q[5], kx, ky))
            return out

        prims = echelle(po, 0.0) + _decale(pe, wo * kx, 0) + echelle(pf, wo * kx + we)
        return ((wo + wf) * kx + we, max(ae, t * 0.72), max(de, t * 0.22), prims)
    return (0.0, t * 0.72, t * 0.22, [])


@functools.lru_cache(maxsize=256)
def mise_en_page(s: str, taille_px: float):
    """(largeur, montée, descente, primitives) d'une formule pour une taille de corps en pixels (cache)."""
    return _boite(analyser(s), taille_px)


def taille_de(p) -> float:
    """Taille en pixels de la police courante du peintre (multipliée par 1,08 comme sur le web)."""
    f = p.font()
    if f.pixelSize() > 0:
        px = f.pixelSize()
    else:
        dev = p.device()
        dpi = dev.logicalDpiY() if dev is not None else 96
        px = f.pointSizeF() * dpi / 72.0
    return px * 1.08


def largeur(p, s: str) -> float:
    return mise_en_page(s, round(taille_de(p) * 4) / 4)[0]


def peindre(p, x: float, y: float, boite, couleur):
    """Peint une boîte mise en page, la ligne de base commençant en (x, y)."""
    from PyQt6.QtCore import QPointF, Qt
    from PyQt6.QtGui import QPen, QPolygonF
    p.save()
    for q in boite[3]:
        if q[0] == 't':
            _, qx, qy, tp, s, synth, kx, ky = q
            f = _police(tp)
            if synth:
                f.setItalic(True)
            p.setFont(f)
            p.setPen(couleur)
            if kx != 1.0 or ky != 1.0:
                p.save()
                p.translate(x + qx, y + qy)
                p.scale(kx, ky)
                p.drawText(QPointF(0, 0), s)
                p.restore()
            else:
                p.drawText(QPointF(x + qx, y + qy), s)
        else:
            pen = QPen(couleur, q[2])
            pen.setCapStyle(Qt.PenCapStyle.FlatCap if len(q[1]) == 2 else Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPolyline(QPolygonF([QPointF(x + a, y + b) for a, b in q[1]]))
    p.restore()


def dessiner(p, x: float, y: float, s: str, centre: bool = False, couleur=None):
    """Dessine une formule sur la toile dans la couleur du stylo courant (ou `couleur`) ; (x, y) : début de la ligne
    de base, ou centre de la formule si `centre`.  Rend la boîte (x, y, largeur, hauteur) occupée."""
    b = mise_en_page(s, round(taille_de(p) * 4) / 4)
    w, asc, desc = b[0], b[1], b[2]
    x0 = x - w / 2 if centre else x
    y0 = y + (asc - desc) / 2 if centre else y
    peindre(p, x0, y0, b, couleur if couleur is not None else p.pen().color())
    return (x0, y0 - asc, w, asc + desc)


# ==================================================================== textes riches (QLabel, info-bulles, aide)
# Formules reconnues dans les descriptions, les aides, les libellés et les valeurs (même liste que Coupole Web,
# src/app/texte_riche.ts), plus tout ce qui est écrit entre $…$.
FORMULES = sorted({
    'F = G M₁ M₂ / R²', 'F = G M₁ M₂ / d²', 'F = G M₁ M₂ / R', 'H = TSL − α', 'H = LST − α', 'P² = a³ / M', 'P² = a³',
    'd = 1 / p', '1/p', 'b = √(a² − c²)', 'm₁ r₁ = m₂ r₂', 'σT⁴/π', '(σT⁴)', 'σT⁴', 'σ T⁴', 'T⁴', 'v ∝ 1/√R', '1/√R',
    'c Δλ / λ₀', 'Δλ / λ = v / c', 'Δλ / λ', 'f₀ / (1 − v_r / c)', '(R_p / R_*)²', 'H = (da/dt) / a', 'da/dt', '1 / H',
    'a × b / c²', 'a b / c²', 'a = F / M', '(F / M₁)', '(F / M₂)', 'm − M = 5 log₁₀ d − 5', 'E = Δm c²', 'v² R / G',
    'F / f', '(c / λ)', '∝ 1 / sin h', '206 265″ × d / D', '206,265″ × d / D', '2 asin(d / 2D)', 'P (1 ± v/c)',
    '∝ n²', '(1 + cos i) / 2', 'λ_max = b / T', 'e = c / a', 'L = 4π R² σ T⁴', 'L / L☉ = (R / R☉)² (T / T☉)⁴',
    'R / R☉ = √(L / L☉) / (T / T☉)²', 'v = H d', 'v = √(v_r² + v_t²)', 'v_r = c Δλ / λ₀', 'F = P / 4π d²',
    'h = 90° − φ + δ', '90° − φ + δ', 'cos H₀ = −tan φ tan δ', 'E = h ν', 'ν = c / λ', '1/S = 1/E − 1/P',
    '1/S = 1/P − 1/E', '1 / S = 1 / P₁ − 1 / P₂', 'sin E = a_int / a_ext', 'P = 2π √(r³ / GM)', 'v = √(GM / r)',
    'M = v² R / G', 'n₁ sin θ₁ = n₂ sin θ₂', 'sin θ_c = n₂ / n₁', 'r₁ / r₂ = m₂ / m₁',
    'K = (2πG / P)^⅓ M_p sin i / (M_* + M_p)^⅔', 'E = 13,598 eV (1/n² − 1/m²)', 'E = 13.598 eV (1/n² − 1/m²)',
    'ζ(ψ) = (M / M⊕)(R / d)³ R (3 cos² ψ − 1) / 2', 'F = Δm c²',
}, key=lambda f: -len(f))
_MOTIF = re.compile(r'\$([^$]+)\$|(' + '|'.join(re.escape(f) for f in FORMULES) + ')')
_VALEUR_FORMULE = re.compile(r'^[\w\s₀-₉⁰-⁹⁻ⁿ½⅓⅔√()\[\],.·×−+=/∝≈<>|′″°☉⊕_*]+$')


def est_formule(s: str) -> bool:
    """Une valeur affichée qui n'est qu'une formule (relation, radical) — pas un résultat avec unité."""
    if not _VALEUR_FORMULE.match(s) or not re.search(r'[=∝√]', s):
        return False
    sans = re.sub(r'log₁₀|log|sin|cos|tan', '', s)
    if re.search(r'\d\s*(?:[A-Za-z]{2,}|[hs]\b|min\b)', sans):
        return False
    if re.search(r'[\d⁰-⁹]\s*[A-Za-z]{1,3}(?:/[A-Za-z]+)?\s*$', s):
        return False
    return not any(len(w) > 3 and w not in ('asin', 'acos', 'atan') for w in re.split(r'[\W\d_]+', s))


def morceaux(s: str) -> list:
    """Découpe un texte en morceaux : ('texte', …) et ('formule', …)."""
    out, i = [], 0
    for m in _MOTIF.finditer(s):
        if m.start() < i:
            continue
        avant = s[m.start() - 1] if m.start() > 0 else ' '
        apres = s[m.end()] if m.end() < len(s) else ' '
        if not m.group(1) and (avant.isalnum() or apres.isalnum()):
            continue                                       # une formule est un mot entier
        debut, fin = m.start(), m.end()
        f = m.group(1) or m.group(2)
        if not m.group(1) and debut > 0 and s[debut - 1] == '(' and fin < len(s) and s[fin] == ')' \
                and not f.startswith('('):
            debut, fin, f = debut - 1, fin + 1, '(%s)' % f
        if debut > i:
            out.append(('texte', s[i:debut]))
        out.append(('formule', f))
        i = fin
    if i < len(s):
        out.append(('texte', s[i:]))
    return out


@functools.lru_cache(maxsize=512)
def _image_html(s: str, taille_px: float, couleur: str, dpr: float) -> str:
    """Balise <img> (PNG en data URL, rendu à `dpr` × pour les écrans denses) d'une formule ; l'image est symétrique
    autour de l'axe mathématique pour s'aligner au milieu de la ligne (vertical-align: middle)."""
    from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, Qt
    from PyQt6.QtGui import QColor, QImage, QPainter
    b = mise_en_page(s, taille_px)
    w, asc, desc = b[0], b[1], b[2]
    axe = taille_px * 0.3
    demi = max(asc - axe, desc + axe) + 1
    W, H = int(w + 3), int(2 * demi + 1)
    img = QImage(max(1, int(W * dpr)), max(1, int(H * dpr)), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    p.scale(dpr, dpr)
    peindre(p, 1, demi + axe, b, QColor(couleur))
    p.end()
    ba = QByteArray()
    tampon = QBuffer(ba)
    tampon.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(tampon, 'PNG')
    return ('<img src="data:image/png;base64,%s" width="%d" height="%d" style="vertical-align: middle" alt="%s">'
            % (base64.b64encode(bytes(ba)).decode('ascii'), W, H, _html.escape(s, quote=True)))


def html(s: str, taille_px: float = 14.0, couleur: str = '#D9DDE2', dpr: float = 2.0) -> str:
    return _image_html(s, round(taille_px * 4) / 4, couleur, dpr)


def enrichir(texte: str, taille_px: float = 14.0, couleur: str = '#D9DDE2', valeur: bool = False) -> str:
    """HTML d'un texte (échappé) dont les formules reconnues sont mises en forme ; `valeur` : une valeur qui n'est
    qu'une formule est rendue entière."""
    if valeur and est_formule(texte):
        return html(texte, taille_px * 1.08, couleur)
    out = []
    for genre, m in morceaux(texte):
        out.append(html(m, taille_px * 1.08, couleur) if genre == 'formule' else _puissances_html(_html.escape(m)))
    return ''.join(out)


_PUISSANCE = re.compile('10([⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+)')
_EXP_VERS = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺', '0123456789−+')


def _puissances_html(s: str) -> str:
    """« × 10⁻¹¹ » → « × 10<sup>−11</sup> » : vrai exposant dans le texte riche de Qt."""
    return _PUISSANCE.sub(lambda m: '10<sup>%s</sup>' % m.group(1).translate(_EXP_VERS), s)


def contexte_widget(w) -> tuple:
    """(taille en pixels, couleur du texte, rapport de pixels) d'un widget, pour enrichir()."""
    f = w.font()
    px = f.pixelSize() if f.pixelSize() > 0 else f.pointSizeF() * w.logicalDpiY() / 72.0
    return px, w.palette().windowText().color().name(), max(1.0, float(w.devicePixelRatioF()))
