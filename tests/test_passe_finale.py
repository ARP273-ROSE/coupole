"""Passe finale (0.7.0) : audit fonctionnel automatisé de bout en bout.

- les 517 questions : chaque variante (jusqu'à 3 par question) s'instancie, s'affiche, se note (bonne réponse →
  « réussie », mauvaise → tentative fausse enregistrée), « Montrer la réponse » marque la réponse vue ;
- textes des figures toujours lisibles sur ce qu'il y a dessous (contraste ≥ 3, deux thèmes) ;
- les 96 animations : ouverture, chaque réglage aux bornes et chaque choix, chaque bouton, quelques pas : aucune
  exception, et aucune opération ne prend plus de 100 ms de processeur dans le fil graphique (300 ms en intégration
  continue, machines partagées) ;
- glissers aléatoires (dont valeurs non finies) sur toutes les animations ;
- sauvegarde : export → effacement → import = état identique ; import d'un export de Coupole Web ;
- langue et thème changés à chaud, fenêtres de ressources fermées puis rouvertes, effacement puis changement de
  thème (le plantage de la 0.6.0), fermeture et réouverture (réglages retrouvés) ;
- un module dont la construction échoue ne fait plus tomber l'application.
"""
from __future__ import annotations

import math
import os
import random
import sys
import time

import pytest

from coupole.modules.anim import catalogue
from coupole.modules.anim.classe import contenu
from coupole.modules.anim.classe import sauvegarde as S

BUDGET_MS = 300 if os.environ.get('CI') else 100


def _trace(t, v, tb):
    import traceback
    return ''.join(traceback.format_exception(t, v, tb))[-1500:]


def _attendre(app, s=0.05):
    """Boucle d'événements comme dans l'application, destructions différées comprises (deleteLater : sans elles,
    les panneaux remplacés par un changement de langue s'accumuleraient pendant le test)."""
    from PyQt6.QtCore import QCoreApplication, QEvent
    t0 = time.time()
    while time.time() - t0 < s:
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete.value)


# ------------------------------------------------------------------ questions
def test_toutes_les_questions_se_notent(app_qt):
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import PageQuestion, VueClasse
    from coupole.modules.anim.classe.moteur_questions import variantes
    v = VueClasse()
    v.resize(1100, 760)
    doc = ST.stockage().doc
    n = notees = 0
    for qid, q in contenu.toutes_les_questions().items():
        cle = q['modules'][0]['module']
        pq = PageQuestion(v, cle, qid, False)
        vs = variantes(q)[:3] or [{}]
        for k, var in enumerate(vs):
            if var:
                pq.parametres = {a: b for a, b in var.items()}
                pq._nouvelle()
            inst = pq.inst
            assert inst['enonce'] or inst['figure'], qid
            n += 1
            if pq.ouverte or not inst['choix']:
                continue
            fausses = [c['id'] for c in inst['choix'] if c['id'] not in inst['bonnes']]
            if fausses and k == 0:
                pq.choisir(fausses[0])
                pq.valider()
                assert doc['questions'][qid]['tentatives'][-1]['juste'] is False, qid
                pq._nouvelle()
            for b in inst['bonnes']:
                pq.choisir(b)
            pq.valider()
            assert doc['questions'][qid]['tentatives'][-1]['juste'] is True, (qid, var)
            assert S.etat_question(doc, qid) == 'reussie', qid
            notees += 1
        pq.b_reponse.click()
        assert doc['questions'][qid]['reponse_vue'], qid
        pq.deleteLater()
    app_qt.processEvents()
    assert len(contenu.toutes_les_questions()) == 517 and n >= 517 and notees > 400
    b = S.bilan(doc, list(contenu.toutes_les_questions()))
    assert b['reussies'] >= 400 and b['tentatives'] >= notees


def test_textes_des_figures_lisibles(app_qt):
    """Un texte de figure sans couleur explicite (ou dont la couleur se confond avec le fond peint dessous) prend une
    couleur lisible : 0.7.0, « (B) Voie lactée » noir sur un ovale bleu nuit dans le thème clair."""
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    from coupole.modules.anim.classe import figure_qt
    from coupole.modules.anim.classe.moteur_questions import instancier, variantes
    vus, faibles = [], []
    origine = figure_qt.Peintre.lisible

    def espion(self, jeton, pt):
        c = origine(self, jeton, pt)
        k = self.contraste(c, self.dessous(pt))
        vus.append(k)
        if k < 3:
            faibles.append(round(k, 2))
        return c
    figure_qt.Peintre.lisible = espion
    try:
        img = QImage(520, 340, QImage.Format.Format_ARGB32_Premultiplied)
        macros = contenu.macros()
        for q in contenu.toutes_les_questions().values():
            for var in variantes(q)[:2] or [{}]:
                i = instancier(q, '1', var, 'fr', macros=macros)
                for fig in [i['figure'], i['figure_indice']] + [c.get('figure') for c in i['choix']]:
                    if not fig:
                        continue
                    for th in ('sombre', 'clair'):
                        for rep in (False, True):
                            p = QPainter(img)
                            figure_qt.peindre(p, fig, QRectF(0, 0, 520, 340), th, rep, True, i['bonnes'])
                            p.end()
    finally:
        figure_qt.Peintre.lisible = origine
    assert len(vus) > 5000
    # au plus quelques cas où aucune couleur n'atteint 3 (fond moyen, ni clair ni sombre) : jamais sous 2,5
    assert len(faibles) <= len(vus) // 500 and min(faibles, default=3) >= 2.5, (len(faibles), sorted(faibles)[:10])


# ------------------------------------------------------------------ animations : anti-gel et anti-plantage
def _operations(a):
    from PyQt6.QtWidgets import QCheckBox, QComboBox, QPushButton
    for cle, (w, _defaut) in list(a._defauts.items()):
        if isinstance(w, QCheckBox):
            yield cle, lambda w=w: w.setChecked(not w.isChecked())
            yield cle, lambda w=w: w.setChecked(not w.isChecked())
        elif isinstance(w, QComboBox):
            for k in range(w.count()):
                yield cle, lambda w=w, k=k: w.setCurrentIndex(k)
        elif hasattr(w, 'mini'):
            yield cle, lambda w=w: w.setValue(w.mini)
            yield cle, lambda w=w: w.setValue(w.maxi)
            yield cle, lambda w=w: w.setValue((w.mini + w.maxi) / 2)
    for b in a.findChildren(QPushButton):
        if b.isVisibleTo(a) and b.isEnabled():
            yield 'bouton ' + b.text(), b.click
    for _ in range(3):
        yield 'pas', lambda: a.pas(0.1)
    yield 'reinitialiser', a.reinitialiser


def test_animations_sans_gel_ni_exception(app_qt, monkeypatch):
    from coupole.modules.anim.gui import Panneau
    erreurs = []
    monkeypatch.setattr(sys, 'excepthook', lambda t, v, tb: erreurs.append(_trace(t, v, tb)))
    p = Panneau()
    p.resize(1280, 820)
    p.show()
    app_qt.processEvents()
    lents = []
    for e in catalogue.ENTREES:
        c0 = time.thread_time()
        a = p.ouvrir(e.id)
        app_qt.processEvents()
        a.toile.repaint()
        d = (time.thread_time() - c0) * 1000
        if d > BUDGET_MS * 2:                        # ouverture : module importé et données lues une fois (× 2)
            lents.append((round(d), e.id, 'ouvrir'))
        # trois passages (la liste finit par « Réinitialiser » : chacun repart du même état) ; une opération est
        # lente si elle l'est à chaque fois (une machine partagée ralentit parfois un passage)
        durees = []
        for passage in range(3):
            for k, (nom, f) in enumerate(_operations(a)):
                app_qt.processEvents()
                c0 = time.thread_time()
                f()
                a.toile.repaint()
                app_qt.processEvents()
                d = (time.thread_time() - c0) * 1000
                if passage == 0:
                    durees.append([d, nom])
                elif k < len(durees):
                    durees[k][0] = min(durees[k][0], d)
                assert not erreurs, (e.id, nom, erreurs)
        lents += [(round(d), e.id, nom) for d, nom in durees if d > BUDGET_MS]
        if a.ANIMEE and a.en_lecture:
            a.basculer_lecture()
        a.arreter()
    p.close()
    assert not erreurs, erreurs
    assert not lents, sorted(lents, reverse=True)[:10]


@pytest.mark.parametrize('ident', [e.id for e in catalogue.ENTREES])
def test_glissers_aleatoires_sur_chaque_animation(app_qt, ident, monkeypatch):
    from PyQt6.QtCore import QPointF, Qt
    erreurs = []
    monkeypatch.setattr(sys, 'excepthook', lambda t, v, tb: erreurs.append(_trace(t, v, tb)))
    rng = random.Random(ident)
    a = catalogue.PAR_ID[ident].charger()()
    a.resize(800, 560)
    a.image(700, 460)
    for k in range(60):
        x, y = rng.uniform(-50, 750), rng.uniform(-50, 510)
        a.presser(QPointF(x, y), rng.choice([Qt.MouseButton.LeftButton, Qt.MouseButton.RightButton]))
        dx, dy = rng.choice([rng.gauss(0, 5), rng.gauss(0, 500), 0.0]), rng.gauss(0, 40)
        if k % 17 == 0:
            dx = float('nan') if k % 2 else float('inf')
        a.glisser(QPointF(x + (dx if math.isfinite(dx) else 0), y + dy), dx, dy)
        a.relacher(QPointF(x, y))
        a.survoler(QPointF(rng.uniform(0, 700), rng.uniform(0, 460)))
        a.molette(QPointF(x, y), rng.choice([-240.0, 120.0, 1e6]))
        if k % 10 == 0:
            a.double_clic(QPointF(x, y))
            a.pas(0.05)
            a.image(700, 460)
    img = a.image(700, 460)
    assert not img.isNull()
    a.close()
    assert not erreurs, erreurs


# ------------------------------------------------------------------ sauvegarde
def _etat_rempli():
    from coupole.modules.anim.classe import stockage as ST
    s = ST.stockage().doc
    S.noter_tentative(s, 'ca_intro_scale', {'date': S.maintenant(), 'reponse': ['A'], 'juste': True,
                                            'parametres': {'objet': 'jupiter'}, 'graine': '1'})
    S.noter_tentative(s, 'ca_intro_increasingdist', {'date': S.maintenant(), 'reponse': ['B'], 'juste': False,
                                                     'parametres': {}, 'graine': '1'})
    S.marquer(s, 'ca_intro_increasingdist', 'a_revoir', True)
    S.creer_module(s, 'Séance du jeudi', [{'genre': 'question', 'id': 'ca_intro_scale'},
                                          {'genre': 'animation', 'id': 'kepler'}])
    ST.stockage().memoriser_reglages('kepler', {'e': 0.5})
    ST.stockage().modifie()
    return s


def test_export_effacement_import_etat_identique(app_qt, tmp_path, monkeypatch):
    from PyQt6.QtWidgets import QMessageBox
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import VueClasse
    _etat_rempli()
    avant = S.exporter(ST.stockage().doc)
    ch = tmp_path / 'export.json'
    ST.stockage().exporter_vers(ch)
    v = VueClasse()
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: QMessageBox.StandardButton.Yes)
    assert v.effacer({'partie': 'tout'}, 'test')
    assert ST.stockage().doc['questions'] == {} and ST.stockage().doc['mes_modules'] == []
    assert v.importer_fichier(str(ch), 'remplacer')
    apres = S.exporter(ST.stockage().doc)

    def sans_date(t):
        import json
        d = json.loads(t)
        d.pop('modifie', None)
        return d
    assert sans_date(apres) == sans_date(avant)
    assert ST.stockage().reglages_animation('kepler') == {'e': 0.5}


def test_import_d_un_export_de_coupole_web(app_qt, tmp_path):
    """Un export de Coupole Web (même format, application « coupole-web ») s'importe tel quel au bureau."""
    import json
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import VueClasse
    web = S.migrer({}, 'coupole-web/0.4.0')
    S.noter_tentative(web, 'ca_intro_scale', {'date': '2026-10-14T10:00:00Z', 'reponse': ['A'], 'juste': True,
                                              'parametres': {'objet': 'jupiter'}, 'graine': '1'})
    S.creer_module(web, 'Depuis le web', [{'genre': 'fiche', 'id': 'intro_density'}], 'mm-web', '2026-10-14T10:00:00Z')
    web['animations']['zodiac'] = {'modifie': '2026-10-14T10:00:00Z', 'reglages': {'jour': 172}}
    ch = tmp_path / 'coupole-web.json'
    ch.write_text(S.exporter(web), encoding='utf-8')
    assert json.loads(ch.read_text('utf-8'))['application'].startswith('coupole-web')
    v = VueClasse()
    assert v.importer_fichier(str(ch), 'fusionner')
    s = ST.stockage().doc
    assert S.etat_question(s, 'ca_intro_scale') == 'reussie'
    assert any(m['nom'] == 'Depuis le web' for m in s['mes_modules'])
    assert ST.stockage().reglages_animation('zodiac') == {'jour': 172}


# ------------------------------------------------------------------ fenêtre principale : à chaud
@pytest.fixture
def fenetre(app_qt):
    from coupole.core import config
    config.reglages()['maj_auto'] = False
    config.reglages()['rapports_autorises'] = False
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    yield f
    f.close()
    from coupole.gui.outils import attendre_taches
    attendre_taches()


def test_langue_et_theme_a_chaud_partout(app_qt, fenetre, monkeypatch):
    from coupole.core import config
    erreurs = []
    monkeypatch.setattr(sys, 'excepthook', lambda t, v, tb: erreurs.append(_trace(t, v, tb)))
    p = fenetre.ouvrir_module('anim')
    p.ouvrir('orion3d')
    p.classe.aller_question('intro', 'ca_intro_scale', False)
    from coupole.modules.anim.classe.ressources_qt import fermer_toutes, ouvrir_ressource
    ouvrir_ressource('fiche', 'intro_density')
    ouvrir_ressource('table', 'densities')
    for th, lg in (('clair', 'en'), ('sombre', 'fr'), ('clair', 'fr'), ('sombre', 'en')):
        fenetre.changer_apparence(th)
        fenetre.changer_langue(lg)
        _attendre(app_qt)
        for i in range(fenetre.barre.count()):
            fenetre.barre.setCurrentRow(i)
            _attendre(app_qt, 0.02)
        assert config.reglages()['apparence'] == th
        p = fenetre.ouvrir_module('anim')
        for vue in ('modules', 'mes', 'progression', 'animations'):
            p.montrer(vue)
            _attendre(app_qt, 0.02)
    fermer_toutes()
    fenetre.changer_langue('fr')
    fenetre.changer_apparence(config.DEFAUTS['apparence'])
    assert not erreurs, erreurs


def test_ressources_fermees_rouvertes_et_effacement_puis_theme(app_qt, fenetre, monkeypatch):
    """Le plantage de la 0.6.0 (case « exporter avant » détruite) et les fenêtres de ressources détruites."""
    from PyQt6.QtWidgets import QMessageBox
    from coupole.modules.anim.classe.ressources_qt import fenetres_ouvertes, fermer_toutes, ouvrir_ressource
    erreurs = []
    monkeypatch.setattr(sys, 'excepthook', lambda t, v, tb: erreurs.append(_trace(t, v, tb)))
    p = fenetre.ouvrir_module('anim')
    for k in range(3):
        for g, i in (('fiche', 'intro_density'), ('table', 'densities'), ('image', 'startrails')):
            f = ouvrir_ressource(g, i)
            if k == 1:
                f.close()
                _attendre(app_qt, 0.02)
                ouvrir_ressource(g, i)
        _attendre(app_qt, 0.02)
        assert len(fenetres_ouvertes()) == 3
        fenetre.changer_apparence('clair' if k % 2 else 'sombre')
        fermer_toutes()
        _attendre(app_qt, 0.02)
    _etat_rempli()
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: QMessageBox.StandardButton.Yes)
    for partie in ({'partie': 'reponses'}, {'partie': 'tout'}):
        assert p.classe.effacer(partie, 'test')
        import gc
        gc.collect()
        _attendre(app_qt, 0.05)
        fenetre.changer_apparence('clair')
        fenetre.changer_apparence('sombre')
        _attendre(app_qt, 0.05)
    assert not erreurs, erreurs


def test_fermer_rouvrir_reglages_retrouves(app_qt):
    from coupole.core import config, etat_interface
    from coupole.gui import memoire
    from coupole.gui.fenetre import FenetrePrincipale
    from coupole.modules.anim.classe import stockage as ST
    f = FenetrePrincipale()
    f.show()
    f.resize(1180, 760)
    f.changer_apparence('clair')
    p = f.ouvrir_module('anim')
    w = p.ouvrir('kepler')
    cle, (wid, _d) = next((k, x) for k, x in w._defauts.items() if hasattr(x[0], 'mini'))
    wid.setValue(wid.mini)
    _attendre(app_qt, 0.1)
    f.close()
    ST.stockage().ecrire()
    from coupole.gui.outils import attendre_taches
    attendre_taches()
    etat_interface.reinitialiser_pour_tests()
    memoire.reinitialiser_pour_tests()
    g = FenetrePrincipale()
    g.show()
    _attendre(app_qt, 0.1)
    assert g.panneau_courant() is g.panneau_module('anim')                 # module affiché retrouvé
    assert config.reglages()['apparence'] == 'clair'
    w2 = g.panneau_module('anim').ouvrir('kepler')
    assert abs(w2._defauts[cle][0].value() - wid.mini) < 1e-6
    g.changer_apparence(config.DEFAUTS['apparence'])
    g.close()
    attendre_taches()


def test_module_defectueux_ne_fait_pas_tomber_l_application(app_qt, monkeypatch):
    """0.7.0 : un module dont le panneau lève une exception en cours de construction ; son panneau à moitié construit
    recevait ensuite showEvent/resizeEvent (exception → arrêt de l'application)."""
    from PyQt6.QtWidgets import QLabel, QWidget
    from coupole.core import modules
    erreurs = []
    monkeypatch.setattr(sys, 'excepthook', lambda t, v, tb: erreurs.append(_trace(t, v, tb)))

    class Casse(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            raise RuntimeError('construction ratée')

        def showEvent(self, ev):
            self.attribut_jamais_pose.cassé()

        def resizeEvent(self, ev):
            self.attribut_jamais_pose.cassé()
    m0 = modules.decouvrir()[0]
    orig = modules.Module.classe_gui
    monkeypatch.setattr(modules.Module, 'classe_gui', lambda self: Casse if self is m0 else orig(self))
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.show()
    f.resize(1000, 700)
    f.barre.setCurrentRow(0)
    _attendre(app_qt, 0.1)
    assert isinstance(f.panneaux[0], QLabel)
    assert not f.findChildren(Casse)
    f.close()
    assert not erreurs, erreurs

