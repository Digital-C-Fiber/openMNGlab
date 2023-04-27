from __future__ import annotations

from dataclasses import dataclass

from openmnglab.datamodel.interface import IDataScheme
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.base import PlannerBase, check_input, ProxyData
from openmnglab.planning.exceptions import PlanningError
from openmnglab.planning.plan.interface import IStage, IPlannedData
from openmnglab.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class _Stage(IStage):
    def __init__(self, definition: IFunctionDefinition, *data_in: _PlannedData):
        hashgen = Hash()
        hashgen.update(definition.config_hash)
        for inp in data_in:
            hashgen.update(inp.calculated_hash)
        self._calculated_hash = hashgen.digest()
        self._depth = max(*data_in, default=0, key=lambda x: x.depth)
        self._definition = definition
        self._data_in = data_in
        self._data_out = tuple(_PlannedData.from_function(self, out, i) for i, out in enumerate(definition.produces))

    @property
    def definition(self) -> IFunctionDefinition:
        return self._definition

    @property
    def data_in(self) -> tuple[_PlannedData]:
        return self._data_in

    @property
    def data_out(self) -> tuple[_PlannedData]:
        return self._data_out

    @property
    def calculated_hash(self) -> bytes:
        return self._calculated_hash

    @property
    def depth(self) -> int:
        return self._depth


@dataclass(frozen=True)
class _PlannedData(IPlannedData):
    depth: int
    calculated_hash: bytes
    schema: IDataScheme
    produced_by: _Stage

    @staticmethod
    def from_function(func: _Stage, scheme: IDataScheme, pos: int) -> _PlannedData:
        depth = func.depth + 1
        hashgen = Hash()
        hashgen.int(pos)
        hashgen.update(func.calculated_hash)
        return _PlannedData(depth, hashgen.digest(), scheme, func)


class DefaultPlanner(PlannerBase[_Stage, _PlannedData]):

    def _add_function(self, function: IFunctionDefinition, *inp_data: _PlannedData) -> tuple[IProxyData, ...]:
        check_input(function.consumes, tuple(d.schema for d in inp_data))
        planned_func = _Stage(function, *inp_data)
        if planned_func.calculated_hash in self._functions:
            raise PlanningError("A function with the same hash is already planned")
        self._functions[planned_func.calculated_hash] = planned_func
        for prod in planned_func.data_out:
            self._data[prod.calculated_hash] = prod
        return tuple(ProxyData.copy_from(o) for o in planned_func.data_out)
