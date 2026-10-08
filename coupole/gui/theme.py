"""Apparence propre à Coupole, indépendante des réglages de l'ordinateur.

Le style natif suit le thème du système (mode sombre de Windows 11/macOS, thèmes GTK/KDE) et mélange alors
des couleurs fixées par l'application avec celles du système : texte noir sur fond sombre, info-bulles
illisibles, tableaux sans contraste.  On impose donc partout le même style Qt (« Fusion »), une palette
complète, une feuille de style et une police de taille fixe.  Le thème (clair ou sombre) se choisit dans
les Réglages ; il ne dépend jamais de celui du système.
"""
from __future__ import annotations

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QStyleFactory

ACCENT = '#3F6F9F'                              # bleu ardoise, doux pour les yeux

# Couleurs douces : blanc cassé chaud plutôt que blanc pur, anthracite plutôt que noir, bordures légères.
# Chaque couple texte/fond garde un contraste WCAG ≥ 4,5 (vérifié par tests/test_interface.py).
THEMES = {
    'clair': {
        'fenetre': '#F4F4F0', 'base': '#FBFBF8', 'alterne': '#F1F1EC', 'texte': '#2E333B',
        'texte_doux': '#646C77', 'desactive': '#A4AAB2', 'bouton': '#ECEDE8', 'bordure': '#D8DBD9',
        'selection': ACCENT, 'texte_selection': '#FFFFFF', 'bulle': '#FBF7EC', 'texte_bulle': '#2E333B',
        'lien': ACCENT, 'entete': '#EDEEE9', 'survol': '#E3EAF1',
    },
    'sombre': {
        'fenetre': '#262A31', 'base': '#1F2329', 'alterne': '#2A2E35', 'texte': '#D9DDE2',
        'texte_doux': '#A3ABB6', 'desactive': '#69717C', 'bouton': '#30353E', 'bordure': '#3B414B',
        'selection': '#3E6C99', 'texte_selection': '#FFFFFF', 'bulle': '#30353E', 'texte_bulle': '#D9DDE2',
        'lien': '#8DB4DA', 'entete': '#2C3139', 'survol': '#343C48',
    },
}

# Familles essayées dans l'ordre : la première présente sur le système est prise.  La taille, elle, est
# fixée (en points, donc mise à l'échelle par Qt selon la densité de l'écran) : un réglage de police du
# système ne peut plus rendre l'interface minuscule ou déborder.
FAMILLES = ['Segoe UI', 'SF Pro Text', 'Helvetica Neue', 'Noto Sans', 'Cantarell', 'Ubuntu', 'DejaVu Sans',
            'Arial', 'Liberation Sans']
TAILLE_POINTS = 10


def palette(nom: str) -> QPalette:
    c = {k: QColor(v) for k, v in THEMES.get(nom, THEMES['clair']).items()}
    p = QPalette()
    R, G = QPalette.ColorRole, QPalette.ColorGroup
    for groupe in (G.Active, G.Inactive):
        p.setColor(groupe, R.Window, c['fenetre'])
        p.setColor(groupe, R.WindowText, c['texte'])
        p.setColor(groupe, R.Base, c['base'])
        p.setColor(groupe, R.AlternateBase, c['alterne'])
        p.setColor(groupe, R.Text, c['texte'])
        p.setColor(groupe, R.Button, c['bouton'])
        p.setColor(groupe, R.ButtonText, c['texte'])
        p.setColor(groupe, R.BrightText, QColor('#FF5A4E'))
        p.setColor(groupe, R.Highlight, c['selection'])
        p.setColor(groupe, R.HighlightedText, c['texte_selection'])
        p.setColor(groupe, R.ToolTipBase, c['bulle'])
        p.setColor(groupe, R.ToolTipText, c['texte_bulle'])
        p.setColor(groupe, R.Link, c['lien'])
        p.setColor(groupe, R.LinkVisited, c['lien'])
        p.setColor(groupe, R.PlaceholderText, c['texte_doux'])
        p.setColor(groupe, R.Light, c['base'])
        p.setColor(groupe, R.Midlight, c['alterne'])
        p.setColor(groupe, R.Mid, c['bordure'])
        p.setColor(groupe, R.Dark, c['bordure'])
        p.setColor(groupe, R.Shadow, QColor(0, 0, 0, 90))
    for role in (R.WindowText, R.Text, R.ButtonText, R.PlaceholderText):
        p.setColor(G.Disabled, role, c['desactive'])
    for role, cle in ((R.Window, 'fenetre'), (R.Base, 'fenetre'), (R.Button, 'bouton'),
                      (R.Highlight, 'bordure'), (R.HighlightedText, 'texte')):
        p.setColor(G.Disabled, role, c[cle])
    return p


def feuille_de_style(nom: str) -> str:
    c = THEMES.get(nom, THEMES['clair'])
    return """
QToolTip { color: %(texte_bulle)s; background-color: %(bulle)s; border: 1px solid %(bordure)s; border-radius: 6px; padding: 5px 7px; }
QListWidget#barreModules { background: %(base)s; border: 1px solid %(bordure)s; border-radius: 10px; padding: 4px; }
QListWidget#barreModules::item { padding: 7px 6px; border-radius: 8px; margin: 1px 0; }
QListWidget#barreModules::item:hover:!selected { background: %(survol)s; }
QListWidget#barreModules { outline: 0; show-decoration-selected: 1; }
QListWidget#barreModules::item:selected { background: %(selection)s; color: %(texte_selection)s; border: none; }
QCheckBox::indicator, QRadioButton::indicator { width: 15px; height: 15px; border: 1px solid %(texte_doux)s;
                                               background: %(base)s; }
QCheckBox::indicator { border-radius: 4px; }
QRadioButton::indicator { border-radius: 8px; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background: %(selection)s; border-color: %(selection)s; }
QCheckBox::indicator:hover, QRadioButton::indicator:hover { border-color: %(selection)s; }
QCheckBox:disabled, QRadioButton:disabled { color: %(desactive)s; }
QTabWidget::pane { border: 1px solid %(bordure)s; border-radius: 10px; top: -1px; background: %(fenetre)s; }
QTabBar::tab { padding: 5px 12px; border: 1px solid %(bordure)s; border-bottom: none; background: %(bouton)s;
               color: %(texte)s; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 3px; }
QTabBar::tab:selected { background: %(fenetre)s; font-weight: bold; }
QTabBar::tab:hover:!selected { background: %(survol)s; }
QHeaderView::section { background: %(entete)s; color: %(texte)s; padding: 4px 6px; border: none;
                       border-right: 1px solid %(bordure)s; border-bottom: 1px solid %(bordure)s; }
QTableView, QTreeView, QListView { gridline-color: %(alterne)s; border: 1px solid %(bordure)s; border-radius: 8px; selection-background-color: %(selection)s;
                                   selection-color: %(texte_selection)s; }
QPushButton { padding: 6px 14px; border: 1px solid %(bordure)s; border-radius: 8px; background: %(bouton)s;
              color: %(texte)s; }
QPushButton:hover { background: %(survol)s; }
QPushButton:pressed { background: %(alterne)s; }
QPushButton:default { border: 1px solid %(selection)s; }
QPushButton:disabled { color: %(desactive)s; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QPlainTextEdit, QTextEdit, QTextBrowser {
    border: 1px solid %(bordure)s; border-radius: 7px; padding: 4px 6px; background: %(base)s; color: %(texte)s;
    selection-background-color: %(selection)s; selection-color: %(texte_selection)s; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 1px solid %(selection)s; }
QComboBox QAbstractItemView { background: %(base)s; color: %(texte)s; border: 1px solid %(bordure)s;
                              selection-background-color: %(selection)s; selection-color: %(texte_selection)s; }
QProgressBar { border: 1px solid %(bordure)s; border-radius: 8px; text-align: center; background: %(base)s;
               color: %(texte)s; min-height: 16px; }
QProgressBar::chunk { background: %(selection)s; border-radius: 7px; }
QGroupBox { border: 1px solid %(bordure)s; border-radius: 10px; margin-top: 12px; padding-top: 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: %(texte)s; }
QStatusBar { color: %(texte_doux)s; }
QMenu { background: %(base)s; color: %(texte)s; border: 1px solid %(bordure)s; border-radius: 8px; padding: 4px; }
QMenu::item { padding: 5px 18px; border-radius: 6px; }
QMenu::item:selected { background: %(selection)s; color: %(texte_selection)s; }
QMenuBar::item:selected { background: %(survol)s; color: %(texte)s; }
""" % c


def police() -> QFont:
    f = QFont()
    f.setFamilies(FAMILLES)
    f.setPointSizeF(TAILLE_POINTS)
    return f


def appliquer(app: QApplication | None = None, nom: str | None = None) -> str:
    """Applique le thème `nom` (« clair » ou « sombre ») ; par défaut celui des Réglages.  Rend le nom appliqué."""
    from ..core import config
    app = app or QApplication.instance()
    if app is None:
        return ''
    if nom not in THEMES:
        nom = config.reglages()['apparence']
    if nom not in THEMES:
        nom = 'clair'
    style = QStyleFactory.create('Fusion')
    if style is not None:
        app.setStyle(style)
        app.setProperty('coupole_style', style.name())    # app.style() est enveloppé par la feuille de style
    try:                                        # Qt ≥ 6.8 : ne plus suivre le mode clair/sombre du système
        from PyQt6.QtCore import Qt
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark if nom == 'sombre' else Qt.ColorScheme.Light)
    except Exception:
        pass
    app.setPalette(palette(nom))
    app.setFont(police())
    app.setStyleSheet(feuille_de_style(nom))
    return nom


def couleur(cle: str) -> QColor:
    """Couleur du thème courant (pour les widgets dessinés à la main)."""
    from ..core import config
    nom = config.reglages()['apparence']
    return QColor(THEMES.get(nom, THEMES['clair'])[cle])
