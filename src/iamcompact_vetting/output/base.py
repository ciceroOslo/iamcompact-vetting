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
from abc import ABC, abstractmethod
from collections.abc import Sequence, Mapping
import enum
import typing as tp

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


class NoWriterError(Exception):
    """Raised when the `.write` method of a `NoWriter` instance is called."""
    pass
###END abstract class ResultsWriter

class NoWriter(ResultsWriter[tp.Any, None]):
    """ResultsWriter that can be used when no writer is wanted.

    If the `.write` method of this class is called, a `NoWriterError` is
    raised.

    Init Parameters
    ---------------
    message : str
        Message to be printed when the `.write` method is called.
    """
    def __init__(
            self,
            *,
            message: str = 'No writer has been set for this output.',
    ):
        self.message: str = message
    ###END def NoWriter.__init__
    def write(self, output_data: tp.Any) -> None:
        raise NoWriterError(self.message)
    ###END def NoWriter.write
###END class NoWriter

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


class CTCol(enum.StrEnum):
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


class SummaryColumnSource(enum.Enum):
    """Specifies where to get the column names of summary DataFrames from."""
    DICT_KEYS = enum.auto()
    CRITERIA_NAMES = enum.auto()
###END enum class SummaryColumnSource

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
    ) -> dict[str, pd.DataFrame]:
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

    def prepare_summary_output(
            self,
            data: pyam.IamDataFrame,
            /,
            criteria: tp.Optional[Mapping[str, CriterionTargetRangeTypeVar]] \
                = None,
            *,
            prepared_output: tp.Optional[dict[str, pd.DataFrame]] = None,
            columns: tp.Optional[Mapping[str, Sequence[CTCol]]] = None,
            column_titles: tp.Optional[Mapping[str, Mapping[CTCol, str]]] \
                = None,
            column_name_source: tp.Optional[SummaryColumnSource|str] = None,
            confirm_levels: tp.Optional[Sequence[str]] = None,
            drop_levels: tp.Optional[str|Sequence[str]] = None,
    ) -> dict[str, pd.DataFrame]:
        """Create DataFrame with values from one column for all criteria.
        
        Returns a dict of DataFrames, where each DataFrame contains the values
        for a single column from the output from each criterion, and has each
        criterion along the columns.

        **NB!** The current implementation of this method in practice assumes
        that the `.get_values` method of each criterion will return a `Series`
        with the same index levels, including both level names and level
        ordering, even if the documentation might make it look like that is not
        the case. A future version might take care to do whatever broadcasting,
        level reordering and reindexing that is necessary to align the Series
        properly. But for now you will need to ensure that all the criteria
        return Series with the same index levels, and override them with
        subclasses if necessary.

        Parameters
        ----------
        data : pyam.IamDataFrame
            The data to be used in the output.
        criteria : Mapping[str, CriterionTargetRangeTypeVar], optional
            The criteria to be used in the output. If `None` (default) and
            `prepared_output` is `None`, `self.criteria` will be used.
        prepared_output : Mapping[str, pd.DataFrame], optional
            Already prepared output from `self.prepare_output`. Can be used to
            boost efficiency, as the method will otherwise call
            `self.prepare_output`. If you specify `prepared_output` you must
            ensure that the `criteria` is identical to criteria passed to the
            original call to `prepare_output` that was used to prepare the
            DataFrames. If `columns` is specified, you must also ensure that it
            is identical. `column_titles` will be ignored.
        columns : Mapping[str, Sequence[CTCol]], optional
            The columns to be used in the output. If `None` (default),
            `self._default_columns` will be used.
        column_titles : Mapping[str, Mapping[CTCol, str]], optional
            The column titles to be used in the output. If `None` (default),
            `self._default_column_titles` will be used. The titles will be the
            keys of the returned dict.
        column_name_source : SummaryColumnSource or str, optional
            Where to get the column names of the summary DataFrames from (which
            identify the criteria). If a str, the names will be taken from an
            index level, which must then be present in the Series returned by
            the `.get_values` method of each criterion in `criteria`. **NB!** If
            you pass a string value for `column_name_source`, you will probably
            also need to pass a value for `drop_levels`, to ensure that the
            specified index level is not dropped, since dropping levels takes
            place before obtaining column names. If `column_name_source` is a
            `SummaryColumnSource` enum, the following will be used: 
              * `SummaryColumnSource.DICT_KEYS`: The column names will be
                taken from the dictionary keys of `criteria`.
              * `SummaryColumnSource.CRITERIA_NAMES`: The column names will be
                taken from the `.name` property of each criterion in `criteria`.
            Optional, the deafult is `SummaryColumnSource.DICT_KEYS`.
        drop_levels : str or Sequence[str], optional
            Level names to be dropped from the index of the returned DataFrame
            from each criterion, and not included in the index of the DataFrame
            returned from this method. If `column_name_source` is a string, the
            corresponding level is always dropped (since it is used in the
            column names), and **must be not** included here. Any levels with
            the given names will be dropped, but no error is raised if the given
            names are not present in the indexes of the Series returned by any
            of the criteria in `criteria`. Optional, the default is to drop the
            levels `variable` and the level names given in the
            `.rename_variable_column` attribute of each `CriterionTargetRange`
            instance in `criteria`. If you do not wish to drop any levels, pass
            in an empty tuple or list.
        confirm_levels : Sequence[str], optional
            Level names to be confirmed to be present in the index of the
            returned DataFrame from each criterion, after dropping the levels
            specified in `drop_levels` and any that are implicitly dropped based
            on `column_name_source`. If given, each DataFrame must have
            exactly the index level names given by this parameter. If you do not
            wish to confirm levels, pass in an empty tuple or list. Note that
            if there are discrepancies in the level names across criteria, this
            method is likely to return unexpected results. Optional, by default
            equal to `("model", "scenario", "region")`. If a level name is 
        """
        if criteria is None:
            criteria = self.criteria
        if confirm_levels is None:
            confirm_levels = ('model', 'scenario', 'region')
        else:
            confirm_levels = tuple(confirm_levels)
        if column_name_source is None:
            column_name_source = SummaryColumnSource.DICT_KEYS
        if drop_levels is None:
            drop_levels = ('variable',) + tuple(
                _crit.rename_variable_column for _crit in criteria.values()
                    if isinstance(_crit.rename_variable_column, str)
            )
        if isinstance(drop_levels, str):
            drop_levels = (drop_levels,)
        drop_levels = tuple(drop_levels)
        if not isinstance(column_name_source, SummaryColumnSource):
            if not isinstance(column_name_source, str):
                raise TypeError(
                    f"`column_name_source` must be either a `str` or "
                    f"`SummaryColumnSource` enum, not {type(column_name_source)}"
                )
            confirm_levels = confirm_levels + (column_name_source,)
        full_output: dict[str, pd.DataFrame] = prepared_output \
                if prepared_output is not None \
                    else self.prepare_output(
                        data,
                        criteria=criteria,
                        columns=columns,
                        column_titles=column_titles,
                    )
        # Detect column names, check that all DataFrames have the same columns,
        # and that the number of column names is equal to the number of elements
        # in `columns` if it is not `None`. Start with the column names of the
        # first DataFrame, check the number of columns, then compare all other
        # DataFrames to that.
        output_columns: tuple[str, ...] \
            = tuple(next(iter(full_output.values())).columns)
        if columns is not None:
            if len(columns) != len(output_columns):
                raise ValueError(
                    f'Expected the number of columns in `columns` to be '
                    f'equal to the number of columns in the DataFrame returned '
                    f'by `prepare_output`. Expected {len(columns)}, but found '
                    f'{len(output_columns)}.'
                )
        output_column_set: set[str] = set(output_columns)
        for _key, _df in full_output.items():
            if (len(_df.columns) != len(output_columns)) \
                    or (set(_df.columns) != output_column_set):
                raise ValueError(
                    f'Expected all columns in the DataFrames returned by '
                    '`prepare_output` to have the same names. Expected '
                    f'column names {output_columns}, but found '
                    f'{_df.columns} for the criterion given by key '
                    f'"{_key}".'
                )
        if len(drop_levels) > 0:
            full_output = {
                _key: _df.droplevel(drop_levels)
                    for _key, _df in full_output.items()
            }
        if len(confirm_levels) > 0:
            for _key, _df in full_output.items():
                if not set(_df.index.names) == set(confirm_levels):
                    raise ValueError(
                        f'Expected all index levels in `confirm_levels` to be '
                        f'present in the index of the DataFrame returned by '
                        f'`prepare_output` for the criterion given by key '
                        f'"{_key}". Expected index levels {confirm_levels}, '
                        f'but found {set(_df.index.names)}.'
                    )
        # Create a helper function to transform the output from a single
        # criterion. Should be a Series, where the correct column has already
        # been selected. The resulting DataFrames will be concatenated
        # horizontally
        def _transform_crit_output(
                _crit_output: pd.Series,
                _column_name_source: SummaryColumnSource|str,
                _dict_key: str,
                _name: str,
        ) -> pd.DataFrame:
            match _column_name_source:
                case SummaryColumnSource.DICT_KEYS:
                    return pd.DataFrame(
                        data=_crit_output,
                        index=_crit_output.index,
                        columns=[_dict_key],
                    )
                case SummaryColumnSource.CRITERIA_NAMES:
                    return pd.DataFrame(
                        data=_crit_output,
                        index=_crit_output.index,
                        columns=[_name],
                    )
                case levelname if isinstance(levelname, str):
                    return _crit_output.unstack(level=levelname)
                case _:
                    raise TypeError(
                        f'`column_name_source` must be either a `str` or a '
                        '`SummaryColumnSource` enum, not '
                        f'{type(column_name_source)}.'
                    )

        return_dict: dict[str, pd.DataFrame] = {
            _column: tp.cast(pd.DataFrame, pd.concat(
                [
                    _transform_crit_output(
                        _crit_output=_df[_column],
                        _column_name_source=column_name_source,
                        _dict_key=_key,
                        _name=criteria[_key].name,
                    ) for _key, _df in full_output.items()
                ],
                axis=1,
            )) for _column in output_columns
        }
        return return_dict
###END class MultiCriterionTargetRangeOutput
