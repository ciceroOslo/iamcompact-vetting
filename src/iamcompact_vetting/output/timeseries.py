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
    bound=TimeseriesRefCriterion,
)  # Should probably also add `covariant=True`, but need to check with actual
   # behavior whether it's that or `contravariant=True`.

CriterionTargetRangeTypeVar = tp.TypeVar(
    'CriterionTargetRangeTypeVar',
    bound=CriterionTargetRange,
)

SummaryOutputTypeVar = tp.TypeVar(
    'SummaryOutputTypeVar',
    bound=CriterionTargetRangeOutput,
)

class TimeseriesRefFullComparisonOutput(
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


TimeseriesOutputTypeVar = tp.TypeVar(
    'TimeseriesOutputTypeVar',
    bound=TimeseriesRefFullComparisonOutput,
)


class MissingDefaultTypeError(Exception):
    """Exception raised when a default type is missing.

    Used by the `TimeseriesRefFullAndSummaryOutput` class `__init__` method
    when `target_range`, `timeseries_output` or `summary_output` is not set,
    and the class attributes `target_range_default_type`,
    `timeseries_output_default_type` or `summary_output_default_type`,
    respectively, is not defined (i.e., the `__init__` method is being called
    on `TimeseriesRefFullAndSummaryOutput` itself or on a subclass that does not
    define these class attributes).
    """
    ...
###END class MissingDefaultTypeError


class TimeseriesRefComparisonAndTargetOutput(
    tp.Generic[
        TimeseriesRefCriterionTypeVar,
        CriterionTargetRangeTypeVar,
        TimeseriesOutputTypeVar,
        SummaryOutputTypeVar,
        DataFrameMappingWriterTypeVar,
        WriteReturnTypeVar,
    ],
    ResultOutput[
        TimeseriesRefCriterionTypeVar,
        pyam.IamDataFrame,
        dict[str, pd.DataFrame],
        DataFrameMappingWriterTypeVar,
        WriteReturnTypeVar,
    ]
):
    """Base class to output full comparison and targets for TimeseriesRefCriterion.

    The `prepare_output` method of this class returns a two-element dictionary,
    one with the full data as prepared by a `TimeseriesComparisonFullDataOutput`
    instance, and the second with summary metrics prepared by a instance of
    `CriterionTargetRangeOutput` or subclass.

    The class is intended to be used for outputting full and summary results to
    different worksheets in an Excel file using `MultiDataFrameExcelWriter`. The
    keys of the dictionary are then the names of the worksheets. But it can
    also be used for any other writer or purpose that accepts a two-element
    dictionary of the type described here.
    """

    target_range_default_type: tp.Type[CriterionTargetRangeTypeVar]
    timeseries_output_default_type: tp.Type[TimeseriesOutputTypeVar]
    summary_output_default_type: tp.Type[SummaryOutputTypeVar]

    def __init__(
            self,
            *,
            criteria: TimeseriesRefCriterionTypeVar,
            target_range: tp.Optional[
                Callable[
                    [TimeseriesRefCriterionTypeVar],
                    CriterionTargetRangeTypeVar
                ]
            ] = None,
            target_range_type: tp.Optional[
                tp.Type[CriterionTargetRangeTypeVar]
            ] = None,
            target: tp.Optional[float] = None,
            range: tp.Optional[tuple[float, float] | RelativeRange] = None,
            distance_func: tp.Optional[Callable[[float], float]] = None,
            timeseries_output: tp.Optional[
                tp.Callable[
                    [TimeseriesRefCriterion],
                    TimeseriesOutputTypeVar,
                ]
            ] = None,
            timeseries_output_type: tp.Optional[
                tp.Type[TimeseriesOutputTypeVar]
            ] = None,
            summary_output: tp.Optional[
                tp.Callable[
                    [CriterionTargetRangeTypeVar],
                    SummaryOutputTypeVar,
                ]
            ] = None,
            summary_output_type: tp.Optional[
                tp.Type[SummaryOutputTypeVar]
            ] = None,
            writer: tp.Optional[DataFrameMappingWriterTypeVar] = None,
            full_comparison_key: tp.Optional[str] = None,
            summary_key: tp.Optional[str] = None,
    ):
        """Init method.

        Parameters
        ----------
        criteria : TimeseriesRefCriterion
            The criterion to be used to prepare the output data.
        target_range : callable, optional
            A function that takes the `TimeseriesRefCriterion` instance passed
            through the `criteria` parameter and returns a
            `CriterionTargetRange` or subclass instance. See the docstring of
            `CriterionTargetRangeOutput` for details. Optional. If not given, an
            instance of the type given by `target_range_type` is
            constructed using the target, range and optionally `distance_func`
            parameters passed through the `target`, `range` and `distance_func`
            parameters. To access other parameters of the `CriterionTargetRange`
            init method, use a partial function of `CriterionTargetRange` as the
            `target_range` parameter, or pass a lambda that calls
            `CriterionTargetRange` with the parameters set to the desired
            values. If `target_range` is not set, the parameters
            `target_range_type`, `target` and `range` must be set.
            Subclasses can define a default for `target_range_type` by
            setting the class attribute `target_range_default_type`.
        target_range_type : type, optional
            The default type to use to construct a `CriterionTargetRange` or
            subclass instance if `target_range` is not set. Must be a subclass
            of `CriterionTargetRange`, or `CriterionTargetRange` itself.
            Optional, by default uses the class attribute
            `target_range_default_type` if set. If that attribute is not set and
            `target_range` is not set, a MissingDefaultTypeError is raised.
        target : float, optional
            If `target_range` is not set, this parameter is mandatory and used
            to construct a `CriterionTargetRange` instance. A ValueError is
            raised if `target_range` is set and `target` is not None.
        range : 2-tuple of floats or RelativeRange
            If `target_range` is not set, this parameter is mandatory and used
            to construct a `CriterionTargetRange` instance. A ValueError is
            raised if `target_range` is set and `range` is not None.
        distance_func : callable, optional
            If `target_range` is not set, this parameter is used to construct
            a `CriterionTargetRange` instance. A ValueError is raised if
            `target_range` is set and `distance_func` is not None. Optional.
            see the `CriterionTargetRange` docstring for the default behavior.
        timeseries_output : callable, optional
            A function that takes the `TimeseriesRefCriterion` instance passed
            through the `criteria` parameter and returns a
            TimeseriesRefFullComparisonOutput instance, which will be used to
            output the full comparision data. If not set, an instance of the
            type given by `timeseries_output_type` is constructed using
            the writer passed through the `writer` parameter. Optional, by If
            `timeseries_output` is not set, the `timeseries_output_type`
            and `writer` parameters must be set. Subclasses can define a default
            for `timeseries_output_type` by setting the class attribute
            `timeseries_output_default_type`.
        timeseries_output_type : type, optional
            The default type to use to construct a
            `TimeseriesRefFullComparisonOutput` instance if `timeseries_output`
            is not set. Must be a subclass of
            `TimeseriesRefFullComparisonOutput`, or
            `TimeseriesRefFullComparisonOutput` itself. Optional, by default
            uses the class attribute `timeseries_output_default_type` if set.
            If that attribute is not set and `timeseries_output` is not set,
            a MissingDefaultTypeError is raised.
        summary_output : callable, optional
            A function that takes the `CriterionTargetRange` instance passed
            through the `target_range` parameter (or constructed using the
            `target`, `range` and `distance_func` parameters) and returns a
            CriterionTargetRangeOutput instance, which will be used to output
            the summary metrics. If not set, an instance of the type given by
            `summary_output_type` is constructed using the writer
            passed through the `writer` parameter. Optional, by If
            `summary_output` is not set, the `summary_output_type` and
            `writer` parameters must be set. Subclasses can define a default
            for `summary_output_type` by setting the class attribute
            `summary_output_default_type`.
        summary_output_type : type, optional
            The default type to use to construct a
            `CriterionTargetRangeOutput` instance if `summary_output` is not
            set. Must be a subclass of
            `CriterionTargetRangeOutput`, or
            `CriterionTargetRangeOutput` itself. Optional, by default uses the
            class attribute `summary_output_default_type` if set. If that
            attribute is not set and `summary_output` is not set, a
            MissingDefaultTypeError is raised.
        writer : DataFrameMappingWriter
            The writer to be used to write the output data if either
            `timeseries_output` or `summary_output` is not set. Note that if one
            of those is set but not the other, the `writer` parameter must be
            equal to or at least compatible with the writer instance used by the
            one that is set. If either `timeseries_output` or `summary_output`
            is not set, the `writer` parameter is mandatory. If both are set,
            the `writer` parameter is ignored.
        full_comparison_key : str, optional
            The key to use for the full comparison data in the output dict
            returned by the `prepare_output` method. Optional. If not set, the
            default key "Full comparison" is used.
        summary_key : str, optional
            The key to use for the summary metrics in the output dict
            returned by the `prepare_output` method. Optional. If not set, the
            default key "Summary metrics" is used.
        """
        self.criteria: TimeseriesRefCriterionTypeVar = criteria
        if target_range_type is None:
            if hasattr(self, 'target_range_default_type'):
                target_range_type = self.target_range_default_type
        if timeseries_output_type is None:
            if hasattr(self, 'timeseries_output_default_type'):
                timeseries_output_type = self.timeseries_output_default_type
        if summary_output_type is None:
            if hasattr(self, 'summary_output_default_type'):
                summary_output_type = self.summary_output_default_type
        self.target_range: CriterionTargetRangeTypeVar \
                = self._prepare_target_range(
            target_range=target_range,
            target_range_type=target_range_type,
            criteria=criteria,
            target=target,
            range=range,
            distance_func=distance_func,
        )
        self.timeseries_output: TimeseriesOutputTypeVar = \
            self._prepare_timeseries_output(
                timeseries_output=timeseries_output,
                timeseries_output_type=timeseries_output_type,
                criteria=criteria,
                writer=writer,
            )
        self.summary_output: SummaryOutputTypeVar = \
            self._prepare_summary_output(
                summary_output=summary_output,
                summary_output_type=summary_output_type,
                target_range=self.target_range,
                writer=writer,
            )
        self.full_comparison_key: str = \
            full_comparison_key if full_comparison_key is not None \
                else 'Full comparison'
        self.summary_key: str = summary_key if summary_key is not None \
            else 'Summary metrics'
    ###END def TimeseriesComparisonOutput.__init__

    def _prepare_target_range(
            self,
            target_range: Callable[
                [TimeseriesRefCriterionTypeVar],
                CriterionTargetRangeTypeVar
            ] | None,
            target_range_type: tp.Type[CriterionTargetRangeTypeVar] | None,
            criteria: TimeseriesRefCriterionTypeVar,
            target: float | None,
            range: tp.Tuple[float, float] | RelativeRange | None,
            distance_func: tp.Callable[[float], float] | None,
    ) -> CriterionTargetRangeTypeVar:
        """Prepare a CriterionTargetRange or subclass instance for output.

        This method can be overridden by subclasses to customize how
        `target_range` is used to create a `CriterionTargetRange` or subclass
        instance, and/or how a default is created if `target_range` is None.
        """
        if target_range is not None:
            return target_range(criteria)
        else:
            if target_range_type is None:
                raise ValueError(
                    'Either `target_range` or `target_range_type` must be set.'
                )
            if target is None:
                raise ValueError(
                    '`target` cannot be None when `target_range` is not set.'
                )
            if range is None:
                raise ValueError(
                    '`range` cannot be None when `target_range` is not set.'
                )
            return target_range_type(
                criterion=criteria,
                target=target,
                range=range,
                distance_func=distance_func,
            )
    ###END def TimeseriesComparisonOutput._prepare_target_range

    def _prepare_timeseries_output(
            self,
            timeseries_output: Callable[
                [TimeseriesRefCriterionTypeVar],
                TimeseriesOutputTypeVar
            ] | None,
            timeseries_output_type: tp.Type[TimeseriesOutputTypeVar] | None,
            criteria: TimeseriesRefCriterionTypeVar,
            writer: DataFrameMappingWriterTypeVar | None,
    ) -> TimeseriesOutputTypeVar:
        """Prepare a TimeseriesOutput or subclass instance for output.

        This method can be overridden by subclasses to customize how
        `timeseries_output` is used to create a `TimeseriesOutput` or subclass
        instance, and/or how a default is created if `timeseries_output` is
        None.
        """
        if timeseries_output is not None:
            return timeseries_output(criteria)
        else:
            if timeseries_output_type is None:
                raise ValueError(
                    'Either `timeseries_output` or `timeseries_output_type` '
                    'must be set.'
                )
            return timeseries_output_type(
                criteria=criteria,
                writer=writer,
            )
    ###END def TimeseriesComparisonOutput._prepare_timeseries_output

    def _prepare_summary_output(
            self,
            summary_output: Callable[
                [CriterionTargetRangeTypeVar],
                SummaryOutputTypeVar
            ] | None,
            summary_output_type: tp.Type[SummaryOutputTypeVar] | None,
            target_range: CriterionTargetRangeTypeVar,
            writer: DataFrameMappingWriterTypeVar | None,
    ) -> SummaryOutputTypeVar:
        """Prepare a SummaryOutput or subclass instance for output.

        This method can be overridden by subclasses to customize how
        `summary_output` is used to create a `SummaryOutput` or subclass
        instance, and/or how a default is created if `summary_output` is
        None.
        """
        if summary_output is not None:
            return summary_output(target_range)
        else:
            if summary_output_type is None:
                raise ValueError(
                    'Either `summary_output` or `summary_output_type` '
                    'must be set.'
                )
            return summary_output_type(
                criteria=target_range,
                writer=writer,
            )
    ###END def TimeseriesComparisonOutput._prepare_summary_output

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
        full_comparison: pd.DataFrame = \
            self.timeseries_output.prepare_output(data)
        summary_metrics: pd.DataFrame = self.summary_output.prepare_output(data)
        return {
            self.full_comparison_key: full_comparison,
            self.summary_key: summary_metrics,
        }
    ###END def TimeseriesComparisonOutput.prepare_output

###END class TimeseriesComparisonOutput


class OLDCODE_TO_BE_SPLIT_TimeSeriesRefFullAndSummaryOutput(
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
        self._full_data_output: TimeseriesRefFullComparisonOutput[
            TimeseriesRefCriterionTypeVar,
            NoWriter,
            None
        ] = TimeseriesRefFullComparisonOutput(
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
