import unittest

from archiver.manifests.manifest_factory import ManifestFactory
from archiver.manifests.md5_sum_manifest import Md5SumManifest
from archiver.manifests.inventory_manifest import InventoryManifest
from archiver.manifests.patsy_db_manifest import PatsyDbManifest
from archiver.manifests.single_asset_manifest import SingleAssetManifest


class TestManifestFactory(unittest.TestCase):
    def setUp(self):
        pass

    def test_create(self):
        manifest = ManifestFactory.create('tests/data/manifests/sample_md5sum_manifest.txt')
        self.assertIsInstance(manifest, Md5SumManifest)

        manifest = ManifestFactory.create('tests/data/manifests/sample_patsy_manifest.csv')
        self.assertIsInstance(manifest, PatsyDbManifest)

        manifest = ManifestFactory.create(None)
        self.assertIsInstance(manifest, SingleAssetManifest)

        manifest = ManifestFactory.create('tests/data/manifests/sample_inventory_manifest.csv')
        self.assertIsInstance(manifest, InventoryManifest)
