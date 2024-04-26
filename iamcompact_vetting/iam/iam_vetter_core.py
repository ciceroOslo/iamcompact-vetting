"""Base classes and core functionality for vettting pyam.IamDataFrame instances."""
import typing as tp
import abc

from pyam import IamDataFrame

from iamcompact_vetting.vetter_base import Vetter, VettingResultsBase



ResultsType = tp.TypeVar('ResultsType', bound=VettingResultsBase)


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



