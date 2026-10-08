"""coupole machine [--json] : ce que Coupole voit de l'ordinateur et ce qu'il en fait."""
from __future__ import annotations

import json

from ...core import config
from ...core.i18n import tr


def rapport() -> dict:
    """Diagnostic complet (dictionnaire) : partagé par la CLI et l'interface."""
    from ...core import astap, calcul, machine, parallele
    m = machine.detecter(rafraichir=True)
    r = config.reglages()
    plan = parallele.planifier(m, r['telechargements_max'], r['conversions_max'], True if r['mode_econome'] else None)
    e = astap.detecter(r['astap_executable'], r['astap_catalogue'])
    dest = r['dossier_sortie'] or str(config.dossier_sortie_defaut())
    return {'machine': m.en_dict(), 'plan': plan.__dict__, 'astap': {**e.__dict__, 'utilisable': e.utilisable},
            'gpu': calcul.resume_gpu(), 'disque_libre_go': round(machine.disque_libre_go(dest), 1),
            'destination': dest}


def lignes(d: dict) -> list[tuple[str, str]]:
    """(libellé, valeur) traduits, pour l'affichage."""
    m, p, a, g = d['machine'], d['plan'], d['astap'], d['gpu']
    out = [(tr('mach_systeme'), '%s %s (%s)' % (m['nom_systeme'], m['version_systeme'], m['architecture'])),
           (tr('mach_processeur'), m['processeur']),
           (tr('mach_coeurs'), tr('mach_coeurs_val', p=m['coeurs_physiques'], l=m['coeurs_logiques'])),
           (tr('mach_memoire'), tr('mach_memoire_val', t='%.1f' % (m['memoire_totale_mo'] / 1024),
                                   d='%.1f' % (m['memoire_disponible_mo'] / 1024))),
           (tr('mach_disque'), tr('mach_disque_val', g=d['disque_libre_go'], dest=d['destination'])),
           (tr('mach_python'), m['python'])]
    if m['cartes']:
        for c in m['cartes']:
            mem = (' — ' + tr('taille_mo', v=c['memoire_mo'])) if c['memoire_mo'] else ''
            out.append((tr('mach_gpu'), '%s [%s]%s' % (c['nom'], c['fabricant'], mem)))
    else:
        out.append((tr('mach_gpu'), tr('mach_gpu_aucune')))
    out.append((tr('mach_gpu_usage'), tr('mach_gpu_cupy_oui') if g['cupy'] else tr('mach_gpu_cupy_non')))
    out.append((tr('mach_plan'), tr('mach_plan_val', dl=p['telechargements'], conv=p['conversions'])))
    out.append((tr('mach_plan_raison'), tr(p['raison'])))
    out.append((tr('mach_econome'), tr('oui') if p['econome'] else tr('non')))
    out.append(('ASTAP', tr(('astap_pret' if a['utilisable'] else
                             'astap_absent' if not a['executable'] else
                             'astap_sans_catalogue' if not a['catalogue'] else 'astap_catalogue_incomplet'))))
    return out


def enregistrer(p):
    p.add_argument('--json', action='store_true', help=tr('cli_aide_json'))
    p.set_defaults(fonction=cmd)


def cmd(a):
    d = rapport()
    if a.json:
        print(json.dumps(d, indent=1, ensure_ascii=False, default=str))
        return 0
    largeur = max(len(k) for k, _ in lignes(d))
    for k, v in lignes(d):
        print('%-*s  %s' % (largeur, k, v))
    print()
    print(tr('mach_gpu_note'))
    return 0
