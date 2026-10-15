"""Navigation par modules (0.6.0), mêmes contenus et mêmes règles que Coupole Web : données importées (24 modules,
517 questions, fiches, tables, schémas, images), moteur des questions identique au web (empreintes), sauvegarde
commune (cas de parité avec src/contenu/sauvegarde.ts), schémas sans recouvrement (chasses estimées et mesure Qt),
règle typographique, rendu hors écran de toutes les questions, pages (accueil, module, question, recherche, Mes
modules, progression), fenêtres de ressources, export / import / réinitialisation, réglages des animations gardés."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

from coupole.modules.anim.classe import contenu
from coupole.modules.anim.classe import sauvegarde as S

ICI = Path(__file__).parent


def test_modules_et_ressources_completes():
    from coupole.modules.anim import catalogue
    ms = contenu.modules()
    assert len(ms) == 24 and sum(m['affiche'] for m in ms) == 22
    assert len(contenu.toutes_les_questions()) == 517
    for m in ms:
        for a in m['animations']:
            assert a in catalogue.PAR_ID, (m['cle'], a)
        for f in m['fiches']:
            assert contenu.fiche(f), f
        for t in m['tables']:
            assert contenu.table(t), t
        for i in m['images']:
            assert contenu.image(i), i
        for q in m['questions']:
            assert re.fullmatch(r'[WGCD]\d+', q['n']) and (not q['ok'] or contenu.question(q['id']))
    for i in contenu._images().values():
        if i['nature'] == 'photo':
            assert contenu.chemin_image(i['id']).exists() and i.get('credit') and i.get('licence'), i['id']


def test_moteur_identique_au_web():
    from coupole.modules.anim.classe.moteur_questions import instancier, json_canonique
    ref = json.loads((ICI / 'classe_banque_empreintes.json').read_text('utf-8'))
    macros = contenu.macros()
    n = 0
    for c in ref['cas']:
        q = contenu.question(c['id'])
        inst = instancier(q, c['graine'], c['parametres'], c['langue'], macros=macros)
        assert hashlib.sha256(json_canonique(inst).encode()).hexdigest() == c['sha256'], c['id']
        n += 1
    assert n > 5000


def _rejouer(c):
    e, g = c['entree'], c['genre']
    ex = (lambda s: None if s is None else S.exporter(s))
    if g == 'migrer':
        return ex(S.migrer(e['brut'], e['application']))
    if g == 'importer':
        return ex(S.importer(e['texte'], 'app'))
    if g == 'fusionner':
        return ex(S.fusionner(e['a'], e['b']))
    if g == 'reinitialiser':
        return ex(S.reinitialiser(e['s'], e['partie']))
    if g == 'bilan':
        return S.bilan(e['s'], e['questions'])
    if g == 'etat':
        return S.etat_question(e['s'], e['qid'])
    if g == 'reglages':
        return S.json_js(S.reglages_valides(e['entree']))
    s, res = S.migrer(e['depart']), []
    for o in e['operations']:
        f = {'creer': lambda: S.creer_module(s, o['nom'], o['elements'], o['id'], o['quand']),
             'nom_libre': lambda: S.nom_libre(s, o['base'], o['numeroter']),
             'renommer': lambda: S.renommer_module(s, o['id'], o['nom'], o['quand']),
             'ajouter': lambda: S.ajouter_element(s, o['id'], o['element'], o['quand']),
             'deplacer': lambda: S.deplacer_element(s, o['id'], o['de'], o['vers'], o['quand']),
             'retirer': lambda: S.retirer_element(s, o['id'], o['element'], o['quand']),
             'supprimer': lambda: S.supprimer_module(s, o['id']),
             'marquer': lambda: S.marquer(s, o['qid'], o['champ'], o['v']),
             'etat': lambda: S.etat_question(s, o['qid']),
             'tentative': lambda: S.noter_tentative(s, o['qid'], o['t']),
             'bilan': lambda: S.bilan(s, o['questions']),
             'est_favori': lambda: S.est_favori(s, o['genre'], o['id']),
             'ajouter_favori': lambda: S.ajouter_favori(s, o['genre'], o['id'], o['quand']),
             'retirer_favori': lambda: S.retirer_favori(s, o['genre'], o['id']),
             'basculer_favori': lambda: S.basculer_favori(s, o['genre'], o['id'], o['quand'])}[o['op']]
        r = f()
        res.append(None if r is None else json.loads(S.json_js(r)))
    return {'resultats': res, 'final': S.exporter(s)}


def test_sauvegarde_identique_au_web():
    cas = json.loads((ICI / 'sauvegarde_cas.json').read_text('utf-8'))['cas']
    assert len(cas) > 30
    for k, c in enumerate(cas):
        assert _rejouer(c) == c['sortie'], (k, c['genre'])


INTERDITS = [
    (re.compile(r'(?<![^\W\d_])(k?m|cm|g|W|J|K|pc|kpc|Mpc)\s?/\s?(s|s²|m²|m³|cm³|K|Mpc)(?![^\W\d_])'), 'unité à barre oblique'),
    (re.compile(r'10\^'), '« 10^ »'), (re.compile(r'\d[eE][−+-]?\d'), '« e-11 »'),
    (re.compile(r'(?<![\w\-–])-\s?\d|\d\s-\s\d'), '« - » comme moins'),
]


def _textes(v, lg, cle='', out=None):
    out = [] if out is None else out
    if re.fullmatch(r'liens|modules|sources|source|schemas|mots_cles|classaction|statut|questions|animations|fiches|tables|'
                    r'images|verifie|dimensions|octets|id|ref|fichier|url|source_url|licence_url|format|type|t|genre|cle|lien|'
                    r'nature|fond|trait|couleur|ancre|base|src', cle):
        return out
    if isinstance(v, str):
        out.append(v)
    elif isinstance(v, list):
        for x in v:
            _textes(x, lg, cle, out)
    elif isinstance(v, dict):
        if set(v) == {'fr', 'en'}:
            _textes(v[lg], lg, cle, out)
        else:
            for k, x in v.items():
                _textes(x, lg, k, out)
    return out


def test_regle_typographique_ressources_et_questions():
    from coupole.modules.anim.classe.moteur_questions import instancier, variantes
    fautes = []
    objets = list(contenu._lire('fiches').values()) + list(contenu._lire('tables').values()) + \
        list(contenu._lire('schemas').values()) + list(contenu._images().values())
    for lg in ('fr', 'en'):
        for o in objets:
            for s in _textes(o, lg):
                t = re.sub(r'\$[^$]*\$', ' ', s)
                fautes += ['%s (%s) : %s' % (o.get('id'), lg, nom) for r, nom in INTERDITS if r.search(t)]
    macros = contenu.macros()
    for q in contenu.toutes_les_questions().values():
        for v in variantes(q)[:4]:
            for lg in ('fr', 'en'):
                i = instancier(q, '3', v, lg, macros=macros)
                for s in [i['titre'], i['enonce'], i['indice'], i['explication']] + i['elements_de_reponse'] + \
                        [c.get('texte') for c in i['choix']]:
                    if isinstance(s, str):
                        t = re.sub(r'\$[^$]*\$', ' ', s.replace('**', ''))
                        fautes += ['%s (%s) : %s' % (q['id'], lg, nom) for r, nom in INTERDITS if r.search(t)]
    assert fautes[:20] == []


def test_schemas_sans_recouvrement(app_qt):
    from coupole.modules.anim.classe.schema_qt import mesure_affichee, recouvrements
    pb = []
    for i, s in contenu._lire('schemas').items():
        for lg in ('fr', 'en'):
            pb += ['%s (%s) : %s' % (i, lg, x) for x in recouvrements(s, lg)]
    assert pb == []
    # à l'écran (0.7.0) : mesure réelle bornée par la chasse estimée (texte resserré au dessin s'il est plus large dans
    # la police du système) → aucun recouvrement, quels que soient le système et sa police (Windows, macOS, Linux)
    reels = ['%s (%s) : %s' % (i, lg, x) for i, s in contenu._lire('schemas').items() for lg in ('fr', 'en')
             for x in recouvrements(s, lg, mesure_affichee)]
    assert reels == []
    # une police système nettement plus large (×1,4) : toujours aucun recouvrement
    from coupole.modules.anim.classe import schema_qt
    import unittest.mock as um
    with um.patch.object(schema_qt, 'mesure_reelle', lambda t, ta, g=False: 1.4 * schema_qt.largeur_estimee(t, ta, g)):
        assert not [i for i, s in contenu._lire('schemas').items() for lg in ('fr', 'en')
                    if recouvrements(s, lg, schema_qt.mesure_affichee)]


def test_rendu_de_toutes_les_questions_et_ressources(app_qt):
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QImage, QPainter
    from coupole.modules.anim.classe import figure_qt, schema_qt
    from coupole.modules.anim.classe.moteur_questions import instancier
    img = QImage(640, 420, QImage.Format.Format_ARGB32)
    macros = contenu.macros()
    for q in contenu.toutes_les_questions().values():
        i = instancier(q, '1', None, 'fr', macros=macros)
        for fig in [i['figure'], i['figure_indice']] + [c.get('figure') for c in i['choix']]:
            if fig:
                p = QPainter(img)
                figure_qt.peindre(p, fig, QRectF(0, 0, 640, 420), 'sombre', True, True, i['bonnes'])
                p.end()
    for s in contenu._lire('schemas').values():
        p = QPainter(img)
        schema_qt.peindre(p, s, QRectF(0, 0, 640, 420), 'clair', 'en')
        p.end()


def test_pages_et_progression(app_qt, tmp_path, monkeypatch):
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import PageModule, PageProgression, PageQuestion, PageRecherche, VueClasse
    from coupole.modules.anim.classe.ressources_qt import fenetres_ouvertes, fermer_toutes, ouvrir_ressource
    v = VueClasse()
    v.resize(1200, 800)
    v.aller_module('intro', False)
    assert isinstance(v.pile.currentWidget(), PageModule) and v.pile.currentWidget().onglets.count() == 5
    v.aller_question('intro', 'ca_intro_scale', False)
    pq = v.pile.currentWidget()
    assert isinstance(pq, PageQuestion) and pq.inst['bonnes'] == ['A']
    pq.choisir('B')
    pq.valider()
    assert S.etat_question(ST.stockage().doc, 'ca_intro_scale') == 'ratee'
    pq.b_reponse.click()
    assert ST.stockage().doc['questions']['ca_intro_scale']['reponse_vue']
    # précédente / suivante : W → G → C → D, en boucle
    pq.b_suiv.click()
    assert v.pile.currentWidget().qid == 'ca_intro_increasingdist'
    v.retour()
    assert v.pile.currentWidget().qid == 'ca_intro_scale'
    # écrit sur disque, atomique, avec la version précédente
    assert ST.stockage().ecrire() and ST.stockage().ecrire()
    assert ST.stockage().chemin.with_name('sauvegarde.json.prec').exists()
    assert json.loads(ST.stockage().chemin.read_text('utf-8'))['format'] == 'coupole-sauvegarde'
    # recherche FR/EN (questions, animations, fiches…)
    v.aller_recherche('density')
    pr = v.pile.currentWidget()
    assert isinstance(pr, PageRecherche) and len({r['doc']['g'] for r in pr.resultats()}) >= 2
    assert '<b style=' in pr.vue_res.toHtml() or 'font-weight' in pr.vue_res.toHtml()
    # fenêtres de ressources : plusieurs à la fois, une seule par ressource
    ouvrir_ressource('fiche', 'intro_density')
    ouvrir_ressource('table', 'densities')
    ouvrir_ressource('table', 'densities')
    ouvrir_ressource('image', 'startrails')
    assert len(fenetres_ouvertes()) == 3
    fermer_toutes()
    # progression, export, réinitialisation avec copie et annulation, import (fusion)
    v.aller_progression()
    assert isinstance(v.pile.currentWidget(), PageProgression)
    ch = tmp_path / 'export.json'
    ST.stockage().exporter_vers(ch)
    avant = S.exporter(ST.stockage().doc)
    from PyQt6.QtWidgets import QMessageBox
    monkeypatch.setattr(QMessageBox, 'exec', lambda self: QMessageBox.StandardButton.Yes)
    assert v.effacer({'partie': 'reponses'}, 'test')
    assert ST.stockage().doc['questions'] == {}
    v._annuler()
    assert S.exporter(ST.stockage().doc).replace(ST.stockage().doc['modifie'], '') .count('ca_intro_scale') == avant.count('ca_intro_scale')
    assert v.importer_fichier(str(ch), 'fusionner')
    assert 'ca_intro_scale' in ST.stockage().doc['questions']
    (tmp_path / 'abime.json').write_text('{pas du json')
    monkeypatch.setattr(QMessageBox, 'warning', lambda *a, **k: None)
    assert not v.importer_fichier(str(tmp_path / 'abime.json'), 'remplacer')


def test_mes_modules_et_page_perso(app_qt):
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import PageModule, VueClasse
    s = ST.stockage().doc
    m = S.creer_module(s, 'Séance', [{'genre': 'question', 'id': 'ca_intro_scale'}, {'genre': 'fiche', 'id': 'intro_density'},
                                       {'genre': 'animation', 'id': 'kepler'}])
    ST.stockage().modifie()
    v = VueClasse()
    v.aller_module(m['id'], True)
    p = v.pile.currentWidget()
    assert isinstance(p, PageModule) and p.onglets.count() == 6       # + « Organiser »
    p.liste_org.setCurrentRow(2)
    p._deplacer(-1)
    assert [e['id'] for e in S.trouver_module(s, m['id'])['elements']] == ['ca_intro_scale', 'kepler', 'intro_density']
    p._retirer('fiche', 'intro_density')
    assert len(S.trouver_module(s, m['id'])['elements']) == 2
    v.aller_question(m['id'], 'ca_intro_scale', True)
    assert v.pile.currentWidget().info['n'] == 'G1'


def test_stockage_version_future_et_ancien_format(tmp_path):
    from coupole.modules.anim.classe.stockage import Stockage
    ch = tmp_path / 'futur.json'
    ch.write_text(json.dumps({'format': S.FORMAT, 'version': 99, 'x': 1}))
    st = Stockage(ch)
    assert st.lecture_seule and not st.ecrire()
    assert json.loads(ch.read_text())['version'] == 99            # jamais écrasée
    from coupole.core.etat_interface import etat
    etat().ecrire('modules.anim.kepler.e', 0.5)
    st2 = Stockage(tmp_path / 'neuf.json')
    assert st2.reglages_animation('kepler') == {'e': 0.5}


def test_reglages_des_animations_gardes(app_qt):
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.gui import Panneau
    p = Panneau()
    w = p.ouvrir('kepler')
    assert p.vues.currentIndex() == 1
    cle, (wid, defaut) = next((k, x) for k, x in w._defauts.items() if hasattr(x[0], 'mini'))
    wid.setValue(wid.mini)
    assert ST.stockage().reglages_animation('kepler').get(cle) is not None
    # une autre session : la valeur est reprise de la sauvegarde
    p2 = Panneau()
    w2 = p2.ouvrir('kepler')
    assert abs(w2._defauts[cle][0].value() - wid.mini) < 1e-6


def test_export_import_par_les_dialogues_de_l_application(app_qt, monkeypatch):
    """Exporter et Importer passent par gui/fichiers.py (dialogue natif, parent transmis)."""
    from coupole.gui import fichiers
    from coupole.modules.anim.classe.gui import PageProgression, VueClasse
    vus = []
    monkeypatch.setattr(fichiers, 'choisir_enregistrement', lambda parent, titre, depart='', filtre='': (vus.append(('e', titre, depart)), ('', ''))[1])
    monkeypatch.setattr(fichiers, 'choisir_fichier', lambda parent, titre, depart='', filtre='': (vus.append(('i', titre)), ('', ''))[1])
    v = VueClasse()
    v.aller_progression()
    p = v.pile.currentWidget()
    assert isinstance(p, PageProgression)
    p.exporter()
    p.importer()
    assert [x[0] for x in vus] == ['e', 'i'] and vus[0][2].startswith('coupole-sauvegarde-')
