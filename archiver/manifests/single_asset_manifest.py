import os
from .manifest import Manifest


class SingleAssetManifest(Manifest):
    """
    Placeholder manifest for a single asset.
    The asset must be added to the Batch manuall.
    """
    def __init__(self, manifest_filename):
        self.manifest_filename = manifest_filename
        self.manifest_path = os.path.dirname(manifest_filename)

    def load_manifest(self, results_filename, batch):
        """
        Does nothing. Asset must be added to Batch manually
        """
        pass
