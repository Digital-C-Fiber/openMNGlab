from __future__ import annotations

from openmnglab.model.datamodel.interface import IDataSchema
from openmnglab.model.functions.interface import IFunctionDefinition, ProxyRet
from openmnglab.model.planning.plan.interface import IStage, IVirtualData
from openmnglab.planning.base import PlannerBase, check_input, DataReference
from openmnglab.planning.exceptions import PlanningError
from openmnglab.util.hashing import HashBuilder
from openmnglab.util.iterables import ensure_iterable, unpack_sequence


class Stage(IStage):
    def __init__(self, definition: IFunctionDefinition, *data_in: VirtualData):
        hashgen = HashBuilder()
        hashgen.update(definition.config_hash)
        for inp in data_in:
            hashgen.update(inp.planning_id)
        self._calculated_hash = hashgen.digest()
        self._depth = max((d.depth for d in data_in), default=0)
        self._definition = definition
        self._data_in = data_in
        self._data_out = tuple(VirtualData.from_function(self, out, i) for i, out in
                               enumerate(
                                   ensure_iterable(definition.output_for(*(d.schema for d in data_in)), IDataSchema)))

    @property
    def definition(self) -> IFunctionDefinition:
        return self._definition

    @property
    def data_in(self) -> tuple[VirtualData]:
        return self._data_in

    @property
    def data_out(self) -> tuple[VirtualData]:
        return self._data_out

    @property
    def planning_id(self) -> bytes:
        return self._calculated_hash

    @property
    def depth(self) -> int:
        return self._depth


class VirtualData(IVirtualData):

    def __init__(self, depth: int, calculated_hash: bytes, schema: IDataSchema, produced_by: Stage):
        self._depth = depth
        self._calculated_hash = calculated_hash
        self._schema = schema
        self.produced_by = produced_by

    @staticmethod
    def from_function(func: Stage, scheme: IDataSchema, pos: int) -> VirtualData:
        depth = func.depth + 1
        hashgen = HashBuilder()
        hashgen.int(pos)
        hashgen.update(func.planning_id)
        return VirtualData(depth, hashgen.digest(), scheme, func)

    @property
    def schema(self) -> IDataSchema:
        return self._schema

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def planning_id(self) -> bytes:
        return self._calculated_hash


class DefaultPlanner(PlannerBase[Stage, VirtualData]):

    def _add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: VirtualData) -> ProxyRet:
        check_input(function.slot_acceptors, tuple(d.schema for d in inp_data))
        stage = Stage(function, *inp_data)
        if stage.planning_id in self._functions:
            raise PlanningError("A function with the same hash is already planned")
        self._functions[stage.planning_id] = stage
        for prod in stage.data_out:
            self._data[prod.planning_id] = prod
        return unpack_sequence(tuple(DataReference(o.planning_id) for o in stage.data_out))
