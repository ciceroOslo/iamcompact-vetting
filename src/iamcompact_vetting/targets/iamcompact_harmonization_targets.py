"""Vetting against harmonisation recommendations in IAM COMPACT."""
from collections.abc import Callable
import functools
import typing as tp

import pandas as pd
import pyam
import numpy as np

from .target_classes import (
    CriterionTargetRange,
    RelativeRange,
)
from ..pea_timeseries.timeseries_criteria_core import (
    AggDims,
    TimeseriesRefCriterion,
    get_ratio_comparison,
)
from ..pea_timeseries.dims import DIM
from ..data import d43



IAMCOMPACT_HARMONIZATION_DEFAULT_TOLERANCE: tp.Final[float] = 0.02


class IamCompactHarmonizationRatioCriterion(TimeseriesRefCriterion):
    """TimeseriesRefCriterion for IAM COMPACT harmonisation.

    The values returned by the `.get_values` method are the ratios of the values
    in the data to be vetted divided by the harmonized reference values. `np.inf` is
    returned where the reference value is zero but the value to be vetted is not, and
    `1.0` is returned if they are both zero.

    By default, the class only aggregates over time, not regions, so that the
    Series returned by the `.get_values` method are the includes values per
    region, and not just aggregated to one value per model and scenario. This
    behavior can be changed through the `default_agg_dims` parameter.
    """

    def __init__(
        self,
        criterion_name: str,
        reference: pyam.IamDataFrame,
        comparison_function: tp.Optional[
            Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]
        ] = None,
        region_agg: tp.Optional[TimeseriesRefCriterion.AggFuncArg] = None,
        time_agg: tp.Optional[TimeseriesRefCriterion.AggFuncArg] = None,
        default_agg_dims: tp.Optional[AggDims] = None,
        broadcast_dims: tp.Optional[tp.Iterable[str]] = None,
        rating_function: tp.Optional[Callable[[float], float]] = None,
    ):
        if comparison_function is None:
            comparison_function = get_ratio_comparison(
                div_by_zero_value=np.inf,
                zero_by_zero_value=1.0,
            )
        if region_agg is None:
            region_agg = 'max'
        if time_agg is None:
            time_agg = 'max'
        if default_agg_dims is None:
            default_agg_dims = AggDims.TIME
        if broadcast_dims is None:
            broadcast_dims = ('model', 'scenario')
        if rating_function is None:
            rating_function = lambda x: x
        super().__init__(
            criterion_name=criterion_name,
            reference=reference,
            comparison_function=comparison_function,
            region_agg=region_agg,
            time_agg=time_agg,
            default_agg_dims=default_agg_dims,
            broadcast_dims=broadcast_dims,
            rating_function=rating_function,
        )
    ###END def IamCompactHarmonizationRatioCriterion.__init__

    def compare(self,
            iamdf: pyam.IamDataFrame,
            filter: tp.Optional[tp.Dict[str, tp.Any]] = None,
            join: tp.Literal['inner', 'outer', 'reference', 'input', None] \
                = 'inner',
    ) -> pd.Series:
        """Return comparison values for the given `IamDataFrame`.

        This method acts like the superclass method
        `TimeseriesRefCriterion.compare`, except that it drops any regions that
        are not present in the reference dataset `self.reference`, and reindexes
        the result to match `self.reference` on the variables, the input data
        `iamdf` on the model, scenario and region dimensions, filling with nans
        for any variables that are not present in the input data.

        Parameters
        ----------
        iamdf : pyam.IamDataFrame
            The `IamDataFrame` to get comparison values for.

        Returns
        -------
        pd.Series
            The comparison values for the given `IamDataFrame`.
        """
        iamdf_filtered: pyam.IamDataFrame = iamdf.filter(
            region=self.reference.region,
            variable=self.reference.variable,
        )  # pyright: ignore[reportAssignmentType]
        comparison_series: pd.Series = super().compare(
            iamdf_filtered,
            filter=filter if filter is not None else {
                DIM.REGION: iamdf_filtered.region,
                DIM.TIME: getattr(iamdf_filtered, DIM.TIME),
            },
            join=join,
        )
        return comparison_series
    ###END def IamCompactHarmonizationRatioCriterion.compare

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


class IamCompactHarmonizationTarget(CriterionTargetRange):
    """Target for IAM COMPACT harmonisation.

    By default, the target assumes that the `.get_value` method of the criterion
    that is passed in returns the ratio of the data to be vetted to the
    harmonized reference values. By default, the target range is set to accept
    a value up to `IAMCOMPACT_HARMONIZATION_TOLERANCE` lower or higher than 1.0.

    The `.get_distance` method by default returns the difference between the
    values returned by the `.get_value` method of `criterion` and 1.0. This can
    be overridden by passing a `distance_func` parameter to the `__init__`
    method.

    The `__init__` method sets appropriate values for the IAM COMPACT
    harmonization vetting, but allow all parameters from the parent class
    `CriterionTargetRange` to be adjusted by passing them as keyword arguments.
    See the `CriterionTargetRange` class docstring for the full list of valid
    parameters.
    """

    def _iam_compact_harmonization_default_distance_func(
            self,
            value: float,
    ) -> float:
        return value - self.target
    ###END def IamCompactHarmonizationTarget \
    #     ._iam_compact_harmonization_default_distance_func

    def __init__(
            self,
            criterion: IamCompactHarmonizationRatioCriterion,
            target: tp.Optional[float] = None,
            range: tp.Optional[tuple[float, float]] = None,
            *,
            distance_func: tp.Optional[tp.Callable[[float], float]] \
                = None,
            **kwargs,
    ):
        """Init method.

        See the docstring of `CriterionTargetRange.__init__` for explanation
        of parameters and full list of keyword arguments.
        """
        if target is None:
            target = 1.0
        if range is None:
            range = RelativeRange(
                lower=1.0-IAMCOMPACT_HARMONIZATION_DEFAULT_TOLERANCE,
                upper=1.0+IAMCOMPACT_HARMONIZATION_DEFAULT_TOLERANCE,
            )
        super().__init__(
            criterion=criterion,
            target=target,
            range=range,
            distance_func=distance_func
                if distance_func is not None
                else self._iam_compact_harmonization_default_distance_func,
            **kwargs
        )
    ###END def IamCompactHarmonizationTarget.__init__
