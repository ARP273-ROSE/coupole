# Installation de Coupole avec le Python de Windows / Installing Coupole with the Windows Python.
#
#   Double-cliquer sur install.bat (ou : powershell -ExecutionPolicy Bypass -File install.ps1)
#   Paramètre -Oui : sans question / no question.
#
# 1. trouve un Python >= 3.10 (lanceur « py » ou python.exe) / finds a Python >= 3.10;
# 2. crée un environnement virtuel dans %LOCALAPPDATA%\Programs\CoupolePython ;
# 3. y installe Coupole et toutes ses dépendances / installs Coupole and all its dependencies;
# 4. crée les raccourcis Bureau et menu Démarrer / creates Desktop and Start menu shortcuts.
# Aucun droit administrateur / no administrator rights.
param([switch]$Oui)
$ErrorActionPreference = 'Stop'
$Ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$FR = (Get-UICulture).TwoLetterISOLanguageName -eq 'fr'
function Dire([string]$fr, [string]$en) { if ($FR) { Write-Host $fr } else { Write-Host $en } }

$Dest = Join-Path $env:LOCALAPPDATA 'Programs\CoupolePython'
$Version = (Get-Content (Join-Path $Ici 'VERSION') -Raw).Trim()

# ---------------------------------------------------------------- 1. Python >= 3.10
$Py = $null
$Candidats = @()
if (Get-Command py -ErrorAction SilentlyContinue) {
    foreach ($v in '3.14', '3.13', '3.12', '3.11', '3.10') { $Candidats += ,@('py', "-$v") }
}
foreach ($n in 'python', 'python3') {
    $c = Get-Command $n -ErrorAction SilentlyContinue
    if ($c -and $c.Source -notlike '*WindowsApps*') { $Candidats += ,@($c.Source) }
}
foreach ($cand in $Candidats) {
    try {
        $args_ = @()
        if ($cand.Count -gt 1) { $args_ = $cand[1..($cand.Count - 1)] }
        & $cand[0] @args_ -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $Py = (& $cand[0] @args_ -c 'import sys; print(sys.executable)').Trim()
            break
        }
    } catch { }
}
if (-not $Py) {
    Dire "Aucun Python 3.10 ou plus récent n'a été trouvé." "No Python 3.10 or newer was found."
    Dire "Installez-le depuis https://www.python.org/downloads/windows/ (cocher « Add python.exe to PATH »)," `
         "Install it from https://www.python.org/downloads/windows/ (tick « Add python.exe to PATH »),"
    Dire "ou dans un terminal : winget install Python.Python.3.12 — puis relancez install.bat." `
         "or in a terminal: winget install Python.Python.3.12 — then run install.bat again."
    Dire "Sans Python : l'installeur Coupole-Setup.exe (Releases sur GitHub) embarque tout." `
         "Without Python: the Coupole-Setup.exe installer (GitHub Releases) bundles everything."
    exit 1
}

Dire "Coupole $Version sera installé dans : $Dest" "Coupole $Version will be installed into: $Dest"
Dire "Python utilisé : $Py" "Python used: $Py"
if (-not $Oui) {
    Dire "Appuyez sur Entrée pour installer (Ctrl+C pour annuler)." "Press Enter to install (Ctrl+C to cancel)."
    [void](Read-Host)
}

# ---------------------------------------------------------------- 2. et 3. environnement et dépendances
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
& $Py -m venv (Join-Path $Dest 'venv')
if ($LASTEXITCODE -ne 0) { Dire "Échec de la création de l'environnement." "Could not create the environment."; exit 1 }
$VPy = Join-Path $Dest 'venv\Scripts\python.exe'
& $VPy -m pip install --quiet --upgrade pip
Dire "Installation de Coupole et de ses dépendances (PyQt6, numpy, astropy...) : quelques minutes." `
     "Installing Coupole and its dependencies (PyQt6, numpy, astropy...): a few minutes."
& $VPy -m pip install --quiet $Ici
if ($LASTEXITCODE -ne 0) { Dire "Échec de l'installation (voir les messages ci-dessus)." "Installation failed (see the messages above)."; exit 1 }

# ---------------------------------------------------------------- 4. raccourcis
$Gui = Join-Path $Dest 'venv\Scripts\coupole-gui.exe'
$Ico = Join-Path $Dest 'coupole.ico'
Copy-Item (Join-Path $Ici 'coupole.ico') $Ico -Force -ErrorAction SilentlyContinue
$Shell = New-Object -ComObject WScript.Shell
foreach ($Dossier in @([Environment]::GetFolderPath('Desktop'), (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs'))) {
    $L = $Shell.CreateShortcut((Join-Path $Dossier 'Coupole.lnk'))
    $L.TargetPath = $Gui
    $L.WorkingDirectory = $env:USERPROFILE
    $L.IconLocation = $Ico
    $L.Description = 'Coupole'
    $L.Save()
}
Dire "Terminé : raccourcis « Coupole » sur le Bureau et dans le menu Démarrer." "Done: « Coupole » shortcuts on the Desktop and in the Start menu."
Dire "Ligne de commande : $Dest\venv\Scripts\coupole.exe --help" "Command line: $Dest\venv\Scripts\coupole.exe --help"
Dire "Désinstaller : supprimer $Dest et les deux raccourcis (vos réglages restent dans %LOCALAPPDATA%\Coupole)." `
     "Uninstall: delete $Dest and both shortcuts (your settings stay in %LOCALAPPDATA%\Coupole)."
