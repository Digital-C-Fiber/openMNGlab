from typing import Optional


class PlanningError(Exception):
    ...


class FunctionArgumentsError(PlanningError):
    def __init__(self, function_name: Optional[str] = None):
        self.function_name = function_name if function_name is not None else ""


class InvalidFunctionArgumentCountError(FunctionArgumentsError):

    def __init__(self, expected_count: int, actual_count: int, function_name: Optional[str] = None):
        super().__init__(function_name)
        self.expected_count = expected_count
        self.actual_count = actual_count

    def __str__(self):
        return f"Argument count missmatch. Function {self.function_name} expects {self.expected_count} arguments, but {self.actual_count} were given"


class FunctionArgumentSchemaError(FunctionArgumentsError):

    def __init__(self, argument_pos: int, function_name: Optional[str] = None):
        super().__init__(function_name)
        self.argument_pos = argument_pos

    def __str__(self):
        return f"Exception while trying to set data of argument number {self.argument_pos} of function {self.function_name}"
