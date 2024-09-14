"""ResultOutput items that provide assessment outputs for IAM COMPACT."""
from collections.abc import Mapping
import typing as tp

import pandas as pd
import pyam

from .base import (
    CriterionTargetRangeOutput,
    CTCol,
    MultiCriterionTargetRangeOutput,
    NoWriter,
)
from .excel import (
    MultiDataFrameExcelWriter,
    make_valid_excel_sheetname,
)
from ..targets.ar6_vetting_targets import vetting_targets as ar6_vetting_targets
from ..targets.target_classes import CriterionTargetRange



class IamCompactMultiTargetRangeOutput(
    MultiCriterionTargetRangeOutput[
        CriterionTargetRange,
        MultiDataFrameExcelWriter | NoWriter
    ]
):
    """MultiCriterionTargetRangeOutput subclass for IAM COMPACT.

    Used to produce the output for the IPCC AR6 vetting checks. The class sets
    appropriate defaults and overrides to the MultiCriterionTargetRangeOutput
    superclass, but does not introduce new methods or other functionality.

    By default, the output will include the `INRANGE` and `VALUE` columns, which
    will include the pass/fail status of each criterion and the value of the
    assessed variable/parameter, respectively. By default, the columns will have
    the names `"Passed"` and `"Value"`, respectively. This can be overridden by
    keyword arguments passed to the superclass.

    Init Parameters
    ---------------
    criteria : Mapping[str, CriterionTargetRange]
        Mapping of criterion names to CriterionTargetRange instances that define
        the vetting checks to be performed. The keys of the dictionary are used
        as keys in the output. When writing output to Excel, the same titles
        will be truncated to at most 31 characters and used as names for the
        worksheets in the Excel file.
    writer : MultiDataFrameExcelWriter or NoWriter, optional
        Writer that will be used to write the output to an Excel file. If not
        provided, a NoWriter instance will be used, and calling the
        `write_output` or `write_results` method will raise an exception.
    **kwargs
        Additional keyword arguments to be passed to the superclass. See the
        documentation of `MultiCriterionTargetRangeOutput` for details.
    """

    _default_columns = [CTCol.INRANGE, CTCol.VALUE]  # Sets defaults, overrides
                                                     # the superclass
    _default_column_titles = {  # Sets defaults, overrides the superclass
        CTCol.INRANGE: 'Passed',
        CTCol.VALUE: 'Value',
    }

    def __init__(
            self,
            criteria: Mapping[str, CriterionTargetRange],
            writer: tp.Optional[MultiDataFrameExcelWriter|NoWriter] = None,
            **kwargs: tp.Unpack[MultiCriterionTargetRangeOutput.InitKwargsType],
    ):
        if writer is None:
            writer = NoWriter()
        super().__init__(criteria=criteria, writer=writer, **kwargs)
    ###END def IamCompactMultiTargetRangeOutput.__init__

###END class IamCompactMultiTargetRangeOutput


# The declaration of ar6_vetting_target_range_output should be changed to use a
# an IamCompactMultiTargetRangeOutput object instead. Keeping it as-is for now
# to use as a model for how to define the IamCompactMultiTargetRangeOutput
# class.
ar6_vetting_target_range_output = IamCompactMultiTargetRangeOutput(
    criteria={_crit.name: _crit for _crit in ar6_vetting_targets},
    writer=NoWriter(),
)
