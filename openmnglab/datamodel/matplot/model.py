import matplotlib.pyplot as plt

from openmnglab.model.datamodel.interface import IDataContainer, T_co, IDataSchema


class MatPlotLibContainer(IDataContainer[plt.Figure]):

    def __init__(self, figure: plt.Figure):
        self.figure = figure

    @property
    def data(self) -> plt.Figure:
        return self.figure

    def deep_copy(self) -> IDataContainer[T_co]:
        raise NotImplementedError("deep copy cannot be implemented for matplotlib figures")


class MatPlotlibSchema(IDataSchema):
    def validate(self, data_container: IDataContainer) -> bool:
        return isinstance(data_container, MatPlotLibContainer) and data_container.data is not None

    def accepts(self, output_data_scheme: IDataSchema) -> bool:
        return isinstance(output_data_scheme, MatPlotLibContainer)
