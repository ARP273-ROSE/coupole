"""Ce qu'on possède déjà (Banque OHP) : état simulé du dossier de sortie → statuts, comptes par objet, images
manquantes, complétude des lots, ligne de commande (--manquantes, colonne « possédé » et CSV)."""
import csv
import json
import os

import pytest

from coupole.modules.ohp.conversion import ident
from coupole.modules.ohp.pilote import Etat
from coupole.modules.ohp.possession import Possession, lire_infos_ok


def etat_simule(dest, images, ok=(), doublon=(), echec=()):
    """Écrit `<dest>/_traitement/etat.sqlite` avec des statuts choisis ; rend les chemins « final » des converties."""
    e = Etat(os.path.join(str(dest), '_traitement', 'etat.sqlite'))
    finals = {}
    try:
        for k, x in enumerate(ok):
            dossier = os.path.join(str(dest), 'Asteroides', x['objet'], x['tel'] + '_' + x['filter_name'].replace(' ', ''))
            os.makedirs(dossier, exist_ok=True)
            final = os.path.join(dossier, 'img%d.xisf' % k)
            open(final, 'wb').close()
            info = {'final': final, 'objet': x['objet'], 'cat': x['cat'], 'tel': x['tel'],
                    'filtre_base': x['filter_name'], 'nuit': str(x['nuit']), 'staging': final}
            e.ecrire(ident(x), x['access_url'], 'ok', info)
            finals[ident(x)] = final
        for x in doublon:
            e.ecrire(ident(x), x['access_url'], 'doublon', {'doublon_de': 'abc'})
        for x in echec:
            e.ecrire(ident(x), x['access_url'], 'echec', {'erreur': 'simulated'})
    finally:
        e.fermer()
    return finals


@pytest.fixture
def palisana(inventaire):
    imgs = [x for x in inventaire.images if x['objet'] == '(914) Palisana']
    utiles = [x for x in imgs if not x['doublon']]
    assert len(imgs) == 16 and len(utiles) == 10
    return imgs, utiles


def test_sans_dossier_rien_n_est_possede(tmp_path, palisana):
    imgs, utiles = palisana
    p = Possession.lire(tmp_path / 'inexistant')
    assert not p.existe and all(p.statut(x) == 'absente' for x in imgs) and not any(p.possedee(x) for x in imgs)
    assert len(p.manquantes(imgs)) == 10                        # les doublons de la base ne sont jamais « manquants »
    c = p.compte(imgs)
    assert c == {'possedees': 0, 'doublons': 0, 'echecs': 0, 'absentes': 10, 'total': 10}
    assert Possession.etat_objet(c) == 'aucun'
    # base abîmée : jamais d'exception, rien de possédé
    (tmp_path / '_traitement').mkdir()
    (tmp_path / '_traitement' / 'etat.sqlite').write_bytes(b'pas une base sqlite')
    assert not Possession.lire(tmp_path).existe and lire_infos_ok(tmp_path) == []


def test_statuts_comptes_et_manquantes(tmp_path, palisana, inventaire):
    imgs, utiles = palisana
    finals = etat_simule(tmp_path, imgs, ok=utiles[:4], doublon=utiles[4:5], echec=utiles[5:6])
    p = Possession.lire(tmp_path)
    assert p.existe
    assert [p.statut(x) for x in utiles] == ['ok'] * 4 + ['doublon', 'echec'] + ['absente'] * 4
    assert p.possedee(utiles[0]) and p.possedee(utiles[4]) and not p.possedee(utiles[5]) and not p.possedee(utiles[6])
    d = p.detail(utiles[0])
    assert d['statut'] == 'ok' and d['date'] and d['chemin'] and not os.path.isabs(d['chemin'])   # chemin relatif à dest
    assert os.path.join(str(tmp_path), d['chemin']) == finals[ident(utiles[0])]
    assert p.detail(utiles[9]) == {'statut': 'absente', 'date': '', 'chemin': '', 'origine': ''}
    # manquantes : échec (à retenter) et absentes, jamais les doublons (de la base ou de pixels)
    manq = p.manquantes(imgs)
    assert len(manq) == 5 and utiles[5] in manq and utiles[4] not in manq and not any(x['doublon'] for x in manq)
    c = p.compte(imgs)
    assert c == {'possedees': 4, 'doublons': 1, 'echecs': 1, 'absentes': 4, 'total': 10}
    assert Possession.etat_objet(c) == 'partiel'
    assert Possession.etat_objet({'possedees': 9, 'doublons': 1, 'echecs': 0, 'absentes': 0, 'total': 10}) == 'complet'
    # par objet sur tout l'inventaire : seul Palisana est entamé
    co = p.compte_objets(inventaire.images)
    assert co['(914) Palisana'] == c
    assert all(v['possedees'] == 0 for k, v in co.items() if k != '(914) Palisana')


def test_completude_des_lots(tmp_path, palisana, inventaire):
    imgs, utiles = palisana
    etat_simule(tmp_path, imgs, ok=utiles[:4])
    p = Possession.lire(tmp_path)
    infos = lire_infos_ok(tmp_path)
    assert len(infos) == 4
    lots = p.lots(inventaire.images, infos)
    assert len(lots) >= 1
    for dossier, c in lots.items():
        assert c['converties'] <= c['base'] and os.path.isdir(dossier)
    # un lot devient complet quand toutes les poses de sa clé (objet, télescope, filtre, nuit) sont converties
    premiere_cle = (utiles[0]['tel'], utiles[0]['filter_name'], str(utiles[0]['nuit']))
    meme_cle = [x for x in utiles if (x['tel'], x['filter_name'], str(x['nuit'])) == premiere_cle]
    etat_simule(tmp_path / 'b', imgs, ok=meme_cle)
    lots = Possession.lire(tmp_path / 'b').lots(inventaire.images, lire_infos_ok(tmp_path / 'b'))
    assert any(c['complet'] and c['converties'] == c['base'] == len(meme_cle) for c in lots.values())


def test_cli_manquantes_et_colonne_possede(tmp_path, palisana, capsys):
    from coupole import cli
    imgs, utiles = palisana
    etat_simule(tmp_path, imgs, ok=utiles[:4], doublon=utiles[4:5], echec=utiles[5:6])
    # --manquantes : lisible, dans les deux langues
    assert cli.main(['--lang', 'fr', 'ohp', 'inventaire', '--manquantes', '--dest', str(tmp_path)]) == 0
    fr = capsys.readouterr().out
    assert 'Palisana' in fr and '5 / 10' in fr and 'À télécharger' in fr and 'possédées : 4' in fr
    assert cli.main(['--lang', 'en', 'ohp', 'inventory', '--missing', '--dest', str(tmp_path)]) == 0
    en = capsys.readouterr().out
    assert 'To download' in en and 'owned: 4' in en and 'À télécharger' not in en
    # --json : comptes exacts
    assert cli.main(['ohp', 'inventaire', '--manquantes', '--json', '--dest', str(tmp_path)]) == 0
    j = json.loads(capsys.readouterr().out)
    pal = next(o for o in j['objets'] if o['objet'] == '(914) Palisana')
    assert j['copie'] and pal['manquantes'] == 5 and pal['total'] == 10 and pal['possedees'] == 4
    assert j['total']['manquantes'] == sum(o['manquantes'] for o in j['objets'])
    # dossier sans copie : tout est à télécharger, sans erreur
    assert cli.main(['--lang', 'fr', 'ohp', 'inventaire', '--manquantes', '--dest', str(tmp_path / 'vide')]) == 0
    assert 'tout est à télécharger' in capsys.readouterr().out
    # colonne « possédé » dans la liste et le CSV
    fichier = tmp_path / 'images.csv'
    assert cli.main(['--lang', 'fr', 'ohp', 'images', '(914) Palisana', '--dest', str(tmp_path), '--csv', str(fichier)]) == 0
    out = capsys.readouterr().out
    assert 'possédée' in out and 'à télécharger' in out and 'échec' in out
    with open(fichier, encoding='utf-8-sig') as f:
        lignes = list(csv.DictReader(f, delimiter=';'))
    assert len(lignes) == 16 and {'possedee', 'statut_local', 'fichier_local'} <= set(lignes[0])
    assert sum(int(l['possedee']) for l in lignes) == 5                    # 4 converties + 1 doublon de pixels
    assert sorted({l['statut_local'] for l in lignes}) == ['absente', 'doublon', 'echec', 'ok']
    assert all(l['fichier_local'] for l in lignes if l['statut_local'] == 'ok')
