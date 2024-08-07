"""Base classes and core functionality for vettting pyam.IamDataFrame instances."""
import typing as tp
import abc
import enum
from collections.abc import Mapping, Callable, Sequence
import dataclasses
import logging
import functools

from pyam import IamDataFrame
import pyam
import pandas as pd

from iamcompact_vetting.vetter_base import (
    Vetter,
    VettingResultsBase,
    TargetCheckResult,
    TargetCheckVetter
)
from iamcompact_vetting import pyam_helpers



class Dim(str, enum.Enum):
    """Enum for the dimensions of an `IamDataFrame`."""
    MODEL = 'model'
    SCENARIO = 'scenario'
    REGION = 'region'
    VARIABLE = 'variable'
    UNIT = 'unit'
    YEAR = 'year'
###END class Dim



TIMEDIM: Dim = Dim.YEAR
"""Name of the time dimension used."""

# TypeVars
ResultsType = tp.TypeVar('ResultsType', bound=VettingResultsBase)
"""TypeVar for the results of a vetting check."""

MeasureType = tp.TypeVar('MeasureType')
"""TypeVar for the type of the object that measures how close the quantity is to
the target value or range."""

StatusType = tp.TypeVar('StatusType', bound=enum.Enum)
"""TypeVar for the status of a vetting check (should be an enum)."""

TVar = tp.TypeVar('TVar')
"""Generic TypeVar for any type."""


# Create a trivial logger object that does not log anything, but can be used in
# cases where a logger is required but no logging is desired. The object should
# be either an instance or a subclass instance of `logging.Logger`.
class _TrivialLogger(logging.Logger):
    def __init__(self):
        super().__init__(name='TrivialLogger', level=logging.NOTSET)
    ###END def _TrivialLogger.__init__

    def log(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.log

    def debug(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.debug

    def info(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.info

    def warning(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.warning

    def error(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.error

    def critical(self, *args, **kwargs):
        pass
    ###END def _TrivialLogger.critical

###END class _TrivialLogger



def notnone(value: TVar | None) -> TVar:
    """Ensure that a value is not None.

    This function is useful for both ensuring that filter values are not None,
    and to avoid type checking errors, given that many functions in the pyam
    package return None when no data is found, and so can result in type
    checking errors.
    """
    if value is None:
        raise ValueError("Value cannot be None.")
    return value
###END def notnone  


class IamDataFrameVetter(
        Vetter[IamDataFrame, ResultsType],
        tp.Generic[ResultsType],
        abc.ABC
):
    """Base class for performing vetting checks on an `IamDataFrame`.

    Subclasses should implement the `.check` method, which takes an
    `IamDataFrame` as input, and returns a subclass of `VettingResultsBase`. The
    class should also declare the `result_type` attribute, which should be the
    subclass of `VettingResults` that is returned by `.check`.

    Properties
    ----------

    """

    def __init__(self, data: IamDataFrame):
        """
        Parameters
        ----------
        data : IamDataFrame
            The `IamDataFrame` to be checked.
        """
        self._data: IamDataFrame = data
    ###END def IamDataFrameVetter.__init__

    @property
    def data(self) -> IamDataFrame:
        """The `IamDataFrame` to be checked. Note that the data object itself
        is returned, not a copy, so it should not be changed unintentionally.
        """
        return self._data
    ###END property def IamDataFrameVetter.data

    @abc.abstractmethod
    def check(self, data: IamDataFrame) -> ResultsType:
        """Perform a vetting check on the given `IamDataFrame`.

        Parameters
        ----------
        data : IamDataFrame
            The `IamDataFrame` to be checked.

        Returns
        -------
        ResultsType
            The results of the vetting check.
        """
        raise NotImplementedError
    ###END abstractmethod def IamDataFrameVetter.check

###END class IamDataFrameVetter


class IamDataFrameTargetCheckResult(
    TargetCheckResult[
        IamDataFrame,
        IamDataFrame,
        MeasureType,
        StatusType
    ],
    tp.Generic[MeasureType, StatusType]
):
    """Generic base class for result of checking IamDataFrame against a target.
 
    Does not contain additional functionality relative to the
    `TargetCheckResult` base class, only adds type hints and serves as a base
    class for more specific implementations for checking IamDataFrame instances
    against targets.
    """
    ...
###END class IamDataFrameTargetCheckResult


IamDataFrameTargetCheckResultType = tp.TypeVar(
    'IamDataFrameTargetCheckResultType',
    bound=IamDataFrameTargetCheckResult
)


class IamDataFrameTargetVetter(
    TargetCheckVetter[
        IamDataFrame,
        IamDataFrame,
        MeasureType,
        StatusType,
        IamDataFrameTargetCheckResultType
    ],
    tp.Generic[IamDataFrameTargetCheckResultType, MeasureType, StatusType]
):
    """Base class for checking an `IamDataFrame` against a target.
 
    Attributes
    ----------
    filter : Callable[[IamDataFrame], IamDataFrame]
        A filter to apply to the data before checking it against the target.
        Will be called on the data passed to `self.check` before the check is
        performed. Should usually select the data to be compared from a larger
        dataset.
    """

    filter: Callable[[IamDataFrame], IamDataFrame]

    def __init__(
            self,
            target: IamDataFrame,
            compare_func: Callable[[IamDataFrame, IamDataFrame], MeasureType],
            results_type: tp.Type[IamDataFrameTargetCheckResultType],
            status_mapping: Callable[[MeasureType], StatusType],
            filter: Mapping[str, tp.Any] \
                | Callable[[IamDataFrame], IamDataFrame] = lambda _idf: _idf
    ):
        """
        Parameters
        ----------
        target : IamDataFrame
            The target `IamDataFrame` to check against.
        compare_func : Callable[[IamDataFrame, IamDataFrame], MeasureType]
            A function that takes the `IamDataFrame` to be checked and `target`
            as positional input parameters, and returns a measure of how close
            the first `IamDataFrame` is to the second. The type of the measure
            is specified by the `MeasureType` type variable.
        results_type : tp.Type[IamDataFrameTargetCheckResult[MeasureType, StatusType]]
            The type of the results object that will be returned by the `check`
            method. Should be a subclass of `IamDataFrameTargetCheckResult`.
        status_mapping : Callable[[MeasureType], StatusType]
            A function that takes the output of `compare_func` as input and
            returns a status value.
        filter : Mapping[str, tp.Any] | Callable[[IamDataFrame], IamDataFrame],
                Optional
            A filter to apply to the data before checking it against the target.
            Can be a callable that takes an `IamDataFrame` as input and returns
            an `IamDataFrame` as output, or a dict of filters to pass to the
            `IamDataFrame.filter` method. Optional, default is a filter that
            returns the input `IamDataFrame` unchanged.
        """
        super().__init__(
            target_value=target,
            compute_measure=compare_func,
            result_type=results_type,
            status_mapping=status_mapping
        )
        if isinstance(filter, Mapping):
            self.filter = lambda data: notnone(data.filter(**filter))
        elif callable(filter):
            self.filter = filter
        else:
            raise TypeError("`filter` must be a Mapping or a callable.")
    ###END def IamDataFrameTargetVetter.__init__

    def check(self, data: IamDataFrame) -> IamDataFrameTargetCheckResultType:
        """Check the given `IamDataFrame` against the target.

        Parameters
        ----------
        data : IamDataFrame
            The `IamDataFrame` to be checked.

        Returns
        -------
        IamDataFrameTargetCheckResult[MeasureType, StatusType]
            The results of the check.
        """
        return super().check(self.filter(data))
    ###END def IamDataFrameTargetVetter.check

###END class IamDataFrameTargetVetter


class IamDataFrameTimeseriesCheckResult(
    IamDataFrameTargetCheckResult[IamDataFrame, StatusType],
    tp.Generic[StatusType]
):
    """Base class for result of checking IamDataFrame timeseries against a target.
 
    Does not contain additional functionality relative to the
    `IamDataFrameTargetCheckResult` base class, only adds type hints and serves
    as a base class for more specific implementations for checking IamDataFrame
    instances against a target timeseries of another IamDataFrame.
    """
    ...
###END class IamDataFrameTimeseriesCheckResult


@dataclasses.dataclass(kw_only=True)
class IamDataFrameTimeseriesComparisonSpec:
    """Specification for comparing two IamDataFrame instances as timeseries.
 
    Attributes
    ----------
    compare_func : CompareFunc
        The function that takes the data and target, respectively, as the first
        two parameters, and returns a new `IamDataFrame` with the result. The
        data will be filtered by the `filter` attribute of an instance of
        `IamDataFrameTimeseriesVetter` before being passed to this function.
        The values in the dimension(s) of the data given by the `match_dim`
        attribute must match the values in the same dimension(s) of the target.
        The values of the target in other dimensions will be broadcast to match
        the data (note that the target must have only one unique value in each
        of those dimensions, or a `ValueError` will be raised).
        The precise parameters of `compare_func` must be as follows:
            - data : IamDataFrame
                The data to be compared.
            - target : IamDataFrame
                The target timeseries.
            - meta : Optional[pd.DataFrame]
                A metadata DataFrame to be included in the result. If None, the
                default behavior is up to the implementation of the comparison,
                but by default the metadata should be consistent with those of
                the `data` IamDataFrame. It is mandatory for comparison
                functions to handle metadata appropriately.
                Optional, by default None.
            - logger : Optional[logging.Logger]
                A logger to use for logging messages. Optional, by default None.
                If None, no log messages should be written (although the
                may define a logger internally for debugging purposes, or a
                trivial logger that does nothing, to avoid frequent checks
                of whether `logger` is None).
        *NB* The function is expected to check and account for different units
        in the data and target, and to set appropriate units for the result.
        This will often be done automatically if the arithmetic methods of
        `pyam.IamDataFrame` are used, but that is not always the case.
    match_dims : tuple of str
        The dimension(s) of the data and target that must match for the
        comparison. The values in these dimensions will be used to match the
        data and target, and the values in the other dimensions of the target
        will be broadcast to match the data. Note that this parameter must be
        passed to `__init__` as a sequence of strings, even if only one string
        is passed.
    dim_prefix : Mapping[str, str], Optional
        Prefix to add to the values of the result `IamDataFrame` in each
        dimension (e.g., `{'variable': 'Harmonization Comparison|'}). Empty dict
        by default.
        *NB* No separator is added between the prefix and the original value
        (such as a pipe character for variable names). You must add this
        explicitly if it is desired.
    dim_suffix : Mapping[str, str]
        Suffix to add to the values of the result `IamDataFrame` in each
        dimension (e.g., `{'variable': '|Absolute Difference'}). Empty dict by
        default.
        *NB* No separator is added between the original value and the suffix
        (such as a pipe character for variable names). You must add this
        explicitly if it is desired.
    match_time : bool, optional
        Whether to match the time dimension of the data and target. If `True`,
        the time dimension will be added to `match_dims`. Optional, by default
        True.
    """
    class CompareFunc(tp.Protocol):
        def __call__(
                self,
                data: IamDataFrame,
                target: IamDataFrame,
                meta: tp.Optional[pd.DataFrame] = None,
                logger: tp.Optional[logging.Logger] = None
        ) -> IamDataFrame:
            ...
    compare_func: CompareFunc
    match_dims: tuple[str, ...]
    match_time: bool = True
    dim_prefix: Mapping[str, str] = dataclasses.field(default_factory=dict)
    dim_suffix: Mapping[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if self.match_time:
            super().__setattr__('match_dims', (*self.match_dims, TIMEDIM))
            # Have to use super().__setattr__ to circumvent the frozen attribute
###END class IamDataFrameTimeseriesComparisonSpec


ComparisonType = tp.TypeVar(
    'ComparisonType',
    bound=IamDataFrameTimeseriesComparisonSpec
)


class IamDataFrameTimeseriesVetter(
    IamDataFrameTargetVetter[
        IamDataFrameTimeseriesCheckResult[StatusType],
        IamDataFrame,
        StatusType
    ],
    tp.Generic[ComparisonType, StatusType]
):
    """Base class for checking an `IamDataFrame` against a timeseries target.

    The `.check` method of this class will select data from an `IamDataFrame`
    based on the filter provided to the `__init__` method, perform one or a
    sequence of operations (also provided to `__init__`) to compare the selected
    data to the target timeseries and produce a data set of time series
    representing the results of each comparison and return an
    `IamDataFrameTimeseriesCheckResult` object with the resulting dataset along
    with a status value.

    Attributes
    ----------
    comparisons : list of IamDataFrameTimeseriesComparisonSpec
        The comparison operations to perform on the data and target timeseries.
    """
    comparisons: list[ComparisonType]

    @property
    def target(self) -> IamDataFrame:
        """The target `IamDataFrame` to check against."""
        return self.target_value
    ###END property def IamDataFrameTimeseriesVetter.target

    def __init__(
            self,
            target: IamDataFrame,
            comparisons: Sequence[ComparisonType],
            status_mapping: Callable[[IamDataFrame], StatusType],
            filter: Mapping[str, tp.Any] \
                | Callable[[IamDataFrame], IamDataFrame] = lambda _idf: _idf,
    ):
        """
        Parameters
        ----------
        target : IamDataFrame
            The target `IamDataFrame` to check against.
        comparisons : Sequence[IamDataFrameTimeseriesComparisonSpec]
            The comparison operations to perform on the data and target
            timeseries. The comparison functions will be called in the order
            they are given in this sequence, and the results returned by each
            will be concatenated to form the final result.
        status_mapping : Callable[[IamDataFrame], StatusType]
            A function that takes the output `IamDataFrame` from the comparison
            functions as input and returns a status value.
        filter : Mapping[str, tp.Any] | Callable[[IamDataFrame], IamDataFrame],
                Optional
            A filter to apply to the data before checking it against the target.
            Can be a callable that takes an `IamDataFrame` as input and returns
            an `IamDataFrame` as output, or a dict of filters to pass to the
            `IamDataFrame.filter` method. Optional, default is a filter that
            returns the input `IamDataFrame` unchanged.
        """
        super().__init__(
            target=target,
            compare_func=self._do_comparisons,
            results_type=IamDataFrameTimeseriesCheckResult,
            status_mapping=status_mapping,
            filter=filter,
        )
        self.comparisons = list(comparisons)
    ###END def IamDataFrameTimeseriesVetter.__init__

    @staticmethod
    def _make_one_comparison(
            data: IamDataFrame,
            target: IamDataFrame,
            comparison: ComparisonType
    ) -> IamDataFrame:
        """Perform a single comparison operation on the data and target.

        Parameters
        ----------
        data : IamDataFrame
            The data to be compared.
        comparison : IamDataFrameTimeseriesComparisonSpec
            The comparison operation to perform.

        Returns
        -------
        IamDataFrame
            The result of the comparison.
        """
        broadcast_dims: list[str] = [_dim for _dim in data.dimensions
                                     if _dim not in comparison.match_dims
                                     and _dim != Dim.UNIT]
        target_broadcast_dim_values: dict[str, tp.Any] = {
            _dim: getattr(target, _dim) for _dim in broadcast_dims
        }
        for _dim, _val in target_broadcast_dim_values.items():
            if len(_val) > 1:
                raise ValueError(
                    f"Target has more than one unique value in dimension {_dim}."
                )
            target_broadcast_dim_values[_dim] = _val[0]
        target_broadcasted: IamDataFrame = pyam.concat(
            [
                target.rename({_dim: {target_broadcast_dim_values[_dim]: _dataval}})
                for _dim in broadcast_dims for _dataval in getattr(data, _dim)
            ]
        )
        compared: IamDataFrame = comparison.compare_func(data, target_broadcasted)
        # Create a dict that will rename each value in each dimension in
        # `comparison.dim_prefix` and `comparison.dim_suffix` to add the prefix
        # and suffix, respectively.
        rename_dict: dict[str, dict[str, str]] = {
            _dim: {
                _val: f"{comparison.dim_prefix.get(_dim, '')}{_val}{comparison.dim_suffix.get(_dim, '')}"
                for _val in getattr(compared, _dim)
            }
            for _dim in set((*comparison.dim_prefix.keys(),
                             *comparison.dim_suffix.keys()))
        }
        return notnone(
            compared.rename(
                mapping=rename_dict,
                append=False,
                inplace=False
            )
        )
        # return comparison.compare_func(
        #     data.filter(**{dim: data[dim].unique()[0] for dim in comparison.match_dims}),
        #     self.target.filter(**{dim: self.target[dim].unique()[0] for dim in comparison.match_dims})
        # ).rename(
        #     **comparison.dim_prefix,
        #     **comparison.dim_suffix
        # )
    ###END def IamDataFrameTimeseriesVetter._make_one_comparison

    def _do_comparisons(self, data: IamDataFrame, target: IamDataFrame) -> IamDataFrame:
        """Perform the comparison operations on the data and target timeseries.

        Parameters
        ----------
        data : IamDataFrame
            The data to be compared.
        target : IamDataFrame
            The target timeseries.

        Returns
        -------
        IamDataFrame
            The result of the comparison.
        """
        data = self.filter(data)
        result: IamDataFrame = pyam.concat(
            [
                self._make_one_comparison(
                    data=data,
                    target=target,
                    comparison=comparison
                )
                for comparison in self.comparisons
            ]
        )
        return result
    ###END def IamDataFrameTimeseriesVetter._do_comparisons

###END class IamDataFrameTimeseriesVetter


class IamDataFrameTimeseriesVariableComparison(
    IamDataFrameTimeseriesComparisonSpec
):
    """Comparison specification for comparing two IamDataFrame instances as timeseries.

    Is similar to `IamDataFrameTimeseriesComparisonSpec`, but has the following
    additional behavior, tailored for comparing variable values:
        - The `target` IamDataFrame is converted to match the units of the
          `data` IamDataFrame before the comparison is performed. The conversion
          is done per variable, using `pyam_helpers.make_consistent_units`. As
          a result, comparisons can be made performantly between `data` and
          `target` by comparing the underlying `pandas.Series` objects directly
          (though keep in mind that the provided comparison function must
          then manually ensure that the units are set correctly for the result
          if the comparison operation implies a change of units, such as taking
          ratios or percentage-wise differences).
        - `match_dims` is by default set to `('variable', 'region')`, in
          addition to the time dimension.
        - The class provides a decorator `log_variable_mismatches` that will
          compare which variables are present in `data` and `target`. If a
          logger is provided to the comparison function, the decorator will log
          a message at level `logging.INFO` that lists variables present in
          `data` but not in `target` (or no message if there are none), and at
          level `logging.WARNING` that lists variables present in `target` but
          not in `data` (or no message if there are none).
    """

    @staticmethod
    def log_variable_mismatches(
            compare_func: IamDataFrameTimeseriesComparisonSpec.CompareFunc
    ) -> IamDataFrameTimeseriesComparisonSpec.CompareFunc:
        """Decorator for comparing which variables are present in the data and target.

        If a logger is provided to the comparison function, the decorator will
        log a message at level `logging.INFO` that lists variables present in
        `data` but not in `target` (or no message if there are none), and at
        level `logging.WARNING` that lists variables present in `target` but
        not in `data` (or no message if there are none).

        Parameters
        ----------
        compare_func : IamDataFrameTimeseriesComparisonSpec.CompareFunc
            The comparison function to decorate.

        Returns
        -------
        IamDataFrameTimeseriesComparisonSpec.CompareFunc
            The decorated comparison function.
        """
        @functools.wraps(compare_func)
        def _decorated(
                data: IamDataFrame,
                target: IamDataFrame,
                meta: tp.Optional[pd.DataFrame] = None,
                logger: tp.Optional[logging.Logger] = None
        ) -> IamDataFrame:
            data_vars: set[str] = set(data.variable)
            target_vars: set[str] = set(target.variable)
            if logger is not None:
                missing_in_target: set[str] = data_vars - target_vars
                missing_in_data: set[str] = target_vars - data_vars
                if missing_in_target:
                    logger.warning(
                        f"Variables present in data but not in target: {missing_in_target}"
                    )
                if missing_in_data:
                    logger.info(
                        f"Variables present in target but not in data: {missing_in_data}"
                    )
            return compare_func(
                data=data,
                target=target,
                meta=meta,
                logger=logger
            )
        return _decorated
    ###END def IamDataFrameTimeseriesVariableComparison.log_variable_mismatches

    def _call_compare_func(
            self,
            data: IamDataFrame,
            target: IamDataFrame,
            meta: tp.Optional[pd.DataFrame] = None,
            logger: tp.Optional[logging.Logger] = None
    ) -> IamDataFrame:
        """Call the comparison function with the data and target.

        Parameters
        ----------
        data : IamDataFrame
            The data to be compared.
        target : IamDataFrame
            The target timeseries.
        logger : Optional[logging.Logger], optional
            A logger to use for logging messages. Optional, by default None.

        Returns
        -------
        IamDataFrame
            The result of the comparison.
        """
        target = pyam_helpers.make_consistent_units(
            df=target,
            match_df=data,
            keep_meta=True
        )
        if logger is None:
            logger = self.logger
        return self._external_compare_func(
            data=data,
            target=target,
            meta=meta,
            logger=logger
        )
    ###END def IamDataFrameTimeseriesVariableComparison._call_compare_func

    def __init__(
        self,
        compare_func: IamDataFrameTimeseriesComparisonSpec.CompareFunc,
        match_dims: Sequence[str] = ('variable', 'region'),
        dim_prefix: tp.Optional[Mapping[str, str]] = None,
        dim_suffix: tp.Optional[Mapping[str, str]] = None,
        log_variable_mismatches: bool = True,
        logger: tp.Optional[logging.Logger] = None
    ):
        self.logger: logging.Logger|None = logger
        if log_variable_mismatches:
            compare_func = self.log_variable_mismatches(compare_func)
        self._external_compare_func: \
            IamDataFrameTimeseriesComparisonSpec.CompareFunc = compare_func
        if dim_prefix is None:
            dim_prefix = {}
        if dim_suffix is None:
            dim_suffix = {}
        super().__init__(
            compare_func=self._call_compare_func,
            match_dims=tuple(match_dims),
            dim_prefix=dim_prefix,
            dim_suffix=dim_suffix
        )
    ###END def IamDataFrameTimeseriesVariableComparison.__init__

###END class IamDataFrameTimeseriesVariableComparison


@dataclasses.dataclass(init=False)
class IamDataFrameVariableDiff(IamDataFrameTimeseriesVariableComparison):
    """Comparison specification for comparing two IamDataFrame instances as
    timeseries.

    This class is a subclass of `IamDataFrameTimeseriesVariableComparison` that
    provides a comparison function that calculates the difference between the
    values in the data and target timeseries for each variable.

    The comparison function will return an `IamDataFrame` with the same
    dimensions as the data and target, but with the values in the time dimension
    replaced by the differences between the values in the data and target
    timeseries.

    The comparison function will also set the units of the result to the units
    of the data timeseries, and will add a suffix to the variable names of the
    result to indicate that the values are the absolute differences between the
    data and target timeseries.
    """

    def __init__(
        self,
        match_dims: Sequence[str] = ('variable', 'region'),
        logger: tp.Optional[logging.Logger] = None,
        log_variable_mismatches: bool = True,
        use_abs_diff: bool = False,
        var_suffix: tp.Optional[str] = None,
        var_prefix: str = ''
    ):
        """
        Parameters
        ----------
        logger : Optional[logging.Logger], optional
            A logger to use for logging messages. Optional, by default None.
        log_variable_mismatches : bool, optional
            Whether to log a message at level `logging.INFO` that lists
            variables present in the data but not in the target, and at level
            `logging.WARNING` that lists variables present in the target but not
            in the data. Optional, by default True.
        use_abs_diff : bool, optional
            Whether to calculate the absolute difference between the data and
            target timeseries. If `True`, the absolute difference will be
            calculated, otherwise the signed difference will be calculated
            (positive where the data is greater than the target. Optional, by
            default False.
        """
        if use_abs_diff:
            self._compare_func = functools.partial(self._compare_func,
                                                   use_abs_diff=True)
        if var_suffix is None:
            var_suffix = '|Absolute Difference' if use_abs_diff \
                else '|Difference'
        super().__init__(
            compare_func=self._compare_func,
            match_dims=match_dims,
            dim_suffix={'variable': var_suffix},
            dim_prefix={'variable': var_prefix},
            logger=logger,
            log_variable_mismatches=log_variable_mismatches
        )
    ###END def IamDataFrameVariableDiff.__init__

    @staticmethod
    def _compare_func(
            data: IamDataFrame,
            target: IamDataFrame,
            meta: tp.Optional[pd.DataFrame] = None,
            logger: tp.Optional[logging.Logger] = None,
            use_abs_diff: bool = False
    ) -> IamDataFrame:
        """Calculate the absolute difference between the data and target timeseries.

        Parameters
        ----------
        data : IamDataFrame
            The data to be compared.
        target : IamDataFrame
            The target timeseries.
        meta: Optional[pd.DataFrame], optional
            A metadata DataFrame to be included in the result. If None,
            `data.meta` will be used as the metadata for the result. Optional,
            by default None. If you want the result to have no metadata, pass an
            empty DataFrame.
        logger : Optional[logging.Logger], optional
            A logger to use for logging messages. Optional, by default None.

        Returns
        -------
        IamDataFrame
            The result of the comparison.
        """
        result_data: pd.Series = pyam_helpers.as_pandas_series(data) \
            - pyam_helpers.as_pandas_series(target)
        if use_abs_diff:
            result_data = result_data.abs()
        if meta is None:
            meta = data.meta
        return pyam.IamDataFrame(result_data, meta=meta)
    ###END def IamDataFrameVariableDiff._compare_func

###END class IamDataFrameVariableDiff
