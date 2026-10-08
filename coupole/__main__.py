"""``python -m coupole`` : sans argument, l'interface graphique ; avec arguments, la ligne de commande."""
import sys

from .cli import main

if __name__ == '__main__':
    sys.exit(main())
