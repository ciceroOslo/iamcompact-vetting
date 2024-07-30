"""Base classes that extend pea.Criterion to entire IAM output timeseries.

The classes in this module are used to rate year-by-year differences between
a given IAM output timeseries and a reference timeseries. This replaces
previously started work that aimed to do the same through an entirely separate
class hierarchy (in the module `iam_vetter_core`). The new approach instead
leverages and integrates with the existing `Criterion` class and related
methods of the `pathways-ensemble-analysis` package (`pea`).
"""
import typing as tp
from collections.abc import Iterable, Callable
import functools
import logging

import pyam
import pandas as pd
import pathways_ensemble_analysis as pea
from pathways_ensemble_analysis.criteria.base import Criterion

from iamcompact_vetting import pyam_helpers
from iamcompact_vetting.iam.dims import IamDimName, DIM



class TimeseriesRefCriterion(Criterion):
    """Base class for criteria that compare IAM output timeseries.

    This class is a subclass of `pea.Criterion` that is designed to compare
    year-by-year differences between a given IAM output timeseries and a
    reference timeseries. Unlike most `pea.Criterion` subclasses and methods,
    which return a single value for an entire model/scenario or a Series with a
    single value for each model/scenario, the methods of this class return a
    Series with a value for each year for a single model/scenario pair, or a
    Series with an additional index level for the year and values for each year
    for each model/scenario pair.

    Init parameters
    ---------------
    criterion_name : str
        The name of the criterion.
    reference : pyam.IamDataFrame
        The reference timeseries to compare against.
    comparison_function : callable
        The function to use to compare the timeseries. The function should take
        two `pyam.IamDataFrame` objects as positional arguments and return a
        `pandas.Series` with comparison values (like differences, ratios or
        other difference measures). The first `IamDataFrame` should be one being
        compared to (`self.reference`) and the second one the object to be
        compared. The design of this base class implicitly assumes that the
        returned `Series` has the same index as the intersection of the indexes
        of the two `IamDataFrame`s (after broadcasting), but this is not
        enforced. You can also pass functions that compare the underlying
        `pandas.Series` objects, which can be significantly faster, by using the
        `pyam_series_comparison` decorator (in this module, see separate
        docstring).
    broadcast_dims : iterable of str, optional
        The dimensions to broadcast over when comparing the timeseries. This
        should be a subset of the dimensions of the `reference` timeseries.
        `reference` should only have one value for each of these dimensions, or
        a `ValueError` will be raised. `reference` will be broadcast to the
        values of thsese dimensions in the `IamDataFrame` being comopared to
        before being passed to `comparison_function`. Optional, defaults to
        `['model', 'scenario']`.
    rating_function : callable, optional
        The function to use to rate the comparison values. This function should
        take a `pandas.Series` and return a single value. Optional, defaults to
        absolute max.

    Methods
    -------
    get_values(iamdf: pyam.IamDataFrame) -> pd.Series
        Returns the comparison values for the given `IamDataFrame`, after
        broadcasting and other processing and applying
        `self.comparison_function`. The values are returned as a
        `pandas.Series`, but in a form that can be converted directly to a
        `pyam.IamDataFrame` by passing it to the `pyam.IamDataFrame` __init__
        method. The returned `Series` from `TimeSeriesRefCriterion.get_values`
        will generally have the same index as the intersection of the indexes of
        the `IamDataFrame` and the `reference` timeseries (after broadcasting),
        but this is not enforced.
    rate(s: pd.Series) -> pd.Series
        Rates the comparison values in the given `pandas.Series` using
        `self.rating_function`. The returned `Series` will usually be an
        aggregate over years, and hence have an index without the 'year' level.
    """

    def __init__(
            self,
            criterion_name: str,
            reference: pyam.IamDataFrame,
            comparison_function: tp.Callable[
                [pyam.IamDataFrame, pyam.IamDataFrame], pd.Series
            ],
            broadcast_dims: Iterable[str] = ('model', 'scenario'),
            rating_function: Callable[[pd.Series], pd.Series] = \
                lambda s: s.abs().max(),
    ):
        self.reference: pyam.IamDataFrame = reference
        self.comparison_function: Callable[
            [pyam.IamDataFrame, pyam.IamDataFrame], pd.Series
        ] = comparison_function
        self.broadcast_dims: list[str] = list(broadcast_dims)
        self.rating_function = rating_function
        super().__init__(
            criterion_name=criterion_name,
            region='*',
            rating_function=rating_function
        )
    ###END def TimeseriesRefCriterion.__init__

    def get_values(self, iamdf: pyam.IamDataFrame) -> pd.Series:
        """Return comparison values for the given `IamDataFrame`.

        This method returns the comparison values for the given `IamDataFrame`,
        after broadcasting and other processing and applying
        `self.comparison_function`. The values are returned as a
        `pandas.Series`, but in a form that can be converted directly to a
        `pyam.IamDataFrame` by passing it to the `pyam.IamDataFrame` __init__
        method. The returned `Series` from `TimeSeriesRefCriterion.get_values`
        will generally have the same index as the intersection of the indexes of
        the `IamDataFrame` and the `reference` timeseries (after broadcasting),
        but this is not enforced.

        Parameters
        ----------
        iamdf : pyam.IamDataFrame
            The `IamDataFrame` to get comparison values for.

        Returns
        -------
        pd.Series
            The comparison values for the given `IamDataFrame`.
        """
        ref = pyam_helpers.broadcast_dims(self.reference, iamdf,
                                          self.broadcast_dims)
        return self.comparison_function(iamdf, ref)
    ###END def TimeseriesRefCriterion.get_values
    
###END class TimeseriesRefCriterion


@tp.overload
def pyam_series_comparison(
        func: Callable[[pd.Series, pd.Series], pd.Series],
        *,
        match_units: bool = True
) -> Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]:
    ...
@tp.overload
def pyam_series_comparison(
        *,
        match_units: bool = True
) -> Callable[
        [Callable[[pd.Series, pd.Series], pd.Series]],
        Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]
]:
    ...
def pyam_series_comparison(
        func: tp.Optional[Callable[[pd.Series, pd.Series], pd.Series]] = None,
        *,
        match_units: bool = True
) -> Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series] | \
    Callable[
        [Callable[[pd.Series, pd.Series], pd.Series]],
        Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]
    ]:
    """Convert function comparing `Series` to one comparing `IamDataFrame`s.
    
    The function is designed to be used as a decorator. The decorated function
    must take two `pandas.Series` objects as positional arguments and return a
    `pandas.Series`. By default, the units of the first `Series` will be
    converted to the units of the second `Series` before the comparison is
    made, using the `pyam_helpers.match_units` function. If you are sure that
    the units are already consistent, you can pass `match_units=False` to the
    decorator (an optional keyword argument) to skip this step and improve
    performance.
    """
    def decorator(
            _func: Callable[[pd.Series, pd.Series], pd.Series]
    ) -> Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]:
        @functools.wraps(_func)
        def wrapper(iamdf1: pyam.IamDataFrame, iamdf2: pyam.IamDataFrame) \
                -> pd.Series:
            if match_units:
                iamdf1 = pyam_helpers.make_consistent_units(
                    df=iamdf1,
                    match_df=iamdf2
                )
            return _func(
                pyam_helpers.as_pandas_series(iamdf1),
                pyam_helpers.as_pandas_series(iamdf2)
            )
        return wrapper
    if func is None:
        return decorator
    return decorator(func)
###END def pyam_series_comparison
