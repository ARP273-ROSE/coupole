"""Garde-fou (0.1.12) : le dépôt est public — aucune donnée personnelle dans ses fichiers.

Parcourt TOUS les fichiers suivis par git (à défaut, toute l'arborescence hors build/dist) : fichiers texte, texte
extrait des PDF (pdftotext), contenu décompressé des .gz, blocs texte des PNG, chaînes des autres fichiers binaires.
Les motifs viennent de l'infrastructure et de la vie de l'auteur ; la liste blanche est explicite (`PERMIS`).
Les captures du manuel sont produites dans un dossier personnel neutre (`outils/captures.py`, vérifié ici)."""
import gzip
import os
import re
import shutil
import subprocess
import zlib
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[1]
CE_FICHIER = Path(__file__).resolve()

MOTIFS = [
    r'(?i)kevin', r'\b[Ss]ophie\b', r'(?i)cyrille', r'(?i)kguion', r'(?i)altesch', r'(?i)@gmail\.com',
    r'(?i)orly\.tour', r'(?i)gypaete', r'(?i)alert[-_ ]?bay', r'(?i)fakarava', r'(?i)mauna ?kea', r'(?i)manjaro-de',
    r'/mnt/nas\b', r'/mnt/zpool2', r'/mnt/apps_pool', r'/workspace\b', r'(?<![\w.])/root/',
    r'/home/(?!(?:x|user|utilisateur|runner|astro)\b)[A-Za-z0-9_.-]+',
    r'(?i)C:\\{1,2}Users\\{1,2}(?!(?:x|Public|runneradmin)\b)\w+',
    r'(?i)compi[eè]gne', r'(?i)air ?france', r'\bPNT\b', r'(?i)ryzen 5 8500', r'(?i)\bASI ?6200',
    r'(?i)\bfc-?76', r'\bFSQ\b', r'(?i)2600 ?mc', r'(?i)\bclaude\b', r'(?i)patagonie', r'(?i)truenas', r'(?i)8500G',
]
# liste blanche explicite : (motif, texte exact admis) — SOPHIE en capitales est le spectrographe de l'OHP (motif
# sensible à la casse), le collecteur de rapports et le compte GitHub sont publics.
PERMIS = {'fenice.giff.re', 'ARP273-ROSE'}
EXCLUS = {'build', 'dist', '.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}
RE = [re.compile(m) for m in MOTIFS]


def fichiers_du_depot():
    try:
        r = subprocess.run(['git', 'ls-files', '-z'], cwd=RACINE, capture_output=True, timeout=30)
        if r.returncode == 0 and r.stdout:
            return [RACINE / f for f in r.stdout.decode('utf-8').split('\0') if f]
    except (OSError, subprocess.SubprocessError):
        pass
    out = []
    for d, sous, noms in os.walk(RACINE):
        sous[:] = [s for s in sous if s not in EXCLUS and not s.endswith('.egg-info')]
        out += [Path(d) / n for n in noms if not n.endswith(('.tar.gz', '.deb', '.zip', '.pyc'))]
    return out


def chercher(texte: str):
    return [m.group(0) for r in RE for m in r.finditer(texte) if m.group(0) not in PERMIS]


def textes_png(donnees: bytes) -> str:
    """Blocs tEXt / zTXt / iTXt d'un PNG (logiciel, commentaire, chemin…)."""
    out, i = [], 8
    while i + 8 <= len(donnees):
        n = int.from_bytes(donnees[i:i + 4], 'big')
        genre = donnees[i + 4:i + 8]
        corps = donnees[i + 8:i + 8 + n]
        if genre == b'tEXt':
            out.append(corps.decode('latin-1'))
        elif genre == b'zTXt':
            k = corps.find(b'\0')
            out.append(corps[:k].decode('latin-1') + ' ' + zlib.decompress(corps[k + 2:]).decode('latin-1', 'replace'))
        elif genre == b'iTXt':
            out.append(corps.decode('utf-8', 'replace'))
        i += 12 + n
    return '\n'.join(out)


def contenu(p: Path) -> str:
    donnees = p.read_bytes()
    nom = p.name.lower()
    if nom.endswith('.pdf'):
        if not shutil.which('pdftotext'):
            pytest.skip('pdftotext absent (poppler-utils) : PDF non vérifiables ici')
        r = subprocess.run(['pdftotext', '-q', str(p), '-'], capture_output=True, timeout=120)
        texte = r.stdout.decode('utf-8', 'replace')
        if shutil.which('pdfinfo'):                                   # métadonnées (auteur, créateur, titre…)
            texte += subprocess.run(['pdfinfo', str(p)], capture_output=True, timeout=60).stdout.decode('utf-8', 'replace')
        return texte
    if nom.endswith('.gz'):
        return gzip.decompress(donnees).decode('utf-8', 'replace')
    if nom.endswith('.png'):
        return textes_png(donnees)
    if b'\0' not in donnees[:8192]:
        try:
            return donnees.decode('utf-8')
        except UnicodeDecodeError:
            pass
    # binaire : chaînes intégrées (suites d'au moins 6 caractères imprimables, comme `strings`)
    return '\n'.join(m.decode('ascii') for m in re.findall(rb'[\x20-\x7e]{6,}', donnees))


def test_motifs_detectes():
    """Le garde-fou sait reconnaître ce qu'il cherche (et laisse passer la liste blanche)."""
    for x in ('Retour de Kevin', '/mnt/nas/X', '/home/jdupont/a', 'C:\\Users\\jdupont\\a', '/workspace/GitHub',
              'Ryzen 5 8500G', 'ASI 6200MM', 'FLAT FSQ', 'master 2600mc', 'Sophie'):
        assert chercher(x), x
    for x in ('T193 SOPHIE', '/home/x/OHP_DU_ECU', 'C:\\Users\\x\\OHP', '/mnt/partage/OHP_DU_ECU',
              'https://fenice.giff.re/rapports/collecte.php', 'ARP273-ROSE', '/srv/ancien/OHP_DU_ECU'):
        assert not chercher(x), x


def test_aucune_donnee_personnelle_dans_le_depot():
    fautes = []
    vus = 0
    for p in fichiers_du_depot():
        if p.resolve() == CE_FICHIER or not p.is_file():
            continue
        vus += 1
        for t in sorted(set(chercher(contenu(p)))):
            fautes.append('%s : %r' % (p.relative_to(RACINE), t))
    assert vus > 100
    assert not fautes, 'données personnelles :\n' + '\n'.join(fautes[:80])


def test_captures_dans_un_dossier_neutre():
    """Les captures du manuel sont faites avec un dossier personnel neutre (aucun chemin réel dans les champs)."""
    texte = (RACINE / 'outils' / 'captures.py').read_text(encoding='utf-8')
    assert "DOSSIER_NEUTRE" in texte and "os.environ['HOME'] = DOSSIER_NEUTRE" in texte
    assert 'machine_neutre()' in texte                  # ni noyau ni modèle de processeur de la machine de capture
