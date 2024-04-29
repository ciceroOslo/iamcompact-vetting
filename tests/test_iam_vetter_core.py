"""Tests for the IAM Vetter Core module.

In particular contains setting up test data and performing tests on the
`iamcompact_vetting.iam.iam_vetter_core.IamDataFrameTimeseriesVetter` class.
"""
import typing as tp
import unittest

import pandas as pd
from pyam import IamDataFrame
import pyam

from iamcompact_vetting.iam.iam_vetter_core import IamDataFrameTimeseriesVetter


# Construct an IamDataFrame with years 2005, 2010, 2015, 2020, 2025, 2030, and 2
# variables 'Primary Energy' and 'Secondary Energy|Electricity', with two models
# 'ModelA' and 'ModelB', and two scenarios 'Scenario1' and 'Scenario2', as well
# as three regions 'Region1', 'Region2', and 'Region3'. 'Secondary
# Energy|Electricity' should have units 'EJ/yr' for 'ModelA' and 'TWh/yr' for
# 'ModelB'. 'Primary Energy' should have numbers that vary between 1 and 100 in
# all cases, and 'Secondary Energy|Electricity' should have numbers that vary
# between 0.1 and 10 when the unit is 'EJ/yr' and 30 and 3000 when the unit is
# 'TWh/yr'.
def construct_test_iamdf() -> IamDataFrame:
    """Construct a test IamDataFrame for testing the IamDataFrameTimeseriesVetter."""
    data = [
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2005, 1.0),
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2010, 2.0),
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2015, 3.5),
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2020, 5.0),
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2025, 5.5),
        ('ModelA', 'Scenario1', 'Region1', 'Primary Energy', 'EJ/yr', 2030, 4.75),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2005, 0.1),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2010, 0.3),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2015, 0.5),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2020, 0.7),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2025, 0.9),
        ('ModelA', 'Scenario1', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2030, 1.1),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2005, 30.0),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2010, 40.0),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2015, 50.0),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2020, 60.0),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2025, 70.0),
        ('ModelA', 'Scenario1', 'Region2', 'Primary Energy', 'EJ/yr', 2030, 80.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2005, 3.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2010, 4.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2015, 5.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2020, 6.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2025, 7.0),
        ('ModelA', 'Scenario1', 'Region2', 'Secondary Energy|Electricity', 'EJ/yr', 2030, 8.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2005, 10.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2010, 20.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2015, 30.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2020, 40.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2025, 50.0),
        ('ModelA', 'Scenario1', 'Region3', 'Primary Energy', 'EJ/yr', 2030, 60.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2005, 1.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2010, 2.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2015, 3.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2020, 4.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2025, 5.0),
        ('ModelA', 'Scenario1', 'Region3', 'Secondary Energy|Electricity', 'EJ/yr', 2030, 6.0),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2005, 1.0),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2010, 2.0),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2015, 3.5),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2020, 5.0),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2025, 5.5),
        ('ModelA', 'Scenario2', 'Region1', 'Primary Energy', 'EJ/yr', 2030, 4.75),
        ('ModelA', 'Scenario2', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2005, 0.1),
        ('ModelA', 'Scenario2', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2010, 0.3),
        ('ModelA', 'Scenario2', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr', 2015, 0.5),
        ('ModelA', 'Scenario2', 'Region1', 'Secondary Energy|Electricity', 'EJ/yr',
    ]