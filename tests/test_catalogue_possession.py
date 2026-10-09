"""0.1.8 — voir ce qu'on possède (Banque OHP) : pastille et couleur de chaque objet, colonne « possédé » visible,
résumé de la possession, listes vides qui s'expliquent, dossier de sortie changé → possession recalculée.

Retour d'usage : avec la banque complète déjà téléchargée, « À télécharger seulement » vidait bien les listes…
sans rien dire, et la colonne « possédé » était hors de vue : on croyait que rien ne marchait.
"""
import time

import pytest

from coupole.modules.ohp.conversion import ident
from coupole.modules.ohp.possession import Possession


def attendre(app, cond, delai=30):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    return cond()


# ================================================================ états agrégés (sans interface)
@pytest.mark.parametrize('compte, etat', [
    ({'possedees': 9, 'doublons': 3, 'echecs': 0, 'absentes': 0, 'total': 12}, 'complet'),   # doublons compris
    ({'possedees': 4, 'doublons': 1, 'echecs': 0, 'absentes': 5, 'total': 10}, 'partiel'),
    ({'possedees': 0, 'doublons': 0, 'echecs': 0, 'absentes': 10, 'total': 10}, 'absente'),
    ({'possedees': 8, 'doublons': 0, 'echecs': 1, 'absentes': 1, 'total': 10}, 'echec'),     # l'échec prime
    ({'possedees': 0, 'doublons': 0, 'echecs': 2, 'absentes': 0, 'total': 2}, 'echec'),
    ({'possedees': 0, 'doublons': 0, 'echecs': 0, 'absentes': 0, 'total': 0}, 'absente'),
])
def test_etat_agrege_d_un_objet(compte, etat):
    assert Possession.etat_agrege(compte) == etat


def test_etats_simules_sur_l_inventaire(inventaire):
    """Tout possédé, partiel, rien, échec : sur de vraies images de la banque."""
    objets = {}
    for x in inventaire.images:
        if not x['doublon']:
            objets.setdefault(x['objet'], []).append(x)
    noms = [o for o, l in sorted(objets.items()) if len(l) >= 3][:4]
    a, b, c, d = (objets[n] for n in noms)
    statuts = {ident(x): 'ok' for x in a[:-1]}
    statuts[ident(a[-1])] = 'doublon'                                   # a : tout possédé (un doublon écarté)
    statuts.update({ident(x): 'ok' for x in b[:1]})                     # b : partiel
    statuts.update({ident(x): 'ok' for x in d[:-1]})                    # d : un échec
    statuts[ident(d[-1])] = 'echec'
    poss = Possession('/dest', statuts)
    comptes = poss.compte_objets(inventaire.images)
    assert [Possession.etat_agrege(comptes[n]) for n in noms] == ['complet', 'partiel', 'absente', 'echec']


def test_tri_par_etat():
    from coupole.gui.modele import cle_de_tri
    from coupole.modules.ohp.gui import ProgressionEtat
    vals = [ProgressionEtat(10, 10, 'complet'), ProgressionEtat(0, 10, 'absente'), ProgressionEtat(9, 10, 'echec'),
            ProgressionEtat(5, 10, 'partiel'), ProgressionEtat(2, 10, 'partiel')]
    triees = sorted(vals, key=cle_de_tri)
    assert [(v.etat, v.n) for v in triees] == [('echec', 9), ('absente', 0), ('partiel', 2), ('partiel', 5),
                                               ('complet', 10)]
    assert str(vals[0]) == '10 / 10'


def test_bulle_de_l_etat_d_un_objet(langue):
    from coupole.modules.ohp.gui import Panneau
    c = {'possedees': 9, 'doublons': 3, 'echecs': 0, 'absentes': 0, 'total': 12}
    assert Panneau.bulle_etat_objet(c) == '12 possédées / 12 · 0 à télécharger · 0 échec(s) · 3 doublon(s) écarté(s)'
    langue('en')
    assert Panneau.bulle_etat_objet(c) == '12 owned / 12 · 0 to download · 0 failed · 3 duplicate(s) left out'


# ================================================================ panneau
@pytest.fixture
def panneau(app_qt, monkeypatch):
    from coupole.core import config
    from coupole.modules.ohp.gui import Panneau
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = Panneau()
    p.resize(1300, 800)
    p.show()
    assert attendre(app_qt, lambda: p.inv is not None and p.m_obj.rowCount() > 0)
    # étapes différées du chargement (dont la possession du dossier par défaut) terminées : sinon elles relisent
    # le dossier du champ après la possession simulée par le test
    assert attendre(app_qt, lambda: not getattr(p, '_etapes', None) and getattr(p, '_comptes', None) is not None)
    yield p
    p.arreter()
    p.close()
    p.deleteLater()
    app_qt.processEvents()


def _possession(p, app_qt, dest, statuts):
    """Possession simulée appliquée comme si elle revenait du fil de fond."""
    poss = Possession(dest, statuts)
    p.dest.setText(dest)
    p._possession_prete((poss, [], poss.compte_objets(p.inv.images), p.inv.images))
    app_qt.processEvents()


def test_colonne_possede_apres_le_nom(panneau):
    from coupole.gui import memoire
    h = panneau.v_obj.horizontalHeader()
    assert h.visualIndex(panneau.COL_POSSEDE) == h.visualIndex(panneau.COL_OBJET) + 1
    if not panneau.v_obj.property(memoire.PROPRIETE_LARGEURS):   # largeurs automatiques : visible sans défiler
        panneau.sp_catalogue.setSizes([560, 620])
        assert h.sectionViewportPosition(panneau.COL_POSSEDE) + h.sectionSize(panneau.COL_POSSEDE) <= \
            panneau.v_obj.viewport().width()


def test_ordre_des_colonnes_migre_ou_respecte(app_qt):
    """Ordre d'origine gardé par une version antérieure → nouvel ordre ; ordre choisi à la main → respecté."""
    from PyQt6.QtGui import QStandardItemModel
    from PyQt6.QtWidgets import QTableView
    from coupole.core.etat_interface import etat
    from coupole.gui import memoire

    def vue(cle, gardé):
        etat().ecrire(cle, gardé)
        v = QTableView()
        v.setModel(QStandardItemModel(0, 5))
        h = v.horizontalHeader()
        h.moveSection(h.visualIndex(3), 2)                    # nouvel ordre par défaut : 0 1 3 2 4
        memoire.entete(v, cle, version=2)
        return [h.logicalIndex(i) for i in range(5)]
    assert vue('essai.migration', {'n': 5, 'ordre': [0, 1, 2, 3, 4]}) == [0, 1, 3, 2, 4]
    assert vue('essai.main', {'n': 5, 'ordre': [1, 0, 2, 3, 4]}) == [1, 0, 2, 3, 4]
    assert vue('essai.v2', {'n': 5, 'ordre': [0, 1, 2, 3, 4], 'version': 2}) == [0, 1, 2, 3, 4]


def test_pastille_couleur_et_bulle_de_chaque_objet(panneau, app_qt, inventaire):
    from PyQt6.QtCore import Qt
    from coupole.gui import pastilles
    p = panneau
    par_objet = {}
    for x in inventaire.images:
        if not x['doublon']:
            par_objet.setdefault(x['objet'], []).append(x)
    noms = [o for o, l in sorted(par_objet.items()) if len(l) >= 3][:4]
    a, b, c, d = (par_objet[n] for n in noms)
    statuts = {ident(x): 'ok' for x in a}
    statuts.update({ident(x): 'ok' for x in b[:1]})
    statuts.update({ident(x): 'echec' for x in d[:1]})
    _possession(p, app_qt, '/nas/Astronomie/OHP_DU_ECU', statuts)
    tete = p.v_obj.horizontalHeader().logicalIndex(0)
    attendus = dict(zip(noms, ('ok', 'partiel', 'absente', 'echec')))
    vus = set()
    for r, o in enumerate(p.m_obj.donnees):
        if o['objet'] not in attendus:
            continue
        vus.add(o['objet'])
        nom = attendus[o['objet']]
        assert p.m_obj.data(p.m_obj.index(r, tete), Qt.ItemDataRole.DecorationRole) is not None
        assert p.m_obj.data(p.m_obj.index(r, p.COL_OBJET), Qt.ItemDataRole.ForegroundRole) == \
            pastilles.couleur_statut(nom)
        bulle = p.m_obj.data(p.m_obj.index(r, tete), Qt.ItemDataRole.ToolTipRole)
        assert 'possédées /' in bulle and 'à télécharger' in bulle and 'doublon' in bulle
    assert vus == set(noms)
    # la pastille suit la colonne déplacée en tête
    h = p.v_obj.horizontalHeader()
    h.moveSection(h.visualIndex(p.COL_OBJET), 0)
    app_qt.processEvents()
    r = next(r for r, o in enumerate(p.m_obj.donnees) if o['objet'] == noms[0])
    assert p.m_obj.data(p.m_obj.index(r, p.COL_OBJET), Qt.ItemDataRole.DecorationRole) is not None
    h.moveSection(h.visualIndex(p.COL_OBJET), 1)              # ordre rétabli (il est gardé d'un test à l'autre)
    # légende commune : sous les deux listes (hors du volet des images), avec l'état « en partie »
    assert 'en partie' in p.l_legende.text() and pastilles.couleur_statut('partiel').name() in p.l_legende.text()
    assert p.l_legende.parent() is p.sp_catalogue.parent()


def test_message_quand_aucun_objet_n_est_choisi(panneau, app_qt):
    p = panneau
    p.v_obj.clearSelection()
    p._minuteur_choix.stop()
    p._objets_choisis()
    app_qt.processEvents()
    assert attendre(app_qt, lambda: p.m_img.rowCount() == 0, 5)   # objets cachés → plus d'objet choisi
    assert p.v_img.texte_vide() == 'Choisissez un ou plusieurs objets dans la liste de gauche pour voir leurs images.'
    p.v_img.viewport().grab()                                 # dessiné dans la zone même, sans erreur
    # premier lancement (rien de gardé) : le premier objet est choisi
    p._objets_attendus, p._premier_objet_par_defaut = None, True
    p._restaurer_selection()
    p._minuteur_choix.stop()
    p._objets_choisis()
    app_qt.processEvents()
    assert len(p.v_obj.selectionModel().selectedRows()) == 1 and p.m_img.rowCount() > 0
    assert p.v_img.texte_vide() == ''


def test_tout_deja_telecharge(panneau, app_qt):
    """Toute la banque possédée + « À télécharger seulement » : les deux listes vides le disent, le résumé aussi."""
    p = panneau
    dest = '/mnt/nas/Astronomie/OHP_DU_ECU'
    statuts = {ident(x): 'ok' for x in p.inv.images if not x['doublon']}
    for x in [x for x in p.inv.images if not x['doublon']][:5]:
        statuts[ident(x)] = 'doublon'
    _possession(p, app_qt, dest, statuts)
    texte = p.l_inventaire.text()
    assert 'possédées : ' in texte and '(+ 5 doublons écartés)' in texte and 'à télécharger : 0' in texte, texte
    p.f_manquantes.setChecked(True)
    app_qt.processEvents()
    assert p.p_obj.rowCount() == 0
    assert p.v_obj.texte_vide().replace('​', '') == 'Tout est déjà téléchargé dans ' + dest
    assert attendre(app_qt, lambda: p.m_img.rowCount() == 0, 5)   # objets cachés → plus d'objet choisi
    assert p.v_img.texte_vide().replace('​', '') == 'Tout est déjà téléchargé dans ' + dest
    p.v_obj.viewport().grab()
    # un objet incomplet réapparaît, la liste n'est plus vide
    x = next(x for x in p.inv.images if not x['doublon'])
    del statuts[ident(x)]
    _possession(p, app_qt, dest, statuts)
    assert p.p_obj.rowCount() == 1 and p.v_obj.texte_vide() == ''
    assert 'à télécharger : 1' in p.l_inventaire.text()
    p.f_manquantes.setChecked(False)


def test_resume_en_anglais(panneau, app_qt, langue):
    p = panneau
    langue('en')
    _possession(p, app_qt, '/nas/x', {})
    assert 'owned: 0 (+ 0 duplicates left out)' in p.l_inventaire.text()


def test_changer_de_dossier_relit_la_possession(panneau, app_qt, tmp_path, monkeypatch):
    """Onglet Traitement (champ, Parcourir) ou Préférences : relecture en fond, pastilles, colonne, résumé, et une
    ligne dans la barre d'état."""
    from coupole.core import config
    from .test_possession import etat_simule
    p = panneau
    imgs = [x for x in p.inv.images if x['objet'] == '(914) Palisana']
    utiles = [x for x in imgs if not x['doublon']]
    a, b = tmp_path / 'a', tmp_path / 'b'
    etat_simule(a, imgs, ok=utiles[:2])
    etat_simule(b, imgs, ok=utiles[:7])
    p.dest.setText(str(a))
    p._charger_possession()
    assert attendre(app_qt, lambda: p.possession.dest == str(a) and p._comptes is not None)
    rang = next(r for r, o in enumerate(p.m_obj.donnees) if o['objet'] == '(914) Palisana')
    assert str(p.m_obj.lignes[rang][p.COL_POSSEDE]) == '2 / 10'
    # champ du dossier modifié puis validé
    p.dest.setText(str(b))
    p.dest.editingFinished.emit()
    assert attendre(app_qt, lambda: p.possession.dest == str(b) and
                    str(p.m_obj.lignes[rang][p.COL_POSSEDE]) == '7 / 10')
    assert p.message_possession == 'Possession recalculée : 7 images trouvées dans %s' % b
    assert 'possédées : 7' in p.l_inventaire.text()
    # Préférences : le dossier de sortie change → l'onglet suit et relit
    monkeypatch.setitem(config.reglages().valeurs, 'dossier_sortie', str(b))
    p._prefs_vues = None
    p._suivre_preferences(config.reglages())
    monkeypatch.setitem(config.reglages().valeurs, 'dossier_sortie', str(a))
    p._suivre_preferences(config.reglages())
    assert attendre(app_qt, lambda: p.possession.dest == str(a) and
                    str(p.m_obj.lignes[rang][p.COL_POSSEDE]) == '2 / 10')
    assert p.message_possession == 'Possession recalculée : 2 images trouvées dans %s' % a
    # un résultat périmé (ancien dossier) ne remplace pas le nouveau
    vieux = Possession(str(b), {ident(x): 'ok' for x in utiles})
    p._possession_prete((vieux, [], vieux.compte_objets(p.inv.images), p.inv.images))
    assert p.possession.dest == str(a)
