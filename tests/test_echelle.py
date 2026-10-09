"""Second audit (0.1.4) : comportement à l'échelle de la banque entière et au-delà (×10), budgets de temps.

Les budgets sont volontairement larges (machines d'intégration partagées, Windows lent) : ils ne vérifient pas une
performance fine mais l'absence d'un défaut d'échelle (comparaison Python par paire, appel par ligne dans le fil
graphique, relecture inutile).  Les compteurs (nombre de lectures, d'écritures, de validations) sont, eux, exacts.
"""
import os
import random
import sqlite3
import threading
import time

import numpy as np
import pytest

N = 80_000          # dix fois la banque (7 989 lignes)


def chrono(f, *a, **k):
    t = time.perf_counter()
    r = f(*a, **k)
    return r, time.perf_counter() - t


# ================================================================ tableaux (fil graphique)
@pytest.fixture
def lignes_80k():
    rng = random.Random(1)
    lignes = [(rng.choice(['possédée', 'échec', 'à télécharger']), '2024-%02d-%02d' % (rng.randint(1, 12), rng.randint(1, 28)),
               rng.random() * 1000, 'objet %d' % rng.randint(0, 999), rng.randint(0, 50)) for _ in range(N)]
    return lignes, [{'k': k} for k in range(N)]


def test_tri_de_80000_lignes_sans_comparaison_python(app_qt, lignes_80k):
    from PyQt6.QtCore import Qt
    from coupole.gui.modele import ModeleTableau, vue_tableau
    lignes, donnees = lignes_80k
    m = ModeleTableau(['a', 'b', 'c', 'd', 'e'])
    v, proxy = vue_tableau(m, 'ohp_table_images_aide')
    _, dt = chrono(m.remplir, lignes, donnees)
    assert dt < 0.5
    for col in (2, 1, 0, 4):
        _, dt = chrono(v.sortByColumn, col, Qt.SortOrder.AscendingOrder)
        assert dt < 0.8, (col, dt)
        cles = [m.lignes[r][col] for r in range(0, N, 997)]
        assert cles == sorted(cles)
    # les données suivent leurs lignes
    assert all(m.lignes[r] == lignes[m.donnees[r]['k']] for r in range(0, N, 1013))
    # ordre décroissant, puis ordre d'origine (colonne -1)
    v.sortByColumn(2, Qt.SortOrder.DescendingOrder)
    assert m.lignes[0][2] >= m.lignes[1][2] >= m.lignes[-1][2]
    proxy.sort(-1)
    assert [d['k'] for d in m.donnees[:50]] == list(range(50))
    # un nouveau remplissage reste trié selon le tri choisi
    v.sortByColumn(4, Qt.SortOrder.AscendingOrder)
    m.remplir(lignes[:1000], donnees[:1000])
    assert [m.lignes[r][4] for r in range(1000)] == sorted(l[4] for l in lignes[:1000])
    # les ajouts aussi (qualité : résultats arrivant au fil de l'eau)
    m.ajouter(lignes[1000:2000], donnees[1000:2000])
    assert [m.lignes[r][4] for r in range(2000)] == sorted(l[4] for l in lignes[:2000])


def test_la_selection_suit_le_tri(app_qt, lignes_80k):
    from PyQt6.QtCore import Qt
    from coupole.gui.modele import ModeleTableau, lignes_choisies, vue_tableau
    lignes, donnees = lignes_80k
    m = ModeleTableau(['a', 'b', 'c', 'd', 'e'])
    v, proxy = vue_tableau(m, 'ohp_table_images_aide')
    m.remplir(lignes[:5000], donnees[:5000])
    v.selectRow(10)
    choisie = lignes_choisies(v, proxy, m)[0]
    v.sortByColumn(2, Qt.SortOrder.DescendingOrder)
    assert lignes_choisies(v, proxy, m) == [choisie]


def test_nombres_tries_comme_nombres(app_qt):
    from PyQt6.QtCore import Qt
    from coupole.gui.modele import ModeleTableau, Nombre, vue_tableau
    m = ModeleTableau(['fwhm'])
    v, _ = vue_tableau(m, 'qual_table_aide')
    m.remplir([(Nombre(x),) for x in (10.25, 2.5, 3.0, 100.0)])
    v.sortByColumn(0, Qt.SortOrder.AscendingOrder)
    assert [str(m.lignes[r][0]) for r in range(4)] == ['2.5', '3', '10.25', '100']


def test_modele_paresseux_ne_calcule_que_les_lignes_visibles(app_qt):
    from PyQt6.QtCore import Qt
    from coupole.gui.modele import ModeleParesseux, cle_de_tri, vue_tableau
    appels = {'ligne': 0, 'style': 0}
    objets = [{'t': (k * 7919) % N, 'nom': 'n%05d' % k} for k in range(N)]

    def ligne(x):
        appels['ligne'] += 1
        return ('%d' % x['t'], x['nom'])

    def style(x):
        appels['style'] += 1
        return {}
    m = ModeleParesseux(['t', 'nom'], ligne, style, None, lambda col: (lambda x: (0, x['t'], 0)) if col == 0 else None)
    v, _ = vue_tableau(m, 'ohp_table_images_aide')
    v.resize(600, 400)
    v.show()
    _, dt = chrono(m.remplir_objets, objets)
    app_qt.processEvents()
    assert dt < 0.3 and m.rowCount() == N
    assert appels['ligne'] < 2000                          # quelques dizaines de lignes visibles, pas 80 000
    _, dt = chrono(v.sortByColumn, 0, Qt.SortOrder.AscendingOrder)   # clé rapide fournie
    app_qt.processEvents()
    assert dt < 0.8 and m.donnees[0]['t'] <= m.donnees[1]['t'] <= m.donnees[-1]['t']
    assert appels['ligne'] < 4000
    avant = appels['style']
    m.invalider(lignes=False)                               # thème changé : seulement les styles affichés
    app_qt.processEvents()
    assert appels['style'] - avant < 2000
    assert m.lignes[5] == ligne(m.donnees[5]) and len(m.lignes) == N
    assert cle_de_tri(None) > cle_de_tri('a') > cle_de_tri(3.0)


def test_tout_selectionner_80000_lignes_et_entete(app_qt):
    """« Tout sélectionner » puis redessiner : l'en-tête Qt d'origine parcourait chaque ligne (0,7 s)."""
    from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
    from PyQt6.QtWidgets import QHeaderView, QTableView
    from coupole.gui.modele import EnTete, ModeleTableau, vue_tableau
    m = ModeleTableau(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'])
    v, _ = vue_tableau(m, 'ohp_table_images_aide')
    m.remplir([tuple(range(9))] * N)
    v.resize(900, 500)
    v.show()
    app_qt.processEvents()
    assert isinstance(v.horizontalHeader(), EnTete) and v.horizontalHeader().sectionsClickable()
    v.selectAll()
    t = time.perf_counter()
    app_qt.processEvents()
    v.horizontalHeader().repaint()
    v.viewport().repaint()
    assert time.perf_counter() - t < 0.3
    # même rendu que l'en-tête d'origine (sans sélection, avec indicateur de tri)

    class M(QAbstractTableModel):
        def rowCount(self, p=QModelIndex()):
            return 0 if p.isValid() else 10

        def columnCount(self, p=QModelIndex()):
            return 0 if p.isValid() else 4

        def data(self, i, role=Qt.ItemDataRole.DisplayRole):
            return None

        def headerData(self, s, o, role=Qt.ItemDataRole.DisplayRole):
            return 'Colonne %d' % s if role == Qt.ItemDataRole.DisplayRole and o == Qt.Orientation.Horizontal else None
    images = []
    for perso in (False, True):
        t = QTableView()
        if perso:
            e = EnTete(Qt.Orientation.Horizontal, t)
            e.setSectionsClickable(True)
            t.setHorizontalHeader(e)
        mm = M()
        t.setModel(mm)
        t.setSortingEnabled(True)
        t.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        t.resize(600, 200)
        t.show()
        app_qt.processEvents()
        images.append(t.horizontalHeader().grab().toImage())
    assert images[0] == images[1]
    assert isinstance(images[0], type(images[1])) and QHeaderView is not None


def test_filtre_du_catalogue_80000_objets(app_qt, lignes_80k):
    from PyQt6.QtCore import Qt
    from coupole.gui.modele import ModeleTableau, vue_tableau
    lignes, donnees = lignes_80k
    m = ModeleTableau(['a', 'b', 'c', 'd', 'e'])
    v, proxy = vue_tableau(m, 'ohp_table_objets_aide', filtrable=True)
    m.remplir(lignes, donnees)
    garder = {id(d) for d, l in zip(m.donnees, m.lignes) if l[0] == 'échec'}
    _, dt = chrono(proxy.definir_visibles, garder)
    assert dt < 0.5 and proxy.rowCount() == len(garder)
    v.sortByColumn(2, Qt.SortOrder.AscendingOrder)          # le filtre suit les objets, pas les numéros de ligne
    assert proxy.rowCount() == len(garder)
    assert all(proxy.data(proxy.index(r, 0)) == 'échec' for r in range(0, proxy.rowCount(), 101))
    proxy.definir_visibles(None)
    assert proxy.rowCount() == N


# ================================================================ panneau Banque OHP à 10 × la banque
@pytest.fixture(scope='module')
def inventaire_x10():
    from coupole.modules.ohp.inventaire import Inventaire
    inv = Inventaire.charger()
    base = inv.images
    imgs = []
    for k in range(10):
        for x in base:
            y = dict(x)
            if k:
                y['access_url'] = x['access_url'] + '?k=%d' % k
                y['objet'] = x['objet'] + ' %d' % k if k % 2 else x['objet']
                y['t_min'] = x['t_min'] + k * 1e-4
            imgs.append(y)
    inv.images = imgs
    return inv


def _fermer(panneau):
    """Panneau détruit (et non seulement fermé) : sinon il réagit encore aux gestes des tests suivants (un champ
    qui perd le focus relit la possession et recalcule 80 000 lignes dans le fil graphique d'un autre test)."""
    from PyQt6 import sip
    panneau.close()
    sip.delete(panneau)


def _attendre(app_qt, cond, delai=60):
    fin = time.time() + delai
    while not cond() and time.time() < fin:
        app_qt.processEvents()
        time.sleep(0.005)
    return cond()


def test_catalogue_a_dix_fois_la_banque(app_qt, inventaire_x10, monkeypatch):
    """Tout sélectionner, trier, filtrer, changer de thème : chaque geste reste court dans le fil graphique."""
    from PyQt6.QtCore import Qt
    from coupole.core import config
    from coupole.gui import outils
    from coupole.modules.ohp.gui import Panneau
    from coupole.modules.ohp.possession import Possession
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = Panneau()
    p.resize(1400, 900)
    p.show()
    t0 = time.time()
    while p.inv is None and time.time() - t0 < 30:
        app_qt.processEvents()
        time.sleep(0.01)
    monkeypatch.setattr(outils.Tache, 'start', lambda self: None)     # fil graphique seul
    inv = inventaire_x10
    Panneau.preparer_objets(inv)
    p.possession = Possession.vide()
    _, dt = chrono(p._inventaire_pret, inv)
    assert dt < 2.0, dt
    assert p.m_obj.rowCount() == len(inv.objets())

    def tout():
        p.v_obj.selectAll()
        p._minuteur_choix.stop()
        p._objets_choisis()
        app_qt.processEvents()
    _, dt = chrono(tout)
    assert p.m_img.rowCount() == len(inv.images) and dt < 2.0, dt
    for col in (1, 0, 5):
        _, dt = chrono(p.v_img.sortByColumn, col, Qt.SortOrder.DescendingOrder)
        assert dt < 1.5, (col, dt)
    _, dt = chrono(p.v_img.selectAll)
    app_qt.processEvents()
    assert dt < 0.5
    _, dt = chrono(p.recherche.setText, 'pal')
    assert dt < 0.5 and 0 < p.p_obj.rowCount() < p.m_obj.rowCount()
    p.recherche.setText('')
    _, dt = chrono(p.reglages_changes)                      # thème : couleurs seulement
    assert dt < 1.0, dt
    _fermer(p)


def test_chargement_a_dix_fois_la_banque_sans_gel(app_qt, inventaire_x10, monkeypatch):
    """0.1.5 : chargement réel (fil de fond → fil graphique) de 80 000 lignes, mesuré par un minuteur de 10 ms :
    aucun silence > 100 ms (budget ×3 pour l'intégration continue).  0.1.4 : 0,5–0,8 s (calculs de fond
    simultanés au premier dessin des tables, qui reprenait le GIL à chaque rappel Python)."""
    from PyQt6.QtCore import QTimer
    from coupole.core import config
    from coupole.gui import outils
    from coupole.modules.ohp import inventaire as INV
    from coupole.modules.ohp.gui import Panneau
    inv = inventaire_x10
    for attribut in ('_index_memo', '_cles_memo', '_anom_memo', '_resume_memo'):
        inv.__dict__.pop(attribut, None)                    # tout recalculer, comme au premier lancement
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    monkeypatch.setattr(INV.Inventaire, 'charger', classmethod(lambda cls, rafraichir=False: inv))
    lancees = []
    init = outils.Tache.__init__

    def compter(self, fonction, *a, **k):
        lancees.append(getattr(fonction, '__name__', '?'))
        init(self, fonction, *a, **k)
    monkeypatch.setattr(outils.Tache, '__init__', compter)
    p = Panneau()
    p.resize(1400, 900)
    p.show()
    ecarts, dernier = [], [time.perf_counter()]

    def battement():
        t = time.perf_counter()
        ecarts.append(t - dernier[0])
        dernier[0] = t
    tm = QTimer()
    tm.timeout.connect(battement)
    tm.start(10)
    assert _attendre(app_qt, lambda: p.inv is inv and len(p.ciel.points) > 0 and p.m_anom.rowCount() > 0
                     and not getattr(p, '_etapes', None) and not any(t.isRunning() for t in list(outils._actives)), 120)
    fin = time.time() + 0.3
    while time.time() < fin:
        app_qt.processEvents()
        time.sleep(0.005)
    tm.stop()
    assert p.m_obj.rowCount() == len(inv.objets())
    assert max(ecarts) < 0.3, max(ecarts)
    # carte du ciel, anomalies et possession calculées par le fil de chargement, pas par des fils concurrents
    apres = lancees[lancees.index('charger_et_preparer') + 1:]
    assert not {'points_ciel', 'anomalies_de', 'lire'} & set(apres), apres
    _fermer(p)


def test_tri_heure_du_site_et_drapeaux_80000_lignes(app_qt, inventaire_x10, monkeypatch):
    """0.1.5 : clés entières précalculées au chargement (heure du site, drapeaux), tri numpy : < 150 ms à 80 000
    lignes (budget ×3) ; 0.1.4 : toutes les cellules de la colonne calculées (~0,5–0,7 s)."""
    from PyQt6.QtCore import Qt
    from coupole.core import config
    from coupole.gui import outils
    from coupole.modules.ohp.gui import Panneau
    from coupole.modules.ohp.possession import Possession
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = Panneau()
    p.resize(1400, 900)
    p.show()
    assert _attendre(app_qt, lambda: p.inv is not None, 30)
    monkeypatch.setattr(outils.Tache, 'start', lambda self: None)
    inv = inventaire_x10
    Panneau.preparer_objets(inv)
    p.possession = Possession.vide()
    p._inventaire_pret(inv)
    p.v_obj.selectAll()
    p._minuteur_choix.stop()
    p._objets_choisis()
    app_qt.processEvents()
    assert p.m_img.rowCount() == len(inv.images)
    calculees = len(p.m_img._c_lignes)
    for col in (2, 7, 2, 7, 0, 4, 5, 6, 8):
        for ordre in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            _, dt = chrono(p.v_img.sortByColumn, col, ordre)
            assert dt < 0.45, (col, ordre, dt)
    assert len(p.m_img._c_lignes) - calculees < 2000           # aucune colonne calculée en entier pour trier
    _fermer(p)


def test_cles_de_tri_des_images_donnent_l_ordre_des_cellules(app_qt, inventaire, monkeypatch):
    """Chaque clé rapide de la table des images rend EXACTEMENT l'ordre (stable) de la valeur affichée triée par
    `cle_de_tri`, sur la banque réelle (dates, heures du site, drapeaux, possession…), croissant et décroissant."""
    from PyQt6.QtCore import Qt
    from coupole.core import config
    from coupole.gui import outils
    from coupole.gui.modele import cle_de_tri
    from coupole.modules.ohp.gui import Panneau
    from coupole.modules.ohp.possession import Possession
    monkeypatch.setitem(config.reglages().valeurs, 'ohp_verifier_nouveautes', False)
    p = Panneau()
    assert _attendre(app_qt, lambda: p.inv is not None, 30)
    monkeypatch.setattr(outils.Tache, 'start', lambda self: None)
    imgs = [dict(x) for x in inventaire.images]
    for k, x in enumerate(imgs):                     # variété : drapeaux « nouveau », image sans site connu
        if k % 7 == 0:
            x['nouveau'], x['vu_le'] = True, '2026-0%d-01' % (1 + k % 3)
        if k % 11 == 0:
            x['site'] = 'inconnu'
    inv = type(inventaire).__new__(type(inventaire))
    inv.__dict__.update({a: v for a, v in inventaire.__dict__.items() if not a.endswith('_memo')})
    inv.images = imgs
    Panneau.preparer_objets(inv)
    statuts = {}
    for k, x in enumerate(imgs[:3000]):
        statuts[x['access_url']] = ('ok', 'doublon', 'echec')[k % 3]
    poss = Possession.vide()
    monkeypatch.setattr(Possession, 'statut', lambda self, x: statuts.get(x['access_url'], 'absente'))
    p.possession = poss
    p._inventaire_pret(inv)
    p.v_obj.selectAll()
    p._minuteur_choix.stop()
    p._objets_choisis()
    m = p.m_img
    assert m.rowCount() == len(imgs)
    for col in (0, 2, 4, 5, 6, 7, 8, 2, 7):
        for ordre in (Qt.SortOrder.AscendingOrder, Qt.SortOrder.DescendingOrder):
            avant = list(m.donnees)
            p.v_img.sortByColumn(col, ordre)
            attendu = sorted(avant, key=lambda x: cle_de_tri(p._ligne_image(x)[col]),
                             reverse=ordre == Qt.SortOrder.DescendingOrder)
            assert [id(x) for x in m.donnees] == [id(x) for x in attendu], (col, ordre)
    p.v_img.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    assert [x['t_min'] for x in m.donnees] == sorted(x['t_min'] for x in imgs)
    _fermer(p)


def test_permutation_triee_identique_a_sorted():
    from coupole.gui.modele import permutation_triee
    rng = random.Random(3)
    for cles in ([rng.randint(0, 50) for _ in range(5000)], [rng.choice([0.5, -0.0, 0.0, 2.25, float('inf')])
                                                               for _ in range(5000)],
                 [rng.randint(0, 9) for _ in range(500)], [(rng.randint(0, 3), 'a') for _ in range(3000)],
                 [rng.random() for _ in range(3000)] + [float('nan')], [2 ** 70, 1] * 1000):
        for dec in (False, True):
            assert permutation_triee(cles, dec) == sorted(range(len(cles)), key=cles.__getitem__, reverse=dec)




# ================================================================ carte du ciel, tracé
def test_carte_du_ciel_8000_points(app_qt):
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QColor, QMouseEvent
    from coupole.gui.cartes import CarteCiel
    rng = np.random.default_rng(2)
    c = CarteCiel()
    c.resize(1400, 800)
    c.show()
    pts = [(float(ra), float(de), 3.0, QColor('#E07B39'), 'p%d' % k, k)
           for k, (ra, de) in enumerate(zip(rng.uniform(0, 360, 8000), rng.uniform(-80, 80, 8000)))]
    _, dt = chrono(lambda: (c.definir(pts), c.repaint()))
    assert dt < 0.6, dt

    def survol():
        for k in range(20):
            pos = QPointF(100 + 50 * k, 300)
            c.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove, pos, pos, Qt.MouseButton.NoButton,
                                         Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier))
    _, dt = chrono(survol)
    assert dt < 0.3, dt
    x, y = (float(v) for v in c._px(pts[123][0], pts[123][1]))
    assert c._proche(QPointF(x + 0.5, y)) is not None


def test_trace_le_survol_ne_redessine_pas_la_courbe(app_qt, monkeypatch):
    from PyQt6.QtCore import QEvent, QPointF, Qt
    from PyQt6.QtGui import QMouseEvent
    from coupole.gui.trace import Trace
    t = Trace()
    t.resize(1200, 600)
    t.show()
    x = np.linspace(1, 2, 1_000_000)
    t.definir(x, np.sin(x * 50), 'x', 'y')
    t.repaint()
    n = {'fond': 0}
    orig = Trace._dessiner_fond
    monkeypatch.setattr(Trace, '_dessiner_fond', lambda self, p: (n.__setitem__('fond', n['fond'] + 1), orig(self, p)))
    for k in range(10):
        pos = QPointF(200 + 40 * k, 200)
        t.mouseMoveEvent(QMouseEvent(QEvent.Type.MouseMove, pos, pos, Qt.MouseButton.NoButton, Qt.MouseButton.NoButton,
                                     Qt.KeyboardModifier.NoModifier))
        t.repaint()
    assert n['fond'] == 0
    t.resize(1000, 500)
    app_qt.processEvents()
    t.repaint()
    assert n['fond'] == 1


# ================================================================ calculs vectorisés : mêmes résultats
def _medoide_par_paire(v2):
    from coupole.core.astro import sep_deg
    best, bn = v2[0], -1
    for a in v2:
        n = sum(1 for b in v2 if sep_deg(a[0], a[1], b[0], b[1]) < max(a[2], 0.2))
        if n > bn:
            best, bn = a, n
    return best


def test_attentes_vectorisees_identiques(inventaire):
    from coupole.modules.ohp import astrometrie
    med, medo = astrometrie.attentes(inventaire.images)
    pos = {}
    for x in inventaire.images:
        if not x['doublon']:
            pos.setdefault(astrometrie.cle_groupe(x), []).append((x['s_ra'], x['s_dec'], x['s_fov']))
    for k in list(pos)[:40]:
        v = pos[k]
        v2 = v[::len(v) // 400 + 1] if len(v) > 400 else v
        b = _medoide_par_paire(v2)
        assert medo[k] == (b[0], b[1], len(v))


def _grouper_par_paire(items):
    from coupole.core.astro import ecart_angle, sep_deg
    from coupole.modules.ohp.lots import TOL_ANGLE, TOL_ECHELLE

    def compatibles(a, b):
        fov = a['nx'] * a['echelle'] / 3600
        return (sep_deg(a['ra'], a['dec'], b['ra'], b['dec']) < fov / 4 and
                ecart_angle(a['angle'], b['angle']) < TOL_ANGLE and a['parite'] == b['parite'] and
                abs(a['echelle'] / b['echelle'] - 1) < TOL_ECHELLE)
    reste, groupes = list(items), []
    while reste:
        echant = reste if len(reste) <= 600 else reste[::len(reste) // 600 + 1]
        best = max(echant, key=lambda a: sum(1 for b in echant if compatibles(a[1], b[1])))
        g = [it for it in reste if compatibles(best[1], it[1])]
        if best not in g:
            g.append(best)
        ids = {id(it) for it in g}
        reste = [it for it in reste if id(it) not in ids]
        groupes.append(g)
    groupes.sort(key=lambda g: (-len(g), min(it[1]['mjd'] for it in g)))
    return groupes


def test_groupement_des_champs_vectorise_identique():
    from coupole.modules.ohp.lots import grouper_champs
    rng = np.random.default_rng(5)
    items = []
    for k in range(700):                         # 3 pointages, deux orientations, une parité inversée, du bruit
        c = k % 3
        items.append(('i%d' % k, {'ra': 10 + 0.3 * c + rng.normal(0, 0.01), 'dec': 20 + rng.normal(0, 0.01),
                                  'angle': (0 if k % 5 else 180) + rng.normal(0, 1), 'parite': -1 if k % 97 else 1,
                                  'echelle': 0.77 * (1 + rng.normal(0, 0.003)), 'nx': 1024, 'mjd': 60000 + k}))
    attendu = [[i for i, _ in g] for g in _grouper_par_paire(items)]
    obtenu, dt = chrono(grouper_champs, items)
    assert [[i for i, _ in g] for g in obtenu] == attendu
    assert dt < 2.0


# ================================================================ E/S : rangement, base d'état, journal
def _destination(tmp_path, inventaire, n=60):
    """Destination simulée : n images « ok » d'objets fixes (solution validée) dans _traitement/converties."""
    from coupole.modules.ohp.conversion import ident, info_de_base
    from coupole.modules.ohp.pilote import Etat
    xs = [x for x in inventaire.images if x['cat'] in ('neb', 'gal', 'amas') and not x['doublon']][:n]
    conv = tmp_path / '_traitement' / 'converties'
    conv.mkdir(parents=True)
    e = Etat(str(tmp_path / '_traitement' / 'etat.sqlite'))
    for k, x in enumerate(xs):
        f = conv / (ident(x) + '.xisf')
        f.write_bytes(b'x')
        info = dict(info_de_base(x), staging=str(f), final=None, extension='.xisf', wcs='validee', ra=x['s_ra'],
                    dec=x['s_dec'], echelle=0.77, angle=0.0, parite=-1, nx=1024, ny=1024, filtre='R',
                    filtre_sys='', filtre_dossier='R', debut='2024-01-01T00:00:%02d' % (k % 60), pose=30.0,
                    mjd=x['t_min'])
        e.ecrire(ident(x), x['access_url'], 'ok', info)
    e.fermer()
    return xs


def test_ranger_une_seconde_fois_n_ecrit_ni_ne_parcourt_rien(tmp_path, inventaire, monkeypatch):
    from coupole.core import config
    from coupole.core.parallele import Plan
    from coupole.modules.ohp import lots
    from coupole.modules.ohp.pilote import Traitement
    _destination(tmp_path, inventaire)
    t = Traitement(str(tmp_path), inventaire, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    try:
        index = t.ranger()
        assert index and (tmp_path / 'INDEX_LOTS.csv').exists()
        lot = tmp_path / index[0][0] / 'LOT.txt'
        assert lot.exists()
        ecritures, parcours, exists = [], [], []
        vrai = config.ecrire_atomique
        monkeypatch.setattr(config, 'ecrire_atomique', lambda c, *a, **k: (ecritures.append(str(c)), vrai(c, *a, **k))[1])
        monkeypatch.setattr(os, 'walk', lambda *a, **k: (parcours.append(a), iter(()))[1])
        vrai_exists = os.path.exists
        monkeypatch.setattr(os.path, 'exists', lambda c: (exists.append(c), vrai_exists(c))[1])
        index2 = t.ranger()
        assert index2 == index
        # seul journal.csv est réécrit : ni LOT.txt, ni INDEX_LOTS.csv, ni parcours de l'arborescence, et aucun
        # test d'existence par fichier rangé
        assert [os.path.basename(c) for c in ecritures] == ['journal.csv'], ecritures
        # un test d'existence par lot (LOT.txt), aucun par fichier rangé, aucun parcours de l'arborescence
        assert parcours == [] and len(exists) <= len(index) + 5, len(exists)
        monkeypatch.undo()
        # un LOT.txt effacé à la main est récrit au rangement suivant
        lot.unlink()
        t.ranger()
        assert lot.exists()
        # empreintes oubliées (destination d'une version précédente) : contenu recomparé, rien de récrit s'il est égal
        os.remove(tmp_path / '_traitement' / lots.FICHIER_EMPREINTES)
        avant = lot.stat().st_mtime_ns
        t.ranger()
        assert lot.stat().st_mtime_ns == avant
    finally:
        t.fermer()


def test_ranger_remet_en_place_et_nettoie_les_dossiers_quittes(tmp_path, inventaire):
    from coupole.core.parallele import Plan
    from coupole.modules.ohp.pilote import Traitement
    _destination(tmp_path, inventaire, 20)
    t = Traitement(str(tmp_path), inventaire, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    try:
        t.ranger()
        i, info = t.etat.ok()[0]
        final = info['final']
        vieux = tmp_path / 'ancien' / 'sous'
        vieux.mkdir(parents=True)
        os.replace(final, vieux / 'f.xisf')
        (vieux / 'LOT.txt').write_text('x')
        t.etat.ecrire(i, info['url'], 'ok', dict(info, final=str(vieux / 'f.xisf')))
        t.ranger()
        assert os.path.exists(final) and not (tmp_path / 'ancien').exists()
    finally:
        t.fermer()


class _CompteValidations:
    def __init__(self, db):
        self.db, self.n = db, 0

    def execute(self, *a):
        return self.db.execute(*a)

    def commit(self):
        self.n += 1
        self.db.commit()

    def close(self):
        self.db.close()


def test_base_d_etat_validations_groupees(tmp_path):
    from coupole.modules.ohp.pilote import Etat
    chemin = str(tmp_path / '_traitement' / 'etat.sqlite')
    e = Etat(chemin, 1.0)
    e.db = c = _CompteValidations(e.db)
    for k in range(300):
        e.ecrire('id%d' % k, 'u', 'ok', {'k': k})
        e.empreinte('sha%d' % k, 'id%d' % k)
    assert c.n <= 2                                         # et non 600
    assert e.lire('id299')[0] == 'ok'                       # la même connexion voit tout
    e._derniere -= 2
    e.valider_si_du()                                       # délai écoulé : tout est sur le disque
    autre = sqlite3.connect(chemin)
    assert autre.execute('SELECT COUNT(*) FROM images').fetchone()[0] == 300
    autre.close()
    e.ecrire('dernier', 'u', 'ok', {})
    e.fermer()                                              # la fermeture valide ce qui reste
    autre = sqlite3.connect(chemin)
    assert autre.execute("SELECT COUNT(*) FROM images WHERE id='dernier'").fetchone()[0] == 1
    autre.close()
    e = Etat(chemin)                                        # délai 0 : une validation par écriture (comme avant)
    e.db = c = _CompteValidations(e.db)
    e.ecrire('x', 'u', 'ok', {})
    assert c.n == 1
    e.fermer()


def test_journal_tamponne(tmp_path, monkeypatch):
    import builtins
    from coupole.modules.ohp.pilote import Journal
    j = Journal(str(tmp_path), 1.0)
    ouvertures = []
    vrai = builtins.open
    monkeypatch.setattr(builtins, 'open', lambda f, *a, **k: (ouvertures.append(f), vrai(f, *a, **k))[1])
    for k in range(200):
        j.ecrire('jrn_pause')
    assert len([o for o in ouvertures if str(o).endswith('JOURNAL.txt')]) <= 1
    j.vider()
    monkeypatch.undo()
    assert (tmp_path / 'JOURNAL.txt').read_text(encoding='utf-8').count('\n') == 200


def test_doublons_de_la_banque_notes_en_une_passe(tmp_path, inventaire, monkeypatch):
    """`lancer` notait chaque doublon par une lecture + une validation : 12,5 s pour 144 doublons sur un partage."""
    from coupole.core.parallele import Plan
    from coupole.modules.ohp import pilote
    t = pilote.Traitement(str(tmp_path), inventaire, Plan(1, 1, True, ''), {'format': 'xisf', 'langue': 'fr'})
    lectures = []
    vrai = t.etat.lire
    monkeypatch.setattr(t.etat, 'lire', lambda i: (lectures.append(i), vrai(i))[1])
    dbl = [x for x in inventaire.images if x['doublon']]
    t.arret.set()                                           # rien à télécharger : seulement la prise en compte
    t.lancer(dbl)
    t.fermer()
    assert lectures == []
    e = pilote.Etat(str(tmp_path / '_traitement' / 'etat.sqlite'))
    assert sum(1 for s in e.statuts().values() if s == 'doublon') == len({pilote.ident(x) for x in dbl})
    e.fermer()


# ================================================================ réorganiser : index, parallélisme, arrêt
def test_rattachement_par_index_et_non_par_parcours(inventaire):
    from coupole.modules.ohp import reorganisation as R
    idx, dt = chrono(R.index_par_fichier, inventaire)
    assert dt < 1.0
    x = inventaire.images[100]
    nom = x['access_url'].rsplit('/', 1)[-1]
    assert x in idx[nom]
    a = {'chemin': '/x/f.xisf', 'raison': '', 'source': nom, 'date_obs': None, 'nx': 0, 'ny': 0, 'sol': None,
         'statut': None, 'objet_entete': None, 'taille': 10}
    y, info, raison = R.rattacher_analyse(a, idx)
    assert raison == '' and y['access_url'].rsplit('/', 1)[-1] == nom and info['octets_sortie'] == 10
    assert R.rattacher_analyse(dict(a, source='inconnu.fits'), idx)[2] == 'inconnu_inventaire'
    assert R.rattacher_analyse(dict(a, raison='illisible'), idx)[2] == 'illisible'


def test_inventorier_parallele_identique_et_arret(tmp_path, inventaire, monkeypatch):
    from coupole.core import xisf
    from coupole.modules.ohp import reorganisation as R
    xs = [x for x in inventaire.images if not x['doublon']][:40]
    for k, x in enumerate(xs):
        d = tmp_path / ('d%d' % (k % 4))
        d.mkdir(exist_ok=True)
        xisf.ecrire(str(d / ('f%02d.xisf' % k)), np.zeros((8, 8), '<u2'), [('EXPTIME', '1.0', '')],
                    proprietes=[('OHP:Source:URL', 'String', x['access_url'])])
    (tmp_path / '_traitement').mkdir()
    (tmp_path / '_traitement' / 'ignore.xisf').write_bytes(b'x')
    seq = R.inventorier(str(tmp_path), inventaire, '/nulle/part', processus=1)
    monkeypatch.setattr(R, 'SEUIL_PROCESSUS', 4)
    vus = []
    par = R.inventorier(str(tmp_path), inventaire, '/nulle/part', progression=lambda f, n: vus.append((f, n)),
                        processus=2)
    assert [(c, x['access_url']) for c, x, _ in seq[0]] == [(c, x['access_url']) for c, x, _ in par[0]]
    assert len(seq[0]) == 40 and seq[1] == par[1] == [] and vus[-1] == (40, 40)
    arret = threading.Event()
    arret.set()
    trouves, _ = R.inventorier(str(tmp_path), inventaire, '/nulle/part', arret=arret, processus=2)
    assert len(trouves) < 40


# ================================================================ parcours parallèle
def test_parcours_parallele_comme_os_walk(tmp_path):
    from coupole.core import parcours
    for a in range(5):
        for b in range(4):
            d = tmp_path / ('A%d' % a) / ('B%d' % b)
            d.mkdir(parents=True)
            for k in range(3):
                (d / ('img%d.xisf' % k)).write_bytes(b'x')
            (d / 'note.txt').write_text('x')
    (tmp_path / '_traitement').mkdir()
    (tmp_path / '_traitement' / 'cache.xisf').write_bytes(b'x')
    attendu = {}
    for d, sous, fs in os.walk(tmp_path):
        sous[:] = [s for s in sous if s != '_traitement']
        im = sorted(os.path.join(d, f) for f in fs if f.endswith('.xisf'))
        if im:
            attendu[d] = im
    assert parcours.lister(tmp_path, ('.xisf',)) == dict(sorted(attendu.items()))
    assert parcours.lister(tmp_path / 'absent', ('.xisf',)) == {}


# ================================================================ qualité : un seul parcours, cache en une requête
@pytest.fixture
def petit_dossier(tmp_path):
    from coupole.core import xisf
    from .synthetique import image
    for lot in range(3):
        d = tmp_path / ('O%d' % lot) / 'R'
        d.mkdir(parents=True)
        for k in range(12):
            a = image(n=96, fwhm=3.0, etoiles=4, seed=lot * 100 + k, fond=500.0, bruit=8.0)
            xisf.ecrire(str(d / ('2025-%04d.xisf' % k)), np.clip(a, 0, 65535).astype('<u2'), [('EXPTIME', '30.0', '')])
    return tmp_path


def test_qualite_plan_repris_sans_relire_le_disque(petit_dossier, monkeypatch):
    from coupole.modules.qualite import mesures as M, moteur, rapport
    if not M.disponible():
        pytest.skip('sep absent')
    from coupole.core.parallele import Plan
    plan = Plan(1, 2, False, 'x')
    ecritures = []
    vrai = rapport.ecrire
    monkeypatch.setattr(rapport, 'ecrire', lambda d, l, txt=True: (ecritures.append((d, txt)), vrai(d, l, txt))[1])
    b = moteur.Mesureur(petit_dossier, plan, None).lancer()
    assert b['mesurees'] == 36 and not b['annule']
    # QUALITE.csv : au plus quelques écritures par lot (et non une par image : O(n²) octets sur un gros lot)
    par_lot = {}
    for d, _ in ecritures:
        par_lot[d] = par_lot.get(d, 0) + 1
    assert len(par_lot) == 3 and max(par_lot.values()) <= 4, par_lot
    # relance avec le plan du dialogue : ni stat, ni requête par image
    p = moteur.planifier(petit_dossier, None)
    assert p['deja'] == 36 and p['a_mesurer'] == 0 and len(p['connus']) == 36
    stats = []
    monkeypatch.setattr(moteur, '_empreinte', lambda f: stats.append(f) or (0, 0.0))
    monkeypatch.setattr(moteur.CacheMesures, 'lire', lambda *a: pytest.fail('lecture du cache par image'))
    b = moteur.Mesureur(petit_dossier, plan, None, plan_dossier=p, ecrire_rapports=False).lancer()
    assert b['deja'] == 36 and b['mesurees'] == 0 and stats == []
    # autre échantillon : seulement re-sélectionné, rien n'est relu
    b = moteur.Mesureur(petit_dossier, plan, 2, plan_dossier=p, ecrire_rapports=False).lancer()
    assert b['n'] == 6 and stats == []


def test_cache_qualite_validations_groupees(tmp_path):
    from coupole.modules.qualite import moteur
    c = moteur.CacheMesures(tmp_path, 1.0)
    c.db = compte = _CompteValidations(c.db)
    for k in range(200):
        c.ecrire('/f%d' % k, 1, 2.0, {'k': k})
    assert compte.n <= 1
    c.fermer()
    c = moteur.CacheMesures(tmp_path)
    assert c.compte() == 200 and len(c.tout()) == 200
    c.fermer()
