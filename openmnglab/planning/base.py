from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Iterable, Mapping, Sequence

from openmnglab.datamodel.exceptions import DataSchemaCompatibilityError
from openmnglab.model.datamodel.interface import ISchemaAcceptor, IDataSchema
from openmnglab.model.functions.interface import IFunctionDefinition, ProxyRet
from openmnglab.model.planning.interface import IExecutionPlanner, IDataReference
from openmnglab.model.planning.plan.interface import IExecutionPlan, IStage, IVirtualData, IPlannedElement
from openmnglab.planning.exceptions import InvalidFunctionArgumentCountError, FunctionArgumentSchemaError, PlanningError
from openmnglab.util.iterables import ensure_sequence


def check_input(expected_schemes: Sequence[ISchemaAcceptor] | ISchemaAcceptor | None,
                actual_schemes: Sequence[IDataSchema] | IDataSchema | None):
    expected_schemes: Sequence[ISchemaAcceptor] = ensure_sequence(expected_schemes, ISchemaAcceptor)
    actual_schemes: Sequence[IDataSchema] = ensure_sequence(actual_schemes, IDataSchema)
    if len(expected_schemes) != len(actual_schemes):
        raise InvalidFunctionArgumentCountError(len(expected_schemes), len(actual_schemes))
    for pos, (expected_scheme, actual_scheme) in enumerate(zip(expected_schemes, actual_schemes)):
        expected_scheme: ISchemaAcceptor
        actual_scheme: IDataSchema
        try:
            if not expected_scheme.accepts(actual_scheme):
                raise DataSchemaCompatibilityError("Expected scheme is not compatible with actual scheme")
        except DataSchemaCompatibilityError as ds_compat_err:
            raise FunctionArgumentSchemaError(pos) from ds_compat_err


class DataReference(IDataReference):
    def __init__(self, ref_id: bytes):
        self._ref_id = ref_id

    @property
    def referenced_data_id(self) -> bytes:
        return self._ref_id

    @staticmethod
    def copy_from(other: IDataReference) -> DataReference:
        return DataReference(other.referenced_data_id)


class ExecutionPlan(IExecutionPlan):
    def __init__(self, functions: Iterable[IStage] | Mapping[bytes, IStage],
                 data: Iterable[IVirtualData] | Mapping[bytes, IVirtualData]):
        def to_mapping(param: Iterable[IPlannedElement] | Mapping[bytes, IPlannedElement]):
            return param if isinstance(param, Mapping) else {element.planning_id: element for element in param}

        self._functions: Mapping[bytes, IStage] = to_mapping(functions)
        self._proxy_data: Mapping[bytes, IVirtualData] = to_mapping(data)

    @property
    def stages(self) -> Mapping[bytes, IStage]:
        return self._functions

    @property
    def planned_data(self) -> Mapping[bytes, IVirtualData]:
        return self._proxy_data


_FuncT = TypeVar('_FuncT', bound=IStage)
_DataT = TypeVar('_DataT', bound=IVirtualData)


class PlannerBase(Generic[_FuncT, _DataT], IExecutionPlanner, ABC):

    def __init__(self):
        self._functions: dict[bytes, _FuncT] = dict()
        self._data: dict[bytes, _DataT] = dict()

    def get_plan(self) -> ExecutionPlan:
        return ExecutionPlan(self._functions.copy(), self._data.copy())

    @abstractmethod
    def _add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: _DataT) -> ProxyRet:
        ...

    def add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: IDataReference) -> ProxyRet:
        return self._add_function(function, *self._get_referenced_virt_data(*inp_data))

    def _get_referenced_virt_data(self, *inp_data: IDataReference) -> Iterable[_DataT]:
        for pos, inp in enumerate(inp_data):
            concrete_data = self._data.get(inp.referenced_data_id)
            if concrete_data is None:
                raise PlanningError(
                    f"Argument at position {pos} with hash {inp.referenced_data_id.hex()} is not part of this plan and therefore cannot be used as an argument in it")
            yield concrete_data
