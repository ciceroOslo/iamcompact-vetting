"""Helper functions for the `pyam` package.

Functions
---------
make_consistent_units(df, match_df, unit_col='unit', match_dims=('variable',)) \
        -> pyam.IamDataFrame
    Make the units of an IamDataFrame consistent with another IamDataFrame.
    Converts units only for the variables where the units are different, does
    not convert a given unit for all variables the way
    `pyam.IamDataFrame.convert_unit` does. Only converts units for variables
    present in both IamDataFrames, and does not require both IamDataFrames to
    have the same regions, models, or scenarios, unless specified.
"""
import typing as tp

import pyam
import pandas as pd


TV = tp.TypeVar('TV')
def notnone(x: TV|None) -> TV:
    assert x is not None
    return x
###END def notnone


def make_consistent_units(
        df: pyam.IamDataFrame,
        match_df: pyam.IamDataFrame,
        unit_col: str = 'unit',
        match_dims: tp.Sequence[str] = ('variable',),
        keep_meta: bool = True
) -> pyam.IamDataFrame:
    """Make the units of an IamDataFrame consistent with another IamDataFrame.

    Converts units only for the variables where the units are different, does
    not convert a given unit for all variables the way
    `pyam.IamDataFrame.convert_unit` does. Only converts units for variables
    present in both IamDataFrames, and does not require both IamDataFrames to
    have the same regions, models, or scenarios, unless specified.

    Parameters
    ----------
    df : pyam.IamDataFrame
        IamDataFrame to make the units consistent for.
    match_df : pyam.IamDataFrame
        IamDataFrame to match the units to.
    unit_col : str, optional
        Name of the dimension in the IamDataFrame that contains the units.
        Optional, defaults to 'unit'.
    keep_meta : bool, optional
        Whether to keep the metadata of `df` when converting units. Optional,
        defaults to True.
    match_dims : Sequence[str], optional
        Dimensions to match the units on. Optional, defaults to ('variable',).
        It is assumed that the units are the same for all other dimensions in
        `match_df`.

    Returns
    -------
    pyam.IamDataFrame
        IamDataFrame with units consisetent with `match_df`.
    """
    # First use the `pyam.IamDataFrame.unit_mapping` property to get a list of
    # all variables in `df` that have different units from `match_df`.
    df_unit_mapping: dict[str, str|list[str]] = df.unit_mapping
    match_unit_mapping: dict[str, list[str]] = match_df.unit_mapping
    differing_vars: list[str] = [
        _var for _var, _unit in df_unit_mapping.items()
        if _unit != match_unit_mapping.get(_var, _unit)
    ]
    matching_df: pyam.IamDataFrame = notnone(
        df.filter(variable=differing_vars, keep=False)
    )
    converted_dfs: list[pyam.IamDataFrame] = []
    for _var in differing_vars:
        # If _var has a single unit in `match_df`, convert it to that unit using
        # `pyam.IamDataFrame.convert_unit`.
        target_unit: str|list[str] = match_unit_mapping[_var]
        if isinstance(target_unit, str):
            converted_dfs.append(
                notnone(
                    notnone(df.filter(variable=_var)) \
                        .convert_unit(_var, to=target_unit)
                )
            )
        else:
            raise NotImplementedError(
                'Conversion using a target dataframe with more than one unit '
                'for a single variable is not yet implemented.'
            )
    converted_data_series: pd.Series = pd.concat(
        [matching_df._data, *[_df._data for _df in converted_dfs]]
    )
    # Reorder rows to match the data of the original IamDataFrame.
    converted_data_series = converted_data_series.reindex(df._data.index)
    converted_df: pyam.IamDataFrame = pyam.IamDataFrame(converted_data_series) \
        if not keep_meta else \
            pyam.IamDataFrame(converted_data_series, meta=df.meta)
    return converted_df
###END def make_consistent_units
