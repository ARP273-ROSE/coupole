"""Partages du DU (0.8.0) : partages mémorisés, session (liste, nouveautés, en-têtes partiels, tableaux), téléchargement
rangé, et DÉPÔT de sa mesure sans rien écraser (conflits simulés), contre un serveur WebDAV factice."""
import datetime as D
import os
import stat
import sys

import pytest

from coupole.modules.partages import depot, etat, tableur
from coupole.modules.partages import telechargement as TL
from coupole.modules.partages.session import Session, analyser_cartes

from . import partages_exemple as X
from .serveur_webdav import ServeurWebdav

UTC = D.timezone.utc


@pytest.fixture
def serveur():
    fa, _ = X.fits_lune(X.PARIS, X.T_LUNE, 'Observateur A')
    fb, _ = X.fits_lune(X.MARSEILLE, X.T_LUNE, 'Observateur B')
    depot_date = D.datetime(2025, 11, 4, 9, 0, tzinfo=UTC).timestamp()
    s = ServeurWebdav({
        '2025/2025-11-03-18-38-26-A.fits': fa,
        '2025/2025-11-03-18-38-26-B.fits': fb,
        '2025/localisations.xlsx': X.classeur(X.lignes_mesures()),
        'Lisez-moi.txt': b'Deposez vos images ici.',
    }, dates={'2025/2025-11-03-18-38-26-A.fits': depot_date, '2025/2025-11-03-18-38-26-B.fits': depot_date})
    yield s
    s.fermer()


@pytest.fixture
def session(serveur):
    for x in etat.lister():
        etat.retirer(x.ident)
    m = etat.ajouter('Défi parallaxe', serveur.lien)
    s = Session(m)
    s.verifier()
    s.rafraichir()
    yield s
    etat.retirer(m.ident)


# ------------------------------------------------------------------ partages mémorisés
def test_partages_memorises(serveur):
    a = etat.ajouter('Défi', serveur.lien)
    b = etat.ajouter('Défi', serveur.lien.replace(serveur.jeton, 'Autre9999'))
    assert b.nom == 'Défi (2)' and len(etat.lister()) >= 2
    assert etat.ajouter('Nouveau nom', serveur.lien).ident == a.ident             # même lien : mis à jour
    assert etat.trouver(a.ident).nom == 'Nouveau nom'
    etat.renommer(a.ident, 'Renommé')
    assert etat.trouver('Renommé') is not None
    if sys.platform != 'win32':
        assert stat.S_IMODE(os.stat(etat._chemin()).st_mode) == 0o600                 # le lien est un secret
    assert serveur.jeton not in etat.exporter_texte(etat.trouver('Renommé'))
    assert etat.retirer(a.ident) and etat.retirer(b.ident) and not etat.retirer(b.ident)
    assert serveur.methodes() <= {'PROPFIND', 'GET'}                                # oublier : rien sur le serveur


def test_session_liste_nouveautes_entetes(session, serveur):
    st = session.structure
    assert st.resume()['fichiers'] == 4 and st.resume()['nouveaux'] == 0
    session.marquer_vus()
    serveur.poser('2025/2025-11-03-18-38-30-C.jpg', b'\xff\xd8\xff')
    st = session.rafraichir()
    assert [f.chemin for f in st.fichiers if f.nouveau] == ['2025/2025-11-03-18-38-30-C.jpg']
    assert session.depuis_cache().resume()['fichiers'] == 5                         # hors ligne : dernière liste
    n = len(serveur.requetes)
    e = session.lire_entete_fits('2025/2025-11-03-18-38-26-A.fits')
    assert serveur.requetes[n][2].get('Range', '').startswith('bytes=0-')          # en-tête seul, pas l'image
    assert (e['lat'], e['lon']) == pytest.approx(X.PARIS[:2]) and e['wcs'] and e['objet'] == 'Moon'
    assert D.datetime.fromisoformat(e['milieu']) == X.T_LUNE + D.timedelta(seconds=0.5)
    f = session.structure.fichier('2025/2025-11-03-18-38-26-A.fits')
    assert f.instant_source == 'entete'
    assert Session(etat.trouver(session.ident)).entetes                              # gardé entre deux lancements


def test_session_tableau_controle(session):
    classeur, tableaux = session.lire_tableau('2025/localisations.xlsx')
    assert len(tableaux) == 1 and len(tableaux[0].mesures) == 5
    assert any(a.cle == 'pt_a_fichier_absent' for a in tableaux[0].anomalies)    # ISS_inexistant.fits
    assert session.tableaux_de_mesures() == tableaux


def test_cartes_fits_tolerantes():
    cartes = analyser_cartes(b''.join(x.ljust(80).encode() for x in (
        "SIMPLE  =                    T", "OBJECT  = 'L''ISS   '", "SITELAT = '+44:13:51'", "EXPTIME = 1.5D0 / s",
        "BIZARRE = TRUE", "END")))
    assert cartes == {'SIMPLE': True, 'OBJECT': "L'ISS", 'SITELAT': '+44:13:51', 'EXPTIME': 1.5, 'BIZARRE': 'TRUE'}


# ------------------------------------------------------------------ téléchargement rangé
def test_telechargement_range_et_reprise(session, tmp_path):
    fichiers = [f for f in session.structure.fichiers if f.genre in ('fits', 'tableau')]
    session.lire_tableau('2025/localisations.xlsx')            # le tableau dit que A et B visaient la Lune
    evs = []
    r = TL.Telechargement(session, fichiers, str(tmp_path), 'fits', rapporter=evs.append).executer()
    assert r.get('ok') == 3
    jour = tmp_path / 'defi-parallaxe' / '2025-11-03' / 'lune'
    assert (jour / 'a' / '2025-11-03-18-38-26-A.fits').exists()
    assert (jour / 'a' / TL.ORIGINAUX / '2025-11-03-18-38-26-A.fits').exists()
    from astropy.io import fits
    h = fits.getheader(jour / 'a' / '2025-11-03-18-38-26-A.fits')
    assert h['CTYPE1'] == 'RA---TAN' and h['BITPIX'] == -32
    assert any(e['genre'] == 'fini' and e['wcs'] == 'entete' for e in evs)
    r2 = TL.Telechargement(session, fichiers, str(tmp_path), 'xisf').executer()
    assert r2.get('deja') == 3                                       # déjà là : rien ne repart
    assert set(TL.possedes(str(tmp_path), session.ident)) == {f.chemin for f in fichiers}


# ------------------------------------------------------------------ dépôt
def _plan(session, tmp_path, nom='mon_image.fits'):
    local = tmp_path / nom
    local.write_bytes(b'SIMPLE  =                    T'.ljust(2880))
    _, ts = session.lire_tableau('2025/localisations.xlsx')
    mesure = {'cible': 'Lune', 'auteur': 'Observateur F', 'date': D.datetime(2025, 11, 3, 18, 38, 27, tzinfo=UTC),
              'latitude': 45.0, 'longitude': 4.5, 'altitude': 200}
    return depot.preparer(session, '2025', [str(local)], '2025/localisations.xlsx', ts[0], mesure, 'Observateur F')


def test_plan_exact_et_noms_libres(session, tmp_path):
    assert depot.nom_libre('a.fits', {'A.FITS', 'a_2.fits'}) == 'a_3.fits'
    assert depot.nom_libre('b.fits.fz', {'b.fits.fz'}) == 'b_2.fits.fz'
    assert depot.nom_sur('a/b:c?.fits') == 'a_b_c_.fits' and depot.nom_sur(' .. ') == 'fichier'
    plan = _plan(session, tmp_path, '2025-11-03-18-38-26-A.fits')                # nom déjà pris
    assert plan.fichiers[0].distant == '2025/2025-11-03-18-38-26-A_2.fits'
    assert dict(plan.colonnes)['Nom du fichier'] == '2025-11-03-18-38-26-A_2.fits'
    assert dict(plan.colonnes)['Date + heure (TU)'] == '03/11/2025 18:38:27 TU'      # format du tableau
    assert plan.valeurs[0] is None                                                   # numéro : laissé tel quel
    assert plan.csv_secours.startswith('2025/ligne_Observateur_F_') and plan.octets() == 2880


def test_depot_sans_rien_ecraser(session, serveur, tmp_path):
    avant = {c: v for c, v in serveur.fichiers.items()}
    plan = _plan(session, tmp_path)
    r = depot.executer(session, plan, str(tmp_path / 'sauvegardes'))
    assert r['fichiers'] == ['2025/mon_image.fits'] and r['tableau'] == 'ligne' and r['ligne'] == 8
    for c, v in avant.items():                                   # les fichiers des autres : intacts
        if c != '2025/localisations.xlsx':
            assert serveur.fichiers[c] == v
    fe = tableur.lire(serveur.fichiers['2025/localisations.xlsx']).feuille(0)
    assert fe.cellules[(8, 4)].valeur == 'Observateur F' and fe.cellules[(7, 4)].valeur == 'Observateur E'
    assert os.path.getsize(r['sauvegarde']) == len(avant['2025/localisations.xlsx'])      # copie avant écriture
    assert serveur.ecrasements == [] and serveur.interdites == []
    assert serveur.methodes() <= {'PROPFIND', 'GET', 'PUT'}


def test_depot_conflits(session, serveur, tmp_path):
    plan = _plan(session, tmp_path)

    def autre_etudiant(s, chemin):                 # quelqu'un dépose le même nom ET modifie le tableau entre-temps
        s.poser('2025/mon_image.fits', b'image de quelqu un d autre')
    serveur.avant_put = autre_etudiant
    r = depot.executer(session, plan, str(tmp_path / 's'))
    assert r['fichiers'] == ['2025/mon_image_2.fits'] and r['renommes']
    assert serveur.fichiers['2025/mon_image.fits'] == b'image de quelqu un d autre'

    plan2 = _plan(session, tmp_path, 'deuxieme.fits')
    compte = {'n': 0}

    def tableau_toujours_modifie(s, chemin):
        if chemin.endswith('.xlsx'):
            compte['n'] += 1
            s.poser(chemin, s.fichiers[chemin])                    # même contenu, nouvel ETag : la condition tombe
        s.avant_put = tableau_toujours_modifie
    serveur.avant_put = tableau_toujours_modifie
    avant = serveur.fichiers['2025/localisations.xlsx']
    r = depot.executer(session, plan2, str(tmp_path / 's'))
    serveur.avant_put = None
    assert compte['n'] == depot.ESSAIS_TABLEAU and r['tableau'] == 'csv'
    assert serveur.fichiers['2025/localisations.xlsx'] == avant                 # jamais écrasé
    contenu = serveur.fichiers[r['csv']].decode('utf-8-sig')
    assert 'Observateur F' in contenu and contenu.splitlines()[0].startswith('N°;Cible;Nom du fichier')
    assert serveur.ecrasements == []


def test_depot_refuse_sans_droit(session, serveur, tmp_path):
    serveur.permissions = 'G'
    plan = _plan(session, tmp_path)
    from coupole.modules.partages.webdav import ErreurPartage
    with pytest.raises(ErreurPartage) as e:
        depot.executer(session, plan, str(tmp_path / 's'))
    assert e.value.cle == 'pt_err_403'


def test_ligne_de_commande(serveur, capsys, tmp_path):
    """coupole partages : ajouter, liste, explorer, tableau, paires, télécharger, mesurer, oublier (serveur local)."""
    import json as J

    from coupole.cli import main
    for x in etat.lister():
        etat.retirer(x.ident)
    assert main(['--lang', 'fr', 'partages', 'ajouter', 'Essai', serveur.lien]) == 0
    assert main(['--lang', 'fr', 'partages', 'liste', '--json']) == 0
    sortie = capsys.readouterr().out
    assert 'Essai' in sortie and serveur.jeton not in sortie                    # le jeton n'est jamais affiché
    assert main(['--lang', 'fr', 'partages', 'explorer', 'Essai', '--json']) == 0
    d = J.loads(capsys.readouterr().out)
    assert d['resume']['fichiers'] == 4
    assert main(['--lang', 'fr', 'partages', 'tableau', 'Essai', '--json']) == 0
    assert 'Observateur B' in capsys.readouterr().out
    assert main(['--lang', 'fr', 'partages', 'paires', 'Essai', '--entetes', '--json']) == 0
    paires = J.loads(capsys.readouterr().out)
    assert any(p['cible'] == 'lune' for p in paires)
    assert main(['--lang', 'fr', 'partages', 'telecharger', 'Essai', '2025/2025-11-03-18-38-26-A.fits',
                 '--dossier', str(tmp_path), '--format', 'fits']) == 0
    capsys.readouterr()
    fichier = next(tmp_path.rglob('2025-11-03-18-38-26-A.fits'))
    assert main(['--lang', 'fr', 'partages', 'mesurer', str(fichier), '--cible', 'lune', '--json']) == 0
    m = J.loads(capsys.readouterr().out)
    assert m
    assert main(['--lang', 'fr', 'partages', 'oublier', 'Essai']) == 0
    assert serveur.methodes() <= {'PROPFIND', 'GET'}
