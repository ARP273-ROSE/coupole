"""Système de fichiers FUSE « partage réseau simulé » : passe-plat avec une latence fixe par opération
(getattr, open, read, write, readdir, create, rename, unlink, fsync…), comme un aller-retour SMB."""
import errno, os, sys, time, threading
from fuse import FUSE, FuseOSError, Operations

LAT = float(os.environ.get('LATENCE_MS', '2')) / 1000.0
COMPTE = {}
VERROU = threading.Lock()

def attendre(op):
    with VERROU:
        COMPTE[op] = COMPTE.get(op, 0) + 1
    if LAT:
        time.sleep(LAT)

class Passe(Operations):
    def __init__(self, racine):
        self.racine = racine
    def _p(self, p):
        return os.path.join(self.racine, p.lstrip('/'))
    def access(self, p, mode):
        attendre('access')
        if not os.access(self._p(p), mode):
            raise FuseOSError(errno.EACCES)
    def chmod(self, p, mode):
        attendre('chmod'); return os.chmod(self._p(p), mode)
    def chown(self, p, u, g):
        attendre('chown'); return os.chown(self._p(p), u, g)
    def getattr(self, p, fh=None):
        attendre('getattr')
        st = os.lstat(self._p(p))
        return {k: getattr(st, k) for k in ('st_atime', 'st_ctime', 'st_gid', 'st_mode', 'st_mtime', 'st_nlink',
                                             'st_size', 'st_uid')}
    def readdir(self, p, fh):
        attendre('readdir')                 # types transmis (d_type), comme SMB et NTFS : is_dir() sans aller-retour
        out = ['.', '..']
        with os.scandir(self._p(p)) as it:
            for e in it:
                out.append((e.name, {'st_mode': 0o040755 if e.is_dir(follow_symlinks=False) else 0o100644}, 0))
        return out
    def readlink(self, p):
        return os.readlink(self._p(p))
    def mkdir(self, p, mode):
        attendre('mkdir'); return os.mkdir(self._p(p), mode)
    def rmdir(self, p):
        attendre('rmdir'); return os.rmdir(self._p(p))
    def statfs(self, p):
        attendre('statfs')
        s = os.statvfs(self._p(p))
        return {k: getattr(s, k) for k in ('f_bavail', 'f_bfree', 'f_blocks', 'f_bsize', 'f_favail', 'f_ffree',
                                            'f_files', 'f_flag', 'f_frsize', 'f_namemax')}
    def unlink(self, p):
        attendre('unlink'); return os.unlink(self._p(p))
    def rename(self, a, b):
        attendre('rename'); return os.rename(self._p(a), self._p(b))
    def utimens(self, p, times=None):
        attendre('utimens'); return os.utime(self._p(p), times)
    def open(self, p, flags):
        attendre('open'); return os.open(self._p(p), flags)
    def create(self, p, mode, fi=None):
        attendre('create'); return os.open(self._p(p), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    def read(self, p, n, off, fh):
        attendre('read'); return os.pread(fh, n, off)
    def write(self, p, data, off, fh):
        attendre('write'); return os.pwrite(fh, data, off)
    def truncate(self, p, n, fh=None):
        attendre('truncate')
        with open(self._p(p), 'r+') as f:
            f.truncate(n)
    def flush(self, p, fh):
        attendre('flush'); return 0
    def release(self, p, fh):
        return os.close(fh)
    def fsync(self, p, ds, fh):
        attendre('fsync'); return os.fsync(fh)

if __name__ == '__main__':
    src, pt = sys.argv[1], sys.argv[2]
    ro = '--ro' in sys.argv
    FUSE(Passe(src), pt, foreground=True, nothreads=False, ro=ro, allow_other=True, big_writes=True,
         max_read=131072)
