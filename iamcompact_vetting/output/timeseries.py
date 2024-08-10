"""Module for outputting results of timeseries comparisons.

Currently this module only contains classes for writing comparisons between
IAM model results and harmonisation data or other timeseries reference data.
"""
import typing as tp

from ..targets.iamcompact_harmonization_targets import (
    IamCompactHarmonizationRatioCriterion,
)
