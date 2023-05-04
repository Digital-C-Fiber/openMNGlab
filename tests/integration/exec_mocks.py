from typing import Optional, Iterable, Sequence

from openmnglab.datamodel.interface import IDataContainer, IDataScheme
from openmnglab.functions.base import DefaultFunctionBase
from openmnglab.functions.interface import IFunctionDefinition, IFunction
from openmnglab.planning.plan.interface import IPlannedData, IStage


class MockData(IDataContainer[bytes]):
    def __init__(self, stage: bytes, output_num: int):
        self.output_num = output_num
        self.stage = stage

    @property
    def data(self) -> bytes:
        return self.stage


class MockFunction(DefaultFunctionBase):
    def __init__(self, producer: bytes, produce_count: int = 0):
        self.producer = producer
        self.output_count = produce_count

    def set_input(self, *data_in: IDataContainer):
        # function does nothing (can grap input through the spy system), so it just passes
        pass

    def execute(self) -> Optional[Iterable[IDataContainer]]:
        return (MockData(self.producer, i) for i in range(self.output_count))


class MockFunctionDefinition(IFunctionDefinition):
    def __init__(self, ident, config_hash: bytes, ident_hash: bytes, produces: Optional[Sequence[IDataScheme]] = None,
                 outputs: Optional[Sequence[IDataScheme]] = None, out_count=None):
        self._ident = ident
        self._conf_hash = config_hash
        self._ident_hash = ident_hash
        self._produces = produces
        self._out = outputs
        self.out_count = out_count if out_count is not None else len(outputs) if outputs is not None else 0

    @property
    def identifier(self) -> str:
        return self._ident

    @property
    def config_hash(self) -> bytes:
        return self._conf_hash

    @property
    def identifying_hash(self) -> bytes:
        return self._ident_hash

    @property
    def produces(self) -> Optional[Sequence[IDataScheme]]:
        return self._produces

    @property
    def consumes(self) -> Optional[Sequence[IDataScheme]]:
        return self._out

    def new_function(self) -> IFunction:
        return MockFunction(self._ident_hash, self.out_count)


class MockDataScheme(IDataScheme):
    def __init__(self, is_compat=True, verify=True):
        self._is_compat = is_compat
        self._verify = verify

    def is_compatible(self, other: IDataScheme) -> bool:
        return self._is_compat

    def verify(self, data: object) -> bool:
        return self._verify


class MockPlannedData(IPlannedData):

    def __init__(self, schema: IDataScheme, calculated_hash: bytes, depth: int):
        self._schema = schema
        self._calculated_hash = calculated_hash
        self._depth = depth

    @property
    def schema(self) -> IDataScheme:
        return self._schema

    @property
    def calculated_hash(self) -> bytes:
        return self._calculated_hash

    @property
    def depth(self) -> int:
        return self._depth


class MockStage(IStage):
    def __init__(self, definition: IFunctionDefinition, depth: int, hash: bytes,
                 data_out: Optional[list[IPlannedData]] = None, data_in: Optional[list[IPlannedData]] = None):
        self._def = definition
        self._data_in = data_in if data_in is not None else list()
        self._data_out = data_out if data_out is not None else list()
        self._depth = depth
        self._hash = hash

    @property
    def definition(self) -> IFunctionDefinition:
        return self._def

    @property
    def data_in(self) -> Sequence[IPlannedData]:
        return self._data_in

    @property
    def data_out(self) -> Sequence[IPlannedData]:
        return self._data_out

    @property
    def calculated_hash(self) -> bytes:
        return self._hash

    @property
    def depth(self) -> int:
        return self._depth
