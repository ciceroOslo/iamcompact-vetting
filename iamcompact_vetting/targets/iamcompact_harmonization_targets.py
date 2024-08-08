"""Vetting against harmonisation recommendations in IAM COMPACT."""
import typing as tp

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


gdp_pop_harmonization_criterion = TimeseriesRefCriterion(
    criterion_name='gdp_pop_harmonisation',
    reference=d43.get_gdp_pop_harmonisation_iamdf(with_iso3_column=False),
    comparison_function=get_ratio_comparison(
        div_by_zero_value=np.inf,
        zero_by_zero_value=1.0,
    ),
    region_agg='max',
    time_agg='max',
    broadcast_dims=('model', 'scenario'),
    rating_function=lambda x: np.sqrt(np.log10(x)**2),  # Order-of-magnitude analogue
                                                        # of RMS distance for a ratio comparison
)
"""TimeseriesRefCriterion for gdp/population harmonization.

The values returned by the `.get_values` method are the ratios of the values
in the data to be vetted divided by the harmonized reference values. `np.inf` is
returned where the reference value is zero but the value to be vetted is not, and
`1.0` is returned if they are both zero.
"""
