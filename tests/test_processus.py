"""Confinement des processus enfants (core/processus.py).

Sous Windows : un processus confiné qui engendre un enfant (``ping -n 60``) est tué par TerminateProcess — comme le
fait ``Process.terminate()`` du pilote à l'annulation — et l'enfant doit mourir avec lui ; témoin : sans confinement,
l'enfant survit (c'est le défaut que le job object corrige).  Ailleurs : l'appel est sans effet et ne lève rien.
"""
import subprocess
import sys
import time

import pytest

from coupole.core import processus

CODE = """
import subprocess, sys, time
from coupole.core import processus
ok = processus.confiner_descendance() if %r else False
p = subprocess.Popen(['ping', '-n', '60', '127.0.0.1'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(ok, p.pid, flush=True)
time.sleep(60)
"""


def _lancer(confiner: bool):
    parent = subprocess.Popen([sys.executable, '-c', CODE % confiner], stdout=subprocess.PIPE, text=True)
    ligne = parent.stdout.readline().split()
    assert len(ligne) == 2, ligne
    return parent, ligne[0] == 'True', int(ligne[1])


def _vivant(pid: int) -> bool:
    import psutil
    try:
        return psutil.Process(pid).status() != psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return False


def _attendre_mort(pid: int, delai: float = 5.0) -> bool:
    fin = time.monotonic() + delai
    while time.monotonic() < fin:
        if not _vivant(pid):
            return True
        time.sleep(0.1)
    return not _vivant(pid)


def _tuer(pid: int):
    import psutil
    try:
        psutil.Process(pid).kill()
    except psutil.NoSuchProcess:
        pass


@pytest.mark.skipif(sys.platform != 'win32', reason='job object : Windows seulement')
def test_job_object_tue_le_petit_fils_avec_le_processus():
    parent, confine, pid = _lancer(True)
    try:
        assert confine, 'le confinement doit réussir sous Windows'
        assert _vivant(pid)
        parent.kill()                                   # TerminateProcess, comme Process.terminate() du pilote
        parent.wait(10)
        assert _attendre_mort(pid), 'l\'enfant (ping) devait mourir avec son parent confiné'
    finally:
        _tuer(pid)
        if parent.poll() is None:
            parent.kill()


@pytest.mark.skipif(sys.platform != 'win32', reason='job object : Windows seulement')
def test_temoin_sans_job_object_le_petit_fils_survit():
    """Prouve que le test ci-dessus mesure bien quelque chose : sans job, TerminateProcess laisse l'enfant vivre."""
    parent, confine, pid = _lancer(False)
    try:
        assert not confine
        parent.kill()
        parent.wait(10)
        time.sleep(1.0)
        assert _vivant(pid), 'sans confinement, ping devait survivre à son parent'
    finally:
        _tuer(pid)
        if parent.poll() is None:
            parent.kill()


@pytest.mark.skipif(sys.platform == 'win32', reason='hors Windows seulement (sous Windows, voir les tests ci-dessus)')
def test_hors_windows_sans_effet_et_sans_exception():
    assert not processus.disponible()
    assert processus.confiner_descendance() is False and not processus.est_confine()
    assert processus.confiner_descendance() is False                  # idempotent, toujours sans exception
