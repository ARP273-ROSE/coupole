"""IRSA (NASA/IPAC Infrared Science Archive) : Spitzer (mosaïques SEIP), WISE (AllWISE Atlas), 2MASS (Atlas).

IRSA a un service TAP (``https://irsa.ipac.caltech.edu/TAP``, table ``ivoa.obscore``) mais ses lignes ne donnent
qu'une adresse DataLink (une requête de plus PAR image pour trouver le fichier).  Son service SIA version 2
(``https://irsa.ipac.caltech.edu/SIA``), qui rend les mêmes colonnes ObsCore, donne directement l'adresse du fichier
(``access_url``), sa taille et le rôle du produit (``dataproduct_subtype`` : science, weight, noise, auxiliary) :
c'est lui qu'on interroge, une requête par collection (``archives.irsa.collections``, modifiable).

Produits finaux : ``spitzer_seip`` (Spitzer Enhanced Imaging Products : mosaïques IRAC 3,6–8 µm et MIPS 24 µm),
``wise_allwise`` (images Atlas, 1,56° de côté, W1–W4), ``twomass_allsky`` (images Atlas J, H, Ks).  Seules les
images de rôle « science » sont gardées.  Toutes ces données sont publiques.
"""
from __future__ import annotations

import urllib.parse

from .base import (Archive, Requete, deja_public, entier, iso_normal, lien, lire_url, lire_tableau, nombre,
                   noter_lignes, observation)
from ....core import sources

MISSIONS = {'spitzer_seip': 'Spitzer', 'wise_allwise': 'WISE', 'twomass_allsky': '2MASS',
            'wise_allsky': 'WISE', 'twomass_full': '2MASS', 'neowiser': 'WISE'}
CREDITS = {'Spitzer': 'NASA/JPL-Caltech (Spitzer, IRSA)', 'WISE': 'NASA/JPL-Caltech/UCLA (WISE, IRSA)',
           '2MASS': '2MASS/UMass/IPAC-Caltech/NASA/NSF (IRSA)'}
# longueurs d'onde centrales (nm) quand la ligne n'en donne pas
BANDES = {'IRAC1': 3550, 'IRAC2': 4493, 'IRAC3': 5731, 'IRAC4': 7872, 'MIPS24': 23680, 'W1': 3368, 'W2': 4618,
          'W3': 12082, 'W4': 22194, 'J': 1235, 'H': 1662, 'K': 2159, 'KS': 2159}


def collections() -> list[str]:
    return [c.strip() for c in (sources.valeur('archives.irsa.collections') or '').split(',') if c.strip()]


class Irsa(Archive):
    id = 'irsa'
    nom = 'IRSA (NASA/IPAC)'
    missions = ('Spitzer', 'WISE', '2MASS')
    credit = 'NASA/IPAC Infrared Science Archive'
    conditions = 'arc_cond_irsa'
    etape = 1

    def url(self, collection: str, q: Requete) -> str:
        p = {'COLLECTION': collection, 'POS': 'CIRCLE %.7f %.7f %.7f' % (q.ra, q.dec, q.rayon),
             'RESPONSEFORMAT': 'csv', 'MAXREC': str(q.limite + 1)}
        return sources.valeur('archives.irsa.sia').rstrip('/') + '?' + urllib.parse.urlencode(p)

    def chercher(self, q: Requete) -> list[dict]:
        if q.ra is None:
            return []
        out = []
        for c in collections():
            m = MISSIONS.get(c, c)
            if q.missions and m not in q.missions:
                continue
            lignes = lire_tableau(lire_url(self.url(c, q), service='irsa'))
            noter_lignes(len(lignes))
            out += [o for o in (self.convertir(l) for l in lignes) if o is not None]
        return out

    def convertir(self, l: dict) -> dict | None:
        url = (l.get('access_url') or '').strip()
        if not url.lower().endswith(('.fits', '.fits.gz')):
            return None
        col = l.get('obs_collection', '')
        mission = MISSIONS.get(col, col)
        sous = (l.get('dataproduct_subtype') or '').strip().lower()
        bande = (l.get('energy_bandpassname') or '').strip()
        a, b = nombre(l.get('em_min')), nombre(l.get('em_max'))
        lam = (a + b) / 2 * 1e9 if a is not None and b is not None else BANDES.get(bande.upper())
        kb = nombre(l.get('access_estsize'))
        publique = iso_normal(l.get('obs_release_date'))
        ra, dec = nombre(l.get('s_ra')), nombre(l.get('s_dec'))
        fichier = url.rsplit('/', 1)[-1]
        return observation(
            id='irsa:%s:%s' % (col, fichier), archive='irsa', mission=mission, instrument=l.get('instrument_name', ''),
            filtre=bande, lambda_nm=lam, debut=_mjd_iso(l.get('t_min')), publique=publique,
            public=deja_public(publique), calib=entier(l.get('calib_level')), final=sous in ('science', ''),
            cible=l.get('target_name', '') or l.get('obs_id', ''), ra=ra, dec=dec, url=url, fichier=fichier,
            taille=int(kb * 1024) if kb else None,
            page=lien('archives.irsa.page', ra='%.5f' % ra, dec='%+.5f' % dec) if ra is not None and dec is not None else '',
            programme=l.get('proposal_id', ''), pi=l.get('proposal_pi', ''),
            titre=l.get('proposal_title', '') or l.get('obs_title', ''), credit=CREDITS.get(mission, self.credit),
            conditions=self.conditions, obs_id=l.get('obs_id', ''), sous_type=sous)


def _mjd_iso(v):
    from .base import mjd_vers_iso
    return mjd_vers_iso(v)
