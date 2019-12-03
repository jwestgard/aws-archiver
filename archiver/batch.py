from boto3.s3.transfer import TransferConfig
import os
from .asset import Asset


def calculate_chunk_bytes(chunk_string):
    """
    Return the chunk size in bytes after converting the human-readable chunk size specification.
    """
    if chunk_string.endswith('MB'):
        return int(chunk_string[:-2]) * (1024**2)
    elif chunk_string.endswith('GB'):
        return int(chunk_string[:-2]) * (1024**3)
    else:
        raise ConfigException


class Batch():
    """
    Class representing a set of resources to be archived,
    and an AWS configuration where they will be archived.
    """

    def __init__(self, args):
        """Set up a batch of assets to be loaded with the supplied args."""
        self.name = args.name
        self.chunk_bytes = calculate_chunk_bytes(args.chunk)
        self.bucket = args.bucket
        self.storage_class = args.storage

        self.logdir = args.logs
        if not os.path.isdir(self.logdir):
            os.mkdir(self.logdir)

        self.max_threads = args.threads
        if self.max_threads == 1:
            self.use_threads = False
        else:
            self.use_threads = True

        # Read assets information from an md5sum-style listing
        if args.mapfile:
            self.contents = []
            with open(args.mapfile) as handle:
                for line in handle:
                    # passing None as delimiter splits on any amount of whitespace
                    md5, path = line.strip().split(None, 1)
                    self.contents.append(Asset(path, md5))

        # Otherwise process a single asset path passed as an argument
        else:
            self.contents = [Asset(path=args.asset)]

        # Set up the AWS transfer configuration for the batch
        self.aws_config = TransferConfig(
                                multipart_threshold=self.chunk_bytes,
                                max_concurrency=self.max_threads,
                                multipart_chunksize=self.chunk_bytes,
                                use_threads=self.use_threads
                                )
