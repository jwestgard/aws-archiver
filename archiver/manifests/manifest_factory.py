import os
from .inventory_manifest import InventoryManifest
from .md5_sum_manifest import Md5SumManifest
from .patsy_db_manifest import PatsyDbManifest
from .single_asset_manifest import SingleAssetManifest


class ManifestFactory:
    @staticmethod
    def create(manifest_filename):
        """
        Returns the appropriate Manifest implementation for the given file
        """
        if manifest_filename is None:
            return SingleAssetManifest(os.path.curdir)
        with open(manifest_filename) as manifest_file:
            # Read the first line
            line = manifest_file.readline().strip()

            if line == "md5,filepath,relpath":
                return PatsyDbManifest(manifest_filename)
            elif line == "BATCH,PATH,DIRECTORY,RELPATH,FILENAME,EXTENSION,BYTES,MTIME,MODDATE,MD5,SHA1,SHA256":
                return InventoryManifest(manifest_filename)
            else:

                return Md5SumManifest(manifest_filename)
