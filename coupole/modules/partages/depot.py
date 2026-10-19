"""Déposer SA mesure dans un partage : ses fichiers, et SA ligne dans le tableau des mesures, sans rien écraser.

Règles (toutes vérifiées par les essais) :
* rien ne part sans une action explicite et une confirmation qui liste EXACTEMENT ce qui sera envoyé (``Plan``) ;
* chaque fichier est déposé sous un nom libre (« nom_2.fits » si « nom.fits » existe déjà) et avec la condition
  « If-None-Match: * » : si quelqu'un dépose le même nom entre-temps, le serveur refuse et l'on prend le nom suivant ;
* la ligne du tableau : on relit le tableau JUSTE AVANT (avec son ETag), on garde une copie locale de cette version,
  on ajoute la ligne dans la première ligne libre (aucune cellule remplie n'est jamais remplacée), et l'on dépose
  avec « If-Match: <ETag> » : si quelqu'un a modifié le tableau entre-temps, le serveur refuse ; on relit et l'on
  recommence (3 fois) ; en dernier recours, la ligne est déposée à côté dans un petit fichier
  « ligne_<nom>_<date>.csv » (même colonnes) que l'enseignant pourra recopier ;
* aucune suppression, aucun renommage, aucun déplacement : le client WebDAV n'en a pas les moyens.
"""
from __future__ import annotations

import csv
import datetime as D
import io
import os
import re
import time
from dataclasses import dataclass, field

from . import tableur
from .mesures import Tableau
from .structure import normaliser
from .webdav import Conflit, ErreurPartage

UTC = D.timezone.utc
ESSAIS_TABLEAU = 3


@dataclass
class FichierADeposer:
    local: str
    distant: str              # chemin complet dans le partage (nom libre au moment du plan)
    taille: int


@dataclass
class Plan:
    dossier: str
    fichiers: list = field(default_factory=list)
    tableau: str = ''                     # chemin du tableau ('' : pas de ligne)
    feuille: str = ''
    colonnes: list = field(default_factory=list)      # [(titre de colonne, valeur affichée)]
    valeurs: list = field(default_factory=list)       # valeurs par colonne (index 0 = colonne A)
    csv_secours: str = ''                 # chemin du .csv de secours (si le tableau ne peut pas recevoir la ligne)

    def octets(self) -> int:
        return sum(f.taille for f in self.fichiers)


def nom_libre(nom: str, existants: set) -> str:
    """« photo.fits » → « photo_2.fits », « photo_3.fits »… s'il existe déjà (comparaison sans casse)."""
    bas = {normaliser(x) for x in existants}
    if normaliser(nom) not in bas:
        return nom
    racine, ext = os.path.splitext(nom)
    if racine.lower().endswith('.fits') or racine.lower().endswith('.fit'):
        racine, ext2 = os.path.splitext(racine)
        ext = ext2 + ext
    k = 2
    while normaliser('%s_%d%s' % (racine, k, ext)) in bas:
        k += 1
    return '%s_%d%s' % (racine, k, ext)


def nom_sur(t: str) -> str:
    t = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', '_', t).strip(' .')
    return t[:120] or 'fichier'


def format_date_comme(tableau: Tableau, exemple: str = '') -> str:
    """Format de date le plus fréquent dans le tableau (« JJ/MM/AAAA HH:MM:SS TU » par défaut)."""
    iso = sum(1 for m in tableau.mesures if re.search(r'\d{4}-\d{2}-\d{2}', m.brut.get('date', '')))
    barres = sum(1 for m in tableau.mesures if re.search(r'\d{1,2}/\d{1,2}/\d{4}', m.brut.get('date', '')))
    return '%Y-%m-%d %H:%M:%S UTC' if iso > barres else '%d/%m/%Y %H:%M:%S TU'


def valeurs_ligne(tableau: Tableau, mesure: dict) -> list:
    """Valeurs de la ligne dans l'ordre des colonnes du tableau, d'après `mesure` (rôle → valeur) ; colonnes
    inconnues laissées vides, numéro laissé tel quel (None)."""
    n = max(list(tableau.titres) + list(tableau.colonnes.values()) + [0])
    vals: list = [''] * n
    fmt = format_date_comme(tableau)
    for role, col in tableau.colonnes.items():
        if role == 'numero':
            vals[col - 1] = None
            continue
        v = mesure.get(role)
        if isinstance(v, D.datetime):
            v = v.astimezone(UTC).strftime(fmt)
        vals[col - 1] = '' if v is None else v
    return vals


def preparer(session, dossier: str, fichiers_locaux: list, tableau_chemin: str = '', tableau: Tableau | None = None,
             mesure: dict | None = None, auteur: str = '') -> Plan:
    """Plan exact du dépôt (noms libres d'après la liste actuelle du partage)."""
    existants = {e.chemin for e in session.client.propfind(dossier, 1)} if dossier is not None else set()
    noms = {c.rsplit('/', 1)[-1] for c in existants}
    plan = Plan(dossier.strip('/'))
    for local in fichiers_locaux:
        nom = nom_libre(nom_sur(os.path.basename(local)), noms)
        noms.add(nom)
        plan.fichiers.append(FichierADeposer(local, (plan.dossier + '/' if plan.dossier else '') + nom,
                                             os.path.getsize(local)))
    if tableau_chemin and tableau is not None and mesure:
        plan.tableau = tableau_chemin
        plan.feuille = tableau.feuille
        if 'fichier' in tableau.colonnes and not mesure.get('fichier') and plan.fichiers:
            mesure = dict(mesure, fichier=plan.fichiers[0].distant.rsplit('/', 1)[-1])
        plan.valeurs = valeurs_ligne(tableau, mesure)
        plan.colonnes = [(tableau.titres.get(k + 1, tableur.colonne_lettres(k + 1)), '' if v is None else str(v))
                         for k, v in enumerate(plan.valeurs)]
        base = tableau_chemin.rsplit('/', 1)[0] if '/' in tableau_chemin else ''
        quand = D.datetime.now(UTC).strftime('%Y%m%d-%H%M%S')
        nom_csv = nom_libre('ligne_%s_%s.csv' % (nom_sur(auteur or 'mesure').replace(' ', '_'), quand),
                            {c.rsplit('/', 1)[-1] for c in existants})
        plan.csv_secours = (base + '/' if base else '') + nom_csv
    return plan


def contenu_csv(plan: Plan) -> bytes:
    s = io.StringIO()
    w = csv.writer(s, delimiter=';')
    w.writerow([t for t, _ in plan.colonnes])
    w.writerow([v for _, v in plan.colonnes])
    return s.getvalue().encode('utf-8-sig')


def executer(session, plan: Plan, sauvegardes: str, progression=None, journal=None) -> dict:
    """Dépose ce que dit le plan.  Rend {'fichiers': [chemins déposés], 'tableau': 'ligne'|'csv'|'', 'ligne': n,
    'sauvegarde': chemin de la copie locale du tableau, 'csv': chemin du csv de secours}."""
    journal = journal or (lambda *a, **k: None)
    res = {'fichiers': [], 'tableau': '', 'ligne': 0, 'sauvegarde': '', 'csv': '', 'renommes': []}
    for f in plan.fichiers:
        cible = f.distant
        for essai in range(5):
            try:
                session.client.deposer_fichier(cible, f.local, None, progression)
                break
            except Conflit:
                dossier = cible.rsplit('/', 1)[0] if '/' in cible else ''
                presents = {e.chemin.rsplit('/', 1)[-1] for e in session.client.propfind(dossier, 1)}
                cible = (dossier + '/' if dossier else '') + nom_libre(cible.rsplit('/', 1)[-1], presents)
                res['renommes'].append((f.distant, cible))
        else:
            raise ErreurPartage('pt_err_412', 412)
        res['fichiers'].append(cible)
        journal('pt_j_fichier', chemin=cible)
    if not plan.tableau:
        return res
    os.makedirs(sauvegardes, exist_ok=True)
    for essai in range(ESSAIS_TABLEAU):
        octets, etag = session.client.lire_avec_etag(plan.tableau)
        copie = os.path.join(sauvegardes, '%s_%s' % (time.strftime('%Y%m%d-%H%M%S'),
                                                    nom_sur(plan.tableau.rsplit('/', 1)[-1])))
        with open(copie, 'wb') as fh:
            fh.write(octets)
        res['sauvegarde'] = copie
        try:
            nouveau, ligne = tableur.ajouter_ligne(octets, plan.valeurs, plan.feuille or 0)
        except (tableur.ClasseurIllisible, KeyError, StopIteration, ValueError):
            break
        if not etag:
            break                                   # sans ETag, pas de dépôt conditionnel : on n'écrase pas
        try:
            session.client.deposer(plan.tableau, nouveau, si_etag=etag,
                                   type_mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            res['tableau'], res['ligne'] = 'ligne', ligne
            journal('pt_j_ligne', chemin=plan.tableau, ligne=ligne)
            return res
        except Conflit:
            journal('pt_j_conflit', chemin=plan.tableau, essai=essai + 1)
            time.sleep(0.5 * (essai + 1))
    # dernier recours : un petit fichier à côté
    session.client.deposer(plan.csv_secours, contenu_csv(plan), type_mime='text/csv')
    res['tableau'], res['csv'] = 'csv', plan.csv_secours
    journal('pt_j_csv', chemin=plan.csv_secours)
    return res
