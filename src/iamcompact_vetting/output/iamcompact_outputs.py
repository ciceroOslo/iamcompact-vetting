"""ResultOutput items that provide assessment outputs for IAM COMPACT."""

import pandas as pd
import pyam

from .base import (
    CriterionTargetRangeOutput,
    MultiCriterionTargetRangeOutput,
    NoWriter,
)
from .excel import (
    MultiDataFrameExcelWriter,
    make_valid_excel_sheetname,
)
from ..targets.ar6_vetting_targets import vetting_targets
from ..targets.target_classes import CriterionTargetRange



ar6_vetting_target_range_output: MultiCriterionTargetRangeOutput[
    CriterionTargetRange,
    MultiDataFrameExcelWriter | NoWriter
] = MultiCriterionTargetRangeOutput(
    criteria={_crit.name: _crit for _crit in vetting_targets},
    writer=NoWriter(),
)
