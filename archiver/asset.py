import os

class Asset():

    '''Class representing a binary resource to be archived'''

    def __init__(self, path, md5=None):
        self.path      = path
        self.md5       = md5 or self.generate_md5()
        self.filename  = os.path.basename(self.path)
        self.mtime     = int(os.path.getmtime(path))
        self.directory = os.path.dirname(path)
        self.bytes     = os.path.getsize(path)
        self.extension = os.path.splitext(path)[1].lstrip('.').upper()

    def generate_md5(self):
        with open(self.path, 'rb') as f:
            while True:
                data = f.read(8192)
                if not data:
                    break
                else:
                    hash.update(data)
        return hash.hexdigest()
