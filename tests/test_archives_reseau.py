"""Essai réel du module Archives (réseau public) : sauté sauf avec COUPOLE_TEST_RESEAU=1.

Requêtes limitées (quelques lignes par archive) et deux petits fichiers (2MASS ~2 Mo, Voyager ~2 Mo) téléchargés
dans un dossier temporaire, préparés puis effacés avec lui."""
import os

import numpy as np
import pytest

pytestmark = pytest.mark.skipif(os.environ.get('COUPOLE_TEST_RESEAU') != '1',
                                reason='essai réseau : COUPOLE_TEST_RESEAU=1')


def test_recherches_reelles():
    from coupole.modules.archives import recherche as R
    from coupole.modules.archives.services.base import Requete
    q = R.requete('M 16', 3.0, limite=50)
    assert abs(q.ra - 274.7) < 0.1 and abs(q.dec + 13.8) < 0.1
    res = {r.archive: r for r in R.chercher(q, ('mast', 'eso', 'irsa', 'noirlab', 'sdss'))}
    for a in ('mast', 'eso', 'irsa'):
        assert not res[a].erreur and res[a].observations, (a, res[a].erreur)
    assert all(o['final'] and o['public'] for r in res.values() for o in r.observations)
    pl = R.chercher(Requete(cible='Io', date_min='1979-03-01', date_max='1979-03-10', limite=5), ('opus',))[0]
    assert not pl.erreur and pl.observations and pl.observations[0]['mission'] == 'Voyager'
    ju = R.chercher(Requete(cible='Jupiter', limite=3), ('pds',))[0]
    assert not ju.erreur and ju.observations


def test_petits_telechargements_reels(tmp_path):
    from coupole.modules.archives import recherche as R
    from coupole.modules.archives import telechargement as T
    from coupole.modules.archives.extraction import lire_prepare
    from coupole.modules.archives.services.base import Requete
    q = R.requete('M 16', 3.0, missions=('2MASS',), limite=20)
    deux = [o for o in R.toutes(R.chercher(q, ('irsa',))) if o['filtre'] == 'J'][:1]
    vg = R.chercher(Requete(cible='Io', date_min='1979-03-01', date_max='1979-03-02', limite=2), ('opus',))[0]
    obs = deux + vg.observations[:1]
    assert len(obs) == 2
    e = T.estimer(obs)
    assert e['octets'] < 20e6
    b = T.Telechargement(tmp_path, obs, cible='essai', debit_octets_s=4e6).executer()
    assert b.get('ok') == 2, b
    p = T.possession(tmp_path)
    for o in obs:
        d, h = lire_prepare(os.path.join(T.dossier_archives(tmp_path), p[o['id']]['prepare']))
        assert d.ndim == 2 and np.isfinite(d).any() and h['CREDIT']
