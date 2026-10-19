"""Partages du DU (0.8.0) : structure devinée, classeurs (lecture, ajout d'une ligne sans rien toucher d'autre),
tableau des mesures (normalisation et contrôles), textes."""
import datetime as D
import io
import re
import zipfile
from pathlib import Path

import pytest

from coupole.modules.partages import mesures as M
from coupole.modules.partages import structure as S
from coupole.modules.partages import tableur as T

from . import partages_exemple as X

UTC = D.timezone.utc


# ============================================================================================== structure
@pytest.mark.parametrize('nom,attendu', [
    ('2025-11-03-18-38-26-A.fits', [D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC)]),
    ('IMG20260618223000.jpg', [D.datetime(2026, 6, 18, 22, 30, tzinfo=UTC)]),
    ('ISS_20251018_050430.png', [D.datetime(2025, 10, 18, 5, 4, 30, tzinfo=UTC)]),
    ('ISS-26-10-17-04-29-11.204-ABC.fit', [D.datetime(2026, 10, 17, 4, 29, 11, 204000, tzinfo=UTC),
                                           D.datetime(2017, 10, 26, 4, 29, 11, 204000, tzinfo=UTC)]),
    ('compte-rendu.pdf', []),
])
def test_instants_du_nom(nom, attendu):
    assert S.instants_du_nom(nom) == attendu


def test_ambiguite_tranchee_par_la_date_de_depot():
    depot = D.datetime(2026, 10, 18, 9, 0, tzinfo=UTC).timestamp()
    assert S.instant_du_nom('17-10-26-04-29-11-Nom.fit', depot).date() == D.date(2026, 10, 17)
    assert S.instant_du_nom('26-10-17-04-29-11-Nom.fit', depot).date() == D.date(2026, 10, 17)


def test_dossiers_observateurs_cibles():
    assert S.date_du_dossier('17 Octobre 2026') == D.date(2026, 10, 17)
    assert S.date_du_dossier('1er mars 2026') == D.date(2026, 3, 1)
    assert S.date_du_dossier('2025') == D.date(2025, 1, 1) and S.annee_seule('2025')
    assert S.decouper_dossier('17-10-2026 - Lyon - Observateur C') == {
        'date': D.date(2026, 10, 17), 'lieu': 'Lyon', 'observateur': 'Observateur C'}
    assert S.observateur_du_nom('ISS-26-10-17-04-29-11.204-ABC.fit') == 'ABC'
    assert S.observateur_du_nom('2025-11-03-18-38-26-Observateur A.fits') == 'Observateur A'
    assert S.observateur_du_nom('IMG_20260618_223000.jpg') == ''
    assert S.cible_de('ISS_20251018.png') == 'iss' and S.cible_de('photo', 'Moon 2025') == 'lune'
    assert S.genre_de('a.fits.fz') == 'fits' and S.genre_de('b.XLSX') == 'tableau' and S.genre_de('c.wcs') == \
        'astrometrie' and S.genre_de('d.ser') == 'ser' and S.genre_de('e.bin') == 'autre'
    assert S.est_annotation('lune_astrometry_annotated.png')


def _entrees(noms_dates):
    return [{'chemin': c, 'dossier': False, 'taille': 1000, 'modifie': d, 'etag': 'e'} for c, d in noms_dates]


def test_decouvrir_prises_series_nouveautes():
    depot = D.datetime(2026, 10, 18, 9, 0, tzinfo=UTC).timestamp()
    noms = []
    for k in range(5):                              # série ISS de l'observateur ABC : une pose toutes les 2 s
        base = '2026/17 Octobre 2026/ISS-26-10-17-04-29-%02d.204-ABC' % (11 + 2 * k)
        noms += [base + '.fit', base + '.png']      # deux variantes d'une même prise
    noms += ['2026/17 Octobre 2026/ISS-26-10-17-04-29-12.000-XYZ.fit',
             '2026/17 Octobre 2026/ISS-26-10-17-04-45-00.000-XYZ.fit',      # 15 min plus tard : autre série
             '2026/17 Octobre 2026/IMG20240101120000.jpg',                  # date du nom ≠ dossier : douteux
             '2026/localisations.xlsx', '2025/2025-11-03-18-38-26-A.fits', 'Lisez-moi.txt']
    st = S.decouvrir(_entrees([(n, depot) for n in noms]))
    assert st.resume()['fichiers'] == len(noms) and st.resume()['nouveaux'] == 0      # première visite
    abc = [f for f in st.fichiers if f.observateur == 'ABC']
    assert len({f.prise for f in abc}) == 5 and len({f.serie for f in abc}) == 1
    xyz = [f for f in st.fichiers if f.observateur == 'XYZ']
    assert len({f.serie for f in xyz}) == 2
    douteux = st.fichier('2026/17 Octobre 2026/IMG20240101120000.jpg')
    assert douteux.doute and douteux.instant_source == 'nom'
    assert [f.chemin for f in st.tableaux] == ['2026/localisations.xlsx']
    assert st.observateurs == ['A', 'ABC', 'XYZ'] and set(st.cibles) == {'iss'}
    assert st.dossiers['2026/17 Octobre 2026'].date == D.date(2026, 10, 17)
    assert st.dossiers['2025'].annee_seule
    st2 = S.decouvrir(_entrees([(n, depot) for n in noms + ['2026/nouvelle.fits']]), set(noms))
    assert [f.chemin for f in st2.fichiers if f.nouveau] == ['2026/nouvelle.fits']


# ============================================================================================== classeurs
@pytest.fixture
def xlsx():
    return X.classeur(X.lignes_mesures())


def test_lire_classeur(xlsx):
    c = T.lire(xlsx, 'localisations.xlsx')
    assert [f.nom for f in c.feuilles] == ['Localisations', 'Calculs']
    fe = c.feuille(0)
    assert fe.cellules[(2, 3)].valeur == 'Nom du fichier'
    assert fe.cellules[(4, 5)].date and abs((fe.cellules[(4, 5)].comme_date() - X.T_LUNE.replace(tzinfo=None))
                                            .total_seconds()) < 0.01
    assert c.feuille('Calculs').cellules[(1, 2)].formule == '2*PI()*6371'
    assert T.ligne_libre(fe) == 8                    # lignes 3 à 7 remplies ; 8 à 30 numérotées mais vides


def test_ajouter_ligne_ne_touche_a_rien_d_autre(xlsx):
    nouveau, n = T.ajouter_ligne(xlsx, [None, 'Lune', 'mon_image.fits', 'Observateur F', '03/11/2025 18:40:00 TU',
                                        2.5, 48.1, 60.5])
    assert n == 8
    a, b = zipfile.ZipFile(io.BytesIO(xlsx)), zipfile.ZipFile(io.BytesIO(nouveau))
    assert a.namelist() == b.namelist()
    for nom in a.namelist():                          # toutes les autres entrées : identiques à l'octet près
        if nom != 'xl/worksheets/sheet1.xml':
            assert a.read(nom) == b.read(nom), nom
    fe = T.lire(nouveau).feuille(0)
    assert [fe.cellules.get((8, k)).valeur for k in range(1, 9)] == [6.0, 'Lune', 'mon_image.fits', 'Observateur F',
                                                                    '03/11/2025 18:40:00 TU', 2.5, 48.1, 60.5]
    assert fe.cellules[(8, 2)].ref == 'B8'
    avant = T.lire(xlsx).feuille(0)
    for (l, c), cel in avant.cellules.items():        # aucune cellule existante n'a changé
        assert fe.cellules[(l, c)].valeur == cel.valeur, (l, c)
    x = b.read('xl/worksheets/sheet1.xml').decode()
    assert re.search(r'<c r="B8" s="3" t="inlineStr">', x)     # style de la ligne pré-numérotée gardé
    assert '<dimension ref="A1:J30"/>' in x and '<mergeCell ref="A1:J1"/>' in x
    # deuxième ajout : ligne suivante ; jamais de cellule remplie remplacée
    nouveau2, n2 = T.ajouter_ligne(nouveau, [None, 'ISS'])
    assert n2 == 9


def test_ligne_occupee_refusee():
    octets = T.ecrire_xlsx_simple([['Cible', 'Latitude', 'Longitude'], ['Lune', 1, 2]])
    fe = T.lire(octets).feuille(0)
    assert T.ligne_libre(fe, None) == 3
    # la colonne de numérotation ne compte pas pour trouver la ligne libre, mais une cellule déjà remplie n'est
    # JAMAIS remplacée : écrire dans A3 (occupée) est refusé
    numerote = T.ecrire_xlsx_simple([['Cible', 'Latitude', 'Longitude'], ['Lune', 1, 2], ['3']])
    assert T.ligne_libre(T.lire(numerote).feuille(0), 1) == 3
    with pytest.raises(T.ClasseurIllisible):
        T.ajouter_ligne(numerote, ['y'], 0, colonne_numero=1)
    assert T.ajouter_ligne(numerote, [None, 'ISS'], 0, colonne_numero=1)[1] == 3


def test_csv_et_classeurs_illisibles():
    c = T.lire('Cible;Latitude;Longitude\nLune;48,8;2,3\n'.encode('cp1252'), 'a.csv')
    assert c.format == 'csv' and c.feuille(0).cellules[(2, 2)].valeur == '48,8'
    with pytest.raises(T.ClasseurIllisible):
        T.lire(b'PK\x03\x04pas un zip', 'a.xlsx')
    bombe = io.BytesIO()
    with zipfile.ZipFile(bombe, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('xl/workbook.xml', b' ' * (T.TAILLE_MAX_ENTREE + 1))
    with pytest.raises(T.ClasseurIllisible):
        T.lire(bombe.getvalue(), 'a.xlsx')
    assert T.colonne_lettres(28) == 'AB' and T.colonne_num('AB') == 28


# ============================================================================================== valeurs
@pytest.mark.parametrize('texte,attendu', [
    ('2,45°', 2.45), ('02,5658°', 2.5658), (2.45, 2.45), ('48°47′05″ N', 48 + 47 / 60 + 5 / 3600),
    ("2°27' E", 2.45), ('O 1,6', -1.6), ('1.6 W', -1.6), ('+44:13:51:00', 44 + 13 / 60 + 51 / 3600),
    ('-31 57 08', -(31 + 57 / 60 + 8 / 3600)), ('43°17,8′ S', -(43 + 17.8 / 60)),
])
def test_angles(texte, attendu):
    assert M.angle(texte).valeur == pytest.approx(attendu, abs=1e-9)


def test_ascension_droite_en_heures():
    assert M.angle('0h41m50s', heures=True).valeur == pytest.approx((41 / 60 + 50 / 3600) * 15)
    assert M.angle('pas un angle').valeur is None and 'pt_n_illisible' in M.angle('pas un angle').notes


@pytest.mark.parametrize('texte,attendu,note', [
    ('03/11/2025 18:38:26 TU', D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC), 'pt_n_tu'),
    ('10/25/2025 20:45:52 TU', D.datetime(2025, 10, 25, 20, 45, 52, tzinfo=UTC), 'pt_n_date_us'),
    ('2025-11-03 18:38:26.5 UTC', D.datetime(2025, 11, 3, 18, 38, 26, 500000, tzinfo=UTC), 'pt_n_tu'),
    ('03/11/2025 19:38:26 +01:00', D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC), 'pt_n_decalage'),
    ('03/11/2025 19:38:26 heure locale', D.datetime(2025, 11, 3, 19, 38, 26, tzinfo=UTC), 'pt_n_heure_locale_dite'),
    ('03/11/2025 18h38', D.datetime(2025, 11, 3, 18, 38, tzinfo=UTC), 'pt_n_date_ambigue'),
    (45964.776689814815, D.datetime(2025, 11, 3, 18, 38, 26, tzinfo=UTC), 'pt_n_excel'),
])
def test_instants(texte, attendu, note):
    v = M.instant(texte)
    assert abs((v.valeur - attendu).total_seconds()) < 0.01 and note in v.notes


def test_roles_des_colonnes():
    assert M.role_de('Nom du fichier') == 'fichier' and M.role_de('Date + heure (TU)') == 'date'
    assert M.role_de('Long.') == 'longitude' and M.role_de('Altitude (m)') == 'altitude'
    assert M.role_de('Altitude de la Lune (km)') == '' and M.role_de('Hauteur') == 'hauteur'
    assert M.role_de('Azimuth') == 'azimut' and M.role_de('Observer') == 'auteur'


# ============================================================================================== contrôles
def _tableau(xlsx, fichiers=None, entetes=None):
    fe = T.lire(xlsx).feuille(0)
    assert M.est_tableau_de_mesures(fe)
    return M.controler(M.lire_tableau(fe), fichiers, entetes)


def _cles(m):
    return {a.cle for a in m.anomalies}


def test_controles_ligne_par_ligne(xlsx):
    noms = {M.normaliser(n): n for n in ('2025-11-03-18-38-26-A.fits', '2025-11-03-18-38-26-B.fits',
                                          '2025-11-03-18-38-26-C.jpg')}
    t = _tableau(xlsx, noms)
    a, b, c, d, e = t.mesures
    assert t.ligne_entete == 2 and len(t.mesures) == 5
    assert (a.lat, a.lon) == pytest.approx(X.PARIS[:2]) and a.niveau == 'info' and 'pt_a_normalise' in _cles(a)
    assert a.instant == X.T_LUNE
    # B : échange prouvé par la Lune (hauteur et azimut notés ne collent qu'avec les coordonnées échangées)
    assert 'pt_a_inversion_lune' in _cles(b) and b.niveau == 'erreur'
    assert (b.retenu('lat'), b.retenu('lon')) == pytest.approx(X.MARSEILLE[:2])
    assert (b.lat, b.lon) == pytest.approx((X.MARSEILLE[1], X.MARSEILLE[0]))      # l'original n'est pas touché
    assert abs((b.instant - X.T_LUNE).total_seconds()) < 0.01
    # C : heure locale notée ; la position de la Lune s'accorde avec l'heure moins 1 h
    assert 'pt_a_heure_locale_lune' in _cles(c) and c.retenu('instant') == X.T_LUNE - D.timedelta(hours=1)
    assert c.retenu('instant', appliquer=False) == X.T_LUNE
    # D : date américaine, fichier absent du partage
    assert {'pt_a_date_us', 'pt_a_fichier_absent'} <= _cles(d) and d.alt_m == 170.0
    assert d.lat == pytest.approx(45 + 45 / 60 + 50 / 3600) and d.cible == 'iss'
    # E : latitude impossible : inversion certaine, site austral retrouvé
    assert 'pt_a_inversion_certaine' in _cles(e) and (e.retenu('lat'), e.retenu('lon')) == pytest.approx(X.PERTH[:2])
    assert t.resume()['lignes'] == 5 and t.resume()['erreur'] >= 2


def test_controles_par_en_tete():
    lignes = [['Lune', 'x.fits', 'Observateur A', '03/11/2025 19:38:26', 48.8566, 2.3522, 35, None, None],
              ['Lune', 'y.fits', 'Observateur B', '03/11/2025 18:38:28 TU', 5.3698, 43.2965, 12, None, None]]
    entetes = {'x.fits': {'lat': 48.8566, 'lon': 2.3522, 'instant': X.T_LUNE},
               'y.fits': {'lat': 43.2965, 'lon': 5.3698, 'instant': X.T_LUNE}}
    t = _tableau(X.classeur(lignes), None, entetes)
    x, y = t.mesures
    assert 'pt_a_heure_locale_entete' in _cles(x) and x.retenu('instant') == X.T_LUNE
    # x : lat/lon notés dans l'ordre (longitude, latitude) = (48.86, 2.35) → échange prouvé par l'en-tête
    assert 'pt_a_inversion_entete' in _cles(x)
    assert 'pt_a_ecart_horloge' in _cles(y) and 'pt_a_inversion_entete' not in _cles(y)


def test_inversion_par_comparaison_aux_lieux_surs():
    lignes = [['ISS', 'a.fits', 'Observateur A', '17/10/2026 04:29:11 TU', 2.3522, 48.8566, 35, None, None],
              ['ISS', 'b.fits', 'Observateur B', '17/10/2026 04:29:11 TU', 45.764, 4.8357, 170, None, None],
              ['ISS', 'c.fits', 'Observateur C', '17/10/2026 04:29:11 TU', 115.8613, -31.9523, 20, None, None]]
    t = _tableau(X.classeur(lignes), None, {'a.fits': {'lat': 48.8566, 'lon': 2.3522}})
    a, b, c = t.mesures
    assert not any(x.champ == 'lat' for x in a.anomalies)
    assert 'pt_a_inversion_probable' in _cles(b) and b.retenu('lat') == pytest.approx(45.764)
    assert 'pt_a_inversion_probable' not in _cles(c)             # site austral lointain : légitime, rien à redire


# ============================================================================================== textes
def test_cles_dynamiques_du_module_existent():
    from coupole.core import i18n
    from coupole.modules.partages.analyses.parallaxe import calcul
    cles = i18n.toutes_les_cles()
    racine = Path(M.__file__).parent
    litteraux = set()
    for f in racine.rglob('*.py'):
        if f.name != 'textes.py':
            litteraux |= set(re.findall(r"""['"]((?:pt|pc)_[a-z0-9_]*[a-z0-9])['"]""", f.read_text(encoding='utf-8')))
    internes = {k for k in litteraux if k.startswith('pt_n_')} | {'pt_commande'}   # codes internes, jamais affichés
    assert sorted(k for k in litteraux - internes if k not in cles) == []
    attendues = (['pt_cible_' + c for c in set(S.CIBLES.values())] + ['pt_genre_' + g for g in list(S.GENRES) + ['autre']]
                 + ['pc_source_' + s for s in ('tableau', 'entete', 'nom')]
                 + ['pc_res_' + g for g in ('diurne', 'vitesse', 'orbite')]
                 + ['pc_eph_' + s for s in ('de440', 'meeus')] + ['pc_eph_etat_' + s for s in ('de440', 'meeus')]
                 + ['pc_r_titre_' + g for g in ('lune', 'iss')] + ['pc_r_methode_' + g for g in ('lune', 'iss')]
                 + ['pt_niveau_' + n for n in ('ok', 'info', 'attention', 'erreur')]
                 + ['pc_b_' + b for b in ('direction', 'position', 'heure', 'ephemeride')]
                 + ['pt_droit_' + d for d in ('lire', 'deposer', 'ecrire', 'dossiers', 'renommer', 'deplacer',
                                              'supprimer', 'repartager')])
    assert [k for k in attendues if k not in cles] == []
    assert calcul.ErreurCalcul('pc_err_derriere').cle in cles


def test_date_ambigue_tranchee_par_le_nom_du_fichier():
    lignes = [['Lune', '2025-11-03-18-38-26-A.fits', 'Observateur A', '11/03/2025 18:38:26 TU', 2.35, 48.86, 35,
               None, None],
              ['Lune', 'sans_date.fits', 'Observateur B', '11/03/2025 18:38:26 TU', 5.37, 43.30, 12, None, None]]
    a, b = _tableau(X.classeur(lignes)).mesures
    assert 'pt_a_date_inversee_nom' in _cles(a) and a.retenu('instant') == X.T_LUNE
    assert a.instant == D.datetime(2025, 3, 11, 18, 38, 26, tzinfo=UTC)          # l'original n'est pas touché
    assert 'pt_a_date_ambigue' in _cles(b) and 'instant' not in b.corrections
