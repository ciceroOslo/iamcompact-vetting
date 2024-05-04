"""Tests for the IAM Vetter Core module.

In particular contains setting up test data and performing tests on the
`iamcompact_vetting.iam.iam_vetter_core.IamDataFrameTimeseriesVetter` class.
"""
import typing as tp
import unittest

import pandas as pd
from pyam import IamDataFrame
import pyam
import numpy as np

from iamcompact_vetting.iam.iam_vetter_core import IamDataFrameTimeseriesVetter


TV = tp.TypeVar('TV')
def notnone(x: TV|None) -> TV:
    assert x is not None
    return x
###END def notnone


# Construct an IamDataFrame with years 2005, 2010, 2015, 2020, 2025, 2030, and 2
# variables 'Primary Energy' and 'Secondary Energy|Electricity', with two models
# 'ModelA' and 'ModelB', and two scenarios 'Scenario1' and 'Scenario2', as well
# as three regions 'Region1', 'Region2', and 'Region3'. 'Secondary
# Energy|Electricity' should have units 'EJ/yr' for 'ModelA' and 'TWh/yr' for
# 'ModelB'. 'Primary Energy' should have numbers that vary between 1 and 100 in
# all cases, and 'Secondary Energy|Electricity' should have numbers that vary
# between 0.1 and 10 when the unit is 'EJ/yr' and 30 and 3000 when the unit is
# 'TWh/yr'.
def construct_test_iamdf() -> tuple[IamDataFrame, IamDataFrame]:
    """Construct a test IamDataFrame for testing the IamDataFrameTimeseriesVetter.
    
    Returns
    -------
    data_series, target_series : (IamDataFrame, IamDataFrame)
        A tuple of two IamDataFrames, the first being the test IamDataFrame and
        the second being the target IamDataFrame. They each have the following
        structure:
          - data_models: ['ModelA', 'ModelB']
          - data_scenarios: ['Scenario1', 'Scenario2']
          - regions: ['Region1', 'Region2', 'Region3']
          - years: [2005, 2010, 2015, 2020, 2025, 2030]
          - variables: ['Primary Energy', 'Secondary Energy|Electricity']
          - units: ['EJ/yr', 'TWh/yr']
        The values for 'Primary Energy' for both models and
        'Secondary Energy|Electricity' for 'ModelA' have units `EJ/yr` and vary
        randomly between 1 and 100. The values for
        'Secondary Energy|Electricity' for 'ModelB' have units `TWh/yr` and vary
        randomly 1000/3.6 and 100000/3.6 (the same range as the `EJ/yr` values,
        but converted to `TWh/yr`).
    """
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
    data_series: pd.Series = pd.Series(
        data=np.random.rand(len(index)) * 99.0 + 1.0,
        index=index
    )
    # Create a target series that varies randomly between 0.9 and 1.1 times the
    # value of target_series.
    diff_factors: pd.Series = pd.Series(
        data=np.random.rand(len(index)) * 0.2 + 0.9,
        index=index
    )
    target_series: pd.Series = data_series * diff_factors
    # Multiply the target_series by 1000 and divide by 3.6 where the unit is
    # 'TWh/yr' and the model is 'ModelB' and the variable is 'Secondary
    # Energy|Electricity'.
    data_series = data_series.where(
        (data_series.index.get_level_values('unit') == 'EJ/yr') |
        (data_series.index.get_level_values('model') == 'ModelA') |
        (data_series.index.get_level_values('variable') == 'Primary Energy'),
        other=data_series * 1000.0 / 3.6
    )
    # The units of the target_series should be 'EJ/yr' everywhere, and not
    # converted, so set the `unit` level of the target series to 'EJ/yr'
    # everywhere.
    assert isinstance(target_series.index, pd.MultiIndex)
    # target_series.index = target_series.index.set_levels(['EJ/yr'], level='unit')
    # values: pd.Series = pd.Series(
    #     data=[1.0 + 99.0 * i / 5.0 for i in range(6 * 2 * 3 * 2 * 2)],
    #     index=index
    # )
    return (
        IamDataFrame(data_series),
        notnone(IamDataFrame(target_series).rename(
            {'unit': {'TWh/yr': 'EJ/yr'}}
        ))
    )
