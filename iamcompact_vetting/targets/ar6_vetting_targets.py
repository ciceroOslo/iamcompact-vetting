"""Vetting criteria and targets/ranges for IPCC AR6.

Credit: The Criterion objects used here are originally taken from example
notebooks in the `pathways_ensemble_analysis` package repository.
"""
from pathways_ensemble_analysis.criteria.base import (
    Criterion,
    SingleVariableCriterion,
    ChangeOverTimeCriterion,
)

from .target_classes import CriterionTargetRange



# Temporarily define all the Criterion objets as part of a `vetting_criteria`
# list. This should be refactored into a list of `CriterionTargetRange` objects
# afterwards.

vetting_criteria = []

# Historical emissions

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CO2 total (EIP + AFOLU) emissions 2020",
        region="World",
        year=2020,
        variable="Emissions|CO2",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CO2 EIP emissions 2020",
        region="World",
        year=2020,
        variable="Emissions|CO2|Energy and Industrial Processes",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CH4 emissions 2020",
        region="World",
        year=2020,
        variable="Emissions|CH4",
        unit="Mt CH4 / yr",
    )
)

vetting_criteria.append(
    ChangeOverTimeCriterion(
        criterion_name="CO2 EIP emissions 2010-2020 change",
        region="World",
        year=2020,
        reference_year=2010,
        variable="Emissions|CO2|Energy and Industrial Processes",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CCS from energy 2020",
        region="World",
        year=2020,
        variable="Carbon Sequestration|CCS|Energy",
        unit="Mt CO2 / yr",
    )
)

# Historical energy production

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Primary Energy 2020",
        region="World",
        year=2020,
        variable="Primary Energy",
        unit="EJ / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Electricity: nuclear 2020",
        region="World",
        year=2020,
        variable="Secondary Energy|Electricity|Nuclear",
        unit="EJ / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Electricity: solar and wind 2020",
        region="World",
        year=2020,
        variable="Secondary Energy|Electricity|Wind and Solar",
        unit="EJ / yr",
    )
)

# Future criteria

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CO2 EIP emissions 2030",
        region="World",
        year=2030,
        variable="Emissions|CO2|Energy and Industrial Processes",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CCS from energy 2030",
        region="World",
        year=2030,
        variable="Carbon Sequestration|CCS|Energy",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Electricity: nuclear 2030",
        region="World",
        year=2030,
        variable="Secondary Energy|Electricity|Nuclear",
        unit="EJ / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CH4 emissions 2040",
        region="World",
        year=2040,
        variable="Emissions|CH4",
        unit="Mt CH4 / yr",
    )
)

# Additionally defined criteria (which are not investigated in the AR6 vetting process

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CO2 EIP emissions 2050",
        region="World",
        year=2050,
        variable="Emissions|CO2|Energy and Industrial Processes",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="CCS from energy 2050",
        region="World",
        year=2050,
        variable="Carbon Sequestration|CCS|Energy",
        unit="Mt CO2 / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Electricity: nuclear 2050",
        region="World",
        year=2050,
        variable="Secondary Energy|Electricity|Nuclear",
        unit="EJ / yr",
    )
)

vetting_criteria.append(
    SingleVariableCriterion(
        criterion_name="Electricity: solar and wind 2050",
        region="World",
        year=2050,
        variable="Secondary Energy|Electricity|Wind and Solar",
        unit="EJ / yr",
    )
)