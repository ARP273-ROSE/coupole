"""Sondes planétaires (étape 3) : Voyager ISS et Cassini ISS par OPUS (PDS Ring-Moon Systems Node), JunoCam par
l'Atlas du PDS Imaging Node.

* **OPUS** (``https://opus.pds-rings.seti.org/api``) : ``data.json`` cherche par instrument, corps visé, dates et
  filtre et rend, pour chaque observation, le chemin du produit principal (``primaryfilespec``) ; les adresses des
  produits dérivés sont résolues au moment du téléchargement par ``files/<opusid>.json`` (une requête par fichier
  téléchargé, jamais par ligne affichée).  Produit retenu : Voyager ``*_GEOMED.IMG`` (calibré et corrigé de la
  distorsion du vidicon, grille 1000 × 1000) ; Cassini ``*_CALIB.IMG`` (calibré par CISSCAL, distorsion non
  corrigée).  Vignette : ``holdings/previews/…_thumb.jpg``.
* **PDS Imaging Atlas** (``https://pds-imaging.jpl.nasa.gov/solr/pds_archives/search``, Solr) : JunoCam
  (``ATLAS_INSTRUMENT_NAME:jnc``) ; produits RDR (niveau 3, calibrés) et EDR (bruts).  Une image JunoCam est un
  empilement de *framelets* (bandes de 128 lignes, 4 filtres) : Coupole convertit le fichier tel quel ; la
  reconstruction de l'image (projection selon la géométrie SPICE) n'est pas faite (voir ``docs/archives_methode.md``).

Formats : PDS3 (label détaché ``.LBL`` ou attaché), VICAR, PDS4 → ``pds.py``.
Crédits : NASA/JPL-Caltech ; Cassini : NASA/JPL-Caltech/Space Science Institute ; Juno : NASA/JPL-Caltech/SwRI/MSSS.
"""
from __future__ import annotations

import json
import urllib.parse

from .base import Archive, Requete, iso_normal, lien, lire_json, nombre, noter_lignes, observation
from ....core import sources

INSTRUMENTS = {'Voyager': 'Voyager ISS', 'Cassini': 'Cassini ISS'}
FILTRE_COL = {'Voyager': 'VGISSfilter', 'Cassini': 'COISSfilter'}
CREDITS = {'Voyager': 'NASA/JPL-Caltech (PDS Ring-Moon Systems Node)',
           'Cassini': 'NASA/JPL-Caltech/Space Science Institute (PDS Ring-Moon Systems Node)',
           'Juno': 'NASA/JPL-Caltech/SwRI/MSSS (PDS Imaging Node)'}
# corps en français → nom anglais attendu par les archives
CORPS = {'mercure': 'Mercury', 'venus': 'Venus', 'vénus': 'Venus', 'terre': 'Earth', 'lune': 'Moon', 'mars': 'Mars',
         'jupiter': 'Jupiter', 'saturne': 'Saturn', 'uranus': 'Uranus', 'neptune': 'Neptune', 'pluton': 'Pluto',
         'io': 'Io', 'europe': 'Europa', 'ganymède': 'Ganymede', 'ganymede': 'Ganymede', 'callisto': 'Callisto',
         'titan': 'Titan', 'encelade': 'Enceladus', 'mimas': 'Mimas', 'téthys': 'Tethys', 'tethys': 'Tethys',
         'dioné': 'Dione', 'dione': 'Dione', 'rhéa': 'Rhea', 'rhea': 'Rhea', 'japet': 'Iapetus', 'hypérion': 'Hyperion',
         'phœbé': 'Phoebe', 'phoebe': 'Phoebe', 'miranda': 'Miranda', 'ariel': 'Ariel', 'umbriel': 'Umbriel',
         'titania': 'Titania', 'obéron': 'Oberon', 'oberon': 'Oberon', 'triton': 'Triton', 'anneaux': 'Rings'}
# longueur d'onde centrale approximative (nm) des filtres courants (documentation des instruments)
LAMBDA = {'VIOLET': 416, 'BLUE': 479, 'GREEN': 566, 'ORANGE': 591, 'UV': 346, 'CLEAR': 497, 'CH4_U': 541,
          'CH4_JS': 619, 'SODIUM': 589, 'RED': 649, 'BL1': 451, 'GRN': 568, 'RED,': 650, 'IR1': 752, 'IR2': 862,
          'IR3': 928, 'IR4': 1002, 'UV1': 258, 'UV2': 298, 'UV3': 338, 'MT1': 619, 'MT2': 727, 'MT3': 889,
          'CB1': 619, 'CB2': 750, 'CB3': 938, 'HAL': 656, 'METHANE': 889}


def corps(nom: str) -> str:
    n = (nom or '').strip()
    return CORPS.get(n.lower(), n[:1].upper() + n[1:] if n else '')


def lambda_filtre(filtre: str):
    f = (filtre or '').upper()
    for morceau in f.replace('+', ',').split(','):
        m = morceau.strip()
        if m in LAMBDA and m not in ('CL1', 'CL2', 'CLEAR'):
            return LAMBDA[m]
    return LAMBDA.get(f.split(',')[0].strip()) if f else None


class Opus(Archive):
    id = 'opus'
    nom = 'OPUS (PDS Ring-Moon Systems Node)'
    missions = ('Voyager', 'Cassini')
    credit = 'NASA/JPL-Caltech (PDS)'
    conditions = 'arc_cond_pds'
    celeste = False
    etape = 3

    def url(self, mission: str, q: Requete) -> str:
        p = {'instrument': INSTRUMENTS[mission], 'limit': str(q.limite + 1),
             'cols': 'opusid,instrument,planet,target,time1,%s,primaryfilespec,observationduration' % FILTRE_COL[mission]}
        if q.cible:
            p['target'] = corps(q.cible)
        if q.date_min:
            p['time1'] = q.date_min[:10]
        if q.date_max:
            p['time2'] = q.date_max[:10] + 'T23:59:59'
        if len(q.filtres) == 1:
            p[FILTRE_COL[mission]] = q.filtres[0].upper()
        return sources.valeur('archives.opus.api').rstrip('/') + '/data.json?' + urllib.parse.urlencode(p)

    def chercher(self, q: Requete) -> list[dict]:
        if not q.cible:
            return []
        out = []
        for m in INSTRUMENTS:
            if q.missions and m not in q.missions:
                continue
            rep = lire_json(self.url(m, q), service='opus')
            noter_lignes(len(rep.get('page', [])))
            for ligne in rep.get('page', []):
                o = self.convertir(m, ligne)
                if o is not None:
                    out.append(o)
        return out

    def convertir(self, mission: str, l: list) -> dict | None:
        if len(l) < 7:
            return None
        opusid, instrument, planete, cible, debut, filtre, spec = l[:7]
        if not spec:
            return None
        volume = spec.split('/', 1)[0]
        serie = volume[:7] + 'xxx'
        base = spec.rsplit('.', 1)[0]
        racine = sources.valeur('archives.opus.api').rsplit('/api', 1)[0] + '/holdings'
        if mission == 'Voyager':
            base = base.rsplit('_', 1)[0]                         # C1462321_RAW → C1462321
            url = '%s/volumes/%s/%s_GEOMED.IMG' % (racine, serie, base)
            etiquette = url[:-4] + '.LBL'
            apercu = '%s/previews/%s/%s_thumb.jpg' % (racine, serie, base)
        else:
            url = '%s/calibrated/%s/%s_CALIB.IMG' % (racine, serie, base)
            etiquette = url[:-4] + '.LBL'
            apercu = '%s/previews/%s/%s_thumb.jpg' % (racine, serie, base)
        fichier = url.rsplit('/', 1)[-1]
        return observation(
            id='opus:' + opusid, archive='opus', mission=mission, instrument=instrument, filtre=filtre or '',
            lambda_nm=lambda_filtre(filtre), debut=iso_normal(debut), publique='', public=True, calib=3, final=True,
            cible=cible or planete, url=url, fichier=fichier, format='pds3', etiquette=etiquette, apercu=apercu,
            page=lien('archives.opus.page', id=opusid), programme=volume, credit=CREDITS[mission],
            conditions=self.conditions, obs_id=opusid)

    def adresse_fichier(self, o: dict) -> str:
        """Adresse exacte par ``files/<opusid>.json`` (le chemin déduit sert de repli)."""
        try:
            rep = lire_json(sources.valeur('archives.opus.api').rstrip('/') + '/files/%s.json' % o['obs_id'],
                            service='opus')
            produits = next(iter(rep.get('data', {}).values()), {})
            cle = 'vgiss_geomed' if o['mission'] == 'Voyager' else 'coiss_calib'
            for u in produits.get(cle, []):
                if u.upper().endswith('.IMG'):
                    lbl = [x for x in produits.get(cle, []) if x.upper().endswith('.LBL')]
                    if lbl:
                        o['etiquette'] = lbl[0]
                    return u
        except Exception:
            pass
        return o['url']


class PdsAtlas(Archive):
    id = 'pds'
    nom = 'PDS Imaging Node (Atlas)'
    missions = ('Juno',)
    credit = CREDITS['Juno']
    conditions = 'arc_cond_pds'
    celeste = False
    etape = 3
    CHAMPS = ('identifier', 'ATLAS_DATA_URL', 'ATLAS_LABEL_URL', 'ATLAS_THUMBNAIL_URL', 'START_TIME', 'TARGET_NAME',
              'FILTER_NAME', 'ATLAS_PRODUCT_TYPE', 'PROCESSING_LEVEL_ID', 'MISSION_PHASE_NAME', 'LINES', 'LINE_SAMPLES',
              'SAMPLE_BITS', 'PRODUCT_ID', 'DATA_SET_ID')

    def url(self, q: Requete) -> str:
        fq = ['ATLAS_MISSION_NAME:juno', 'ATLAS_INSTRUMENT_NAME:jnc']
        if q.cible:
            fq.append('TARGET_NAME:"%s"' % corps(q.cible).upper().replace('"', ''))
        if q.finaux:
            fq.append('ATLAS_PRODUCT_TYPE:rdr')
        if q.date_min or q.date_max:
            fq.append('START_TIME:[%s TO %s]' % ((q.date_min[:10] + 'T00:00:00Z') if q.date_min else '*',
                                                 (q.date_max[:10] + 'T23:59:59Z') if q.date_max else '*'))
        p = [('q', '*:*'), ('rows', str(q.limite + 1)), ('wt', 'json'), ('fl', ','.join(self.CHAMPS))] + \
            [('fq', f) for f in fq]
        return sources.valeur('archives.pds.atlas') + '?' + urllib.parse.urlencode(p)

    def chercher(self, q: Requete) -> list[dict]:
        if not q.cible or (q.missions and 'Juno' not in q.missions):
            return []
        rep = lire_json(self.url(q), service='pds')
        noter_lignes(len(rep.get('response', {}).get('docs', [])))
        return [o for o in (self.convertir(d) for d in rep.get('response', {}).get('docs', [])) if o is not None]

    def convertir(self, d: dict) -> dict | None:
        url = d.get('ATLAS_DATA_URL') or ''
        if not url:
            return None
        ident = d.get('identifier')
        ident = ident[0] if isinstance(ident, list) and ident else (ident or d.get('PRODUCT_ID') or url.rsplit('/', 1)[-1])
        filtres = d.get('FILTER_NAME') or []
        filtres = filtres if isinstance(filtres, list) else [filtres]
        rdr = (d.get('ATLAS_PRODUCT_TYPE') or '').lower() == 'rdr'
        lignes, colonnes, bits = nombre(d.get('LINES')), nombre(d.get('LINE_SAMPLES')), nombre(d.get('SAMPLE_BITS'))
        taille = int(lignes * colonnes * bits / 8) if lignes and colonnes and bits else None
        cible = d.get('TARGET_NAME') or ''
        return observation(
            id='pds:' + ident, archive='pds', mission='Juno', instrument='JunoCam', filtre=';'.join(filtres),
            lambda_nm=None, debut=iso_normal(d.get('START_TIME')), publique='', public=True,
            calib=3 if rdr else 1, final=rdr, cible=cible.title() if isinstance(cible, str) else '', url=url,
            fichier=url.rsplit('/', 1)[-1], format='pds3', etiquette=d.get('ATLAS_LABEL_URL') or '',
            taille=taille, apercu=d.get('ATLAS_THUMBNAIL_URL') or '', page=lien('archives.pds.page', id=ident),
            programme=d.get('MISSION_PHASE_NAME') or '', titre=d.get('DATA_SET_ID') or '', credit=self.credit,
            conditions=self.conditions, obs_id=ident)


__all__ = ['Opus', 'PdsAtlas', 'corps', 'json']
