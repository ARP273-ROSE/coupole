#!/bin/sh
# Vrai partage SMB pour les essais de la base d'état (0.1.10, docs/AUDIT2_2026-10.md § 10) :
# serveur Samba en conteneur, client cifs du noyau (conteneur privilégié : mount -t cifs, options par défaut).
#   sh outils/audit2/samba/essai.sh            # tests (COUPOLE_TEST_SMB) + essai réel (3 images de (914) Palisana)
#   sh outils/audit2/samba/essai.sh nettoyer   # retire conteneurs, réseau et images
set -e
ICI=$(cd "$(dirname "$0")" && pwd)
DEPOT=$(cd "$ICI/../../.." && pwd)
# depuis un conteneur qui pilote le Docker de l'hôte : chemin du dépôt vu par l'hôte
DEPOT_HOTE=${DEPOT_HOTE:-$DEPOT}
if [ "$1" = nettoyer ]; then
  docker rm -f coupole-smb coupole-smb-client >/dev/null 2>&1 || true
  docker network rm coupole-smb-net >/dev/null 2>&1 || true
  docker rmi coupole-smb-serveur coupole-smb-client >/dev/null 2>&1 || true
  exit 0
fi
docker build -q -t coupole-smb-serveur -f "$ICI/Dockerfile.serveur" "$ICI" >/dev/null
docker build -q -t coupole-smb-client -f "$ICI/Dockerfile.client" "$ICI" >/dev/null
docker network create coupole-smb-net >/dev/null 2>&1 || true
docker run -d --rm --name coupole-smb --network coupole-smb-net coupole-smb-serveur >/dev/null
docker run -d --rm --name coupole-smb-client --privileged --network coupole-smb-net -v "$DEPOT_HOTE":/src:ro \
  coupole-smb-client sleep infinity >/dev/null
sleep 2
docker exec coupole-smb-client sh -c 'mkdir -p /mnt/nas && mount -t cifs //coupole-smb/Astronomie /mnt/nas -o username=kevin,password=secret,uid=3000 && grep cifs /proc/mounts'
docker exec coupole-smb-client sh -c 'mkdir -p /work && cd /src && tar --exclude=./build --exclude=./dist --exclude=.git -cf - . | tar -xf - -C /work'
docker exec -w /work -e QT_QPA_PLATFORM=offscreen -e COUPOLE_TEST_SMB=/mnt/nas coupole-smb-client \
  python -m pytest -q -rs tests/test_base_partagee.py
docker exec -w /work coupole-smb-client python outils/audit2/samba/essai_reel.py
