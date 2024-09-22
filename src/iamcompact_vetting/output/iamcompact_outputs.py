"""ResultOutput items that provide assessment outputs for IAM COMPACT."""
from collections.abc import Callable, Mapping, Sequence
import typing as tp

import pandas as pd
import pyam

from .base import (
    CriterionTargetRangeOutput,
    CTCol,
    MultiCriterionTargetRangeOutput,
    NoWriter,
)
from .excel import (
    MultiDataFrameExcelWriter,
    make_valid_excel_sheetname,
)
from ..pea_timeseries.timeseries_criteria_core import (
    AggDims,
    TimeseriesRefCriterion
)
from .styling.base import CriterionTargetRangeOutputStyles
from .timeseries import (
    TimeseriesRefComparisonAndTargetOutput,
    TimeseriesRefFullComparisonOutput,
)
from ..targets.ar6_vetting_targets import vetting_targets as ar6_vetting_targets
from ..targets.iamcompact_harmonization_targets import (
    IamCompactHarmonizationRatioCriterion,
    IamCompactHarmonizationTarget,
)
from ..targets.target_classes import (
    CriterionTargetRange,
)



class IamCompactMultiTargetRangeOutput(
    MultiCriterionTargetRangeOutput[
        CriterionTargetRange,
        CriterionTargetRangeOutput,
        MultiDataFrameExcelWriter | NoWriter
    ]
):
    """MultiCriterionTargetRangeOutput subclass for IAM COMPACT.

    Used to produce the output for the IPCC AR6 vetting checks. The class sets
    appropriate defaults and overrides to the MultiCriterionTargetRangeOutput
    superclass, but does not introduce new methods or other functionality.

    By default, the output will include the `INRANGE` and `VALUE` columns, which
    will include the pass/fail status of each criterion and the value of the
    assessed variable/parameter, respectively. By default, the columns will have
    the names `"Passed"` and `"Value"`, respectively. This can be overridden by
    keyword arguments passed to the superclass.

    Init Parameters
    ---------------
    criteria : Mapping[str, CriterionTargetRange]
        Mapping of criterion names to CriterionTargetRange instances that define
        the vetting checks to be performed. The keys of the dictionary are used
        as keys in the output. When writing output to Excel, the same titles
        will be truncated to at most 31 characters and used as names for the
        worksheets in the Excel file.
    writer : MultiDataFrameExcelWriter or NoWriter, optional
        Writer that will be used to write the output to an Excel file. If not
        provided, a NoWriter instance will be used, and calling the
        `write_output` or `write_results` method will raise an exception.
    **kwargs
        Additional keyword arguments to be passed to the superclass. See the
        documentation of `MultiCriterionTargetRangeOutput` for details.
    """

    _default_columns = [CTCol.INRANGE, CTCol.VALUE]  # Sets defaults, overrides
                                                     # the superclass
    _default_column_titles = {  # Sets defaults, overrides the superclass
        CTCol.INRANGE: 'Passed',
        CTCol.VALUE: 'Value',
    }
    _default_summary_keys = {  # Sets defaults, overrides the superclass
        CTCol.INRANGE: 'Pass vs. Fail Summary',
        CTCol.VALUE: 'Values Summary',
    }

    def __init__(
            self,
            criteria: Mapping[str, CriterionTargetRange],
            writer: tp.Optional[MultiDataFrameExcelWriter|NoWriter] = None,
            **kwargs: tp.Unpack[MultiCriterionTargetRangeOutput.InitKwargsType],
    ):
        if writer is None:
            writer = NoWriter()
        super().__init__(criteria=criteria, writer=writer, **kwargs)
    ###END def IamCompactMultiTargetRangeOutput.__init__

###END class IamCompactMultiTargetRangeOutput


# The declaration of ar6_vetting_target_range_output should be changed to use a
# an IamCompactMultiTargetRangeOutput object instead. Keeping it as-is for now
# to use as a model for how to define the IamCompactMultiTargetRangeOutput
# class.
ar6_vetting_target_range_output = IamCompactMultiTargetRangeOutput(
    criteria={_crit.name: _crit for _crit in ar6_vetting_targets},
    writer=NoWriter(),
)


class IamCompactTimeseriesRefComparisonOutput(
    TimeseriesRefComparisonAndTargetOutput[
        IamCompactHarmonizationRatioCriterion,
        IamCompactHarmonizationTarget,
        TimeseriesRefFullComparisonOutput,
        CriterionTargetRangeOutput,
        MultiDataFrameExcelWriter | NoWriter,
        None,
        CriterionTargetRangeOutputStyles
    ]
):
    """TimeseriesRefComparisonAndTargetOutput for IAM COMPACT harmonization.

    Used to produce outout for harmonization vetting checks.
    """

    def __init__(
            self,
            reference: pyam.IamDataFrame \
                | IamCompactHarmonizationRatioCriterion,
            criterion_name: tp.Optional[str] = None,
            *,
            comparison_function: tp.Optional[
                Callable[[pyam.IamDataFrame, pyam.IamDataFrame], pd.Series]
            ] = None,
            range: tp.Optional[tuple[float, float]] = None,
            target: tp.Optional[float] = None,
            region_agg: tp.Optional[TimeseriesRefCriterion.AggFuncArg] = None,
            time_agg: tp.Optional[TimeseriesRefCriterion.AggFuncArg] = None,
            default_agg_dims: tp.Optional[AggDims] = None,
            broadcast_dims: tp.Optional[tp.Iterable[str]] = None,
            full_comparison_key: tp.Optional[str] = None,
            summary_key: tp.Optional[str] = None,
            summary_columns: tp.Optional[Sequence[CTCol]] = None,
            summary_column_titles: tp.Optional[Mapping[CTCol, str]] = None,
            style: tp.Optional[CriterionTargetRangeOutputStyles] = None,
            writer: tp.Optional[MultiDataFrameExcelWriter|NoWriter] = None,
    ) -> None:
        """
        Parameters
        ----------
        reference : pyam.IamDataFrame | IamCompactHarmonizationRatioCriterion
            IamDataFrame of harmonized data values to compare against. Can also
            be an IamCompactHarmonizationRatioCriterion instance that contains
            the desired reference values, in which case the parameters
            `criterion_name`, `comparison_function`, `region_agg`, `time_agg`,
            `default_agg_dims`, and `broadcast_dims` will all be ignored if
            given.
        criterion_name : str, optional
            A name to identify the criterion, if an existing criterion is not
            given through `reference`. Is required if `reference` is None.
        comparison_function, region_agg, time_agg, default_agg_dims, broadcast_dims
            Passed to the `IamCompactHarmonizationRatioCriterion` init method
            together with `reference`(if `reference` is not already an
            `IamCompactHarmonizationRatioCriterion` instance, in which case
            these parameters are all ignored). See the documentation of
            `IamCompactHarmonizationRatioCriterion` and `TimeseriesRefCriterion`
            for how these parameters are used.
        target : float, optional
            Target value for what the return value from `comparison_function`
            should be when comparing the reference and the data to be vetted.
            When `comparison_function` is None, it defaults to taking the ratio
            of the data to be vetted to the reference values. In that case,
            1.0 is usually the most suitable value for `target`, which is
            therefore also the default value when not specified.
        range : tuple[float, float], optional
            Range of acceptable values for the return value from
            `comparison_function`. Optional. If not specified, it defaults to
            `(1.0-default_tol, 1.0+default_tol)`, where `default_tol` is equal
            to `IAMCOMPACT_HARMONIZATION_DEFAULT_TOLERANCE`, which is usually
            0.02, i.e., that a deviation of +/- 2% is acceptable.
        full_comparison_key : str, optional
            The key to use for the `DataFrame` with the full comparison values
            (output of `comparison_function` for all points in all
            non-aggregated dimensions) in the dict returned by `prepare_output`
            and `prepare_styled_output`. When writing to Excel with
            `MultiDataFrameExcelWriter`, this will also be used as the
            corresponding worksheet name. Optional, defaults to `"Full
            comparison"`.
        summary_key : str, optional
            The key to use for the `DataFrame` with the summary values in the
            dict returned by `prepare_output` and `prepare_styled_output`. When
            writing to Excel with `MultiDataFrameExcelWriter`, this will also
            be used as the corresponding worksheet name. Optional, defaults to
            `"Summary"`.
        summary_columns : Sequence[CTCol], optional
            The columns to use for the summary values in the summary DataFrame
            in the dict returned by `prepare_output` and
            `prepare_styled_output`. Optional, defaults to `[CTCol.INRANGE,
            CTCol.VALUE]`, i.e., a column with in-range/out-of-range boolean
            values, a column with aggregated return values from
            `comparison_function` and a column with the
        summary_column_titles : Mapping[CTCol, str], optional
            The titles to use for the summary columns in the summary DataFrame.
            Optional, defaults to `{CTCol.INRANGE: "In range",
            CTCol.VALUE: "Comparison values"}`.
        """
        if isinstance(reference, IamCompactHarmonizationRatioCriterion):
            criterion: IamCompactHarmonizationRatioCriterion = reference
        else:
            if criterion_name is None:
                raise ValueError(
                    'criterion_name must be given if reference is not an '
                    'IamCompactHarmonizationRatioCriterion instance'
                )
            criterion = IamCompactHarmonizationRatioCriterion(
                criterion_name=criterion_name,
                reference=reference,
                comparison_function=comparison_function,
                region_agg=region_agg,
                time_agg=time_agg,
                default_agg_dims=default_agg_dims,
                broadcast_dims=broadcast_dims,
            )
        if summary_key is None:
            summary_key = 'Summary'
        if full_comparison_key is None:
            full_comparison_key = 'Full comparison'
        if writer is None:
            writer = NoWriter()
        if summary_columns is None:
            summary_columns = [CTCol.INRANGE, CTCol.VALUE]
        if summary_column_titles is None:
            summary_column_titles = {
                CTCol.INRANGE: 'In range',
                CTCol.VALUE: 'Comparison values',
            }
        def _make_summary_output_obj(
                _target_range: IamCompactHarmonizationTarget,
        ) -> CriterionTargetRangeOutput:
            return CriterionTargetRangeOutput(
                criteria=_target_range,
                writer=writer,
                columns=summary_columns,
                column_titles=summary_column_titles
            )
        super().__init__(
            criteria=criterion,
            target_range_type=IamCompactHarmonizationTarget,
            target=target,
            range=range,
            timeseries_output_type=TimeseriesRefFullComparisonOutput,
            summary_output=_make_summary_output_obj,
            full_comparison_key=full_comparison_key,
            summary_key=summary_key,
            style=style,
            writer=writer,
        )
    ###END def IamCompactHarmonizationRatioCriterion.__init__

###END class IamCompactHarmonizationRatioCriterion
