"""Base classes and core functionality for vettting pyam.IamDataFrame instances."""
import typing as tp
import abc
import enum
from collections.abc import Mapping, Callable, Sequence
import dataclasses

from pyam import IamDataFrame
import pyam

from iamcompact_vetting.vetter_base import (
    Vetter,
    VettingResultsBase,
    TargetCheckResult,
    TargetCheckVetter
)



TIMEDIM: str = 'year'
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


class IamDataFrameTargetVetter(
    TargetCheckVetter[
        IamDataFrame,
        IamDataFrame,
        MeasureType,
        StatusType,
        IamDataFrameTargetCheckResult[MeasureType, StatusType]
    ],
    tp.Generic[MeasureType, StatusType]
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
            filter: Mapping[str, tp.Any] \
                | Callable[[IamDataFrame], IamDataFrame],
            target: IamDataFrame,
            compare_func: Callable[[IamDataFrame, IamDataFrame], MeasureType],
            results_type: tp.Type[IamDataFrameTargetCheckResult[MeasureType, StatusType]],
            status_mapping: Callable[[MeasureType], StatusType]
    ):
        """
        Parameters
        ----------
        filter : Mapping[str, tp.Any] | Callable[[IamDataFrame], IamDataFrame]
            A filter to apply to the data before checking it against the target.
            Can be a callable that takes an `IamDataFrame` as input and returns
            an `IamDataFrame` as output, or a dict of filters to pass to the
            `IamDataFrame.filter` method.
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

    def check(self, data: IamDataFrame) -> IamDataFrameTargetCheckResult[MeasureType, StatusType]:
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


@dataclasses.dataclass(kw_only=True, frozen=True)
class IamDataFrameTimeseriesComparisonSpec:
    """Specification for comparing two IamDataFrame instances as timeseries.
 
    Attributes
    ----------
    compare_func : Callable[[IamDataFrame, IamDataFrame], IamDataFrame]
        The function that takes the data and target, respectively, as the first
        two parameters, and returns a new `IamDataFrame` with the result. The
        data will be filtered by the `filter` attribute of an instance of
        `IamDataFrameTimeseriesVetter` before being passed to this function.
        The values in the dimension(s) of the data given by the `match_dim`
        attribute must match the values in the same dimension(s) of the target.
        The values of the target in other dimensions will be broadcast to match
        the data (note that the target must have only one unique value in each
        of those dimensions, or a `ValueError` will be raised).
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
    compare_func: Callable[[IamDataFrame, IamDataFrame], IamDataFrame]
    match_dims: tuple[str, ...]
    match_time: bool = True
    dim_prefix: Mapping[str, str] = dataclasses.field(default_factory=dict)
    dim_suffix: Mapping[str, str] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if self.match_time:
            super().__setattr__('match_dims', (*self.match_dims, TIMEDIM))
            # Have to use super().__setattr__ to circumvent the frozen attribute
###END class IamDataFrameTimeseriesComparisonSpec


class IamDataFrameTimeseriesVetter(
    IamDataFrameTargetVetter[IamDataFrame, StatusType],
    tp.Generic[StatusType]
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
    comparisons: list[IamDataFrameTimeseriesComparisonSpec]

    @property
    def target(self) -> IamDataFrame:
        """The target `IamDataFrame` to check against."""
        return self.target_value
    ###END property def IamDataFrameTimeseriesVetter.target

    def __init__(
            self,
            filter: Mapping[str, tp.Any] \
                | Callable[[IamDataFrame], IamDataFrame],
            target: IamDataFrame,
            comparisons: Sequence[IamDataFrameTimeseriesComparisonSpec],
            status_mapping: Callable[[IamDataFrame], StatusType]
    ):
        """
        Parameters
        ----------
        filter : Mapping[str, tp.Any] | Callable[[IamDataFrame], IamDataFrame]
            A filter to apply to the data before checking it against the target.
            Can be a callable that takes an `IamDataFrame` as input and returns
            an `IamDataFrame` as output, or a dict of filters to pass to the
            `IamDataFrame.filter` method.
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
        """
        super().__init__(
            filter=filter,
            target=target,
            compare_func=self._do_comparisons,
            results_type=IamDataFrameTimeseriesCheckResult,
            status_mapping=status_mapping
        )
        self.comparisons = list(comparisons)
    ###END def IamDataFrameTimeseriesVetter.__init__

    @staticmethod
    def _make_one_comparison(
            data: IamDataFrame,
            target: IamDataFrame,
            comparison: IamDataFrameTimeseriesComparisonSpec
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
                                     if _dim not in comparison.match_dims]
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
