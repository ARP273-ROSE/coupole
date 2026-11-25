# Vérification SageMath des orbites de halo de l'animation « Les points de Lagrange » (code propre à Coupole).
# Développement du 3e ordre de D. L. Richardson (Celestial Mechanics 22, 241, 1980) recalculé ici (coefficients c_n,
# λ, k, a_ij, b_ij, d_ij, s1, s2, l1, l2 ; repère X = x_L + γx), puis contrôlé de façon indépendante : correction
# différentielle (méthode de Newton sur x0 et vy0, Z0 fixé) d'une vraie orbite périodique du problème restreint
# circulaire en 3D (scipy DOP853, tolérance 1e-12) en partant de l'état de Richardson ; écarts état initial et
# demi-période entre Richardson et l'orbite corrigée.
# Usage : sage outils/verif_anim/halo_verif.sage   (écrit tests/halo_sage.json)
import json, os
ICI = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
SORTIE = os.environ.get('SORTIE', os.path.join(ICI, '..', '..', 'tests', 'halo_sage.json'))
from sage.version import version as VERSION_SAGE
import numpy as np
from math import sqrt, cos, sin, pi
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
def L(mu, point):
    def gx(x):
        dx1, dx2 = x+mu, x-1+mu
        return x - (1-mu)*dx1/abs(dx1)**3 - mu*dx2/abs(dx2)**3
    if point==1: return brentq(gx, -mu+1e-9, 1-mu-1e-9, xtol=1e-15)
    return brentq(gx, 1-mu+1e-9, 2.0, xtol=1e-15)
def rich(mu, point, Az_a, dn=1):
    xl = L(mu, point)
    g = (1-mu-xl) if point==1 else (xl-(1-mu))
    def c(n):
        if point==1: return (mu + (-1)**n*(1-mu)*g**(n+1)/(1-g)**(n+1))/g**3
        return ((-1)**n*mu + (-1)**n*(1-mu)*g**(n+1)/(1+g)**(n+1))/g**3
    c2,c3,c4=c(2),c(3),c(4)
    lam=sqrt((-(c2-2)+sqrt((c2-2)**2+4*(c2-1)*(1+2*c2)))/2)
    k=2*lam/(lam**2+1-c2); D=lam**2-c2
    d1=3*lam**2/k*(k*(6*lam**2-1)-2*lam); d2=8*lam**2/k*(k*(11*lam**2-1)-2*lam)
    a21=3*c3*(k**2-2)/(4*(1+2*c2)); a22=3*c3/(4*(1+2*c2))
    a23=-3*c3*lam/(4*k*d1)*(3*k**3*lam-6*k*(k-lam)+4); a24=-3*c3*lam/(4*k*d1)*(2+3*k*lam)
    b21=-3*c3*lam/(2*d1)*(3*k*lam-4); b22=3*c3*lam/d1; d21=-c3/(2*lam**2)
    a31=-9*lam/(4*d2)*(4*c3*(k*a23-b21)+k*c4*(4+k**2))+(9*lam**2+1-c2)/(2*d2)*(3*c3*(2*a23-k*b21)+c4*(2+3*k**2))
    a32=-1/d2*(9*lam/4*(4*c3*(k*a24-b22)+k*c4)+3/2*(9*lam**2+1-c2)*(c3*(k*b22+d21-2*a24)-c4))
    b31=3/(8*d2)*(8*lam*(3*c3*(k*b21-2*a23)-c4*(2+3*k**2))+(9*lam**2+1+2*c2)*(4*c3*(k*a23-b21)+k*c4*(4+k**2)))
    b32=1/d2*(9*lam*(c3*(k*b22+d21-2*a24)-c4)+3/8*(9*lam**2+1+2*c2)*(4*c3*(k*a24-b22)+k*c4))
    d31=3/(64*lam**2)*(4*c3*a24+c4); d32=3/(64*lam**2)*(4*c3*(a23-d21)+c4*(4+k**2))
    den=2*lam*(lam*(1+k**2)-2*k)
    s1=(3/2*c3*(2*a21*(k**2-2)-a23*(k**2+2)-2*k*b21)-3/8*c4*(3*k**4-8*k**2+8))/den
    s2=(3/2*c3*(2*a22*(k**2-2)+a24*(k**2+2)+2*k*b22+5*d21)+3/8*c4*(12-k**2))/den
    l1=-3/2*c3*(2*a21+a23+5*d21)-3/8*c4*(12-k**2)+2*lam**2*s1
    l2=3/2*c3*(a24-2*a22)+9/8*c4+2*lam**2*s2
    Az=Az_a/g
    Ax=sqrt((-D-l2*Az**2)/l1)
    nu=1+s1*Ax**2+s2*Az**2
    def etat(t1):
        x=a21*Ax**2+a22*Az**2-Ax*cos(t1)+(a23*Ax**2-a24*Az**2)*cos(2*t1)+(a31*Ax**3-a32*Ax*Az**2)*cos(3*t1)
        y=k*Ax*sin(t1)+(b21*Ax**2-b22*Az**2)*sin(2*t1)+(b31*Ax**3-b32*Ax*Az**2)*sin(3*t1)
        z=dn*Az*cos(t1)+dn*d21*Ax*Az*(cos(2*t1)-3)+dn*(d32*Az*Ax**2-d31*Az**3)*cos(3*t1)
        w=lam*nu
        vx=w*(Ax*sin(t1)-2*(a23*Ax**2-a24*Az**2)*sin(2*t1)-3*(a31*Ax**3-a32*Ax*Az**2)*sin(3*t1))
        vy=w*(k*Ax*cos(t1)+2*(b21*Ax**2-b22*Az**2)*cos(2*t1)+3*(b31*Ax**3-b32*Ax*Az**2)*cos(3*t1))
        vz=w*(-dn*Az*sin(t1)-2*dn*d21*Ax*Az*sin(2*t1)-3*dn*(d32*Az*Ax**2-d31*Az**3)*sin(3*t1))
        return np.array([x,y,z,vx,vy,vz])
    return xl, g, Ax, Az, lam, nu, etat
def f(t,s,mu):
    x,y,z,vx,vy,vz=s
    r1=sqrt((x+mu)**2+y*y+z*z); r2=sqrt((x-1+mu)**2+y*y+z*z)
    k1=(1-mu)/r1**3; k2=mu/r2**3
    return [vx,vy,vz, x-k1*(x+mu)-k2*(x-1+mu)+2*vy, y-k1*y-k2*y-2*vx, -k1*z-k2*z]
def croise(S, mu, T):
    def ev(t, s, mu): return s[1]
    ev.direction = 0
    so=solve_ivp(f,(0,0.75*T),S,args=(mu,),rtol=1e-12,atol=1e-14,method='DOP853',events=ev)
    for te, ye in zip(so.t_events[0], so.y_events[0]):
        if te > 0.25*T: return te, ye
    return None, None

SYS = {'soleil_terre': 1/(1 + 328900.56), 'terre_lune': 1/(1 + 81.300568), 'soleil_jupiter': 1/(1 + 1047.348644)}
res = {'sage': VERSION_SAGE, 'cas': []}
for nom, mu in SYS.items():
    for point in (1, 2):
        for delta in (0.01, -0.004):
            xl0 = L(mu, point)
            g0 = (1 - mu - xl0) if point == 1 else (xl0 - (1 - mu))
            # même borne que Coupole : Az ≤ 0,4 γ
            xl, g, Ax, Az, lam, nu, etat = rich(mu, point, min(abs(delta), 0.4*g0), 1 if delta >= 0 else -1)
            T = 2*pi/(lam*nu)
            e = etat(0.0)
            S = np.array([xl + g*e[0], 0.0, g*e[2], 0.0, g*e[4], 0.0]); S0 = S.copy()
            ok = False
            for it in range(30):
                te, ye = croise(S, mu, T)
                F = np.array([ye[3], ye[5]])
                if np.linalg.norm(F) < 1e-11:
                    ok = True; break
                J = np.zeros((2, 2))
                for j, idx in enumerate((0, 4)):
                    Sp = S.copy(); h = 1e-8; Sp[idx] += h
                    te2, ye2 = croise(Sp, mu, T)
                    J[:, j] = (np.array([ye2[3], ye2[5]]) - F)/h
                d = np.linalg.solve(J, -F); S[0] += d[0]; S[4] += d[1]
            assert ok
            res['cas'].append({'systeme': nom, 'point': 'L%d' % point, 'delta': delta, 'gamma': float(g), 'Ax': float(Ax),
                               'Az': float(Az), 'periode': float(T), 'richardson': [float(x) for x in S0[:3]] + [float(g*e[3]), float(S0[4]), float(g*e[5])],
                               'corrige': [float(x) for x in S], 'demi_periode_corrigee': float(te)})
            print(nom, point, delta, 'dx0/Az %.4f  dz %.1e  dvy0/vy0 %.4f  T/2 %.5f / %.5f' % ((S[0]-S0[0])/(g*Az), 0, (S[4]-S0[4])/S0[4], te, T/2))
with open(SORTIE, 'w') as fo:
    json.dump(res, fo, indent=1, default=float)
