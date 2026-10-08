"""Cartes FITS lues telles qu'écrites, et en-tête modifiable avec traçabilité.

Chaque valeur remplacée est recopiée dans un ``HISTORY valeur d'origine : ...``
(repris de ``ohp_xisf.py``).  Les cartes sont gardées dans l'ordre d'origine.
"""
from __future__ import annotations

import re
import textwrap
import unicodedata


def ascii_(s) -> str:
    return unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode('ascii')


def fstr(s) -> str:
    """Valeur chaîne FITS (entre apostrophes, ASCII)."""
    return "'%s'" % ascii_(str(s)).replace("'", "''")


def fnum(v, fmt='%.10g') -> str:
    return fmt % v


def lire_cartes(chemin) -> list[str]:
    """Cartes de l'en-tête primaire (80 caractères), sans END."""
    cartes = []
    with open(chemin, 'rb') as f:
        while True:
            b = f.read(2880)
            if len(b) < 2880:
                raise IOError('truncated FITS header')
            for i in range(0, 2880, 80):
                c = b[i:i + 80].decode('ascii', 'replace')
                if c[:8] == 'END     ':
                    return cartes
                cartes.append(c)


def decouper(carte: str):
    """(nom, valeur, commentaire) au sens de l'élément FITSKeyword de XISF."""
    nom = carte[:8].strip().upper()
    if nom and not re.match(r'^[A-Z0-9_-]{1,8}$', nom):
        return ('COMMENT', '', carte.rstrip())
    if nom in ('HISTORY', 'COMMENT', '') or carte[8:10] != '= ':
        texte = carte[8:].rstrip()
        if nom == '':
            nom = 'COMMENT'
        if nom not in ('HISTORY', 'COMMENT'):
            return ('COMMENT', '', (carte[:8].strip() + ' ' + texte).strip())
        return (nom, '', texte.strip() if nom == 'COMMENT' else texte[1:] if texte.startswith(' ') else texte)
    s = carte[10:].lstrip()
    if s.startswith("'"):
        i, val = 1, ''
        while i < len(s):
            if s[i] == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    val += "'"
                    i += 2
                    continue
                break
            val += s[i]
            i += 1
        valeur = "'%s'" % val.rstrip().replace("'", "''")
        apres = s[i + 1:]
        com = apres.split('/', 1)[1].strip() if '/' in apres else ''
    elif '/' in s:
        v, com = s.split('/', 1)
        valeur, com = v.strip(), com.strip()
    else:
        valeur, com = s.strip(), ''
    return (nom, valeur, com)


class Entete:
    """Liste ordonnée de [nom, valeur, commentaire] avec historique des modifications."""

    # Modèle de la carte HISTORY qui garde une valeur remplacée (remplacé selon la langue des en-têtes).
    MODELE_ORIGINE = "valeur d'origine : {nom} = {valeur}{raison}"

    def __init__(self, cartes, modele_origine: str | None = None):
        self.k = [list(decouper(c)) for c in cartes]
        self.modifs: list[str] = []
        self.histoire: list[str] = []
        self.modele = modele_origine or self.MODELE_ORIGINE

    def _origine(self, nom, valeur, raison):
        return self.modele.format(nom=nom, valeur=valeur, raison=(' (' + raison + ')') if raison else '')

    def get(self, nom):
        for k in self.k:
            if k[0] == nom:
                return k[1]
        return None

    def gets(self, nom):
        v = self.get(nom)
        if v is None:
            return None
        return v[1:-1].replace("''", "'").strip() if v.startswith("'") else v.strip()

    def getf(self, nom):
        try:
            return float(self.gets(nom))
        except (TypeError, ValueError):
            return None

    def poser(self, nom, valeur, com, raison=''):
        """Remplace en place ou ajoute ; l'ancienne valeur part en HISTORY si elle change."""
        for k in self.k:
            if k[0] == nom:
                if k[1] != valeur:
                    self.histoire.append(self._origine(nom, k[1], raison))
                    self.modifs.append(nom)
                    k[1] = valeur
                    if com:
                        k[2] = com
                return
        self.k.append([nom, valeur, com])
        self.modifs.append('+' + nom)

    def neutraliser(self, pred, raison):
        """Retire les mots-clés devenus faux en les recopiant en HISTORY."""
        garde = []
        for k in self.k:
            if k[0] not in ('HISTORY', 'COMMENT') and pred(k[0]):
                self.histoire.append(self._origine(k[0], k[1], raison))
                self.modifs.append('-' + k[0])
            else:
                garde.append(k)
        self.k = garde

    def header_astropy(self):
        from astropy.io import fits
        h = fits.Header()
        for nom, val, com in self.k:
            if nom in ('HISTORY', 'COMMENT'):
                continue
            try:
                h.append(fits.Card.fromstring(('%-8s= %s' % (nom, val))[:80]))
            except Exception:
                pass
        return h

    def finaliser(self):
        out = [tuple(k) for k in self.k]
        for t in self.histoire:
            for morceau in textwrap.wrap(ascii_(t), 70, break_long_words=True, break_on_hyphens=False):
                out.append(('HISTORY', '', morceau))
        return out
