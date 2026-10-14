"""Construit les données embarquées (bureau et web) des spectres physiques, d'« Orion en 3D », des fiches au survol et
de la couleur vraie des étoiles, à partir des deux jeux de données préparés et vérifiés hors du dépôt :

  * modèle « spectres physiques » (Saha–Boltzmann sur ATLAS9, raies NIST, bandes TiO/CH ; ses propres tests et sa
    vérification SageMath) : donnees/modele_spectres.json, donnees/etalonnage.json, tests/valeurs_reference.json ;
  * « Orion en 3D » (SIMBAD, Gaia DR3, Hipparcos 2007, articles publiés ; vérification SageMath) :
    donnees/orion3d_scene.json, fiches_orion.json, fiches_animations.json, couleurs_reference.json,
    code/couleurs_etoiles.json, images/web/*.webp.

Usage : python3 outils/donnees_etoiles_reelles.py DOSSIER_SPECTRES DOSSIER_ORION

Écrit dans coupole/modules/anim/donnees/ : modele_spectres.json.gz, spectres_atmosphere.json.gz, orion3d.json.gz,
couleurs_etoiles.json.gz, fiches.json.gz, etoiles_reelles.json.gz, orion/*.webp ; et dans tests/ :
spectres_physiques_reference.json.gz, couleurs_reference.json.  Bibliothèque standard seulement."""
from __future__ import annotations

import gzip
import json
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parents[1]
DONNEES = ICI / 'coupole' / 'modules' / 'anim' / 'donnees'

# animations qui dessinent de vraies étoiles : clé du jeu de fiches → identifiant ClassAction
ANIMATIONS = {
    'bigdipper (grande_ourse)': 'bigdipper',
    'dipperclock (horloge_grande_ourse)': 'dipperclock',
    'heliacalrisingsim (lever_heliaque)': 'heliacalrisingsim',
    'celhorcomp (comparaison_reperes)': 'celhorcomp',
    'hrexplorer (diagramme_hr) — groupe proches': 'hrexplorer:proches',
    'hrexplorer (diagramme_hr) — groupe brillantes': 'hrexplorer:brillantes',
    'hrexplorer (diagramme_hr) — groupe communes': 'hrexplorer:communes',
}
# champs des fiches gardés pour l'affichage (le reste : positions, mouvements, géométrie détaillée, reste dans le jeu
# de données d'origine)
GARDES = ('id', 'categorie', 'noms', 'designations', 'type', 'type_spectral', 'V', 'B_V', 'M_V', 'distance', 'teff',
          'rayon_Rsun', 'luminosite_log_Lsun', 'taille_arcmin', 'taille_pc', 'longueur_pc', 'diametre_deg', 'arc_deg',
          'age', 'etoiles_excitatrices')


def ecrire_gz(chemin: Path, donnees) -> None:
    texte = json.dumps(donnees, ensure_ascii=False, separators=(',', ':'))
    chemin.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(chemin, 'wt', encoding='utf-8', compresslevel=9) as f:
        f.write(texte)
    # gzip met la date dans l'en-tête : on la fixe pour des fichiers identiques d'une construction à l'autre
    brut = bytearray(chemin.read_bytes())
    brut[4:8] = b'\0\0\0\0'
    chemin.write_bytes(bytes(brut))
    print('%-60s %8d octets (%d en clair)' % (chemin.relative_to(ICI), chemin.stat().st_size, len(texte.encode())))


def lire(chemin: Path):
    return json.loads(chemin.read_text(encoding='utf-8'))


def compacter(f: dict) -> dict:
    out = {k: f[k] for k in GARDES if f.get(k) not in (None, [], {})}
    if isinstance(out.get('noms'), dict):
        out['noms'] = {k: v for k, v in out['noms'].items() if k in ('fr', 'en', 'source')}
    if isinstance(out.get('type'), dict):
        out['type'] = {k: v for k, v in out['type'].items() if k in ('fr', 'en', 'source')}
    d = out.get('distance')
    if isinstance(d, dict):
        d = {k: v for k, v in d.items() if v not in (None, [], '') and k not in ('plx_mas', 'plx_err_mas')}
        if d.get('alternatives'):
            d['alternatives'] = [a for a in d['alternatives'] if a.get('d') is not None][:5]
            if not d['alternatives']:
                del d['alternatives']
        out['distance'] = d
    c = f.get('couleur_ecran') or {}
    if c.get('hex'):
        out['couleur'] = c['hex']
    return out


def trapeze_gaia(f: dict) -> None:
    """Décision du 14/10/2026 : Trapèze à 388 ± 5 pc (VLBA) par défaut ; Gaia DR3 (402 pc, 4 étoiles combinées,
    vérifié par SageMath) et Menten et al. 2007 (414 pc) dans la fiche comme mesures concurrentes."""
    if not f['id'].startswith('orion:tet01_ori_'):
        return
    d = f.get('distance') or {}
    alt = d.setdefault('alternatives', [])
    if not any(abs((a.get('d') or 0) - 402.0) < 0.5 for a in alt):
        alt.insert(0, {'d': 402.0, 'moins': 4.0, 'plus': 4.0,
                       'ref': 'Gaia DR3, moyenne pondérée des 4 étoiles du Trapèze (θ¹ Ori A–D, point zéro de '
                              'Lindegren et al. 2021 soustrait) : ϖ = 2,4877 ± 0,0247 mas (SageMath)'})


def matrice_icrs_vers_gal() -> list[list[float]]:
    """Matrice de rotation ICRS → galactique, calculée par astropy (repère « Galactic ») : images des trois axes.
    (Contrôle : outils/verif_anim/orion3d_verif.sage la retrouve depuis les coordonnées galactiques des 60 étoiles.)"""
    from astropy.coordinates import ICRS, Galactic, CartesianRepresentation, SkyCoord
    colonnes = []
    for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
        c = SkyCoord(CartesianRepresentation(*v), frame=ICRS()).transform_to(Galactic())
        r = c.cartesian
        colonnes.append([float(r.x), float(r.y), float(r.z)])
    return [[round(colonnes[j][i], 12) for j in range(3)] for i in range(3)]


def main(spectres: Path, orion: Path) -> None:
    # ------------------------------------------------------------ spectres physiques
    ecrire_gz(DONNEES / 'modele_spectres.json.gz', lire(spectres / 'donnees' / 'modele_spectres.json'))
    et = lire(spectres / 'donnees' / 'etalonnage.json')
    atm = {'source': 'etalonnage.json (atmosphere[].drapeaux) du modèle « spectres physiques » : bit 1 = log g hors '
                     'de la grille ATLAS9 (extrapolé), bit 2 = T_eff < 3 500 K (extrapolé)', 'classes': {}}
    for cl, lignes in et['atmosphere'].items():
        atm['classes'][cl] = [(1 if any(x.startswith('log g') for x in e['drapeaux']) else 0)
                              | (2 if any(x.startswith('Teff<') for x in e['drapeaux']) else 0) for e in lignes]
    ecrire_gz(DONNEES / 'spectres_atmosphere.json.gz', atm)
    ecrire_gz(ICI / 'tests' / 'spectres_physiques_reference.json.gz', lire(spectres / 'tests' / 'valeurs_reference.json'))

    # ------------------------------------------------------------ couleur des étoiles
    ecrire_gz(DONNEES / 'couleurs_etoiles.json.gz', lire(orion / 'code' / 'couleurs_etoiles.json'))
    ref = lire(orion / 'donnees' / 'couleurs_reference.json')
    (ICI / 'tests' / 'couleurs_reference.json').write_text(json.dumps(ref, ensure_ascii=False, indent=1) + '\n',
                                                         encoding='utf-8')

    # ------------------------------------------------------------ Orion en 3D
    scene = lire(orion / 'donnees' / 'orion3d_scene.json')
    scene['icrs_vers_gal'] = matrice_icrs_vers_gal()
    ecrire_gz(DONNEES / 'orion3d.json.gz', scene)
    (DONNEES / 'orion').mkdir(exist_ok=True)
    for t in scene['textures']:
        shutil.copyfile(orion / 'images' / 'web' / t['fichier'], DONNEES / 'orion' / t['fichier'])

    # ------------------------------------------------------------ fiches
    fiches: dict[str, dict] = {}
    for f in lire(orion / 'donnees' / 'fiches_orion.json')['fiches']:
        trapeze_gaia(f)
        fiches[f['id']] = compacter(f)
    par_anim: dict[str, dict[str, str]] = {}
    reelles: dict[str, dict[str, list]] = {}
    fa = lire(orion / 'donnees' / 'fiches_animations.json')['animations']
    for cle_jeu, anim in ANIMATIONS.items():
        for e in fa[cle_jeu]:
            f = e.get('fiche')
            if not f:
                continue
            fid = f['id']
            if fid not in fiches:
                fiches[fid] = compacter(f)
            par_anim.setdefault(anim, {})[e['cle']] = fid
            teff = (f.get('teff') or {}).get('valeur')
            couleur = (f.get('couleur_ecran') or {}).get('hex')
            d = f.get('distance') or {}
            reelles.setdefault(anim, {})[e['cle']] = [fid, teff, couleur, d.get('al'), d.get('al_moins'),
                                                      d.get('al_plus')]
    ecrire_gz(DONNEES / 'fiches.json.gz', {
        'source': 'Fiches au survol : SIMBAD (CDS), Gaia DR3 (ESA/DPAC), Hipparcos 2007 (van Leeuwen), articles cités '
                  'dans chaque champ « source » ; requêtes du 14/10/2026.',
        'fiches': fiches, 'animations': par_anim})
    ecrire_gz(DONNEES / 'etoiles_reelles.json.gz', {
        'colonnes': ['fiche', 'teff_K', 'couleur', 'distance_al', 'al_moins', 'al_plus'], 'animations': reelles})


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
