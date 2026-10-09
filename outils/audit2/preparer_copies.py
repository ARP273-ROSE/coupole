"""Prépare deux copies de la destination (locale et « réseau ») : etat.sqlite réécrit, INDEX_LOTS.csv, et
7 625 fichiers vides aux emplacements « final » (pour ranger / réorganiser sans toucher à la banque)."""
import json, os, shutil, sqlite3, sys
ANCIEN = '/workspace/Workspace/OHP_DU_ECU'
def preparer(phys, vue):
    if os.path.exists(phys):
        shutil.rmtree(phys)
    os.makedirs(phys + '/_traitement')
    shutil.copy('/travail/copie/INDEX_LOTS.csv', phys)
    shutil.copy('/travail/copie/_traitement/journal.csv', phys + '/_traitement')
    src = sqlite3.connect('file:/travail/copie/_traitement/etat.sqlite?mode=ro', uri=True)
    dst = sqlite3.connect(phys + '/_traitement/etat.sqlite')
    dst.execute('CREATE TABLE images (id TEXT PRIMARY KEY, url TEXT, statut TEXT, essais INTEGER DEFAULT 0, info TEXT, maj TEXT)')
    dst.execute('CREATE TABLE empreintes (sha TEXT PRIMARY KEY, id TEXT)')
    dst.execute('CREATE TABLE meta (cle TEXT PRIMARY KEY, valeur TEXT)')
    dst.execute("INSERT INTO meta VALUES ('langue','fr'),('format','xisf')")
    n = 0
    for i, url, st, ess, info, maj in src.execute('SELECT * FROM images'):
        d = json.loads(info) if info else {}
        for k in ('final', 'staging'):
            if d.get(k):
                d[k] = d[k].replace(ANCIEN, vue)
        if st == 'ok' and d.get('final'):
            p = d['final'].replace(vue, phys)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').close()
            n += 1
        if d.get('sha_pixels'):
            dst.execute('INSERT OR IGNORE INTO empreintes VALUES (?,?)', (d['sha_pixels'], i))
        dst.execute('INSERT INTO images VALUES (?,?,?,?,?,?)', (i, url, st, ess, json.dumps(d, ensure_ascii=False), maj))
    dst.commit()
    print(phys, n, 'fichiers')
preparer('/travail/copie_locale', '/travail/copie_locale')
preparer('/travail/reseau_src/copie', '/mnt/reseau/copie')
