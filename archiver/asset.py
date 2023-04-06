import hashlib
import os
from .exceptions import ConfigException
from .utils import calculate_relative_path

GB = 1024 ** 3


class Asset:
    """
    Class representing a binary resource to be archived.
    """

    def __init__(self, path, batch_name=None, md5=None, relpath=None, manifest_row=None, etag=None):
        self.local_path = path
        self.batch_name = batch_name
        self.md5 = md5 or self.calculate_md5()
        self.filename = os.path.basename(self.local_path)
        self.mtime = int(os.path.getmtime(self.local_path))
        self.directory = os.path.dirname(self.local_path)
        self.bytes = os.path.getsize(self.local_path)
        self.extension = os.path.splitext(self.filename)[1].lstrip('.').upper()
        self.relpath = relpath
        self.manifest_row = manifest_row
        self.etag = etag

    def calculate_md5(self):
        """
        Calculate and return the object's md5 hash.
        """
        md5sum = hashlib.md5()
        with open(self.local_path, 'rb') as f:
            for data in f:
                md5sum.update(data)
        return md5sum.hexdigest()

    def calculate_etag(self, chunk_size):
        """
        Calculate the AWS etag: either the md5 hash, or for files larger than
        the specified chunk size, the hash of all the chunk hashes concatenated
        together, followed by the number of chunks.
        """
        file_size = os.path.getsize(self.local_path)

        if file_size == 0:
            # Special handling for zero byte files, just return the MD5 sum of
            # an empty string
            return hashlib.md5(b'').hexdigest()

        # Min unchunked file_size is the smaller of chunk_size and GB
        min_unchunked_file_size = min(chunk_size, GB)

        # For files that are small enough not to be chunked, simply return
        # the asset MD5
        use_asset_md5 = (file_size < min_unchunked_file_size) and self.md5
        if use_asset_md5:
            return self.md5

        md5s = []
        with open(self.local_path, 'rb') as handle:
            if chunk_size < GB:
                for data in chunked(handle, chunk_size):
                    md5s.append(hashlib.md5(data))
            else:
                # Python doesn't like reading more than 1GB of bytes from a file at a time.
                # To get around this, we read 1GB at a time and assemble those portions into
                # the final md5sum.
                if chunk_size % GB != 0:
                    raise ConfigException('Chunk sizes >1GB must be multiples of 1GB')
                portions_per_chunk = chunk_size // GB
                md5sum = None
                for i, data in enumerate(chunked(handle, GB), 1):
                    if md5sum is None:
                        md5sum = hashlib.md5()
                    md5sum.update(data)
                    if i % portions_per_chunk == 0:
                        md5s.append(md5sum)
                        md5sum = None
                else:
                    # check to see if we have a pending md5sum
                    # after the last iteration of the loop
                    if md5sum is not None:
                        md5s.append(md5sum)

        if len(md5s) == 1:
            return md5s[0].hexdigest()
        else:
            digests = hashlib.md5(b''.join(m.digest() for m in md5s))
            return f'{digests.hexdigest()}-{len(md5s)}'


def chunked(handle, chunk_size):
    # based on https://stackoverflow.com/a/54989668/5124907
    return iter(lambda: handle.read(chunk_size), b'')
