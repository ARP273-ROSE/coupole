"""Point d'entrée des paquets autonomes (Windows, macOS, Linux) : python/ + app/lancer.py.

Sans argument : interface graphique ; avec arguments : ligne de commande (comme « python -m coupole »).
"""
import multiprocessing
import os
import sys

if __name__ == '__main__':
    multiprocessing.freeze_support()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from coupole.cli import main
    sys.exit(main())
