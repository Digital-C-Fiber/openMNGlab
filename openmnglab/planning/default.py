from __future__ import annotations

from openmnglab.model.datamodel.interface import IOutputDataScheme, IInputDataScheme
from openmnglab.model.functions.interface import IFunctionDefinition, ProxyRet
from openmnglab.planning.base import PlannerBase, check_input, ProxyData
from openmnglab.planning.exceptions import PlanningError
from openmnglab.model.planning.interface import IProxyData
from openmnglab.model.planning.plan.interface import IStage, IPlannedData
from openmnglab.util.hashing import Hash
from openmnglab.util.iterables import ensure_iterable, unpack_sequence


class Stage(IStage):
    def __init__(self, definition: IFunctionDefinition, *data_in: PlannedData):
        hashgen = Hash()
        hashgen.update(definition.config_hash)
        for inp in data_in:
            hashgen.update(inp.calculated_hash)
        self._calculated_hash = hashgen.digest()
        self._depth = max((d.depth for d in data_in), default=0)
        self._definition = definition
        self._data_in = data_in
        self._data_out = tuple(PlannedData.from_function(self, out, i) for i, out in
                               enumerate(ensure_iterable(definition.production_for(*(d.schema for d in data_in)), IOutputDataScheme)))

    @property
    def definition(self) -> IFunctionDefinition:
        return self._definition

    @property
    def data_in(self) -> tuple[PlannedData]:
        return self._data_in

    @property
    def data_out(self) -> tuple[PlannedData]:
        return self._data_out

    @property
    def calculated_hash(self) -> bytes:
        return self._calculated_hash

    @property
    def depth(self) -> int:
        return self._depth


class PlannedData(IPlannedData):

    def __init__(self, depth: int, calculated_hash: bytes, schema: IOutputDataScheme, produced_by: Stage):
        self._depth = depth
        self._calculated_hash = calculated_hash
        self._schema = schema
        self.produced_by = produced_by

    @staticmethod
    def from_function(func: Stage, scheme: IOutputDataScheme, pos: int) -> PlannedData:
        depth = func.depth + 1
        hashgen = Hash()
        hashgen.int(pos)
        hashgen.update(func.calculated_hash)
        return PlannedData(depth, hashgen.digest(), scheme, func)

    @property
    def schema(self) -> IOutputDataScheme:
        return self._schema

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def calculated_hash(self) -> bytes:
        return self._calculated_hash


class DefaultPlanner(PlannerBase[Stage, PlannedData]):

    def _add_function(self, function: IFunctionDefinition[ProxyRet], *inp_data: PlannedData) -> ProxyRet:
        check_input(function.consumes, tuple(d.schema for d in inp_data))
        stage = Stage(function, *inp_data)
        if stage.calculated_hash in self._functions:
            raise PlanningError("A function with the same hash is already planned")
        self._functions[stage.calculated_hash] = stage
        for prod in stage.data_out:
            self._data[prod.calculated_hash] = prod
        return unpack_sequence(tuple(ProxyData.copy_from(o) for o in stage.data_out))
