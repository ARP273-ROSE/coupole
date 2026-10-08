"""Textes du module « Ma machine » (FR/EN)."""

TEXTES = {
    'mach_systeme': {'fr': 'Système', 'en': 'System'},
    'mach_processeur': {'fr': 'Processeur', 'en': 'Processor'},
    'mach_coeurs': {'fr': 'Cœurs', 'en': 'Cores'},
    'mach_coeurs_val': {'fr': '{p} physiques, {l} logiques', 'en': '{p} physical, {l} logical'},
    'mach_memoire': {'fr': 'Mémoire', 'en': 'Memory'},
    'mach_memoire_val': {'fr': '{t} Go, dont {d} Go disponibles', 'en': '{t} GB, {d} GB available'},
    'mach_disque': {'fr': 'Disque', 'en': 'Disk'},
    'mach_disque_val': {'fr': '{g} Go libres ({dest})', 'en': '{g} GB free ({dest})'},
    'mach_python': {'fr': 'Python', 'en': 'Python'},
    'mach_gpu': {'fr': 'Carte graphique', 'en': 'Graphics card'},
    'mach_gpu_aucune': {'fr': 'aucune détectée', 'en': 'none detected'},
    'mach_gpu_usage': {'fr': 'Calcul sur carte graphique', 'en': 'GPU computing'},
    'mach_gpu_cupy_oui': {'fr': 'possible (CuPy présent) — pour les modules qui en tirent profit',
                          'en': 'possible (CuPy present) — for modules that benefit from it'},
    'mach_gpu_cupy_non': {'fr': 'non utilisé (CuPy absent ; aucun module actuel n\'en a besoin)',
                          'en': 'not used (CuPy missing; no current module needs it)'},
    'mach_plan': {'fr': 'Parallélisme retenu', 'en': 'Chosen parallelism'},
    'mach_plan_val': {'fr': '{dl} téléchargement(s), {conv} conversion(s) simultanés',
                      'en': '{dl} download(s), {conv} conversion(s) at once'},
    'mach_plan_raison': {'fr': 'Pourquoi', 'en': 'Why'},
    'mach_econome': {'fr': 'Mode économe', 'en': 'Economy mode'},
    'mach_gpu_note': {
        'fr': "La carte graphique est détectée et affichée, mais le module « Banque OHP » ne l'utilise pas : son travail "
              "est limité par le réseau, le disque et la compression Zstandard (processeur). L'API coupole.core.calcul "
              "permet aux modules futurs d'utiliser CuPy (facultatif) quand c'est utile.",
        'en': 'The graphics card is detected and shown, but the « OHP image bank » module does not use it: its work is '
              'bound by the network, the disk and Zstandard compression (processor). The coupole.core.calcul API lets '
              'future modules use CuPy (optional) when it helps.'},
    'mach_titre': {'fr': 'Ma machine', 'en': 'My computer'},
    'mach_rafraichir': {'fr': 'Actualiser', 'en': 'Refresh'},
    'mach_rafraichir_aide': {'fr': 'Relit le matériel, la mémoire disponible et l\'état d\'ASTAP.',
                             'en': 'Read the hardware, the available memory and the ASTAP status again.'},
    'mach_copier': {'fr': 'Copier le diagnostic', 'en': 'Copy the diagnosis'},
    'mach_copier_aide': {'fr': 'Copie le diagnostic dans le presse-papiers (à joindre à une question).',
                         'en': 'Copy the diagnosis to the clipboard (to attach to a question).'},
    'mach_copie_faite': {'fr': 'Diagnostic copié.', 'en': 'Diagnosis copied.'},
    'mach_tableau_aide': {'fr': 'Ce que Coupole détecte de cet ordinateur et ce qu\'il en déduit.',
                          'en': 'What Coupole detects about this computer and what it infers.'},
}
