"""Bilingue partout : chaque texte existe en français et en anglais, aucune chaîne en dur dans l'interface."""
import ast
import re
import string
from pathlib import Path

import pytest

from coupole.core import i18n

RACINE = Path(__file__).resolve().parents[1] / 'coupole'


def champs(texte):
    return sorted({f[1] for f in string.Formatter().parse(texte) if f[1]})


def test_chaque_cle_a_les_deux_langues():
    trous = {k: [lg for lg in i18n.LANGUES if not (v.get(lg) or '').strip()] for k, v in i18n.toutes_les_cles().items()}
    assert not {k: v for k, v in trous.items() if v}


def test_memes_champs_dans_les_deux_langues():
    ecarts = {k: (champs(v['fr']), champs(v['en'])) for k, v in i18n.toutes_les_cles().items()
              if '%' not in v['fr'] and champs(v['fr']) != champs(v['en'])}
    assert not ecarts


def test_en_tetes_fits_en_ascii():
    for k, v in i18n.toutes_les_cles().items():
        if k.startswith('hdr_'):
            for lg in ('fr', 'en'):
                assert v[lg].isascii(), (k, lg)


def _cles_utilisees():
    pref = re.compile(r"""(?:\btr|\bbouton|\bbouton_outil|\betiquette|\bcase|\bbilingue)\(\s*['"]([a-z][a-z0-9_]*)['"]""")
    act = re.compile(r"""\baction\(\s*self\s*,\s*['"]([a-z][a-z0-9_]*)['"]""")
    aid = re.compile(r"""(?:aide|liste|champ|nombre|decimal|vue_tableau)\([^'"\n]*?['"]([a-z][a-z0-9_]*_aide)['"]""")
    cle_aide = re.compile(r"""cle_aide=['"]([a-z][a-z0-9_]*)['"]""")
    out = set()
    for f in RACINE.rglob('*.py'):
        t = f.read_text(encoding='utf-8')
        for rx in (pref, act, aid, cle_aide):
            out |= set(rx.findall(t))
        out |= {'hdr_' + k for k in re.findall(r"""\bH\(\s*['"]([a-z][a-z0-9_]*)['"]""", t)}
        out |= {'lot_' + k for k in re.findall(r"""\bT\(\s*['"]([a-z][a-z0-9_]*)['"]""", t)}
        # les boutons, cases et actions ont une info-bulle « <clé>_aide »
        for k in re.findall(r"""\b(?:bouton|bouton_outil|case)\(\s*['"]([a-z][a-z0-9_]*)['"]\s*[,)]""", t):
            if 'cle_aide=' not in t[t.find(k):t.find(k) + 120]:
                out.add(k + '_aide')
        for k in act.findall(t):
            out.add(k + '_aide')
    return {k for k in out if not k.endswith('_')}


def test_toutes_les_cles_utilisees_existent():
    manquantes = sorted(k for k in _cles_utilisees() if k not in i18n.toutes_les_cles())
    assert not manquantes, manquantes


# ---------------------------------------------------------------- aucune chaîne en dur dans l'interface
APPELS = {'setText', 'setWindowTitle', 'setToolTip', 'setStatusTip', 'setPlaceholderText', 'addTab', 'showMessage',
          'QLabel', 'QPushButton', 'QCheckBox', 'QGroupBox', 'QAction', 'addMenu', 'information', 'warning',
          'question', 'critical', 'setSpecialValueText', 'setSuffix', 'print', 'setHorizontalHeaderLabels'}
PERMIS = re.compile(r"^(\s|[\W\d_]|%[-0-9.]*[sdgfr]|\{[a-z_]*(:[^}]*)?\}|<[^>]*>|Coupole|ASTAP|T120|IRIS|XISF|FITS|"
                    r"JSON|CSV|PNG|Qt|PyQt|UTC|OK|Français|English|ÉCART|ECHEC|ÉCHEC|MHz|km/s|HDU|n=|install-)*$")
FICHIERS = [p for p in RACINE.rglob('*.py') if p.parent.name in ('gui',) or p.name in ('cli.py', 'gui.py')]


def _litteraux_interdits(arbre):
    for n in ast.walk(arbre):
        if not isinstance(n, ast.Call):
            continue
        nom = n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, 'id', '')
        if isinstance(n.func, ast.Attribute) and 'log' in ast.dump(n.func.value).lower():
            continue                                  # journal technique (anglais), pas l'interface
        args = list(n.args)
        if nom == 'add_argument':
            args = [k.value for k in n.keywords if k.arg in ('help', 'metavar')]
        elif nom not in APPELS:
            continue
        for a in args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str) and re.search(r'[A-Za-zÀ-ÿ]{2,}', a.value) \
                    and not PERMIS.match(a.value):
                yield n.lineno, a.value


@pytest.mark.parametrize('fichier', FICHIERS, ids=lambda p: str(p.relative_to(RACINE)))
def test_aucune_chaine_en_dur(fichier):
    trouves = list(_litteraux_interdits(ast.parse(fichier.read_text(encoding='utf-8'))))
    assert not trouves, trouves


@pytest.mark.parametrize('code,attendu', [('fr_FR.UTF-8', 'fr'), ('fr_CA', 'fr'), ('en_GB', 'en'), ('de_DE.UTF-8', 'en'),
                                          ('C', 'en'), ('', 'en')])
def test_detection_de_la_langue(code, attendu, monkeypatch):
    for v in ('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'):
        monkeypatch.delenv(v, raising=False)
    if code:
        monkeypatch.setenv('LANG', code)
    monkeypatch.setattr('locale.setlocale', lambda *a: 'C')
    assert i18n.detecter_langue() == attendu


def test_choix_force_et_repli(langue):
    langue('en')
    assert i18n.tr('menu_aide') == '&Help'
    langue('fr')
    assert i18n.tr('menu_aide') == '&Aide'
    assert i18n.choisir_langue('kl') == 'en'          # langue non traduite : anglais, jamais d'étiquette vide
    assert i18n.tr('cle_inexistante') == 'cle_inexistante'
