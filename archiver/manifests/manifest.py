import abc


class Manifest(metaclass=abc.ABCMeta):
    """
    An interface for manifests.
    """
    @abc.abstractmethod
    def batch_name(self):
        """
        Returns the batch name associated with the manifest, or None if the
        batch name is not specified by the manifest
        """
        return None

    @abc.abstractmethod
    def load_manifest(self, results_filename, batch):
        """
        Loads the assets from the manifest into the given batch. If
        results_filename is provided, the file will be parsed and assets
        listed in the file will not be added to the batch
        """
        raise NotImplementedError
