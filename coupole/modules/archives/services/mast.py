"""MAST (Mikulski Archive for Space Telescopes, STScI) : Hubble, JWST, GALEX.

(TESS, Kepler et Pan-STARRS ne sont pas proposés : TESS ne livre que des cubes de pleine image de 2 Go sans
intérêt pour une image, Kepler aucune image de champ, et Pan-STARRS n'est pas dans cette vue de MAST — il a son
propre service de découpes.  Spitzer est servi par IRSA, en mosaïques finales.)

Interrogation : service TAP officiel de MAST (``https://mast.stsci.edu/vo-tap/api/v0.1/caom``), vue
``dbo.obspointing`` — la table ObsCore de ce service (``ivoa.obscore``) n'a ni filtre, ni date de publication, ni
investigateur, ni adresse du produit ; ``dbo.obspointing`` a tout cela (``filters``, ``t_obs_release``,
``datarights``, ``proposal_pi``, ``obs_title``, ``dataurl``, ``jpegurl``).  Mesuré le 9 octobre 2026 : une
recherche par cône (``CONTAINS(POINT, CIRCLE)``) dépasse le délai de la passerelle (504 au bout de 60 s) ; une
boîte en ascension droite et déclinaison sur ``s_ra``/``s_dec`` répond en moins de 2 s.  On interroge donc une
boîte qui contient le cercle (agrandie d'une marge pour les grandes mosaïques), puis on garde les observations
dont le centre est dans le cercle ou dont l'empreinte (``s_region``) contient la cible.

Produits finaux (calib_level 3) : JWST ``*_i2d.fits`` (image rééchantillonnée et combinée, étape 3 du pipeline),
HST ``*_drz.fits`` / ``*_drc.fits`` (images « drizzlées », ``drc`` = corrigée de l'efficacité de transfert de
charge), GALEX ``*-int.fits.gz`` (image d'intensité).  Téléchargement : ``Download/file?uri=mast:…``.
"""
from __future__ import annotations

import math

from .base import (Archive, Requete, adql_texte, boite_ra, deja_public, entier, lien, mjd_vers_iso, nombre,
                   observation, recouvre, tap)
from ....core import sources

COLLECTIONS = ('JWST', 'HST', 'GALEX')
PAR_DEFAUT = COLLECTIONS
MARGE = 0.15                  # degrés ajoutés à la boîte : une mosaïque dont le centre est loin peut couvrir la cible
CREDITS = {'JWST': 'NASA/ESA/CSA, STScI', 'HST': 'NASA/ESA, STScI', 'HLA': 'NASA/ESA, STScI (Hubble Legacy Archive)',
           'GALEX': 'NASA/GALEX, STScI', 'SPITZER_SHA': 'NASA/JPL-Caltech'}
SUFFIXES_FINAUX = ('_i2d.fits', '_drz.fits', '_drc.fits', '-int.fits.gz')
COLONNES = ('obs_collection', 'instrument_name', 'obs_id', 'obsid', 'calib_level', 'dataproduct_type', 'filters',
            's_ra', 's_dec', 't_min', 't_obs_release', 'target_name', 'proposal_id', 'proposal_pi', 'obs_title',
            'jpegurl', 'dataurl', 'datarights', 'em_min', 'em_max', 's_region')


def final(collection: str, fichier: str, calib) -> bool:
    f = fichier.lower()
    if collection == 'JWST':
        return calib == 3 and f.endswith('_i2d.fits')
    if collection in ('HST', 'HLA'):
        return (calib or 0) >= 3 and f.endswith(('_drz.fits', '_drc.fits'))
    if collection == 'GALEX':
        return f.endswith('-int.fits.gz')
    if collection == 'SPITZER_SHA':
        return f.endswith(('maic.fits', 'mosaic.fits'))
    return calib == 3


def lambda_nm(em_min, em_max):
    """Centre de la bande en nm.  `obspointing` donne em_min/em_max en nm (le champ annonce « m » : valeurs
    vérifiées sur F770W = 6 600–8 800, F435W ≈ 360–490)."""
    a, b = nombre(em_min), nombre(em_max)
    if a is None or b is None:
        return None
    c = (a + b) / 2
    if c < 1e-3:                               # en mètres, au cas où le service se corrigerait
        c *= 1e9
    return c


class Mast(Archive):
    id = 'mast'
    nom = 'MAST (STScI)'
    missions = COLLECTIONS
    credit = 'NASA, STScI (MAST)'
    conditions = 'arc_cond_mast'
    etape = 1

    def requete_adql(self, q: Requete, collections) -> str:
        cond = ['obs_collection IN (%s)' % ','.join(adql_texte(c) for c in collections),
                "dataproduct_type = 'image'"]
        if q.finaux:                      # produits finaux : filtrés AVANT la limite de lignes, côté serveur
            cond.append('calib_level >= 2')
            cond.append('(%s)' % ' OR '.join("dataurl LIKE '%%%s'" % s for s in SUFFIXES_FINAUX))
        if q.ra is not None and q.dec is not None:
            r = q.rayon + MARGE
            cond.append('s_dec BETWEEN %.6f AND %.6f' % (q.dec - r, q.dec + r))
            b = boite_ra(q.ra, q.dec, r)
            if b is not None:
                cond.append('(%s)' % ' OR '.join('s_ra BETWEEN %.6f AND %.6f' % ab for ab in b))
        if q.date_min:
            cond.append('t_min >= %.5f' % _mjd(q.date_min))
        if q.date_max:
            cond.append('t_min <= %.5f' % (_mjd(q.date_max) + 1))
        ordre = ''
        if q.ra is not None and q.dec is not None:      # les plus proches d'abord : la limite garde les bonnes lignes
            c2 = math.cos(math.radians(q.dec)) ** 2
            ordre = ' ORDER BY (s_ra - (%.6f)) * (s_ra - (%.6f)) * %.6f + (s_dec - (%.6f)) * (s_dec - (%.6f))' % (
                q.ra, q.ra, c2, q.dec, q.dec)
        return 'SELECT TOP %d %s FROM dbo.obspointing WHERE %s%s' % (q.limite + 1, ','.join(COLONNES),
                                                                     ' AND '.join(cond), ordre)

    def chercher(self, q: Requete) -> list[dict]:
        collections = [c for c in q.missions if c in COLLECTIONS] if q.missions else list(PAR_DEFAUT)
        if not collections:
            return []
        lignes = tap(sources.valeur('archives.mast.tap'), self.requete_adql(q, collections), service='mast')
        out = []
        for l in lignes:
            if l.get('obs_collection') not in collections:
                continue
            o = self.convertir(l)
            if o is None:
                continue
            region = o.pop('_region', '')
            if q.ra is None or recouvre(o, q.ra, q.dec, q.rayon, region):
                out.append(o)
        return out

    def convertir(self, l: dict) -> dict | None:
        url = (l.get('dataurl') or '').strip()
        if not url or 'fitscut' in url:
            return None
        col = l.get('obs_collection', '')
        calib = entier(l.get('calib_level'))
        if url.startswith('mast:'):
            fichier = url.rsplit('/', 1)[-1]
            adresse = lien('archives.mast.fichier', uri=url)
        else:
            fichier = url.rsplit('/', 1)[-1].rsplit('=', 1)[-1]
            adresse = url.replace('&amp;', '&')
        if not fichier.lower().endswith(('.fits', '.fits.gz', '.fit')):
            return None
        apercu = (l.get('jpegurl') or '').strip()
        if apercu.startswith('mast:'):
            apercu = lien('archives.mast.fichier', uri=apercu)
        publique = mjd_vers_iso(l.get('t_obs_release'))
        mission = col
        return observation(
            id='mast:' + (l.get('obs_id') or fichier), archive='mast', mission=mission, instrument=l.get('instrument_name', ''),
            filtre=l.get('filters', ''), lambda_nm=lambda_nm(l.get('em_min'), l.get('em_max')),
            debut=mjd_vers_iso(l.get('t_min')), publique=publique,
            public=deja_public(publique, (l.get('datarights') or '').strip()), calib=calib,
            final=final(col, fichier, calib), cible=l.get('target_name', ''), ra=nombre(l.get('s_ra')),
            dec=nombre(l.get('s_dec')), url=adresse, fichier=fichier, apercu=apercu,
            page=lien('archives.mast.page', obs_id=l.get('obs_id', '')), programme=l.get('proposal_id', ''),
            pi=l.get('proposal_pi', ''), titre=l.get('obs_title', ''), credit=CREDITS.get(col, self.credit),
            conditions=self.conditions, obs_id=l.get('obs_id', ''), _region=l.get('s_region', ''))


def _mjd(date_iso: str) -> float:
    import datetime as D
    d = D.datetime.strptime(date_iso[:10], '%Y-%m-%d')
    return (d - D.datetime(1858, 11, 17)).days
