import os
from .asset import Asset


class Batch():

    '''Class representing a set of resources to be archived'''

    def __init__(self, args):
        print(args)
        if args.mapfile:
            self.mapfile = args.mapfile
            self.contents = self.from_mapfile()
        elif args.asset:
            self.contents = [Asset(path=args.asset)]


    def from_mapfile(self):

        '''Read assets from md5sum-style inventory file'''

        assets = []
        with open(mapfile) as handle:
            lines = [line.strip() for line in handle]

        for line in lines:
            md5, path = line.split(None, 1)
            assets.append(Asset(path, md5))

        return assets