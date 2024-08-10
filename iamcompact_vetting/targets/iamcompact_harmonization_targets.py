"""Vetting against harmonisation recommendations in IAM COMPACT."""
import typing as tp
from collections.abc import Callable

import pyam
import pandas as pd
import numpy as np

from .target_classes import CriterionTargetRange
from ..pea_timeseries.timeseries_criteria_core import (
    TimeseriesRefCriterion,
    AggFuncTuple,
    AggDimOrder,
    get_ratio_comparison,
)
from ..data import d43



class IamCompactHarmonizationRatioCriterion(TimeseriesRefCriterion):
    """TimeseriesRefCriterion for IAM COMPACT harmonisation.

    The values returned by the `.get_values` method are the ratios of the values
    in the data to be vetted divided by the harmonized reference values. `np.inf` is
    returned where the reference value is zero but the value to be vetted is not, and
    `1.0` is returned if they are both zero.
    """

    def __init__(
        self,
        criterion_name: str,
        reference: pyam.IamDataFrame,
        comparison_function: tp.Optional[
            Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]
        ] = None,
        region_agg: TimeseriesRefCriterion.AggFuncArg = 'max',
        time_agg: TimeseriesRefCriterion.AggFuncArg = 'max',
        broadcast_dims: tp.Iterable[str] = ('model', 'scenario'),
        rating_function: Callable[[float], float] = lambda x: x,
    ):
        if comparison_function is None:
            comparison_function = get_ratio_comparison(
                div_by_zero_value=np.inf,
                zero_by_zero_value=1.0,
            )
        super().__init__(
            criterion_name=criterion_name,
            reference=reference,
            comparison_function=comparison_function,
            region_agg=region_agg,
            time_agg=time_agg,
            broadcast_dims=broadcast_dims,
            rating_function=rating_function,
        )
    ###END def IamCompactHarmonizationRatioCriterion.__init__

###END class IamCompactHarmonizationRatioCriterion


gdp_pop_harmonization_criterion = IamCompactHarmonizationRatioCriterion(
    criterion_name='gdp_pop_harmonisation',
    reference=d43.get_gdp_pop_harmonisation_iamdf(with_iso3_column=False),
    rating_function=lambda x: np.sqrt(np.log10(x)**2),  # Order-of-magnitude analogue
                                                        # of RMS distance for a ratio comparison
)
"""IamCompactHarmonisationRatioCriterion for gdp/population harmonization.

The values returned by the `.get_values` method are the ratios of the values
in the data to be vetted divided by the harmonized reference values. `np.inf` is
returned where the reference value is zero but the value to be vetted is not, and
`1.0` is returned if they are both zero.
"""
