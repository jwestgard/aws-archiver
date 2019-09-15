def Batch():

    '''Class representing a set of resources to be archived'''

    def __init__(self, mapfile):
        self.mapfile = mapfile
        with open(mapfile) as handle:
            self.items = []
            for row in handle:
                print(row)