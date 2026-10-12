"""Nature des produits d'archive et regroupement « un produit logique par filtre ».

Un astrophotographe amateur prend des poses unitaires (lights), puis les empile.  Les archives livrent, pour les
mêmes poses, plusieurs produits déjà empilés.  Pour Hubble (ACS, WFC3), MAST en publie trois familles, toutes
« drizzlées » (calibrées, corrigées de la distorsion, poses combinées, rayons cosmiques rejetés) :

* **pipeline standard** (``ipppssoot_drz`` / ``_drc``) : une association de poses d'une même visite et d'un même
  filtre ; ``drc`` = poses corrigées de l'efficacité de transfert de charge (CTE) avant combinaison (ACS/WFC,
  WFC3/UVIS) — HST Data Handbook (ACS), « Types of ACS files » ;
* **HAP, mosaïque d'une visite (SVM)** (``hst_<prog>_<visite>_<inst>_<det>_<filtre>_<ipppss>_drc``) : les mêmes
  poses, mais tous les filtres de la visite alignés entre eux et sur Gaia, sur la même grille orientée nord en
  haut (MAST, « HAP Single Visit Mosaics Now Available », décembre 2020) ; l'image ``…_total_…`` est la somme de
  tous les filtres, une **image de détection** pour les catalogues, pas un filtre ;
* **HAP, mosaïque multi-visites (MVM)** (``hst_skycell-pPPPPxXXyYY_<inst>_<det>_<filtre>_all_drc``) : *toutes* les
  poses publiques de ce filtre dans une « cellule du ciel » (0,2° de côté, 0,04″ par pixel, grille fixe commune à
  tous les filtres), alignées sur Gaia, rognée au plus petit rectangle qui contient toutes les poses de la cellule
  (tous filtres confondus) — MAST, « Multi-Visit Mosaics from Hubble Now Available », mai 2022 ; DrizzlePac,
  « Multi-visit Mosaic Processing ».  Limites documentées : décalage résiduel de quelques pixels possible entre
  visites, objets mobiles dédoublés, ACS et WFC3 seulement (pas WFPC2).

Choix par défaut (justifié par ces documents) : la **MVM** si elle existe — elle contient toutes les poses du
filtre (temps de pose total le plus long), corrigées de la CTE, et ses filtres partagent la même grille (couleur
directe) ; sinon, par visite, la **SVM** (alignée sur Gaia, filtres sur une grille commune) ; sinon le produit du
pipeline standard.  Les autres produits du même jeu de poses deviennent des *variantes* (cachées par défaut) ;
les images de détection sont écartées par défaut.  JWST : produit ``c…`` (mosaïque de plusieurs observations)
sinon l'observation ``o…`` au temps de pose le plus long.

Aucune requête réseau ici.
"""
from __future__ import annotations

import re

# nature lisible : pose unitaire, produit combiné (plusieurs poses empilées), mosaïque (plusieurs champs ou visites)
NATURES = ('pose', 'combine', 'mosaique', 'detection')

RE_HST_ASSOC = re.compile(r'^[a-z0-9]{6}[0-9a-z]{2}[0-9]$', re.I)        # ipppssoo0 : association (finit par 0)
RE_HST_POSE = re.compile(r'^[a-z0-9]{8}[a-z]$', re.I)                    # ipppssoot (t = q, r…) : une pose


def produit_mast(o: dict) -> tuple[str, str, str]:
    """(produit, nature, visite) d'une observation de MAST.  produit : 'mvm' | 'svm' | 'detection' | 'pipeline' |
    'pose' | 'jwst_mosaique' | 'jwst_obs' | 'galex' | 'autre'."""
    ident = (o.get('obs_id') or '').lower()
    prov = (o.get('provenance') or '').upper()
    filtre = (o.get('filtre') or '').lower()
    if o.get('mission') == 'HST':
        if prov == 'HAP-MVM' or ident.startswith('hst_skycell'):
            return 'mvm', 'mosaique', ''
        if ident.startswith('hst_'):
            visite = ident.rsplit('_', 1)[-1]
            if filtre == 'detection' or '_total_' in ident:
                return 'detection', 'detection', visite
            return 'svm', 'combine', visite
        if RE_HST_POSE.match(ident):
            return 'pose', 'pose', ident[:6]
        return 'pipeline', 'combine', ident[:6]
    if o.get('mission') == 'JWST':
        m = re.match(r'^jw\d{5}-([co])\d+', ident)
        if m and m.group(1) == 'c':
            return 'jwst_mosaique', 'mosaique', ''
        return 'jwst_obs', 'combine', ''
    if o.get('mission') == 'GALEX':
        return 'galex', 'combine', ''
    return 'autre', 'combine' if o.get('final') else 'pose', ''


def nature_generale(o: dict) -> str:
    """Nature des produits des autres archives (d'après leur documentation)."""
    a, m, st = o.get('archive'), o.get('mission'), (o.get('sous_type') or '').lower()
    if a == 'irsa':
        return 'mosaique' if m in ('Spitzer', 'WISE') else 'combine'          # SEIP, Atlas WISE ; Atlas 2MASS : 6 poses
    if a in ('sdss', 'koa', 'opus', 'pds'):
        return 'pose'                                                       # une pose (balayage SDSS de 53,9 s)
    if a == 'noirlab':
        return 'combine' if 'stack' in st or o.get('produit') == 'stacked' else 'pose'
    if a == 'eso':
        return 'mosaique' if 'tile' in st else ('combine' if o.get('final') else 'pose')
    return 'combine' if o.get('final') else 'pose'


def classer(o: dict) -> dict:
    """Complète `produit`, `nature`, `visite` (sans rien écraser de déjà fixé)."""
    if o.get('archive') == 'mast':
        p, n, v = produit_mast(o)
    else:
        p, n, v = o.get('produit') or 'autre', nature_generale(o), ''
    if not o.get('produit'):
        o['produit'] = p
    o['nature'] = o.get('nature') or n
    o['visite'] = o.get('visite') or v
    return o


def _cle_filtre(o: dict) -> tuple:
    return (o.get('archive'), o.get('mission'), (o.get('instrument') or '').upper(), (o.get('filtre') or '').upper())


def _expo(o: dict) -> float:
    return o.get('exposition') or 0.0


def regrouper(observations: list[dict]) -> list[dict]:
    """Marque chaque observation : `groupe` (clé du produit logique), `variante` (False = produit retenu par
    défaut), `raison` (clé de texte : pourquoi retenue ou pourquoi variante).  Rend la même liste."""
    for o in observations:
        classer(o)
        o['variante'] = False
        o['raison'] = ''
        o['groupe'] = '|'.join(str(x) for x in _cle_filtre(o))
    par_filtre: dict[tuple, list] = {}
    for o in observations:
        if o.get('archive') == 'mast' and o.get('mission') in ('HST', 'JWST'):
            par_filtre.setdefault(_cle_filtre(o), []).append(o)
    for cle, liste in par_filtre.items():
        if cle[1] == 'HST':
            _regrouper_hst(liste)
        else:
            _regrouper_jwst(liste)
    return observations


def _meilleur(liste):
    return max(liste, key=lambda o: (_expo(o), o.get('debut') or ''))


def _regrouper_hst(liste):
    for o in liste:
        if o['produit'] == 'detection':
            o['variante'], o['raison'] = True, 'arc_r_detection'
    utiles = [o for o in liste if o['produit'] != 'detection']
    mvm = [o for o in utiles if o['produit'] == 'mvm']
    if mvm:
        choisi = _meilleur(mvm)
        choisi['raison'] = 'arc_r_mvm'
        for o in utiles:
            if o is choisi:
                continue
            o['variante'] = True
            o['raison'] = {'mvm': 'arc_r_autre_cellule', 'svm': 'arc_r_svm_dans_mvm',
                           'pipeline': 'arc_r_pipeline_dans_mvm', 'pose': 'arc_r_pose_dans_mvm'}.get(o['produit'],
                                                                                                 'arc_r_variante')
            o['groupe'] = choisi['groupe']
        return
    par_visite: dict[str, list] = {}
    for o in utiles:
        par_visite.setdefault(o.get('visite') or o.get('obs_id') or o['id'], []).append(o)
    for visite, l in par_visite.items():
        cle = '%s|%s' % (l[0]['groupe'], visite)
        svm = [o for o in l if o['produit'] == 'svm']
        pipe = [o for o in l if o['produit'] == 'pipeline']
        if svm:
            choisi, raison = _meilleur(svm), 'arc_r_svm'
        elif pipe:
            choisi, raison = _meilleur(pipe), 'arc_r_pipeline'
        else:                                    # poses unitaires seulement (objets mobiles) : chacune compte
            for o in l:
                o['raison'], o['groupe'] = 'arc_r_pose_seule', '%s|%s' % (cle, o.get('obs_id'))
            continue
        choisi['raison'] = raison
        for o in l:
            o['groupe'] = cle
            if o is not choisi:
                o['variante'] = True
                o['raison'] = {'pipeline': 'arc_r_pipeline_meme_visite', 'pose': 'arc_r_pose_dans_assoc',
                               'svm': 'arc_r_variante'}.get(o['produit'], 'arc_r_variante')


def _regrouper_jwst(liste):
    mosaiques = [o for o in liste if o['produit'] == 'jwst_mosaique']
    choisi = _meilleur(mosaiques or liste)
    choisi['raison'] = 'arc_r_jwst_mosaique' if mosaiques else 'arc_r_jwst_obs'
    for o in liste:
        o['groupe'] = choisi['groupe']
        if o is not choisi:
            o['variante'], o['raison'] = True, 'arc_r_jwst_autre'


def visibles(observations: list[dict], variantes: bool = False) -> list[dict]:
    """Observations à montrer : les produits retenus, plus les variantes si demandé."""
    return list(observations) if variantes else [o for o in observations if not o.get('variante')]


def resume_exposition(secondes, poses=None) -> str:
    """« 4 × 650 s = 43 min », « 2 000 s », « 9 600 s (2 h 40 min) » — sans dépendre de la langue (unités SI)."""
    if not secondes:
        return ''
    s = float(secondes)
    total = _duree(s)
    if poses and poses > 1:
        return '%d × %s = %s' % (poses, _nombre(s / poses) + ' s', total)
    return total


def _nombre(x: float) -> str:
    return ('%.0f' % x) if x >= 10 else ('%.1f' % x).rstrip('0').rstrip('.')


def _duree(s: float) -> str:
    if s < 120:
        return _nombre(s) + ' s'
    if s < 3600:
        return '%s s (%d min)' % (_milliers(s), round(s / 60))
    h, m = divmod(round(s / 60), 60)
    return '%s s (%d h %02d min)' % (_milliers(s), h, m)


def _milliers(s: float) -> str:
    return '{:,.0f}'.format(s).replace(',', ' ')
