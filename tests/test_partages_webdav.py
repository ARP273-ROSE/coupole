"""Partages du DU (0.8.0) : lien de partage, client WebDAV contre un serveur factice, aucune méthode destructrice."""
import threading

import pytest

from coupole.modules.partages import webdav as W
from .serveur_webdav import ServeurWebdav


@pytest.fixture
def serveur():
    s = ServeurWebdav({
        '2026/17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.fit': b'SIMPLE  =                    T' + b' ' * 3000,
        '2026/localisations.csv': 'Cible;Latitude;Longitude\nLune;48,8;2,3\n'.encode('utf-8'),
        'Lisez-moi.txt': b'bonjour',
    })
    yield s
    s.fermer()


# ------------------------------------------------------------------ lien
@pytest.mark.parametrize('texte,serveur_attendu,jeton', [
    ('https://nuage.exemple.org/s/AbCdEf123456', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('https://nuage.exemple.org/index.php/s/AbCdEf123456', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('https://nuage.exemple.org/s/AbCdEf123456/download?path=%2F2026', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('nuage.exemple.org/s/AbCdEf123456', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('https://nuage.exemple.org/cloud/s/AbCdEf123456', 'https://nuage.exemple.org/cloud', 'AbCdEf123456'),
    ('https://nuage.exemple.org/public.php/dav/files/AbCdEf123456/', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('davs://AbCdEf123456@nuage.exemple.org/public.php/webdav/', 'https://nuage.exemple.org', 'AbCdEf123456'),
    ('  <https://nuage.exemple.org:8443/s/AbCdEf123456>  ', 'https://nuage.exemple.org:8443', 'AbCdEf123456'),
])
def test_lien_reconnu(texte, serveur_attendu, jeton):
    p = W.analyser_lien(texte)
    assert (p.serveur, p.jeton) == (serveur_attendu, jeton)
    assert p.racine == serveur_attendu + '/public.php/webdav/'


@pytest.mark.parametrize('texte,cle', [
    ('', 'pt_lien_vide'),
    ('http://nuage.exemple.org/s/AbCdEf123456', 'pt_lien_https'),          # jeton en clair : refusé
    ('https://nuage.exemple.org/apps/files/', 'pt_lien_pas_partage'),
    ('https://nuage.exemple.org/public.php/webdav/', 'pt_lien_jeton_manquant'),
    ('https://nuage.exemple.org/s/ab', 'pt_lien_jeton_invalide'),
    ('ftp://nuage.exemple.org/s/AbCdEf123456', 'pt_lien_illisible'),
])
def test_lien_refuse(texte, cle):
    with pytest.raises(W.LienInvalide) as e:
        W.analyser_lien(texte)
    assert e.value.cle == cle


def test_lien_masque_le_jeton():
    p = W.analyser_lien('https://nuage.exemple.org/s/AbCdEf123456')
    assert 'AbCdEf123456' not in p.masque() and p.masque().startswith('https://nuage.exemple.org/s/Ab')
    assert p.lien() == 'https://nuage.exemple.org/s/AbCdEf123456'


def test_droits_dans_l_ordre():
    assert W.droits_de('RGDNVCK') == ['lire', 'deposer', 'dossiers', 'renommer', 'deplacer', 'supprimer',
                                      'repartager']
    assert W.droits_de('') == []


# ------------------------------------------------------------------ lecture
def test_verifier_lister_lire(serveur):
    c = W.Client(W.analyser_lien(serveur.lien))
    info = c.verifier()
    assert info.droits == ['lire', 'deposer', 'dossiers']
    assert {e.chemin for e in info.entrees} == {'2026', 'Lisez-moi.txt'}
    tout = c.lister_tout()
    chemins = {e.chemin for e in tout}
    assert '2026/17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.fit' in chemins       # espaces et accents
    assert '2026/17 Octobre 2026' in chemins and '' not in chemins
    f = next(e for e in tout if e.chemin.endswith('.fit'))
    assert f.taille == 3030 and f.etag and f.modifie > 1e9 and not f.dossier
    assert c.lire('Lisez-moi.txt') == b'bonjour'
    assert c.lire(f.chemin, 0, 5) == b'SIMPLE'                                       # requête partielle
    contenu, etag = c.lire_avec_etag('Lisez-moi.txt')
    assert contenu == b'bonjour' and etag == serveur.etags['Lisez-moi.txt']
    assert c.etat('absent.txt') is None


def test_mauvais_jeton_et_mot_de_passe(serveur):
    p = W.analyser_lien(serveur.lien)
    p.jeton = 'Faux12345'
    with pytest.raises(W.ErreurPartage) as e:
        W.Client(p).verifier()
    assert e.value.cle == 'pt_err_401'
    serveur.mot_de_passe = 'secret'
    with pytest.raises(W.ErreurPartage):
        W.Client(W.analyser_lien(serveur.lien)).verifier()
    assert W.Client(W.analyser_lien(serveur.lien, mot_de_passe='secret')).verifier().droits


def test_telecharger_moteur_commun(serveur, tmp_path):
    c = W.Client(W.analyser_lien(serveur.lien))
    dest = tmp_path / 'a.fit'
    c.telecharger('2026/17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.fit', str(dest), 3030)
    assert dest.read_bytes() == serveur.fichiers['2026/17 Octobre 2026/ISS-26-10-17-04-29-11.204-ABC.fit']


def test_arret_de_la_liste(serveur):
    ev = threading.Event()
    ev.set()
    from coupole.core import reseau
    with pytest.raises(reseau.Annule):
        W.Client(W.analyser_lien(serveur.lien)).lister_tout(ev)


def test_reponse_hostile_ignoree():
    xml = (b'<?xml version="1.0"?><d:multistatus xmlns:d="DAV:"><d:response><d:href>/public.php/webdav/../../etc/'
           b'passwd</d:href><d:propstat><d:prop><d:resourcetype/></d:prop><d:status>HTTP/1.1 200 OK</d:status>'
           b'</d:propstat></d:response></d:multistatus>')
    assert W.analyser_multistatus(xml, '/public.php/webdav/') == []
    with pytest.raises(W.ErreurPartage):
        W.analyser_multistatus(b'<pas du xml', '/public.php/webdav/')


# ------------------------------------------------------------------ écriture : toujours conditionnelle
def test_depot_conditionnel(serveur):
    c = W.Client(W.analyser_lien(serveur.lien))
    etag = c.deposer('2026/nouveau.txt', b'un')
    assert serveur.fichiers['2026/nouveau.txt'] == b'un' and etag == serveur.etags['2026/nouveau.txt']
    with pytest.raises(W.Conflit):                       # existe déjà : If-None-Match: * refusé, rien d'écrasé
        c.deposer('2026/nouveau.txt', b'deux')
    assert serveur.fichiers['2026/nouveau.txt'] == b'un'
    with pytest.raises(W.Conflit):                       # ETag périmé : refusé
        c.deposer('2026/nouveau.txt', b'trois', si_etag='perime')
    assert serveur.fichiers['2026/nouveau.txt'] == b'un'
    c.deposer('2026/nouveau.txt', b'quatre', si_etag=etag)
    assert serveur.fichiers['2026/nouveau.txt'] == b'quatre'
    assert c.creer_dossier('2026/Mesures') is True and c.creer_dossier('2026/Mesures') is False
    assert serveur.ecrasements == []


def test_depot_fichier_par_blocs(serveur, tmp_path):
    local = tmp_path / 'video.ser'
    local.write_bytes(bytes(range(256)) * 1000)
    vus = []
    W.Client(W.analyser_lien(serveur.lien)).deposer_fichier('video.ser', str(local), progression=vus.append)
    assert serveur.fichiers['video.ser'] == local.read_bytes() and sum(vus) == 256000


def test_aucune_methode_destructrice(serveur):
    c = W.Client(W.analyser_lien(serveur.lien))
    for m in ('DELETE', 'MOVE', 'COPY', 'PROPPATCH'):
        with pytest.raises(ValueError):
            c._requete(m, 'Lisez-moi.txt')
        assert not hasattr(c, m.lower())
    assert not any(hasattr(c, n) for n in ('supprimer', 'renommer', 'deplacer', 'copier', 'effacer'))
    assert serveur.interdites == []
    assert set(W.Client.METHODES) == {'PROPFIND', 'GET', 'PUT', 'MKCOL'}
