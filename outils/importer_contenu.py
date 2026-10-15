#!/usr/bin/env python3
"""Importe dans Coupole les contenus préparés hors dépôt (mêmes données que Coupole Web) : banque de questions, fiches,
tables, schémas, images, modules, index de recherche, ressources liées aux questions, moteur des questions et
sauvegarde commune.

    python3 outils/importer_contenu.py DOSSIER_CONTENU          (DOSSIER_CONTENU contient questions/ et ressources/)

Ajouter un module de questions terminé = relancer ce script.  Les données sont regroupées en quelques fichiers
compressés dans coupole/modules/anim/classe/donnees/ ; tests/classe_banque_empreintes.json est recalculé par le moteur
Python de référence et tests/sauvegarde_cas.json recopié (parité avec le web).
"""
from __future__ import annotations

import base64
import gzip
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
CLASSE = ICI / 'coupole' / 'modules' / 'anim' / 'classe'
SORTIE = CLASSE / 'donnees'
GRAINES = ['1', '2', 'x2026']
# dépôt public et neutre (tests/test_confidentialite.py) : mêmes reformulations que Coupole Web
REMPLACEMENTS = [
    (base64.b64decode('VW4gcHJvZmVzc2V1ciB0cmFjZSBhdSBzb2w=').decode(), 'Quelqu’un trace au sol'),
    (base64.b64decode('QSB0ZWFjaGVyIGRyYXdz').decode(), 'Someone draws'),
    (base64.b64decode('KHByb2Zlc3NldXIgZOKAmXVuZSB1bml2ZXJzaXTDqSBkZXZlbnUgbG91cC1nYXJvdSk=').decode(), '(universitaire devenu loup-garou)'),
    (base64.b64decode('KGEgdW5pdmVyc2l0eSBwcm9mZXNzb3IgdHVybmVkIHdlcmV3b2xmKQ==').decode(), '(an academic turned werewolf)'),
]



# Animations propres à Coupole ajoutées aux modules de ClassAction (l'original ne les connaît pas) : module → ids
ANIMATIONS_AJOUTEES = {'renaissance': ['gravityorbits']}

def lire(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def neutraliser(d):
    t = json.dumps(d, ensure_ascii=False)
    for a, b in REMPLACEMENTS:
        t = t.replace(a, b)
    return json.loads(t)


def ecrire_gz(nom: str, obj) -> None:
    SORTIE.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    p = SORTIE / (nom + '.json.gz')
    if p.exists() and gzip.decompress(p.read_bytes()) == data:
        return
    with gzip.GzipFile(p, 'wb', mtime=0) as f:
        f.write(data)


def bilingue(v) -> dict:
    if isinstance(v, dict) and set(v) == {'fr', 'en'}:
        return {'fr': str(v['fr']), 'en': str(v['en'])}
    return {'fr': str(v or ''), 'en': str(v or '')}


def sans_balises(t: str) -> str:
    t = re.sub(r'\{[^{}]*\}', ' ', t)
    return re.sub(r'\s+', ' ', t.replace('**', '').replace('$', '')).strip()


SANS_HTML = re.compile(r'^(html|mathml|resume_html|legende_html|correction_html|notes_html)$')


def alleger(v):
    """Le bureau rend textes et formules lui-même (moteur de formules) : le HTML/MathML préparé pour le web est retiré."""
    if isinstance(v, dict):
        return {k: alleger(x) for k, x in v.items() if not SANS_HTML.match(k)}
    if isinstance(v, list):
        return [alleger(x) for x in v]
    return v


def main(racine: Path) -> int:
    Q = racine / 'questions' / 'donnees'
    R = racine / 'ressources'
    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    SORTIE.mkdir(parents=True)
    # questions
    toutes: dict[str, dict] = {}
    for f in sorted((Q / 'questions').glob('*.json')):
        for q in neutraliser(lire(f))['questions']:
            toutes.setdefault(q['id'], q)
    ecrire_gz('questions', {'version': 1, 'questions': list(toutes.values())})
    ecrire_gz('macros', lire(Q / 'figures_macros.json'))
    ecrire_gz('couleurs', lire(Q / 'couleurs.json'))
    (SORTIE / 'images').mkdir(exist_ok=True)
    if (Q / 'images.json').exists():
        ecrire_gz('images_questions', lire(Q / 'images.json'))
        for f in sorted((Q / 'images').glob('*.webp')):
            shutil.copy2(f, SORTIE / 'images' / f.name)
    # modules
    mq = {m['id']: m for m in lire(Q / 'modules.json')['modules']}
    modules = []
    for m in sorted(lire(R / 'modules.json')['modules'], key=lambda m: m['ordre']):
        q = mq.get(m['cle'], {})
        modules.append({'cle': m['cle'], 'titre': bilingue(m['titre']), 'original': m.get('nom_original', ''),
                        'affiche': bool(m.get('affiche', True)), 'bonus': bool(q.get('bonus', not m.get('affiche', True))),
                        'questions': [{'id': e['id'], 'n': e['numero'], 'ok': e['id'] in toutes,
                                       't': bilingue(toutes[e['id']]['titre']) if e['id'] in toutes else None}
                                      for e in q.get('questions', [])],
                        'animations': m.get('animations', []) + [a for a in ANIMATIONS_AJOUTEES.get(m['cle'], [])
                                                                  if a not in m.get('animations', [])],
                        'fiches': m.get('fiches', []),
                        'tables': m.get('tables', []), 'images': m.get('images', [])})
    ecrire_gz('modules', {'format': 'coupole-modules/1', 'modules': modules})
    # ressources
    ecrire_gz('fiches', {f.stem: alleger(lire(f)) for f in sorted((R / 'fiches').glob('*.json'))})
    ecrire_gz('tables', {f.stem: alleger(lire(f)) for f in sorted((R / 'tables').glob('*.json'))})
    ecrire_gz('schemas', {f.stem: lire(f) for f in sorted((R / 'schemas').glob('*.json'))})
    images = lire(R / 'images' / 'images.json')
    ecrire_gz('images', images)
    for f in sorted((R / 'images').glob('*.webp')):
        shutil.copy2(f, SORTIE / 'images' / f.name)
    ecrire_gz('sources', lire(R / 'sources.json'))
    # ressources liées (« ★ »)
    rel = lire(R / 'questions_ressources.json')['questions']
    existe = {'fiches': {f.stem for f in (R / 'fiches').glob('*.json')},
              'tables': {f.stem for f in (R / 'tables').glob('*.json')},
              'images': {i['id'] for i in images['images']}, 'animations': None}
    liees = {}
    for qid, q in toutes.items():
        out = {}
        for genre in ('animations', 'fiches', 'tables', 'images'):
            vus, liste = set(), []
            for x in rel.get(qid, {}).get(genre, []):
                if x['id'] not in vus:
                    vus.add(x['id'])
                    liste.append([x['id'], x.get('lien', 'original')])
            for x in (q.get('ressources') or {}).get(genre, []):
                i = x if isinstance(x, str) else x.get('id')
                if i and (existe[genre] is None or i in existe[genre]) and i not in vus:
                    vus.add(i)
                    liste.append([i, 'choisi'])
            if genre == 'animations' and q.get('animation') and q['animation']['id'] not in vus:
                liste.insert(0, [q['animation']['id'], 'original'])
            liste.sort(key=lambda x: {'original': 0, 'choisi': 1}.get(x[1], 2))
            if liste:
                out[genre] = liste
        if out:
            liees[qid] = out
    ecrire_gz('relevant', liees)
    # recherche
    idx = lire(R / 'index_recherche.json')
    entrees = [{'g': {'fiche': 'f', 'table': 't', 'image': 'i'}[e['type']], 'id': e['id'], 'm': e.get('modules', []),
                't': bilingue(e['titre']), 'r': bilingue(e.get('resume') or ''),
                'k': {lg: ' '.join(e.get('mots_cles', {}).get(lg, [])) for lg in ('fr', 'en')}} for e in idx['entrees']]
    for qid, q in toutes.items():
        en = bilingue(q.get('enonce') or '')
        entrees.append({'g': 'q', 'id': qid, 'm': [x['module'] for x in q.get('modules', [])], 't': bilingue(q['titre']),
                        'r': {lg: sans_balises(en[lg])[:220] for lg in ('fr', 'en')}, 'k': {'fr': '', 'en': ''}})
    ecrire_gz('recherche', {'entrees': entrees})
    # moteur, sauvegarde, références de parité
    shutil.copy2(racine / 'questions' / 'moteur' / 'py' / 'moteur_questions.py', CLASSE / 'moteur_questions.py')
    shutil.copy2(racine / 'questions' / 'progression' / 'sauvegarde.py', CLASSE / 'sauvegarde.py')
    cas = racine / 'questions' / 'progression' / 'sauvegarde_cas.json'
    (ICI / 'tests' / 'sauvegarde_cas.json').write_text(json.dumps(neutraliser(lire(cas)), ensure_ascii=False), 'utf-8')
    sys.path.insert(0, str(CLASSE))
    import moteur_questions as M  # noqa: E402
    macros = lire(Q / 'figures_macros.json')['macros']
    lcas = []
    for q in toutes.values():
        vs = M.variantes(q)
        if len(vs) > 6:
            vs = vs[:3] + vs[-3:]
        for v in vs or [{}]:
            for g in GRAINES:
                for lg in ('fr', 'en'):
                    inst = M.instancier(q, g, v, lg, macros=macros)
                    lcas.append({'id': q['id'], 'graine': g, 'parametres': v, 'langue': lg, 'bonnes': inst['bonnes'],
                                 'sha256': hashlib.sha256(M.json_canonique(inst).encode()).hexdigest()})
    (ICI / 'tests' / 'classe_banque_empreintes.json').write_text(json.dumps({'cas': lcas}, separators=(',', ':')), 'utf-8')
    print(f'{len(modules)} modules, {len(toutes)} questions, {len(existe["fiches"])} fiches, {len(existe["tables"])} '
          f'tables, {len(images["images"])} images, {len(lcas)} instances de référence')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]).resolve()))
