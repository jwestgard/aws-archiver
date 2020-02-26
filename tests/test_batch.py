import os
import unittest
from archiver.batch import Batch, ManifestFileType


class TestBatch(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_md5sum_manifest(self):
        batch = Batch(path='tests/data/manifests', bucket='test_bucket', asset_root='/', log_dir='/tmp')
        batch.load_manifest('sample_md5sum_manifest.txt')
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_load_patsy_manifest(self):
        batch = Batch(path='tests/data/manifests', bucket='test_bucket', asset_root='/', log_dir='/tmp')
        batch.load_manifest('sample_patsy_manifest.csv')
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_manifest_file_type(self):
        manifest_type = Batch.manifest_file_type('tests/data/manifests/sample_md5sum_manifest.txt')
        self.assertEqual(ManifestFileType.MD5_SUM, manifest_type)

        manifest_type = Batch.manifest_file_type('tests/data/manifests/sample_patsy_manifest.csv')
        self.assertEqual(ManifestFileType.PATSY_DB, manifest_type)

    def test_add_asset_without_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        batch = Batch(path=sample_file_1_path, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path)

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('tests/data/files/sample_file_1.txt', asset.relpath)

    def test_add_asset_with_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        batch = Batch(path=sample_file_1_path, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path, relpath='test/specific/relpath/sample_file_1.txt')

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('test/specific/relpath/sample_file_1.txt', asset.relpath)
