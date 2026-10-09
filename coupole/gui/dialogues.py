"""Dialogues du cœur : consentement, réglages, assistant ASTAP, à propos, signalement, mise à jour, aide."""
from __future__ import annotations

import html
import json
import os
import platform

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QGridLayout, QHBoxLayout, QLabel,
                             QMessageBox, QPlainTextEdit, QTabWidget, QTextBrowser, QVBoxLayout, QWidget)

from .. import __version__
from ..core import config, i18n
from ..core.i18n import tr
from . import adaptatif
from .outils import Tache, aide, bouton, case, champ, decimal, liste, nombre


def _boutons(dlg, ok=True, annuler=True):
    std = QDialogButtonBox.StandardButton
    bb = QDialogButtonBox((std.Ok if ok else std.NoButton) | (std.Cancel if annuler else std.NoButton))
    if ok:
        b = bb.button(std.Ok)
        b.setText(tr('dlg_ok'))
        aide(b, 'dlg_ok_aide')
    if annuler:
        b = bb.button(std.Cancel)
        b.setText(tr('dlg_annuler'))
        aide(b, 'dlg_annuler_aide')
    bb.accepted.connect(dlg.accept)
    bb.rejected.connect(dlg.reject)
    return bb


def navigateur(html_texte: str, cle_aide: str) -> QTextBrowser:
    t = QTextBrowser()
    t.setOpenExternalLinks(True)
    t.setHtml(html_texte)
    return aide(t, cle_aide)


# ======================================================================== consentement
class DialogueConsentement(QDialog):
    """Premier lancement : rien n'est envoyé sans accord explicite."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('consent_titre'))
        v = QVBoxLayout(self)
        t = QLabel(tr('consent_texte'))
        t.setWordWrap(True)
        t.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(t)
        h = QHBoxLayout()
        self.b_non = bouton('consent_non', self.reject)
        self.b_oui = bouton('consent_oui', self.accept)
        h.addStretch(1)
        h.addWidget(self.b_non)
        h.addWidget(self.b_oui)
        v.addLayout(h)
        adaptatif.ajuster(self, 560, 360, cle='consentement')
        adaptatif.assouplir(self)


def demander_consentement_si_besoin(parent=None):
    from ..core import rapports
    if rapports.consentement() is None:
        d = DialogueConsentement(parent)
        rapports.definir_consentement(d.exec() == QDialog.DialogCode.Accepted)


# ======================================================================== réglages
class DialogueReglages(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('reg_titre'))
        r = config.reglages()
        racine = QVBoxLayout(self)
        self.onglets = aide(QTabWidget(), 'reg_onglets_aide')
        racine.addWidget(self.onglets)
        general = QWidget()
        self.onglets.addTab(adaptatif.defilable(general), tr('reg_onglet_general'))
        self.onglets.addTab(adaptatif.defilable(self._onglet_sources()), tr('reg_onglet_sources'))
        f = QFormLayout(general)
        self.langue = liste('reg_langue_aide', [(tr('reg_langue_auto'), 'auto'), ('Français', 'fr'), ('English', 'en')])
        self.langue.setCurrentIndex(max(0, self.langue.findData(r['langue'])))
        f.addRow(tr('reg_langue'), self.langue)
        self.noms = liste('reg_noms_aide', [(tr('reg_langue_auto'), 'auto'), ('Français', 'fr'), ('English', 'en')])
        self.noms.setCurrentIndex(max(0, self.noms.findData(r['langue_noms'])))
        f.addRow(tr('reg_noms'), self.noms)
        self.apparence = liste('reg_apparence_aide', [(tr('reg_apparence_clair'), 'clair'),
                                                      (tr('reg_apparence_sombre'), 'sombre')])
        self.apparence.setCurrentIndex(max(0, self.apparence.findData(r['apparence'])))
        f.addRow(tr('reg_apparence'), self.apparence)
        h = QHBoxLayout()
        self.dest = champ('reg_dest_aide', r['dossier_sortie'] or str(config.dossier_sortie_defaut() / 'OHP_DU_ECU'))
        h.addWidget(self.dest, 1)
        h.addWidget(bouton('reg_parcourir', self._parcourir))
        f.addRow(tr('reg_dest'), h)
        self.format = liste('reg_format_aide', [(tr('fmt_xisf'), 'xisf'), (tr('fmt_fz'), 'fz'), (tr('fmt_fits'), 'fits')])
        self.format.setCurrentIndex(max(0, self.format.findData(r['format_sortie'])))
        f.addRow(tr('reg_format'), self.format)
        self.dl = nombre('reg_dl_aide', 0, 4, int(r['telechargements_max'] or 0), 'reg_auto')
        f.addRow(tr('reg_dl'), self.dl)
        self.conv = nombre('reg_conv_aide', 0, 16, int(r['conversions_max'] or 0), 'reg_auto')
        f.addRow(tr('reg_conv'), self.conv)
        self.debit = decimal('reg_debit_aide', 0.5, 20.0, float(r['debit_max_mo_s'] or 8.0), 'unite_mos')
        f.addRow(tr('reg_debit'), self.debit)
        self.eco = case('reg_econome', bool(r['mode_econome']))
        f.addRow('', self.eco)
        self.maj = case('reg_maj', bool(r['maj_auto']))
        f.addRow('', self.maj)
        self.nouveautes = case('reg_nouveautes', bool(r['ohp_verifier_nouveautes']))
        f.addRow('', self.nouveautes)
        self.nouv_heures = nombre('reg_nouveautes_heures_aide', 1, 720, int(r['ohp_nouveautes_heures'] or 24))
        self.nouv_heures.setSuffix(' ' + tr('unite_heures'))
        f.addRow(tr('reg_nouveautes_heures'), self.nouv_heures)
        # disposition gardée d'une fermeture à l'autre (interface.json) : on peut toujours revenir à l'origine
        self.disposition_reinitialisee = False
        h = QHBoxLayout()
        h.addWidget(bouton('reg_disposition_reinit', self._reinitialiser_disposition))
        h.addStretch(1)
        f.addRow(tr('reg_disposition'), h)
        racine.addWidget(_boutons(self))
        adaptatif.ajuster(self, 820, 520, cle='reglages')
        adaptatif.assouplir(self)
        from . import memoire
        memoire.onglets(self.onglets, 'dialogues.reglages_onglet')

    def _onglet_sources(self):
        from ..core import sources
        w = QWidget()
        v = QVBoxLayout(w)
        intro = QLabel(tr('reg_sources_intro'))
        intro.setWordWrap(True)
        v.addWidget(intro)
        g = QGridLayout()
        self.champs_sources = {}
        self.origines = {}
        for i, (cle, (val, origine)) in enumerate(sources.toutes().items()):
            g.addWidget(QLabel(cle), i, 0)
            e = champ('reg_source_aide', val)
            self.champs_sources[cle] = e
            g.addWidget(e, i, 1)
            o = QLabel(tr('sources_origine_' + origine))
            self.origines[cle] = o
            g.addWidget(o, i, 2)
            g.addWidget(bouton('reg_source_defaut', lambda _=False, k=cle: self._defaut(k)), i, 3)
            g.addWidget(bouton('reg_source_tester', lambda _=False, k=cle: self._tester(k)), i, 4)
        v.addLayout(g)
        h = QHBoxLayout()
        h.addWidget(bouton('reg_sources_reinit', self._tout_defaut))
        h.addWidget(bouton('reg_sources_distant', self._distant))
        h.addStretch(1)
        v.addLayout(h)
        v.addStretch(1)
        return w

    def _actualiser_sources(self):
        from ..core import sources
        for cle, (val, origine) in sources.toutes().items():
            self.champs_sources[cle].setText(val)
            self.origines[cle].setText(tr('sources_origine_' + origine))

    def _defaut(self, cle):
        from ..core import sources
        sources.forcer(cle, None)
        self._actualiser_sources()

    def _tout_defaut(self):
        from ..core import sources
        sources.tout_reinitialiser()
        self._actualiser_sources()

    def _distant(self):
        from ..core import sources
        t = Tache(sources.rafraichir_distant, parent=self)     # requête réseau : jamais dans le fil graphique
        t.quand_fini(lambda ok: (QMessageBox.information(self, tr('reg_onglet_sources'),
                                                         tr('sources_distant_ok' if ok else 'sources_distant_non')),
                                 self._actualiser_sources()))
        self._t_distant = t
        t.start()

    def _enregistrer_sources(self):
        from ..core import sources
        for cle, e in self.champs_sources.items():
            if e.text().strip() != sources.valeur(cle):
                sources.forcer(cle, e.text().strip())

    def _tester(self, cle):
        from ..core import sources
        self._enregistrer_sources()
        t = Tache(sources.tester, cle, parent=self)
        t.quand_fini(lambda r: QMessageBox.information(
            self, cle, tr('sources_test_ok' if r[0] else 'sources_test_echec', cle=cle, detail=r[1][:200])))
        self._t_test = t
        t.start()

    def _parcourir(self):
        d = QFileDialog.getExistingDirectory(self, tr('reg_dest'), self.dest.text())
        if d:
            self.dest.setText(d)

    def _reinitialiser_disposition(self):
        """Fenêtre, colonnes, séparateurs, filtres, onglets et dossiers des dialogues reviennent à l'origine ;
        les réglages de cette fenêtre (langue, thème, dossier de sortie…) ne changent pas."""
        if QMessageBox.question(self, tr('reg_disposition'), tr('reg_disposition_question')) != \
                QMessageBox.StandardButton.Yes:
            return
        self.disposition_reinitialisee = True
        self.accept()

    def accept(self):
        r = config.reglages()
        ancienne = r['langue']
        r['langue'] = self.langue.currentData()
        r['langue_noms'] = self.noms.currentData()
        r['dossier_sortie'] = self.dest.text().strip()
        r['format_sortie'] = self.format.currentData()
        r['telechargements_max'] = self.dl.value()
        r['conversions_max'] = self.conv.value()
        r['debit_max_mo_s'] = self.debit.value()
        r['mode_econome'] = self.eco.isChecked()
        r['maj_auto'] = self.maj.isChecked()
        r['ohp_verifier_nouveautes'] = self.nouveautes.isChecked()
        r['ohp_nouveautes_heures'] = self.nouv_heures.value()
        if r['apparence'] != self.apparence.currentData():
            r['apparence'] = self.apparence.currentData()
            from . import theme
            theme.appliquer(nom=r['apparence'])
        self._enregistrer_sources()
        self.langue_changee = ancienne != r['langue']
        super().accept()


# ======================================================================== ASTAP
class DialogueASTAP(QDialog):
    """Assistant : état, guide d'installation pour ce système, recherche, choix manuel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('astapdlg_titre'))
        v = QVBoxLayout(self)
        self.etat = QLabel()
        self.etat.setWordWrap(True)
        self.etat.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(self.etat)
        h = QGridLayout()                          # 2 × 2 : tient sur un écran étroit
        h.addWidget(bouton('astapdlg_chercher', self.actualiser), 0, 0)
        h.addWidget(bouton('astapdlg_choisir_exe', self.choisir_exe), 0, 1)
        h.addWidget(bouton('astapdlg_choisir_cat', self.choisir_cat), 1, 0)
        h.addWidget(bouton('astapdlg_oublier', self.oublier), 1, 1)
        h.setColumnStretch(2, 1)
        v.addLayout(h)
        self.guide = navigateur('', 'astapdlg_guide_aide')
        v.addWidget(self.guide, 1)
        v.addWidget(_boutons(self, ok=True, annuler=False))
        adaptatif.ajuster(self, 780, 640, cle='astap')
        adaptatif.assouplir(self)
        self.actualiser()

    def actualiser(self):
        """Détection (sous-processus « astap_cli -h », parcours de dossiers) hors du fil graphique."""
        from ..core import astap
        r = config.reglages()
        self.etat.setText(tr('astapdlg_recherche'))
        self._t = Tache(astap.detecter, r['astap_executable'], r['astap_catalogue'], parent=self)
        self._t.quand_fini(self._afficher)
        self._t.start()

    def _afficher(self, e):
        couleur = '#2C7A55' if e.utilisable else '#B5382B'
        lignes = ['<b style="color:%s">%s</b>' % (couleur, html.escape(tr(e.message_cle())))]
        lignes.append('%s : %s' % (tr('astap_executable'), html.escape(e.executable or '—')))
        if e.version:
            lignes.append('%s : %s' % (tr('astap_version'), html.escape(e.version)))
        lignes.append('%s : %s' % (tr('astap_catalogue'), html.escape(
            '%s (%d %s) — %s' % (e.catalogue.upper(), e.catalogue_fichiers, tr('astap_tuiles'), e.catalogue_dossier)
            if e.catalogue else '—')))
        if not e.utilisable:
            lignes.append('<i>%s</i>' % html.escape(tr('astap_sans_effet')))
        self.etat.setText(adaptatif.coupable('<br>'.join(lignes)).replace('<br\u200b>', '<br>').replace('</\u200b', '</'))
        self.guide.setHtml(guide_astap_html())

    def choisir_exe(self):
        from . import memoire
        actuel = config.reglages()['astap_executable']
        depart = os.path.dirname(actuel) if actuel and os.path.isabs(actuel) else memoire.dossier('astap_exe')
        f, _ = QFileDialog.getOpenFileName(self, tr('astapdlg_choisir_exe'), depart)
        if f:
            memoire.retenir('astap_exe', f, est_fichier=True)
            config.reglages()['astap_executable'] = f
            self.actualiser()

    def choisir_cat(self):
        from . import memoire
        d = QFileDialog.getExistingDirectory(self, tr('astapdlg_choisir_cat'),
                                             config.reglages()['astap_catalogue'] or memoire.dossier('astap_cat'))
        if d:
            memoire.retenir('astap_cat', d)
            config.reglages()['astap_catalogue'] = d
            self.actualiser()

    def oublier(self):
        config.reglages()['astap_executable'] = ''
        config.reglages()['astap_catalogue'] = ''
        self.actualiser()


def guide_astap_html() -> str:
    from ..core import astap
    c = astap.conseils_installation()
    e = html.escape
    p = ['<h3>%s</h3>' % e(tr('astap_guide_titre', systeme=tr('os_' + c['systeme']), arch=c['arch'],
                                famille=(' (' + c['famille'] + ')') if c['famille'] else '')),
         '<p>%s</p>' % e(tr('astap_guide_pourquoi')), '<p>%s</p>' % e(tr('astap_guide_catalogue')), '<ol>']
    liens = ''.join('<li><a href="%s">%s</a></li>' % (e(u), e(tr(k))) for k, u in c['programme'])
    if c['cli'] and all(u != c['cli'] for _, u in c['programme']):
        liens += '<li><a href="%s">%s</a></li>' % (e(c['cli']), e(tr('astap_lien_cli_zip')))
    p.append('<li>%s<ul>%s</ul></li>' % (e(tr('astap_guide_programme')), liens))
    p.append('<li>%s<ul>%s</ul></li>' % (e(tr('astap_guide_cat')),
                                         ''.join('<li><a href="%s">%s</a></li>' % (e(u), e(tr(k)))
                                                 for k, u in c['catalogue'])))
    for et in c['etapes']:
        p.append('<li>%s</li>' % e(tr(et, dossier=c['dossier'])))
    p.append('</ol><p>%s</p>' % e(tr('astap_guide_detection')))
    p.append('<p><a href="%s">%s</a></p>' % (e(c['page']), e(tr('astap_guide_page', page=c['page']))))
    return ''.join(p)


# ======================================================================== à propos
def texte_configuration() -> str:
    """Texte « configuration détectée ».  Sondes système et ASTAP : à appeler hors du fil graphique
    (les dialogues le font par une Tache) ; `machine.detecter()` est mis en cache après le premier appel."""
    from ..core import astap, machine
    m = machine.detecter()
    r = config.reglages()
    a = astap.detecter(r['astap_executable'], r['astap_catalogue'])
    gpu = ', '.join('%s [%s]' % (c.nom, c.fabricant) for c in m.cartes) or tr('gpu_aucune')
    return tr('apropos_config', os='%s %s (%s)' % (m.nom_systeme, m.version_systeme, m.architecture),
              cpu=m.processeur, p=m.coeurs_physiques, l=m.coeurs_logiques,
              ram='%.1f' % (m.memoire_totale_mo / 1024), gpu=gpu, python=platform.python_version(),
              astap=tr(a.message_cle()) + ((' — ' + a.executable) if a.executable else ''))


class DialogueAPropos(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('apropos_titre'))
        v = QVBoxLayout(self)
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        self._gabarit = '<h2>Coupole %s</h2><p>%s</p><p>%s</p><pre>%%s</pre><p>%s</p>' % (
            __version__, html.escape(tr('apropos_texte')), html.escape(tr('apropos_credits')),
            html.escape(tr('apropos_licence')))
        self._qt = '\nQt %s / PyQt %s' % (QT_VERSION_STR, PYQT_VERSION_STR)
        self.navig = navigateur(self._gabarit % html.escape(tr('astapdlg_recherche')), 'apropos_aide')
        v.addWidget(self.navig)
        v.addWidget(_boutons(self, ok=True, annuler=False))
        adaptatif.ajuster(self, 640, 560, cle='apropos')
        adaptatif.assouplir(self)
        self._t = Tache(texte_configuration, parent=self)      # sondes : hors du fil graphique
        self._t.quand_fini(lambda txt: self.navig.setHtml(self._gabarit % html.escape(txt + self._qt)))
        self._t.start()


# ======================================================================== signalement
class DialogueSignaler(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('signaler_titre'))
        v = QVBoxLayout(self)
        l = QLabel(tr('signaler_texte'))
        l.setWordWrap(True)
        v.addWidget(l)
        self.texte = aide(QPlainTextEdit(), 'signaler_zone_aide')
        v.addWidget(self.texte, 1)
        self.diag = case('signaler_diag', True)
        v.addWidget(self.diag)
        h = QHBoxLayout()
        h.addWidget(bouton('signaler_fichier', self.fichier))
        h.addStretch(1)
        h.addWidget(bouton('dlg_annuler', self.reject))
        self.b_env = bouton('signaler_envoyer', self.envoyer)
        h.addWidget(self.b_env)
        v.addLayout(h)
        adaptatif.ajuster(self, 560, 420, cle='signaler')
        adaptatif.assouplir(self)

    def _rapport(self, diagnostic: str = ''):
        champs = {'description': self.texte.toPlainText()[:4000]}
        if self.diag.isChecked():
            champs['diagnostic'] = diagnostic
        return champs

    def _avec_diagnostic(self, suite):
        """Le diagnostic (sondes système, ASTAP) se calcule hors du fil graphique, puis `suite(texte)`."""
        if not self.diag.isChecked():
            suite('')
            return
        self.b_env.setEnabled(False)
        self._t = Tache(texte_configuration, parent=self)
        self._t.quand_fini(lambda txt: (self.b_env.setEnabled(True), suite(txt)))
        self._t.quand_erreur(lambda e: (self.b_env.setEnabled(True), suite(e)))
        self._t.start()

    def envoyer(self):
        from ..core import rapports
        if rapports.consentement() is not True:
            if QMessageBox.question(self, tr('signaler_titre'), tr('signaler_consentement')) != \
                    QMessageBox.StandardButton.Yes:
                return
            rapports.definir_consentement(True)

        def suite(diag):
            rapports.envoyer('manuel', **self._rapport(diag))
            QMessageBox.information(self, tr('signaler_titre'), tr('signaler_envoye'))
            self.accept()
        self._avec_diagnostic(suite)

    def fichier(self):
        from ..core import rapports
        from . import memoire
        f, _ = QFileDialog.getSaveFileName(self, tr('signaler_fichier'),
                                           os.path.join(memoire.dossier('signaler'), 'coupole-rapport.json'),
                                           'JSON (*.json)')
        if not f:
            return
        memoire.retenir('signaler', f, est_fichier=True)

        def suite(diag):
            r = rapports.machine()
            r.update(self._rapport(diag))
            r['genre'] = 'manuel'
            try:
                config.ecrire_json_atomique(f, r)
            except OSError as e:
                QMessageBox.warning(self, tr('signaler_titre'), tr('erreur_ecriture', chemin=f, erreur=str(e)))
                return
            QMessageBox.information(self, tr('signaler_titre'), tr('ecrit', chemin=f))
        self._avec_diagnostic(suite)


# ======================================================================== raccourcis, aide d'écran
RACCOURCIS = [('F1', 'racc_f1'), ('Shift+F1', 'racc_manuel'), ('Ctrl+1 … Ctrl+9', 'racc_modules'),
              ('Ctrl+,', 'racc_reglages'), ('Ctrl+Shift+A', 'racc_astap'), ('Ctrl+Shift+D', 'racc_apparence'),
              ('Ctrl+R', 'racc_actualiser'),
              ('Ctrl+Q', 'racc_quitter')]


def afficher_raccourcis(parent):
    lignes = ''.join('<tr><td><b>%s</b></td><td>&nbsp;&nbsp;%s</td></tr>' % (html.escape(k), html.escape(tr(c)))
                     for k, c in RACCOURCIS)
    d = QDialog(parent)
    d.setWindowTitle(tr('racc_titre'))
    v = QVBoxLayout(d)
    v.addWidget(navigateur('<table>%s</table>' % lignes, 'racc_aide'))
    v.addWidget(_boutons(d, ok=True, annuler=False))
    adaptatif.ajuster(d, 460, 300, cle='raccourcis')
    adaptatif.assouplir(d)
    d.exec()


def afficher_aide(parent, titre: str, texte: str):
    d = QDialog(parent)
    d.setWindowTitle(tr('aide_ecran_titre', ecran=titre))
    v = QVBoxLayout(d)
    v.addWidget(navigateur(texte, 'aide_ecran_aide'))
    v.addWidget(_boutons(d, ok=True, annuler=False))
    adaptatif.ajuster(d, 640, 520, cle='aide')
    adaptatif.assouplir(d)
    d.exec()


def ouvrir_fichier(chemin: str):
    QDesktopServices.openUrl(QUrl.fromLocalFile(chemin))


# ======================================================================== mise à jour
def verifier_maj(parent, silencieux=False):
    """Vérifie en arrière-plan ; ne dérange que s'il y a une nouvelle version (ou sur demande)."""
    from ..core import maj
    t = Tache(maj.verifier, __version__, parent=parent)
    if hasattr(parent, 'statusBar') and not silencieux:
        parent.statusBar().showMessage(tr('maj_verification', depot=maj.depot()), 4000)

    def fini(m):
        if not m:
            if not silencieux:
                QMessageBox.information(parent, tr('maj_titre'), tr('maj_aucune', version=__version__))
            return
        notes = maj.notes_dans_la_langue(m['notes'], i18n.langue())[:3000]
        genre = maj.type_installation()
        if genre == 'pip':
            QMessageBox.information(parent, tr('maj_titre'), tr('maj_disponible', version=m['version']) + '\n\n' +
                                    tr('maj_pip', commande=maj.commande_pip()) + '\n\n' + notes)
            return
        if genre != 'paquet':                   # paquet système (.deb) : signaler et ouvrir la page, ne rien écrire
            c = maj.consigne_systeme(m)
            b = QMessageBox(QMessageBox.Icon.Information, tr('maj_titre'),
                            tr('maj_disponible', version=m['version']) + '\n\n' +
                            tr('maj_systeme', url=c['url'], commande=c['commande']) + '\n\n' + notes, parent=parent)
            ouvrir = b.addButton(tr('maj_ouvrir_page'), QMessageBox.ButtonRole.AcceptRole)
            ouvrir.setToolTip(tr('maj_ouvrir_page_aide'))
            b.addButton(QMessageBox.StandardButton.Close)
            b.exec()
            if b.clickedButton() is ouvrir:
                QDesktopServices.openUrl(QUrl(c['url']))
            return
        if QMessageBox.question(parent, tr('maj_titre'), tr('maj_question', version=m['version']) + '\n\n' + notes) \
                != QMessageBox.StandardButton.Yes:
            return
        t2 = Tache(maj.appliquer, m, parent=parent)
        t2.quand_fini(lambda _: (QMessageBox.information(parent, tr('maj_titre'), tr('maj_redemarrer')),
                                 maj.relancer(), parent.close()))
        t2.quand_erreur(lambda e: QMessageBox.warning(parent, tr('maj_titre'), tr('maj_echec', erreur=e)))
        parent._tache_maj2 = t2
        t2.start()

    def erreur(e):
        if not silencieux:
            QMessageBox.warning(parent, tr('maj_titre'), tr('maj_echec', erreur=e))
    t.quand_fini(fini)
    t.quand_erreur(erreur)
    parent._tache_maj = t
    t.start()
