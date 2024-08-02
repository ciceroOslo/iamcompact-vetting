"""Test of unittest. Dummy module, should be deleted before publishing."""
import typing as tp
import unittest


TV = tp.TypeVar('TV')

def dummyfunc(x: TV) -> TV:
    return x
###END def dummyfunc


class TestDummy(unittest.TestCase):

    def setUp(self) -> None:
        self.myint: int = 43
    ###END def TestDummy.setUp

    def test_dummyfunc(self) -> None:
        self.assertEqual(dummyfunc(1), 1)
    ###END def TestDummy.test_dummyfunc

    def test_faildummyfunc(self) -> None:
        self.assertEqual(dummyfunc(2), 2)
    ###END def TestDummy.test_faildummyfunc

    def test_dummy_myint(self) -> None:
        self.assertEqual(dummyfunc(self.myint), 43)

###END class TestDummy
