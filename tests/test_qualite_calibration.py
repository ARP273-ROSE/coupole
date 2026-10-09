"""0.1.11 — Qualité des images sur les poses personnelles d'un utilisateur.

1. Lecteur XISF tolérant : N.I.N.A. écrit des `<FITSKeyword>` sans `comment` (« CD1_1 ») et l'ASIAIR n'écrit pas de
   `<Metadata>` ; la lecture stricte (nos fichiers) les refusait → 70 poses « mesurées » sans une valeur.
2. Jamais d'échec silencieux : colonne « état », motif lisible, résumé « N trouvées, M mesurées, K en erreur (…) ».
3. Poses de ciel seulement : flats, darks, bias, masters, sorties de WBPP exclus (dossier, nom, puis en-tête).

Les XISF « à la N.I.N.A. » et « à l'ASIAIR » sont construits ici octet par octet, comme ces logiciels les écrivent
(en-têtes relevés sur une vraie pose N.I.N.A. 3.2 d'une caméra CMOS de 61 Mpx et un vrai flat de l'ASIAIR, 2026).
"""
import os
import zlib

import numpy as np
import pytest

from coupole.core import xisf
from coupole.modules.qualite import calibration, mesures as M, moteur, rapport

from .synthetique import image

sans_sep = pytest.mark.skipif(not M.disponible(), reason='sep absent (dépendance facultative)')


def xisf_tiers(chemin, data, mots, metadata=True, codec='zlib+sh', proprietes=()):
    """XISF écrit comme N.I.N.A. (FITSKeyword sans `comment` possible, zlib+sh, bounds sur UInt16) ou comme
    l'ASIAIR (`metadata=False` : pas de <Metadata>, ColorFilterArray, commentaires vides)."""
    data = np.ascontiguousarray(data, '<u2')
    ny, nx = data.shape
    brut = data.tobytes()
    bloc = zlib.compress(xisf.melanger(brut, 2).tobytes(), 6) if codec == 'zlib+sh' else brut
    comp = ' compression="zlib+sh:%d:2"' % len(brut) if codec == 'zlib+sh' else ''
    cles = []
    for m in mots:
        if len(m) == 2:                                     # N.I.N.A. : pas d'attribut comment
            cles.append('<FITSKeyword name="%s" value="%s" />' % m)
        else:
            cles.append('<FITSKeyword name="%s" value="%s" comment="%s"/>' % m)
    props = ''.join('<Property id="%s" type="String" value="%s"/>' % p for p in proprietes)
    meta = ('<Metadata><Property id="XISF:CreationTime" type="String" value="2026-10-02T22:48:05Z"/>'
            '<Property id="XISF:CreatorApplication" type="String" value="N.I.N.A."/></Metadata>') if metadata else ''
    pos = 8192 if metadata else 4096

    def xml(p):
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<xisf version="1.0" xmlns="http://www.pixinsight.com/xisf">'
                '<Image geometry="%d:%d:1" sampleFormat="UInt16" bounds="0:65535" colorSpace="Gray" '
                'location="attachment:%d:%d"%s>%s%s%s</Image>%s</xisf>'
                % (nx, ny, p, len(bloc), comp, '' if metadata else
                   '<ColorFilterArray pattern="RGGB" width="2" height="2" name="RGGB Bayer Filter"/>',
                   ''.join(cles), props, meta)).encode('utf-8')
    x = xml(pos)
    assert 16 + len(x) <= pos
    entete = b'XISF0100' + len(x).to_bytes(4, 'little') + bytes(4) + x
    with open(chemin, 'wb') as f:
        f.write(entete + bytes(pos - len(entete)) + bloc)
    return chemin


MOTS_NINA = [('IMAGETYP', "'LIGHT'", 'Type of exposure'), ('EXPTIME', '300.0', '[s] Exposure duration'),
             ('EGAIN', '0.2467', '[e-/ADU] Electrons per A/D unit'), ('XPIXSZ', '3.76', '[um] Pixel X axis size'),
             ('CD1_1', '-0.000385009286428'), ('CD1_2', '0.00027098936217'), ('CD2_1', '-0.00027098936217'),
             ('CD2_2', '-0.000385009286428')]
MOTS_ASIAIR = [('CREATOR', "'ZWO 2600AIR'", ''), ('IMAGETYP', "'Light'", ''), ('EXPTIME', '120', ''),
               ('FOCALLEN', '489', ''), ('XPIXSZ', '3.76', '')]


def _ciel(n=256, fwhm=3.5, seed=1):
    return np.clip(image(n=n, fwhm=fwhm, etoiles=40, seed=seed, fond=800.0, bruit=10.0), 0, 65535).astype('<u2')


# ================================================================ 1. lecteur tolérant
def test_xisf_a_la_nina(tmp_path):
    a = _ciel()
    p = xisf_tiers(str(tmp_path / 'LIGHT_NGC 7822_0000.xisf'), a, MOTS_NINA)
    with pytest.raises(xisf.ErreurXISF, match='incomplete FITSKeyword'):
        xisf.lire(p, strict=True)                                 # le refus de la 0.1.10
    d, inf = xisf.lire(p)
    assert np.array_equal(d, a) and inf['compression'].startswith('zlib+sh')
    assert ('CD1_1', '-0.000385009286428', '') in inf['mots_cles']
    assert xisf.lire_entete(p)['mots_cles'][4] == ('CD1_1', '-0.000385009286428', '')


def test_xisf_a_l_asiair_sans_metadata(tmp_path):
    a = _ciel(seed=2)
    p = xisf_tiers(str(tmp_path / 'Light_M 101_0002.xisf'), a, MOTS_ASIAIR, metadata=False)
    with pytest.raises(xisf.ErreurXISF, match='Metadata missing'):
        xisf.lire(p, strict=True)
    d, _ = xisf.lire(p)
    assert np.array_equal(d, a)


def test_lecture_tolerante_refuse_encore_l_illisible(tmp_path):
    a = _ciel(seed=3)
    p = xisf_tiers(str(tmp_path / 'x.xisf'), a, MOTS_NINA)
    brut = open(p, 'rb').read()
    (tmp_path / 't.xisf').write_bytes(brut[:-100])                       # tronqué : pixels absents
    with pytest.raises(xisf.ErreurXISF, match='outside the file'):
        xisf.lire(str(tmp_path / 't.xisf'))
    (tmp_path / 's.xisf').write_bytes(b'SIMPLE  = T' + brut[11:])          # FITS déguisé (vu chez l'utilisateur)
    with pytest.raises(xisf.ErreurXISF, match='signature'):
        xisf.lire(str(tmp_path / 's.xisf'))


def test_autres_lecteurs_de_l_application(tmp_path):
    """Ouvrir avec (nature du fichier), Banque OHP (réorganiser : en-tête), métadonnées : mêmes fichiers tiers."""
    from coupole.core import logiciels
    from coupole.modules.ohp import metadonnees, reorganisation
    n = xisf_tiers(str(tmp_path / 'LIGHT_n.xisf'), _ciel(128), MOTS_NINA)
    a = xisf_tiers(str(tmp_path / 'Light_a.xisf'), _ciel(128), MOTS_ASIAIR, metadata=False)
    for p in (n, a):
        assert logiciels.nature(p) == 'xisf_entier'
        assert logiciels.capables('xisf_entier')['pixinsight']
        mots, props = reorganisation.lire_entete_xisf(p)
        assert props['_nx'] == 128 and all(isinstance(c, str) for _, _, c in mots)
        assert reorganisation.analyser(p)['raison'] == 'pas_coupole'          # lu, simplement pas de Coupole
    assert metadonnees.instrument_fichier(n)['pixel_um'] == 3.76


def test_nos_fichiers_restent_controles_strictement(tmp_path):
    p = tmp_path / 'c.xisf'
    xisf.ecrire(p, np.arange(64, dtype='<u2').reshape(8, 8), [('EXPTIME', '1.0', 'x')])
    assert xisf.verifier(p)[0].shape == (8, 8)


def test_image_couleur(tmp_path):
    """Trois canaux (debayérisée) : tableau (3, ny, nx) ; la mesure prend la moyenne."""
    a = np.stack([_ciel(128, seed=s) for s in (1, 2, 3)])
    p = tmp_path / 'rgb.xisf'
    brut = a.tobytes()
    x = ('<?xml version="1.0" encoding="UTF-8"?><xisf version="1.0" xmlns="http://www.pixinsight.com/xisf">'
         '<Image geometry="128:128:3" sampleFormat="UInt16" colorSpace="RGB" location="attachment:4096:%d"/></xisf>'
         % len(brut)).encode()
    e = b'XISF0100' + len(x).to_bytes(4, 'little') + bytes(4) + x
    p.write_bytes(e + bytes(4096 - len(e)) + brut)
    d, inf = xisf.lire(p)
    assert d.shape == (3, 128, 128) and inf['canaux'] == 3 and np.array_equal(d, a)
    plan, _ = M.lire_image(p)
    assert plan.shape == (128, 128) and plan.dtype == np.float32


# ================================================================ 3. exclusion
@pytest.mark.parametrize('chemin, motif', [
    ('2026-10-03 NGC 7822/Nuit_1/Light/LIGHT_NGC 7822_0000.xisf', ''),
    ('2026-10-03 NGC 7822/Nuit_1/Flats/FLAT_2026-10-03_0001.xisf', 'dossier:Flats'),
    ('2026-10-03 NGC 7822/Nuit_1/Darks/x.xisf', 'dossier:Darks'),
    ('N/Bias/x.fits', 'dossier:Bias'), ('N/Offsets/x.fits', 'dossier:Offsets'), ('N/DarkFlats/x.fits', 'dossier:DarkFlats'),
    ('N/Plats/x.fits', 'dossier:Plats'), ('N/Noirs/x.fits', 'dossier:Noirs'), ('FLAT L/x.fits', 'dossier:FLAT L'),
    ('Dark-Bias/master OSC/x.xisf', 'dossier:Dark-Bias'), ('WBPP/calibrated/a_c.xisf', 'dossier:calibrated'),
    ('WBPP/registered/a.xisf', 'dossier:registered'), ('WBPP/cosmetized/a.xisf', 'dossier:cosmetized'),
    ('WBPP/debayered/a.xisf', 'dossier:debayered'), ('S/_platesolve_tmp/a.fits', 'dossier:_platesolve_tmp'),
    ('S/Calibration/a.fits', 'dossier:Calibration'), ('S/master/a.xisf', 'dossier:master'),
    ('Nuit_2_master/LIGHT_Markarian_0039.xisf', ''),                       # (dossier d'un utilisateur : des lights)
    ('L/FLAT_2026_0001.xisf', 'nom'), ('L/DARK_300s.xisf', 'nom'), ('L/BIAS_0001.fits', 'nom'),
    ('L/DARKFLAT_0001.fits', 'nom'), ('L/Flat_Unknown_2026-09-13_0023.xisf', 'nom'),
    ('L/masterDark_BIN-1_300s.xisf', 'nom'), ('L/masterFlat_FILTER-Ha.xisf', 'nom'),
    ('L/masterLight-BINNING_1-FILTER_S.xisf', 'nom'), ('L/superbias533.xisf', 'nom'),
    ('L/LIGHT_0001_c.xisf', 'nom'), ('L/LIGHT_0001_c_cc.xisf', 'nom'), ('L/LIGHT_0001_c_cc_r.xisf', 'nom'),
    ('L/LIGHT_0001_r.xisf', 'nom'), ('L/LIGHT_0001_cc.xisf', 'nom'), ('L/integration_Ha.xisf', 'nom'),
    ('09_Galaxies/M31/champ_1_T120/R/20250716-201500_M31_R_60s.xisf', ''),  # sortie Coupole : filtre R ≠ _r
    ('L/M31_R.xisf', ''), ('L/Dark_Nebula_LDN1622.fits', 'nom'),
])
def test_motifs_dossier_et_nom(chemin, motif):
    assert calibration.motif_chemin('/r/' + chemin, '/r') == motif


@pytest.mark.parametrize('valeur, exclu', [('LIGHT', False), ('Light Frame', False), ('Science', False),
                                           ('object', False), ('', False), ('Flat Field', True), ('FLAT', True),
                                           ('Dark Frame', True), ('Bias Frame', True), ('Offset', True),
                                           ('Master Light', True), ('masterDark', True), ('ZERO', True)])
def test_motif_entete(valeur, exclu):
    assert bool(calibration.motif_entete(valeur)) == exclu


def test_type_image_lu_dans_l_entete_xisf(tmp_path):
    a = _ciel(128)
    p = xisf_tiers(str(tmp_path / 'p.xisf'), a, [('EXPTIME', '1.0')],
                   proprietes=[('Observation:Image:Type', 'Flat')])
    assert M.type_image(M.entete(p)) == 'flat'


def arborescence(racine):
    """Dossier d'acquisition N.I.N.A. + sorties WBPP + ASIAIR, comme ceux d'un utilisateur."""
    nuit = racine / '2026-10-03 NGC 7822' / 'Nuit_1'
    poses = {}
    for sous, noms in {'Light': ['LIGHT_NGC 7822_%04d.xisf' % k for k in range(3)],
                       'Flats': ['FLAT_SII_%04d.xisf' % k for k in range(2)],
                       'Darks': ['DARK_300s_%04d.xisf' % k for k in range(2)],
                       'Bias': ['BIAS_%04d.xisf' % k for k in range(2)]}.items():
        (nuit / sous).mkdir(parents=True)
        for k, n in enumerate(noms):
            poses[nuit / sous / n] = xisf_tiers(str(nuit / sous / n), _ciel(256, seed=10 + k), MOTS_NINA)
    w = racine / 'WBPP'
    for sous, n in (('calibrated', 'LIGHT_0001_c.xisf'), ('registered', 'LIGHT_0001_c_r.xisf'),
                    ('master', 'masterDark_BIN-1_300s.xisf')):
        (w / sous).mkdir(parents=True)
        xisf_tiers(str(w / sous / n), _ciel(160), MOTS_NINA)
    asi = racine / 'ASIAIR'
    asi.mkdir()
    xisf_tiers(str(asi / 'Light_M 101_0002.xisf'), _ciel(160, seed=5), MOTS_ASIAIR, metadata=False)
    xisf_tiers(str(asi / 'Flat_Unknown_0023.xisf'), _ciel(160, seed=6), MOTS_ASIAIR, metadata=False)
    # pose rangée avec les lights mais dont l'en-tête dit « Flat » : exclue à la mesure (niveau 3)
    xisf_tiers(str(nuit / 'Light' / 'pose_inconnue.xisf'), _ciel(160, seed=7),
               [('IMAGETYP', "'Flat Field'"), ('EXPTIME', '1.0')])
    # pose abîmée : jamais silencieuse
    (nuit / 'Light' / 'LIGHT_NGC 7822_abimee.xisf').write_bytes(b'XISF0100' + bytes(8) + b'<pas du xml')
    return racine


def _mesurer(racine, **kw):
    evts = []
    m = moteur.Mesureur(racine, None, None, rapporter=evts.append, ecrire_rapports=False, processus_max=1, **kw)
    return m.lancer(), evts


@sans_sep
def test_poses_de_ciel_seulement(tmp_path):
    racine = arborescence(tmp_path / 'acq')
    b, evts = _mesurer(racine)
    lignes = [l for v in b['lignes'].values() for l in v]
    mesurees = sorted(l['fichier'] for l in lignes if not l.get('erreur') and not l.get('exclu'))
    assert mesurees == ['LIGHT_NGC 7822_0000.xisf', 'LIGHT_NGC 7822_0001.xisf', 'LIGHT_NGC 7822_0002.xisf',
                        'Light_M 101_0002.xisf']
    assert all(l.get('sources') for l in lignes if l['fichier'] in mesurees)      # vraiment mesurées
    assert any(l.get('fwhm_px') for l in lignes if l['fichier'] in mesurees)
    motifs = {os.path.basename(f): m for f, m in b['liste_exclus']}
    assert motifs['FLAT_SII_0000.xisf'] == 'dossier:Flats' and motifs['BIAS_0001.xisf'] == 'dossier:Bias'
    assert motifs['LIGHT_0001_c.xisf'] == 'dossier:calibrated' and motifs['Flat_Unknown_0023.xisf'] == 'nom'
    assert motifs['masterDark_BIN-1_300s.xisf'] == 'dossier:master'
    assert motifs['pose_inconnue.xisf'] == 'entete:flat field'
    assert b['exclus'] == len(b['liste_exclus']) == 11 and b['mesurees_ok'] == 4 and b['echecs'] == 1
    abimee = next(l for l in lignes if l['fichier'] == 'LIGHT_NGC 7822_abimee.xisf')
    assert rapport.etat_ligne(abimee, 'fr').startswith('erreur : format XISF non lu')
    texte = rapport.bilan_texte(b, 'fr')
    assert '4 pose(s) de ciel mesurée(s), 1 en erreur (format XISF non lu' in texte
    assert '11 fichier(s) de calibration exclu(s)' in texte
    inconnue = next(l for l in lignes if l['fichier'] == 'pose_inconnue.xisf')
    assert rapport.etat_ligne(inconnue, 'en') == 'excluded (calibration: header: flat field)'


@sans_sep
def test_avec_calibration_tout_est_mesure(tmp_path):
    racine = arborescence(tmp_path / 'acq')
    b, _ = _mesurer(racine, avec_calibration=True)
    assert b['exclus'] == 0 and b['mesurees_ok'] == 15 and b['echecs'] == 1


@sans_sep
def test_tout_en_erreur_jamais_silencieux(tmp_path, capsys):
    """La situation d'un utilisateur en 0.1.10 : toutes les poses illisibles → résumé, colonne état, code de sortie 1."""
    from coupole.cli import main
    d = tmp_path / 'L'
    d.mkdir()
    for k in range(3):
        (d / ('LIGHT_%d.xisf' % k)).write_bytes(b'XISF0100' + bytes(8) + b'<x')
    assert main(['qualite', str(d)]) == 1
    out = capsys.readouterr().out
    assert '3 image(s) trouvée(s), 0 pose(s) de ciel mesurée(s), 3 en erreur (format XISF non lu' in out or \
        '3 image(s) found, 0 sky frame(s) measured, 3 with an error (XISF format not read' in out


@sans_sep
def test_cli_avec_calibration_et_liste(tmp_path, capsys):
    from coupole.cli import main
    racine = arborescence(tmp_path / 'acq')
    assert main(['qualite', str(racine)]) == 0
    out = capsys.readouterr().out
    assert ('11 fichier(s) de calibration exclu(s)' in out or '11 calibration file(s) excluded' in out)
    assert 'FLAT_SII_0000.xisf' in out
    assert main(['qualite', str(racine), '--avec-calibration']) == 0
    out = capsys.readouterr().out
    assert '0 fichier(s) de calibration exclu(s)' in out or '0 calibration file(s) excluded' in out


@sans_sep
def test_mesure_d_une_pose_nina_synthetique(tmp_path):
    """Pose « à la N.I.N.A. » (zlib+sh, CD sans commentaire) : FWHM retrouvée, échelle tirée de la matrice CD."""
    a = np.clip(image(n=512, fwhm=4.0, etoiles=120, seed=4, fond=800.0, bruit=10.0), 0, 65535).astype('<u2')
    p = xisf_tiers(str(tmp_path / 'LIGHT_x.xisf'), a, MOTS_NINA)
    r = moteur.mesurer_une(p)
    assert 'erreur' not in r and abs(r['fwhm_px'] - 4.0) / 4.0 < 0.05
    assert r['echelle'] == pytest.approx(1.695, abs=0.002) and r['fwhm_arcsec'] == pytest.approx(r['fwhm_px'] * 1.695, rel=1e-3)


def test_memoire_par_image_et_processus(tmp_path):
    p = xisf_tiers(str(tmp_path / 'g.xisf'), np.zeros((64, 64), '<u2'), MOTS_NINA)
    assert moteur.memoire_par_image_mo(p) == 150
    # pose de 61 Mpx : ≈ 1,2 Go par mesure ; 8 Go libres → 3 processus au plus (moitié de la mémoire)
    from coupole.core.parallele import PART_MEMOIRE
    par = int(9576 * 6388 * 18 / 2**20) + 150
    assert moteur.limiter_par_memoire(7, par, dispo_mo=8000) == int(8000 * PART_MEMOIRE // par) == 3
    assert moteur.limiter_par_memoire(7, par, dispo_mo=500) == 1 and moteur.limiter_par_memoire(3, 0) == 3


@sans_sep
def test_interface_case_et_liste_des_exclus(app_qt, tmp_path):
    import time
    from coupole.modules.qualite.gui import Panneau
    racine = arborescence(tmp_path / 'acq')
    p = Panneau()
    p.show()
    try:
        assert not p.avec_calibration.isChecked() and not p.b_exclus.isEnabled()
        p.lancer(str(racine), tout=True)
        fin = time.time() + 120
        while p.bilan is None and time.time() < fin:
            app_qt.processEvents()
            time.sleep(0.02)
        assert p.bilan is not None and p.b_exclus.isEnabled()
        assert 'en erreur' in p.l_progression.text() and 'calibration exclu' in p.l_progression.text()
        col = rapport.COLONNES.index('etat')
        etats = [str(p.modele.data(p.modele.index(r, col))) for r in range(p.modele.rowCount())]
        assert any(e.startswith('erreur : format XISF non lu') for e in etats) and 'mesurée' in etats
        b = p.voir_exclus()
        assert 'FLAT_SII_0000.xisf — dossier « Flats »' in b.detailedText()
        b.close()
    finally:
        p.arreter()
        p.close()
