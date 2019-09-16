import os

class Batch():

    '''Class representing a set of resources to be archived'''

    def __init__(self, mapfile):
        self.mapfile = mapfile
        self.skips, self.contents = self.read_mapfile()

    def read_mapfile(self):
        assets = []
        skips = []
        with open(self.mapfile) as handle:
            lines = [line.strip() for line in handle]
        for line in lines:
            md5, path = line.split(None, 1)
            if os.path.basename(path).startswith('.'):
                skips.append(path)
            elif not os.path.exists(path):
                skips.append(path)
            else:
                assets.append((path, md5))
        return skips, assets
