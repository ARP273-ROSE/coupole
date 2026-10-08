#!/bin/sh
# Installation de Coupole avec le Python du système (Linux, macOS).
# Installing Coupole with the system Python (Linux, macOS).
#
#   sh install.sh          (une question : Entrée pour installer / one question: Enter to install)
#   sh install.sh --oui    (sans question / no question)
#
# Ce que fait le script / What the script does:
#   1. trouve un Python >= 3.10 / finds a Python >= 3.10;
#   2. crée un environnement virtuel dans ~/.local/share/coupole/venv (macOS : ~/Library/Application Support/Coupole/venv) ;
#   3. y installe Coupole et toutes ses dépendances (pip) / installs Coupole and all its dependencies;
#   4. crée les lanceurs ~/.local/bin/coupole et coupole-gui, et une entrée de menu (Linux) ou ~/Applications/Coupole.app (macOS).
# Rien n'est écrit hors de votre dossier personnel ; aucun mot de passe administrateur.
set -eu

ICI=$(cd "$(dirname "$0")" && pwd)
OUI=0
[ "${1:-}" = "--oui" ] || [ "${1:-}" = "--yes" ] && OUI=1

case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
  fr*) FR=1 ;;
  *) FR=0 ;;
esac
dire() { if [ "$FR" = 1 ]; then printf '%s\n' "$1"; else printf '%s\n' "$2"; fi; }

SYSTEME=$(uname -s)
if [ "$SYSTEME" = "Darwin" ]; then
  DEST="$HOME/Library/Application Support/Coupole"
else
  DEST="${XDG_DATA_HOME:-$HOME/.local/share}/coupole"
fi
BIN="$HOME/.local/bin"

# ---------------------------------------------------------------- 1. Python >= 3.10
PY=""
for cand in python3.14 python3.13 python3.12 python3.11 python3.10 python3 python; do
  if command -v "$cand" >/dev/null 2>&1; then
    if "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PY=$(command -v "$cand"); break
    fi
  fi
done
if [ -z "$PY" ]; then
  dire "Aucun Python 3.10 ou plus récent n'a été trouvé." "No Python 3.10 or newer was found."
  if [ "$SYSTEME" = "Darwin" ]; then
    dire "Installez-le depuis https://www.python.org/downloads/macos/ (ou : brew install python), puis relancez ce script." \
         "Install it from https://www.python.org/downloads/macos/ (or: brew install python), then run this script again."
  else
    dire "Installez-le avec le gestionnaire de paquets, par exemple :" "Install it with the package manager, for instance:"
    echo "  Debian/Ubuntu : sudo apt install python3 python3-venv"
    echo "  Fedora        : sudo dnf install python3"
    echo "  Arch          : sudo pacman -S python"
    dire "puis relancez ce script. Sans Python : téléchargez le paquet Linux autonome (Releases sur GitHub), qui embarque tout." \
         "then run this script again. Without Python: download the standalone Linux package (GitHub Releases), which bundles everything."
  fi
  exit 1
fi
if ! "$PY" -c 'import venv, ensurepip' 2>/dev/null; then
  dire "Python est là ($PY) mais sans le module venv." "Python is here ($PY) but without the venv module."
  dire "Debian/Ubuntu : sudo apt install python3-venv   — puis relancez ce script." \
       "Debian/Ubuntu: sudo apt install python3-venv   — then run this script again."
  exit 1
fi

dire "Coupole $(cat "$ICI/VERSION") sera installé dans : $DEST" "Coupole $(cat "$ICI/VERSION") will be installed into: $DEST"
dire "Python utilisé : $PY ($("$PY" -c 'import platform; print(platform.python_version())'))" \
     "Python used: $PY ($("$PY" -c 'import platform; print(platform.python_version())'))"
if [ "$OUI" = 0 ]; then
  dire "Appuyez sur Entrée pour installer (Ctrl+C pour annuler)." "Press Enter to install (Ctrl+C to cancel)."
  read -r _ || true
fi

# ---------------------------------------------------------------- 2. et 3. environnement et dépendances
mkdir -p "$DEST"
"$PY" -m venv "$DEST/venv"
"$DEST/venv/bin/python" -m pip install --quiet --upgrade pip
dire "Installation de Coupole et de ses dépendances (PyQt6, numpy, astropy...) : quelques minutes." \
     "Installing Coupole and its dependencies (PyQt6, numpy, astropy...): a few minutes."
"$DEST/venv/bin/python" -m pip install --quiet "$ICI"
"$DEST/venv/bin/coupole" --version >/dev/null

# ---------------------------------------------------------------- 4. lanceurs
mkdir -p "$BIN"
ln -sf "$DEST/venv/bin/coupole" "$BIN/coupole"
ln -sf "$DEST/venv/bin/coupole-gui" "$BIN/coupole-gui"
cp "$ICI/logo/coupole_256.png" "$DEST/coupole.png" 2>/dev/null || true
if [ "$SYSTEME" = "Darwin" ]; then
  APP="$HOME/Applications/Coupole.app"
  mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
  cat > "$APP/Contents/MacOS/Coupole" <<EOF
#!/bin/sh
exec "$DEST/venv/bin/coupole-gui" "\$@"
EOF
  chmod +x "$APP/Contents/MacOS/Coupole"
  cp "$ICI/logo/coupole.icns" "$APP/Contents/Resources/coupole.icns" 2>/dev/null || true
  cat > "$APP/Contents/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>CFBundleName</key><string>Coupole</string>
  <key>CFBundleExecutable</key><string>Coupole</string>
  <key>CFBundleIdentifier</key><string>info.coupole.app</string>
  <key>CFBundleIconFile</key><string>coupole.icns</string>
  <key>CFBundlePackageType</key><string>APPL</string>
</dict></plist>
EOF
  dire "Application : $APP" "Application: $APP"
else
  APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
  mkdir -p "$APPS"
  cat > "$APPS/coupole.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Coupole
Comment=Boite a outils du DU ECU (Observatoire de Paris) / ECU diploma toolbox
Exec="$DEST/venv/bin/coupole-gui"
Icon=$DEST/coupole.png
Terminal=false
Categories=Science;Astronomy;Education;
EOF
  dire "Entrée de menu : $APPS/coupole.desktop" "Menu entry: $APPS/coupole.desktop"
fi

dire "Terminé. Lancer : coupole-gui (interface) ou coupole --help (ligne de commande)." \
     "Done. Start: coupole-gui (interface) or coupole --help (command line)."
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) dire "Ajoutez $BIN à votre PATH, ou lancez $BIN/coupole-gui." "Add $BIN to your PATH, or run $BIN/coupole-gui." ;;
esac
dire "Désinstaller : supprimer $DEST, $BIN/coupole, $BIN/coupole-gui (vos réglages restent dans ~/.config/coupole)." \
     "Uninstall: delete $DEST, $BIN/coupole, $BIN/coupole-gui (your settings stay in ~/.config/coupole)."
