from typing import Callable

from openmnglab.execution.interface import IExecutor
from openmnglab.execution.singlethreaded import SingleThreadedExecutor
from openmnglab.planning.base import ExecutionPlan
from openmnglab.planning.plan.interface import IExecutionPlan
from tests.integration.exec_mocks import MockFunctionDefinition, MockStage, MockDataScheme, MockPlannedData

EXECUTOR_CONSTRUCTORS: dict[str, Callable[[IExecutionPlan], IExecutor]] = {
    SingleThreadedExecutor.__name__: lambda x: SingleThreadedExecutor(x)
}


def setup_empty_execution_plan() -> IExecutionPlan:
    return ExecutionPlan({}, {})


def setup_single_func_empty_execution_plan() -> IExecutionPlan:
    initial_function = MockFunctionDefinition("omngl.testing.mockfuncsource", bytes(), bytes.fromhex(
        "deadbeef"))
    initial_stage = MockStage(initial_function, 0, initial_function.identifying_hash)
    return ExecutionPlan((initial_stage,), {})


def setup_exec_plan_with_same_def() -> IExecutionPlan:
    initial_function = MockFunctionDefinition("omngl.testing.mockfuncsource", bytes(), bytes.fromhex(
        "deadbeef"))
    initial_stage_a = MockStage(initial_function, 0, initial_function.identifying_hash)
    initial_stage_b = MockStage(initial_function, 0, bytes.fromhex("deadbeef2a"))
    return ExecutionPlan((initial_stage_a, initial_stage_b), {})


def setup_multi_func_def_execution_plan() -> IExecutionPlan:
    true_data_scheme = MockDataScheme()
    initial_function = MockFunctionDefinition("omngl.testing.mockfuncsource", bytes(), bytes.fromhex(
        "deadbeef"), outputs=(true_data_scheme, true_data_scheme))
    initial_function_output = (MockPlannedData(true_data_scheme,
                                               bytes.fromhex("5a6e11"),
                                               1), MockPlannedData(true_data_scheme,
                                                                   bytes.fromhex("5a6e22"),
                                                                   1))
    initial_stage = MockStage(initial_function, 0, initial_function.identifying_hash,
                              data_out=list(initial_function_output))
    return ExecutionPlan((initial_stage,), (*initial_function_output,))


def setup_single_func_execution_plan() -> IExecutionPlan:
    true_data_scheme = MockDataScheme()
    initial_function = MockFunctionDefinition("omngl.testing.mockfuncsource", bytes(), bytes.fromhex(
        "07a74b7f6a061a9e88bcba6a8a77afa6e4f4cc7a15a3aa01c917e11c"), outputs=(true_data_scheme,))
    second_function = MockFunctionDefinition("omngl.testing.mockfunc_a", bytes(), bytes.fromhex())
    initial_function_output = MockPlannedData(true_data_scheme,
                                              bytes.fromhex("f97af9d721ac928227aef6b8952159e68606bc06ac60879a97f74daf"),
                                              1)
    initial_stage = MockStage(initial_function, 0, initial_function.identifying_hash,
                              data_out=[initial_function_output])
