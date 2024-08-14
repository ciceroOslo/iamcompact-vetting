"""Module for outputting results of timeseries comparisons.

Currently this module only contains classes for writing comparisons between
IAM model results and harmonisation data or other timeseries reference data.
"""
import typing as tp

import pyam
import pandas as pd

from ..targets.iamcompact_harmonization_targets import (
    IamCompactHarmonizationRatioCriterion,
)
from ..pea_timeseries.timeseries_criteria_core import (
    TimeseriesRefCriterion,
)
from ..pea_timeseries.dims import DIM
from .base import (
    ResultOutput,
    ResultsWriter,
    WriteReturnTypeVar,
    WriterTypeVar,
)


TimeseriesRefCriterionTypeVar = tp.TypeVar(
    'TimeseriesRefCriterionTypeVar',
    bound=TimeseriesRefCriterion
)  # Should probably also add `covariant=True`, but need to check with actual
   # behavior whether it's that or `contravariant=True`.

class TimeseriesComparisonFullDataOutput(
    ResultOutput[
        TimeseriesRefCriterionTypeVar,
        pyam.IamDataFrame,
        pd.DataFrame,
        WriterTypeVar,
        WriteReturnTypeVar,
    ]
):
    """Class for outputting full timeseries data from timeseries comparisons.

    The `prepare_output` method of this class takes a `TimeseriesRefCriterion`
    or subclass instance as input, and returns output as a pandas `DataFrame`.
    The `DataFrame` returned by this class is the same as one would get by
    pivoting/unstacking the years of the Series returned by the `get_values`
    method of the `TimeseriesRefCriterion` instance, or by creating a
    `pyam.IamDataFrame` from that Serie` and calling its `.timeseries()` method.
    Subclasses may implement more case-specific behavior and processing.
    """

    def prepare_output(
        self,
        data: pyam.IamDataFrame,
        /,
        criteria: tp.Optional[TimeseriesRefCriterionTypeVar] = None,
    ) -> pd.DataFrame:
        """Prepare the output data for writing.

        Parameters
        ----------
        criterion : TimeseriesRefCriterion
            The criterion to be used to prepare the output data.

        Returns
        -------
        pd.DataFrame
            The output data to be written.
        """
        if criteria is None:
           criteria = self.criteria
        comparison_result: pd.Series = criteria.compare(data)
        timeseries_df: pd.DataFrame = \
            comparison_result.unstack(level=DIM.TIME)
        return timeseries_df
    ###END def TimeseriesComparisonFullDataOutput.prepare_output

###END class TimeseriesComparisonFullDataOutput
