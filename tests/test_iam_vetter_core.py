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

from iamcompact_vetting.pdhelpers import replace_level_values
from iamcompact_vetting.iam.iam_vetter_core import (
    IamDataFrameTimeseriesVetter,
    IamDataFrameVariableDiff,
    # IamDataFrameVariableRatio,
    IamDataFrameTimeseriesCheckResult
)
from iamcompact_vetting.vetter_base import FinishedStatus


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
def construct_test_iamdf() -> tuple[
        IamDataFrame,
        IamDataFrame,
        IamDataFrame,
        IamDataFrame
]:
    """Construct a test IamDataFrame for testing the IamDataFrameTimeseriesVetter.
    
    Returns
    -------
    data_df, target_df, diff_df, ratio_df : (IamDataFrame, IamDataFrame)
        A tuple of four IamDataFrames, the first being the test IamDataFrame and
        the second being the target IamDataFrame. They each have the following
        structure:
          - data_models: ['ModelA', 'ModelB'] for `data_df` and ['Target Model']
            for `target_df`
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
        The last two IamDataFrames have the same structure as `data_df`, and
        values equal to the difference and ratio of the values in `data_df`
        relative to `target_df`, respectively (matching on all dimensions
        except for the `model` and `unit` dimensions). They are both in units
        of `EJ/yr`.
    """
    data_models: list[str] = ['ModelA', 'ModelB']
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
    # Create a target series that is numerically equal to data_series for
    # `model == "ModelB"`, but with the model name replaced by `"Target Model"`
    target_series: pd.Series = data_series.xs('ModelB', level='model',
                                              drop_level=False)
    target_series = replace_level_values(
        target_series,
        mapping={'ModelB': 'Target Model'},
        level_name='model'
    )
    target_series_allEJ = replace_level_values(
        target_series,
        mapping={'TWh/yr': 'EJ/yr'},
        level_name='unit'
    )
    target_series_electTWh = target_series.where(
        target_series.index.get_level_values('unit') != 'TWh/yr',
        other=target_series * 1000.0 / 3.6
    )

    # Multiply the target_series by 1000 and divide by 3.6 where the unit is
    # 'TWh/yr' and the model is 'ModelB' and the variable is 'Secondary
    # Energy|Electricity'.
    data_series = data_series.where(
        (data_series.index.get_level_values('unit') == 'EJ/yr') |
        (data_series.index.get_level_values('model') == 'ModelA') |
        (data_series.index.get_level_values('variable') == 'Primary Energy'),
        other=data_series * 1000.0 / 3.6
    )

    diff_series: pd.Series = tp.cast(pd.Series, pd.concat(
        [
            data_series.xs('ModelA', level='model', drop_level=False) \
                - replace_level_values(
                    target_series_allEJ,
                    mapping={'Target Model': 'ModelA'},
                    level_name='model'
                ),
            data_series.xs('ModelB', level='model', drop_level=False) \
                - replace_level_values(
                    target_series_electTWh,
                    mapping={'Target Model': 'ModelB'},
                    level_name='model'
                )
        ]
    ))
    ratio_series: pd.Series = pd.concat(
        [
            data_series.xs('ModelA', level='model', drop_level=False) \
                / replace_level_values(
                    target_series_allEJ,
                    mapping={'Target Model': 'ModelA'},
                    level_name='model'
                ),
            data_series.xs('ModelB', level='model', drop_level=False) \
                / replace_level_values(
                    target_series_electTWh,
                    mapping={'Target Model': 'ModelB'},
                    level_name='model'
                )
        ]
    )
    ratio_series = replace_level_values(
        ratio_series,
        mapping={_unit: '' for _unit in ['EJ/yr', 'TWh/yr']},
        level_name='unit'
    )
    # The units of the target_series should be 'EJ/yr' everywhere, and not
    # converted, so set the `unit` level of the target series to 'EJ/yr'
    # everywhere.
    assert isinstance(target_series_electTWh.index, pd.MultiIndex)
    # target_series.index = target_series.index.set_levels(['EJ/yr'], level='unit')
    # values: pd.Series = pd.Series(
    #     data=[1.0 + 99.0 * i / 5.0 for i in range(6 * 2 * 3 * 2 * 2)],
    #     index=index
    # )
    return (
        IamDataFrame(data_series),
        notnone(IamDataFrame(target_series_electTWh)),
        notnone(IamDataFrame(diff_series)),
        notnone(IamDataFrame(ratio_series))
    )
###END def construct_test_iamdf


class TestIamDataFrameTimeseriesVetterDiffRatio(unittest.TestCase):
    """Tests for the IamDataFrameTimeseriesVetter class.
    
    These test use the `iam_vetter_core.IamDataFrameVariableDiff` and
    `iam_vetter_core.IamDataFrameVariableRatio` classes to compare values, and
    thereby test both the `IamDataFrameTimeseriesVetter` class and the
    `IamDataFrameTimeseriesVariableComparison` class.
    """

    data_df: IamDataFrame
    target_df: IamDataFrame
    diff_df: IamDataFrame
    ratio_df: IamDataFrame
    diff_comparison: IamDataFrameVariableDiff
    # ratio_comparison: IamDataFrameVariableRatio
    
    def setUp(self) -> None:
        """Set up the test data for the IamDataFrameTimeseriesVetter tests."""
        self.data_df, self.target_df, self.diff_df, self.ratio_df = \
            construct_test_iamdf()
    ###END def TestIamDataFrameTimeseriesVetterDiffRatio.setUp

    def test_diff_vetter_no_var_suffix(self) -> None:
        """Test IamDataFrameTimeseriesVetter with IamDataFrameVariableDiff."""
        diff_vetter_no_var_suffix = IamDataFrameTimeseriesVetter(
            target=self.target_df,
            comparisons=[
                IamDataFrameVariableDiff(
                    match_dims=['scenario', 'region', 'variable', 'year'],
                    var_suffix='',
                    var_prefix=''
                )
            ],
            status_mapping=lambda _idf: FinishedStatus.FINISHED
        )
        results: IamDataFrameTimeseriesCheckResult[FinishedStatus] \
            = diff_vetter_no_var_suffix.check(self.data_df)
        self.assertEqual(results.status, FinishedStatus.FINISHED)
        self.assertTrue(results.value.equals(self.data_df))
        self.assertTrue(results.target_value.equals(self.target_df))
        self.assertTrue(results.measure.equals(self.diff_df))
    ###END def TestIamDataFrameTimeseriesVetterDiffRatio.test_diff_vetter

    def test_diff_vetter_default_var_suffix(self) -> None:
        """Test IamDataFrameTimeseriesVetter with IamDataFrameVariableDiff."""
        diff_vetter_no_var_suffix = IamDataFrameTimeseriesVetter(
            target=self.target_df,
            comparisons=[
                IamDataFrameVariableDiff(
                    match_dims=['scenario', 'region', 'variable', 'year'],
                )
            ],
            status_mapping=lambda _idf: FinishedStatus.FINISHED
        )
        results: IamDataFrameTimeseriesCheckResult[FinishedStatus] \
            = diff_vetter_no_var_suffix.check(self.data_df)
        diff_var_rename_dict: dict[str, str] = {
            _varname: _varname + '|Difference' for _varname in self.diff_df.variable
        }
        self.assertEqual(results.status, FinishedStatus.FINISHED)
        self.assertTrue(results.value.equals(self.data_df))
        self.assertTrue(results.target_value.equals(self.target_df))
        self.assertTrue(results.measure.equals(
            self.diff_df.rename(variable=diff_var_rename_dict)
        ))
    ###END def TestIamDataFrameTimeseriesVetterDiffRatio.test_diff_vetter

###END class TestIamDataFrameTimeseriesVetterDiffRatio
    
