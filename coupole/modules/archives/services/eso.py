"""ESO Science Archive Facility : produits réduits « Phase 3 » (TAP ObsCore ``https://archive.eso.org/tap_obs``).

La table ``ivoa.ObsCore`` de l'ESO ne contient QUE des produits Phase 3 (réduits et validés : images de VISTA,
VST, HAWK-I, FORS, VIMOS, OmegaCAM, MUSE en image blanche…) ; les données brutes sont ailleurs (``dbo.raw``).
Tous les produits images de cette table sont donc des produits finaux (calib_level 2 ou 3).  Recherche par
``INTERSECTS(s_region, CIRCLE)`` (l'empreinte touche le cercle) : 2 à 5 s.  Taille annoncée : ``access_estsize``
en kilo-octets.  Téléchargement anonyme : ``https://dataportal.eso.org/dataPortal/file/<dp_id>`` (ce serveur ne
gère pas les requêtes partielles : la reprise repart du début, voir ``core/reseau.telecharger``).

Conditions : données publiques après la période réservée (``obs_release_date``) ; mention demandée
« Based on data obtained from the ESO Science Archive Facility » et identifiant du programme.
"""
from __future__ import annotations

from .base import Archive, Requete, adql_texte, deja_public, entier, iso_normal, lien, mjd_vers_iso, nombre, observation, tap
from ....core import sources

COLONNES = ('obs_collection', 'instrument_name', 'obs_id', 'dp_id', 'calib_level', 'dataproduct_subtype', 'filter',
            'em_min', 'em_max', 's_ra', 's_dec', 't_min', 'obs_release_date', 'target_name', 'proposal_id',
            'access_estsize', 'obs_title', 'obs_creator_name', 'facility_name')


class Eso(Archive):
    id = 'eso'
    nom = 'ESO Science Archive'
    missions = ('ESO',)
    credit = 'ESO'
    conditions = 'arc_cond_eso'
    etape = 1

    def requete_adql(self, q: Requete) -> str:
        cond = ["dataproduct_type = 'image'"]
        if q.ra is not None and q.dec is not None:
            cond.append("INTERSECTS(s_region, CIRCLE('ICRS', %.7f, %.7f, %.7f)) = 1" % (q.ra, q.dec, q.rayon))
        for i in q.instruments:
            cond.append('instrument_name LIKE %s' % adql_texte('%' + i.upper() + '%'))
            break                                   # un seul filtre côté serveur ; les autres côté client
        if q.date_min:
            cond.append('t_min >= %.5f' % _mjd(q.date_min))
        if q.date_max:
            cond.append('t_min <= %.5f' % (_mjd(q.date_max) + 1))
        return 'SELECT TOP %d %s FROM ivoa.ObsCore WHERE %s' % (q.limite + 1, ','.join(COLONNES), ' AND '.join(cond))

    def chercher(self, q: Requete) -> list[dict]:
        if q.missions and 'ESO' not in q.missions:
            return []
        if q.ra is None:
            return []
        if len(q.instruments) > 1:                 # plusieurs instruments : tout demander, filtrer côté client
            q = Requete(**{**q.__dict__, 'instruments': ()})
        lignes = tap(sources.valeur('archives.eso.tap'), self.requete_adql(q), service='eso')
        return [self.convertir(l) for l in lignes if l.get('dp_id')]

    def convertir(self, l: dict) -> dict:
        dp = l['dp_id'].strip()
        publique = iso_normal(l.get('obs_release_date'))
        kb = nombre(l.get('access_estsize'))
        em_min, em_max = nombre(l.get('em_min')), nombre(l.get('em_max'))
        lam = (em_min + em_max) / 2 * 1e9 if em_min is not None and em_max is not None else None
        calib = entier(l.get('calib_level'))
        programme = l.get('proposal_id', '')
        return observation(
            id='eso:' + dp, archive='eso', mission='ESO', instrument=l.get('instrument_name', ''),
            filtre=l.get('filter', ''), lambda_nm=lam, debut=mjd_vers_iso(l.get('t_min')), publique=publique,
            public=deja_public(publique), calib=calib, final=(calib or 0) >= 2, cible=l.get('target_name', ''),
            ra=nombre(l.get('s_ra')), dec=nombre(l.get('s_dec')), url=lien('archives.eso.fichier', id=dp),
            fichier=dp.replace(':', '_') + '.fits', taille=int(kb * 1000) if kb else None, apercu='',
            page=lien('archives.eso.page', id=dp), programme=programme, pi=l.get('obs_creator_name', ''),
            titre=l.get('obs_title', ''), credit='ESO' + ((' (%s)' % programme) if programme else ''),
            conditions=self.conditions, obs_id=l.get('obs_id', ''), sous_type=l.get('dataproduct_subtype', ''))


def _mjd(date_iso: str) -> float:
    import datetime as D
    d = D.datetime.strptime(date_iso[:10], '%Y-%m-%d')
    return (d - D.datetime(1858, 11, 17)).days
