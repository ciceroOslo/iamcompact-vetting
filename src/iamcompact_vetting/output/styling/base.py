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


@dataclasses.dataclass(kw_only=True)
class CriterionTargetRangeOutputStyles(
    Mapping[str|CTCol, PassFailStyles|InRangeStyles]
):
    """Styles for output of `CriterionTargetRangeOutput.
    
    Note that the attribute names of this dataclass must be the same as the
    string values of the enums in `CTCol`. If the latter change, the attribute
    names here must change as well.

    Also note that if you subclass this dataclass and add new attributes, you
    must prefix the subclass definition with the `@dataclasses.dataclass`
    decorator.
    """

    in_range: PassFailStyles = dataclasses.field(default_factory=PassFailStyles)
    """Styling for cells in the `CTCol.INRANGE` column."""

    value: InRangeStyles = dataclasses.field(default_factory=InRangeStyles)
    """Styling for cells in the `CTCol.VALUE` column."""

    distance: InRangeStyles = dataclasses.field(default_factory=InRangeStyles)
    """Styling for cells in the `CTCol.DISTANCE` column."""

    # Implement abstract methods from `collections.abc.Mapping`

    def __getitem__(self, key: str|CTCol) -> PassFailStyles|InRangeStyles:
        return getattr(self, str(key))
    ###END def CriterionTargetRangeOutputStyles.__getitem__

    def __len__(self) -> int:
        return len(dataclasses.fields(self))
    ###END def CriterionTargetRangeOutputStyles.__len__

    def __iter__(self) -> tp.Iterator[str]:
        return (_field.name for _field in dataclasses.fields(self))
    ###END def CriterionTargetRangeOutputStyles.__iter__

###END class CriterionTargetRangeOutputStyles

# Check that the field names of the `CriterionTargetRangeOutputStyles` class
# match the enum names in `CTCol`. In the future, maybe this should be made into
# __subclass_init__ method instead.
assert all(
    _field.name in CTCol
    for _field in dataclasses.fields(CriterionTargetRangeOutputStyles)
)
