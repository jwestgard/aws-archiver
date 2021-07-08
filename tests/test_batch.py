import os
import unittest
from archiver.batch import Batch, ManifestFileType
from archiver.deposit import manifest_factory
from unittest.mock import patch, MagicMock

from archiver.manifests.md5_sum_manifest import Md5SumManifest
from archiver.manifests.patsy_db_manifest import PatsyDbManifest
from archiver.manifests.single_asset_manifest import SingleAssetManifest


class TestBatch(unittest.TestCase):
    def setUp(self):
        pass

    def test_load_md5sum_manifest(self):
        manifest = manifest_factory('tests/data/manifests/sample_md5sum_manifest.txt')
        self.assertIsInstance(manifest, Md5SumManifest)
        batch = Batch(manifest, bucket='test_bucket', asset_root='/', log_dir='/tmp')
        manifest.load_manifest('sample_md5sum_manifest.txt', batch)
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_load_patsy_manifest(self):
        manifest = manifest_factory('tests/data/manifests/sample_patsy_manifest.csv')
        self.assertIsInstance(manifest, PatsyDbManifest)
        batch = Batch(manifest, bucket='test_bucket', asset_root='/', log_dir='/tmp')
        manifest.load_manifest('sample_patsy_manifest.csv', batch)
        self.assertEqual(5, batch.stats['total_assets'])
        self.assertEqual(5, batch.stats['assets_missing'])

    def test_manifest_factory(self):
        manifest = manifest_factory('tests/data/manifests/sample_md5sum_manifest.txt')
        self.assertIsInstance(manifest, Md5SumManifest)

        manifest = manifest_factory('tests/data/manifests/sample_patsy_manifest.csv')
        self.assertIsInstance(manifest, PatsyDbManifest)

        manifest = manifest_factory(None)
        self.assertIsInstance(manifest, SingleAssetManifest)

    def test_add_asset_without_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        manifest = manifest_factory(None)
        batch = Batch(manifest, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path)

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('tests/data/files/sample_file_1.txt', asset.relpath)

    def test_add_asset_with_specified_relpath(self):
        sample_file_1_path = os.path.abspath('tests/data/files/sample_file_1.txt')
        asset_root = os.path.abspath('.')
        manifest = manifest_factory(None)
        batch = Batch(manifest, bucket='test_bucket', asset_root=asset_root, log_dir='/tmp')

        batch.add_asset(sample_file_1_path, relpath='test/specific/relpath/sample_file_1.txt')

        self.assertEqual(1, batch.stats['total_assets'])
        self.assertEqual(1, batch.stats['assets_found'])
        asset = batch.contents[0]
        self.assertEqual('test/specific/relpath/sample_file_1.txt', asset.relpath)
