"""Base and default classes for defining styles for output."""
from collections.abc import Callable, Hashable, Mapping,  Sequence
import dataclasses
import typing as tp

import pandas as pd

from ..base import CTCol



class PandasFormatParams(tp.TypedDict, total=False):
    """Parameters accepted by `pandas.DataFrame.style.format`."""

    formatter: tp.Optional[
        str | tp.Callable[[tp.Any], str] \
            | dict[str, str | tp.Callable[[tp.Any], str]]
    ]
    subset: tp.Optional[
        Hashable | Sequence[Hashable] | tuple[Hashable|slice, ...]
    ]
    na_rep: tp.Optional[str]
    precision: tp.Optional[int]
    decimal: tp.Optional[str]
    thousands: tp.Optional[str]
    escape: tp.Optional[str | tp.Literal['html', 'latex', 'latex-math']]
    hyperlinks: tp.Optional[tp.Literal['html', 'latex']]
###END class PdFormatParams



@dataclasses.dataclass(kw_only=True)
class PandasFormaterMixin:
    """Mixin for style classes that format pandas DataFrames.

    Provides an attribute to set what parameters to pass to the
    `pandas.DataFrame.style.format` method.
    """

    FORMAT: PandasFormatParams = dataclasses.field(
        default_factory=lambda: PandasFormatParams()
    )

###END dataclass class PandasFormaterMixin


@dataclasses.dataclass(kw_only=True)
class PassFailStyles:
    """Styling for cells and columns with pass/fail data.

    Each attribute provides a CSS string that to be applied to cells with the
    corresponding type of status value.
    """

    PASS: str = 'color: green'
    """Used to indicate a passed check."""

    FAIL: str = 'color: red; font-weight: bold'
    """Used to indicate a failed check."""

    NA: str = 'color: black; background-color: lightgrey'
    """Used to indicate values that are missing or could not be assessed."""

###END dataclass class PassFailStyles


@dataclasses.dataclass
class InRangeStyles:
    """Styling for cells that fall within or outside a certain range."""

    IN_RANGE: str = ''
    """Used to indicate cells that fall within a given range."""

    ABOVE_RANGE: str = 'color: violet; font-weight: bold'
    """Indicates cells that are above the range."""

    BELOW_RANGE: str = 'color: red; font-weight: bold'
    """Indicates cells that are below the range."""

    NA: str = 'color: black; background-color: lightgrey'
    """Used to indicate values that are missing or could not be assessed."""

###END dataclass class InRangeStyles


CriterionRangeStyles = dataclasses.make_dataclass(
    'CriterionRangeStyles',
    fields=[
        (CTCol.INRANGE, PassFailStyles,
         dataclasses.field(default_factory=PassFailStyles)),
        (CTCol.VALUE, InRangeStyles,
         dataclasses.field(default_factory=InRangeStyles)),
        (CTCol.DISTANCE, InRangeStyles,
         dataclasses.field(default_factory=InRangeStyles)),
    ]
)
