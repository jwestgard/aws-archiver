import os
import unittest
from archiver.asset import Asset


class TestAsset(unittest.TestCase):
    def setUp(self):
        pass

    def test_asset_for_sample_file_with_provided_relpath(self):
        sample_file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(sample_file_path, md5='SAMPLE_MD5', relpath="foo/bar/sample_file_1.txt")

        expected_bytes = os.path.getsize(sample_file_path)
        expected_mtime = int(os.path.getmtime(sample_file_path))

        self.assertEqual(sample_file_path, asset.local_path)
        self.assertEqual('SAMPLE_MD5', asset.md5)
        self.assertEqual('sample_file_1.txt', asset.filename)
        self.assertEqual('tests/data/files', asset.directory)
        self.assertEqual('foo/bar/sample_file_1.txt', asset.relpath)
        self.assertEqual(expected_bytes, asset.bytes)
        self.assertEqual(expected_mtime, asset.mtime)

    def test_etag_for_zero_byte_file(self):
        zero_byte_file_path = 'tests/data/files/zero_byte_file.txt'
        asset = Asset(zero_byte_file_path)
        etag = asset.calculate_etag(1)
        self.assertEqual('d41d8cd98f00b204e9800998ecf8427e', etag)

    def test_etag_for_single_nonchunked_file(self):
        file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(file_path)
        # Chunk every 10 bytes
        etag = asset.calculate_etag(10)
        self.assertEqual('6d0b865b7d33c81b43fabaf044a35f76', etag)

    def test_etag_for_chunked_file(self):
        file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(file_path)
        # Chunk every byte
        etag = asset.calculate_etag(1)

        self.assertEqual('90d341c0ca6509f2a82783bdcb806bbb-4', etag)
