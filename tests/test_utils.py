import unittest
from archiver.asset import Asset
from archiver.exceptions import PathOutOfScopeException
from archiver.utils import calculate_relative_path


class TestUtils(unittest.TestCase):
    def setUp(self):
        pass

    def test_calculate_relative_path(self):
        test_cases = [
            dict(batch_root='/', local_path='/foo/bar/quuz/test.txt', expected='foo/bar/quuz/test.txt'),
            dict(batch_root='/foo', local_path='/foo/bar/quuz/test.txt', expected='bar/quuz/test.txt'),
            dict(batch_root='/foo/bar', local_path='/foo/bar/quuz/test.txt', expected='quuz/test.txt'),
        ]

        for t in test_cases:
            relative_path = calculate_relative_path(t['batch_root'], t['local_path'])
            self.assertEqual(t['expected'], relative_path, f"Failed test_case: {t}")

        with self.assertRaises(PathOutOfScopeException):
            relative_path = calculate_relative_path('/foo/bar', '/abc/def/ghi/text.txt')
