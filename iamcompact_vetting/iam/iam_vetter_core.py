"""Base classes and core functionality for vettting pyam.IamDataFrame instances."""
import typing as tp
import abc
import enum
from collections.abc import Mapping, Callable

from pyam import IamDataFrame

from iamcompact_vetting.vetter_base import (
    Vetter,
    VettingResultsBase,
    TargetCheckResult,
    TargetCheckVetter
)



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
    """Base class for checking an `IamDataFrame` against a target."""

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
        ...

###END class IamDataFrameTargetVetter
