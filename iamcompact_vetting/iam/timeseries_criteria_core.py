"""Base classes that extend pea.Criterion to entire IAM output timeseries.

The classes in this module are used to rate year-by-year differences between
a given IAM output timeseries and a reference timeseries. This replaces
previously started work that aimed to do the same through an entirely separate
class hierarchy (in the module `iam_vetter_core`). The new approach instead
leverages and integrates with the existing `Criterion` class and related
methods of the `pathways-ensemble-analysis` package (`pea`).
"""
import typing as tp
import logging

import pyam
import pandas as pd
import pathways_ensemble_analysis as pea
from pathways_ensemble_analysis.criteria.base import Criterion

from .dims import IamDim



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
        a `pyam.IamDataFrame` and a `pyam.IamDataFrame` as positional arguments
        and return a `pandas.Series` with comparison values (like differences,
        ratios or other difference measures). The design of this base class
        implicitly assumes that the returned `Series` has the same index as the
        intersection of the indexes of the two `IamDataFrame`s (after
        broadcasting), but this is not enforced.
        You can also pass functions that compare the underlying `pandas.Series`
        objects, which can be significantly faster, by using the
        `pyam_series_comparison` decorator (in this module, see separate
        docstring). In most cases, you will probably also want to prefix that
        with the `math_units` decorator (also in this module, see separate
        docstring) to ensure that units are consistent before comparing the
        Series, but this can be left out to improve performance if you are sure
        that the units are already consistent.
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




