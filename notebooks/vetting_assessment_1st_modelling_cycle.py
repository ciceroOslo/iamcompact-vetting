"""Notebook to assess AR6 vetting ranges for a user-provided IamDataFrame."""

# %% [markdown]
# # Run IAM COMPACT locally/interactively
#
# The code in this notebook shows how to run IAM COMPACT veting checks for the
# 1st modelling cycle manually and locally on the users' own computers, without
# being dependent on the I2AM PARIS web platform.
#
# The notebook comes in two formats:
#   * Extension `.ipynb`: A Jupyter notebook. Requires using a Jupyter notebook
#     server or a locally running Jupyter notebook kernel.
#   * Extension `.py`: A standard Python file with cell denoted in comments as
#     starting with `# %%`. Can be used interactively in Visual Studio Code or
#     other applications that can run Python files interactively and recognizes
#     the `# %%` cell delimiter. Can also be imported as a module, in which case
#     the entire file is run non-interactively from top to bottom, and outputs
#     become available as module attributes.
#
# This notebook is specific to 1st modelling cycle and the model result files
# that were available on the IAM COMPACT SharePoint in July 2024. This includes
# code to load and fix issues with those specific files. A separate notebbok
# file, named `vetting_assessment`, can be used if you want to run the code with
# other model results in hopefully non-problematic IAMC-formatted Excel file.
#
# In order to use this notebook, you will need to obtain a pickle file (used to
# store Python objects) with the results of the 1st modelling cycle. The file
# is called `data_dict.pkl` and must be placed in the folder
# `notebooks/cycle1_study_model_outputs`. You must have access to the IAM
# COMPACT SharePoint, and can find the file in the folder
# `Documents > General > 2-Deliverables and Milestones > WP4 (Modelling –
# Quantitative evidence in support of post-2030 Paris-compliant climate action) >
# First Modelling Cycle`. You can download the pickle file directly using the
# following link (provided you have access):
# [https://epuntuagr.sharepoint.com/:u:/r/sites/iamcompact/Shared%20Documents/General/2-Deliverables%20and%20Milestones/WP4%20(Modelling%20%E2%80%93%20Quantitative%20evidence%20in%20support%20of%20post-2030%20Paris-compliant%20climate%20action)/First%20Modelling%20Cycle/data_dict.pkl?csf=1&web=1&e=ehfa45](https://epuntuagr.sharepoint.com/:u:/r/sites/iamcompact/Shared%20Documents/General/2-Deliverables%20and%20Milestones/WP4%20(Modelling%20%E2%80%93%20Quantitative%20evidence%20in%20support%20of%20post-2030%20Paris-compliant%20climate%20action)/First%20Modelling%20Cycle/data_dict.pkl?csf=1&web=1&e=ehfa45)

# %% [markdown]
# # Setup
#
# %% [markdown]
# ## Imports
#
# Import the required packages.
# %%
from pathlib import Path
import re
from collections.abc import Mapping

import pyam
import pandas as pd
from pandas.io.formats.style import Styler as PandasStyler

from iamcompact_vetting.output.iamcompact_outputs import \
    ar6_vetting_target_range_output
from iamcompact_vetting.targets.iamcompact_harmonization_targets import(
    gdp_pop_harmonization_criterion,
    IamCompactHarmonizationRatioCriterion,
    IamCompactHarmonizationTarget,
)
from iamcompact_vetting.targets.target_classes import(
    CriterionTargetRange,
)
from iamcompact_vetting.output.base import (
    CriterionTargetRangeOutput,
    MultiCriterionTargetRangeOutput,
)
from iamcompact_vetting.output.timeseries import (
    TimeseriesRefFullComparisonOutput,
    TimeseriesRefComparisonAndTargetOutput,
)
from iamcompact_vetting.output.excel import (
    DataFrameExcelWriter,
    MultiDataFrameExcelWriter,
    make_valid_excel_sheetname,
)


# %% [markdown]
# ## Set pandas display options
#
# We increase the number of rows displayed to make it easier to see full
# outputs. Decrease or increase as needed.
# %%
pd.options.display.min_rows = 250
pd.options.display.max_rows = 300

# %% [markdown]
# ## Get the model/scenario data to be assessed.
#
# In the code cell below, add code to load the data you want to assess and
# assign it to the variable `iam_df`. This can be done either by using
# `pyam.IamDataFrame` to read from an Excel or CSV file, or by importing
# your own code that loads and/or processes the data.
#
# In this notebook specifically for the 1st modelling cycle, we use import a
# separate module that loads precompiled data from the Excel files with results
# from the 1st modelling cycle.
#
# *NB!* This will fail if you have not placed the pickle file 'data_dict.pkl'
# with the required data in the `notebooks/cycle1_study_model_outputs`
# subfolder. See the top of this file for explanations.
# %%
from cycle1_study_model_outputs.cycle1_results import joint_iamdf

iam_df: pyam.IamDataFrame = joint_iamdf


# %% [markdown]
# # Data processing / fixing data issues
#
# In the code cell or cells below, add code to fix any errors in the data that
# you want to fix or do any necessary processing before running the vetting
# code. The variable `iam_df` must hold the correct data at the end. Add cells
# as needed, preferably at least one cell per distinct error being fixed.
#
# In this notebook for the 1st modelling cycle, there are several cells that
# make modifications to units, variable names and other aspects that needed to
# be adjusted to be compatible with the vetting procedures. Each distinct issue
# is processed in a separate cell under a distinct header.
#
# %% [markdown]
# ## Replace faulty unit `MtCO2/yr` with `Mt CO2/yr`
#
# The IAMC standard has a space between the mass unit and the gas species name
# for species-specific mass units.
# %%
iam_df = iam_df.rename(
    unit={"MtCO2/yr": "Mt CO2/yr"}
)  # pyright: ignore[reportAssignmentType]

# %% [markdown]
# ## Replace `Carbon Capture` with `Carbon Sequestration|CCS` for PROMETHEUS
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
    model='PROMETHEUS V1', 
    variable='Carbon Capture*',
    keep=False,  # pyright: ignore[reportAssignmentType]
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
# ## Replace `Energy & Industrial Processes` with `Energy and Industrial Processes` in variable names.
#
# The IAMC standard uses "and" in variable names rather than "&".
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
# ## Define a new variable `Secondary Energy|Electricity|Wind and Solar`
#
# One of the AR6 vetting criteria require a single variable for electricity
# generated from wind and solar. This was not present in the 1st cycle models,
# so define it by adding up `Secondary Energy|Electricity|Wind` and 
# `Secondary Energy|Electricity|Solar`.
# %%
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
# ## Correct GDP and population unit names
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

# %%
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
# ## Rename unspecified `GDP` variable
#
# The TIAM result files in the 1st modelling cycle uses a variable `GDP` without
# specifying whether it is MER or PPP. For vetting, we assume it's PPP and
# therefore rename it to `GDP|PPP` so that it will match the reference data.
# %%
iam_df = iam_df.rename(variable={'GDP': 'GDP|PPP'})  # pyright: ignore[reportAssignmentType]

# %%[markdown]
# # Assess the AR6 vetting ranges
#
# The cells below assess whether the results are in range and how far they are
# from the target value of each vetting criterion.
#
# The procedure uses `ar6_vetting_targets`, a list of `CriterionTargetRange`
# instances, each of which assesses `iam_df` against one of the AR6 vetting
# criteria. This list is used to produce a list of `MultiCriterionTargetRangeOutput`
# instance, which uses `vetting_targets`to produce output DataFrames, each of 
# which are then written as a worksheet to an Excel file using a
# `MultiDataFrameExcelWriter` instance.
#
# The output Excel file will contain one worksheet for each vetting criterion.
# Each sheet has three index columns, with the name of a model/scenario pair
# in the first two, and the name of the vetting criterion in the third. The
# remaining columns are three value columns with vetting results:
#
# * `Is in target range`: A boolean value. `TRUE` if the model/scenario passes
#   the vetting criterion, `FALSE` otherwise.
# * `Rel. distance from target`: A measure of distance from the central target
#   value of the vetting criterion. The value is defined differently for each
#   criterion, and the exact value is not important, but it will generally be
#   between -1 and +1 for model/scenario pairs that pass the criterion, and
#   equal to 0 if it exactly hits the central value of the criterion. Values
#   very close to -1 or +1 indicate that the value of the vetted variable is
#   almost too low or too high to pass vetting.
# * `Value`: The value of the vetted variable. See the documentation of the AR6
#   vetting criteria for which variable or function of variables is evaluated in
#   each case.
#
# %% [markdown]
# First create a `pandas.ExcelWriter` instance which will write to the output
# Excel file. We need a common `pandas.ExcelWriter` instance for all of the
# vetting criteria, so that we can write results to different worksheets of the
# same Excel file.
#
# The cell below creates a `pandas.ExcelWriter` instance that will write to the
# file `vetting_results.xlsx` in the current working directory. Replace the file
# name with an alternative one or with a Python `Path` object if you wish to
# write to a differently named file or to a different directory.
# %%
results_excel_writer: pd.ExcelWriter = \
    pd.ExcelWriter("ar6_vetting_results.xlsx", engine='xlsxwriter')

# %% [markdown]
# Then create the `MultiCriterionTargetRangeOutput` instance for the
# AR6 vetting criteria. The instance needs a `MultiDataFrameExcelWriter`
# instance # to write the results to different worksheets of the same Excel
# file. The # worksheets will have the same name as the corresponding vetting
# criterion, but with the name potentially shortened and with some characters
# substituted to make sure that they are valid names for Excel worksheets.
# %%
vetting_results_output = ar6_vetting_target_range_output
ar6_vetting_target_range_output._default_include_summary = True
vetting_results_output.writer = MultiDataFrameExcelWriter(
    results_excel_writer,
    force_valid_sheet_name=True,
)

# %% [markdown]
# Finally, we call the `write_results` method of the
# `MultiCriterionTargetRangeOutput` instance, to compute the results and write
# them to the Excel file.
#
# The results are also returned as `pandas.DataFrame` objects in the dict
# `vetting_results_frames`, whose keys are equal to the Excel worksheet names
# (which in turn are equal to the names of the AR6 vetting criteria, shortened
# and modified to be valid Excel worksheet names).
#
# `results_excel_writer.close()` must be called at the end to close and save the
# Excel file.
# %%
vetting_results: dict[str, pd.DataFrame] | dict[str, PandasStyler]
vetting_results, _ = vetting_results_output.write_results(
    iam_df,
    prepare_output_kwargs=dict(add_summary_output=True),
)
# vetting_results_styled = vetting_results_output.style_output(
#     vetting_results,
#     include_summary=True,
# )
results_excel_writer.close()

# %% [markdown]
# # Assess agreement with harmonisation data for population and GDP.
#
# The cells below will compare the model results in `iam_df` with the
# harmonization data for population and GDP in each region that is defined (has
# the same name) in both the harmonization data and in any of the models in
# `iam_df`. Note that it does not currently take into account differences in
# region definitions, or aggregate or translate model-specific region names used
# in different models. This is intended for a future version.
#
# The results are returned as a `pandas.DataFrame` and written to an Excel file
# with two worksheets:
# * `Ratios, full`: Shows the ratio between the values in `iam_df` relative to
#     the harmonization data, for each data point that exists in both data sets
#     for each year with no aggregation. Will be 1.0 values that are identical
#     to the harmonization data.
# * `Summary`: A table with summary results per model/scenario/region
#     combination. The table has two columns:
#     - `Pass`: Shows TRUE for model/scenario/region combinations that pass the
#       vetting criterion. This usually requires that all data points be within
#       2% of the target value, i.e., that the ratio is between 0.98 and 1.02.
#     - `Max rel. diff`: The maximum absolute relative difference between the
#       data value and harmonization data for the model/scenario/region
#       combination. The number given is `maxdiff - 1`, where `maxdiff` is
#       the ratio that differs most from 1.0 across all years. For example, if
#       the most deviant data value is 10% higher than the harmonization data,
#       `Max rel. diff` will be 0.1 (the ratio most different from 1.0 will be
#       1.1). If it is 15% lower than the harmonization data, `Max rel. diff`
#       will be -0.15 (the ratio most different from 1.0 will be 0.85).
#
# Generally, for population and GDP, the ratios should be between 0.98 and 1.02
# to be considered a close match. Values outside that range suggest that either
# the model/scenario has used data that do not agree with the harmonization
# data, or that there are issues with currency conversions, region definitions
# or other inconsistencies or mistakes.

# %%
# First get just the GDP and Population variables from the data. Assert that it
# is not None (not necessary, but if you use Python with a type checker, it is
# needed to avoid a warning, since the `IamDataFrame.filter` method can return
# None):
iam_df_pop_gdp = iam_df.filter(variable=['Population', 'GDP|PPP'])
assert iam_df_pop_gdp is not None

# %% [markdown]
# Then create a `pandas.ExcelWriter` that later code will use to write to a
# specified Excel file. At the moment, it writes to the file
# `gdp_pop_harmonization_vetting.xlsx` in the current working directory, but
# you can change this to your liking.

# %% [markdown]
# **Test cell**. This should be removed in production, and moved further down to
# after the Excel part.
gdp_pop_target: IamCompactHarmonizationTarget = IamCompactHarmonizationTarget(
    criterion=gdp_pop_harmonization_criterion,
)

# %%
gdp_pop_results_excel_writer: pd.ExcelWriter = pd.ExcelWriter(
        'gdp_pop_harmonization_vetting.xlsx',
        engine='xlsxwriter',
)

# %% [markdown]
# Then create a `DataFrameExcelWriter` instance that will do the actual writing
# to Excel:
# %%
gdp_pop_harmonization_assessment_writer: MultiDataFrameExcelWriter = \
    MultiDataFrameExcelWriter(
        file=gdp_pop_results_excel_writer,
)

# %%
gdp_pop_harmonization_output: TimeseriesRefComparisonAndTargetOutput[
    IamCompactHarmonizationRatioCriterion,
    IamCompactHarmonizationTarget,
    TimeseriesRefFullComparisonOutput,
    CriterionTargetRangeOutput,
    MultiDataFrameExcelWriter,
    None
] = TimeseriesRefComparisonAndTargetOutput(
    criteria=gdp_pop_harmonization_criterion,
    target_range=IamCompactHarmonizationTarget,
    timeseries_output_type=TimeseriesRefFullComparisonOutput,
    summary_output_type=CriterionTargetRangeOutput,
    writer=gdp_pop_harmonization_assessment_writer
)

# %%
gdp_pop_harmonization_result, _ignore = \
    gdp_pop_harmonization_output.write_results(iam_df_pop_gdp)

# %%
gdp_pop_harmonization_assessment_writer.close()
