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

import pandas as pd
import xlsxwriter

from .base import (
    ResultOutput,
    ResultsWriter,
    OutputDataTypeVar,
    WriteReturnTypeVar,
)


ExcelOutputSpec: tp.TypeAlias \
    = Path | str | BytesIO | xlsxwriter.Workbook


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

    _workbook: xlsxwriter.Workbook

    def __init__(
            self,
            file: ExcelOutputSpec,
    ) -> None:
        """
        Parameters
        ----------
        file : ExcelOutputSpec
            Path or str specifying the Excel file to write to, or a pre-existing
            `xlsxwriter.Workbook` object. Can also write to an in-memory
            `BytesIO` object.
        """
        if not isinstance(file, xlsxwriter.Workbook):
            if not isinstance(file, (Path, str, BytesIO)):
                raise TypeError(
                    '`file` must be a `Path`, `str`, `BytesIO`, or '
                    '`xlsxwriter.Workbook` object.'
                )
            self._workbook = xlsxwriter.Workbook(file)
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


class DataFrameExcelWriter(ExcelWriterBase[pd.DataFrame, None]):

    sheet_name: str

    def __init__(
            self,
            file: ExcelOutputSpec|pd.ExcelWriter,
            sheet_name: str,
            style: tp.Optional[ExcelDataFrameStyle] = None,
    ) -> None:
        """
        Parameters
        ----------
        file : ExcelOutputSpec
            Path or str specifying the Excel file to write to, or a pre-existing
            `xlsxwriter.Workbook` or `pandas.ExcelWriter` object. Can also write
            to an in-memory `BytesIO` object.If using a `pandas.ExcelWriter`
            object, it must use `xlsxwriter` as its engine.
        sheet_name : str
            The name of the sheet to write the data to.
        style : ExcelDataFrameStyle, optional
            The style to apply to the data in the sheet. Optional, defaults to
            None.
        """
        if isinstance(file, pd.ExcelWriter):
            if not isinstance(file.book, xlsxwriter.Workbook):
                raise ValueError(
                    'When using a `pandas.ExcelWriter` object, its `.book` '
                    'attribute must be an `xlsxwriter.Workbook` object, i.e., '
                    'it must use `xlsxwriter` as its engine.'
                )
            super().__init__(file=file.book)
        else:
            super().__init__(file)
        self.sheet_name: str = sheet_name
    ###END def DataFrameExcelWriter.__init__

    def write(
            self,
            data: pd.DataFrame,
            /,
            sheet_name: tp.Optional[str] = None,
    ) -> None:
        """Write the given `pandas.DataFrame` to the workbook.
        
        Parameters
        ----------
        data : pd.DataFrame
            The data to write to the workbook.
        sheet_name : str, optional
            The name of the sheet to write the data to. Optional, defaults to
            `self.sheet_name` (the `sheet_name` passed to `__init__`).
        """
        if sheet_name is None:
            sheet_name = self.sheet_name
        data.to_excel(self._workbook, sheet_name=sheet_name)
    ###END def DataFrameExcelWriter.write

###END class DataFrameExcelWriter
