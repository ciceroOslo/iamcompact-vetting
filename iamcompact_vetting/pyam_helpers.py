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
    if x is None:
        raise ValueError('Value is None')
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
        source_units: str|list[str] = df_unit_mapping[_var]
        if isinstance(source_units, str):
            source_units = [source_units]
        for _source_unit in source_units:
            if isinstance(target_unit, str):
                converted_dfs.append(
                    notnone(
                        notnone(df.filter(variable=_var)) \
                            .convert_unit(_source_unit, to=target_unit)
                    )
                )
            else:
                raise NotImplementedError(
                    'Conversion using a target dataframe with more than one '
                    'unit for a single variable is not yet implemented.'
                )
    converted_data_series: pd.Series = pd.concat(
        [matching_df._data, *[_df._data for _df in converted_dfs]]
    )
    converted_df: pyam.IamDataFrame = pyam.IamDataFrame(converted_data_series) \
        if not keep_meta else \
            pyam.IamDataFrame(converted_data_series, meta=df.meta)
    return converted_df
###END def make_consistent_units


def as_pandas_series(
        df: pyam.IamDataFrame,
        name: tp.Optional[str] = None,
        copy: bool = True
) -> pd.Series:
    """Get the data of a `pyam.IamDataFram` as `pandas.Series` with MultiIndex.

    This function currently does the same as getting the private attribute
    `df._data` or `df._data.copy()` of the `pyam.IamDataFrame` directly, but
    should be used instead of that to avoid breaking changes in the future.

    Parameters
    ----------
    df : pyam.IamDataFrame
        IamDataFrame to get the data from.
    name : str, optional
        Name of the returned Series. Optional, defaults to None.
    copy : bool, optional
        Whether to return a copy of the data. If necessary, this parameter can
        be set to False to improve performance, but this carries some risks
        and may be removed or deprecated in the future. If False, the private
        attribute `df._data` is returned. Note that any changes made to the
        returned Series can then cause changes to and potentially corrupt the
        original IamDataFrame. Also, if the internal attributes of
        `pyam.IamDataFrame` are changed in the future, the `_data` attribute may
        be removed or changed, and any code using `copy=False` may then break.
        Optional, defaults to True.

    Returns
    -------
    pd.Series
        Data of the IamDataFrame as a Series.
    """
    data_ser: pd.Series = df._data if not copy else df._data.copy()
    if name is not None:
        data_ser.name = name
    return data_ser
###END def as_pandas_series
