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
# This notebook is a general notebook for running the 1st modelling cycle
# vetting checks, and requires you to provide the data you want to assess. To
# run the notebook with the data from the Excel files that were uploaded to the
# IAM COMPACT SharePoint with results from select models and studies, see the
# notebook named `vetting_assessment_1st_modelling_cycle`.

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

import pyam
import pandas as pd

from iamcompact_vetting.targets.ar6_vetting_targets import (
    vetting_targets
)
from iamcompact_vetting.targets.iamcompact_harmonization_targets import(
    IamCompactHarmonizationRatioCriterion,
    gdp_pop_harmonization_criterion
)
from iamcompact_vetting.targets.target_classes import(
    CriterionTargetRange,
)
from iamcompact_vetting.output.base import CriterionTargetRangeOutput
from iamcompact_vetting.output.timeseries import (
    TimeseriesComparisonFullDataOutput,
)
from iamcompact_vetting.output.excel import (
    DataFrameExcelWriter,
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
# %%
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
# ## Fix 1
#
# Add the required code in the cell below. Add more cells as needed below this
# one to organize the code into one cell per distinct fix or processing step.
# %%

# %%[markdown]
# # Assess the AR6 vetting ranges
#
# The cells below assess whether the results are in range and how far they are
# from the target value of each vetting criterion.
#
# The procedure uses `vetting_targets`, a list of `CriterionTargetRange`
# instances, each of which assesses `iam_df` against one of the AR6 vetting
# criteria. This list is used to produce a list of `CriterionTargetRangeOutput`
# instances, each of which which uses one of the elements of `vetting_targets`
# to produce output data structures, each of which are then written to an Excel
# file using a `DataFrameExcelWriter` instance.
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
results_excel_writer: pd.ExcelWriter = pd.ExcelWriter("vetting_results.xlsx",
                                              engine='xlsxwriter')

# %% [markdown]
# Then create the list of `CriterionTargetRangeOutput` instances, one for each
# AR6 vetting criterion. Each instance needs a `DataFrameExcelWriter` instance
# to write the results to a different worksheet of the same Excel file. The
# worksheets will have the same name as the corresponding vetting criterion, but
# with the name potentially shortened and with some characters substituted to
# make sure that they are valid names for Excel worksheets.
# %%
vetting_results_outputs: list[
    CriterionTargetRangeOutput[DataFrameExcelWriter, None]
] = [
    CriterionTargetRangeOutput(
        criteria=_crit_target,
        writer=DataFrameExcelWriter(
            results_excel_writer,
            sheet_name=make_valid_excel_sheetname(_crit_target.name)
        )
    )
    for _crit_target in vetting_targets
]

# %% [markdown]
# Finally, we call the `write_results` method of each of the
# `CriterionTargetRangeOutput` instances, to compute the results and write them
# to the Excel file.
#
# The results are also returned as `pandas.DataFrame` objects in the list
# `vetting_results_frames`.
#
# `results_excel_writer.close()` must be called at the end to close and save the
# Excel file.
# %%
vetting_results_frames: list[pd.DataFrame] = []
for _output in vetting_results_outputs:
    _frame, _ = _output.write_results(iam_df)
    vetting_results_frames.append(_frame)
results_excel_writer.close()

# %% [markdown]
# # Assess agreement with harmonisation data for population and GDP.
#
# The cells below will compare the model results in `iam_df` with the
# harmonization data for population and GDP in each region that is defined
# (has the same name) in both the harmonization data and in any of the models
# in `iam_df`. Note that it does not currently take into account differences
# in region definitions, or aggregate or translate model-specific region names
# used in different models. This is intended for a future version.
#
# To be assessed, `iam_df` needs to contain population data in a variable named
# `Population` and GDP data in a variable named `GDP|PPP`. The GDP data must be
# be in purchasing-power parity terms (PPP), and the unit name must have the
# form `billion CCC_YYYY/yr`, where `CCC` is the currency code and `YYYY` is the
# year. For example, `billion USD_2017/yr` for 2017 US dollars (which in this
# case is also called "international dollars", since the GDP should be converted
# to USD using purchasing-power parity (PPP) rather than market exchange rates
# (MER).
#
# The results are returned as a `pandas.DataFrame` and written to an Excel file
# as the ratio between the values in `iam_df` relative to the harmonization
# data, for each data point that exists in both data sets. If a given model and
# scenario agrees precisely with the harmonization data, the corresponding value
# in the result will be 1.0. If the model has a smaller or greater value than
# the harmonization data, the value in the result will be smaller or greater
# than 1.0, respectively.
#
# Generally, for population and GDP, the ratios should be between 0.98 and 1.02
# to be considered a close match. Values outside that range suggest that either
# the model/scenario has used data that do not agree with the harmonization
# data, or that there are issues with currency conversions, region definitions
# or other inconsistencies or mistakes.
#
# First get just the GDP and Population variables from the data. Assert that it
# is not None (not necessary, but if you use Python with a type checker, it is
# needed to avoid a warning, since the `IamDataFrame.filter` method can return
# None):
# %%
iam_df_pop_gdp = iam_df.filter(variable=['Population', 'GDP|PPP'])
assert iam_df_pop_gdp is not None

# %% [markdown]
# Then define a Path to where you want to write an Excel file with the results
# at the moment it writes it to the file `gdp_pop_harmonization_assessment.xlsx`
# in the current working directory, but you can change this to your liking.
# Consult the Python documentation for `pathlib.Path` if you are unfamiliar with
# how to use Path objects.
# %%
gdp_pop_harmonization_assessment_output_file: Path = \
    Path.cwd() / 'gdp_pop_harmonization_assessment.xlsx'

# %% [markdown]
# Then create a `DataFrameExcelWriter` instance that will do the actual writing
# to Excel:
# %%
gdp_pop_harmonization_assessment_writer: DataFrameExcelWriter = \
    DataFrameExcelWriter(
        file=gdp_pop_harmonization_assessment_output_file,
        sheet_name='Results vs harmonization ratio',
    )

# %% [markdown]
# Define a `TimeseriesComparisonFullDataOutput` instance, which will calculate
# the results, and use `gdp_pop_harmonization_assessment_writer` to write the
# results to the Excel file.
# %%
gdp_pop_harmonization_assessment_output: \
    TimeseriesComparisonFullDataOutput[
        IamCompactHarmonizationRatioCriterion,
        DataFrameExcelWriter,
        None,
] = TimeseriesComparisonFullDataOutput(
    criteria=gdp_pop_harmonization_criterion,
    writer=gdp_pop_harmonization_assessment_writer
)
# %%
gdp_pop_harmonization_result, _ignore = \
    gdp_pop_harmonization_assessment_output.write_results(iam_df_pop_gdp)

# %% [markdown]
# Then close the workbook to save it.
# %%
gdp_pop_harmonization_assessment_output.writer.close()
