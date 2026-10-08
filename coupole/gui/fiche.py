"""Fiche d'informations en ligne sur un objet (SIMBAD, Sesame, JPL SBDB) : widget réutilisable par les modules.

La requête part hors du fil graphique, au plus une fois par objet affiché (attente de 600 ms après le dernier
changement de sélection : faire défiler un tableau n'envoie rien), et la réponse d'un objet qui n'est plus
demandé est ignorée.  Hors ligne : la fiche en cache s'affiche avec sa date, sinon un message clair.
"""
from __future__ import annotations

import html
import math

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QLabel, QTextBrowser, QVBoxLayout, QWidget

from ..core import config
from ..core.i18n import langue, tr
from .adaptatif import Flux
from .outils import Tache, aide, bouton, case

NOMS_SERVICES = {'simbad': 'SIMBAD (CDS)', 'sesame': 'Sesame (CDS)', 'sbdb': 'JPL SBDB'}


def _n(v, dec=3) -> str:
    """Nombre dans la langue courante (virgule décimale en français)."""
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return '—'
    s = ('%.' + str(dec) + 'f') % v if isinstance(v, float) else str(v)
    return s.replace('.', ',') if langue() == 'fr' else s


def _g(v, chiffres=4) -> str:
    """`chiffres` chiffres significatifs, en notation ordinaire de 10⁻⁴ à 10⁹ (pas de « 1.73e+03 »)."""
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return '—'
    if v == 0:
        return '0'
    e = math.floor(math.log10(abs(v)))
    s = ('%.*f' % (max(0, chiffres - 1 - e), v)) if -4 <= e < 9 else '%.*e' % (chiffres - 1, v)
    return s.replace('.', ',') if langue() == 'fr' else s


def _court(v) -> str:
    """Valeur telle que publiée, sans zéros ajoutés (« -100 », « -0,000334 »)."""
    if v is None:
        return '—'
    s = '%.7g' % v
    return s.replace('.', ',') if langue() == 'fr' else s


def _sexa(texte: str, dec: int) -> str:
    """« 20 12 06.5418877464 » → « 20 12 06.54 » (précision affichée raisonnable)."""
    import re
    m = re.match(r'^(.*?\d\d)(?:\.(\d+))?$', (texte or '').strip())
    if not m:
        return texte or ''
    return m.group(1) + (('.' + m.group(2)[:dec]) if m.group(2) and dec else '')


def _ligne(cle, valeur_html, **kw) -> str:
    return '<tr><td style="padding:2px 10px 2px 0; vertical-align:top"><b>%s</b></td><td>%s</td></tr>' % (
        html.escape(tr(cle, **kw)), valeur_html)


def html_fiche(r: dict) -> str:
    """Fiche (résultat de ``enligne.fiche_objet``) en HTML, dans la langue courante."""
    f = r.get('fiche') or {}
    service = NOMS_SERVICES.get(f.get('service', ''), f.get('service', ''))
    e = html.escape
    if f.get('ambigu'):
        return '<p>%s</p>' % e(tr('fiche_ambigu', nom=f.get('nom', ''), liste=', '.join(f.get('candidats', [])[:10])))
    out = ['<h3>%s</h3><table>' % e(f.get('nom', ''))]
    if r.get('demande') and f.get('service') != 'sbdb':
        from ..core.simbad import flatten
        if flatten(r['demande']) != flatten(f.get('nom', '')) and \
                flatten(r['demande']) not in {flatten(i) for i in f.get('ids', [])[:3]}:
            out.append(_ligne('fiche_retenu', e(f.get('nom', '')) + '<br><i>%s</i>' % e(
                tr('fiche_retenu_note', demande=r['demande'])), service=service))
    if f.get('service') in ('simbad', 'sesame'):
        t = f.get('type') or ''
        if f.get('otype'):
            t = '%s (%s)' % (t, f['otype']) if t else f['otype']
        if t:
            out.append(_ligne('fiche_type', e(t)))
        if f.get('ra') is not None:
            sexa = (' — %s, %s' % (_sexa(f.get('ra_s', ''), 2), _sexa(f.get('dec_s', ''), 1))) if f.get('ra_s') else ''
            out.append(_ligne('fiche_coord', e('α = %s°, δ = %s°%s' % (_n(f['ra'], 5), _n(f['dec'], 5), sexa))))
        if f.get('flux'):
            out.append(_ligne('fiche_mags', e('  '.join('%s = %s' % (b, _n(v, 2)) for b, v in f['flux'].items()))))
        plx, err = f.get('plx'), f.get('plx_err')
        if plx is not None:
            if plx > 0 and err and plx / err >= 5:
                pc = 1000.0 / plx
                txt = tr('fiche_plx_distance', plx=_g(plx), err=_g(err, 2), pc=_g(pc, 3), al=_g(pc * 3.26156, 3))
            else:
                txt = tr('fiche_plx_imprecise', plx=_g(plx), err=_g(err, 2) if err else '?')
            out.append(_ligne('fiche_plx', e(txt)))
        d = f.get('distance')
        if d:
            s = '%s %s' % (_g(d['valeur']), d['unite'])
            if d.get('moins') is not None:
                s += ' (−%s / +%s)' % (_g(d['moins'], 2), _g(d['plus'], 2))
            if d.get('methode'):
                s += ' — %s %s' % (tr('fiche_methode'), d['methode'])
            if d.get('reference'):
                s += ' — %s' % d['reference']
            out.append(_ligne('fiche_distance', e(s)))
        if f.get('vr') is not None or f.get('z') is not None:
            s = tr('fiche_vitesse_val', v=_court(f.get('vr')), z=_court(f.get('z')))
            if f.get('rv_qualite'):
                s += ' (%s %s)' % (tr('fiche_qualite'), f['rv_qualite'])
            out.append(_ligne('fiche_vitesse', e(s)))
        if f.get('dim_x'):
            out.append(_ligne('fiche_taille', e(tr('fiche_taille_val', x=_g(f['dim_x'], 3),
                                                   y=_g(f.get('dim_y') or f['dim_x'], 3),
                                                   a=_g(f.get('dim_angle'), 3)))))
        if f.get('sp'):
            out.append(_ligne('fiche_sp', e(f['sp'])))
        if f.get('morpho'):
            out.append(_ligne('fiche_morpho', e(f['morpho'])))
        ids = [i for i in f.get('ids', []) if i != f.get('nom')]
        if ids:
            s = ', '.join(ids[:14]) + ((' ' + tr('fiche_ids_plus', n=len(ids) - 14)) if len(ids) > 14 else '')
            out.append(_ligne('fiche_ids', e(s)))
    elif f.get('service') == 'sbdb':
        c = f.get('classe', '')
        if f.get('classe_code'):
            c += ' (%s)' % f['classe_code']
        drap = [tr('fiche_neo')] if f.get('neo') else []
        drap += [tr('fiche_pha')] if f.get('pha') else []
        if drap:
            c += ' — ' + ', '.join(drap)
        out.append(_ligne('fiche_classe', e(c)))
        el = f.get('elements') or {}
        lignes = []
        for k, dec in (('a', 4), ('e', 4), ('i', 3), ('q', 4), ('ad', 4), ('om', 3), ('w', 3)):
            if k in el and el[k][0] is not None:
                unite = {'deg': '°', 'au': ' au'}.get(el[k][1], (' ' + el[k][1]) if el[k][1] else '')
                lignes.append('%s = %s%s' % (tr('fiche_el_' + k), _n(float(el[k][0]), dec), unite))
        if 'per' in el and el['per'][0] is not None and el['per'][1] == 'd':
            lignes.append('%s = %s' % (tr('fiche_el_per'), tr('fiche_annees', v=_n(el['per'][0] / 365.25, 2))))
        if lignes:
            jd = f.get('epoque_jd')
            out.append('<tr><td style="padding:2px 10px 2px 0; vertical-align:top"><b>%s</b></td><td>%s</td></tr>' % (
                e(tr('fiche_elements', jd=_n(jd, 1) if jd else '?')), '<br>'.join(e(x) for x in lignes)))
        ph = f.get('phys') or {}
        lignes = []
        for k, unite in (('diameter', ' km'), ('albedo', ''), ('rot_per', ' h'), ('H', '')):
            if k in ph:
                v = ph[k][0]
                lignes.append('%s = %s%s' % (tr('fiche_ph_' + k), _g(v, 4) if isinstance(v, float) else v, unite))
            elif k in ('diameter', 'albedo', 'rot_per'):
                lignes.append('%s : %s' % (tr('fiche_ph_' + k), tr('fiche_ph_inconnu')))
        out.append('<tr><td style="padding:2px 10px 2px 0; vertical-align:top"><b>%s</b></td><td>%s</td></tr>' % (
            e(tr('fiche_physique')), '<br>'.join(e(x) for x in lignes)))
    liens = f.get('liens') or {}
    if liens:
        out.append(_ligne('fiche_liens', ' · '.join('<a href="%s">%s</a>' % (e(u), e(tr('fiche_lien_' + k)))
                                                    for k, u in liens.items())))
    out.append('</table>')
    date = (r.get('date') or '')[:16].replace('T', ' ')
    suffixe = tr('fiche_depuis_cache') if r.get('cache') else ''
    if r.get('perime'):
        suffixe += tr('fiche_perime')
    out.append('<p><small>%s</small></p>' % e(tr('fiche_date', service=service, date=date, cache=suffixe)))
    return ''.join(out)


def message(r: dict, service: str = '') -> str:
    """Texte d'état pour un résultat sans fiche."""
    etat = r.get('etat')
    nom = r.get('demande', '')
    if etat == 'hors_ligne':
        return tr('fiche_hors_ligne', erreur=r.get('erreur', '')[:120])
    if etat == 'introuvable':
        return tr('fiche_introuvable', nom=nom, service=service or 'SIMBAD / Sesame / JPL SBDB')
    if etat == 'desactive':
        return tr('fiche_desactive', nom=nom)
    if etat == 'sans_fiche':
        return tr(r.get('raison') or 'fiche_vide')
    return ''


class FicheEnLigne(QWidget):
    """Affiche la fiche d'un objet ; `demander(nom, cat, sbdb, autres)` la charge (en différé, hors du fil)."""

    ATTENTE_MS = 600

    def __init__(self, parent=None):
        super().__init__(parent)
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 0)
        h = Flux()
        self.activer = case('fiche_activer', bool(config.reglages()['services_en_ligne']))
        self.activer.toggled.connect(self._activer)
        h.addWidget(self.activer)
        self.b_actualiser = bouton('fiche_actualiser', lambda: self._lancer(rafraichir=True))
        h.addWidget(self.b_actualiser)
        self.b_cosmo = bouton('fiche_vers_cosmo', self._vers_cosmo)
        self.b_cosmo.setEnabled(False)
        h.addWidget(self.b_cosmo)
        v.addLayout(h)
        self.etat = QLabel(tr('fiche_choisir'))
        self.etat.setWordWrap(True)
        v.addWidget(self.etat)
        self.vue = aide(QTextBrowser(), 'fiche_vue_aide')
        self.vue.setOpenExternalLinks(True)
        v.addWidget(self.vue, 1)
        self._demande = None
        self._numero = 0
        self._resultat = None
        self._minuterie = QTimer(self)
        self._minuterie.setSingleShot(True)
        self._minuterie.timeout.connect(self._lancer)

    # ------------------------------------------------------------ API
    def demander(self, nom: str | None, cat: str | None = None, sbdb: str | None = None, autres=()):
        """Objet à afficher (None : aucun).  La requête part après ATTENTE_MS sans nouveau changement."""
        self._demande = (nom, cat, sbdb, tuple(autres)) if nom else None
        self._numero += 1
        self._resultat = None
        self.b_cosmo.setEnabled(False)
        if not nom:
            self._minuterie.stop()
            self.etat.setText(tr('fiche_choisir'))
            self.vue.clear()
            return
        self._minuterie.start(self.ATTENTE_MS)

    def resultat(self):
        return self._resultat

    # ------------------------------------------------------------ interne
    def _activer(self, oui):
        config.reglages()['services_en_ligne'] = bool(oui)
        if oui and self._demande:
            self._lancer()

    def _lancer(self, rafraichir=False):
        if not self._demande:
            return
        from ..core import enligne
        nom, cat, sbdb, autres = self._demande
        numero = self._numero
        service = 'JPL SBDB' if (cat in enligne.PETITS_CORPS or sbdb) else 'SIMBAD'
        self.etat.setText(tr('fiche_attente', service=service, nom=nom))
        self._t = Tache(enligne.fiche_objet, nom, cat, sbdb, autres, rafraichir,
                        en_ligne=self.activer.isChecked())
        self._t.fini.connect(lambda r, k=numero: self._recu(r, k))
        self._t.erreur.connect(lambda e, k=numero: self._recu({'etat': 'hors_ligne', 'erreur': e, 'demande': nom}, k))
        self._t.start()

    def _recu(self, r, numero):
        if numero != self._numero:          # réponse d'un objet qui n'est plus demandé
            return
        self._resultat = r
        if r.get('fiche') and r.get('etat') == 'ok':
            self.etat.setText('')
            self.vue.setHtml(html_fiche(r))
            z = r['fiche'].get('z')
            ok = z is not None and z > 0 and self._fenetre_cosmo() is not None
            self.b_cosmo.setEnabled(ok)
            if z is not None and z <= 0:
                self.etat.setText(tr('fiche_pas_de_z'))
        else:
            self.vue.clear()
            self.etat.setText(message(r))

    def _fenetre_cosmo(self):
        f = self.window()
        return f if hasattr(f, 'ouvrir_module') and f.panneau_module('cosmo') is not None else None

    def _vers_cosmo(self):
        r = self._resultat or {}
        f = r.get('fiche') or {}
        fen = self._fenetre_cosmo()
        if fen is None or not f.get('z') or f['z'] <= 0:
            return
        p = fen.ouvrir_module('cosmo')
        if p is not None and hasattr(p, 'recevoir_redshift'):
            p.recevoir_redshift(f['z'], f.get('nom', ''))
