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
    which return a single value for an entire model/scenario or a Series with
    a single value for each model/scenario, the methods of this class return a
    Series with a value for each year for a single model/scenario pair, or
    a Series with an additional index level for the year and values for each
    year for each model/scenario pair.

    Init parameters
    ---------------
    criterion_name : str
        The name of the criterion.
    reference : pyam.IamDataFrame
    """


