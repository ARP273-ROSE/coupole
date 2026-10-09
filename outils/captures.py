"""Captures d'écran de l'interface (pour le manuel et les tests visuels), sans écran :

    QT_QPA_PLATFORM=offscreen python outils/captures.py fr docs/manuel/img [DOSSIER_QUALITE] [DESTINATION]

DESTINATION : un dossier de sortie (INDEX_LOTS.csv et quelques images par lot) pour l'onglet Lots et son encadré
« Pour PixInsight / N.I.N.A. ».
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def attendre(app, condition, delai=30.0):
    t0 = time.time()
    while not condition() and time.time() - t0 < delai:
        app.processEvents()
        time.sleep(0.02)


def spectre_exemple(dossier):
    """Spectre H I synthétique (raie à -40 km/s et +25 km/s) pour illustrer le module Spectres et séries."""
    import numpy as np
    from astropy.io import fits
    from coupole.core import donnees as D
    n, f0 = 1024, D.HI_HZ
    df = 2.4e6 / n
    f = f0 - 1.2e6 + np.arange(n) * df
    y = 12 + 6 * np.exp(-0.5 * ((f - D.frequence_depuis_vitesse(-40, f0)) / 40e3) ** 2) \
        + 3 * np.exp(-0.5 * ((f - D.frequence_depuis_vitesse(25, f0)) / 25e3) ** 2) \
        + np.random.default_rng(1).normal(0, 0.25, n)
    h = fits.Header()
    h.update(CTYPE1='FREQ', CUNIT1='Hz', CRVAL1=f[0], CDELT1=df, CRPIX1=1.0, RESTFRQ=f0, SPECSYS='TOPOCENT', BUNIT='K',
             BTYPE='Ta')
    p = Path.home() / 'spectre_HI_synthetique.fits'
    fits.PrimaryHDU(y, header=h).writeto(p, overwrite=True)
    return str(p)


def main():
    langue = sys.argv[1] if len(sys.argv) > 1 else 'fr'
    dossier = Path(sys.argv[2] if len(sys.argv) > 2 else 'captures')
    dossier.mkdir(parents=True, exist_ok=True)
    from PyQt6.QtWidgets import QApplication
    from coupole.cli import initialiser
    from coupole.core import config, rapports
    config.reglages()['rapports_autorises'] = False
    config.reglages()['maj_auto'] = False
    initialiser(langue)
    rapports.init()
    app = QApplication(sys.argv)
    from coupole.gui import theme
    config.reglages()['apparence'] = os.environ.get('COUPOLE_THEME', config.DEFAUTS['apparence'])   # le défaut : sombre
    theme.appliquer(app)
    from coupole.gui.fenetre import FenetrePrincipale
    f = FenetrePrincipale()
    f.resize(1400, 860)
    f.show()
    ohp = f.panneaux[0]
    attendre(app, lambda: ohp.inv is not None)
    attendre(app, lambda: not getattr(ohp, '_etapes', None) and getattr(ohp, '_comptes', None) is not None)
    # possession d'exemple (illustration des pastilles du manuel) : un tiers des objets complets, un tiers en
    # partie, quelques échecs, le reste à télécharger
    from coupole.modules.ohp.conversion import ident
    from coupole.modules.ohp.possession import Possession
    par_objet = {}
    for x in ohp.inv.images:
        if not x['doublon']:
            par_objet.setdefault(x['objet'], []).append(x)
    statuts = {}
    for k, (o, l) in enumerate(sorted(par_objet.items())):
        if o == 'NGC 6888' or k % 3 == 1:
            statuts.update({ident(x): 'ok' for x in l[:max(1, len(l) // 2)]})
        elif k % 3 == 0:
            statuts.update({ident(x): 'ok' for x in l})
            if len(l) > 2:
                statuts[ident(l[-1])] = 'doublon'
        if k % 11 == 4:
            statuts[ident(l[0])] = 'echec'
    poss = Possession(ohp._dest_courante(), statuts)
    ohp._possession_prete((poss, [], poss.compte_objets(ohp.inv.images), ohp.inv.images))
    # sélection : NGC 6888 (exemple du manuel)
    for r, o in enumerate(ohp.m_obj.donnees):
        if o['objet'] == 'NGC 6888':
            idx = ohp.p_obj.mapFromSource(ohp.m_obj.index(r, 0))
            ohp.v_obj.selectRow(idx.row())
            ohp.v_obj.scrollTo(idx)
    attendre(app, lambda: False, 0.5)
    ohp.f_nuit.setCurrentIndex(max(0, ohp.f_nuit.findData('2025-07-16')))
    attendre(app, lambda: False, 0.5)

    def capture(nom):
        attendre(app, lambda: False, 0.4)
        f.grab().save(str(dossier / ('%s_%s.png' % (nom, langue))))

    capture('catalogue')
    ohp.vers_traitement()
    capture('traitement')
    ohp.onglets.setCurrentIndex(3)
    attendre(app, lambda: ohp.m_anom.rowCount() > 0, 20)
    capture('anomalies')
    ohp.onglets.setCurrentIndex(4)
    capture('ciel')
    ohp.onglets.setCurrentIndex(2)
    if len(sys.argv) > 4:                          # vraie destination : lots, focale, pixel, échelle
        ohp.dest.setText(sys.argv[4])
        ohp._remplir_lots()
        attendre(app, lambda: ohp.m_lots.rowCount() > 0 and getattr(ohp, '_inst_lots', None), 30)
        r = next((k for k, l in enumerate(ohp.m_lots.lignes) if l[0].endswith('champ_1_T120/V')), 0)
        ohp.v_lots.selectRow(ohp.p_lots.mapFromSource(ohp.m_lots.index(r, 0)).row())
        attendre(app, lambda: ohp._astro_valeurs['focale'].text() != '—', 20)
    capture('lots')
    # fiche en ligne de NGC 6888 (vraie requête SIMBAD si Internet est disponible, sinon message hors ligne)
    ohp.onglets.setCurrentIndex(ohp.onglet_fiche)
    attendre(app, lambda: ohp.fiche.resultat() is not None, 30)
    capture('fiche')
    ohp.onglets.setCurrentIndex(0)
    for i, p in enumerate(f.panneaux):
        mid = getattr(getattr(p, 'module', None), 'id', '')
        if mid == 'donnees':
            p.ouvrir(spectre_exemple(dossier))
            p.axe.setCurrentIndex(2)
        if mid == 'sites':
            p.en_ligne.setChecked(False)           # pas de tuiles téléchargées pour les captures
        if mid == 'cosmo':                         # 3C 273, Planck 2018, comparaison SH0ES
            f.barre.setCurrentRow(i)               # le premier calcul part au premier affichage
            attendre(app, lambda: p.resultat is not None, 60)
            p.shoes.setChecked(True)
            p.recevoir_redshift(0.158, '3C 273')
            attendre(app, lambda: p.resultat is not None and abs(p.resultat['z'] - 0.158) < 1e-9
                     and 'shoes' in p.resultat, 60)
            # les deux dispositions : côte à côte sur un grand écran (2 000 px), empilée à 1 400 px
            f.barre.setCurrentRow(i)
            f.resize(2000, 1000)
            p.definir_disposition('cote')
            attendre(app, lambda: False, 1.5)
            capture('module_cosmo_cote')
            p.definir_disposition('auto')
            f.resize(1400, 860)
        if mid == 'qualite' and len(sys.argv) > 3:
            p.l_dossier.setText(sys.argv[3])
            p.lancer()
            attendre(app, lambda: not p.occupe(), 120)
        if mid and mid != 'ohp':
            f.barre.setCurrentRow(i)
            attendre(app, lambda: False, 1.5)
            capture('module_' + mid)
    from coupole.gui import dialogues
    for nom, classe in (('astap', dialogues.DialogueASTAP), ('apropos', dialogues.DialogueAPropos),
                        ('reglages', dialogues.DialogueReglages)):
        d = classe(f)
        d.show()
        attendre(app, lambda: False, 0.5)
        d.grab().save(str(dossier / ('%s_%s.png' % (nom, langue))))
        d.close()
    print('captures dans', dossier)


if __name__ == '__main__':
    main()
