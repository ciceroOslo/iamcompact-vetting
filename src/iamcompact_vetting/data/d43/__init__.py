"""Harmonization data from IAM COMPACT D4.3 / first modelling cycle.

Module Attributes
-----------------
gdp_pop_harmonization_data_file : pathlib.Path
    Path to Excel file containing socioeconomic harmonization data (Population
    and GDP|PPP).

Functions
---------
get_gdp_pop_harmonisation_iamdf(force_reload: bool = False) -> pyam.IamDataFrame
    Get an IamDataFrame containing the population and GDP harmonization data
"""
from pathlib import Path
import typing as tp

import pyam



gdp_pop_harmonization_data_file: tp.Final[Path] = \
    Path(__file__).parent / 'gdp_pop_iam_compact_20230625_IAMCformat.xlsx'
gdp_pop_harmonization_data_file_regmapped: tp.Final[Path] = \
    Path(__file__).parent / 'gdp_pop_iam_compact_20230625_IAMCformat_region_mapped.xlsx'

_gdp_pop_harmonisation_iamdf_with_iso3: pyam.IamDataFrame|None = None
_gdp_pop_harmonisation_iamdf: pyam.IamDataFrame|None = None

def get_gdp_pop_harmonisation_iamdf(
    force_reload: bool = False,
    with_iso3_column: bool = False,
) -> pyam.IamDataFrame:
    """Get an IamDataFrame with the population and GDP harmonization data.
    
    NB! The returned `IamDataFrame` is cached internally unless `force_reload`
    is `True`, so it should not be
    altered.
    
    Parameters
    ----------
    force_reload : bool
        If `True`, reload the data from the source file even if it has already
        been loaded.
    with_iso3_column : bool, optional
        Whether to include a column of 3-letter ISO country codes as an extra
        column. Note that including this may cause isses if you combine the data
        with data in other `pyam.IamDataFrame` or pandas objects, since the
        index of the returned `IamDataFrame` will contain an extra level `iso3`
        in addition to the usual `IamDataFrame` index levels. Optional, by
        default `False`.
        **NB!** Setting this parameter to `True` or None is deprecated. Doing so
        will exclude aggregate regions.
    """
    global _gdp_pop_harmonisation_iamdf_with_iso3
    global _gdp_pop_harmonisation_iamdf
    if with_iso3_column:
        if _gdp_pop_harmonisation_iamdf_with_iso3 is None or force_reload:
            _gdp_pop_harmonisation_iamdf_with_iso3 = pyam.IamDataFrame(
                gdp_pop_harmonization_data_file
            )
        return _gdp_pop_harmonisation_iamdf_with_iso3
    if not with_iso3_column:
        if _gdp_pop_harmonisation_iamdf is None or force_reload:
            _gdp_pop_harmonisation_iamdf = pyam.IamDataFrame(
                gdp_pop_harmonization_data_file_regmapped
            )
        return _gdp_pop_harmonisation_iamdf
###END def get_gdp_pop_harmonisation_iamdf
