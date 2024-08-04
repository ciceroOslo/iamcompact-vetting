"""Functionality for defining Criterion targets and ranges."""
import typing as tp
from collections.abc import Callable

import pyam
import pandas as pd
from pathways_ensemble_analysis.criteria.base import Criterion



class InvalidRangeError(ValueError):
    """Raised if the range does not contain the target value."""
    ...
###END class InvalidRangeError

class UnitNotSpecifiedError(ValueError):
    """Raised if unit spec parameters are not sufficiently specified."""
    ...
###END class UnitNotSpecifiedError


class CriterionTargetRange:
    """Class for defining Criterion value targets and ranges.

    Init parameters
    ---------------
    criterion : Criterion
        Criterion instance for calculating the values that will be compared to
        the target.
    target : float
        Target value for the criterion.
    range : tuple[float, float], optional
        Tuple with lower and upper limit for the criterion values. Optional,
        defaults to None. An `InvalidRangeError` will be raised if the range
        does not contain the target value.
    unit : str, optional
        Unit of `target`. Optional, defaults to None.
    name : str, optional
        Name of the target. Optional, defaults to `criterion.criterion_name`.
    convert_value_units : bool, optional
        Whether to convert the criterion values returned by
        `criterion.get_values` to `unit`. If True, either `value_unit` must be
        specified, or `criterion.unit` must exist and not be None (`value_unit`
        overrides `criterion.unit` if both are specified), or a
        `UnitNotSpecifiedError` will be raised. If None, values will be
        converted if both `unit` and `criterion.unit` are specified, otherwise
        not. Note that `value_unit` is ignored if `convert_value_units` is None.
        If you want to specify `value_unit`, `convert_value_units` should be
        explicitly set to True. Optional, defaults to None.
    convert_input_units : bool, optional
        Whether to convert the units of `IamDataFrame` objects passed to
        `get_distance_values` to `unit` before passing to
        `criterion.get_values`. This should probably be False if the class of
        `criterion` already does unit conversion internally. If True,
        `get_distance_values` will attempt to convert every unit in the input
        `IamDataFrame` to `unit`, so the user must ensure that `unit` is
        compatible with all units in the input `IamDataFrame`. A
        `UnitNotSpecifiedError` will be raised if `unit` is not specified.
        Optional, defaults to False.
    value_unit : str, optional
        Unit to convert the values returned by `criterion.get_values` from if
        `convert_value_units` is True. Optional, defaults to None.
    distance_func : callable, optional
        Distance function to apply to the criterion values. Should take a float
        and return a float. Is intended to measure how far the criterion values
        are from the target. Optional. If `range` is None, it will default to a
        function that returns the criterion value minus `target` (i.e., can be
        both positive and negative). If `range` is not None, it will default to
        a function that returns the criterion value minus the target, divided by
        the distance between the target and the upper bound if the value is
        greater than the target, and divided by the distance between the target
        and the lower bound if the value is less than the target (i.e., it will
        be `0` if the value is equal to the target, `1` if it is equal to the
        upper bound, and `-1` if it is equal to the lower bound).
    """

    _unit: str|None = None
    _convert_value_units: bool|None = None
    _convert_input_units: bool = False
    _value_unit: str|None = None
    _range: tuple[float, float]|None = None

    def __init__(
            self,
            criterion: Criterion,
            target: float,
            range: tp.Optional[tuple[float, float]] = None,
            unit: tp.Optional[str] = None,
            name: tp.Optional[str] = None,
            convert_value_units: tp.Optional[bool] = None,
            convert_input_units: bool = False,
            value_unit: tp.Optional[str] = None,
            distance_func: tp.Optional[Callable[[float], float]] = None,
    ):
        self._criterion: Criterion = criterion
        self.name: str = criterion.criterion_name if name is None else name
        self.target = target
        self.range = range
        _convert_value_units: bool
        if convert_value_units is not None:
            _convert_value_units = convert_value_units
        else:
            if (unit is not None) and \
                    (getattr(criterion, 'unit', None) is not None):
                _convert_value_units = True
            else:
                _convert_value_units = False
        self._set_unit_specs(
            unit=unit,
            convert_value_units=_convert_value_units,
            value_unit=value_unit,
            convert_input_units=convert_input_units,
            check_specs=True,
        )
        if distance_func is not None:
            self.distance_func: Callable[[float], float] = distance_func
        else:
            self.distance_func = self._default_distance_func
    ###END def CriterionTargetRange.__init__

    @staticmethod
    def _distance_func_without_range(value: float, target: float) -> float:
        return value - target
    ###END staticmethod def CriterionTargetRange._distance_func_without_range

    @staticmethod
    def _distance_func_with_range(
            value: float,
            target: float,
            range: tuple[float, float]
    ) -> float:
        if value > target:
            return (value - target) / (range[1] - target)
        else:
            return (target - value) / (target - range[0])
    ###END def CriterionTargetRange._distance_func_with_range

    def _default_distance_func(self, value: float) -> float:
        if self.range is None:
            return self._distance_func_without_range(value, self.target)
        else:
            return self._distance_func_with_range(value, self.target, self.range)
    ###END def CriterionTarget._default_distance_func

    @property
    def target(self) -> float:
        """Target value for the criterion."""
        return self._target
    @target.setter
    def target(self, value: float):
        if self.range is not None \
                and (value < self.range[0] or value > self.range[1]):
            raise ValueError(
                f"Target value {value} is outside of range {self.range}."
            )
        self._target: float = value

    @property
    def range(self) -> tuple[float, float]|None:
        """Tuple with lower and upper limit for the criterion values."""
        return self._range
    @range.setter
    def range(self, value: tuple[float, float]|None):
        if value is not None:
            if value[0] > value[1]:
                raise ValueError('Lower bound of range must be less than '
                                 'upper bound.')
            if self.target < value[0] or self.target > value[1]:
                raise InvalidRangeError(
                    f"Target value {self.target} is outside of range {value}."
                )
        self._range: tuple[float, float]|None = value

    def _check_unit_specs(
            self,
            criterion: tp.Optional[Criterion] = None,
            unit: tp.Optional[str] = None,
            value_unit: tp.Optional[str] = None,
            convert_value_units: tp.Optional[bool] = None,
            convert_input_units: tp.Optional[bool] = None,
    ) -> None:
        """Checks that unit specification parameters are sufficient.
        
        Raises a `UnitNotSpecifiedError` if the unit specification parameters are not
        sufficiently specified. See init parameter documentation for details.
        """
        if criterion is None:
            criterion = self._criterion
        if unit is None:
            unit = self.unit
        if value_unit is None:
            value_unit = self.value_unit
        if convert_value_units is None:
            convert_value_units = self.convert_value_units
        if convert_input_units is None:
            convert_input_units = self.convert_input_units
        if convert_value_units:
            if unit is None:
                raise UnitNotSpecifiedError(
                    '`unit` must be specified if `convert_value_units` is True.'
                )
            else:
                if (criterion is None) or (not hasattr(criterion, 'unit')) \
                        or (criterion.unit is None):  # pyright: ignore[reportAttributeAccessIssue]
                    raise UnitNotSpecifiedError(
                        '`unit` or `criterion.unit` must be specified if '
                        '`convert_value_units` is True.'
                    )
        if convert_input_units:
            if unit is None:
                raise UnitNotSpecifiedError(
                    '`unit` must be specified if `convert_input_units` is True.'
                )
    ###END def CriterionTargetRange._check_unit_specs

    def _set_unit_specs(
            self,
            unit: str|None,
            value_unit: str|None,
            convert_value_units: bool|None,
            convert_input_units: bool,
            check_specs: bool = True,
    ) -> None:
        """Set the full set of unit specification parameters.
        
        This method is needed since the unit specification parameters are
        mutually dependent, and each of them has a setter method that checks the
        current value of the others before setting the value.

        Each parameter in the list below before `check_specs` is required, and
        the will be set as the value of the corresponding attribute with a `_`
        prefix to the attribute name.

        Parameters
        ----------
        unit : str or None
        value_unit : str or None
        convert_value_units : bool or None
        convert_input_units : bool
        check_specs : bool, optional
            Whether to check that the unit specification parameters are
            sufficiently specified. If True, a `UnitNotSpecifiedError` will be
            raised if the unit specification parameters are not sufficiently
            specified. If False, the values will be set as specified regardless.
            *NB!* Setting this parameter to False is very likely to lead to
            unpredictable results and possibly silent errors. Doing so is not
            recommended unless absolutely necessary.

        Raises
        ------
        UnitNotSpecifiedError
            If the unit specification parameters are not sufficiently specified
            and `check_specs` is True.
        """
        if check_specs:
            self._check_unit_specs(
                criterion=self._criterion,
                unit=unit,
                value_unit=value_unit,
                convert_value_units=convert_value_units,
                convert_input_units=convert_input_units,
            )
        self._unit = unit
        self._value_unit = value_unit
        self._convert_value_units = convert_value_units
        self._convert_input_units = convert_input_units
    ###END def CriterionTargetRange._set_unit_specs


    @property
    def unit(self) -> str|None:
        """Unit for the criterion values."""
        return self._unit
    @unit.setter
    def unit(self, value: str|None):
        self._check_unit_specs(unit=value)
        self._unit: str|None = value

    @property
    def value_unit(self) -> str|None:
        """Unit for the criterion values."""
        return self._value_unit
    @value_unit.setter
    def value_unit(self, value: str|None):
        self._check_unit_specs(value_unit=value)
        self._value_unit: str|None = value

    @property
    def convert_value_units(self) -> bool|None:
        return self._convert_value_units
    @convert_value_units.setter
    def convert_value_units(self, value: bool|None):
        self._check_unit_specs(convert_value_units=value)
        self._convert_value_units: bool|None = value

    @property
    def convert_input_units(self) -> bool:
        return self._convert_input_units
    @convert_input_units.setter
    def convert_input_units(self, value: bool):
        self._check_unit_specs(convert_input_units=value)
        self._convert_input_units: bool = value

    def in_range(self, value: float) -> bool:
        """Checks whether a single number is in the target range.
        
        Only works on single numbers. Pass it to the pandas `apply` method if
        you have a Series or DataFrame of numbers.

        Raises a `ValueError` if `self.range` is not specified.
        """
        if self.range is None:
            raise ValueError('`self.range` must be specified to use `in_range`.')
        return self.range[0] <= value <= self.range[1]
    ###END def CriterionTargetRange.in_range

###END class CriterionTargetRange
