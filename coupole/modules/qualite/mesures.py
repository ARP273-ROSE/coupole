"""Mesures de qualité d'une image, avec SEP (Source Extractor en Python, LGPL) et numpy.

Ne sont proposées que les mesures qui retrouvent les valeurs injectées sur
images synthétiques (tests/test_qualite.py ; précision dans le manuel) :

  fond         médiane robuste du fond (SEP, maillage 64 px), en ADU et ADU/s.
               Pas de conversion en mag/arcsec² : la banque ne donne pas de point zéro fiable.
  bruit        écart-type robuste du fond (SEP, globalrms), ADU.
  rsn          rapport signal sur bruit médian des étoiles mesurées, SEULEMENT si le gain
               (EGAIN/GAIN, e-/ADU) est dans l'en-tête : sans gain, le bruit de photons de l'étoile est
               inconnu et la mesure serait fausse ; elle n'est alors pas donnée.
  fwhm         largeur à mi-hauteur d'un profil de Moffat elliptique à β libre ajusté sur chaque étoile
               (Levenberg-Marquardt, modèle intégré sur le pixel), départ donné par des moments adaptatifs
               (Bernstein & Jarvis 2002).  Médiane sur les étoiles isolées, non saturées, brillantes.
               (Des moments gaussiens seuls surestiment de 13 à 17 % la FWHM d'un profil de Moffat β = 3 :
               mesuré, d'où l'ajustement.)
  ellipticite  1 − b/a du même ajustement.
  carte 3×3    médianes de FWHM et d'ellipticité par neuvième de champ.
  gradient     pente du plan ajusté sur la carte du fond, en % du fond sur toute la diagonale ;
  residu       amplitude (P98 − P2) du fond après retrait du plan, en % : vignetage ou flat résiduel.
               Les « donuts » de poussière ne sont pas détectés (pas de méthode validée ici).
  satures      étoiles dont le pic dépasse le seuil de saturation (SATURATE/DATAMAX de l'en-tête, sinon
               60 000 ADU : convertisseur 16 bits, données calibrées).
  trainees     objets très allongés (grand axe ≥ 12 px et a/b ≥ 6) : traînées probables (satellites).
  echantillon  FWHM en pixels → sous-échantillonné (< 2 px), correct (2 à 5 px), sur-échantillonné (> 5 px).
"""
from __future__ import annotations

import math

import numpy as np

SEUIL_SAT_DEFAUT = 60000.0
SIGMA_FWHM = 2.0 * math.sqrt(2.0 * math.log(2.0))           # 2,3548 : FWHM = 2,3548 σ


_disponible: bool | None = None


def disponible() -> bool:
    """SEP est-il installé ?  Vérifié sans l'importer (find_spec) : rien de lourd au démarrage de l'interface."""
    global _disponible
    if _disponible is None:
        try:
            import importlib.util
            _disponible = importlib.util.find_spec('sep') is not None
        except Exception:
            _disponible = False
    return _disponible


def moments_adaptatifs(cut, x0, y0, s0=2.0, iterations=40):
    """Moments pondérés par une gaussienne adaptée (Bernstein & Jarvis 2002).

    Renvoie (x, y, Mxx, Myy, Mxy) : M est mis à jour à 2 × la covariance pondérée ; à convergence, pour une
    source gaussienne de covariance C, M = C (Mxx = σx²).
    """
    ny, nx = cut.shape
    yy, xx = np.mgrid[0:ny, 0:nx].astype(float)
    mxx = myy = s0 * s0 * 2
    mxy = 0.0
    x, y = x0, y0
    for _ in range(iterations):
        det = mxx * myy - mxy * mxy
        if det <= 0:
            return None
        dx, dy = xx - x, yy - y
        rho2 = (myy * dx * dx - 2 * mxy * dx * dy + mxx * dy * dy) / det
        w = np.exp(-0.5 * rho2)
        wi = w * cut
        s = wi.sum()
        if s <= 0:
            return None
        nxc = (wi * xx).sum() / s
        nyc = (wi * yy).sum() / s
        dx, dy = xx - nxc, yy - nyc
        cxx = (wi * dx * dx).sum() / s
        cyy = (wi * dy * dy).sum() / s
        cxy = (wi * dx * dy).sum() / s
        nmxx, nmyy, nmxy = 2 * cxx, 2 * cyy, 2 * cxy
        conv = abs(nmxx - mxx) + abs(nmyy - myy) + abs(nmxy - mxy) < 1e-6 * (mxx + myy) and \
            abs(nxc - x) + abs(nyc - y) < 1e-6
        x, y, mxx, myy, mxy = nxc, nyc, nmxx, nmyy, nmxy
        if not (0 <= x < nx and 0 <= y < ny) or mxx <= 0 or myy <= 0:
            return None
        if conv:
            break
    return x, y, mxx, myy, mxy


_SOUS = (np.arange(3) + 0.5) / 3 - 0.5        # intégration du modèle sur le pixel (3 × 3 points)


def _moffat(p, xx, yy):
    """Moffat elliptique intégré sur les pixels.  p = (fond, amplitude, x0, y0, ln αa, ln αb, θ, ln(β−1))."""
    fond, amp, x0, y0, la, lb, th, lbeta = p
    aa, ab, beta = math.exp(la), math.exp(lb), 1.0 + math.exp(lbeta)
    c, s = math.cos(th), math.sin(th)
    tot = 0.0
    for ox in _SOUS:
        for oy in _SOUS:
            dx, dy = xx + ox - x0, yy + oy - y0
            u, v = c * dx + s * dy, -s * dx + c * dy
            tot = tot + (1.0 + (u / aa) ** 2 + (v / ab) ** 2) ** (-beta)
    return fond + amp * tot / 9.0


def ajuster_moffat(cut, x0, y0, moments, iterations=60):
    """Ajustement de Levenberg-Marquardt (numpy seul) d'un profil de Moffat elliptique à β libre.

    Le β libre couvre à la fois les profils gaussiens (β grand) et les ailes des étoiles réelles.  Renvoie
    (FWHM moyenne géométrique, FWHM grand axe, petit axe, ellipticité, angle en degrés, β) ou None.
    """
    ny, nx = cut.shape
    yy, xx = np.mgrid[0:ny, 0:nx].astype(float)
    z = cut.ravel()
    xx, yy = xx.ravel(), yy.ravel()
    beta0 = 3.0
    # départ : axes et orientation des moments adaptatifs (sinon θ n'a aucun gradient à αa = αb)
    _, fa0, fb0, _, ang0 = forme(*moments)
    k0 = 2 * math.sqrt(2 ** (1 / beta0) - 1)
    p = np.array([float(np.median(cut[[0, -1], :])), float(cut.max()), x0, y0, math.log(max(0.4, fa0 / k0)),
                  math.log(max(0.4, fb0 / k0)), math.radians(ang0), math.log(beta0 - 1)])
    lam = 1e-3
    mod = _moffat(p, xx, yy)
    chi2 = float(((z - mod) ** 2).sum())
    for _ in range(iterations):
        J = np.empty((z.size, p.size))
        for k in range(p.size):
            h = 1e-4 * max(1.0, abs(p[k])) if k != 1 else 1e-4 * max(1.0, abs(p[1]))
            q = p.copy()
            q[k] += h
            J[:, k] = (_moffat(q, xx, yy) - mod) / h
        g = J.T @ (z - mod)
        H = J.T @ J
        amelioree = False
        for _ in range(10):
            try:
                pas = np.linalg.solve(H + lam * np.diag(np.diag(H) + 1e-12), g)
            except np.linalg.LinAlgError:
                return None
            q = p + pas
            q[7] = min(q[7], math.log(199.0))           # β ≤ 200 : au-delà, profil gaussien à mieux que 0,1 %
            m2 = _moffat(q, xx, yy)
            c2 = float(((z - m2) ** 2).sum())
            if c2 < chi2:
                rel = (chi2 - c2) / max(chi2, 1e-30)
                p, mod, chi2, lam = q, m2, c2, max(lam / 3, 1e-9)
                amelioree = True
                break
            lam *= 4
        if not amelioree or rel < 1e-9:
            break
    fond, amp, x0, y0, la, lb, th, lbeta = p
    beta = 1.0 + math.exp(lbeta)
    k = 2 * math.sqrt(2 ** (1 / beta) - 1)
    fa, fb = k * math.exp(la), k * math.exp(lb)
    if fb > fa:
        fa, fb, th = fb, fa, th + math.pi / 2
    if amp <= 0 or not (0 <= x0 < nx and 0 <= y0 < ny):
        return None
    return math.sqrt(fa * fb), fa, fb, 1 - fb / fa, math.degrees(th) % 180, beta


def forme(mxx, myy, mxy):
    """(FWHM moyenne géométrique, FWHM grand axe, petit axe, ellipticité, angle en degrés)."""
    # à convergence, M est la covariance de la source (point fixe M = 2 (C⁻¹ + M⁻¹)⁻¹ ⇒ M = C)
    t = (mxx + myy) / 2
    d = math.sqrt(max(0.0, ((mxx - myy) / 2) ** 2 + mxy ** 2))
    l1, l2 = t + d, max(t - d, 1e-12)
    a, b = math.sqrt(l1), math.sqrt(l2)
    ang = 0.5 * math.degrees(math.atan2(mxy, mxx - myy))
    return SIGMA_FWHM * math.sqrt(a * b), SIGMA_FWHM * a, SIGMA_FWHM * b, 1 - b / a, ang


def lire_image(chemin):
    """(données float64 natives, en-tête dict) depuis XISF, FITS ou FITS compressé."""
    p = str(chemin)
    if p.lower().endswith('.xisf'):
        from ...core import xisf
        a, inf = xisf.lire(p)
        ent = {}
        for k, v, c in inf['mots_cles']:
            if k not in ('HISTORY', 'COMMENT'):
                ent[k] = v.strip("'").strip() if v.startswith("'") else v
        return np.asarray(a, dtype=np.float64), ent
    import warnings
    from astropy.io import fits
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        with fits.open(p, memmap=False) as hd:
            for h in hd:
                if getattr(h, 'data', None) is not None and np.ndim(h.data) == 2:
                    return np.asarray(h.data, dtype=np.float64), {k: h.header[k] for k in h.header
                                                                  if k not in ('HISTORY', 'COMMENT', '')}
    raise ValueError('no 2-D image in %s' % p)


def _flottant(ent, *cles):
    for k in cles:
        try:
            return float(ent[k])
        except (KeyError, TypeError, ValueError):
            continue
    return None


def echelle(ent):
    """Secondes d'arc par pixel : PIXSCALE, sinon la matrice CD, sinon CDELT."""
    v = _flottant(ent, 'PIXSCALE', 'SCALE')
    if v:
        return v
    cd = [_flottant(ent, k) for k in ('CD1_1', 'CD1_2', 'CD2_1', 'CD2_2')]
    if all(c is not None for c in cd):
        return math.sqrt(abs(cd[0] * cd[3] - cd[1] * cd[2])) * 3600
    c1 = _flottant(ent, 'CDELT1')
    return abs(c1) * 3600 if c1 else None


def analyser(data, ent=None, max_etoiles=400):
    """Mesure une image ; renvoie un dictionnaire (valeurs None quand la mesure n'est pas possible)."""
    import sep
    ent = ent or {}
    a = np.ascontiguousarray(data, dtype=np.float64)
    masque = ~np.isfinite(a)
    if masque.any():
        a = np.where(masque, 0.0, a)
    ny, nx = a.shape
    bkg = sep.Background(a, mask=masque, bw=64, bh=64, fw=3, fh=3)
    fond_carte = bkg.back()
    sub = a - fond_carte
    rms = float(bkg.globalrms)
    r = {'nx': nx, 'ny': ny, 'fond_adu': float(bkg.globalback), 'bruit_adu': rms}
    pose = _flottant(ent, 'EXPTIME', 'EXPOSURE')
    r['fond_adu_s'] = r['fond_adu'] / pose if pose else None
    sep.set_extract_pixstack(max(300000, nx * ny // 4))
    try:
        objs = sep.extract(sub, 5.0, err=rms, mask=masque, minarea=5, deblend_cont=0.005)
    except Exception:
        objs = np.zeros(0, dtype=[('x', float), ('y', float), ('a', float), ('b', float), ('peak', float),
                                  ('flux', float), ('flag', int), ('theta', float)])
    r['sources'] = int(len(objs))
    seuil_sat = _flottant(ent, 'SATURATE', 'DATAMAX') or SEUIL_SAT_DEFAUT
    r['seuil_saturation'] = seuil_sat
    pics = objs['peak'] + fond_carte[np.clip(objs['y'].astype(int), 0, ny - 1),
                                     np.clip(objs['x'].astype(int), 0, nx - 1)] if len(objs) else np.zeros(0)
    sat = pics >= seuil_sat
    r['satures'] = int(sat.sum())
    longues = (objs['a'] >= 12 / 2.0) & (objs['a'] / np.maximum(objs['b'], 1e-3) >= 6) if len(objs) else np.zeros(0, bool)
    # sep : a, b = écarts-types des grands et petits axes ; une traînée de longueur L a a ≈ L / √12
    longues = (objs['a'] * math.sqrt(12) >= 12) & (objs['a'] / np.maximum(objs['b'], 1e-3) >= 6) if len(objs) else longues
    r['trainees'] = int(longues.sum())
    r['trainees_detail'] = [(float(o['x']), float(o['y']), float(np.degrees(o['theta'])))
                            for o in objs[longues]][:10] if len(objs) else []
    # étoiles pour la forme : isolées, non saturées, assez brillantes, loin des bords, peu allongées
    mesures = []
    if len(objs):
        pos = np.c_[objs['x'], objs['y']]
        ordre = np.argsort(-objs['flux'])
        for i in ordre:
            o = objs[i]
            if sat[i] or longues[i] or o['flag'] & 0b11 or o['peak'] < 20 * rms:
                continue
            x, y = float(o['x']), float(o['y'])
            demi = int(max(7, math.ceil(4 * max(o['a'], 1.0))))
            if x < demi or y < demi or x >= nx - demi - 1 or y >= ny - demi - 1:
                continue
            d = np.hypot(pos[:, 0] - x, pos[:, 1] - y)
            if np.sum(d < 2 * demi) > 1:
                continue
            xi, yi = int(round(x)), int(round(y))
            cut = sub[yi - demi:yi + demi + 1, xi - demi:xi + demi + 1]
            m = moments_adaptatifs(cut, x - xi + demi, y - yi + demi, s0=max(1.0, float(o['a'])))
            if m is None:
                continue
            fit = ajuster_moffat(cut, m[0], m[1], m[2:])
            if fit is None:
                continue
            fw, fa, fb, e, ang, beta = fit
            if not (0.8 < fw < 4 * demi):
                continue
            mesures.append((x, y, fw, e, ang, float(o['flux'])))
            if len(mesures) >= max_etoiles:
                break
    r['etoiles'] = len(mesures)
    if mesures:
        m = np.array(mesures)
        r['fwhm_px'] = float(np.median(m[:, 2]))
        r['ellipticite'] = float(np.median(m[:, 3]))
        r['fwhm_px_disp'] = float(np.median(np.abs(m[:, 2] - r['fwhm_px'])) * 1.4826)
        carte_f, carte_e = [], []
        for j in range(3):
            lf, le = [], []
            for k in range(3):
                sel = (m[:, 0] >= k * nx / 3) & (m[:, 0] < (k + 1) * nx / 3) & \
                      (m[:, 1] >= j * ny / 3) & (m[:, 1] < (j + 1) * ny / 3)
                lf.append(float(np.median(m[sel, 2])) if sel.sum() >= 3 else None)
                le.append(float(np.median(m[sel, 3])) if sel.sum() >= 3 else None)
            carte_f.append(lf)
            carte_e.append(le)
        r['carte_fwhm'] = carte_f
        r['carte_ellipticite'] = carte_e
        gain = _flottant(ent, 'EGAIN', 'GAIN')
        if gain and gain > 0:
            # aperture de rayon 1,5 FWHM ; bruit = fond (rms par pixel) + photons de l'étoile (flux / gain)
            rayon = 1.5 * r['fwhm_px']
            flux, err, _ = sep.sum_circle(sub, m[:, 0], m[:, 1], rayon, err=rms, gain=gain)
            ok = (flux > 0) & (err > 0)
            r['rsn'] = float(np.median(flux[ok] / err[ok])) if ok.any() else None
        else:
            r['rsn'] = None
    else:
        r.update(fwhm_px=None, ellipticite=None, fwhm_px_disp=None, carte_fwhm=None, carte_ellipticite=None, rsn=None)
    # fond : plan ajusté sur la carte, puis résidu
    pas = max(1, min(nx, ny) // 64)
    yy, xx = np.mgrid[0:ny:pas, 0:nx:pas]
    z = fond_carte[::pas, ::pas]
    A = np.c_[np.ones(z.size), xx.ravel(), yy.ravel()]
    coef, *_ = np.linalg.lstsq(A, z.ravel(), rcond=None)
    med = float(np.median(z))
    if med > 0:
        pente = math.hypot(coef[1], coef[2])
        r['gradient_pct'] = float(100 * pente * math.hypot(nx, ny) / med)
        r['gradient_angle'] = float(math.degrees(math.atan2(coef[2], coef[1])))
        res = z.ravel() - A @ coef
        r['residu_pct'] = float(100 * (np.percentile(res, 98) - np.percentile(res, 2)) / med)
    else:
        r['gradient_pct'] = r['gradient_angle'] = r['residu_pct'] = None
    sc = echelle(ent)
    r['echelle'] = sc
    if r['fwhm_px']:
        r['fwhm_arcsec'] = r['fwhm_px'] * sc if sc else None
        r['echantillonnage'] = 'sous' if r['fwhm_px'] < 2 else 'sur' if r['fwhm_px'] > 5 else 'correct'
    else:
        r['fwhm_arcsec'] = None
        r['echantillonnage'] = None
    return r
