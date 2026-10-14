"""Moteur des questions de Coupole — implémentation Python de référence (aucune dépendance).

Spécification : moteur/SPEC.md.  L'implémentation TypeScript (moteur/ts/moteur_questions.ts) doit rendre
exactement la même chose pour la même graine (jeux communs : moteur/references/).

API :
    instancier(question, graine='0', parametres=None, langue='fr', hasard_parametres=False, macros=None) -> dict
    evaluer(expression, portee) / gabarit(texte, portee, langue) / formater(valeur, spec, langue)
    Alea(graine) : générateur pseudo-aléatoire mulberry32 (graine FNV-1a 32 bits)."""
from __future__ import annotations

import math
from decimal import Decimal, ROUND_HALF_UP, localcontext

VERSION_MOTEUR = '1.0.0'
MASQUE = 0xFFFFFFFF


class ErreurMoteur(Exception):
    pass


# =====================================================================================================  hasard
def fnv1a32(texte: str) -> int:
    h = 0x811C9DC5
    for o in texte.encode('utf-8'):
        h ^= o
        h = (h * 0x01000193) & MASQUE
    return h


def _imul(a: int, b: int) -> int:
    return (a * b) & MASQUE


class Alea:
    """mulberry32 : 32 bits d'état, période 2^32 ; uniforme() renvoie k / 2^32 (exact en double)."""

    def __init__(self, graine):
        self.etat = fnv1a32(str(graine)) if not isinstance(graine, int) else graine & MASQUE
        self.tirages = 0

    def uint32(self) -> int:
        self.etat = (self.etat + 0x6D2B79F5) & MASQUE
        t = self.etat
        t = _imul(t ^ (t >> 15), t | 1)
        t = (t ^ ((t + _imul(t ^ (t >> 7), t | 61)) & MASQUE)) & MASQUE
        self.tirages += 1
        return (t ^ (t >> 14)) & MASQUE

    def uniforme(self) -> float:
        return self.uint32() / 4294967296

    def entier(self, a: int, b: int) -> int:
        return a + math.floor(self.uniforme() * (b - a + 1))

    def permutation(self, n: int) -> list:
        p = list(range(n))
        for i in range(n - 1, 0, -1):
            j = math.floor(self.uniforme() * (i + 1))
            p[i], p[j] = p[j], p[i]
        return p


# =====================================================================================================  nombres
MOINS = '−'
ESPACE_FINE = ' '
EXPOSANTS = str.maketrans('0123456789-+', '⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺')


def _est_nombre(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _fixe_abs(x: float, n: int) -> str:
    """|x| arrondi à n décimales, demi vers le haut, sur la valeur binaire EXACTE (= Number.toFixed)."""
    d = Decimal(abs(x)).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP)
    s = format(d, 'f')
    return s


def _mantisse_exposant(x: float, chiffres: int):
    """(chiffres significatifs, exposant décimal) de |x| arrondi à `chiffres` chiffres significatifs (= toPrecision)."""
    if x == 0:
        return '0' * chiffres, 0
    with localcontext() as ctx:
        ctx.prec = chiffres
        ctx.rounding = ROUND_HALF_UP
        d = +Decimal(abs(x))
    signe, dig, exp = d.as_tuple()
    dig = ''.join(map(str, dig))
    dig = (dig + '0' * chiffres)[:chiffres]
    e10 = exp + len(d.as_tuple().digits) - 1
    return dig, e10


def _grouper(entier: str, langue: str, seuil: int) -> str:
    if len(entier) < seuil:
        return entier
    sep = ESPACE_FINE if langue == 'fr' else ','
    morceaux = []
    while len(entier) > 3:
        morceaux.insert(0, entier[-3:])
        entier = entier[:-3]
    morceaux.insert(0, entier)
    return sep.join(morceaux)


def _assembler(signe_neg: bool, abs_txt: str, langue: str, seuil: int, plus: bool) -> str:
    if '.' in abs_txt:
        ent, dec = abs_txt.split('.')
    else:
        ent, dec = abs_txt, ''
    ent = _grouper(ent, langue, seuil)
    s = ent + (((',' if langue == 'fr' else '.') + dec) if dec else '')
    nul = all(c in '0' for c in abs_txt.replace('.', ''))
    if signe_neg and not nul:
        return MOINS + s
    if plus and not nul:
        return '+' + s
    return s


def _entier_exact(x: float) -> str:
    return str(int(x))


def nombre_js(x: float) -> str:
    """Écriture canonique d'un nombre, identique à String(x) en JavaScript (sérialisation commune)."""
    if x != x:
        return 'NaN'
    if x in (math.inf, -math.inf):
        return 'Infinity' if x > 0 else '-Infinity'
    if x == 0:
        return '0'
    r = repr(float(x))
    neg = r.startswith('-')
    if neg:
        r = r[1:]
    if 'e' in r:
        m, e = r.split('e')
        e = int(e)
    else:
        m, e = r, 0
    if '.' in m:
        a, b = m.split('.')
    else:
        a, b = m, ''
    if b == '0':
        b = ''
    chiffres = (a + b).lstrip('0')
    # position de la virgule : exposant décimal du premier chiffre significatif
    if a.strip('0'):
        e10 = len(a.lstrip('0')) - 1 + e
    else:
        e10 = -(len(b) - len(b.lstrip('0'))) - 1 + e
    chiffres = chiffres.rstrip('0') or '0'
    k = len(chiffres)
    n = e10 + 1
    if k <= n <= 21:
        s = chiffres + '0' * (n - k)
    elif 0 < n <= 21:
        s = chiffres[:n] + '.' + chiffres[n:]
    elif -6 < n <= 0:
        s = '0.' + '0' * (-n) + chiffres
    else:
        ex = n - 1
        s = chiffres[0] + ('.' + chiffres[1:] if k > 1 else '') + 'e' + ('+' if ex >= 0 else '-') + str(abs(ex))
    return ('-' if neg else '') + s


def arrondi(x: float, n: int = 0) -> float:
    """Arrondi à n décimales, demi loin de zéro, décidé sur la valeur binaire exacte."""
    if not math.isfinite(x):
        return x
    s = _fixe_abs(x, n) if n >= 0 else None
    if n < 0:
        p = 10 ** (-n)
        return float(math.copysign(float(_fixe_abs(x / p, 0)) * p, x))
    v = float(s)
    return -v if x < 0 else v


def arrondi_sig(x: float, n: int) -> float:
    if x == 0 or not math.isfinite(x):
        return x
    dig, e10 = _mantisse_exposant(x, n)
    v = float(dig[0] + '.' + dig[1:] + 'e' + str(e10)) if len(dig) > 1 else float(dig + 'e' + str(e10))
    return -v if x < 0 else v


def formater(v, spec: str = '', langue: str = 'fr') -> str:
    """Rendu d'une valeur dans un gabarit.  spec : '' (auto), fN, gN, sN, eN, i, n, avec '+' en tête possible."""
    if isinstance(v, dict) and set(v) >= {'fr', 'en'}:
        return str(v[langue])
    if isinstance(v, bool):
        return ('vrai' if v else 'faux') if langue == 'fr' else ('true' if v else 'false')
    if isinstance(v, str):
        return v
    if v is None:
        return ''
    if isinstance(v, list):
        return (', ').join(formater(e, spec, langue) for e in v)
    if not _est_nombre(v):
        raise ErreurMoteur(f'valeur non formatable : {v!r}')
    x = float(v)
    if not math.isfinite(x):
        raise ErreurMoteur('nombre non fini dans un gabarit')
    plus = spec.startswith('+')
    if plus:
        spec = spec[1:]
    neg = x < 0 or (x == 0 and math.copysign(1, x) < 0)
    if spec == '':
        if x == math.floor(x) and abs(x) < 1e15:
            return _assembler(neg, _entier_exact(abs(x)), langue, 5, plus)
        dig, e10 = _mantisse_exposant(x, 12)
        if e10 < -6 or e10 >= 15:
            spec = 'e' + str(len(dig.rstrip('0') or '0') - 1)
        else:
            dec = max(0, 11 - e10)
            t = _fixe_abs(x, dec)
            if '.' in t:
                t = t.rstrip('0').rstrip('.')
            return _assembler(neg, t, langue, 5, plus)
    t, a = spec[0], spec[1:]
    if t in 'fg':
        n = int(a or 0)
        return _assembler(neg, _fixe_abs(x, n), langue, 4 if t == 'g' else 5, plus)
    if t == 'i':
        return _assembler(neg, _fixe_abs(x, 0), langue, 5, plus)
    if t == 'n':
        return _assembler(neg, _fixe_abs(x, 0), langue, 10 ** 9, plus)
    if t == 's':
        n = int(a or 3)
        dig, e10 = _mantisse_exposant(x, n)
        if e10 >= n - 1:
            txt = dig + '0' * (e10 - n + 1)
        elif e10 >= 0:
            txt = dig[:e10 + 1] + '.' + dig[e10 + 1:]
        else:
            txt = '0.' + '0' * (-e10 - 1) + dig
        return _assembler(neg, txt, langue, 5, plus)
    if t == 'e':
        n = int(a or 2)
        dig, e10 = _mantisse_exposant(x, n + 1)
        m = dig[0] + ('.' + dig[1:] if n > 0 else '')
        m = _assembler(neg, m, langue, 10 ** 9, plus)
        if x == 0:
            return m
        return m + ' × 10' + str(e10).translate(EXPOSANTS)
    raise ErreurMoteur(f'format inconnu : {spec!r}')


# =====================================================================================================  expressions
MOTS_CLES = {'et': '&&', 'ou': '||', 'non': '!'}


def _jetons(s: str) -> list:
    out = []
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or (c == '.' and i + 1 < n and s[i + 1].isdigit()):
            j = i
            while j < n and (s[j].isdigit() or s[j] == '.'):
                j += 1
            if j < n and s[j] in 'eE' and j + 1 < n and (s[j + 1].isdigit() or (s[j + 1] in '+-' and j + 2 < n and s[j + 2].isdigit())):
                j += 2
                while j < n and s[j].isdigit():
                    j += 1
            try:
                out.append(('nb', float(s[i:j])))
            except ValueError:
                raise ErreurMoteur(f'nombre invalide dans {s!r}')
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < n and (s[j].isalnum() or s[j] == '_'):
                j += 1
            mot = s[i:j]
            if mot in MOTS_CLES:
                out.append(('op', MOTS_CLES[mot]))
            else:
                out.append(('id', mot))
            i = j
            continue
        if c in '\'"':
            j = i + 1
            buf = []
            while j < n and s[j] != c:
                if s[j] == '\\' and j + 1 < n:
                    j += 1
                buf.append(s[j])
                j += 1
            if j >= n:
                raise ErreurMoteur(f'chaîne non fermée : {s!r}')
            out.append(('ch', ''.join(buf)))
            i = j + 1
            continue
        deux = s[i:i + 2]
        if deux in ('==', '!=', '<=', '>=', '&&', '||'):
            out.append(('op', deux))
            i += 2
            continue
        if c in '+-*/%^<>!()[],.':
            out.append(('op', c))
            i += 1
            continue
        raise ErreurMoteur(f'caractère inattendu {c!r} dans {s!r}')
    out.append(('fin', None))
    return out


class _Analyseur:
    def __init__(self, s):
        self.s = s
        self.j = _jetons(s)
        self.k = 0

    def voir(self):
        return self.j[self.k]

    def prendre(self, op=None):
        t = self.j[self.k]
        if op is not None and not (t[0] == 'op' and t[1] == op):
            raise ErreurMoteur(f'« {op} » attendu dans {self.s!r}')
        self.k += 1
        return t

    def est(self, *ops):
        t = self.voir()
        return t[0] == 'op' and t[1] in ops

    def tout(self):
        e = self.ou()
        if self.voir()[0] != 'fin':
            raise ErreurMoteur(f'fin attendue dans {self.s!r}')
        return e

    def ou(self):
        e = self.et()
        while self.est('||'):
            self.prendre()
            e = ('ou', e, self.et())
        return e

    def et(self):
        e = self.non()
        while self.est('&&'):
            self.prendre()
            e = ('et', e, self.non())
        return e

    def non(self):
        if self.est('!'):
            self.prendre()
            return ('non', self.non())
        return self.comp()

    def comp(self):
        e = self.somme()
        if self.est('==', '!=', '<', '<=', '>', '>='):
            op = self.prendre()[1]
            e = ('cmp', op, e, self.somme())
        return e

    def somme(self):
        e = self.produit()
        while self.est('+', '-'):
            op = self.prendre()[1]
            e = ('bin', op, e, self.produit())
        return e

    def produit(self):
        e = self.unaire()
        while self.est('*', '/', '%'):
            op = self.prendre()[1]
            e = ('bin', op, e, self.unaire())
        return e

    def unaire(self):
        if self.est('-'):
            self.prendre()
            return ('neg', self.unaire())
        if self.est('+'):
            self.prendre()
            return self.unaire()
        return self.puiss()

    def puiss(self):
        e = self.postfixe()
        if self.est('^'):
            self.prendre()
            e = ('bin', '^', e, self.unaire())
        return e

    def postfixe(self):
        e = self.primaire()
        while True:
            if self.est('.'):
                self.prendre()
                t = self.prendre()
                if t[0] != 'id':
                    raise ErreurMoteur(f'nom attendu après « . » dans {self.s!r}')
                e = ('champ', e, t[1])
            elif self.est('['):
                self.prendre()
                i = self.ou()
                self.prendre(']')
                e = ('index', e, i)
            elif self.est('(') and e[0] == 'nom':
                self.prendre()
                args = []
                if not self.est(')'):
                    args.append(self.ou())
                    while self.est(','):
                        self.prendre()
                        args.append(self.ou())
                self.prendre(')')
                e = ('appel', e[1], args)
            else:
                return e

    def primaire(self):
        t = self.prendre()
        if t[0] == 'nb':
            return ('lit', t[1])
        if t[0] == 'ch':
            return ('lit', t[1])
        if t[0] == 'id':
            if t[1] in ('vrai', 'true'):
                return ('lit', True)
            if t[1] in ('faux', 'false'):
                return ('lit', False)
            if t[1] in ('nul', 'null'):
                return ('lit', None)
            return ('nom', t[1])
        if t == ('op', '('):
            e = self.ou()
            self.prendre(')')
            return e
        if t == ('op', '['):
            elts = []
            if not self.est(']'):
                elts.append(self.ou())
                while self.est(','):
                    self.prendre()
                    elts.append(self.ou())
            self.prendre(']')
            return ('liste', elts)
        raise ErreurMoteur(f'expression invalide : {self.s!r}')


_CACHE_AST: dict = {}


def analyser(s: str):
    a = _CACHE_AST.get(s)
    if a is None:
        a = _Analyseur(s).tout()
        _CACHE_AST[s] = a
    return a


def _num(v, quoi='nombre'):
    if not _est_nombre(v):
        raise ErreurMoteur(f'{quoi} attendu, reçu {v!r}')
    return float(v)


def egal(a, b) -> bool:
    if _est_nombre(a) and _est_nombre(b):
        return float(a) == float(b)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(egal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(egal(a[k], b[k]) for k in a)
    if type(a) != type(b) and not (_est_nombre(a) and _est_nombre(b)):
        return False
    return a == b


def _vrai(v) -> bool:
    if isinstance(v, bool):
        return v
    raise ErreurMoteur(f'booléen attendu, reçu {v!r}')


def _bilingue(v) -> bool:
    return isinstance(v, dict) and set(v) == {'fr', 'en'}


def _joindre(liste, sep):
    if any(_bilingue(e) for e in liste) or _bilingue(sep):
        return {lg: (sep[lg] if _bilingue(sep) else sep).join(e[lg] if _bilingue(e) else _texte_brut(e) for e in liste)
                for lg in ('fr', 'en')}
    return sep.join(_texte_brut(e) for e in liste)


def _texte_brut(e):
    if isinstance(e, str):
        return e
    raise ErreurMoteur(f'texte attendu, reçu {e!r}')


def _cbrt(x):
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


def _f1(f):
    return lambda a: f(_num(a))


FONCTIONS = {
    'abs': _f1(abs), 'sqrt': _f1(math.sqrt), 'cbrt': _f1(_cbrt), 'exp': _f1(math.exp), 'ln': _f1(math.log),
    'log10': _f1(math.log10), 'log2': _f1(math.log2), 'floor': lambda a: float(math.floor(_num(a))),
    'ceil': lambda a: float(math.ceil(_num(a))), 'trunc': lambda a: float(math.trunc(_num(a))),
    'sign': lambda a: (1.0 if _num(a) > 0 else (-1.0 if _num(a) < 0 else 0.0)),
    'sin': _f1(math.sin), 'cos': _f1(math.cos), 'tan': _f1(math.tan), 'asin': _f1(math.asin), 'acos': _f1(math.acos),
    'atan': _f1(math.atan), 'atan2': lambda y, x: math.atan2(_num(y), _num(x)),
    'sind': lambda a: math.sin(_num(a) * math.pi / 180), 'cosd': lambda a: math.cos(_num(a) * math.pi / 180),
    'tand': lambda a: math.tan(_num(a) * math.pi / 180), 'asind': lambda a: math.asin(_num(a)) * 180 / math.pi,
    'acosd': lambda a: math.acos(_num(a)) * 180 / math.pi, 'atand': lambda a: math.atan(_num(a)) * 180 / math.pi,
    'atan2d': lambda y, x: math.atan2(_num(y), _num(x)) * 180 / math.pi,
    'rad': lambda a: _num(a) * math.pi / 180, 'deg': lambda a: _num(a) * 180 / math.pi,
    'hypot': lambda a, b: math.sqrt(_num(a) * _num(a) + _num(b) * _num(b)),
    'pow': lambda a, b: _puissance(_num(a), _num(b)),
    'mod': lambda a, b: _num(a) - _num(b) * math.floor(_num(a) / _num(b)),
    'clamp': lambda x, a, b: min(max(_num(x), _num(a)), _num(b)),
    'round': lambda a, n=0.0: arrondi(_num(a), int(_num(n))),
    'roundsig': lambda a, n: arrondi_sig(_num(a), int(_num(n))),
    'min': lambda *a: min(_num(x) for x in (a[0] if len(a) == 1 and isinstance(a[0], list) else a)),
    'max': lambda *a: max(_num(x) for x in (a[0] if len(a) == 1 and isinstance(a[0], list) else a)),
    'len': lambda l: float(len(l)),
    'somme': lambda l: _somme(l),
    'prendre': lambda l, idx: [l[_index(i, len(l))] for i in idx],
    'joindre': lambda l, sep=', ': _joindre(l, sep),
    'inverse': lambda l: list(reversed(l)),
    'trier': lambda l: sorted(l, key=lambda x: _num(x)),
    'indice': lambda l, v: float(next((k for k, x in enumerate(l) if egal(x, v)), -1)),
    'contient': lambda l, v: any(egal(x, v) for x in l),
    'distincts': lambda *a: _distincts(a[0] if len(a) == 1 and isinstance(a[0], list) else list(a)),
    'plage': lambda n: [float(k) for k in range(int(_num(n)))],
    'concat': lambda *a: [x for l in a for x in l],
    'texte': lambda v, spec='', langue=None: _texte_fn(v, spec),
}


def _puissance(x, y):
    try:
        r = x ** y
    except (OverflowError, ZeroDivisionError):
        raise ErreurMoteur('puissance invalide')
    if isinstance(r, complex) or r != r:
        raise ErreurMoteur('puissance invalide')
    return float(r)


def _flottants(v):
    """Tous les nombres des données en double (comme en JavaScript) : aucun entier exact de taille arbitraire."""
    if isinstance(v, bool) or v is None or isinstance(v, str):
        return v
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, list):
        return [_flottants(x) for x in v]
    if isinstance(v, dict):
        return {k: _flottants(x) for k, x in v.items()}
    return v


def _somme(l):
    s = 0.0
    for x in l:
        s += _num(x)
    return s


def _distincts(l):
    for i in range(len(l)):
        for j in range(i + 1, len(l)):
            if egal(l[i], l[j]):
                return False
    return True


def _texte_fn(v, spec):
    return {'fr': formater(v, spec, 'fr'), 'en': formater(v, spec, 'en')}


def _index(i, n):
    k = _num(i, 'indice')
    if k != math.floor(k) or k < 0 or k >= n:
        raise ErreurMoteur(f'indice hors limites : {i!r} (taille {n})')
    return int(k)


class Portee:
    """Portée chaînée : noms -> valeurs."""

    def __init__(self, valeurs=None, parent=None):
        self.v = dict(valeurs or {})
        self.parent = parent

    def cherche(self, nom):
        p = self
        while p is not None:
            if nom in p.v:
                return p.v[nom]
            p = p.parent
        if nom == 'pi':
            return math.pi
        raise ErreurMoteur(f'nom inconnu : {nom}')

    def enfant(self, valeurs=None):
        return Portee(valeurs, self)


def _eval(a, portee: Portee):
    k = a[0]
    if k == 'lit':
        return a[1]
    if k == 'nom':
        return portee.cherche(a[1])
    if k == 'liste':
        return [_eval(e, portee) for e in a[1]]
    if k == 'neg':
        return -_num(_eval(a[1], portee))
    if k == 'non':
        return not _vrai(_eval(a[1], portee))
    if k == 'et':
        return _vrai(_eval(a[1], portee)) and _vrai(_eval(a[2], portee))
    if k == 'ou':
        return _vrai(_eval(a[1], portee)) or _vrai(_eval(a[2], portee))
    if k == 'cmp':
        op, x, y = a[1], _eval(a[2], portee), _eval(a[3], portee)
        if op == '==':
            return egal(x, y)
        if op == '!=':
            return not egal(x, y)
        if isinstance(x, str) and isinstance(y, str):
            pass
        else:
            x, y = _num(x), _num(y)
        return {'<': x < y, '<=': x <= y, '>': x > y, '>=': x >= y}[op]
    if k == 'bin':
        op = a[1]
        x, y = _eval(a[2], portee), _eval(a[3], portee)
        if op == '+' and (isinstance(x, (str, dict)) or isinstance(y, (str, dict))):
            if _bilingue(x) or _bilingue(y):
                return {lg: (x[lg] if _bilingue(x) else _texte_brut(x)) + (y[lg] if _bilingue(y) else _texte_brut(y))
                        for lg in ('fr', 'en')}
            return _texte_brut(x) + _texte_brut(y)
        x, y = _num(x), _num(y)
        if op == '+':
            return x + y
        if op == '-':
            return x - y
        if op == '*':
            return x * y
        if op == '/':
            if y == 0:
                raise ErreurMoteur('division par zéro')
            return x / y
        if op == '%':
            if y == 0:
                raise ErreurMoteur('modulo par zéro')
            return x - y * math.floor(x / y)
        if op == '^':
            return _puissance(x, y)
    if k == 'champ':
        o = _eval(a[1], portee)
        if isinstance(o, dict) and a[2] in o:
            return o[a[2]]
        raise ErreurMoteur(f'champ inconnu : {a[2]}')
    if k == 'index':
        o = _eval(a[1], portee)
        i = _eval(a[2], portee)
        if isinstance(o, list):
            return o[_index(i, len(o))]
        if isinstance(o, dict) and isinstance(i, str) and i in o:
            return o[i]
        raise ErreurMoteur('indexation invalide')
    if k == 'appel':
        nom, args = a[1], a[2]
        if nom == 'si':
            if len(args) != 3:
                raise ErreurMoteur('si(condition, alors, sinon)')
            return _eval(args[1], portee) if _vrai(_eval(args[0], portee)) else _eval(args[2], portee)
        f = FONCTIONS.get(nom)
        if f is None:
            raise ErreurMoteur(f'fonction inconnue : {nom}')
        try:
            r = f(*[_eval(x, portee) for x in args])
        except (ValueError, OverflowError, ZeroDivisionError) as e:
            raise ErreurMoteur(f'{nom} : {e}')
        except TypeError as e:
            raise ErreurMoteur(f'{nom} : arguments ({e})')
        if isinstance(r, int) and not isinstance(r, bool):
            r = float(r)
        return r
    raise ErreurMoteur(f'nœud inconnu {k}')


def evaluer(expr, portee: Portee):
    """Une expression (chaîne) ou une valeur littérale (nombre, booléen, liste, objet)."""
    if isinstance(expr, str):
        v = _eval(analyser(expr), portee)
        if isinstance(v, float) and not math.isfinite(v):
            raise ErreurMoteur(f'résultat non fini : {expr!r}')
        return v
    if isinstance(expr, bool) or expr is None:
        return expr
    if _est_nombre(expr):
        return float(expr)
    return expr


# =====================================================================================================  gabarits
def _decouper_gabarit(t: str):
    """Morceaux : ('txt', s) ou ('expr', expr, spec)."""
    out = []
    i, n = 0, len(t)
    buf = []
    while i < n:
        c = t[i]
        if c == '{' and i + 1 < n and t[i + 1] == '{':
            buf.append('{')
            i += 2
            continue
        if c == '}' and i + 1 < n and t[i + 1] == '}':
            buf.append('}')
            i += 2
            continue
        if c == '{':
            if buf:
                out.append(('txt', ''.join(buf)))
                buf = []
            j = i + 1
            prof = 0
            quote = None
            dernier_deux_points = -1
            while j < n:
                d = t[j]
                if quote:
                    if d == '\\':
                        j += 2
                        continue
                    if d == quote:
                        quote = None
                elif d in '\'"':
                    quote = d
                elif d in '([':
                    prof += 1
                elif d in ')]':
                    prof -= 1
                elif d == ':' and prof == 0:
                    dernier_deux_points = j
                elif d == '}' and prof == 0:
                    break
                j += 1
            if j >= n:
                raise ErreurMoteur(f'accolade non fermée : {t!r}')
            if dernier_deux_points >= 0:
                out.append(('expr', t[i + 1:dernier_deux_points].strip(), t[dernier_deux_points + 1:j].strip()))
            else:
                out.append(('expr', t[i + 1:j].strip(), ''))
            i = j + 1
            continue
        buf.append(c)
        i += 1
    if buf:
        out.append(('txt', ''.join(buf)))
    return out


_CACHE_GAB: dict = {}


def gabarit(t, portee: Portee, langue: str) -> str:
    """Texte à trous dans une langue.  t : chaîne (commune aux deux langues) ou {'fr':…, 'en':…}."""
    if t is None:
        return None
    if isinstance(t, dict):
        t = t[langue]
    morceaux = _CACHE_GAB.get(t)
    if morceaux is None:
        morceaux = _decouper_gabarit(t)
        _CACHE_GAB[t] = morceaux
    out = []
    for m in morceaux:
        if m[0] == 'txt':
            out.append(m[1])
        else:
            v = _eval(analyser(m[1]), portee)
            out.append(formater(v, m[2], langue))
    return ''.join(out)


# =====================================================================================================  figures
PRIMITIVES = ('ligne', 'polyligne', 'polygone', 'rect', 'cercle', 'ellipse', 'arc', 'texte', 'fleche', 'image', 'groupe',
              'carte', 'globe')
STYLE = ('trait', 'remplissage', 'couleur', 'tirets', 'ancre', 'base', 'gras', 'italique', 'police', 'choix', 'role',
         'pointe', 'secteur', 'lisse')
NUMERIQUES = {
    'ligne': ('x1', 'y1', 'x2', 'y2'), 'fleche': ('x1', 'y1', 'x2', 'y2', 'tete'), 'rect': ('x', 'y', 'l', 'h', 'rayon'),
    'cercle': ('cx', 'cy', 'r'), 'ellipse': ('cx', 'cy', 'rx', 'ry', 'rotation'),
    'arc': ('cx', 'cy', 'r', 'debut', 'fin'), 'texte': ('x', 'y', 'taille', 'rotation', 'largeur'),
    'image': ('x', 'y', 'l', 'h'), 'polyligne': (), 'polygone': (),
    'carte': ('x', 'y', 'l', 'h', 'lon_min', 'lon_max', 'lat_min', 'lat_max'), 'globe': ('cx', 'cy', 'r', 'lon0', 'lat0'),
}
NUM_COMMUNS = ('epaisseur', 'opacite')
DECIMALES_FIGURE = 3


def _r(x: float) -> float:
    if not math.isfinite(x):
        raise ErreurMoteur('coordonnée non finie')
    v = arrondi(x, DECIMALES_FIGURE)
    return 0.0 if v == 0 else v


class _Contexte:
    def __init__(self, macros, langue, avec_reponse_et_indice=True):
        self.macros = macros or {}
        self.langue = langue
        self.profondeur = 0
        self.compte = 0


def _num_expr(v, portee):
    return _num(evaluer(v, portee), 'coordonnée')


def _points(v, portee):
    if isinstance(v, str):
        pts = evaluer(v, portee)
    else:
        pts = [[evaluer(p[0], portee), evaluer(p[1], portee)] for p in v]
    return [[_num(p[0]), _num(p[1])] for p in pts]


def _styles(e, portee, ctx, out):
    for k in STYLE:
        if k in e:
            v = e[k]
            if k in ('trait', 'remplissage', 'couleur', 'choix', 'role') and isinstance(v, str) and v.startswith('='):
                v = evaluer(v[1:], portee)
            out[k] = v
    if 'tirets' in e and isinstance(e['tirets'], (list, str)):
        t = e['tirets']
        out['tirets'] = [_r(_num_expr(x, portee)) for x in (evaluer(t, portee) if isinstance(t, str) else t)]
    for k in NUM_COMMUNS:
        if k in e:
            out[k] = _r(_num_expr(e[k], portee))
    if 'afficher' in e:
        out['afficher'] = e['afficher']


class _Repere:
    def __init__(self, e, portee):
        g = lambda k, d=None: _num_expr(e[k], portee) if k in e else d
        self.x, self.y, self.l, self.h = g('x', 0.0), g('y', 0.0), g('l'), g('h')
        self.xmin, self.xmax, self.ymin, self.ymax = g('xmin'), g('xmax'), g('ymin'), g('ymax')
        self.xlog, self.ylog = bool(e.get('xlog')), bool(e.get('ylog'))
        if self.xlog and (self.xmin <= 0 or self.xmax <= 0) or self.ylog and (self.ymin <= 0 or self.ymax <= 0):
            raise ErreurMoteur('axe logarithmique : bornes positives requises')

    def _fx(self, v):
        if self.xlog:
            if v <= 0:
                raise ErreurMoteur('valeur ≤ 0 sur axe log')
            return (math.log10(v) - math.log10(self.xmin)) / (math.log10(self.xmax) - math.log10(self.xmin))
        return (v - self.xmin) / (self.xmax - self.xmin)

    def _fy(self, v):
        if self.ylog:
            if v <= 0:
                raise ErreurMoteur('valeur ≤ 0 sur axe log')
            return (math.log10(v) - math.log10(self.ymin)) / (math.log10(self.ymax) - math.log10(self.ymin))
        return (v - self.ymin) / (self.ymax - self.ymin)

    def X(self, v):
        return self.x + self._fx(v) * self.l

    def Y(self, v):
        return self.y + self.h - self._fy(v) * self.h


def _graduations(vmin, vmax, pas, log):
    if log:
        a = math.ceil(math.log10(vmin) - 1e-9)
        b = math.floor(math.log10(vmax) + 1e-9)
        return [10.0 ** k for k in range(a, b + 1)]
    if isinstance(pas, list):
        return [float(p) for p in pas]
    a = math.ceil(vmin / pas - 1e-9)
    b = math.floor(vmax / pas + 1e-9)
    return [k * pas for k in range(a, b + 1)]


def _etiquette_log(v, langue):
    k = round(math.log10(v))
    return '10' + str(k).translate(EXPOSANTS)


def _developper(elements, portee: Portee, ctx: _Contexte, rep: _Repere | None = None) -> list:
    out = []
    for e in elements:
        out.extend(_developper_un(e, portee, ctx, rep))
    return out


def _texte_figure(t, portee, ctx):
    return gabarit(t, portee, ctx.langue)


def _developper_un(e, portee: Portee, ctx: _Contexte, rep) -> list:
    ctx.compte += 1
    if ctx.compte > 200000:
        raise ErreurMoteur('figure trop grande')
    t = e.get('type')
    if 'si' in e and t != 'si':
        if not _vrai(evaluer(e['si'], portee)):
            return []
    if t == 'si':
        branche = e.get('alors', []) if _vrai(evaluer(e['condition'], portee)) else e.get('sinon', [])
        return _developper(branche, portee, ctx, rep)
    if t == 'variables':
        # définit des variables locales visibles des éléments suivants du même bloc : géré par 'bloc'
        raise ErreurMoteur('« variables » doit être placé dans un bloc')
    if t == 'bloc':
        p = portee.enfant()
        for nom, ex in e.get('variables', []):
            p.v[nom] = evaluer(ex, p)
        return _developper(e.get('elements', []), p, ctx, rep)
    if t == 'repeter':
        de, a = _num_expr(e['de'], portee), _num_expr(e['a'], portee)
        pas = _num_expr(e.get('pas', 1), portee)
        if pas <= 0:
            raise ErreurMoteur('pas ≤ 0')
        out = []
        n = math.floor((a - de) / pas + 1e-9)
        if n > 10000:
            raise ErreurMoteur('boucle trop longue')
        for k in range(n + 1):
            p = portee.enfant({e['var']: de + k * pas})
            for nom, ex in e.get('variables', []):
                p.v[nom] = evaluer(ex, p)
            out.extend(_developper(e['elements'], p, ctx, rep))
        return out
    if t == 'macro':
        m = ctx.macros.get(e['nom'])
        if m is None:
            raise ErreurMoteur(f"macro inconnue : {e['nom']}")
        ctx.profondeur += 1
        if ctx.profondeur > 20:
            raise ErreurMoteur('macros trop imbriquées')
        vals = {}
        for k, d in m.get('params', {}).items():
            vals[k] = evaluer(e['params'][k], portee) if k in e.get('params', {}) else evaluer(d, Portee())
        for k in e.get('params', {}):
            if k not in m.get('params', {}):
                raise ErreurMoteur(f"paramètre inconnu {k} pour la macro {e['nom']}")
        p = Portee(vals)
        for nom, ex in m.get('variables', []):
            p.v[nom] = evaluer(ex, p)
        corps = _developper(m['elements'], p, ctx, rep)
        ctx.profondeur -= 1
        g = {'type': 'groupe'}
        for k in ('translation', 'rotation', 'echelle'):
            if k in e:
                if k == 'translation':
                    g[k] = [_r(_num_expr(e[k][0], portee)), _r(_num_expr(e[k][1], portee))]
                else:
                    g[k] = _r(_num_expr(e[k], portee))
        _styles(e, portee, ctx, g)
        if len(g) == 1:
            return corps
        g['elements'] = corps
        return [g]
    if t == 'groupe':
        g = {'type': 'groupe'}
        if 'translation' in e:
            g['translation'] = [_r(_num_expr(e['translation'][0], portee)), _r(_num_expr(e['translation'][1], portee))]
        for k in ('rotation', 'echelle'):
            if k in e:
                g[k] = _r(_num_expr(e[k], portee))
        if 'decoupe' in e:
            g['decoupe'] = [_r(_num_expr(v, portee)) for v in e['decoupe']]
        _styles(e, portee, ctx, g)
        g['elements'] = _developper(e.get('elements', []), portee, ctx, rep)
        return [g]
    if t == 'repere':
        return _developper_repere(e, portee, ctx)
    if t == 'courbe':
        return _developper_courbe(e, portee, ctx, rep)
    if t == 'points':
        pts = _points(e['points'], portee)
        r = _num_expr(e.get('r', 3), portee)
        forme = e.get('forme', 'cercle')
        out = []
        for x, y in pts:
            X, Y = (rep.X(x), rep.Y(y)) if rep else (x, y)
            if forme == 'carre':
                o = {'type': 'rect', 'x': _r(X - r), 'y': _r(Y - r), 'l': _r(2 * r), 'h': _r(2 * r)}
            else:
                o = {'type': 'cercle', 'cx': _r(X), 'cy': _r(Y), 'r': _r(r)}
            _styles(e, portee, ctx, o)
            out.append(o)
        return out
    if t not in PRIMITIVES:
        raise ErreurMoteur(f'type de figure inconnu : {t}')
    o = {'type': t}
    for k in NUMERIQUES[t]:
        if k in e:
            o[k] = _num_expr(e[k], portee)
    if t in ('polyligne', 'polygone'):
        o['points'] = _points(e['points'], portee)
    if t == 'texte':
        o['texte'] = _texte_figure(e['texte'], portee, ctx)
    if t == 'image':
        o['ref'] = gabarit(e['ref'], portee, ctx.langue)
    if rep is not None:
        _vers_repere(o, rep)
    for k in list(o):
        if isinstance(o[k], float):
            o[k] = _r(o[k])
    if 'points' in o:
        o['points'] = [[_r(x), _r(y)] for x, y in o['points']]
    _styles(e, portee, ctx, o)
    return [o]


def _vers_repere(o, rep: _Repere):
    t = o['type']
    if t in ('ligne', 'fleche'):
        o['x1'], o['y1'], o['x2'], o['y2'] = rep.X(o['x1']), rep.Y(o['y1']), rep.X(o['x2']), rep.Y(o['y2'])
    elif t in ('polyligne', 'polygone'):
        o['points'] = [[rep.X(x), rep.Y(y)] for x, y in o['points']]
    elif t in ('cercle', 'ellipse', 'arc'):
        o['cx'], o['cy'] = rep.X(o['cx']), rep.Y(o['cy'])
    elif t in ('texte', 'image'):
        o['x'], o['y'] = rep.X(o['x']), rep.Y(o['y'])
    elif t == 'rect':
        x1, y1 = rep.X(o['x']), rep.Y(o['y'])
        x2, y2 = rep.X(o['x'] + o['l']), rep.Y(o['y'] + o['h'])
        o['x'], o['y'], o['l'], o['h'] = min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)


def _developper_courbe(e, portee, ctx, rep):
    n = int(_num_expr(e.get('n', 100), portee))
    if n < 1 or n > 5000:
        raise ErreurMoteur('courbe : n hors limites')
    segments = [[]]
    if 'fonction' in e:
        de, a = _num_expr(e['de'], portee), _num_expr(e['a'], portee)
        var = e.get('var', 'x')
        ast = analyser(e['fonction'])
        garde = analyser(e['garde']) if 'garde' in e else None
        for k in range(n + 1):
            x = de + (a - de) * k / n
            try:
                pp = portee.enfant({var: x})
                y = _num(_eval(ast, pp))
                ok = math.isfinite(y) and (garde is None or _vrai(_eval(garde, pp)))
            except ErreurMoteur:
                ok = False
            if ok and rep is not None and rep.ylog and y <= 0:
                ok = False
            if ok:
                segments[-1].append([x, y])
            elif segments[-1]:
                segments.append([])
    else:
        de, a = _num_expr(e['t_de'], portee), _num_expr(e['t_a'], portee)
        ax, ay = analyser(e['x']), analyser(e['y'])
        garde = analyser(e['garde']) if 'garde' in e else None
        for k in range(n + 1):
            tt = de + (a - de) * k / n
            p = portee.enfant({'t': tt})
            try:
                x, y = _num(_eval(ax, p)), _num(_eval(ay, p))
                ok = math.isfinite(x) and math.isfinite(y) and (garde is None or _vrai(_eval(garde, p)))
            except ErreurMoteur:
                ok = False
            if ok:
                segments[-1].append([x, y])
            elif segments[-1]:
                segments.append([])
    out = []
    for s in segments:
        if len(s) < 2:
            continue
        if rep is not None:
            s = [[rep.X(x), rep.Y(y)] for x, y in s]
        o = {'type': 'polygone' if e.get('ferme') else 'polyligne', 'points': [[_r(x), _r(y)] for x, y in s]}
        _styles(e, portee, ctx, o)
        out.append(o)
    return out


def _developper_repere(e, portee, ctx):
    rep = _Repere(e, portee)
    out = []
    trait = e.get('couleur_axes', 'trait')
    taille = _num_expr(e.get('taille_texte', 11), portee)
    interieur = {'type': 'groupe', 'decoupe': [_r(rep.x), _r(rep.y), _r(rep.l), _r(rep.h)],
                 'elements': _developper(e.get('elements', []), portee, ctx, rep)}
    # grille
    for axe in ('x', 'y'):
        pas = e.get('graduations_' + axe)
        if pas is None:
            continue
        pas_v = pas if isinstance(pas, list) else _num_expr(pas, portee)
        log = rep.xlog if axe == 'x' else rep.ylog
        vmin, vmax = (rep.xmin, rep.xmax) if axe == 'x' else (rep.ymin, rep.ymax)
        if not log and not isinstance(pas_v, list) and pas_v <= 0:
            raise ErreurMoteur('graduation ≤ 0')
        vals = _graduations(min(vmin, vmax), max(vmin, vmax), pas_v, log)
        if len(vals) > 200:
            raise ErreurMoteur('trop de graduations')
        spec = e.get('format_' + axe, '')
        etiq = e.get('etiquettes_' + axe, True)
        for v in vals:
            if axe == 'x':
                X = rep.X(v)
                if e.get('grille'):
                    out.append({'type': 'ligne', 'x1': _r(X), 'y1': _r(rep.y), 'x2': _r(X), 'y2': _r(rep.y + rep.h),
                                'trait': 'grille', 'epaisseur': 0.5})
                out.append({'type': 'ligne', 'x1': _r(X), 'y1': _r(rep.y + rep.h), 'x2': _r(X), 'y2': _r(rep.y + rep.h + 4),
                            'trait': trait, 'epaisseur': 1.0})
                if etiq:
                    txt = _etiquette_log(v, ctx.langue) if log else formater(v, spec, ctx.langue)
                    out.append({'type': 'texte', 'x': _r(X), 'y': _r(rep.y + rep.h + 6), 'texte': txt, 'taille': _r(taille),
                                'ancre': 'milieu', 'base': 'haut', 'couleur': trait})
            else:
                Y = rep.Y(v)
                if e.get('grille'):
                    out.append({'type': 'ligne', 'x1': _r(rep.x), 'y1': _r(Y), 'x2': _r(rep.x + rep.l), 'y2': _r(Y),
                                'trait': 'grille', 'epaisseur': 0.5})
                out.append({'type': 'ligne', 'x1': _r(rep.x - 4), 'y1': _r(Y), 'x2': _r(rep.x), 'y2': _r(Y),
                            'trait': trait, 'epaisseur': 1.0})
                if etiq:
                    txt = _etiquette_log(v, ctx.langue) if log else formater(v, spec, ctx.langue)
                    out.append({'type': 'texte', 'x': _r(rep.x - 6), 'y': _r(Y), 'texte': txt, 'taille': _r(taille),
                                'ancre': 'fin', 'base': 'milieu', 'couleur': trait})
    out.append(interieur)
    if e.get('cadre', True):
        out.append({'type': 'rect', 'x': _r(rep.x), 'y': _r(rep.y), 'l': _r(rep.l), 'h': _r(rep.h), 'trait': trait,
                    'epaisseur': 1.5})
    else:
        out.append({'type': 'polyligne', 'points': [[_r(rep.x), _r(rep.y)], [_r(rep.x), _r(rep.y + rep.h)],
                                                    [_r(rep.x + rep.l), _r(rep.y + rep.h)]], 'trait': trait, 'epaisseur': 1.5})
    if 'titre_x' in e:
        out.append({'type': 'texte', 'x': _r(rep.x + rep.l / 2), 'y': _r(rep.y + rep.h + (24 if e.get('graduations_x') is not None and e.get('etiquettes_x', True) else 8)),
                    'texte': _texte_figure(e['titre_x'], portee, ctx), 'taille': _r(taille + 1), 'ancre': 'milieu',
                    'base': 'haut', 'couleur': trait})
    if 'titre_y' in e:
        dx = _num_expr(e.get('marge_titre_y', 34 if e.get('graduations_y') is not None and e.get('etiquettes_y', True) else 10), portee)
        out.append({'type': 'texte', 'x': _r(rep.x - dx), 'y': _r(rep.y + rep.h / 2),
                    'texte': _texte_figure(e['titre_y'], portee, ctx), 'taille': _r(taille + 1), 'ancre': 'milieu',
                    'base': 'bas', 'rotation': 90.0, 'couleur': trait})
    return out


def developper_figure(fig, portee: Portee, langue: str, macros=None):
    if fig is None:
        return None
    ctx = _Contexte(macros, langue)
    p = portee.enfant()
    for nom, ex in fig.get('variables', []):
        p.v[nom] = evaluer(ex, p)
    if 'si' in fig and not _vrai(evaluer(fig['si'], p)):
        return None
    out = {'vue': [_r(_num_expr(fig['vue'][0], p)), _r(_num_expr(fig['vue'][1], p))],
           'elements': _developper(fig.get('elements', []), p, ctx)}
    if 'fond' in fig:
        out['fond'] = fig['fond']
    if 'alt' in fig:
        out['alt'] = gabarit(fig['alt'], p, langue)
    return out


# =====================================================================================================  instances
LETTRES = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def _valeurs_option(param, opt, rang):
    v = _flottants(dict(opt.get('valeurs', {})))
    v['id'] = opt['id']
    v['rang'] = float(rang)
    v['libelle'] = opt['libelle']
    return v


def _choisir_parametres(q, portee, demandes, alea, hasard):
    choisis = {}
    for prm in q.get('parametres', []):
        dispo = []
        for k, o in enumerate(prm['options']):
            if 'si' in o and not _vrai(evaluer(o['si'], portee)):
                continue
            dispo.append((k, o))
        if not dispo:
            raise ErreurMoteur(f"aucune option disponible pour {prm['id']}")
        if hasard:
            k, o = dispo[math.floor(alea.uniforme() * len(dispo))]
        else:
            voulu = (demandes or {}).get(prm['id'], prm.get('defaut'))
            k, o = next(((k, o) for k, o in dispo if o['id'] == voulu), dispo[0])
        choisis[prm['id']] = o['id']
        portee.v[prm['id']] = _valeurs_option(prm, o, k)
    return choisis


def _tirer(t, portee, alea):
    ty = t['type']
    if ty == 'entier':
        return float(alea.entier(int(_num(evaluer(t['min'], portee))), int(_num(evaluer(t['max'], portee)))))
    if ty == 'reel':
        a, b = _num(evaluer(t['min'], portee)), _num(evaluer(t['max'], portee))
        if 'pas' in t:
            pas = _num(evaluer(t['pas'], portee))
            n = math.floor((b - a) / pas + 0.5)
            return a + pas * math.floor(alea.uniforme() * (n + 1))
        return a + alea.uniforme() * (b - a)
    if ty == 'choix':
        vals = evaluer(t['valeurs'], portee)
        return vals[math.floor(alea.uniforme() * len(vals))]
    if ty == 'permutation':
        return [float(k) for k in alea.permutation(int(_num(evaluer(t['n'], portee))))]
    raise ErreurMoteur(f'tirage inconnu : {ty}')


def _ids_bonnes(spec, portee, langue):
    if isinstance(spec, list):
        ids = []
        for s in spec:
            ids.extend(_ids_bonnes(s, portee, langue))
        return ids
    txt = gabarit(spec, portee, 'en')
    return [x for x in txt.replace(',', ' ').split() if x]


def instancier(q: dict, graine='0', parametres=None, langue='fr', hasard_parametres=False, macros=None,
               ordre_origine=False) -> dict:
    """Une instance affichable de la question q.

    graine : chaîne ; parametres : {id_menu: id_option} (« Adapt Question ») ; hasard_parametres : tire les menus au
    hasard (variante surprise) ; ordre_origine : ignore le mélange des réponses (contrôles)."""
    if langue not in ('fr', 'en'):
        raise ErreurMoteur('langue fr ou en')
    alea = Alea(str(graine) + '|' + q['id'])
    racine = Portee(_flottants(q.get('donnees', {})))
    portee = racine.enfant()
    choisis = _choisir_parametres(q, portee, parametres, alea, hasard_parametres)
    base = portee
    for essai in range(1001):
        portee = base.enfant()
        for t in q.get('aleatoire', []):
            portee.v[t['id']] = _tirer(t, portee, alea)
        for nom, ex in q.get('variables', []):
            portee.v[nom] = evaluer(ex, portee)
        if 'contrainte' not in q or _vrai(evaluer(q['contrainte'], portee)):
            break
    else:
        raise ErreurMoteur('contrainte jamais satisfaite (1000 essais)')
    # réponses proposées
    choix = []
    for c in q.get('choix', []):
        if 'si' in c and not _vrai(evaluer(c['si'], portee)):
            continue
        choix.append(c)
    bonnes = _ids_bonnes(q['bonne'], portee, langue) if q.get('bonne') is not None else []
    ids = [c['id'] for c in choix]
    for b in bonnes:
        if b not in ids:
            raise ErreurMoteur(f'bonne réponse {b} absente des choix {ids}')
    if q.get('choix_conserves') is not None and choix:
        k = int(_num(evaluer(q['choix_conserves'], portee)))
        if k < len(choix):
            autres = [c for c in choix if c['id'] not in bonnes]
            perm = alea.permutation(len(autres))
            garder = {autres[i]['id'] for i in perm[:max(0, k - len(bonnes))]} | set(bonnes)
            choix = [c for c in choix if c['id'] in garder]
    if q.get('melange') and not ordre_origine and len(choix) > 1:
        perm = alea.permutation(len(choix))
        choix = [choix[i] for i in perm]
    sortie_choix = []
    for k, c in enumerate(choix):
        pc = portee.enfant({'lettre': LETTRES[k]})
        sc = {'id': c['id'], 'lettre': LETTRES[k]}
        if 'texte' in c:
            sc['texte'] = gabarit(c['texte'], pc, langue)
        if 'figure' in c:
            sc['figure'] = developper_figure(c['figure'], pc, langue, _macros(q, macros))
        sortie_choix.append(sc)
    lettre_de = {c['id']: c['lettre'] for c in sortie_choix}
    bonnes_lettres = [lettre_de[b] for b in bonnes]
    pr = portee.enfant({'bonne_lettre': bonnes_lettres[0] if bonnes_lettres else '',
                        'bonnes_lettres': ', '.join(bonnes_lettres),
                        'lettre_de': lettre_de})
    out = {
        'id': q['id'], 'graine': str(graine), 'langue': langue, 'version_moteur': VERSION_MOTEUR,
        'parametres': choisis,
        'valeurs': _valeurs_exposees(q, portee),
        'titre': gabarit(q['titre'], pr, langue),
        'enonce': gabarit(q['enonce'], pr, langue),
        'choix': sortie_choix,
        'bonnes': bonnes, 'bonnes_lettres': bonnes_lettres,
        'indice': gabarit(q.get('indice'), pr, langue),
        'explication': gabarit(q.get('explication'), pr, langue),
        'elements_de_reponse': [gabarit(t, pr, langue) for t in q.get('elements_de_reponse', [])],
        'figure': developper_figure(q.get('figure'), pr, langue, _macros(q, macros)),
        'figure_indice': developper_figure(q.get('figure_indice'), pr, langue, _macros(q, macros)),
        'tirages': alea.tirages,
    }
    return out


def _macros(q, macros):
    if not q.get('macros'):
        return macros
    m = dict(macros or {})
    m.update(q['macros'])
    return m


def _valeurs_exposees(q, portee):
    out = {}
    noms = [t['id'] for t in q.get('aleatoire', [])] + [n for n, _ in q.get('variables', [])]
    for n in noms:
        v = portee.cherche(n)
        out[n] = _exposer(v)
    return out


def _exposer(v):
    if isinstance(v, float):
        return arrondi_sig(v, 12)
    if isinstance(v, list):
        return [_exposer(x) for x in v]
    if isinstance(v, dict):
        return {k: _exposer(x) for k, x in v.items()}
    return v


def variantes(q: dict) -> list:
    """Toutes les combinaisons des menus « Adapt Question » (dans l'ordre), options indisponibles exclues."""
    prms = q.get('parametres', [])
    res = [{}]
    for prm in prms:
        nouv = []
        for r in res:
            portee = Portee(_flottants(q.get('donnees', {}))).enfant()
            for p2 in prms:
                if p2['id'] in r:
                    o = next(o for o in p2['options'] if o['id'] == r[p2['id']])
                    portee.v[p2['id']] = _valeurs_option(p2, o, p2['options'].index(o))
            for k, o in enumerate(prm['options']):
                if 'si' in o and not _vrai(evaluer(o['si'], portee)):
                    continue
                nouv.append(dict(r, **{prm['id']: o['id']}))
        res = nouv
    return res


# =====================================================================================================  JSON canonique
def json_canonique(v) -> str:
    """Sérialisation identique à celle de l'implémentation TypeScript (clés triées, nombres façon JavaScript)."""
    if v is None:
        return 'null'
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if _est_nombre(v):
        return nombre_js(float(v))
    if isinstance(v, str):
        return _chaine_json(v)
    if isinstance(v, list):
        return '[' + ','.join(json_canonique(x) for x in v) + ']'
    if isinstance(v, dict):
        return '{' + ','.join(_chaine_json(k) + ':' + json_canonique(v[k]) for k in sorted(v, key=_cle_utf16)) + '}'
    raise ErreurMoteur(f'non sérialisable : {v!r}')


def _cle_utf16(k: str):
    return k.encode('utf-16-be')


def _chaine_json(s: str) -> str:
    out = ['"']
    for c in s:
        o = ord(c)
        if c == '"':
            out.append('\\"')
        elif c == '\\':
            out.append('\\\\')
        elif c == '\n':
            out.append('\\n')
        elif c == '\r':
            out.append('\\r')
        elif c == '\t':
            out.append('\\t')
        elif c == '\b':
            out.append('\\b')
        elif c == '\f':
            out.append('\\f')
        elif o < 0x20:
            out.append('\\u%04x' % o)
        else:
            out.append(c)
    out.append('"')
    return ''.join(out)
