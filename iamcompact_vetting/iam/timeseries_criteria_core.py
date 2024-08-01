"""Base classes that extend pea.Criterion to entire IAM output timeseries.

The classes in this module are used to rate year-by-year differences between
a given IAM output timeseries and a reference timeseries. This replaces
previously started work that aimed to do the same through an entirely separate
class hierarchy (in the module `iam_vetter_core`). The new approach instead
leverages and integrates with the existing `Criterion` class and related
methods of the `pathways-ensemble-analysis` package (`pea`).
"""
import typing as tp
from collections.abc import Iterable, Callable, Iterator
from enum import StrEnum
import dataclasses
import functools
import logging

import pyam
import pandas as pd
from pandas.core.indexes.frozen import FrozenList
from pandas.core.groupby import SeriesGroupBy
import pathways_ensemble_analysis as pea
from pathways_ensemble_analysis.criteria.base import Criterion

from iamcompact_vetting import pyam_helpers
from iamcompact_vetting.iam.dims import (
    IamDimNames,
    DIM,
    UnknownDimensionNameError,
)



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
        def __call__(self, s: pd.Series, /, *args, **kwargs) -> float:
            ...
    class GroupByAggMethod(tp.Protocol):
        def __call__(self, g: SeriesGroupBy, /, *args, **kwargs) -> pd.Series:
            ...
    ###END class AggFuncTuple.AggFunc

    func: AggFunc | str
    args: Iterable[tp.Any] = ()
    kwargs: dict[str, tp.Any] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.func, str):
            # Check that the attribute named `func` of `pandas.SeriesGroupBy`
            # is a method of `pandas.SeriesGroupBy`.
            groupby_attr: tp.Any = getattr(SeriesGroupBy, self.func)
            if not callable(getattr(SeriesGroupBy, self.func)):
                raise TypeError(
                    f'`{self.func}` is not a callable method of '
                    '`pandas.SeriesGroupBy`.'
                )
        elif not callable(self.func):
            raise TypeError('`func` must be a string or callable.')
    ###END def AggFuncTuple.__post_init__

    # Define iterator protocol to be able to use the class more like a tuple,
    # and `keys`, `values` and `__getitem__` to be able to use it like a
    # mapping.
    def __iter__(self) -> Iterator[tp.Any]:
        return iter(dataclasses.astuple(self))
    def keys(self) -> Iterable[str]:
        return dataclasses.asdict(self).keys()
    def values(self) -> Iterable[tp.Any]:
        return dataclasses.asdict(self).values()
    def __getitem__(self, key: str|int) -> tp.Any:
        if isinstance(key, int):
            return dataclasses.astuple(self)[key]
        elif isinstance(key, str):
            return dataclasses.asdict(self)[key]
    ###END def AggFuncTuple.__iter__

###END class AggFuncTuple


class AggDimOrder(StrEnum):
    """The order in which aggregations should be performed.
    
    The class defines which order to apply aggregations in when calling the
    `get_values` method of the `TimeseriesRefCriterion` class. That method needs
    to aggregate over both time and regions after calling `compare`.
    """
    TIME_FIRST = 'time_first'
    REGION_FIRST = 'region_first'
###END class AggDimOrder


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
        docstring). *NB!* The return value of `comparison_function` is specified
        as `pandas.Series` in order to allow more flexibility in dimensionality
        (i.e., index levels) than would be possible with a `pyam.IamDataFrame`.
        however, when possible, it is best practice to return a `pandas.Series`
        with a format that can be passed directly to `pyam.IamDataFrame` to
        construct a full `pyam.IamDataFrame` object (albeit with empty
        metadata). *NB!* It is the responsibility of the user to ensure that the
        returned `Series` has the correct units in the `unit` index level. If
        the `pyam_series_comparison` decorator is used, the units in the input
        will be made compatible before computation so that the resulting values
        are likely to be correct, but the unit name may no longer be correct.
        For example, if the comparison takes ratios or precentagewise
        differences, the units of the output will not be the same as the units
        of the inputs, and the user is responsible for ensuring that this is
        correctly reflected in the `unit` index level of the returned `Series`.
    region_agg : AggFuncTuple, tuple, callable or str
        The function to use to aggregate the timeseries over regions before
        calling `self.get_values`. If the function does not need to take any
        arguments, it should be either a callable that takes a `pandas.Series`
        and returns a float, or a string that is a method name of the pandas
        `SeriesGroupBy` class. If it takes arguments, it should be a 2- or 
        3-tuple of the form `(func, args, kwargs)`, where `func` is a callable
        or string, or an `AggFuncTuple` object (defined in this module).
    time_agg : AggFuncTuple, tuple, callable or str
        The function to use to aggregate the timeseries over time before
        calling `self.get_values`. Must fulfill the same requirements as
        `region_agg`.
    agg_dim_order: AggDimOrder or str, optional
        Which order to apply aggregations in when calling `self.get_values`.
        Should be an `AggDimOrder` enum, or a string that is equal to one of
        the enum values. Defaults to `AggDimOrder.REGION_FIRST`.
    broadcast_dims : iterable of str, optional
        The dimensions to broadcast over when comparing the timeseries. This
        should be a subset of the dimensions of the `reference` timeseries.
        `reference` should only have one value for each of these dimensions, or
        a `ValueError` will be raised. `reference` will be broadcast to the
        values of thsese dimensions in the `IamDataFrame` being comopared to
        before being passed to `comparison_function`. Optional, defaults to
        `('model', 'scenario')`.
    rating_function : callable, optional
        The function to use to rate the comparison values. This function should
        take a `pandas.Series` and return a single value. Optional, defaults to
        absolute max.
    dim_names : dim.IamDimNames, optional
        The dimension names of the reference `IamDataFrame`s used for reference
        and to be vetted. Optional, defaults to `dims.DIM`
    *args, **kwargs
        Additional arguments to be passed to the superclass `__init__` method.
        See the documentation of `pathways-ensemble-analysis.Criterion` for
        more information.

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

    AggFuncArg: tp.TypeAlias = AggFuncTuple \
        | tuple[
            AggFuncTuple.AggFunc|str,
            Iterable[tp.Any],
            dict[str, tp.Any],
        ] \
        | AggFuncTuple.AggFunc \
        | str

    def __init__(
            self,
            criterion_name: str,
            reference: pyam.IamDataFrame,
            comparison_function: tp.Callable[
                [pyam.IamDataFrame, pyam.IamDataFrame], pd.Series
            ],
            region_agg: AggFuncArg,
            time_agg: AggFuncArg,
            agg_dim_order: AggDimOrder | str = AggDimOrder.REGION_FIRST,
            broadcast_dims: Iterable[str] = ('model', 'scenario'),
            rating_function: Callable[[pd.Series], pd.Series] = \
                lambda s: s.abs().max(),
            dim_names: IamDimNames = DIM,
            *args,
            **kwargs,
    ):
        self.reference: pyam.IamDataFrame = reference
        self.comparison_function: Callable[
            [pyam.IamDataFrame, pyam.IamDataFrame], pd.Series
        ] = comparison_function
        self._time_agg: AggFuncTuple = self._make_agg_func_tuple(time_agg)
        self._region_agg: AggFuncTuple = self._make_agg_func_tuple(region_agg)
        self.agg_dim_order: AggDimOrder = AggDimOrder(agg_dim_order)
        # Raise ValueError if `broadcast_dims` is not a subset of `reference.dimensions`
        if any(
                _dim not in reference.dimensions for _dim in broadcast_dims
        ):
            raise UnknownDimensionNameError('`broadcast_dims` must be a subset '
                                            'of `reference.dimensions`')
        self.dim_names: IamDimNames = dim_names
        self.broadcast_dims: list[str] = list(broadcast_dims)
        self.rating_function = rating_function
        super().__init__(
            criterion_name=criterion_name,
            region='*',
            rating_function=rating_function,
            *args,
            **kwargs
        )
    ###END def TimeseriesRefCriterion.__init__

    def _make_agg_func_tuple(self, agg_func: AggFuncArg) -> AggFuncTuple:
        if isinstance(agg_func, AggFuncTuple):
            return agg_func
        if isinstance(agg_func, str):
            return AggFuncTuple(agg_func)
        if isinstance(agg_func, tuple):
            return AggFuncTuple(*agg_func)
        if callable(agg_func):
            return AggFuncTuple(agg_func)
        raise TypeError(f'`agg_func` must be a string, tuple, or callable.')
    ###END def _make_agg_func_tuple

    def _aggregate_time(self, s: pd.Series) -> pd.Series:
        """Aggregate Series returned by `self.compare` over time."""
        agg_func_tuple: AggFuncTuple = self._time_agg
        return s.groupby(
            tp.cast(FrozenList, s.index.names) \
                .difference([self.dim_names.TIME]),
        ).agg(
            agg_func_tuple.func,
            *agg_func_tuple.args,
            **agg_func_tuple.kwargs
        )
    ###END def TimeseriesRefCriterion._aggregate_time

    def _aggregate_region(self, s: pd.Series) -> pd.Series:
        """Aggregate Series returned by `self.compare` over regions."""
        agg_func_tuple: AggFuncTuple = self._region_agg
        return s.groupby(
            tp.cast(FrozenList, s.index.names) \
                .difference([self.dim_names.REGION]),
        ).agg(
            agg_func_tuple.func,
            *agg_func_tuple.args,
            **agg_func_tuple.kwargs
        )
    ###END def TimeseriesRefCriterion._aggregate_region

    def aggregate_time_and_region(self, s: pd.Series) -> pd.Series:
        """Aggregate Series returned by `self.compare` over time and regions,
        
        This method is used to aggregate the output from `self.compare` before
        passing it to `self.get_values`. Aggregation over time and regions is
        done in the order specified by the `agg_dim_order` parameter passed to
        the `__init__` method.
        """
        if self.agg_dim_order == AggDimOrder.REGION_FIRST:
            return self._aggregate_region(self._aggregate_time(s))
        if self.agg_dim_order == AggDimOrder.TIME_FIRST:
            return self._aggregate_time(self._aggregate_region(s))
        raise RuntimeError(f'Unknown `agg_dim_order` {self.agg_dim_order}.')
    ###END def TimeseriesRefCriterion.aggregate_time_and_region

    def compare(self, iamdf: pyam.IamDataFrame) -> pd.Series:
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
        return self.comparison_function(ref, iamdf)
    ###END def TimeseriesRefCriterion.get_values

    def get_values(
            self,
            file: pyam.IamDataFrame,
    ) -> pd.Series:
        """Return comparison values aggregated over region and time."""
        return self.aggregate_time_and_region(self.compare(file))
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
