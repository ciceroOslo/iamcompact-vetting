"""Common resources for testing"""
import typing as tp

from .test_timeseries_criteria_core import construct_test_iamdf as \
    get_test_energy_iamdf_tuple



TV = tp.TypeVar('TV')
def notnone(x: TV|None) -> TV:
    assert x is not None
    return x
###END def notnone
