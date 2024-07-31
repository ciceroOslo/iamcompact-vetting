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
import dataclasses
import functools
import logging

import pyam
import pandas as pd
from pandas.core.groupby import SeriesGroupBy
import pathways_ensemble_analysis as pea
from pathways_ensemble_analysis.criteria.base import Criterion

from iamcompact_vetting import pyam_helpers
from iamcompact_vetting.iam.dims import IamDimName, DIM



@dataclasses.dataclass(frozen=True)
class AggFuncTuple:
    """Class to hold an aggregation function and its parameter values.
    
    Fields
    ------
    func : Callable[[SeriesGroupBy], pandas.Series]
        The aggregation function to be applied. This field should not be set
        directly, instead use the `agg_func` parameter of the `__init__`
        method of this class.
    args : Iterable, optional
        The positional arguments to be passed to the aggregation function.
    kwargs : dict, optional
        The keyword arguments to be passed to the aggregation function.

    Init Parameters
    ---------------
    agg_func : Callable[[pandas.Series], float] or str
        The aggregation function to be applied by a pandas `SeriesGroupBy`
        object to aggregate over a given dimension, or the name of a method
        of the pandas `SeriesGroupBy` class.
    """

    class AggFunc(tp.Protocol):
        def __call__(self, s: pd.Series, *args, **kwargs) -> float:
            ...
    class GroupByAggMethod(tp.Protocol):
        def __call__(self, g: SeriesGroupBy, *args, **kwargs) -> pd.Series:
            ...
    ###END class AggFuncTuple.AggFunc

    agg_func: dataclasses.InitVar[AggFunc|str]
    func: GroupByAggMethod = dataclasses.field(init=False)
    args: Iterable[tp.Any] = ()
    kwargs: dict[str, tp.Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self, agg_func: AggFunc|str):
        if isinstance(self.func, str):
            # Check that the attribute named `func` of `pandas.SeriesGroupBy`
            # is a method of `pandas.SeriesGroupBy`.
            if not callable(getattr(SeriesGroupBy, self.func)):
                raise AttributeError(
                    f'`{self.func}` is not a method of `pandas.SeriesGroupBy`.'
                )
            object.__setattr__(self, 'func',
                               getattr(SeriesGroupBy, self.func))
            return
        if not callable(agg_func):
            raise TypeError('`func` must be a string or callable.')
        def _apply_agg_func(g: SeriesGroupBy, *args, **kwargs) -> pd.Series:
            return g.agg(agg_func, *args, **kwargs)
        object.__setattr__(self, 'func', _apply_agg_func)
    ###END def AggFuncTuple.__post_init__

    def get_func(self) -> Callable[[pd.Series], pd.Series]:
        """"Get an aggregation function to be applied to a pandas.Series.
        
        This method will return a partial function with the given positional
        and keyword arguments applied to it. If `self.func` is a string, it
        will first be looked up in the `pandas.SeriesGroupBy` methods.

        Returns
        -------
        Callable[[pandas.Series], pandas.Series]
            The aggregation function to be applied to the given
            `pandas.Series`.
        """
        return functools.partial(
            self.func,
            *self.args,
            **self.kwargs
        )
    ###END def AggFuncTuple.get_func

###END class AggFuncTuple


class TimeseriesRefCriterion(Criterion):
    """Base class for criteria that compare IAM output timeseries.

    This class is a subclass of `pea.Criterion` that is designed to compare
    year-by-year differences between a given IAM output timeseries and a
    reference timeseries. In addition to the method `get_value` that all
    `pea.Criterion` subclasses use to provide a single value for a given
    pathway, this class is designed to permit comparisons for all years and for
    multiple regions simultaneously, and therefore provides a method
    `compare` that can be used to get a fully disaggregated comparison (for each
    year and available region) or a partially aggregated one (aggregated over
    only time or only regions).

    The `get_value` method must nevertheless return a single value for a given
    pathway, i.e., a `pandas.Series` with only the levels `model` and
    `scenario` in the index. To achieve this, the user must pass functions that
    aggregate over regions and over time through the `region_agg` and `time_agg`
    parameters of the `__init__` method.

    Unlike most `pea.Criterion` subclasses and methods,
    which return a single value for an entire model/scenario or a Series with a
    single value for each model/scenario, the methods of this class return a
    Series with a value for each year for a single model/scenario pair, or a
    Series with an additional index level for the year and values for each year
    for each model/scenario pair.

    Note that unlike the `pathways-ensemble-analysis.Criterion` base class,
    this class is intended to be able to check data for multiple regions at
    once, and the `__init__` method therefore does not take a `region`
    parameter. Please filter unwanted regions out of both the reference data
    before passing it to the `__init__` method, and from the data to be vetted
    before passing it to the `get_values` method. If you only intend to pass in
    reference data and data to be vetted for a single region, you can pass in
    `"first"` to the `region_agg` parameter of the `__init__` method to avoid
    having to construct an aggregation function (the data will then be
    "aggregated" using the `first` method of the `pandas.GroupBy` class, which
    simply returns the first value for each group, each of which should only
    contain a single value if the data only contains a single region).


    Init parameters
    ---------------
    criterion_name : str
        The name of the criterion.
    reference : pyam.IamDataFrame
        The reference timeseries to compare against. *NB!* The original passed
        object itself is stored and compared against, not a copy. This is done
        to conserve memory, and allow for defining multiple criteria with the
        same reference without taking up additional memory. Ensure that you do
        not unintentionally modify the reference object after passing it in.
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
