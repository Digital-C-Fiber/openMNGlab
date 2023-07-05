import matplotlib.pyplot as plt

from openmnglab.model.datamodel.interface import IDataContainer, T_co, IStaticDataScheme, IOutputDataScheme


class MatPlotLibContainer(IDataContainer[plt.Figure]):

    def __init__(self, figure: plt.Figure):
        self.figure = figure

    @property
    def data(self) -> plt.Figure:
        return self.figure

    def deep_copy(self) -> IDataContainer[T_co]:
        raise NotImplementedError("deep copy cannot be implemented for matplotlib figures")


class MatPlotlibSchema(IStaticDataScheme):
    def validate(self, data_container: IDataContainer) -> bool:
        return isinstance(data_container, MatPlotLibContainer) and data_container.data is not None

    def accepts(self, output_data_scheme: IOutputDataScheme) -> bool:
        return isinstance(output_data_scheme, MatPlotLibContainer)

    def transform(self, data_container: IDataContainer) -> IDataContainer:
        return data_container
