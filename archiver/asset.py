import hashlib
import os


class Asset():

    '''Class representing a binary resource to be archived'''

    def __init__(self, path, md5=None):
        self.local_path = path
        self.md5        = md5 or self.calculate_md5()
        self.filename   = os.path.basename(self.local_path)
        self.mtime      = int(os.path.getmtime(self.local_path))
        self.directory  = os.path.dirname(self.local_path)
        self.bytes      = os.path.getsize(self.local_path)
        self.extension  = os.path.splitext(self.filename)[1].lstrip('.').upper()


    def calculate_md5(self):
        hash = hashlib.md5()
        with open(self.local_path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                else:
                    hash.update(data)
        return hash.hexdigest()
