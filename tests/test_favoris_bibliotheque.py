"""Favoris, bibliothèque, collections et recherche bilingue au bureau (0.7.1) : mêmes données et même sauvegarde que
Coupole Web (format version 2 : favoris ; « Mes modules » de la version 1 = collections)."""
from __future__ import annotations

import json

from coupole.modules.anim.classe import sauvegarde as S


def _vue(app_qt):
    from coupole.modules.anim.classe import stockage as ST
    from coupole.modules.anim.classe.gui import VueClasse
    return ST, VueClasse()


def test_etoiles_partout_et_page_favoris(app_qt, tmp_path):
    from coupole.modules.anim.classe.gui import PageAccueil, PageFavoris, PageModule, PageQuestion
    from coupole.modules.anim.classe.ressources_qt import fermer_toutes, ouvrir_ressource
    ST, v = _vue(app_qt)
    s = ST.stockage().doc
    s['favoris'].clear()
    # module : bouton étoile (bascule accessible)
    v.aller_module('intro', False)
    pm = v.pile.currentWidget()
    assert isinstance(pm, PageModule) and pm.b_favori.accessibleName().startswith(('Favori', 'Favourite'))
    pm.b_favori.click()
    assert S.est_favori(s, 'module', 'intro') and pm.b_favori.isChecked()
    # question : étoile de l'en-tête
    v.aller_question('intro', 'ca_intro_scale', False)
    pq = v.pile.currentWidget()
    assert isinstance(pq, PageQuestion)
    pq.b_favori.click()
    assert S.est_favori(s, 'question', 'ca_intro_scale')
    # fiche : étoile de la fenêtre ; la liste du module montre l'étoile
    f = ouvrir_ressource('fiche', 'intro_density')
    f.b_favori.click()
    assert S.est_favori(s, 'fiche', 'intro_density')
    fermer_toutes()
    v.aller_module('intro', False, 'fiches')
    liste = v.pile.currentWidget().onglets.widget(2)
    assert not liste.item(0).icon().isNull()
    # Ctrl+D dans une liste : bascule l'élément courant
    liste.setCurrentRow(0)
    liste._basculer_courant()
    assert not S.est_favori(s, 'fiche', 'intro_density')
    liste._basculer_courant()
    # accueil : section « Mes favoris », la plus récente d'abord
    v.aller_accueil()
    assert isinstance(v.pile.currentWidget(), PageAccueil)
    # page des favoris : groupée par type, filtre, tri, retrait
    v.aller_favoris()
    pf = v.pile.currentWidget()
    assert isinstance(pf, PageFavoris)
    assert pf.arbre.topLevelItemCount() == 3
    pf.type.setCurrentIndex(pf.type.findData('question'))
    assert pf.arbre.topLevelItemCount() == 1
    pf.type.setCurrentIndex(0)
    pf.tri.setCurrentIndex(pf.tri.findData('titre'))
    feuille = pf.arbre.topLevelItem(0).child(0)
    pf._retirer(feuille.data(0, 256))
    assert len(s['favoris']) == 2
    # export version 2 avec les favoris ; réinitialisation partielle
    ch = tmp_path / 'e.json'
    ST.stockage().exporter_vers(ch)
    doc = json.loads(ch.read_text('utf-8'))
    assert doc['version'] == 2 and len(doc['favoris']) == 2
    n = S.reinitialiser(s, {'partie': 'favoris'})
    assert n['favoris'] == [] and n['questions'] == s['questions']


def test_bibliotheque(app_qt):
    from coupole.modules.anim.classe.gui import PageBibliotheque
    ST, v = _vue(app_qt)
    s = ST.stockage().doc
    v.aller_bibliotheque()
    pb = v.pile.currentWidget()
    assert isinstance(pb, PageBibliotheque) and pb.onglets.count() == 4
    assert '(517)' in pb.onglets.tabText(0)
    # filtre par module
    pb.module.setCurrentIndex(pb.module.findData('lunarcycles'))
    assert pb.onglets.widget(0).topLevelItemCount() == 1
    # images : vignettes (dessinées aux moments creux)
    pb.onglets.setCurrentIndex(3)
    v.resize(1000, 700)
    v.show()
    for _ in range(40):
        pb._vignette_suivante()
    imgs = pb.onglets.widget(3)
    assert any(not imgs.item(k).icon().isNull() for k in range(imgs.count()) if imgs.item(k).data(256))
    # favoris seulement
    S.ajouter_favori(s, 'image', 'lunareclipse')
    pb.fav.setChecked(True)
    assert pb.total('images') == 1
    v.hide()


def test_collections_et_v1(app_qt, tmp_path):
    from coupole.modules.anim.classe.gui import PageMesModules
    ST, v = _vue(app_qt)
    v1 = {'format': 'coupole-sauvegarde', 'version': 1, 'application': 'coupole/0.7.0', 'modifie': '2026-10-10T10:00:00Z',
          'preferences': {}, 'animations': {}, 'questions': {}, 'modules': {},
          'mes_modules': [{'id': 'mm_lundi', 'nom': 'Cours du lundi', 'cree': '2026-10-01T08:00:00Z',
                           'modifie': '2026-10-01T08:00:00Z', 'elements': [{'genre': 'animation', 'id': 'kepler'}]}]}
    ch = tmp_path / 'v1.json'
    ch.write_text(json.dumps(v1), 'utf-8')
    assert v.importer_fichier(str(ch), 'fusionner')
    v.aller_mes_modules()
    assert isinstance(v.pile.currentWidget(), PageMesModules)
    assert 'Collections' in v.fil.text() or 'Mes favoris' in v.fil.text()
    assert any(m['id'] == 'mm_lundi' for m in ST.stockage().doc['mes_modules'])


def test_recherche_bilingue_page(app_qt):
    from coupole.modules.anim.classe.gui import PageRecherche
    ST, v = _vue(app_qt)
    v.aller_recherche('seasons')
    pr = v.pile.currentWidget()
    assert isinstance(pr, PageRecherche)
    gs = [r['doc']['g'] for r in pr.resultats()]
    assert 'animation' in gs and 'question' in gs
    html = pr.vue_res.toHtml()
    assert 'ouvrir:animation:eclipticsimulator' in html
    pr.fav.setChecked(True)
    assert all(S.est_favori(ST.stockage().doc, r['doc']['g'], r['doc']['id']) for r in pr.resultats())


def test_navigation_panneau(app_qt):
    from coupole.modules.anim.gui import Panneau
    p = Panneau()
    assert set(p.b_vues) == {'modules', 'bibliotheque', 'animations', 'favoris', 'progression'}
    p.montrer('bibliotheque')
    p.montrer('favoris')
    p.montrer('mes')                      # ancien nom : redirigé vers les favoris
    w = p.ouvrir('kepler')
    assert w is not None and not p.b_favori.isHidden() and p.b_favori.i == 'kepler'
    p.arreter()
