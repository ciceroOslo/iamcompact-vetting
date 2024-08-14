"""Notebook to assess AR6 vetting ranges for a user-provided IamDataFrame."""

# %% [markdown]
# # Imports
# %%
from pathlib import Path
import re

import pyam
import pandas as pd

from iamcompact_vetting.targets.ar6_vetting_targets import (
    vetting_targets_historical,
    vetting_targets_future,
    vetting_targets
)
from iamcompact_vetting.targets.iamcompact_harmonization_targets import(
    IamCompactHarmonizationRatioCriterion,
    gdp_pop_harmonization_criterion
)
from iamcompact_vetting.targets.target_classes import(
    CriterionTargetRange,
)
from iamcompact_vetting.output.timeseries import (
    TimeseriesComparisonFullDataOutput,
)
from iamcompact_vetting.output.excel import DataFrameExcelWriter


# %% [markdown]
# # Set pandas display options
#
# We increase the number of rows displayed to make it easier to see full
# outputs. Decrease or increase as needed.
# %%
pd.options.display.min_rows = 250
pd.options.display.max_rows = 300

# %% [markdown]
# # Get the model/scenario data to be assessed.
#
# In the code cell below, add code to load the data you want to assess and
# assign it to the variable `iam_df`. This can be done either by using
# `pyam.IamDataFrame` to read from an Excel or CSV file, or by importing
# your own code that loads and/or processes the data.
# %%
from cycle1_study_model_outputs.cycle1_results import joint_iamdf

iam_df: pyam.IamDataFrame = joint_iamdf


# %% [markdown]
# # Fix Errors in the data
#
# In the code cell or cells below, add code to fix any errors in the data that
# you want to fix. the variable `iam_df` must hold the correct data at the end.
# Add cells as needed, preferably at least one cell per distinct error being
# fixed.
#
# In the original version of this notebook with results from the 1st modelling
# cycle as of July 2024, the errors that needed to be fixed included the
# following:
#   - Some models used `MtCO2/yr` (without space) for `Emissions|CO2|Energy and
#     Industrial Processes` instead of `Mt CO2/yr`.

# %% [markdown]
# ### Replace faulty unit `MtCO2/yr` with `Mt CO2/yr`
# %%
iam_df = iam_df.rename(
    unit={"MtCO2/yr": "Mt CO2/yr"}
)  # pyright: ignore[reportAssignmentType]

# %% [markdown]
# ### Replace `Carbon Capture` with `Carbon Sequestration|CCS` for PROMETHEUS
#
# The PROMETHEUS model uses `Carbon Capture` instead of the name
# `Carbon Sequestration|CCS` used by the `pathways-ensemble-analysis` package
# and the AR6 models. Rename it here to make sure that we can use
# `SingleVariableCriterion` for the "CCS from energy" vetting criterion.
# %%
prometheus_CCS_df: pyam.IamDataFrame = iam_df.filter(
    model='PROMETHEUS V1', variable='Carbon Capture*',  # pyright: ignore[reportAssignmentType]
)
other_df: pyam.IamDataFrame = iam_df.filter(
    model='PROMETHEUS V1', variable='Carbon Capture*', keep=False,  # pyright: ignore[reportAssignmentType]
)
prometheus_rename_dict: dict[str, str] = {
    _varname: _varname.replace("Carbon Capture", "Carbon Sequestration|CCS")
    for _varname in prometheus_CCS_df.variable  # pyright: ignore[reportAssignmentType]
}
prometheus_CCS_df = prometheus_CCS_df.rename(
    variable=prometheus_rename_dict
)  # pyright: ignore[reportAssignmentType]
iam_df = pyam.concat([other_df, prometheus_CCS_df])

if len(iam_df.filter(variable='Carbon Capture*').variable) > 0:
    raise RuntimeError('Unexpected `Carbon Capture` variables remaining.')

# %% [markdown]
# ### Replace `Energy & Industrial Processes` with `Energy and Industrial Processes` in variable names.
# %%
iam_df = iam_df.rename(
    variable={
        _varname: _varname.replace(
            "Energy & Industrial Processes", "Energy and Industrial Processes"
        )
        for _varname in iam_df.variable
        if 'Energy & Industrial Processes' in _varname
    }
)  # pyright: ignore[reportAssignmentType]

# %% [markdown]
# ### Define a new variable `Secondary Energy|Electricity|Wind and Solar`
#
# Not present in the 1st cycle models, so define it by adding up
# `Secondary Energy|Electricity|Wind` and `Secondary Energy|Electricity|Solar`.
iam_df = pyam.concat(
    [
        iam_df,
        iam_df.add(
            'Secondary Energy|Electricity|Wind',
            'Secondary Energy|Electricity|Solar',
            'Secondary Energy|Electricity|Wind and Solar',
        )
    ]
)  # pyright: ignore[reportAssignmentType]

# %% [markdown]
# ### Correct GDP and population unit names
#
# GDP variables in the 1st modelling cycle data from some models used currency
# unit and base-year designations that are now considered non-standard, such
# as "\$US" or "US\$" instead of "USD", putting the base year directly after the
# currency unit rather than separating them by an underscore, and "Billion" with
# a capital "B" instead of "billion". The current, correct convention for IAMC
# formatted files is to use, e.g., "USD_2010" or "USD_2017" for 2010 and 2017
# US dollars.
#
# For population, some models used "millions" plural instead of "million", which
# also needs to be corrected.


def _replace_usd_unit_name(s: str) -> str:
    usd_unit_name_pattern = re.compile(r"(?:US\$|\$US)\s*(\d{4})")
    return usd_unit_name_pattern.sub(r"USD_\1", s)

iam_df = iam_df.rename(
    unit={
        _unit: _replace_usd_unit_name(_unit).replace("Billion", "billion")
        for _unit in iam_df.filter(variable='*GDP*').unit
    } | {
        'millions': 'million'
    },
)  # pyright: ignore[reportAssignmentType, reportOptionalMemberAccess]

# %% [markdown]
# ### Rename unspecified `GDP` variable
#
# The TIAM result files in the 1st modelling cycle uses a variable `GDP` without
# specifying whether it is MER or PPP. For vetting, we assume it's PPP and
# therefore rename it to `GDP|PPP` so that it will match the reference data.
iam_df = iam_df.rename(variable={'GDP': 'GDP|PPP'})  # pyright: ignore[reportAssignmentType]

# %%[markdown]
# # Assess the AR6 vetting ranges
#
# The cells below assess whether the results are in range and how far they are
# from the target value of each vetting criterion.
#
# First create lists with DataFrames/Series with the target results and the
# values returned by `.get_values` for each vetting criterion.
# %%
_crit_target: CriterionTargetRange

vetting_results: list[pd.DataFrame] = [
    _crit_target.get_distances_in_range(iam_df)
    for _crit_target in vetting_targets
]

criterion_values: list[pd.Series] = [
    _crit_target.get_values(iam_df)
    for _crit_target in vetting_targets
]

# %% [markdown]
# Then combine the results into single DataFrame/Series.
#
# `vetting_results_df` will be a DataFrame with a column `distance` for the
# distance between the value for a given model/scenario and the target value
# (in most cases `0` when the value is equal to the target, `+1.0` if it is at
# the upper limit of the range, and `-1.0` if it is at the lower limit), and
# a column `in_range` for whether each value is in the target range or not.
#
# `criterion_values_series` will be a Series with the same index as
# `vetting_results_df`, and the values will be the criterion values for each
# model/scenario.
# %%
vetting_results_df: pd.DataFrame = pd.concat(vetting_results, axis="index")

criterion_values_series: pd.Series = pd.concat(criterion_values, axis="index")

# %% [markdown]
# Then turn `vetting_results_df` and `criterion_values_series` into DataFrames
# with one column for each vetting criterion, to make it easier to read.
#
# `vetting_results_df` will be split into two DataFrames,
# `vetting_results_in_range_df` and `vetting_results_distance_df`, one for each
# column in `vetting_results_df`.
# %%
vetting_results_in_range_df: pd.DataFrame = pd.DataFrame(
    data={
        _target_name: vetting_results_df["in_range"] \
            .xs(_target_name, level='variable')
        for _target_name in vetting_results_df.index.unique(level='variable')
    }
)

vetting_results_distance_df: pd.DataFrame = pd.DataFrame(
    data={
        _target_name: vetting_results_df["distance"] \
            .xs(_target_name, level='variable')
        for _target_name in vetting_results_df.index.unique(level='variable')
    }
)

criterion_values_df: pd.DataFrame = pd.DataFrame(
    data={
        _target_name: criterion_values_series \
            .xs(_target_name, level='variable')
        for _target_name in criterion_values_series.index.unique(level='variable')
    }
)


# %% [markdown]
# # Assess compliance with harmonisation data for population and GDP.
#
# *NB!* The current code below is just a test at the moment. First get a
# `TimeseriesRefCriterion` with the population and GDP data from harmonization,
# to test whether it works with the model data.
# assessment_values: pd.Series = \
#     gdp_pop_harmonization_criterion.get_values(
#         iam_df
#     )
# %%
# Commenting out this code again, in favor of using a Timeseries
iam_df_pop_gdp = iam_df.filter(variable=['Population', 'GDP|PPP'])
# %%
assessment_values: pd.Series = \
    gdp_pop_harmonization_criterion.get_values(iam_df_pop_gdp)
# %%
# 
assessment_full_comparison: pd.Series = \
    gdp_pop_harmonization_criterion.compare(iam_df_pop_gdp)

# %% [markdown]
# # Write harmonization assessment result
#
# Test using a `TimesereComparisonFullDataOutput` with a `DataFrameExcelWriter`
# to output the results to an Excel file.
#
# %% [markdown]
# First create a `DataFrameExcelWriter` instance to write to a suitable Excel
# file.
# %%
gdp_pop_harmonization_assessment_output_file: Path = \
    Path.cwd() / 'gdp_pop_harmonization_assessment.xlsx'

gdp_pop_harmonization_assessment_writer: DataFrameExcelWriter = \
    DataFrameExcelWriter(
        file=gdp_pop_harmonization_assessment_output_file,
        sheet_name='Ratio results vs harmonization data',
    )

# %% [markdown]
# Then create a `TimeseriesComparisonFullDataOutput` instance with the
# `DataFrameExcelWriter` instance.
# %%
gdp_pop_harmonization_assessment_output: TimeseriesComparisonFullDataOutput[
    IamCompactHarmonizationRatioCriterion,
    None,
] = TimeseriesComparisonFullDataOutput(
    criteria=gdp_pop_harmonization_criterion,
    writer=gdp_pop_harmonization_assessment_writer
)
