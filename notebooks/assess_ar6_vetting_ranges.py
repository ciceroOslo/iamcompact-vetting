"""Notebook to assess AR6 vetting ranges for a user-provided IamDataFrame."""

# %% [markdown]
# # Imports
# %%
from pathlib import Path

import pyam
import pandas as pd

from iamcompact_vetting.targets.ar6_vetting_targets import (
    vetting_targets_historical,
)
from iamcompact_vetting.targets.target_classes import(
    CriterionTargetRange,
)


# %% [markdown]
# # Get the model/scenario data to be assessed.
#
# In the code cell below, add code to load the data you want to assess and
# assign it to the variable `iam_df`. This can be done either by using
# `pyam.IamDataFrame` to read from an Excel or CSV file, or by importing
# your own code that loads and/or processes the data.
# %%
# from cycle1_study_model_outputs import joint_iamdf
from cycle1_study_model_outputs.cycle1_results import joint_iamdf

iam_df: pyam.IamDataFrame = joint_iamdf

# %%[markdown]
# # Assess the AR6 vetting ranges
# %%
vetting_results: pd.DataFrame = \
    vetting_targets_historical[0].get_distances_in_range(iam_df)

# %% [markdown]
# # Get criterion values
# %%
criterion_values: pd.Series = vetting_targets_historical[0].get_values(iam_df)
