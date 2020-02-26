import os
import unittest
from archiver.asset import Asset
from archiver.exceptions import PathOutOfScopeException

class TestAsset(unittest.TestCase):
    def setUp(self):
        pass

    def test_asset_for_sample_file(self):
        sample_file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(sample_file_path, 'tests/data/', md5='SAMPLE_MD5')

        expected_bytes = os.path.getsize(sample_file_path)
        expected_mtime = int(os.path.getmtime(sample_file_path))

        self.assertEqual(sample_file_path, asset.local_path)
        self.assertEqual('SAMPLE_MD5', asset.md5)
        self.assertEqual('sample_file_1.txt', asset.filename)
        self.assertEqual('tests/data/files', asset.directory)
        self.assertEqual('files/sample_file_1.txt', asset.relpath)
        self.assertEqual(expected_bytes, asset.bytes)
        self.assertEqual(expected_mtime, asset.mtime)

    def test_asset_for_sample_file_with_provided_relpath(self):
        sample_file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(sample_file_path, 'tests/data/', md5='SAMPLE_MD5', relpath="foo/bar/sample_file_1.txt")

        expected_bytes = os.path.getsize(sample_file_path)
        expected_mtime = int(os.path.getmtime(sample_file_path))

        self.assertEqual(sample_file_path, asset.local_path)
        self.assertEqual('SAMPLE_MD5', asset.md5)
        self.assertEqual('sample_file_1.txt', asset.filename)
        self.assertEqual('tests/data/files', asset.directory)
        self.assertEqual('foo/bar/sample_file_1.txt', asset.relpath)
        self.assertEqual(expected_bytes, asset.bytes)
        self.assertEqual(expected_mtime, asset.mtime)

    def test_calculate_relative_path(self):
        test_cases = [
            dict(batch_root='/', local_path='/foo/bar/quuz/test.txt', expected='foo/bar/quuz/test.txt'),
            dict(batch_root='/foo', local_path='/foo/bar/quuz/test.txt', expected='bar/quuz/test.txt'),
            dict(batch_root='/foo/bar', local_path='/foo/bar/quuz/test.txt', expected='quuz/test.txt'),
        ]

        for t in test_cases:
            relative_path = Asset.calculate_relative_path(t['batch_root'], t['local_path'])
            self.assertEqual(t['expected'], relative_path, f"Failed test_case: {t}")

        with self.assertRaises(PathOutOfScopeException):
            relative_path = Asset.calculate_relative_path('/foo/bar', '/abc/def/ghi/text.txt')
