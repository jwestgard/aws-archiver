class Batch():

    '''Class representing a set of resources to be archived'''

    def __init__(self, mapfile):
        self.mapfile = mapfile
        with open(mapfile) as handle:
            self.contents = []
            for row in handle:
                md5, path = row.strip().split(' ', 1)
                self.contents.append((path, md5))
