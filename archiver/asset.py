import hashlib
import os


class Asset():
    """
    Class representing a binary resource to be archived.
    """

    def __init__(self, path, batch_root, md5=None):
        self.local_path = path
        self.md5        = md5 or self.calculate_md5()
        self.filename   = os.path.basename(self.local_path)
        self.mtime      = int(os.path.getmtime(self.local_path))
        self.directory  = os.path.dirname(self.local_path)
        self.bytes      = os.path.getsize(self.local_path)
        self.extension  = os.path.splitext(self.filename)[1].lstrip('.').upper()
        self.relpath    = os.path.relpath(self.local_path, batch_root)

    def calculate_md5(self):
        """
        Calclulate and return the object's md5 hash.
        """
        hash = hashlib.md5()
        with open(self.local_path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                else:
                    hash.update(data)
        return hash.hexdigest()
