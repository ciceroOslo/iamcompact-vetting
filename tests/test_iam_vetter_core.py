"""Tests for the IAM Vetter Core module.

In particular contains setting up test data and performing tests on the
`iamcompact_vetting.iam.iam_vetter_core.IamDataFrameTimeseriesVetter` class.
"""
import typing as tp
import unittest

import pandas as pd
from pyam import IamDataFrame
import pyam

from iamcompact_vetting.iam.iam_vetter_core import IamDataFrameTimeseriesVetter


# Construct an IamDataFrame with years 2005, 2010, 2015, 2020, 2025, 2030, and 2
# variables 'Primary Energy' and 'Secondary Energy|Electricity', with two models
# 'ModelA' and 'ModelB', and two scenarios 'Scenario1' and 'Scenario2', as well
# as three regions 'Region1', 'Region2', and 'Region3'. 'Secondary
# Energy|Electricity' should have units 'EJ/yr' for 'ModelA' and 'TWh/yr' for
# 'ModelB'. 'Primary Energy' should have numbers that vary between 1 and 100 in
# all cases, and 'Secondary Energy|Electricity' should have numbers that vary
# between 0.1 and 10 when the unit is 'EJ/yr' and 30 and 3000 when the unit is
# 'TWh/yr'.
def construct_test_iamdf() -> IamDataFrame:
    """Construct a test IamDataFrame for testing the IamDataFrameTimeseriesVetter."""
    data_models: tp.List[str] = ['ModelA', 'ModelB']
    data_scenarios: list[str] = ['Scenario1', 'Scenario2']
    regions: list[str] = ['Region1', 'Region2', 'Region3']
    years: list[int] = [2005, 2010, 2015, 2020, 2025, 2030]
    variables: list[str] = ['Primary Energy', 'Secondary Energy|Electricity']
    index_without_units: pd.MultiIndex = pd.MultiIndex.from_product(
        [data_models, data_scenarios, regions, variables, years],
        names=['model', 'scenario', 'region', 'variable', 'year']
    )
    units_arrays: list[str] = [
        'TWh/yr' if _model == 'ModelB' and _variable == 'Secondary Energy|Electricity'
        else 'EJ/yr'
        for _model, _variable in zip(index_without_units.get_level_values('model'),
                                     index_without_units.get_level_values('variable'))
    ]
    index: pd.MultiIndex = pd.DataFrame(  # type: ignore
        data=units_arrays,
        index=index_without_units,
        columns=['unit']
    ).set_index('unit', append=True).index
    values: pd.Series = pd.Series(
        data=[1.0 + 99.0 * i / 5.0 for i in range(6 * 2 * 3 * 2 * 2)],
        index=index
    )
    return IamDataFrame(data=values.reset_index(name='value'))
