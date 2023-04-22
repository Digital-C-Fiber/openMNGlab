from typing import Optional


class ExecutionException(Exception):
    ...


class StageExecutionError(ExecutionException):
    def __init__(self, msg: str = "", stage_hash: Optional[bytes] = None):
        super().__init__(msg)
        self.stage_hash = stage_hash


class FunctionError(ExecutionException):
    ...


class FunctionInputError(FunctionError):
    ...


class FunctionExecutionError(FunctionError):
    ...


class FunctionOutputError(FunctionError):
    ...


class FunctionReturnCountMissmatch(FunctionOutputError):
    def __init__(self, expected=None, actual=None):
        super().__init__()
        self.expected_return_count = expected
        self.actual_return_count = actual

    def __str__(self):
        sanitize_count = lambda s: "unkown" if s is None else s
        return f"function did not produce the expected count of outputs. Expected {sanitize_count(self.expected_return_count)}, got {sanitize_count(self.actual_return_count)}"
