"""Détection de la machine : système, processeur, mémoire, disque, carte graphique.

Aucune dépendance obligatoire : chaque système est interrogé par ses moyens
propres (/proc et /sys sous Linux, sysctl et system_profiler sous macOS,
API Win32 et PowerShell/CIM sous Windows).  psutil est utilisé s'il est là.
Toute sonde qui échoue rend « inconnu », jamais une exception.
"""
from __future__ import annotations

import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

_SANS_CONSOLE = getattr(subprocess, 'CREATE_NO_WINDOW', 0)


def _cmd(args, timeout=6) -> str:
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                           creationflags=_SANS_CONSOLE)
        return r.stdout if r.returncode == 0 else ''
    except Exception:
        return ''


@dataclass
class CarteGraphique:
    nom: str
    fabricant: str            # NVIDIA, AMD, Intel, Apple, autre
    memoire_mo: int = 0
    source: str = ''          # comment elle a été vue


@dataclass
class Machine:
    systeme: str              # Windows, Darwin, Linux
    version_systeme: str
    architecture: str         # x86_64, arm64...
    processeur: str
    coeurs_physiques: int
    coeurs_logiques: int
    memoire_totale_mo: int
    memoire_disponible_mo: int
    python: str
    cartes: list = field(default_factory=list)

    @property
    def nom_systeme(self) -> str:
        return {'Darwin': 'macOS'}.get(self.systeme, self.systeme)

    def en_dict(self) -> dict:
        d = asdict(self)
        d['nom_systeme'] = self.nom_systeme
        return d


# ---------------------------------------------------------------- processeur
def _nom_processeur() -> str:
    s = platform.system()
    if s == 'Linux':
        try:
            for ligne in Path('/proc/cpuinfo').read_text(errors='replace').splitlines():
                if ligne.lower().startswith(('model name', 'hardware', 'cpu model')):
                    return ligne.split(':', 1)[1].strip()
        except OSError:
            pass
    elif s == 'Darwin':
        n = _cmd(['sysctl', '-n', 'machdep.cpu.brand_string']).strip()
        if n:
            return n
    elif s == 'Windows':
        n = _cmd(['powershell', '-NoProfile', '-Command',
                  '(Get-CimInstance Win32_Processor | Select-Object -First 1).Name']).strip()
        if n:
            return n
    return platform.processor() or platform.machine() or '?'


def _coeurs() -> tuple[int, int]:
    logiques = os.cpu_count() or 1
    try:
        import psutil  # type: ignore
        p = psutil.cpu_count(logical=False)
        if p:
            return p, logiques
    except Exception:
        pass
    s = platform.system()
    phys = 0
    if s == 'Linux':
        try:
            paires = set()
            phys_id = core_id = None
            for ligne in Path('/proc/cpuinfo').read_text(errors='replace').splitlines():
                if ligne.startswith('physical id'):
                    phys_id = ligne.split(':')[1].strip()
                elif ligne.startswith('core id'):
                    core_id = ligne.split(':')[1].strip()
                elif not ligne.strip():
                    if core_id is not None:
                        paires.add((phys_id, core_id))
                    phys_id = core_id = None
            if core_id is not None:
                paires.add((phys_id, core_id))
            phys = len(paires)
        except OSError:
            pass
    elif s == 'Darwin':
        try:
            phys = int(_cmd(['sysctl', '-n', 'hw.physicalcpu']).strip() or 0)
        except ValueError:
            phys = 0
    elif s == 'Windows':
        try:
            phys = int(_cmd(['powershell', '-NoProfile', '-Command',
                             '(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum'
                             ]).strip() or 0)
        except ValueError:
            phys = 0
    # Conteneur ou machine virtuelle limitée : on ne dépasse jamais les logiques visibles.
    if not phys or phys > logiques:
        phys = logiques
    return phys, logiques


def _coeurs_utilisables() -> int:
    """Cœurs réellement accordés au processus (affinité, quota de conteneur)."""
    n = os.cpu_count() or 1
    try:
        n = len(os.sched_getaffinity(0))  # type: ignore[attr-defined]
    except Exception:
        pass
    try:  # quota cgroup v2 (Docker --cpus)
        q = Path('/sys/fs/cgroup/cpu.max').read_text().split()
        if q and q[0] != 'max':
            n = max(1, min(n, int(int(q[0]) / int(q[1]))))
    except Exception:
        pass
    return n


# ---------------------------------------------------------------- mémoire
def _memoire() -> tuple[int, int]:
    """(totale, disponible) en Mo ; (0, 0) si inconnu."""
    try:
        import psutil  # type: ignore
        v = psutil.virtual_memory()
        return int(v.total / 2**20), int(v.available / 2**20)
    except Exception:
        pass
    s = platform.system()
    try:
        if s == 'Linux':
            info = {}
            for ligne in Path('/proc/meminfo').read_text().splitlines():
                k, v = ligne.split(':', 1)
                info[k] = int(v.split()[0])
            tot = info.get('MemTotal', 0) // 1024
            dispo = info.get('MemAvailable', info.get('MemFree', 0)) // 1024
            return tot, dispo
        if s == 'Windows':
            import ctypes

            class _Etat(ctypes.Structure):
                _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                            ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                            ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                            ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                            ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
            e = _Etat()
            e.dwLength = ctypes.sizeof(_Etat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(e))  # type: ignore[attr-defined]
            return int(e.ullTotalPhys / 2**20), int(e.ullAvailPhys / 2**20)
        if s == 'Darwin':
            tot = int(_cmd(['sysctl', '-n', 'hw.memsize']).strip() or 0) // 2**20
            vm = _cmd(['vm_stat'])
            page = int(re.search(r'page size of (\d+)', vm).group(1)) if 'page size' in vm else 4096
            libres = 0
            for cle in ('Pages free', 'Pages inactive', 'Pages speculative', 'Pages purgeable'):
                m = re.search(cle + r':\s+(\d+)', vm)
                if m:
                    libres += int(m.group(1))
            return tot, (libres * page) // 2**20 or tot // 2
    except Exception:
        pass
    return 0, 0


def memoire_disponible_mo() -> int:
    return _memoire()[1]


# ---------------------------------------------------------------- disque
def disque_libre_go(chemin) -> float:
    """Place libre (Go) sur le volume qui contiendra `chemin` (même s'il n'existe pas encore)."""
    p = Path(chemin).expanduser().absolute()
    while not p.exists() and p != p.parent:
        p = p.parent
    try:
        return shutil.disk_usage(str(p)).free / 1e9
    except OSError:
        return 0.0


# ---------------------------------------------------------------- carte graphique
_VENDEURS = {'0x10de': 'NVIDIA', '0x1002': 'AMD', '0x1022': 'AMD', '0x8086': 'Intel', '0x106b': 'Apple'}


def _fabricant(nom: str) -> str:
    n = nom.lower()
    for mot, fab in (('nvidia', 'NVIDIA'), ('geforce', 'NVIDIA'), ('quadro', 'NVIDIA'), ('tesla', 'NVIDIA'),
                     ('radeon', 'AMD'), ('amd', 'AMD'), ('ati ', 'AMD'), ('intel', 'Intel'),
                     ('apple', 'Apple'), ('m1', 'Apple'), ('m2', 'Apple'), ('m3', 'Apple'), ('m4', 'Apple')):
        if mot in n:
            return fab
    return 'autre'


def _cartes() -> list[CarteGraphique]:
    cartes: list[CarteGraphique] = []
    # NVIDIA : nvidia-smi existe sur les trois systèmes quand le pilote est installé.
    if shutil.which('nvidia-smi'):
        for ligne in _cmd(['nvidia-smi', '--query-gpu=name,memory.total',
                           '--format=csv,noheader,nounits']).splitlines():
            if ',' in ligne:
                nom, mem = ligne.rsplit(',', 1)
                try:
                    m = int(float(mem.strip()))
                except ValueError:
                    m = 0
                cartes.append(CarteGraphique(nom.strip(), 'NVIDIA', m, 'nvidia-smi'))
    s = platform.system()
    if s == 'Linux':
        vus = {c.fabricant for c in cartes}
        for carte in sorted(Path('/sys/class/drm').glob('card[0-9]*')):
            if '-' in carte.name:
                continue
            try:
                vendeur = (carte / 'device' / 'vendor').read_text().strip().lower()
            except OSError:
                continue
            fab = _VENDEURS.get(vendeur, 'autre')
            if fab in vus:
                continue
            nom = fab
            try:
                uevent = (carte / 'device' / 'uevent').read_text()
                m = re.search(r'DRIVER=(\S+)', uevent)
                if m:
                    nom = '%s (%s)' % (fab, m.group(1))
            except OSError:
                pass
            mem = 0
            try:
                mem = int((carte / 'device' / 'mem_info_vram_total').read_text()) // 2**20
            except (OSError, ValueError):
                pass
            cartes.append(CarteGraphique(nom, fab, mem, '/sys/class/drm'))
            vus.add(fab)
        if shutil.which('rocm-smi') and not any(c.fabricant == 'AMD' for c in cartes):
            if _cmd(['rocm-smi', '--showproductname']).strip():
                cartes.append(CarteGraphique('AMD (ROCm)', 'AMD', 0, 'rocm-smi'))
    elif s == 'Darwin':
        txt = _cmd(['system_profiler', 'SPDisplaysDataType', '-json'], timeout=15)
        try:
            for c in json.loads(txt).get('SPDisplaysDataType', []):
                nom = c.get('sppci_model') or c.get('_name') or '?'
                if any(x.nom == nom for x in cartes):
                    continue
                mem = c.get('spdisplays_vram') or c.get('spdisplays_vram_shared') or ''
                m = re.match(r'(\d+)\s*(GB|MB)', mem)
                mo = int(m.group(1)) * (1024 if m and m.group(2) == 'GB' else 1) if m else 0
                cartes.append(CarteGraphique(nom, _fabricant(nom), mo, 'system_profiler'))
        except (ValueError, AttributeError):
            pass
    elif s == 'Windows':
        txt = _cmd(['powershell', '-NoProfile', '-Command',
                    'Get-CimInstance Win32_VideoController | Select-Object Name,AdapterRAM | ConvertTo-Json'],
                   timeout=15)
        try:
            data = json.loads(txt) if txt.strip() else []
            if isinstance(data, dict):
                data = [data]
            for c in data:
                nom = (c.get('Name') or '?').strip()
                if any(x.nom == nom for x in cartes):
                    continue
                mem = c.get('AdapterRAM') or 0
                cartes.append(CarteGraphique(nom, _fabricant(nom), int(mem) // 2**20 if mem else 0, 'CIM'))
        except (ValueError, TypeError):
            pass
    return cartes


_cache: Machine | None = None


def detecter(rafraichir: bool = False) -> Machine:
    global _cache
    if _cache is not None and not rafraichir:
        _cache.memoire_disponible_mo = memoire_disponible_mo() or _cache.memoire_disponible_mo
        return _cache
    phys, log_ = _coeurs()
    tot, dispo = _memoire()
    m = Machine(
        systeme=platform.system() or sys.platform,
        version_systeme=platform.release() + (' ' + platform.mac_ver()[0] if sys.platform == 'darwin' else ''),
        architecture=_architecture(),
        processeur=_nom_processeur(),
        coeurs_physiques=min(phys, _coeurs_utilisables()) or 1,
        coeurs_logiques=min(log_, _coeurs_utilisables()) or 1,
        memoire_totale_mo=tot,
        memoire_disponible_mo=dispo,
        python=platform.python_version(),
        cartes=_cartes(),
    )
    _cache = m
    return m


def _architecture() -> str:
    a = platform.machine().lower()
    return {'amd64': 'x86_64', 'x64': 'x86_64', 'aarch64': 'arm64', 'armv8': 'arm64'}.get(a, a or '?')
