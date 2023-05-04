from typing import Callable

import pytest

from openmnglab.execution.interface import IExecutor
from openmnglab.functions.interface import IFunctionDefinition
from openmnglab.planning.base import ExecutionPlan
from openmnglab.planning.plan.interface import IExecutionPlan
from tests.integration.exec_mocks import MockFunctionDefinition, MockData
from tests.integration.executors.fixtures import ObserverFixture
from tests.integration.executors.params import EXECUTOR_CONSTRUCTORS, setup_single_func_empty_execution_plan, \
    setup_exec_plan_with_same_def, setup_multi_func_def_execution_plan
from tests.integration.spy import SpyObserver


@pytest.mark.parametrize(("new_executor",),
                         [pytest.param(call, id=name) for name, call in EXECUTOR_CONSTRUCTORS.items()])
class TestExecutor(ObserverFixture):

    def test_does_not_fail_on_empty_exec_plan(self, obs: SpyObserver,
                                              new_executor: Callable[[IExecutionPlan], IExecutor]):
        plan = ExecutionPlan({}, {})
        exec = new_executor(plan)
        exec.execute()

    @pytest.mark.parametrize(("execution_plan", "expected_calls"),
                             [pytest.param(setup_single_func_empty_execution_plan, 1, id="Single Stage"),
                              pytest.param(setup_exec_plan_with_same_def, 2,
                                           id="two source stages, same function def")])
    def test_function_creation(self, obs: SpyObserver, new_executor: Callable[[IExecutionPlan], IExecutor],
                               execution_plan: Callable[[], IExecutionPlan], expected_calls: int):
        exec_plan = execution_plan()
        with obs.patch_function(MockFunctionDefinition.new_function):
            ex = new_executor(exec_plan)
            ex.execute()
        new_function_calls = tuple(obs.get_calls_of(IFunctionDefinition.new_function, IFunctionDefinition))
        # An executor MAY create more function instances than stages. However, it should never create less function instances,
        # as it MUST NOT reuse them.
        assert len(new_function_calls) >= expected_calls


class TestDataManagement:
    @pytest.mark.parametrize(("new_executor",),
                             [pytest.param(call, id=name) for name, call in EXECUTOR_CONSTRUCTORS.items()],
                             scope="class")
    @pytest.mark.parametrize(("exec_plan_constructor",),
                             [pytest.param(setup_multi_func_def_execution_plan)], scope="class")
    class TestAssignment:

        @pytest.fixture(scope="class")
        def execution_plan(self, exec_plan_constructor: Callable[[], IExecutionPlan]):
            exec_plan = exec_plan_constructor()
            return exec_plan

        @pytest.fixture(scope="class")
        def executor(self, execution_plan, new_executor):
            exec = new_executor(execution_plan)
            exec.execute()
            return exec

        def test_all_data_keys_present(self, executor: IExecutor, execution_plan: ExecutionPlan):
            assert {k for k in executor.data.keys()}.issubset({k for k in execution_plan.planned_data.keys()})

        def test_container_type_not_changed(self, executor: IExecutor, execution_plan: ExecutionPlan):
            for stage in execution_plan.stages.values():
                for output_data in stage.data_out:
                    prod_data = executor.data[output_data.calculated_hash]
                    # the executor should not change the type of the container.
                    assert isinstance(prod_data, MockData)

        def test_data_is_correct(self, executor: IExecutor, execution_plan: ExecutionPlan):
            for stage in execution_plan.stages.values():
                for output_data in stage.data_out:
                    prod_data: MockData = executor.data[output_data.calculated_hash]
                    # check that data available under the hash acutally belongs to the stage that produced it
                    assert prod_data.stage == stage.calculated_hash

        def test_data_is_in_correct_order(self, executor: IExecutor, execution_plan: ExecutionPlan):
            for stage in execution_plan.stages.values():
                for output_num, output_data in enumerate(stage.data_out):
                    prod_data: MockData = executor.data[output_data.calculated_hash]
                    # check that data is assigned in correct ordert
                    assert prod_data.output_num == output_num
