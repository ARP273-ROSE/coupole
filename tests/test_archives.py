"""Module « Archives » (0.2.0) : réponses simulées des archives, extraction, formats planétaires, alignement,
téléchargement sur un serveur local, possession, ligne de commande.  Aucune requête ne sort de la machine
(l'essai réel est dans `test_archives_reseau.py`, activé par COUPOLE_TEST_RESEAU=1)."""
import gzip
import json
import math
import os
import struct
import threading
import zlib

import numpy as np
import pytest

from coupole.modules.archives import alignement as AL
from coupole.modules.archives import extraction as EX
from coupole.modules.archives import pds as PDS
from coupole.modules.archives import recherche as R
from coupole.modules.archives import services as S
from coupole.modules.archives import telechargement as T
from coupole.modules.archives.services import base as B


# ============================================================================================ réponses simulées
def votable(champs, lignes, erreur=None):
    if erreur:
        return ('<?xml version="1.0"?><VOTABLE xmlns="http://www.ivoa.net/xml/VOTable/v1.3"><RESOURCE type="results">'
                '<INFO name="QUERY_STATUS" value="ERROR">%s</INFO></RESOURCE></VOTABLE>' % erreur).encode()
    f = ''.join('<FIELD name="%s" datatype="char" arraysize="*"/>' % c for c in champs)
    tr = ''.join('<TR>%s</TR>' % ''.join('<TD>%s</TD>' % ('' if v is None else v) for v in l) for l in lignes)
    return ('<?xml version="1.0" encoding="utf-8"?><VOTABLE version="1.4" xmlns="http://www.ivoa.net/xml/VOTable/v1.3">'
            '<RESOURCE type="results"><INFO name="QUERY_STATUS" value="OK"/><TABLE>%s<DATA><TABLEDATA>%s</TABLEDATA>'
            '</DATA></TABLE><INFO name="QUERY_STATUS" value="OVERFLOW"/></RESOURCE></VOTABLE>' % (f, tr)).encode()


CHAMPS_MAST = ['obs_collection', 'instrument_name', 'obs_id', 'obsid', 'calib_level', 'dataproduct_type', 'filters',
               's_ra', 's_dec', 't_min', 't_obs_release', 'target_name', 'proposal_id', 'proposal_pi', 'obs_title',
               'jpegurl', 'dataurl', 'datarights', 'em_min', 'em_max', 's_region']


def ligne_mast(col, obs, fichier, calib=3, droits='PUBLIC', release=59000.0, ra=274.7, dec=-13.8, filtre='F770W',
               region=''):
    return [col, 'MIRI/IMAGE' if col == 'JWST' else 'ACS/WFC', obs, '1', calib, 'image', filtre, ra, dec, '59821.2',
            release, 'M-16', '2739', 'Doe, J.', 'Titre', 'mast:%s/product/%s.jpg' % (col, obs),
            'mast:%s/product/%s' % (col, fichier), droits, '6600.0', '8800.0', region]


def reponses_simulees(monkeypatch, table):
    """`table` : [(fragment d'adresse ou de corps, bytes | Exception)] ; la première qui correspond répond."""
    vues = []

    def faux(url, data=None, delai=B.DELAI, en_tetes=None, service=''):
        import urllib.parse
        cle = url + ' ' + (urllib.parse.unquote_plus(data.decode('utf-8', 'replace')) if data else '')
        vues.append(cle)
        for fragment, rep in table:
            if fragment in cle:
                if isinstance(rep, Exception):
                    raise rep
                return rep
        raise AssertionError('requête inattendue : ' + cle[:300])
    monkeypatch.setattr(B, 'lire_url', faux)
    for m in ('eso', 'irsa', 'mast', 'sol', 'planetes'):
        mod = __import__('coupole.modules.archives.services.' + m, fromlist=['x'])
        if hasattr(mod, 'lire_url'):
            monkeypatch.setattr(mod, 'lire_url', faux)
    monkeypatch.setattr(B, 'INTERVALLE_MIN', 0.0)
    return vues


# ============================================================================================ socle
def test_votable_csv_et_erreur():
    b = votable(['a', 'b'], [[1, 'x&amp;y'], [2, '']])
    assert B.lire_tableau(b) == [{'a': '1', 'b': 'x&y'}, {'a': '2', 'b': ''}]
    assert B.lire_tableau(b'#c\na,b\n1,2\n') == [{'a': '1', 'b': '2'}]
    with pytest.raises(ValueError, match='Unknown column'):
        B.lire_tableau(votable([], [], erreur='Unknown column "x"'))


def test_dates_et_droits():
    assert B.mjd_vers_iso(51544.5) == '2000-01-01T12:00:00'
    assert B.mjd_vers_iso('') == '' and B.mjd_vers_iso('nan') == ''
    assert B.iso_normal('2009-11-09 07:03:22.467Z') == '2009-11-09T07:03:22'
    assert B.iso_normal('2013-02-10') == '2013-02-10'
    assert B.deja_public('2000-01-01T00:00:00') and not B.deja_public('2999-01-01T00:00:00')
    assert not B.deja_public('2000-01-01', 'EXCLUSIVE_ACCESS') and B.deja_public('', 'PUBLIC')
    assert B.dans_periode('2020-05-03T01:00:00', '2020-05-01', '2020-05-03')
    assert not B.dans_periode('2020-05-04T01:00:00', '2020-05-01', '2020-05-03')


def test_geometrie():
    assert B.distance_deg(10, 20, 10, 20) == 0
    assert abs(B.distance_deg(0, 0, 0, 1) - 1) < 1e-12
    assert abs(B.distance_deg(359.9, 0, 0.1, 0) - 0.2) < 1e-9
    (a0, b0), = B.boite_ra(180, 0, 1)
    assert 178.99 < a0 < 179.0 and 181.0 < b0 < 181.01
    a = B.boite_ra(0.5, 0, 1)
    assert a[0][0] > 359 and a[1][0] == 0.0 and abs(a[1][1] - 1.5) < 1e-3
    assert B.boite_ra(10, 89.5, 1) is None                        # pôle : pas de contrainte en RA
    carre = B.polygone('POLYGON ICRS 10 10 10.2 10 10.2 10.2 10 10.2')
    assert B.point_dans_polygone(10.1, 10.1, carre) and not B.point_dans_polygone(10.3, 10.1, carre)
    o = B.observation(ra=11.0, dec=10.1)
    assert B.recouvre(o, 10.1, 10.1, 0.01, 'POLYGON 10 10 10.2 10 10.2 10.2 10 10.2')   # cible dans l'empreinte
    assert not B.recouvre(B.observation(ra=11.0, dec=10.1), 10.1, 10.1, 0.01, '')


@pytest.mark.parametrize('texte,attendu', [('83.822 -5.391', (83.822, -5.391)), ('83.822, +5.391', (83.822, 5.391)),
                                           ('05:35:17.3 -05:23:28', (83.82208, -5.39111)),
                                           ('5h35m17.3s -5d23m28s', (83.82208, -5.39111)), ('M 42', None),
                                           ('400 10', None), ('NGC 3324', None)])
def test_coordonnees(texte, attendu):
    c = R.lire_coordonnees(texte)
    if attendu is None:
        assert c is None
    else:
        assert abs(c[0] - attendu[0]) < 1e-4 and abs(c[1] - attendu[1]) < 1e-4


def test_filtres_communs():
    obs = [B.observation(id='a', mission='JWST', instrument='NIRCAM/IMAGE', filtre='F444W', debut='2022-07-01T00:00:00',
                         final=True), B.observation(id='b', mission='HST', instrument='ACS/WFC', filtre='F658N',
                                                    debut='2005-01-01', final=True),
           B.observation(id='c', mission='HST', instrument='ACS/WFC', filtre='F658N', final=False),
           B.observation(id='d', mission='JWST', instrument='MIRI', filtre='F770W', public=False, final=True),
           B.observation(id='e', mission='HLA', instrument='WFC3', filtre='F128N;F110W', final=True)]
    ids = lambda q: [o['id'] for o in B.filtrer(obs, q)]
    assert ids(B.Requete()) == ['a', 'b', 'e']
    assert ids(B.Requete(finaux=False, publics=False)) == ['a', 'b', 'c', 'd', 'e']
    assert ids(B.Requete(missions=('jwst',), publics=False)) == ['a', 'd']
    assert ids(B.Requete(instruments=('nircam',))) == ['a']
    assert ids(B.Requete(filtres=('F110W',))) == ['e']
    assert ids(B.Requete(date_min='2010-01-01')) == ['a']


# ============================================================================================ archives
def test_mast_produits_finaux_publics_et_boite(monkeypatch):
    lignes = [ligne_mast('JWST', 'jw1', 'jw1_i2d.fits'),
              ligne_mast('JWST', 'jw2', 'jw2_i2d.fits', droits='EXCLUSIVE_ACCESS', release=99999),
              ligne_mast('JWST', 'jw3', 'jw3_cal.fits', calib=2),
              ligne_mast('HST', 'j9', 'j9_drz.fits', filtre='F658N'),
              ligne_mast('HST', 'j8', 'j8_drc.fits', ra=274.9, filtre='F814W'),                     # trop loin
              ligne_mast('HST', 'j7', 'j7_drc.fits', ra=274.9, filtre='F435W',                     # empreinte
                         region='POLYGON 274.6 -13.9 274.95 -13.9 274.95 -13.7 274.6 -13.7'),
              ligne_mast('HLA', 'x', 'x.fits')]
    vues = reponses_simulees(monkeypatch, [('/sync', votable(CHAMPS_MAST, lignes))])
    q = B.Requete(ra=274.7, dec=-13.8, rayon=3 / 60)
    obs = S.ARCHIVES['mast'].chercher(q)
    assert 'dbo.obspointing' in vues[0] and 's_ra BETWEEN' in vues[0] and 'CONTAINS' not in vues[0]
    par = {o['obs_id']: o for o in obs}
    assert set(par) == {'jw1', 'jw2', 'jw3', 'j9', 'j7'}                # HLA ignorée (collection non demandée)
    assert par['jw1']['final'] and par['jw1']['public'] and par['jw1']['credit'] == 'NASA/ESA/CSA, STScI'
    assert not par['jw2']['public'] and not par['jw3']['final'] and par['j9']['credit'] == 'NASA/ESA, STScI'
    assert par['jw1']['url'] == 'https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:JWST/product/jw1_i2d.fits'
    assert par['jw1']['apercu'].endswith('jw1.jpg') and par['jw1']['lambda_nm'] == 7700
    assert [o['obs_id'] for o in B.filtrer(obs, q)] == ['jw1', 'j9', 'j7']
    assert S.ARCHIVES['mast'].chercher(B.Requete(ra=1, dec=2, missions=('ESO',))) == []


def test_mast_requete_pres_de_ra_zero():
    adql = S.ARCHIVES['mast'].requete_adql(B.Requete(ra=0.05, dec=10, rayon=0.05, date_min='2020-01-01'), ['JWST'])
    assert ' OR ' in adql and 't_min >= 58849' in adql


def test_eso_irsa_noirlab_koa_sdss(monkeypatch):
    eso = ('obs_collection,instrument_name,obs_id,dp_id,calib_level,dataproduct_subtype,filter,em_min,em_max,s_ra,s_dec,'
           't_min,obs_release_date,target_name,proposal_id,access_estsize,obs_title,obs_creator_name,facility_name\n'
           'HAWKI,HAWKI,1,ADP.2016-07-26T11:56:16.449,2,pawprint,H,1.4e-6,1.55e-6,83.8,-5.4,54779.28,'
           '2009-11-09T07:03:22.467Z,Field-B3,082.C-0032(A),104904,,,ESO-VLT-U4\n'
           'VIRCAM,VIRCAM,2,ADP.X,3,tile,Ks,1.9e-6,2.3e-6,83.8,-5.4,54779.28,2999-01-01T00:00:00Z,F,1,10,,,\n').encode()
    irsa = ('s_ra,s_dec,instrument_name,dataproduct_subtype,calib_level,energy_bandpassname,obs_id,em_min,em_max,'
            'access_url,access_estsize,obs_collection,proposal_id,proposal_pi,proposal_title,target_name,'
            'obs_release_date,t_min\n'
            '83.8,-5.4,IRAC,science,3,IRAC1,o1,3.1e-6,3.9e-6,https://irsa.ipac.caltech.edu/x/a.mosaic.fits,2978,'
            'spitzer_seip,,,,,2013-12-19 00:00:00,\n'
            '83.8,-5.4,IRAC,weight,3,IRAC1,o1,3.1e-6,3.9e-6,https://irsa.ipac.caltech.edu/x/a.cov.fits,2978,'
            'spitzer_seip,,,,,2013-12-19 00:00:00,\n'
            '83.8,-5.4,IRAC,auxiliary,3,IRAC1,o1,,,https://irsa.ipac.caltech.edu/x/a.tbl,1,spitzer_seip,,,,,,\n').encode()
    noir = json.dumps([{'META': {}}, {'md5sum': 'abc', 'archive_filename': '/net/x/tu1.fits.fz', 'instrument': 'decam',
                                     'telescope': 'ct4m', 'proc_type': 'stacked', 'prod_type': 'image',
                                     'obs_type': 'object', 'release_date': '2013-02-10', 'ifilter':
                                     'r DECam SDSS c0002 6415.0 1480.0', 'proposal': '2013A-0351', 'ra_center': 83.82,
                                     'dec_center': -5.39, 'filesize': 422429760,
                                     'url': 'https://astroarchive.noirlab.edu/api/retrieve/abc/',
                                     'dateobs_center': '2013-02-11T01:44:50Z'}]).encode()
    koa = ('koaid,instrume,filehand,ra,dec,date_obs,utdatetime,propint,filesize_mb,progid,progpi,progtitl,targname,'
           'koaimtyp,filter\nN2.1.fits,NIRC2,/koadata9/N2.1.fits,83.81,-5.37,2011-12-18,2011-12-18 09:36:51,18,4.2,'
           'U1,Doe,T,tt153,object,Lp\n').encode()
    sdss = b'#Table1\nrun,rerun,camcol,field,ra,dec,mjd_r\n3699,301,6,100,83.83,-5.39,52704.4\n'
    reponses_simulees(monkeypatch, [('tap_obs', eso), ('SIA?COLLECTION=spitzer_seip', irsa), ('SIA?', b's_ra\n'),
                                    ('adv_search', noir), ('koa.ipac', koa), ('SqlSearch', sdss)])
    q = B.Requete(ra=83.82, dec=-5.39, rayon=3 / 60, finaux=False, publics=False)
    res = {r.archive: r for r in R.chercher(q, ('eso', 'irsa', 'noirlab', 'koa', 'sdss'))}
    assert all(not r.erreur for r in res.values()), {k: r.erreur for k, r in res.items()}
    e = {o['obs_id']: o for o in res['eso'].observations}
    assert e['1']['taille'] == 104904000 and e['1']['credit'] == 'ESO (082.C-0032(A))' and e['1']['public']
    assert e['1']['url'] == 'https://dataportal.eso.org/dataPortal/file/ADP.2016-07-26T11:56:16.449'
    assert not e['2']['public'] and abs(e['1']['lambda_nm'] - 1475) < 1
    i = res['irsa'].observations
    assert [o['sous_type'] for o in i] == ['science', 'weight'] and i[0]['mission'] == 'Spitzer'
    assert i[0]['final'] and not i[1]['final'] and i[0]['taille'] == 2978 * 1024
    n = res['noirlab'].observations[0]
    assert n['final'] and n['lambda_nm'] == 641.5 and n['taille'] == 422429760 and n['fichier'] == 'tu1.fits.fz'
    k = res['koa'].observations[0]
    assert not k['final'] and k['publique'].startswith('2013-06-18') and k['public']
    assert k['url'].endswith('filehand=/koadata9/N2.1.fits')
    s = res['sdss'].observations
    assert [o['filtre'] for o in s] == list('ugriz') and s[2]['url'].endswith('/301/3699/6/frame-r-003699-6-0100.fits.bz2')
    # produits finaux seulement : KOA ne rend rien, IRSA perd les poids, SDSS reste
    q2 = B.Requete(ra=83.82, dec=-5.39, rayon=3 / 60)
    res2 = {r.archive: r for r in R.chercher(q2, ('irsa', 'koa', 'sdss'))}
    assert res2['koa'].observations == [] and len(res2['irsa'].observations) == 1 and len(res2['sdss'].observations) == 5


def test_archives_sans_acces_et_pannes(monkeypatch):
    from coupole.core import reseau
    reponses_simulees(monkeypatch, [('gemini', b'\nLogin Required. Please visit https://archive.gemini.edu/login'),
                                    ('tap_obs', reseau.ServiceInjoignable('timeout'))])
    res = {r.archive: r for r in R.chercher(B.Requete(ra=1, dec=2), ('goa', 'smoka', 'eso'))}
    assert res['goa'].compte_requis and res['smoka'].non_pris_en_charge and 'smoka.nao.ac.jp' in res['smoka'].erreur
    assert 'timeout' in res['eso'].erreur and res['eso'].observations == []


def test_missions_choisissent_les_archives(monkeypatch):
    vues = reponses_simulees(monkeypatch, [('SIA?', b's_ra\n')])
    R.chercher(B.Requete(ra=1, dec=2, missions=('WISE',)))
    assert vues and all('irsa' in v for v in vues) and any('wise_allwise' in v for v in vues)
    assert not any('spitzer' in v for v in vues)


def test_planetes_opus_et_pds(monkeypatch):
    opus = json.dumps({'page': [['vg-iss-1-j-c1627653', 'Voyager ISS', 'Jupiter', 'Io', '1979-03-01T18:03:31.640',
                                 'Orange', 'VGISS_5104/DATA/C16276XX/C1627653_RAW.LBL', '15.36']]}).encode()
    opus_co = json.dumps({'page': [['co-iss-n1579014742', 'Cassini ISS', 'Saturn', 'Enceladus', '2008-01-14T14:36:06',
                                    'CLEAR', 'COISS_2041/data/1578891812_1579027301/N1579014742_2.IMG', '60']]}).encode()
    pds = json.dumps({'response': {'docs': [{'identifier': ['JNCR_2016156_00R00189_V02'],
                                             'ATLAS_DATA_URL': 'https://pds-imaging.jpl.nasa.gov/data/juno//x/J.IMG',
                                             'ATLAS_LABEL_URL': 'https://pds-imaging.jpl.nasa.gov/data/juno//x/J.LBL',
                                             'ATLAS_THUMBNAIL_URL': 'https://x.nasa.gov/t.png', 'START_TIME':
                                             '2016-06-04T11:15:02.484Z', 'TARGET_NAME': 'JUPITER', 'FILTER_NAME': ['RED'],
                                             'ATLAS_PRODUCT_TYPE': 'rdr', 'LINES': 5120, 'LINE_SAMPLES': 1648,
                                             'SAMPLE_BITS': 16}]}}).encode()
    vues = reponses_simulees(monkeypatch, [('instrument=Voyager', opus), ('instrument=Cassini', opus_co),
                                           ('solr', pds)])
    q = B.Requete(cible='Saturne', date_max='2030-01-01')
    res = {r.archive: r for r in R.chercher(q, ('opus', 'pds', 'mast'))}
    assert any('target=Saturn' in v for v in vues) and any('START_TIME%3A%5B%2A+TO+2030' in v for v in vues)
    v = [o for o in res['opus'].observations if o['mission'] == 'Voyager'][0]
    assert v['url'].endswith('/holdings/volumes/VGISS_5xxx/VGISS_5104/DATA/C16276XX/C1627653_GEOMED.IMG')
    assert v['etiquette'].endswith('C1627653_GEOMED.LBL') and v['apercu'].endswith('C1627653_thumb.jpg')
    c = [o for o in res['opus'].observations if o['mission'] == 'Cassini'][0]
    assert c['url'].endswith('/holdings/calibrated/COISS_2xxx/COISS_2041/data/1578891812_1579027301/N1579014742_2_CALIB.IMG')
    j = res['pds'].observations[0]
    assert j['final'] and j['taille'] == 5120 * 1648 * 2 and j['credit'].startswith('NASA/JPL-Caltech/SwRI/MSSS')
    assert res['mast'].observations == []                           # archive céleste sans coordonnées : rien demandé


# ============================================================================================ extraction FITS
def wcs_entete(ra=83.82, dec=-5.39, pas=0.1 / 3600, nx=200, ny=150, rot=0.0):
    from astropy.io import fits
    h = fits.Header()
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    h.update({'CTYPE1': 'RA---TAN', 'CTYPE2': 'DEC--TAN', 'CRVAL1': ra, 'CRVAL2': dec, 'CRPIX1': nx / 2 + 0.5,
              'CRPIX2': ny / 2 + 0.5, 'CD1_1': -pas * c, 'CD1_2': pas * s, 'CD2_1': pas * s, 'CD2_2': pas * c,
              'RADESYS': 'ICRS', 'EQUINOX': 2000.0})
    return h


def fits_multi(chemin, donnees, bunit='MJy/sr', sci=True, n_detecteurs=0, gz=False, entier=False):
    from astropy.io import fits
    p = fits.PrimaryHDU()
    p.header.update({'TELESCOP': 'JWST', 'INSTRUME': 'NIRCAM', 'FILTER': 'F444W', 'DATE-OBS': '2022-07-01',
                     'PROGRAM': '02739', 'TARGPROP': 'M16'})
    hdus = [p]
    if n_detecteurs:
        for k in range(n_detecteurs):
            h = wcs_entete(ra=83.82 + 0.01 * k)
            hdus.append(fits.ImageHDU(donnees.astype(np.float32) + k, header=h, name='CHIP%d' % (k + 1)))
    else:
        h = wcs_entete(nx=donnees.shape[1], ny=donnees.shape[0])
        h['BUNIT'] = bunit
        h['PHOTMJSR'] = 0.25
        d = donnees.astype(np.int16) if entier else donnees.astype(np.float32)
        hdu = fits.ImageHDU(d, header=h, name='SCI' if sci else 'IMG')
        if entier:
            hdu.header['BZERO'] = 32768
        hdus += [hdu, fits.ImageHDU(np.ones_like(donnees, dtype=np.float32), name='ERR')]
    fits.HDUList(hdus).writeto(chemin, overwrite=True)
    if gz:
        with open(chemin, 'rb') as f, gzip.open(chemin + '.gz', 'wb') as g:
            g.write(f.read())
        os.remove(chemin)
        return chemin + '.gz'
    return chemin


def test_extraction_sci_wcs_nan_masque_credit(tmp_path):
    d = np.random.default_rng(1).normal(100, 5, (150, 200)).astype(np.float32)
    d[:10, :] = np.nan
    src = fits_multi(str(tmp_path / 'jw_i2d.fits'), d)
    o = B.observation(id='mast:jw', archive='mast', mission='JWST', credit='NASA/ESA/CSA, STScI', cible='M 16',
                      lambda_nm=4440.0, page='https://mast.stsci.edu/x')
    for fmt in ('xisf', 'fits'):
        r = EX.preparer(src, str(tmp_path / fmt / 'jw_i2d_sci'), o, fmt)
        assert r['extension'] == 1 and r['nan'] == 2000 and r['wcs'] and r['bunit'] == 'MJy/sr'
        assert os.path.exists(r['masque'])
        lu, h = EX.lire_prepare(r['chemin'])
        assert np.isnan(lu[:10]).all() and np.allclose(lu[10:], d[10:])        # NaN rétablis par le masque
        assert h['CREDIT'] == 'NASA/ESA/CSA, STScI' and h['TELESCOP'] == 'JWST' and h['FILTER'] == 'F444W'
        assert h['BUNIT'] == 'MJy/sr' and h['PHOTMJSR'] == 0.25 and h['ARCHID'] == 'mast:jw' and h['LAMBDA'] == 4440.0
        assert abs(h['CRVAL1'] - 83.82) < 1e-12 and h['NANCOUNT'] == 2000
        assert EX.wcs_celeste(h)
    from coupole.core import xisf
    _, info = xisf.lire(str(tmp_path / 'xisf' / 'jw_i2d_sci.xisf'), strict=True)
    lo, hi = EX.bornes(np.where(np.isfinite(d), d, 0))
    b = info['bounds']
    b = tuple(float(x) for x in b.split(':')) if isinstance(b, str) else tuple(b)
    assert b == (lo, hi)


def test_extraction_detecteurs_cube_entier_gz(tmp_path):
    d = np.zeros((40, 50), dtype=np.float32)
    src = fits_multi(str(tmp_path / 'paw.fits'), d, n_detecteurs=4)
    r = EX.preparer(src, str(tmp_path / 'paw_sci'), None, 'fits')
    assert len(r['chemins']) == 4 and r['chemins'][3].endswith('paw_sci_d4.fits')
    lu, h = EX.lire_prepare(r['chemins'][2])
    assert lu.max() == 2 and h['SCIEXT'] == 3
    from astropy.io import fits
    fits.HDUList([fits.PrimaryHDU(np.zeros((3, 10, 10), np.float32))]).writeto(str(tmp_path / 'cube.fits'))
    with pytest.raises(EX.Inexploitable):
        EX.preparer(str(tmp_path / 'cube.fits'), str(tmp_path / 'cube_sci'))
    src = fits_multi(str(tmp_path / 'brut.fits'), np.arange(600).reshape(20, 30), sci=False, entier=True)
    r = EX.preparer(src, str(tmp_path / 'brut_sci'), None, 'fits')            # BZERO : lecture sans memmap
    lu, _ = EX.lire_prepare(r['chemin'])
    assert lu[0, 5] == 5 + 32768
    src = fits_multi(str(tmp_path / 'z.fits'), np.ones((20, 30)), gz=True)
    assert EX.preparer(src, str(tmp_path / 'z_sci'))['forme'] == (20, 30)


# ============================================================================================ formats planétaires
def label_pds3(lignes, colonnes, sample_type, bits, pointeur, rb=None, extra=''):
    return ('PDS_VERSION_ID = PDS3\r\nRECORD_TYPE = FIXED_LENGTH\r\nRECORD_BYTES = %d\r\n^IMAGE = %s\r\n'
            'TARGET_NAME = "IO"\r\nFILTER_NAME = ("RED", "GREEN")\r\nSTART_TIME = 1979-03-01T18:03:31\r\n'
            'EXPOSURE_DURATION = 192.0 <ms>\r\nDESCRIPTION = "une description\r\nsur deux lignes"\r\n'
            'OBJECT = IMAGE\r\n  LINES = %d\r\n  LINE_SAMPLES = %d\r\n  SAMPLE_TYPE = %s\r\n  SAMPLE_BITS = %d\r\n%s'
            'END_OBJECT = IMAGE\r\nEND\r\n' % (rb or colonnes * bits // 8, pointeur, lignes, colonnes, sample_type,
                                                 bits, extra))


def test_pds3_detache_attache_et_mise_a_l_echelle(tmp_path):
    img = (np.arange(12 * 20) % 251).reshape(12, 20).astype('>i2')
    (tmp_path / 'a.IMG').write_bytes(b'\0' * 40 + img.tobytes())              # 1 enregistrement de 40 octets avant
    (tmp_path / 'a.LBL').write_text(label_pds3(12, 20, 'MSB_INTEGER', 16, '("a.IMG", 2)'), encoding='latin-1')
    d, m = PDS.lire(tmp_path / 'a.IMG', str(tmp_path / 'a.LBL'))
    assert (d == img).all() and m['TARGET_NAME'] == 'IO' and m['FILTER_NAME'] == 'RED, GREEN'
    # pointeur en octets, LSB, mise à l'échelle
    img2 = np.linspace(0, 1000, 6 * 8).reshape(6, 8).astype('<u2')
    (tmp_path / 'b.IMG').write_bytes(b'\0' * 100 + img2.tobytes())
    (tmp_path / 'b.LBL').write_text(label_pds3(6, 8, 'LSB_UNSIGNED_INTEGER', 16, '("b.IMG", 101 <BYTES>)',
                                               extra='  SCALING_FACTOR = 0.5\r\n  OFFSET = 10\r\n'), encoding='latin-1')
    d, _ = PDS.lire(tmp_path / 'b.IMG', str(tmp_path / 'b.LBL'))
    assert np.allclose(d, img2 * 0.5 + 10)
    # label attaché, réels PC_REAL, préfixes de ligne
    lab = label_pds3(4, 5, 'PC_REAL', 32, '2', rb=512, extra='  LINE_PREFIX_BYTES = 4\r\n').encode('latin-1')
    corps = np.arange(20, dtype='<f4').reshape(4, 5)
    lignes = b''.join(b'PREF' + corps[i].tobytes() for i in range(4))
    (tmp_path / 'c.IMG').write_bytes(lab.ljust(512, b' ') + lignes)
    d, m = PDS.lire(tmp_path / 'c.IMG')
    assert (d == corps).all() and m['_format'] == 'PDS3'
    (tmp_path / 'd.IMG').write_bytes(label_pds3(4, 5, 'VAX_REAL', 32, '2', rb=512).encode().ljust(512) + b'\0' * 80)
    with pytest.raises(PDS.FormatNonGere):
        PDS.lire(tmp_path / 'd.IMG')


def vicar(nl, ns, fmt='HALF', intfmt='LOW', nlb=0, nbb=0, donnees=b''):
    tete = "LBLSIZE=%d FORMAT='%s' TYPE='IMAGE' ORG='BSQ' NL=%d NS=%d NB=1 NBB=%d NLB=%d INTFMT='%s' REALFMT='RIEEE'"
    taille = {'BYTE': 1, 'HALF': 2, 'REAL': 4}[fmt]
    rec = nbb + ns * taille
    lbl = rec * math.ceil(160 / rec)
    t = (tete % (lbl, fmt, nl, ns, nbb, nlb, intfmt)).encode().ljust(lbl, b' ')
    return t + b'\xff' * (rec * nlb) + donnees


def test_vicar_et_label_cassini_decale(tmp_path):
    corps = (np.arange(30) * 3).reshape(5, 6).astype('<i2')
    (tmp_path / 'v.IMG').write_bytes(vicar(5, 6, donnees=corps.tobytes()))
    d, m = PDS.lire(tmp_path / 'v.IMG')
    assert (d == corps).all() and m['_format'] == 'VICAR'
    # Cassini CISSCAL : une ligne binaire (NLB=1) avant l'image ; le label PDS3 détaché dit « enregistrement 2 »
    reel = np.linspace(0, 0.6, 4 * 4).reshape(4, 4).astype('<f4')
    brut = vicar(4, 4, fmt='REAL', nlb=1, donnees=reel.tobytes())
    (tmp_path / 'N_CALIB.IMG').write_bytes(brut)
    (tmp_path / 'N_CALIB.LBL').write_text(label_pds3(4, 4, 'PC_REAL', 32, '("N_CALIB.IMG", 2)', rb=32), encoding='latin-1')
    d, m = PDS.lire(tmp_path / 'N_CALIB.IMG', str(tmp_path / 'N_CALIB.LBL'))
    assert np.allclose(d, reel) and m['_format'] == 'VICAR + PDS3' and m['TARGET_NAME'] == 'IO'


def test_pds4_et_conversion_planetaire(tmp_path):
    a = np.arange(6 * 7, dtype='>u2').reshape(6, 7)
    (tmp_path / 'p.dat').write_bytes(b'\0' * 16 + a.tobytes())
    (tmp_path / 'p.xml').write_text(
        '<?xml version="1.0"?><Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">'
        '<Identification_Area><logical_identifier>urn:x</logical_identifier><title>T</title></Identification_Area>'
        '<Observation_Area><Time_Coordinates><start_date_time>2016-07-01T00:00:00Z</start_date_time>'
        '</Time_Coordinates><Target_Identification><name>Jupiter</name></Target_Identification></Observation_Area>'
        '<File_Area_Observational><File><file_name>p.dat</file_name></File><Array_2D_Image><offset unit="byte">16'
        '</offset><axes>2</axes><Element_Array><data_type>UnsignedMSB2</data_type><scaling_factor>2</scaling_factor>'
        '</Element_Array><Axis_Array><axis_name>Line</axis_name><elements>6</elements></Axis_Array><Axis_Array>'
        '<axis_name>Sample</axis_name><elements>7</elements></Axis_Array></Array_2D_Image></File_Area_Observational>'
        '</Product_Observational>', encoding='utf-8')
    d, m = PDS.lire(tmp_path / 'p.xml')
    assert np.allclose(d, a * 2) and m['TARGET_NAME'] == 'Jupiter'
    o = B.observation(id='pds:x', archive='pds', mission='Juno', format='pds4', credit='NASA/JPL-Caltech/SwRI/MSSS')
    r = EX.preparer(str(tmp_path / 'p.xml'), str(tmp_path / 'p_sci'), o, 'xisf')
    lu, h = EX.lire_prepare(r['chemin'])
    assert np.allclose(lu, (a * 2)[::-1])                     # ligne 1 PDS (haut) → dernière ligne FITS
    assert not r['wcs'] and h['PLANFMT'] == 'PDS4' and h['CREDIT'].startswith('NASA/JPL')


# ============================================================================================ alignement
def ciel(entete, etoiles, forme, fwhm_px=3.0, fond=10.0, flux=1000.0):
    """Image synthétique d'étoiles gaussiennes aux positions célestes données."""
    from astropy.wcs import WCS
    w = WCS(entete)
    ny, nx = forme
    y, x = np.mgrid[:ny, :nx]
    img = np.full(forme, fond, dtype=np.float64)
    s = fwhm_px / 2.3548
    for ra, dec in etoiles:
        px, py = w.all_world2pix([[ra, dec]], 0)[0]
        img += flux / (2 * math.pi * s * s) * np.exp(-((x - px) ** 2 + (y - py) ** 2) / (2 * s * s))
    return img.astype(np.float32)


def ecrire_prepare(chemin, img, entete, bunit, filtre, lam, instrument='NIRCAM'):
    from astropy.io import fits
    h = entete.copy()
    h.update({'BUNIT': bunit, 'FILTER': filtre, 'LAMBDA': lam, 'INSTRUME': instrument})
    fits.PrimaryHDU(img, header=h).writeto(chemin, overwrite=True)
    return chemin


ETOILES = [(83.8200, -5.3900), (83.8215, -5.3890), (83.8188, -5.3912), (83.8209, -5.3920)]


def centroide(img, w, ra, dec, r=6):
    px, py = w.all_world2pix([[ra, dec]], 0)[0]
    x0, y0 = int(round(px)), int(round(py))
    bloc = img[y0 - r:y0 + r + 1, x0 - r:x0 + r + 1].astype(np.float64)
    bloc = bloc - np.nanmedian(img)
    bloc[bloc < 0] = 0
    yy, xx = np.mgrid[y0 - r:y0 + r + 1, x0 - r:x0 + r + 1]
    return (xx * bloc).sum() / bloc.sum(), (yy * bloc).sum() / bloc.sum()


@pytest.mark.parametrize('avec_reproject,methode', [(True, 'bilineaire'), (True, 'adaptative'), (True, 'exacte'),
                                                    (False, 'bilineaire')])
def test_alignement_etoiles_superposees(tmp_path, monkeypatch, avec_reproject, methode):
    if not avec_reproject:
        monkeypatch.setattr(AL, 'reproject_disponible', lambda: False)
    elif not AL.reproject_disponible():
        pytest.skip('reproject absent')
    h1 = wcs_entete(pas=0.06 / 3600, nx=260, ny=240)
    h2 = wcs_entete(pas=0.11 / 3600, nx=150, ny=140, rot=27.0, ra=83.8203)       # autre pas, tourné, décalé
    a = ecrire_prepare(str(tmp_path / 'a.fits'), ciel(h1, ETOILES, (240, 260)), h1, 'MJy/sr', 'F200W', 1990.0)
    b = ecrire_prepare(str(tmp_path / 'b.fits'), ciel(h2, ETOILES, (140, 150), fwhm_px=2.0), h2, 'ELECTRONS/S',
                       'F444W', 4440.0)
    r = AL.aligner([a, b], str(tmp_path / 'al'), reference=0, recadrer=False, fmt='fits', methode=methode)
    from astropy.io import fits
    from astropy.wcs import WCS
    ia = fits.getdata(r['fichiers'][0])
    ib = fits.getdata(r['fichiers'][1])
    w = WCS(fits.getheader(r['fichiers'][0]))
    assert ia.shape == ib.shape == (240, 260)
    for ra, dec in ETOILES[:3]:
        xa, ya = centroide(ia, w, ra, dec)
        xb, yb = centroide(ib, w, ra, dec)
        assert math.hypot(xa - xb, ya - yb) < 0.15, (ra, dec, xa, xb, ya, yb)
    # électrons/s (par pixel) : le flux d'une étoile est conservé au changement de pas (fond multiplié par le
    # rapport des surfaces de pixel, (0,06/0,11)²)
    tb = fits.getdata(b)
    rapport = (0.06 / 0.11) ** 2
    from astropy.wcs import WCS as W2
    wb = W2(fits.getheader(b))
    for ra, dec in ETOILES[:3]:
        xa, ya = (int(round(v)) for v in w.all_world2pix([[ra, dec]], 0)[0])
        xb, yb = (int(round(v)) for v in wb.all_world2pix([[ra, dec]], 0)[0])
        fa = (ib[ya - 12:ya + 13, xa - 12:xa + 13] - 10.0 * rapport).sum()
        fb = (tb[yb - 7:yb + 8, xb - 7:xb + 8] - 10.0).sum()
        assert abs(fa / fb - 1) < 0.03, (fa, fb)
    # MJy/sr (brillance) : la valeur du fond ne change pas
    assert abs(np.median(ia) - 10.0) < 0.05
    assert [c['couleur'] for c in r['composition']] == [(0.0, 0.5, 1.0), (1.0, 0.5, 0.0)]
    png = open(r['apercu'], 'rb').read()
    assert png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', png[16:24]) == (260, 240)
    texte = open(os.path.join(str(tmp_path / 'al'), 'composition.txt'), encoding='utf-8').read()
    assert 'R: (1.000*b_aligne)' in texte and 'B: (1.000*a_aligne)' in texte


def test_grille_optimale_et_recadrage(tmp_path):
    h1 = wcs_entete(pas=0.1 / 3600, nx=200, ny=200)
    h2 = wcs_entete(pas=0.1 / 3600, nx=200, ny=200, ra=83.82 + 10 / 3600)          # décalé de 10″ en RA
    a = ecrire_prepare(str(tmp_path / 'a.fits'), ciel(h1, ETOILES, (200, 200)), h1, 'MJy/sr', 'F', 1000.0)
    b = ecrire_prepare(str(tmp_path / 'b.fits'), ciel(h2, ETOILES, (200, 200)), h2, 'MJy/sr', 'G', 2000.0)
    r = AL.aligner([a, b], str(tmp_path / 'opt'), reference=None, recadrer=False, fmt='fits')
    assert r['forme'][1] > 280                                      # couvre les deux : ~ 200 + 100 px
    r2 = AL.aligner([a, b], str(tmp_path / 'rec'), reference=None, recadrer=True, fmt='fits')
    from astropy.io import fits
    d = fits.getdata(r2['fichiers'][0])
    assert r2['forme'][1] <= 205 and np.all(fits.getdata(r2['masque']) == 1) and np.all(d != 0)
    m = np.zeros((30, 40), bool)
    m[5:25, 3:30] = True
    m[0:30, 10] = True
    assert AL.plus_grand_rectangle(m) == (5, 25, 3, 30)


def test_composition_ordre_chromatique():
    c = AL.composition([('i3', 'F444W', None, 'NIRCAM'), ('i1', 'F090W', None, 'NIRCAM'), ('i2', 'F200W', None, 'NIRCAM')])
    assert [x['rang'] for x in c] == [2, 0, 1] and c[1]['couleur'] == (0.0, 0.0, 1.0) and c[0]['couleur'] == (1.0, 0.0, 0.0)
    assert AL.lambda_filtre('F435W', 'ACS/WFC') == 435 and AL.lambda_filtre('F160W', 'WFC3/IR') == 1600
    assert AL.lambda_filtre('F1130W') == 11300 and AL.lambda_filtre('F444W', 'NIRCAM/IMAGE') == 4440
    six = AL.composition([('f%d' % k, '', 400.0 + 100 * k) for k in range(6)])
    teintes = [x['couleur'] for x in sorted(six, key=lambda x: x['rang'])]
    assert teintes[0][2] == 1.0 and teintes[-1] == (1.0, 0.0, 0.0)              # du bleu au rouge
    assert AL.identifiant_pixinsight('jw02739-o002_t001') == 'jw02739_o002_t001'
    assert AL.identifiant_pixinsight('30002561.x') == '_30002561_x'
    assert not AL.par_pixel('MJy/sr') and not AL.par_pixel('nanomaggy/arcsec2') and AL.par_pixel('ELECTRONS/S')


# ============================================================================================ téléchargement
@pytest.fixture
def serveur(tmp_path):
    from tests.serveur_local import ServeurLocal
    d = np.random.default_rng(3).normal(50, 2, (80, 90)).astype(np.float32)
    d[0, 0] = np.nan
    c1 = fits_multi(str(tmp_path / 'src1.fits'), d)
    c2 = fits_multi(str(tmp_path / 'src2.fits'), d + 1)
    s = ServeurLocal({'/a_i2d.fits': open(c1, 'rb').read(), '/b_drz.fits': open(c2, 'rb').read(),
                      '/mauvais.fits': b'pas un fits' * 300})
    yield s
    s.http.shutdown()


def obs_locale(serveur, chemin, mission='JWST', ident=None, taille=None):
    return B.observation(id=ident or 'mast:' + chemin.strip('/'), archive='mast', mission=mission, instrument='NIRCAM/IMAGE',
                         filtre='F444W' if 'a_' in chemin else 'F200W', url=serveur.url(chemin), fichier=chemin.strip('/'),
                         cible='M 16', credit='NASA/ESA/CSA, STScI', taille=taille, public=True, final=True)


def test_telechargement_reprise_etat_possession(serveur, tmp_path):
    obs = [obs_locale(serveur, '/a_i2d.fits'), obs_locale(serveur, '/b_drz.fits'),
           obs_locale(serveur, '/mauvais.fits')]
    e = T.estimer([dict(o) for o in obs])
    assert e['mesures'] == 3 and e['octets'] == sum(len(v) for v in serveur.fichiers.values())
    serveur.pannes['/a_i2d.fits'] = 'coupure_une_fois'
    evts = []
    t = T.Telechargement(tmp_path / 'sortie', obs, cible='M 16', fmt='xisf', rapporter=evts.append, debit_octets_s=0)
    b = t.executer()
    assert b['ok'] == 2 and b['echec'] == 1
    p = T.possession(tmp_path / 'sortie')
    assert p['mast:a_i2d.fits']['statut'] == 'ok' and p['mast:mauvais.fits']['statut'] == 'echec'
    racine = T.dossier_archives(tmp_path / 'sortie')
    prep = os.path.join(racine, p['mast:a_i2d.fits']['prepare'])
    assert prep.endswith(os.path.join('JWST', 'M_16', 'NIRCAM_IMAGE', 'F444W', 'a_i2d_sci.xisf')) and os.path.exists(prep)
    assert os.path.exists(os.path.join(racine, 'JWST', 'M_16', 'NIRCAM_IMAGE', 'F444W', 'a_i2d.fits'))
    journal = open(os.path.join(racine, '_etat', 'JOURNAL.txt'), encoding='utf-8').read()
    assert 'a_i2d_sci.xisf' in journal and ' / ' in journal
    n = len(serveur.requetes)
    b2 = T.Telechargement(tmp_path / 'sortie', obs[:2], cible='M 16').executer()       # déjà là : aucune requête
    assert b2['deja'] == 2 and len(serveur.requetes) == n
    os.remove(prep)                                                                       # effacé à la main
    assert T.possession(tmp_path / 'sortie')['mast:a_i2d.fits']['statut'] == 'absente'


def test_telechargement_sans_original_et_annulation(serveur, tmp_path):
    obs = [obs_locale(serveur, '/b_drz.fits', mission='HST')]
    T.Telechargement(tmp_path / 's', obs, garder_original=False, fmt='fits').executer()
    d = os.path.join(T.dossier_archives(tmp_path / 's'), 'HST', 'M_16', 'NIRCAM_IMAGE', 'F200W')
    assert sorted(os.listdir(d)) == ['b_drz_sci.fits', 'b_drz_sci_masque.fits']
    arret = threading.Event()
    arret.set()
    b = T.Telechargement(tmp_path / 's2', [obs_locale(serveur, '/a_i2d.fits')], arret=arret).executer()
    assert b.get('annule') == 1 and not b.get('ok')


def test_serveur_sans_requete_partielle(tmp_path):
    """Archive de l'ESO : 416 dès l'octet 0 → nouvel essai sans en-tête Range."""
    import http.server
    contenu = b'X' * 5000

    class G(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.headers.get('Range'):
                self.send_response(416)
                self.send_header('Content-Range', 'bytes */-1')
                self.end_headers()
                return
            self.send_response(200)
            self.send_header('Content-Length', str(len(contenu)))
            self.end_headers()
            self.wfile.write(contenu)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), G)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        from coupole.core import reseau
        st, n = reseau.telecharger('http://127.0.0.1:%d/f' % srv.server_address[1], str(tmp_path / 'f'), essais=3)
        assert st == 'ok' and open(tmp_path / 'f', 'rb').read() == contenu
    finally:
        srv.shutdown()


def test_seuil_et_estimation_par_echantillon(monkeypatch):
    from coupole.core import config
    monkeypatch.setitem(config.reglages().valeurs, 'archives_seuil_go', 0.5)
    assert T.seuil_octets() == 5e8
    vues = []
    monkeypatch.setattr(T, 'taille_mesuree', lambda url, delai=30: vues.append(url) or 1000)
    obs = [B.observation(id='x%d' % k, archive='sdss', instrument='SDSS imaging', filtre='r', url='u%d' % k)
           for k in range(200)]
    e = T.estimer(obs)
    assert len(vues) == T.PAR_GROUPE and e['estimes'] == 200 - T.PAR_GROUPE and e['octets'] == 200 * 1000


# ============================================================================================ échelle
def fausses_observations(n):
    rng = np.random.default_rng(5)
    missions = ['JWST', 'HST', 'ESO', 'Spitzer', 'WISE']
    return [B.observation(id='mast:o%06d' % k, archive='mast', mission=missions[k % 5], instrument='INS%d' % (k % 7),
                          filtre='F%03dW' % (100 + k % 50), lambda_nm=float(100 + k % 50) * 10,
                          debut='20%02d-01-01T00:00:00' % (k % 25), cible='C%d' % (k % 100), ra=float(rng.random()),
                          dec=float(rng.random()), distance=float(rng.random()), taille=int(rng.integers(1, 10**9)),
                          final=bool(k % 3), public=bool(k % 4)) for k in range(n)]


def test_cinquante_mille_observations_filtre_tri_possession(tmp_path):
    import time
    obs = fausses_observations(50_000)
    t0 = time.perf_counter()
    f = B.filtrer(obs, B.Requete(missions=('JWST', 'HST'), instruments=('INS1',)))
    tout = R.toutes([B.Resultat('mast', obs)])
    dt = time.perf_counter() - t0
    assert len(tout) == 50_000 and 0 < len(f) < 50_000 and dt < 2.0, dt
    # base d'état de 50 000 lignes : lecture de la possession
    from coupole.modules.ohp.pilote import Etat
    racine = T.dossier_archives(tmp_path)
    e = Etat(os.path.join(racine, '_etat', 'etat.sqlite'), 5.0)
    for o in obs:
        e.db.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', (o['id'], '', 'echec', 1, '{"raison": "x"}', ''))
    e.db.commit()
    e.fermer()
    t0 = time.perf_counter()
    p = T.possession(tmp_path)
    assert len(p) == 50_000 and time.perf_counter() - t0 < 2.0


def test_panneau_cinquante_mille_lignes(app_qt, tmp_path, monkeypatch):
    import time
    from coupole.modules.archives import gui as G
    monkeypatch.setattr(G.T, 'sortie_par_defaut', lambda: str(tmp_path))
    p = G.Panneau()
    p.resize(1400, 900)
    p.show()
    obs = fausses_observations(50_000)
    t0 = time.perf_counter()
    p._resultats((B.Requete(nom='M 16'), [B.Resultat('mast', obs)], obs))
    app_qt.processEvents()
    assert time.perf_counter() - t0 < 2.0
    for col in range(len(G.COLONNES)):
        t0 = time.perf_counter()
        p.vue.sortByColumn(col, G.Qt.SortOrder.DescendingOrder)
        app_qt.processEvents()
        assert time.perf_counter() - t0 < 2.0, (G.COLONNES[col], time.perf_counter() - t0)
    p.vue.selectRow(0)
    app_qt.processEvents()
    o = p.choisies()[0]
    assert o['credit'] in p.fiche.toHtml() or 'Crédit' in p.fiche.toHtml()
    p.vue.selectAll()
    app_qt.processEvents()
    assert len(p.choisies()) == 50_000
    p.arreter()
    p.close()


# ============================================================================================ interface et CLI
def test_panneau_fiche_et_alignement(app_qt, tmp_path, monkeypatch):
    from coupole.modules.archives import gui as G
    monkeypatch.setattr(G.T, 'sortie_par_defaut', lambda: str(tmp_path))
    p = G.Panneau()
    p.show()
    o = B.observation(id='eso:ADP.1', archive='eso', mission='ESO', instrument='HAWKI', filtre='J', public=False,
                      credit='ESO (082.C-0032(A))', conditions='arc_cond_eso', page='https://archive.eso.org/dataset/ADP.1',
                      programme='082.C-0032(A)')
    h = p.html_fiche(o)
    assert 'ESO (082.C-0032(A))' in h and 'archive.eso.org/dataset/ADP.1' in h
    from coupole.core.i18n import tr
    assert tr('arc_f_reservee').split()[0] in h
    p._resultats((B.Requete(nom='x'), [B.Resultat('goa', [], compte_requis=True)], []))
    assert tr('arc_nom_goa') in p.l_etat.text()
    p.aligner()                                                          # moins de deux images : message
    assert p.l_etat.text() == tr('arc_al_deux')
    assert len(p.aide_html()) > 500
    p.arreter()
    p.close()


def test_cli_liste_et_chercher(monkeypatch, capsys):
    from coupole import cli
    assert cli.main(['--lang', 'fr', 'archives', 'liste', '--json']) == 0
    l = json.loads(capsys.readouterr().out)
    assert {x['id'] for x in l} == set(S.ARCHIVES) and [x['id'] for x in l if x['defaut']] == ['mast', 'eso', 'irsa']
    reponses_simulees(monkeypatch, [('/sync', votable(CHAMPS_MAST, [ligne_mast('JWST', 'jw1', 'jw1_i2d.fits')]))])
    assert cli.main(['--lang', 'fr', 'archives', 'chercher', '274.7 -13.8', '--archive', 'mast', '--json']) == 0
    sortie = json.loads(capsys.readouterr().out)
    assert [o['obs_id'] for o in sortie] == ['jw1']
    assert cli.main(['--lang', 'fr', 'archives', 'chercher', '274.7 -13.8', '--archive', 'inconnue']) == 2
