import os
import unittest
from archiver.batch import Batch
from archiver.manifests.manifest_factory import ManifestFactory


class TestBatch(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_inventory_manifest(self):
        manifest = ManifestFactory.create('tests/data/manifests/sample_inventory_manifest.csv')
        batch = Batch(manifest, bucket='test_bucket', asset_root='/', log_dir='/tmp')
        manifest.load_manifest('sample_inventory_manifest.csv', batch)
        self.assertEqual(11, batch.stats['total_assets'])
        self.assertEqual(11, batch.stats['assets_missing'])

    def test_load_md5sum_manifest(self):
        manifest = ManifestFactory.create('tests/data/manifests/sample_md5sum_manifest.txt')
        batch = Batch(manifest, bucket='test_bucket', asset_root='/', log_dir='/tmp')
        manifest.load_manifest('sample_md5sum_manifest.txt', batch)
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_load_patsy_manifest(self):
        manifest = ManifestFactory.create('tests/data/manifests/sample_patsy_manifest.csv')
        batch = Batch(manifest, bucket='test_bucket', asset_root='/', log_dir='/tmp')
        manifest.load_manifest('sample_patsy_manifest.csv', batch)
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_add_asset_without_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        manifest = ManifestFactory.create(None)
        batch = Batch(manifest, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path)

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('tests/data/files/sample_file_1.txt', asset.relpath)

    def test_add_asset_with_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        manifest = ManifestFactory.create(None)
        batch = Batch(manifest, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path, relpath='test/specific/relpath/sample_file_1.txt')

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('test/specific/relpath/sample_file_1.txt', asset.relpath)
