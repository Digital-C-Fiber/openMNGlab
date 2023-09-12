class DataSchemaError(Exception):
    ...


class DataSchemaCompatibilityError(DataSchemaError):
    ...


class DataSchemaConformityError(DataSchemaError):
    ...
