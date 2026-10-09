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
    'mach_gpu_usage_val': {'fr': "Aucune fonction de Coupole n'utilise la carte graphique pour l'instant : rien à installer. "
                                 "Les modules futurs qui en auront besoin l'indiqueront.",
                           'en': 'No Coupole function uses the graphics card for now: nothing to install. Future modules '
                                 'that need it will say so.'},
    'mach_gpu_usage_pret': {'fr': "Aucune fonction de Coupole n'utilise la carte graphique pour l'instant ; la bibliothèque "
                                  "de calcul est présente, les modules futurs qui en auront besoin pourront s'en servir.",
                            'en': 'No Coupole function uses the graphics card for now; the computing library is present, '
                                  'future modules that need it will be able to use it.'},
    'mach_gpu_usage_aide': {'fr': 'Pour les développeurs de modules : extra coupole[gpu] = cupy-cuda12x, NVIDIA + CUDA 12 '
                                  'requis, installation pip uniquement, non inclus dans les paquets autonomes.',
                            'en': 'For module developers: coupole[gpu] extra = cupy-cuda12x, NVIDIA + CUDA 12 required, '
                                  'pip installation only, not included in the standalone packages.'},
    'mach_gpu_val_aide': {'fr': 'Carte détectée (nom, fabricant, mémoire quand elle est connue).',
                          'en': 'Detected card (name, maker, memory when known).'},
    'mach_plan': {'fr': 'Parallélisme retenu', 'en': 'Chosen parallelism'},
    'mach_plan_val': {'fr': '{dl} téléchargement(s), {conv} conversion(s) simultanés',
                      'en': '{dl} download(s), {conv} conversion(s) at once'},
    'mach_plan_raison': {'fr': 'Pourquoi', 'en': 'Why'},
    'mach_econome': {'fr': 'Mode économe', 'en': 'Economy mode'},
    'mach_gpu_note': {
        'fr': "La carte graphique est détectée et affichée pour information. Aucune fonction de Coupole ne l'utilise pour "
              "l'instant : le travail de la Banque OHP est limité par le réseau, le disque et la compression (processeur). "
              "Rien à installer ; les modules futurs qui en auront besoin l'indiqueront.",
        'en': 'The graphics card is detected and shown for information. No Coupole function uses it for now: the OHP '
              'bank work is bound by the network, the disk and compression (processor). Nothing to install; future '
              'modules that need it will say so.'},
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
