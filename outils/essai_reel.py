"""Essai réel de bout en bout : télécharge une petite série depuis le serveur de l'Observatoire, la traite,
et compare au traitement de référence (journal.csv, INDEX_LOTS.csv, et quelques XISF de la copie complète).

    python outils/essai_reel.py DOSSIER_SORTIE [URL ...]
Sans URL : (914) Palisana (16 lignes, 6 doublons) + 2 images IRIS (UInt16 ; Float32 à CTYPE -SIP).
"""
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DEFAUT = ['http://tap-ufe.obspm.fr/getproduct/ufe/data/iris/2024/20240701/padc/M_16-S001-R001-C001-OIII.fits',
          'http://tap-ufe.obspm.fr/getproduct/ufe/data/iris/2024/20240704/padc/NGC_5866-S001-R001-C001-SDSS_z.fits']


def main():
    dest = Path(sys.argv[1])
    urls = set(sys.argv[2:] or DEFAUT)
    from coupole.cli import initialiser
    initialiser('fr')
    from coupole.core import astap, machine, parallele
    from coupole.modules.ohp.inventaire import Inventaire
    from coupole.modules.ohp.pilote import Traitement
    inv = Inventaire.charger()
    sel = [x for x in inv.images if x['objet'] == '(914) Palisana' or x['access_url'] in urls]
    e = astap.detecter()
    plan = parallele.planifier(machine.detecter())
    print('sélection : %d lignes ; ASTAP : %s ; plan : %s' % (len(sel), e.message_cle(), plan))
    evts = []
    t = Traitement(str(dest), inv, plan, {'format': 'xisf', 'langue': 'fr', 'astap': e if e.utilisable else None,
                                          'mode_astap': 'tous'}, rapporter=evts.append, arret=threading.Event())
    t0 = time.time()
    b = t.lancer(sel)
    t.fermer()
    print('durée %.1f s' % (time.time() - t0))
    print(json.dumps(b, indent=1))
    for ev in evts:
        if ev['type'] == 'echec':
            print('ECHEC', ev)


if __name__ == '__main__':
    main()
