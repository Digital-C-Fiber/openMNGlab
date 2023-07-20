from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Collection, TypeVar, Generic, Iterable, Mapping, Sequence

from openmnglab.datamodel.exceptions import DataSchemeCompatibilityError
from openmnglab.model.datamodel.interface import IInputDataScheme, IOutputDataScheme
from openmnglab.model.functions.interface import IFunctionDefinition, ProxyRet
from openmnglab.model.planning.interface import IExecutionPlanner, IProxyData
from openmnglab.model.planning.plan.interface import IExecutionPlan, IStage, IPlannedData, IPlannedElement
from openmnglab.planning.exceptions import InvalidFunctionArgumentCountError, FunctionArgumentSchemaError, PlanningError
from openmnglab.util.iterables import ensure_iterable, ensure_sequence


def check_input(expected_schemes: Sequence[IInputDataScheme] | IInputDataScheme | None,
                actual_schemes: Sequence[IOutputDataScheme] | IOutputDataScheme | None):
    expected_schemes: Sequence[IInputDataScheme] = ensure_sequence(expected_schemes, IInputDataScheme)
    actual_schemes: Sequence[IOutputDataScheme] = ensure_sequence(actual_schemes, IOutputDataScheme)
    if len(expected_schemes) != len(actual_schemes):
        raise InvalidFunctionArgumentCountError(len(expected_schemes), len(actual_schemes))
    for pos, (expected_scheme, actual_scheme) in enumerate(zip(expected_schemes, actual_schemes)):
        expected_scheme: IInputDataScheme
        actual_scheme: IOutputDataScheme
        try:
            if not expected_scheme.accepts(actual_scheme):
                raise DataSchemeCompatibilityError("Expected scheme is not compatible with actual scheme")
        except DataSchemeCompatibilityError as ds_compat_err:
            raise FunctionArgumentSchemaError(pos) from ds_compat_err


class ProxyData(IProxyData):
    def __init__(self, planned_hash: bytes):
        self._planned_hash = planned_hash

    @property
    def calculated_hash(self) -> bytes:
        return self._planned_hash

    @staticmethod
    def copy_from(other: IProxyData) -> ProxyData:
        return ProxyData(other.calculated_hash)


class ExecutionPlan(IExecutionPlan):
    def __init__(self, functions: Iterable[IStage] | Mapping[bytes, IStage],
                 data: Iterable[IPlannedData] | Mapping[bytes, IPlannedData]):
        def to_mapping(param: Iterable[IPlannedElement] | Mapping[bytes, IPlannedElement]):
            return param if isinstance(param, Mapping) else {element.calculated_hash: element for element in param}

        self._functions: Mapping[bytes, IStage] = to_mapping(functions)
        self._proxy_data: Mapping[bytes, IPlannedData] = to_mapping(data)

    @property
    def stages(self) -> Mapping[bytes, IStage]:
        return self._functions

    @property
    def planned_data(self) -> Mapping[bytes, IPlannedData]:
        return self._proxy_data


_FuncT = TypeVar('_FuncT', bound=IStage)
_DataT = TypeVar('_DataT', bound=IPlannedData)


class PlannerBase(IExecutionPlanner, ABC, Generic[_FuncT, _DataT]):

    def __init__(self):
        self._functions: dict[bytes, _FuncT] = dict()
        self._data: dict[bytes, _DataT] = dict()

    def get_plan(self) -> ExecutionPlan:
        return ExecutionPlan(self._functions.copy(), self._data.copy())

    @abstractmethod
    def _add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: _DataT) -> ProxyRet:
        ...

    def add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: IProxyData) -> ProxyRet:
        return self._add_function(function, *self._proxy_data_to_concrete(*inp_data))

    def _proxy_data_to_concrete(self, *inp_data: IProxyData) -> Iterable[_DataT]:
        for pos, inp in enumerate(inp_data):
            concrete_data = self._data.get(inp.calculated_hash)
            if concrete_data is None:
                raise PlanningError(
                    f"Argument at position {pos} with hash {inp.calculated_hash.hex()} is not part of this plan and therefore cannot be used as an argument in it")
            yield concrete_data
