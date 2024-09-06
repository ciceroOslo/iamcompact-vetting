"""Module for outputting results of timeseries comparisons.

Currently this module only contains classes for writing comparisons between
IAM model results and harmonisation data or other timeseries reference data.
"""
import typing as tp
from collections.abc import Sequence, Mapping, Callable

import pyam
import pandas as pd

from ..targets.target_classes import (
    CriterionTargetRange,
    RelativeRange,
)
from ..pea_timeseries.timeseries_criteria_core import (
    TimeseriesRefCriterion,
)
from ..pea_timeseries.dims import DIM
from .base import (
    CTCol,
    CriterionTargetRangeOutput,
    DataFrameMappingWriterTypeVar,
    NoWriter,
    ResultOutput,
    WriteReturnTypeVar,
    WriterTypeVar,
)


TimeseriesRefCriterionTypeVar = tp.TypeVar(
    'TimeseriesRefCriterionTypeVar',
    bound=TimeseriesRefCriterion
)  # Should probably also add `covariant=True`, but need to check with actual
   # behavior whether it's that or `contravariant=True`.

class TimeseriesComparisonFullDataOutput(
    ResultOutput[
        TimeseriesRefCriterionTypeVar,
        pyam.IamDataFrame,
        pd.DataFrame,
        WriterTypeVar,
        WriteReturnTypeVar,
    ]
):
    """Class for outputting full timeseries data from timeseries comparisons.

    The `prepare_output` method of this class takes a `TimeseriesRefCriterion`
    or subclass instance as input, and returns output as a pandas `DataFrame`.
    The `DataFrame` returned by this class is the same as one would get by
    pivoting/unstacking the years of the Series returned by the `get_values`
    method of the `TimeseriesRefCriterion` instance, or by creating a
    `pyam.IamDataFrame` from that Serie` and calling its `.timeseries()` method.
    Subclasses may implement more case-specific behavior and processing.
    """

    def prepare_output(
        self,
        data: pyam.IamDataFrame,
        /,
        criteria: tp.Optional[TimeseriesRefCriterionTypeVar] = None,
    ) -> pd.DataFrame:
        """Prepare the output data for writing.

        Parameters
        ----------
        criterion : TimeseriesRefCriterion
            The criterion to be used to prepare the output data.

        Returns
        -------
        pd.DataFrame
            The output data to be written.
        """
        if criteria is None:
           criteria = self.criteria
        comparison_result: pd.Series = criteria.compare(data)
        timeseries_df: pd.DataFrame = \
            comparison_result.unstack(level=DIM.TIME)
        return timeseries_df
    ###END def TimeseriesComparisonFullDataOutput.prepare_output

###END class TimeseriesComparisonFullDataOutput


class CriterionTargetRangeOtherKwargs(tp.TypedDict, total=False):
    """Additional keyword arguments to be passed to the
    `CriterionTargetRange` class, except for the `target`, `range` and
    `distance_func` parameters.

    Used to annotate the `criterion_target_range_kwargs` parameter of the
    `TimeSeriesRefFullAndSummaryOutput` class `__init__` method.
    """
    unit: tp.Optional[str]
    name: tp.Optional[str]
    convert_value_units: tp.Optional[bool]
    convert_input_units: bool
    value_unit: tp.Optional[str]
###END class TypedDict CriterionTargetRangeOtherKwargs


class TimeSeriesRefFullAndSummaryOutput(
    ResultOutput[
        TimeseriesRefCriterionTypeVar,
        pyam.IamDataFrame,
        dict[str, pd.DataFrame],
        DataFrameMappingWriterTypeVar,
        WriteReturnTypeVar,
    ]
):
    """Class to output both full and summary data for timeseries comparisons.

    The `prepare_output` method of this class returns a two-element dictionary,
    one with the full data as prepared by the 
    `TimeseriesComparisonFullDataOutput` class, and the second with summary
    metrics as prepared by the `CriterionTargetRangeOutput` class.

    The class is intended to be used for outputting full and summary results to
    different worksheets in an Excel file using `MultiDataFrameExcelWriter`. The
    keys of the dictionary are then the names of the worksheets. But it can
    also be used for any other writer or purpose that accepts a two-element
    dictionary of the type described here.
    """

    def __init__(
            self,
            *,
            criteria: TimeseriesRefCriterionTypeVar,
            target: float,
            range: tuple[float, float] | RelativeRange,
            writer: DataFrameMappingWriterTypeVar,
            columns: tp.Optional[Sequence[CTCol]] = None,
            column_titles: tp.Optional[Mapping[CTCol, str]] = None,
            full_comparison_key: tp.Optional[str] = None,
            summary_key: tp.Optional[str] = None,
            distance_func: tp.Optional[Callable[[float], float]] = None,
            criterion_target_range_kwargs: \
                tp.Optional[CriterionTargetRangeOtherKwargs] = None,
    ):
        """Init method.

        Parameters
        ----------
        criteria : TimeseriesRefCriterion
            The criterion to be used to prepare the output data.
        target : float
            The target value used for the summary metrics. It is compared to the
            values returned by the `.get_values` method of the
            `TimeseriesRefCriterion` instance passed through the `criteria`
            parameter. See the docstring of `CriterionTargetRangeOutput` for
            details.
        range : 2-tuple of floats or RelativeRange
            The range used for the summary metrics. See the docstring of
            `CriterionTargetRangeOutput` for details.
        writer : DataFrameMappingWriter
            The writer to be used to write the output data.
        columns : list of CTCol, optional
            The columns to be used in the summary metrics DataFrame. See the
            docstring of CriterionTargetRangeOutput for details. Optional. By
            default, all columns are included.
        column_titles : dict of CTCol, optional
            The column titles to be used in the output data. See the docstring
            of CriterionTargetRangeOutput for details. Optional. By default,
            the following titles are used:
            * `CTCol.INRANGE`: `"Is in target range"`
            * `CTCol.DISTANCE`: `"Rel. distance from target"`
            * `CTCol.VALUE`: `"Value"`
        full_comparison_key : str, optional
            The key to be used for the full comparison DataFrame in the
            dictionary returned by the `prepare_output` method. Optional, by
            default, `"Full comparison"` is used.
        summary_key : str, optional
            The key to be used for the summary metrics DataFrame in the
            dictionary returned by the `prepare_output` method. Optional, by
            default, `"Summary metrics"` is used.
        distance_func : callable, optional
            The function to be used to compute the relative distance from the
            target. See the docstring of `CriterionTargetRangeOutput` for
            details, including the default value. Optional.
        criterion_target_range_kwargs : dict, optional
            Keyword arguments to be passed to a `CriterionTargetRangeOutput`
            instance that is used to prepare the summary metrics, except for
            the `criterion`, `target`, `range` and `distance_func` parameters.
            See the docstring of `CriterionTargetRangeOutput` for details.
        """
        self.criteria: TimeseriesRefCriterionTypeVar = criteria
        self.writer: DataFrameMappingWriterTypeVar = writer
        self._default_columns: Sequence[CTCol] = columns if columns is not None else (
            CTCol.INRANGE,
            CTCol.DISTANCE,
            CTCol.VALUE,
        )
        self._default_column_titles: Mapping[CTCol, str] = column_titles \
            if column_titles is not None else {
                CTCol.INRANGE: 'Is in target range',
                CTCol.DISTANCE: 'Rel. distance from target',
                CTCol.VALUE: 'Value',
        }
        self._full_comparison_key: str = full_comparison_key \
            if full_comparison_key is not None else 'Full comparison'
        self._summary_key: str = summary_key if summary_key is not None \
            else 'Summary metrics'
        self._full_data_output: TimeseriesComparisonFullDataOutput[
            TimeseriesRefCriterionTypeVar,
            NoWriter,
            None
        ] = TimeseriesComparisonFullDataOutput(
            criteria=criteria,
            writer=NoWriter(),
        )
        self._summary_target_range: CriterionTargetRange = CriterionTargetRange(
            criterion=criteria,
            target=target,
            range=range,
            distance_func=distance_func,
            **(criterion_target_range_kwargs or {}),
        )
        # THE OUTPUT-RELATED CODE BELOW NEEDS TO BE CHECKED AND REWRITTEN
        self._summary_output: CriterionTargetRangeOutput[
            CriterionTargetRange,
            NoWriter,
            None
        ] = CriterionTargetRangeOutput(
            criteria=self._summary_target_range,
            writer=NoWriter(),
            columns=columns,
            column_titles=column_titles,
        )
    ###END def TimeseriesComparisonOutput.__init__

    def prepare_output(
            self,
            data: pyam.IamDataFrame,
    ) -> dict[str, pd.DataFrame]:
        """Prepare DataFrames with full comparison and with summary metrics.

        *NB!* Unlike the `prepare_output` method of some other `ResultsOutput`
        subclasses, this method does not take accept a custom `criteria`
        parameter. Use the `criteria` parameter of the `__init__` method when
        creating the instance instead. If there is sufficient demand for
        enabling a custom `criteria` parameter for this method, it may be
        implemented in the future.

        Parameters
        ----------
        data : pyam.IamDataFrame
            The data to be used in the output.

        Returns
        -------
        dict
            A dictionary with the following keys:
            * `self._full_comparison_key`: The full comparison DataFrame
            * `self._summary_key`: The summary metrics DataFrame
        """
        # NB! The code below is probably quite inefficient, as the
        # `prepare_output` calls of both `_full_data_output` and
        # `_summary_output` will call `self.criteria.get_values`, which
        # can be expensive. This should be fixed, maybe by enabling
        # `TimeseriesRefCriterion.get_values` to cache its return value.
        full_comparison = self._full_data_output.prepare_output(data)
        summary_metrics = self._summary_output.prepare_output(data)
        return {
            self._full_comparison_key: full_comparison,
            self._summary_key: summary_metrics,
        }
    ###END def TimeseriesComparisonOutput.prepare_output

###END class TimeseriesComparisonOutput
