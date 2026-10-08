"""Rapports d'incident, d'après le gabarit commun « reporting.py » du kit.

Trois règles :
1. **Rien ne part sans accord.**  Le consentement est demandé au premier
   lancement (interface graphique) et peut être retiré à tout moment ; sans
   lui, les rapports restent dans un dossier local que l'utilisateur peut
   consulter ou envoyer lui-même.
2. **Aucune donnée personnelle.**  Ni nom de machine, ni nom d'utilisateur, ni
   chemin complet : le dossier personnel devient « ~ », les chemins profonds
   sont tronqués.  La machine est décrite par son système, son processeur, sa
   mémoire ; l'installation par un identifiant aléatoire tiré au premier
   lancement, qui ne dit rien de la personne.
3. **Rien ne bloque l'application.**  Envoi dans un fil de fond, délai court ;
   un envoi raté est mis en file et repart au démarrage suivant.

Point de collecte : le même que les autres applications de l'auteur ; il range
les rapports par application d'après l'en-tête X-App (« coupole/x.y.z »).
"""
from __future__ import annotations

import json
import logging
import os
import platform
import re
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path

from .. import __version__
from . import config

log = logging.getLogger(__name__)

APPLICATION = 'coupole'
DELAI = 8
FILE_MAX = 50
AGE_MAX = 30 * 86400
GENRES = ('installation', 'demarrage', 'plantage', 'crash_natif', 'gel', 'manuel')

_dossier: Path | None = None


def init(dossier: Path | None = None) -> None:
    global _dossier
    _dossier = (dossier or config.dossier_config()) / '_rapports'
    try:
        _dossier.mkdir(parents=True, exist_ok=True)
    except OSError:
        log.warning('report queue unavailable', exc_info=True)


def dossier_rapports() -> Path | None:
    return _dossier


def consentement():
    """True, False, ou None tant que la question n'a pas été posée."""
    return config.reglages()['rapports_autorises']


def definir_consentement(accepte: bool) -> None:
    r = config.reglages()
    r['rapports_autorises'] = bool(accepte)
    r['consentement_date'] = time.strftime('%Y-%m-%d %H:%M:%S')


# ---------------------------------------------------------------- anonymisation
def anonymiser(texte) -> str:
    if not texte:
        return ''
    texte = str(texte)
    home = str(Path.home())
    for v in {home, home.replace('\\', '/'), home.lower()}:
        if v and len(v) > 1:
            texte = texte.replace(v, '~')
    for var in ('USERNAME', 'USER', 'LOGNAME'):
        u = os.environ.get(var)
        if u and len(u) > 2:
            texte = re.sub(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(u), '<user>', texte)
    texte = re.sub(r'([A-Za-z]:\\[^\\\n"\']{1,30})(\\[^\\\n"\']{1,60}){2,}\\', r'\1\\…\\', texte)
    texte = re.sub(r'(/(?:home|Users|mnt|media|Volumes)/[^/\n"\']{1,30})(/[^/\n"\']{1,60}){2,}/', r'\1/…/', texte)
    return texte


def machine() -> dict:
    """Le strict nécessaire pour reproduire un problème, sans rien de personnel."""
    from . import machine as m
    try:
        mm = m.detecter()
        d = {'os': '%s %s' % (mm.nom_systeme, mm.version_systeme), 'arch': mm.architecture,
             'processeur': mm.processeur[:60], 'coeurs': mm.coeurs_logiques,
             'memoire_go': round(mm.memoire_totale_mo / 1024, 1),
             'gpu': ', '.join(c.nom for c in mm.cartes)[:80]}
    except Exception:
        d = {'os': '%s %s' % (platform.system(), platform.release()), 'arch': platform.machine()}
    d.update({'poste': 'install-' + str(config.reglages()['id_installation']),
              'python': platform.python_version(), 'application': APPLICATION, 'version': __version__,
              'paquet': _type_installation()})
    return d


def _type_installation() -> str:
    app = Path(__file__).resolve().parents[2]
    if (app.parent / 'python').is_dir():
        return 'paquet'
    if (app / '.git').exists():
        return 'source'
    return 'pip'


# ---------------------------------------------------------------- envoi
def _poster(charge: bytes) -> bool:
    from . import sources
    req = urllib.request.Request(sources.valeur('rapports.collecte'), data=charge, method='POST', headers={
        'Content-Type': 'application/json; charset=utf-8',
        'X-App': '%s/%s' % (APPLICATION, __version__),
        'User-Agent': 'Coupole/%s' % __version__})
    try:
        with urllib.request.urlopen(req, timeout=DELAI) as r:
            return 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        return not (e.code == 429 or e.code >= 500)     # 4xx : inutile de réessayer
    except Exception:
        return False


def _mettre_en_file(rapport: dict) -> Path | None:
    if _dossier is None:
        return None
    try:
        nom = '%s-%s-%d.json' % (time.strftime('%Y%m%dT%H%M%S'), rapport.get('genre', 'autre'), os.getpid())
        p = _dossier / nom
        p.write_text(json.dumps(rapport, ensure_ascii=False, indent=1), encoding='utf-8')
        return p
    except OSError:
        return None


def envoyer(genre: str, **champs) -> dict:
    """Constitue un rapport et le transmet en fond si l'utilisateur l'a accepté."""
    rapport = machine()
    rapport['genre'] = genre if genre in GENRES else 'autre'
    rapport['horodatage'] = time.strftime('%Y-%m-%d %H:%M:%S')
    for cle, valeur in champs.items():
        rapport[cle] = anonymiser(valeur) if isinstance(valeur, str) else valeur
    if consentement() is not True:
        _mettre_en_file(rapport)
        return rapport
    charge = json.dumps(rapport, ensure_ascii=False).encode('utf-8')

    def tache():
        if not _poster(charge):
            _mettre_en_file(rapport)
    threading.Thread(target=tache, name='rapport', daemon=True).start()
    return rapport


def vider_file() -> int:
    if _dossier is None or consentement() is not True:
        return 0
    try:
        fichiers = sorted(_dossier.glob('*.json'))
    except OSError:
        return 0
    for vieux in fichiers[:-FILE_MAX] if len(fichiers) > FILE_MAX else []:
        vieux.unlink(missing_ok=True)
    limite = time.time() - AGE_MAX
    n = 0
    for f in sorted(_dossier.glob('*.json')):
        try:
            if f.stat().st_mtime < limite:
                f.unlink(missing_ok=True)
                continue
            charge = f.read_bytes()
        except OSError:
            continue
        if _poster(charge):
            f.unlink(missing_ok=True)
            n += 1
        else:
            break
    return n


def reprendre_file_en_fond() -> None:
    threading.Thread(target=vider_file, name='rapports-file', daemon=True).start()


def signaler_demarrage() -> None:
    """Preuve de vie, au plus une fois par jour (installation la première fois)."""
    r = config.reglages()
    jour = time.strftime('%Y-%m-%d')
    if not r.get('installee_le'):
        r['installee_le'] = jour
        r['dernier_demarrage'] = jour
        envoyer('installation')
    elif r.get('dernier_demarrage') != jour:
        r['dernier_demarrage'] = jour
        envoyer('demarrage')


def signaler_plantage(tb_texte: str, **champs) -> dict:
    resume = next((l.strip()[:200] for l in reversed(tb_texte.strip().splitlines()) if l.strip()), '')
    return envoyer('plantage', traceback=tb_texte[-8000:], resume=resume, **champs)


def installer_crochets(chemin_faulthandler: Path | None = None) -> None:
    """Exceptions non rattrapées (fil principal et fils secondaires) + crash natif (faulthandler)."""
    ancien = sys.excepthook

    def crochet(t, v, tb):
        texte = ''.join(traceback.format_exception(t, v, tb))
        log.error('uncaught exception:\n%s', texte)
        try:
            signaler_plantage(texte)
        except Exception:
            pass
        ancien(t, v, tb)
    sys.excepthook = crochet

    def crochet_fil(args):
        crochet(args.exc_type, args.exc_value, args.exc_traceback)
    threading.excepthook = crochet_fil
    if chemin_faulthandler is not None:
        try:
            import faulthandler
            relever_crash_natif(chemin_faulthandler)
            f = open(chemin_faulthandler, 'w', encoding='utf-8')
            faulthandler.enable(f)
            installer_crochets._fichier = f  # garder ouvert
        except Exception:
            pass


def relever_crash_natif(chemin) -> bool:
    p = Path(chemin)
    try:
        if not p.exists() or p.stat().st_size == 0:
            return False
        texte = p.read_text(encoding='utf-8', errors='replace')
        p.unlink(missing_ok=True)
    except OSError:
        return False
    if not texte.strip():
        return False
    envoyer('crash_natif', trace=anonymiser(texte)[:8000], resume=texte.strip().splitlines()[0][:200])
    return True


class Vigie:
    """Détecte une interface figée (le fil graphique doit appeler battre() régulièrement)."""

    def __init__(self, seuil=10.0, periode=2.0):
        self.seuil, self.periode = seuil, periode
        self._dernier = time.monotonic()
        self._signale = False
        self._debut = 0.0
        self._actif = False
        self._deja_battu = False
        self._fil_gui = threading.get_ident()

    def battre(self):
        t = time.monotonic()
        self._deja_battu = True
        if self._signale:
            envoyer('gel', resume='end of freeze after %.0f s' % (t - self._debut), phase='fin')
            self._signale = False
        self._dernier = t

    def demarrer(self):
        self._fil_gui = threading.get_ident()
        self._actif = True
        threading.Thread(target=self._boucle, name='vigie', daemon=True).start()

    def arreter(self):
        self._actif = False

    def _boucle(self):
        while self._actif:
            time.sleep(self.periode)
            if not self._deja_battu:
                continue
            retard = time.monotonic() - self._dernier
            if retard >= self.seuil and not self._signale:
                self._signale = True
                self._debut = self._dernier
                envoyer('gel', resume='GUI frozen for %.0f s' % retard, phase='debut', piles=self._piles())

    def _piles(self) -> str:
        morceaux = []
        try:
            cadres = sys._current_frames()
        except Exception:
            return ''
        for ident in sorted(cadres, key=lambda i: i != self._fil_gui):
            pile = ''.join(traceback.format_stack(cadres[ident])[-12:])
            morceaux.append('--- %s ---\n%s' % ('GUI' if ident == self._fil_gui else ident, pile))
        return anonymiser('\n'.join(morceaux))[:8000]
