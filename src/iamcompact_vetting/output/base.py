"""Base classes and abstract base classes for creating and writing output.

Classes
-------
ResultOutput
    Abstract base class for creating output from results. Is intended to be take
    results from one instance or a collection of instances of either
    `pathways_ensemble_analysis.Criterion` (including
    `iamcompact_vetting.criteria.TimeseriesRefCriterion`) or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses. Different
    subclasses will implement output for different types and collections of
    these classes. The subclasses should generally implement the
    `prepare_output` method to return a nominally format-independent output data
    structure, and use a `ResultsWriter` subclass instance to write the output
    to a desired format, through the `write` method.
ResultsWriter
    Abstract base class for writing output. Subclasses should implement writing
    to different formats. In most cases, each non-abstract subclass will be
    intended for use with a specific subclass of `ResultOutput` (which in turn
    is designed to be used with a specific instance or collection of instances
    of `pathways_ensemble_analysis.Criterion` or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses).
"""
import typing as tp
from abc import ABC, abstractmethod
from enum import StrEnum
from collections.abc import Sequence, Mapping

import pyam
import pandas as pd

from ..targets.target_classes import CriterionTargetRange

CritTypeVar = tp.TypeVar('CritTypeVar')
"""TypeVar for the type of `Criterion` or `CriterionTargetRange` expected by a
`ResultOutput` subclass."""
CriterionTargetRangeTypeVar = tp.TypeVar(
    'CriterionTargetRangeTypeVar',
    bound=CriterionTargetRange,
)
OutputDataTypeVar = tp.TypeVar('OutputDataTypeVar')
"""TypeVar for the type of data to be output by a `ResultOutput` subclass
through its `prepare_output` method, and to be written by a `ResultsWriter`
through its `write` method."""
WriteReturnTypeVar = tp.TypeVar('WriteReturnTypeVar')
"""TypeVar for the datatype to be returned by the `write` method of a
`ResultsWriter` subclass."""


class ResultsWriter(ABC, tp.Generic[OutputDataTypeVar, WriteReturnTypeVar]):
    @abstractmethod
    def write(self, output_data: OutputDataTypeVar) -> WriteReturnTypeVar:
        """Write the output data to a desired format.

        Parameters
        ----------
        output_data : OutputDataTypeVar
            The data to be written, prepared into the proper data type by a
            `ResultOutput` subclass instance.

        Returns
        -------
        WriteReturnTypeVar
            Appropriate return value for the `write` method defined by a
            subclass. Can be `None` if no return value is desired.
        """
        ...
#END abstract class ResultsWriter

WriterTypeVar = tp.TypeVar('WriterTypeVar', bound=ResultsWriter, covariant=True)
"""TypeVar for the type of `ResultsWriter` subclass to be used by a
`ResultOutput` subclass instance."""

ResultsInputData: tp.TypeAlias = pyam.IamDataFrame | pd.Series
"""Type alias for the type of data that can be used as input to the
`prepare_output` method of a `ResultOutput` class. Currently set to the union
of `pyam.IamDataFrame` and `pandas.Series`. This is the most general type.
Subclasses may be more restrictive."""

ResultsInputDataTypeVar = tp.TypeVar(
    'ResultsInputDataTypeVar',
    bound=ResultsInputData,
)


class ResultOutput(
        ABC,
        tp.Generic[
            CritTypeVar,
            ResultsInputDataTypeVar,
            OutputDataTypeVar,
            WriterTypeVar,
            WriteReturnTypeVar
        ]
):
    """Abstract base class for creating output from results.

    Is intended to be take results from one instance or a collection of
    instances of either `pathways_ensemble_analysis.Criterion` (including
    `iamcompact_vetting.criteria.TimeseriesRefCriterion`) or
    `iamcompact_vetting.targets.CriterionTargetRange` subclasses. Different
    subclasses will implement output for different types and collections of
    these classes. The subclasses should generally implement the
    `prepare_output` method to return a nominally format-independent output
    data structure, and use a `ResultsWriter` subclass instance to write the
    output to a desired format, through the `write` method.
    """

    def __init__(
            self,
            *,
            criteria: CritTypeVar,
            writer: WriterTypeVar,
    ) -> None:
        """
        All parameters are keyword-only, to allow for future changes in the
        number of input parameters.

        Parameters
        ----------
        criteria : CritTypeVar
            The criteria that will be used to produce results that are to be
            output by the `ResultOutput` instance.
        writer : WriterTypeVar
            The writer to be used to write the output.
        """
        self.criteria: CritTypeVar = criteria
        self.writer: WriterTypeVar= \
            writer
    ###END def ResultOutput.__init__

    @abstractmethod
    def prepare_output(
            self,
            data: ResultsInputDataTypeVar,
            /,
            criteria: tp.Optional[CritTypeVar] = None,
            **kwargs
    ) -> OutputDataTypeVar:
        """Prepare the output data for writing.

        The method takes data (in the form of a `pyam.IamDataFrame` or
        `pandas.Series`, or similar data structure required by a given
        subclass), passes it to the instance or instances store in `criteria`,
        and prepares the proper output data structure for writing based on the
        results.

        Parameters
        ----------
        data : ResultsInputDataTypeVar
            The data to be passed to `criteria` before the results are prepared
            into output.
        critera : CritTypeVar, optional
            The criteria instance(s) to be used for processing `data` and
            producing results to be prepared for output. If `None` (default),
            `self.criteria` should be used (which was set by the `__init__`
            method), but subclasses have to implement this. The method in the
            base class is an empty abstract method.
        **kwargs
            Additional keyword arguments that can be used by subclasses.

        Returns
        -------
        OutputDataTypeVar
            The data to be written, prepared into the proper data type by a
            `ResultOutput` subclass instance.
        """
        ...
    ###END def ResultOutput.prepare_output

    def write_output(
            self,
            output: OutputDataTypeVar,
            /,
            writer: tp.Optional[WriterTypeVar] \
                = None,
            **kwargs
    ) -> WriteReturnTypeVar:
        """Write the output data to the format written by `writer`.

        This method is used for result outputs that have already been prepared
        into the proper format, usually by `self.prepare_output`. To write
        outputs directly based on `Criterion` or `CriterionTargetRange`
        instances, use `self.write_rsults` instead.

        Parameters
        ----------
        output : OutputDataTypeVar
            The data to be written, prepared into the proper output data
            structure, usually through `self.prepare_output`.
        writer : tp.Optional[WriterTypeVar]
            The writer to be used to write the output. If `None`, the
            `self.writer` attribute is used.
        **kwargs
            Additional keyword arguments to be passed to `writer.write`.

        Returns
        -------
        WriteReturnTypeVar
            The return value from the `writer.write` method.
        """
        if writer is None:
            writer = self.writer
        return writer.write(output, **kwargs)
    ###END def ResultOutput.write_output

    def write_results(
            self,
            data: ResultsInputDataTypeVar,
            /,
            criteria: tp.Optional[CritTypeVar] = None,
            *,
            writer: tp.Optional[
                WriterTypeVar
            ] = None,
            prepare_output_kwargs: tp.Optional[tp.Dict[str, tp.Any]] = None,
            write_output_kwargs: tp.Optional[tp.Dict[str, tp.Any]] = None,
    ) -> tuple[OutputDataTypeVar, WriteReturnTypeVar]:
        """Write the results to the format written by `writer`.

        Parameters
        ----------
        results : CritTypeVar
            The results to be prepared into the proper data structure through
            `self.prepare_output`, which is then written through
            `self.write_output`, using the `writer` parameter.
        writer : tp.Optional[WriterTypeVar]
            The writer to be used to write the output. If `None`, the
            `self.writer` attribute is used.
        prepare_output_kwargs : dict, optional
            Additional keyword arguments to be passed to `prpare_output`.
        write_output_kwargs : dict, optional
            Additional keyword arguments to be passed to `write_output`.

        Returns
        -------
        WriteReturnTypeVar
            The return value from the `writer.write` method.
        """
        if prepare_output_kwargs is None:
            prepare_output_kwargs = dict()
        if write_output_kwargs is None:
            write_output_kwargs = dict()
        if criteria is None:
            criteria = self.criteria
        output: OutputDataTypeVar = self.prepare_output(
            data,
            criteria=criteria,
            **prepare_output_kwargs,
        )
        write_returnval: WriteReturnTypeVar = \
            self.write_output(output, writer, **write_output_kwargs)
        return (output, write_returnval)
    ###END def ResultOutput.write_results

###END abstract class ResultOutput


class CTCol(StrEnum):
    """Column names for DataFrames received by `CriterionTargetRangeOutput`."""
    INRANGE = 'in_range'
    DISTANCE = 'distance'
    VALUE = 'value'
###END enum CTCol


class CriterionTargetRangeOutput(
        ResultOutput[
            CriterionTargetRangeTypeVar,
            pyam.IamDataFrame,
            pd.DataFrame,
            WriterTypeVar,
            WriteReturnTypeVar,
        ],
):
    """TODO: NEED TO ADD PROPER DOCSTRING"""

    _default_columns: Sequence[CTCol]
    _default_column_titles: Mapping[CTCol, str]

    def __init__(
            self,
            *,
            criteria: CriterionTargetRangeTypeVar,
            writer: WriterTypeVar,
            columns: tp.Optional[Sequence[CTCol]] = None,
            column_titles: tp.Optional[Mapping[CTCol, str]] = None,
    ):
        """TODO: NEED TO ADD PROPER DOCSTRING"""
        super().__init__(criteria=criteria, writer=writer)
        self._default_columns = columns if columns is not None else (
            CTCol.INRANGE,
            CTCol.DISTANCE,
            CTCol.VALUE,
        )
        if column_titles is not None:
            self._default_column_titles = column_titles
        else:
            self._default_column_titles = {
                CTCol.INRANGE: 'Is in target range',
                CTCol.DISTANCE: 'Rel. distance from target',
                CTCol.VALUE: 'Value',
            }
    ###END def CriterionTargetRangeOutput.__init__

    def prepare_output(
            self,
            data: pyam.IamDataFrame,
            /,
            criteria: tp.Optional[CriterionTargetRangeTypeVar] = None,
            *,
            columns: tp.Optional[Sequence[CTCol]] = None,
            column_titles: tp.Optional[Mapping[CTCol, str]] = None,
    ) -> pd.DataFrame:
        """TODO: NEED TO ADD PROPER DOCSTRING"""
        if columns is None:
            columns = self._default_columns
        if column_titles is None:
            column_titles = self._default_column_titles
        if criteria is None:
            criteria = self.criteria
        result_columns: list[pd.Series] = []
        for _col in columns:
            if _col == CTCol.INRANGE:
                result_columns.append(
                    criteria.get_in_range(data).rename(_col)
                )
            elif _col == CTCol.DISTANCE:
                result_columns.append(
                    criteria.get_distances(data).rename(_col)
                )
            elif _col == CTCol.VALUE:
                result_columns.append(
                    criteria.get_values(data).rename(_col)
                )
            else:
                raise ValueError(f'Unrecognized column: {_col!r}')
        results_df: pd.DataFrame = pd.concat(result_columns, axis=1)
        if column_titles is not None:
            results_df = results_df.rename(columns=column_titles)
        return results_df
    ###END def CriterionTargetRangeOutput.prepare_output

###END class CriterionTargetRangeOutput


DataFrameMappingWriterTypeVar = tp.TypeVar(
    'DataFrameMappingWriterTypeVar',
    bound=ResultsWriter[Mapping[str, pd.DataFrame], tp.Any],
)

class MultiCriterionTargetRangeOutput(
        ResultOutput[
            Mapping[str, CriterionTargetRangeTypeVar],
            pyam.IamDataFrame,
            Mapping[str, pd.DataFrame],
            DataFrameMappingWriterTypeVar,
            tp.Any,
        ],
):
    """Class to make output for multiple CriterionTargetRange instances.

    The class takes a dictionary of `CriterionTargetRangeOutput` instances with
    str names as keys, and returns a dictionary of DataFrames, each produced
    using a `CriterionTargetRange` instance to produce the given DataFrame.
    """

    _default_columns: Sequence[CTCol]
    _default_column_titles: dict[CTCol, str]

    def __init__(
            self,
            *,
            criteria: Mapping[str, CriterionTargetRangeTypeVar],
            writer: DataFrameMappingWriterTypeVar,
            columns: tp.Optional[tp.Sequence[CTCol]] = None,
            column_titles: tp.Optional[tp.Dict[CTCol, str]] = None,
    ):
        """TODO: NEED TO ADD PROPER DOCSTRING"""
        super().__init__(criteria=criteria, writer=writer)
        self._default_columns = columns if columns is not None else (
            CTCol.INRANGE,
            CTCol.DISTANCE,
            CTCol.VALUE,
        )
        if column_titles is not None:
            self._default_column_titles = column_titles
        else:
            self._default_column_titles = {
                CTCol.INRANGE: 'Is in target range',
                CTCol.DISTANCE: 'Rel. distance from target',
                CTCol.VALUE: 'Value',
            }
    ###END def MultiCriterionTargetRangeOutput.__init__

    def prepare_output(
            self,
            data: pyam.IamDataFrame,
            /,
            criteria: tp.Optional[Mapping[str, CriterionTargetRangeTypeVar]] \
                = None,
            *,
            columns: tp.Optional[Mapping[str, Sequence[CTCol]]] = None,
            column_titles: tp.Optional[Mapping[str, Mapping[CTCol, str]]] \
                = None,
    ) -> Mapping[str, pd.DataFrame]:
        """TODO: NEED TO ADD PROPER DOCSTRING"""
        if criteria is None:
            criteria = self.criteria
        if columns is None:
            columns = {
                _name: self._default_columns
                for _name in criteria
            }
        if column_titles is None:
            column_titles = {
                _name: self._default_column_titles
                for _name in criteria
            }
        return {
            _name: CriterionTargetRangeOutput(
                criteria=_criterion,
                writer=self.writer,
                columns=columns[_name],
                column_titles=column_titles[_name],
            ).prepare_output(data)
            for _name, _criterion in criteria.items()
        }
    ###END def MultiCriterionTargetRangeOutput.prepare_output

###END class MultiCriterionTargetRangeOutput
