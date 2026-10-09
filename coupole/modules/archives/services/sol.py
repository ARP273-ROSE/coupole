"""Archives des observatoires au sol (étape 2) : NOIRLab, Keck (KOA), SDSS ; Gemini et Subaru signalés.

* **NOIRLab Astro Data Archive** (Kitt Peak, Cerro Tololo : DECam, Mosaic, 90Prime, NEWFIRM…) : API de
  recherche avancée ``POST /api/adv_search/find/`` (JSON).  Produits finaux = ``proc_type`` « stacked » ou
  « resampled » (piles et images rééchantillonnées du pipeline) ; ``release_date`` donne la fin de la période
  réservée ; ``filesize`` la taille ; téléchargement anonyme ``/api/retrieve/<md5>/`` (fichiers ``.fits.fz``,
  compression par tuiles lue par astropy).
* **Keck Observatory Archive** (KOA, NExScI) : TAP ``https://koa.ipac.caltech.edu/TAP``, une table par instrument
  (``archives.koa.tables``).  KOA n'archive pour l'imagerie que des poses brutes (niveau 0) : aucune n'est un
  produit final ; elles n'apparaissent qu'avec « tous les niveaux ».  Données publiques après ``propint`` mois ;
  téléchargement anonyme ``nph-getKOA?filehand=…`` (sans reprise : le serveur ignore les requêtes partielles).
* **SDSS** (DR17/DR18) : table ``Field`` par le service SQL de SkyServer ; une ligne par champ et par bande
  (u g r i z) ; fichiers ``frame-<bande>-<run>-<camcol>-<field>.fits.bz2`` (images calibrées en nanomaggies, WCS).
* **Gemini Observatory Archive** : l'accès anonyme est refusé (« Login Required ») depuis de nombreuses plages
  d'adresses, à cause des robots ; un compte gratuit (ORCID) est nécessaire → signalé, pas de téléchargement.
* **SMOKA** (Subaru, Kiso, Okayama) : formulaire web seulement, sans interface de programmation publique, et
  surtout des données brutes → signalé, non pris en charge.
"""
from __future__ import annotations

import datetime as D
import math
import urllib.parse

from .base import (Archive, CompteRequis, NonPrisEnCharge, Requete, adql_texte, boite_ra, deja_public, entier,
                   iso_normal, lien, lire_json, lire_tableau, lire_url, maintenant, nombre, noter_lignes, observation,
                   recouvre, tap)
from ....core import sources


# =============================================================================================== NOIRLab
class Noirlab(Archive):
    id = 'noirlab'
    nom = 'NOIRLab Astro Data Archive'
    missions = ('NOIRLab',)
    credit = 'NOIRLab/NSF/AURA (Astro Data Archive)'
    conditions = 'arc_cond_noirlab'
    etape = 2
    CHAMPS = ['md5sum', 'archive_filename', 'instrument', 'telescope', 'proc_type', 'prod_type', 'obs_type',
              'release_date', 'caldat', 'ifilter', 'exposure', 'proposal', 'ra_center', 'dec_center', 'filesize',
              'url', 'dateobs_center']

    def corps(self, q: Requete) -> dict:
        r = q.rayon + 0.15
        ch = [['dec_center', q.dec - r, q.dec + r], ['prod_type', 'image']]
        b = boite_ra(q.ra, q.dec, r)
        if b is not None and len(b) == 1:
            ch.append(['ra_center', b[0][0], b[0][1]])
        ch.append(['proc_type'] + (['stacked', 'resampled'] if q.finaux else ['stacked', 'resampled', 'instcal', 'raw']))
        return {'outfields': self.CHAMPS, 'search': ch}

    def chercher(self, q: Requete) -> list[dict]:
        if q.ra is None or (q.missions and 'NOIRLab' not in q.missions):
            return []
        url = sources.valeur('archives.noirlab.api').rstrip('/') + '/adv_search/find/?limit=%d&rectype=file' % (q.limite + 1)
        rep = lire_json(url, data=self.corps(q), service='noirlab')
        if isinstance(rep, dict) and rep.get('errorMessage'):
            raise ValueError(rep['errorMessage'])
        out = []
        noter_lignes(len(rep) - 1 if isinstance(rep, list) else 0)
        for l in (rep[1:] if isinstance(rep, list) else []):
            o = self.convertir(l)
            if o is not None and recouvre(o, q.ra, q.dec, q.rayon + 0.15):
                out.append(o)
        return out

    def convertir(self, l: dict) -> dict | None:
        url = l.get('url') or ''
        if not url:
            return None
        fichier = (l.get('archive_filename') or '').rsplit('/', 1)[-1] or (l.get('md5sum', '') + '.fits.fz')
        publique = iso_normal(l.get('release_date'))
        filtre = (l.get('ifilter') or '').strip()
        lam = None
        parts = filtre.split()
        for i, p in enumerate(parts[:-1]):           # « r DECam SDSS c0002 6415.0 1480.0 » : centre en Å
            if nombre(p) is not None and nombre(parts[i + 1]) is not None and nombre(p) > 1000:
                lam = nombre(p) / 10
                break
        proc = l.get('proc_type') or ''
        return observation(
            id='noirlab:' + (l.get('md5sum') or fichier), archive='noirlab', mission='NOIRLab',
            instrument='%s/%s' % (l.get('telescope', ''), l.get('instrument', '')), filtre=parts[0] if parts else '',
            lambda_nm=lam, debut=iso_normal(l.get('dateobs_center')), publique=publique, public=deja_public(publique),
            calib=3 if proc in ('stacked', 'resampled') else (2 if proc == 'instcal' else 1),
            final=proc in ('stacked', 'resampled'), cible=l.get('obs_type', ''), ra=nombre(l.get('ra_center')),
            dec=nombre(l.get('dec_center')), url=url, fichier=fichier, taille=entier(l.get('filesize')),
            page=sources.valeur('archives.noirlab.page'), programme=l.get('proposal', '') or '',
            credit=self.credit, conditions=self.conditions, obs_id=l.get('md5sum', ''), sous_type=proc)


# =============================================================================================== KOA
class Koa(Archive):
    id = 'koa'
    nom = 'Keck Observatory Archive'
    missions = ('Keck',)
    credit = 'W. M. Keck Observatory Archive (KOA), NExScI/NASA'
    conditions = 'arc_cond_koa'
    etape = 2
    COLONNES = ('koaid', 'instrume', 'filehand', 'ra', 'dec', 'date_obs', 'utdatetime', 'propint', 'filesize_mb',
                'progid', 'progpi', 'progtitl', 'targname', 'koaimtyp', 'filter')

    def tables(self) -> list[str]:
        return [t.strip() for t in (sources.valeur('archives.koa.tables') or '').split(',') if t.strip()]

    def chercher(self, q: Requete) -> list[dict]:
        if q.ra is None or (q.missions and 'Keck' not in q.missions):
            return []
        if q.finaux:                      # KOA : aucune image finale (poses brutes de niveau 0)
            return []
        out = []
        for t in self.tables():
            cond = ["koaimtyp = 'object'",
                    "CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', %.7f, %.7f, %.7f)) = 1" % (q.ra, q.dec, q.rayon)]
            adql = 'SELECT TOP %d %s FROM %s WHERE %s' % (q.limite + 1, ','.join(self.COLONNES), t, ' AND '.join(cond))
            try:
                lignes = tap(sources.valeur('archives.koa.tap'), adql, service='koa')
            except ValueError:            # colonne absente de cette table : sans filtre
                adql = adql.replace(',filter ', ' ').replace(',filter', '')
                lignes = tap(sources.valeur('archives.koa.tap'), adql, service='koa')
            out += [o for o in (self.convertir(l) for l in lignes) if o is not None]
        return out

    def convertir(self, l: dict) -> dict | None:
        fh = (l.get('filehand') or '').strip()
        if not fh:
            return None
        debut = iso_normal(l.get('utdatetime') or l.get('date_obs'))
        mois = entier(l.get('propint'), 18)
        publique = ''
        if debut:
            d = D.datetime.strptime(debut[:10], '%Y-%m-%d')
            a, m = divmod(d.month - 1 + mois, 12)
            try:
                publique = d.replace(year=d.year + a, month=m + 1).strftime('%Y-%m-%dT00:00:00')
            except ValueError:
                publique = d.replace(year=d.year + a, month=m + 1, day=28).strftime('%Y-%m-%dT00:00:00')
        mb = nombre(l.get('filesize_mb'))
        return observation(
            id='koa:' + (l.get('koaid') or fh.rsplit('/', 1)[-1]), archive='koa', mission='Keck',
            instrument=l.get('instrume', ''), filtre=(l.get('filter') or '').strip(), debut=debut, publique=publique,
            public=deja_public(publique), calib=1, final=False, cible=l.get('targname', ''), ra=nombre(l.get('ra')),
            dec=nombre(l.get('dec')), url=lien('archives.koa.fichier', filehand=fh), fichier=fh.rsplit('/', 1)[-1],
            taille=int(mb * 1e6) if mb else None, page=sources.valeur('archives.koa.page'),
            programme=l.get('progid', ''), pi=l.get('progpi', ''), titre=l.get('progtitl', ''), credit=self.credit,
            conditions=self.conditions, obs_id=l.get('koaid', ''))


# =============================================================================================== SDSS
BANDES_SDSS = {'u': 354.3, 'g': 477.0, 'r': 623.1, 'i': 762.5, 'z': 913.4}


class Sdss(Archive):
    id = 'sdss'
    nom = 'SDSS (SkyServer)'
    missions = ('SDSS',)
    credit = 'Sloan Digital Sky Survey (SDSS)'
    conditions = 'arc_cond_sdss'
    etape = 2

    def chercher(self, q: Requete) -> list[dict]:
        if q.ra is None or (q.missions and 'SDSS' not in q.missions):
            return []
        r = q.rayon + 0.12                       # un champ SDSS fait 13,5′ × 9,8′ : marge d'un demi-champ
        cond = ['dec BETWEEN %.6f AND %.6f' % (q.dec - r, q.dec + r)]
        b = boite_ra(q.ra, q.dec, r)
        if b is not None:
            cond.append('(%s)' % ' OR '.join('ra BETWEEN %.6f AND %.6f' % ab for ab in b))
        c2 = math.cos(math.radians(q.dec)) ** 2
        sql = ('SELECT TOP %d run, rerun, camcol, field, ra, dec, mjd_r FROM Field WHERE %s '
               'ORDER BY (ra - (%.6f)) * (ra - (%.6f)) * %.6f + (dec - (%.6f)) * (dec - (%.6f))') % (
            max(1, q.limite // 5) + 1, ' AND '.join(cond), q.ra, q.ra, c2, q.dec, q.dec)
        url = sources.valeur('archives.sdss.sql') + '?' + urllib.parse.urlencode({'cmd': sql, 'format': 'csv'})
        lignes = lire_tableau(lire_url(url, service='sdss'))
        noter_lignes(len(lignes) * 5)
        out = []
        for l in lignes:
            for bande in 'ugriz':
                o = self.convertir(l, bande)
                if o is not None and recouvre(o, q.ra, q.dec, q.rayon + 0.12):
                    out.append(o)
        return out

    def convertir(self, l: dict, bande: str) -> dict | None:
        run, rerun, camcol, field = (entier(l.get(k)) for k in ('run', 'rerun', 'camcol', 'field'))
        if None in (run, rerun, camcol, field):
            return None
        fichier = 'frame-%s-%06d-%d-%04d.fits.bz2' % (bande, run, camcol, field)
        url = '%s/%d/%d/%d/%s' % (sources.valeur('archives.sdss.frames').rstrip('/'), rerun, run, camcol, fichier)
        ra, dec = nombre(l.get('ra')), nombre(l.get('dec'))
        from .base import mjd_vers_iso
        return observation(
            id='sdss:' + fichier, archive='sdss', mission='SDSS', instrument='SDSS imaging', filtre=bande,
            lambda_nm=BANDES_SDSS[bande], debut=mjd_vers_iso(l.get('mjd_r')), publique='', public=True, calib=2,
            final=True, cible='run %d camcol %d field %d' % (run, camcol, field), ra=ra, dec=dec, url=url,
            fichier=fichier, apercu=lien('archives.sdss.apercu', ra='%.5f' % ra, dec='%.5f' % dec) if ra is not None else '',
            page=lien('archives.sdss.page', ra='%.5f' % ra, dec='%.5f' % dec) if ra is not None else '',
            programme='SDSS', credit=self.credit, conditions=self.conditions, obs_id='%d-%d-%d' % (run, camcol, field))


# =============================================================================================== Gemini, SMOKA
class Gemini(Archive):
    id = 'goa'
    nom = 'Gemini Observatory Archive'
    missions = ('Gemini',)
    credit = 'International Gemini Observatory/NOIRLab/NSF/AURA'
    conditions = 'arc_cond_goa'
    compte = True
    etape = 2

    def chercher(self, q: Requete) -> list[dict]:
        if q.ra is None or (q.missions and 'Gemini' not in q.missions):
            return []
        url = '%s/jsonsummary/canonical/science/NotFail/imaging/ra=%.6f/dec=%.6f/sr=%d' % (
            sources.valeur('archives.goa.api').rstrip('/'), q.ra, q.dec, max(1, int(q.rayon * 3600)))
        brut = lire_url(url, service='goa')
        if b'Login Required' in brut[:400] or brut.lstrip()[:1] not in (b'[', b'{'):
            raise CompteRequis('Gemini Observatory Archive: login required')
        import json
        out = []
        for l in json.loads(brut.decode('utf-8')):
            nom = l.get('name') or l.get('filename') or ''
            if not nom:
                continue
            publique = iso_normal(l.get('release'))
            reduit = 'PROCESSED' in str(l.get('reduction', '')).upper()
            out.append(observation(
                id='goa:' + nom, archive='goa', mission='Gemini', instrument=l.get('instrument', ''),
                filtre=l.get('filter_name', '') or '', debut=iso_normal(l.get('ut_datetime')), publique=publique,
                public=deja_public(publique), calib=3 if reduit else 1, final=reduit, cible=l.get('object', ''),
                ra=nombre(l.get('ra')), dec=nombre(l.get('dec')),
                url=sources.valeur('archives.goa.api').rstrip('/') + '/file/' + nom, fichier=nom,
                taille=entier(l.get('data_size') or l.get('file_size')), programme=l.get('program_id', ''),
                credit=self.credit, conditions=self.conditions, obs_id=l.get('data_label', '')))
        return out


class Smoka(Archive):
    id = 'smoka'
    nom = 'SMOKA (Subaru, Kiso, Okayama)'
    missions = ('Subaru',)
    credit = 'NAOJ (SMOKA)'
    conditions = 'arc_cond_smoka'
    etape = 2

    def chercher(self, q: Requete) -> list[dict]:
        raise NonPrisEnCharge(sources.valeur('archives.smoka.page'))


def _maintenant_iso():
    return maintenant().strftime('%Y-%m-%dT%H:%M:%S')


__all__ = ['Noirlab', 'Koa', 'Sdss', 'Gemini', 'Smoka', 'adql_texte']
