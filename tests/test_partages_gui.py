"""Partages du DU (0.8.0) : l'interface, sans écran, et le parcours d'un débutant de bout en bout contre un serveur
WebDAV factice (aucune requête ne sort de la machine).

Premier lancement (guide en trois étapes, rien de choisi) → ajouter un partage → arbre (dates, séries, tableaux) →
liste à droite, bouton bleu « Télécharger (N · X) », clic droit qui commence par « Télécharger » → tableau des mesures
contrôlé (corrections proposées) → outil Parallaxe détecté, paires trouvées → mesure du centre de la Lune sur les
deux images, distance calculée, rapport → dépôt de sa mesure : confirmation qui liste tout ; refus = rien d'envoyé.
"""
import datetime as D
import time

import pytest

from coupole.modules.partages import etat, tableur

from . import partages_exemple as X
from .serveur_webdav import ServeurWebdav

UTC = D.timezone.utc


def attendre(app, cond, delai=30):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app.processEvents()
        time.sleep(0.01)
    return cond()


@pytest.fixture
def serveur():
    fa, _ = X.fits_lune(X.PARIS, X.T_LUNE, 'Observateur A')
    fb, _ = X.fits_lune(X.MARSEILLE, X.T_LUNE, 'Observateur B')
    s = ServeurWebdav({
        '2025/2025-11-03-18-38-26-A.fits': fa,
        '2025/2025-11-03-18-38-26-B.fits': fb,
        '2025/localisations.xlsx': X.classeur(X.lignes_mesures()),
        '17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.png': b'\x89PNG\r\n\x1a\n',
        'Lisez-moi.txt': b'Deposez vos images ici.',
    }, dates={c: D.datetime(2026, 10, 18, 9, tzinfo=UTC).timestamp() for c in (
        '17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.png',)})
    yield s
    s.fermer()


@pytest.fixture
def panneau(app_qt, tmp_path, monkeypatch):
    from coupole.core.etat_interface import etat as etat_ui
    from coupole.gui import memoire
    from coupole.modules.partages.gui import Panneau
    for x in etat.lister():
        etat.retirer(x.ident)
    etat_ui().ecrire('modules.partages.guide_masque', False)
    etat_ui().ecrire('modules.partages.courant', '')
    memoire.retenir('modules.partages.sortie', str(tmp_path / 'sortie'))
    monkeypatch.setenv('COUPOLE_SANS_DIALOGUE', '1')
    p = Panneau()
    p.resize(1100, 680)
    p.show()
    yield p
    p.arreter()
    p.close()
    p.deleteLater()
    app_qt.processEvents()


def _ajouter(p, app_qt, serveur):
    p.ajouter_partage_direct('Défi parallaxe', serveur.lien)
    assert attendre(app_qt, lambda: p.session is not None and p.session.structure is not None
                    and p.arbre.topLevelItemCount() > 0 and p.session.info is not None)


def _noeud(p, app_qt, genre, cle):
    p._choisir_noeud((genre, cle))
    app_qt.processEvents()


def test_premier_lancement(panneau, app_qt):
    p = panneau
    assert p.guide.isVisible() and p.session is None
    assert p.c_partages.count() == 0 and not p.b_telecharger.isEnabled()
    assert 'Ajouter' in p.l_droits.text() or p.l_droits.text()
    assert p.vue.message_vide()                              # la liste vide dit quoi faire
    assert all('1' in lab.text() or '2' in lab.text() or '3' in lab.text() for lab in p.l_etapes)


def test_parcours_debutant(panneau, app_qt, serveur, tmp_path, monkeypatch):
    p = panneau
    _ajouter(p, app_qt, serveur)
    assert 'lire' in p.session.info.droits and p.b_depot.isEnabled()
    textes = [it.text(0) for it in p._items()]
    assert any('2025' in t for t in textes) and any('17 Octobre 2026' in t for t in textes)
    assert any(x.genre == 'tableau' for x in p.session.structure.fichiers)
    # ① dossier 2025 → la liste de droite ; le bouton bleu dit combien et combien d'octets
    _noeud(p, app_qt, 'dossier', '2025')
    assert p.modele.rowCount() == 3 and p.b_telecharger.isEnabled() and '3' in p.b_telecharger.text()
    # ② tableau des mesures : lu, contrôlé
    p.ouvrir_tableau('2025/localisations.xlsx')
    assert attendre(app_qt, lambda: p.modele_m.rowCount() == 5)
    assert p.onglets.currentIndex() == 1 and p.l_mesures.text()
    ligne_b = p._ligne_m(p.modele_m.donnees[1])
    assert '*' in ligne_b[5]                                   # latitude corrigée, marquée
    p.c_a_verifier.setChecked(True)
    assert 0 < p.modele_m.rowCount() < 5
    p.c_a_verifier.setChecked(False)
    # ③ outil Parallaxe détecté, paires trouvées
    o = p.outil_panneau
    assert o is not None and o.outil_id == 'parallaxe'
    o.chercher_paires()
    assert any(x.cible == 'lune' for x in o.paires)
    # ④ télécharger les deux FITS
    fits_ = [f for f in p.session.structure.fichiers if f.genre == 'fits']
    p.telecharger(fits_)
    assert attendre(app_qt, lambda: not p.occupe() and len(p.possedes) == 2, 60)
    p._afficher(fits_)
    assert not p.b_telecharger.isEnabled()                    # déjà là
    # ⑤ mesurer la Lune sur chaque image, calculer
    o.c_cible.setCurrentIndex(o.c_cible.findData('lune'))
    o.c_methode.setCurrentIndex(o.c_methode.findData('deux'))
    o.mesurer(o.a, [fits_[0]])
    o.mesurer(o.b, [fits_[1]])
    assert attendre(app_qt, lambda: o.a.t_points.rowCount() == 1 and o.b.t_points.rowCount() == 1
                    and o.a.e_lat.text() and o.b.e_lat.text(), 60)
    o.calculer()
    assert attendre(app_qt, lambda: o.resultat is not None, 60)
    r = o.resultat
    assert abs(r['distance_geo_km'] - r['distance_geo_eph_km']) / r['distance_geo_eph_km'] < 0.03
    assert o.b_html.isEnabled() and o.resultats.toPlainText()
    from coupole.modules.partages.analyses.parallaxe.rapport import ecrire_html
    rapport = tmp_path / 'rapport.html'
    ecrire_html(str(rapport), r, '', o.notes_rapport())
    contenu = rapport.read_text(encoding='utf-8')
    assert 'data:image/png;base64' in contenu and serveur.jeton not in contenu
    # ⑥ déposer sa mesure : refus d'abord (rien ne part), puis confirmation
    local = tmp_path / 'ma_lune.fits'
    local.write_bytes(fits_[0] and b'SIMPLE  =                    T'.ljust(2880))
    p.l_depot_fichiers.addItem(str(local))
    p.c_depot_dossier.setCurrentIndex(p.c_depot_dossier.findData('2025'))
    p.c_depot_tableau.setCurrentIndex(1)
    for role, v in (('auteur', 'Observateur F'), ('cible', 'Lune'), ('date', '2025-11-03 18:38:27'),
                    ('latitude', '45,0'), ('longitude', '4°30′ E'), ('altitude', '200')):
        p.e_depot[role].setText(v)
    vus = []
    monkeypatch.setattr(p, '_confirmer_html', lambda h, t: vus.append(h) or False)
    avant = dict(serveur.fichiers)
    p.preparer_depot()
    assert attendre(app_qt, lambda: bool(vus))
    assert 'ma_lune.fits' in vus[0] and 'Observateur F' in vus[0] and '2025/localisations.xlsx' in vus[0]
    app_qt.processEvents()
    assert serveur.fichiers == avant and 'PUT' not in serveur.methodes()
    monkeypatch.setattr(p, '_confirmer_html', lambda h, t: True)
    p.preparer_depot()
    assert attendre(app_qt, lambda: '2025/ma_lune.fits' in serveur.fichiers and
                    tableur.lire(serveur.fichiers['2025/localisations.xlsx']).feuille(0).cellules.get((8, 4))
                    is not None, 30)
    assert tableur.lire(serveur.fichiers['2025/localisations.xlsx']).feuille(0).cellules[(8, 7)].valeur == 45.0
    assert serveur.interdites == [] and serveur.ecrasements == []


def test_nouveautes_et_clic_droit(panneau, app_qt, serveur):
    p = panneau
    _ajouter(p, app_qt, serveur)
    assert not p.bandeau.isVisible()                          # première visite : rien de « nouveau »
    serveur.poser('2025/2025-11-03-18-38-40-C.jpg', b'\xff\xd8\xff\xe0')
    p.rafraichir()
    assert attendre(app_qt, lambda: p.bandeau.isVisible())
    _noeud(p, app_qt, 'nouveaux', '')                           # bouton « Voir les nouveautés »
    assert p.selection_noeud() and all(f.nouveau for f in p.selection_noeud())
    p.marquer_vus()
    assert not p.bandeau.isVisible()
    # clic droit : la première action est « Télécharger »
    from PyQt6.QtWidgets import QMenu
    menus = []
    from coupole.gui import ouvrir
    orig = ouvrir.montrer_menu
    ouvrir.montrer_menu = lambda m, pos: menus.append([a.text() for a in m.actions() if a.text()])
    try:
        _noeud(p, app_qt, 'dossier', '2025')
        p.vue.selectRow(0)
        app_qt.processEvents()
        p._menu_fichiers(p.vue.rect().center())
    finally:
        ouvrir.montrer_menu = orig
    assert menus and menus[0][0].startswith(('Télécharger', 'Download'))
    assert isinstance(QMenu, type)


def test_aide_et_langue(panneau, app_qt, serveur, langue):
    p = panneau
    _ajouter(p, app_qt, serveur)
    h = p.aide_html()
    assert 'Banque OHP' in h and 'Parallaxe' in h
    langue('en')
    from coupole.core.i18n import tr
    assert 'OHP' in tr('pt_aide_html') and 'Partage' not in tr('pt_aide_html')
    langue('fr')


def test_erreur_de_lien_lisible(panneau, app_qt, serveur):
    p = panneau
    serveur.mot_de_passe = 'secret'                            # le partage demande un mot de passe
    p.ajouter_partage_direct('Protégé', serveur.lien)
    assert attendre(app_qt, lambda: 'pt_err' not in p.l_etat.text() and p.l_etat.text() != '' and
                    p.b_rafraichir.isEnabled() and p.session is not None and p.session.structure is None
                    and p.l_etat.text() not in ('', ) and 'mot de passe' in p.l_etat.text().lower(), 20)
