"""Module for writing results to an Excel files.

Classes
-------
ExcelWriterBase
    Abstract base class for writing results to an Excel file. The base class
    contains functionality to handle output file Paths and objects from external
    libraries that are used to write the Excel file. Subclasses need to
    implement functionality for how to write and format given result output data
    structures in the Excel file, including the `write` method.
DataFrameExcelWriter
    Class for writing results that are processed into a `pandas.DataFrame`
    object to an Excel file.
"""
import typing as tp
from pathlib import Path
from io import BytesIO
from abc import abstractmethod
import functools
import dataclasses
from collections.abc import Sequence, Mapping

import pandas as pd
import xlsxwriter
from xlsxwriter import Workbook

from .base import (
    ResultOutput,
    ResultsWriter,
    OutputDataTypeVar,
    WriteReturnTypeVar,
)


MAX_SHEET_NAME_LENGTH: tp.Final[int] = 31
"""The maximum permitted length of a sheet name in an Excel file."""

ExcelFileSpec: tp.TypeAlias \
    = Path | str | BytesIO


SHEET_NAME_SUBSTITUTIONS: tp.Final[tp.Dict[str, str]] = {
    "'": "`",
    '*': 'x',
    '/': '-',
    '\\': '_',
    ':': ';',
    '?': '¿',
    '[': '|',
    ']': '|',
}
"""Dictionary mapping characters that are problematic in Excel sheet names to
substitutions."""

def make_valid_excel_sheetname(
        name: str,
        *,
        substitutions: dict[str, str] = SHEET_NAME_SUBSTITUTIONS,
        if_too_long: tp.Literal['raise', 'truncate'] = 'truncate',
        max_length: int = MAX_SHEET_NAME_LENGTH,
) -> str:
    """Make a string a valid Excel worksheet name.
    
    The function replaces characters that cannot be used in an Excel worksheet
    name with substitutions. The default substitutions are given in the
    `SHEET_NAME_SUBSTITUTIONS` dictionary, and are as follows:

        "'": "`"
        '*': 'x'
        '/': '-'
        '\\': '_'
        ':': ';'
        '?': '¿'
        '[': '|'
        ']': '|'

    The function optionally truncates the name if it is longer than
    `max_length` (default 31), or raises a `ValueError` (determinded by the
    `if_too_long` parameter).

    Parameters
    ----------
    name : str
        The name to check and make valid.
    substitutions : dict[str, str], optional
        A dictionary mapping characters that cannot be used in an Excel
        worksheet name to substitutions. The default is given by the
        `SHEET_NAME_SUBSTITUTIONS` dictionary.
    if_too_long : {"raise", "truncate"}, optional
        Whether to raise a `ValueError` if `name` is longer than `max_length`
        characters, or to truncate it if it is too long. The default is
        "truncate".
    max_length : int, optional
        The maximum length of the name. The default is 31 (which is the maximum
        length supported by Excel at the time of writing).

    Returns
    -------
    str
        The name with all problematic characters replaced, and truncated if
        `if_too_long` is "truncate" and `name` is too long.
    """
    if not isinstance(name, str):
        raise TypeError('`name` must be a string.')
    if not isinstance(max_length, int):
        raise TypeError('`max_length` must be an integer.')
    if substitutions is not SHEET_NAME_SUBSTITUTIONS:  # Check key and value types
        if not all (isinstance(_key, str) for _key in substitutions.keys()):
            raise TypeError('All keys in `substitutions` must be strings.')
        if not all (isinstance(_val, str) for _val in substitutions.values()):
            raise TypeError('All values in `substitutions` must be strings.')
    for _key, _val in substitutions.items():
        name = name.replace(_key, _val)
    if len(name) > max_length:
        if if_too_long == 'raise':
            raise ValueError('`name` is too long.')
        if if_too_long == 'truncate':
            name = name[:max_length]
        else:
            raise ValueError(
                '`if_too_long` must be one of "raise" or "truncate".'
            )
    return name
###END def make_valid_excel_sheetname

excel_style_class = functools.partial(
    dataclasses.dataclass,
    slots=True,
    kw_only=True,
)
"""Decorator for defining subclasses of `ExcelStyleBase`."""


@excel_style_class()
class ExcelStyleBase:
    """Base class for defining styles for writing to an Excel file."""
    pass
###END class ExcelStyleBase


@excel_style_class()
class ExcelDataFrameStyle(ExcelStyleBase):
    """Style specifications for writing DataFrames to an Excel file."""
    pass
###END class ExcelDataFrameStyle


class ExcelWriterBase(ResultsWriter[OutputDataTypeVar, WriteReturnTypeVar]):

    _workbook: Workbook

    def __init__(
            self,
            file: ExcelFileSpec | Workbook,
    ) -> None:
        """
        Parameters
        ----------
        file : str, Path, BytesIO, or xlsxwriter.Workbook
            Path or str specifying the Excel file to write to, or a pre-existing
            `xlsxwriter.Workbook` object. Can also write to an in-memory
            `BytesIO` object.
        """
        if not isinstance(file, Workbook):
            if not isinstance(file, (Path, str, BytesIO)):
                raise TypeError(
                    '`file` must be a `Path`, `str`, `BytesIO`, or '
                    '`xlsxwriter.Workbook` object.'
                )
            self._workbook = Workbook(file)
        else:
            self._workbook = file
        ###END def ExcelWriterBase.__init__

    def close(self) -> None:
        """Close and save the Excel workbook.
        
        Can only be called once, there is no analogue of a save method, which is
        a limitation of the `xlsxwriter` package used by this module to write
        Excel files.

        Note that if you called `__init__` with `files` equal to a `BytesIO`
        instance, you will need to write the contents of the `BytesIO` object
        to a file manually if you want to keep the notebook contents.
        """
        self._workbook.close()
    ###END def ExcelWriterBase.close

###END abstract class ExcelWriterBase


class ToExcelKwargs(tp.TypedDict):
    """Keyword arguments for `pandas.DataFrame.to_excel`."""
    sheet_name: str
    no_rep: str
    float_format: str
    columns: Sequence[str]
    header: bool | list[str]
    index: bool
    index_label: str
    startrow: int
    startcol: int
    merge_cells: bool
    engine_kwargs: dict
###END TypedDict class ToExcelKwargs

class DataFrameExcelWriter(ExcelWriterBase[pd.DataFrame, None]):

    _sheet_name: str

    def __init__(
            self,
            file: ExcelFileSpec | pd.ExcelWriter,
            sheet_name: str,
            style: tp.Optional[ExcelDataFrameStyle] = None,
            check_sheet_name_length: bool = True,
    ) -> None:
        """
        Parameters
        ----------
        file : Path, str, BytesIO, or pandas.ExcelWriter
            Path or str specifying the Excel file to write to, or a pre-existing
            `xlsxwriter.Workbook` or `pandas.ExcelWriter` object. Can also write
            to an in-memory `BytesIO` object.If using a `pandas.ExcelWriter`
            object, it must use `xlsxwriter` as its engine.
        sheet_name : str
            The name of the sheet to write the data to.
        style : ExcelDataFrameStyle, optional
            The style to apply to the data in the sheet. Optional, defaults to
            None.
        check_sheet_name_length : bool, optional
            Whether to check that the sheet name is not longer than
            `MAX_SHEET_NAME_LENGTH` (the maximum permitted length of a
            worksheet name in an Excel file). Raises a ValueError if `True` and
            `sheet_name` is longer than the limit. Optional, defaults to True.
            Note that if you set this to `False` and `sheet_name` is longer
            than `MAX_SHEET_NAME_LENGTH`, you will almost certainly get an error
            when you attempt to write the data to the workbook.
        """
        if isinstance(file, pd.ExcelWriter):
            if not isinstance(file.book, Workbook):
                raise ValueError(
                    'When using a `pandas.ExcelWriter` object, its `.book` '
                    'attribute must be an `xlsxwriter.Workbook` object, i.e., '
                    'it must use `xlsxwriter` as its engine.'
                )
            self.excel_writer: pd.ExcelWriter = file
            super().__init__(file=file.book)
        elif isinstance(file, Workbook):
            raise TypeError(
                '`DataFrameExcelWriter` does not support using an existing '
                '`xlsxwriter.Workbook` instance. If you need this '
                'functionality, instead of creating the `Workbook` instance '
                'directly, you need to create a `pandas.ExcelWriter` object '
                'with `engine="xlsxwriter"` and pass that to this method. '
                'You can then get the `Workbook` instance from the '
                '`.book` attribute of the `pandas.ExcelWriter` object.'
            )
        else:
            self.excel_writer: pd.ExcelWriter = \
                pd.ExcelWriter(file, engine='xlsxwriter')
            super().__init__(file=self.excel_writer.book)
        if check_sheet_name_length:
            self.sheet_name = sheet_name
        else:
            if not isinstance(sheet_name, str):
                raise TypeError(
                    '`sheet_name` must be a string. '
                )
            self._sheet_name = sheet_name
    ###END def DataFrameExcelWriter.__init__

    @property
    def workbook(self) -> Workbook:
        assert isinstance(self.excel_writer.book, Workbook)
        return self.excel_writer.book
    ###END property def DataFrameExcelWriter.workbook

    @property
    def sheet_name(self) -> str:
        return self._sheet_name
    ###END property def DataFrameExcelWriter.sheet_name

    @sheet_name.setter
    def sheet_name(self, value: str) -> None:
        if len(value) > MAX_SHEET_NAME_LENGTH:
            raise ValueError(
                f'`sheet_name` must not be longer than '
                f'{MAX_SHEET_NAME_LENGTH} characters. '
                f'`sheet_name` was {len(value)} characters long.'
            )
        self._sheet_name = value
    ###END property def DataFrameExcelWriter.sheet_name

    def write(
            self,
            data: pd.DataFrame,
            /,
            sheet_name: tp.Optional[str] = None,
            to_excel_kwargs: tp.Optional[dict[str, tp.Any]] = None,
    ) -> None:
        """Write the given `pandas.DataFrame` to the workbook.
        
        Parameters
        ----------
        data : pd.DataFrame
            The data to write to the workbook.
        sheet_name : str, optional
            The name of the sheet to write the data to. Optional, defaults to
            `self.sheet_name` (the `sheet_name` passed to `__init__`).
        to_excel_kwargs : dict, optional
            Additional keyword arguments to pass to `pd.DataFrame.to_excel`
            (apart from `sheet_name`). Optional, defaults to None
        """
        if to_excel_kwargs is None:
            to_excel_kwargs = dict()
        if sheet_name is None:
            if 'sheet_name' in to_excel_kwargs:
                sheet_name = to_excel_kwargs.pop('sheet_name')
            else:
                sheet_name = self.sheet_name
        if 'merge_cells' not in to_excel_kwargs:
            to_excel_kwargs['merge_cells'] = False
        if 'engine' in to_excel_kwargs:
            raise ValueError(
                '`DataFrameExcelWriter` does not support specifying the '
                '`engine` argument to `DataFrame.to_excel`. '
            )
        data.to_excel(
            self.excel_writer,
            sheet_name=sheet_name,
            **to_excel_kwargs
        )
    ###END def DataFrameExcelWriter.write

###END class DataFrameExcelWriter
