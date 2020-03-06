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
