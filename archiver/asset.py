import hashlib
import os


class PathOutOfScopeException(Exception):
    """
    Raised to indicate a local path falls outside the current batch root.
    """
    def __init__(self, path, base_path):
        self.path = path
        self.base_path = base_path

    def __str__(self):
        return f'{self.path} is not contained within {self.base_path}'


class Asset:
    """
    Class representing a binary resource to be archived.
    """

    def __init__(self, path, batch_root, md5=None):
        if not batch_root.endswith('/'):
            batch_root += '/'
        self.local_path = path
        self.md5        = md5 or self.calculate_md5()
        self.filename   = os.path.basename(self.local_path)
        self.mtime      = int(os.path.getmtime(self.local_path))
        self.directory  = os.path.dirname(self.local_path)
        self.bytes      = os.path.getsize(self.local_path)
        self.extension  = os.path.splitext(self.filename)[1].lstrip('.').upper()
        if self.local_path.startswith(batch_root):
            self.relpath = self.local_path[len(batch_root):]
        else:
            raise PathOutOfScopeException(path=self.local_path, base_path=batch_root)

    def calculate_md5(self):
        """
        Calculate and return the object's md5 hash.
        """
        md5sum = hashlib.md5()
        with open(self.local_path, 'rb') as f:
            for data in f:
                md5sum.update(data)
        return md5sum.hexdigest()

    def calculate_etag(self, chunk_size):
        """
        Calculate the AWS etag: either the md5 hash, or for files larger than
        the specified chunk size, the hash of all the chunk hashes concatenated
        together, followed by the number of chunks.
        """
        md5s = []
        with open(self.local_path, 'rb') as handle:
            for data in chunked(handle, chunk_size):
                md5s.append(hashlib.md5(data))

        if len(md5s) == 1:
            return md5s[0].hexdigest()
        else:
            digests = hashlib.md5(b''.join([m.digest() for m in md5s]))
            return f'{digests.hexdigest()}-{len(md5s)}'


def chunked(handle, chunk_size):
    # based on https://stackoverflow.com/a/54989668/5124907
    return iter(lambda: handle.read(chunk_size), b'')
