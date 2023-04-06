import csv
import os
from .manifest import Manifest


class InventoryManifest(Manifest):
    """
    Manifest class for Preserve "inventory" manifest files
    """
    def __init__(self, manifest_filename):
        self.manifest_filename = manifest_filename
        self.manifest_path = os.path.dirname(manifest_filename)

    def load_manifest(self, results_filename, batch, etag_exists=False):
        if os.path.isfile(results_filename):
            with open(results_filename, 'r') as results_file:
                results = csv.DictReader(results_file)
                completed = set((row.get('MD5'), row.get('PATH')) for row in results)
        else:
            completed = set()

        with open(self.manifest_filename) as manifest_file:
            reader = csv.DictReader(manifest_file, delimiter=',')
            for row in reader:
                etag = row['ETAG'] if etag_exists else None
                md5 = row['MD5']
                path = row['PATH']
                relpath = row['RELPATH']
                batch_name = row['BATCH']
                if (md5, path) not in completed:
                    batch.add_asset(path, batch_name=batch_name, md5=md5, relpath=relpath, manifest_row=row, etag=etag)
