# Vérification SageMath de l'animation « Le mécanisme de Kozai-Lidov » (code propre à Coupole).
# 1) Depuis le hamiltonien séculaire quadrupolaire d'une particule test (W = 2 + 3e² − 3 sin²i (1 − e² + 5e² sin²ω),
#    variables de Delaunay G = √(1 − e²), H = G cos i), redérive de/dτ, dω/dτ, dΩ/dτ ; vérifie que la forme
#    vectorielle intégrée par Coupole donne les mêmes de/dτ et di/dτ.
# 2) Inclinaison critique, e_max = √(1 − 5/3 cos² i₀), inclinaison au maximum (39,23°), t_K des trois systèmes.
# 3) Intégration indépendante (mpmath.odefun, série de Taylor, 25 chiffres) : état à τ = 3 et τ = 7.5 pour deux
#    départs, et instants des deux premiers maxima de e (période des oscillations).
# Usage : sage outils/verif_anim/kozai_verif.sage   (écrit tests/kozai_sage.json)
import json, os
import mpmath
from sage.version import version as VERSION_SAGE
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'kozai_sage.json'))
G, Hz, w, e, i = var('G Hz w e i')
assume(G > 0); assume(G < 1); assume(e > 0); assume(e < 1)
W = 2 + 3*(1 - G^2) - 3*(1 - (Hz/G)^2)*(G^2 + 5*(1 - G^2)*sin(w)^2)
Ham = -W/8
sub = {G: sqrt(1 - e^2), Hz: sqrt(1 - e^2)*cos(i)}
de = (-G/sqrt(1 - G^2)*(-diff(Ham, w))).subs(sub)
ok_de = bool((de - 15/8*e*sqrt(1 - e^2)*sin(i)^2*sin(2*w)).simplify_full().simplify_trig() == 0)
ok_dw = bool((diff(Ham, G).subs(sub) - 3/4/sqrt(1 - e^2)*(2*(1 - e^2) + 5*sin(w)^2*(e^2 - sin(i)^2))).simplify_full().simplify_trig() == 0)
print('hamiltonien -> de/dτ, dω/dτ :', ok_de, ok_dw)
R = RealField(80)
z = vector(R, [0, 0, 1])
def vecs(e_, i_, w_, O_=0):
    e_, i_, w_, O_ = R(e_), R(i_) * R(pi) / 180, R(w_) * R(pi) / 180, R(O_) * R(pi) / 180
    eh = vector(R, [cos(O_)*cos(w_) - sin(O_)*sin(w_)*cos(i_), sin(O_)*cos(w_) + cos(O_)*sin(w_)*cos(i_), sin(w_)*sin(i_)])
    nh = vector(R, [sin(O_)*sin(i_), -cos(O_)*sin(i_), cos(i_)])
    return e_*eh, sqrt(1 - e_^2)*nh
def rhs(ev, jv):
    dj = R(3)/4*((jv*z)*jv.cross_product(z) - 5*(ev*z)*ev.cross_product(z))
    dev = R(3)/4*((jv*z)*ev.cross_product(z) + 2*jv.cross_product(ev) - 5*(ev*z)*jv.cross_product(z))
    return dev, dj
ok_vect = True
for (e_, i_, w_) in ((0.3, 63, 40), (0.6, 52, 130), (0.1, 80, 229)):
    ev, jv = vecs(e_, i_, w_)
    dev, dj = rhs(ev, jv)
    ir, wr = R(i_)*R(pi)/180, R(w_)*R(pi)/180
    a = ev*dev/ev.norm(); b = R(15)/8*R(e_)*sqrt(1-R(e_)^2)*sin(ir)^2*sin(2*wr)
    ok_vect = ok_vect and abs(a - b) < 1e-20
print('forme vectorielle = forme en éléments :', ok_vect)
ic = arccos(sqrt(R(3)/5)) * 180 / R(pi)
out = {'sage': VERSION_SAGE, 'hamiltonien': bool(ok_de and ok_dw), 'vectoriel': bool(ok_vect),
       'i_critique': float(ic), 'e_max': {}, 'i_au_max': {}, 't_k': {}, 'etats': [], 'maxima': {}}
for i0 in (45, 65, 80, 89):
    c2 = cos(R(i0)*R(pi)/180)^2
    em = sqrt(1 - R(5)/3*c2)
    out['e_max'][str(i0)] = float(em)
    out['i_au_max'][str(i0)] = float(arccos(cos(R(i0)*R(pi)/180)/sqrt(1 - em^2))*180/R(pi))
JS = R('86164.0905'); AN = R('365.25')*86400
for k, m, ap, per in (('asteroide', R('1047.348644'), R('5.2026')/R('2.7'), R('2.7')^R('1.5')),
                      ('satellite', R('81.300568'), R(384400)/R(26560), JS/2/AN),
                      ('exoplanete', R(1), R(100), R(5)^R('1.5'))):
    out['t_k'][k] = float(m*ap^3*per/(2*R(pi)))
mpmath.mp.dps = 25
def f(t, y):
    ev = vector(R, y[0:3]); jv = vector(R, y[3:6])
    dev, dj = rhs(ev, jv)
    return [mpmath.mpf(float(x)) for x in list(dev) + list(dj)]
def f_mp(t, y):
    ex, ey, ez, jx, jy, jz = y
    jxz = (jy, -jx, 0); exz = (ey, -ex, 0)
    jxe = (jy*ez - jz*ey, jz*ex - jx*ez, jx*ey - jy*ex)
    q = mpmath.mpf(3)/4
    dj = [q*(jz*jxz[k] - 5*ez*exz[k]) for k in range(3)]
    dev = [q*(jz*exz[k] + 2*jxe[k] - 5*ez*jxz[k]) for k in range(3)]
    return dev + dj
for (e0, i0, w0) in ((0.05, 65, 0), (0.3, 50, 90)):
    ev, jv = vecs(e0, i0, w0)
    y0 = [mpmath.mpf(str(x)) for x in list(ev) + list(jv)]
    sol = mpmath.odefun(f_mp, 0, y0)
    etats = {}
    for tt in ('3', '7.5'):
        y = sol(mpmath.mpf(tt))
        etats[tt] = [float(v) for v in y]
    out['etats'].append({'e0': float(e0), 'i0': float(i0), 'w0': float(w0), 'etats': etats})
    # maxima de e : zéros de e·de/dτ (de + à −)
    def s(t):
        y = sol(t); d = f_mp(t, y)
        return sum(y[k]*d[k] for k in range(3))
    maxima = []
    t = mpmath.mpf(0); pas = mpmath.mpf('0.05'); sp = s(t)
    while len(maxima) < 2 and t < 30:
        t2 = t + pas; s2 = s(t2)
        if sp > 0 >= s2:
            maxima.append(float(mpmath.findroot(s, (t, t2), solver='anderson')))
        t, sp = t2, s2
    out['maxima'][str(float(e0)) + '_' + str(int(i0)) + '_' + str(int(w0))] = maxima
    print(e0, i0, w0, maxima)
with open(SORTIE, 'w') as fo:
    json.dump(out, fo, indent=1, ensure_ascii=False)
print(json.dumps({k: out[k] for k in ('i_critique', 'e_max', 't_k', 'maxima')}, indent=1))
