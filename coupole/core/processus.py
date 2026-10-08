"""Confinement des processus enfants : sous Windows, un « job object » lie le sort des petits-enfants au processus.

Problème : sous Windows, ``Process.terminate()`` (TerminateProcess) tue un processus de conversion sans rien
transmettre à l'ASTAP qu'il a lancé — aucun signal, pas de groupe de processus.  Après une annulation, ASTAP finissait
seul (jusqu'à 4 minutes).  Sous Linux et macOS, le gestionnaire SIGTERM du processus de conversion tue ASTAP
(``astap.installer_arret_propre``) : rien à changer.

Solution : chaque processus de conversion se place lui-même, à son démarrage, dans un job object
``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`` dont il détient le seul descripteur.  Ses enfants (ASTAP) en héritent.  Quand le
processus meurt — terminé par le pilote, planté, ou fini normalement — le système ferme ses descripteurs, le job se
ferme et **tout** ce qu'il contient est terminé immédiatement.  Aucune coordination avec le pilote, aucun PID à suivre.

Tout est isolé ici, en ``ctypes`` : si l'API refuse (version ancienne, job parent qui interdit l'imbrication), le
repli est silencieux (journal technique) et le comportement reste celui d'avant.
"""
from __future__ import annotations

import logging
import sys

log = logging.getLogger(__name__)

_job: dict = {'handle': None}          # gardé ouvert exprès : sa fermeture tue le job


def disponible() -> bool:
    """Vrai sous Windows (l'API existe) ; ailleurs le confinement n'a pas d'objet."""
    return sys.platform == 'win32'


def est_confine() -> bool:
    return _job['handle'] is not None


def confiner_descendance() -> bool:
    """Place le processus courant (et ses futurs enfants) dans un job « kill on close ».

    Renvoie True si le confinement est en place (ou l'était déjà), False sinon — jamais d'exception.  Sous Linux et
    macOS : False, sans effet (SIGTERM et groupes de processus font le travail).
    """
    if not disponible():
        return False
    if est_confine():
        return True
    handle = None
    k = None
    try:
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in ('ReadOperationCount', 'WriteOperationCount',
                                                           'OtherOperationCount', 'ReadTransferCount',
                                                           'WriteTransferCount', 'OtherTransferCount')]

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                        ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
                        ('LimitFlags', wintypes.DWORD),
                        ('MinimumWorkingSetSize', ctypes.c_size_t),
                        ('MaximumWorkingSetSize', ctypes.c_size_t),
                        ('ActiveProcessLimit', wintypes.DWORD),
                        ('Affinity', ctypes.c_size_t),
                        ('PriorityClass', wintypes.DWORD),
                        ('SchedulingClass', wintypes.DWORD)]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                        ('IoInfo', IO_COUNTERS),
                        ('ProcessMemoryLimit', ctypes.c_size_t),
                        ('JobMemoryLimit', ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t),
                        ('PeakJobMemoryUsed', ctypes.c_size_t)]

        JobObjectExtendedLimitInformation = 9
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000

        k = ctypes.WinDLL('kernel32', use_last_error=True)
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.CreateJobObjectW.argtypes = [wintypes.LPVOID, wintypes.LPCWSTR]
        k.SetInformationJobObject.restype = wintypes.BOOL
        k.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.GetCurrentProcess.argtypes = []
        k.CloseHandle.restype = wintypes.BOOL
        k.CloseHandle.argtypes = [wintypes.HANDLE]

        handle = k.CreateJobObjectW(None, None)          # descripteur non héritable : les enfants ne le tiennent pas
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k.SetInformationJobObject(handle, JobObjectExtendedLimitInformation, ctypes.byref(info),
                                         ctypes.sizeof(info)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not k.AssignProcessToJobObject(handle, k.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
        _job['handle'] = handle
        return True
    except Exception as e:
        # Le processus n'est PAS dans le job (l'assignation a échoué ou n'a pas eu lieu) : fermer le descripteur
        # est donc sans danger.  Comportement inchangé : TerminateProcess seul.
        log.info('job object unavailable, children will not be killed with the process: %s', e)
        if handle and k is not None:
            try:
                k.CloseHandle(handle)
            except Exception:
                pass
        return False
