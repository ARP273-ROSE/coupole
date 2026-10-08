"""Génère les icônes PNG, ICO (Windows) et ICNS (macOS) depuis logo/coupole.svg (rendu par Qt, sans Inkscape).

    QT_QPA_PLATFORM=offscreen python logo/generer_icones.py
"""
import sys
from pathlib import Path

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QGuiApplication, QImage, QPainter
from PyQt6.QtSvg import QSvgRenderer

ICI = Path(__file__).resolve().parent
RES = ICI.parent / 'coupole' / 'ressources'


def rendre(taille: int) -> QImage:
    r = QSvgRenderer(str(ICI / 'coupole.svg'))
    im = QImage(taille, taille, QImage.Format.Format_ARGB32)
    im.fill(Qt.GlobalColor.transparent)
    p = QPainter(im)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    r.render(p, QRectF(0, 0, taille, taille))
    p.end()
    return im


def main():
    app = QGuiApplication(sys.argv)  # noqa: F841
    tailles = [16, 24, 32, 48, 64, 128, 256, 512, 1024]
    for t in tailles:
        rendre(t).save(str(ICI / ('coupole_%d.png' % t)))
    for t in (64, 256):
        rendre(t).save(str(RES / ('coupole_%d.png' % t)))
    from PIL import Image
    grand = Image.open(ICI / 'coupole_256.png')
    grand.save(ICI / 'coupole.ico', sizes=[(t, t) for t in (16, 24, 32, 48, 64, 128, 256)])
    Image.open(ICI / 'coupole_1024.png').save(ICI / 'coupole.icns')
    print('icônes écrites dans', ICI)


if __name__ == '__main__':
    main()
