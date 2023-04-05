import os

from .inventory_manifest import InventoryManifest
from .md5_sum_manifest import Md5SumManifest
from .patsy_db_manifest import PatsyDbManifest
from .single_asset_manifest import SingleAssetManifest
from ..utils import get_first_line


class ManifestFactory:
    @staticmethod
    def create(manifest_filename: str):
        """
        Returns the appropriate Manifest implementation for the given file
        """
        # These headers should be part of the inventory manifest
        inventory_headers = \
            {'BATCH', 'PATH', 'DIRECTORY', 'RELPATH', 'FILENAME', 'EXTENSION', 'BYTES', 'MTIME', 'MODDATE', 'MD5',
             'SHA1', 'SHA256'}

        # These should be in the patsy manifest
        patsy_headers = {'md5', 'filepath', 'relpath'}

        if manifest_filename is None:
            return SingleAssetManifest(os.path.curdir)
        header = get_first_line(manifest_filename)

        if all(h in header for h in patsy_headers):
            return PatsyDbManifest(manifest_filename)
        elif all(h in header for h in inventory_headers):
            return InventoryManifest(manifest_filename)
        else:
            return Md5SumManifest(manifest_filename)
