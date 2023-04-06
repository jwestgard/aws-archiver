
import csv
import os
from .manifest import Manifest


class Md5SumManifest(Manifest):
    """
    Manifest class for "MD5 Sum" manifest files
    """
    def __init__(self, manifest_filename):
        self.manifest_filename = manifest_filename
        self.manifest_path = os.path.dirname(manifest_filename)

    def load_manifest(self, results_filename, batch):
        if os.path.isfile(results_filename):
            with open(results_filename, 'r') as results_file:
                results = csv.DictReader(results_file)
                completed = set((row.get('MD5'), row.get('PATH')) for row in results)
        else:
            completed = set()

        with open(self.manifest_filename) as manifest_file:
            for line in manifest_file:
                if line == '':
                    continue
                else:
                    # using None as delimiter splits on any whitespace
                    md5, path = line.strip().split(None, 1)
                    manifest_row = {'MD5': md5, 'PATH': path}
                    if (md5, path) not in completed:
                        batch.add_asset(path, md5=md5, manifest_row=manifest_row)
