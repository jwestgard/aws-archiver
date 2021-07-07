import os
import unittest
from unittest.mock import patch
import archiver.asset
from archiver.asset import Asset
from archiver.exceptions import ConfigException


class TestAsset(unittest.TestCase):
    def setUp(self):
        # Some tests reset the "archiver.asset.GB" variable, so store
        # the original value so we can reset it in "tearDown"
        self.original_GB = archiver.asset.GB

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

        # Report file size as is larger than Asset.GB to force chunking
        mock_file_size = archiver.asset.GB + 1
        with unittest.mock.patch('os.path.getsize', return_value=mock_file_size):
            asset = Asset(file_path)
            # Chunk every byte
            etag = asset.calculate_etag(1)

        self.assertEqual('90d341c0ca6509f2a82783bdcb806bbb-4', etag)

    def test_etag_for_chunked_file_where_chunk_size_is_larger_than_asset_GB(self):
        file_path = 'tests/data/files/sample_file_1.txt'

        asset = Asset(file_path)

        # Reset archiver.asset.GB to 1 byte, so that we don't have to have
        # a huge file to do the test
        archiver.asset.GB = 1

        # Chunk every 2 bytes
        etag = asset.calculate_etag(2)

        self.assertEqual('0bbe9c3c497cd97da0754e9be0f7ed59-2', etag)

    def test_raises_config_error_if_chunk_size_not_multiple_of_GB(self):
        file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(file_path)

        # chunk_size is larger than Asset.GB, and not a multiple
        chunk_size = archiver.asset.GB + 1

        # Report file size as 2 chunks
        mock_file_size = chunk_size * 2
        with unittest.mock.patch('os.path.getsize', return_value=mock_file_size):
            with self.assertRaises(ConfigException):
                etag = asset.calculate_etag(chunk_size)

    def test_skips_md5_calculation_for_unchunked_files(self):
        file_path = 'tests/data/files/sample_file_1.txt'
        asset = Asset(file_path)
        asset.md5 = "MD5_FROM_ASSET"
        etag = asset.calculate_etag(10)
        self.assertEqual("MD5_FROM_ASSET", etag)

    def tearDown(self) -> None:
        # Restore the "archiver.asset.GB" to its original value,
        # in case it was modified in a test.
        archiver.asset.GB = self.original_GB
