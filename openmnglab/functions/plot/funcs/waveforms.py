from enum import StrEnum
from typing import Optional, Callable

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from openmnglab.datamodel.matplot.model import MatPlotLibContainer
from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, TRACK, GLOBAL_STIM_ID
from openmnglab.functions.base import FunctionBase
from openmnglab.functions.processing.funcs.interval_data import LEVEL_COLUMN
from openmnglab.util.seaborn import Theme


class WaveformPlotMode(StrEnum):
    AVERAGE = "avg"
    INDIVIDUAL = "individual"


class WaveformPlotFunc(FunctionBase):

    def __init__(self, mode: WaveformPlotMode | str = WaveformPlotMode.AVERAGE,
                 selector: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None, column: str = LEVEL_COLUMN[0],
                 fig_args: Optional[dict] = None, alpha: Optional[float] = None, row: Optional[str] = None,
                 theme: Optional[Theme] = None,
                 col: Optional[str] = None,
                 color_dict: Optional[dict[str, str]] = None,
                 time_col: str = TIMESTAMP, stim_idx: str = GLOBAL_STIM_ID, **sns_args):
        def identity(x):
            return x

        self.theme = theme if theme is not None else Theme()
        self.mode = mode if isinstance(mode, WaveformPlotMode) else WaveformPlotMode(mode.lower())
        self.selector = selector if selector is not None else identity
        self.row = row
        self.col = col
        self.sns_args = sns_args
        self.column = column
        self.data_container = None
        self._alpha = alpha if row != stim_idx != col else 1
        self.figargs = fig_args if fig_args is not None else dict()
        self.timestamp_field = TIMESTAMP
        self.track_index = TRACK
        self.time_col = time_col
        self.colors = color_dict
        self.stim_idx = stim_idx

    @property
    def alpha(self) -> float:
        if self._alpha is None:
            self._alpha = 0.05
        return self._alpha

    @property
    def data(self) -> pd.DataFrame:
        return self.selector(self.data_container.data)

    @property
    def _relplot(self) -> bool:
        return self.col is not None or self.row is not None

    def _plot_line(self, **lineplot_kwargs) -> plt.Figure:
        ax: Axes
        lineplot_kwargs.update(self.sns_args)
        fig, ax = plt.subplots(**self.figargs)
        sns.lineplot(data=self.data, x=self.time_col, y=self.column, palette=self.colors, hue=TRACK, ax=ax,
                     **lineplot_kwargs)
        ax.set_xlabel(f"{self.time_col} [{self.data_container.units[self.time_col].dimensionality.latex}]")
        ax.set_ylabel(f"{self.column} [{self.data_container.units[self.column].dimensionality.latex}]")
        return fig

    def _plot_rel(self, **lineplot_kwargs) -> plt.Figure:
        facet: sns.FacetGrid
        facet = sns.relplot(data=self.data, x=self.time_col, y=self.column, palette=self.colors, hue=TRACK,
                            row=self.row,
                            col=self.col, kind="line", **lineplot_kwargs)
        for axs_row in facet.axes:
            if axs_row[0].get_ylabel() != '':
                axs_row[0].set_ylabel(f"{self.column} [{self.data_container.units[self.column].dimensionality.latex}]")
        for ax in facet.axes[-1]:
            if ax.get_xlabel() != '':
                ax.set_xlabel(f"{self.time_col} [{self.data_container.units[self.time_col].dimensionality.latex}]")
        return facet.fig

    def _plot(self, **plot_kwargs) -> plt.Figure:
        if self.row is not None or self.column is not None:
            return self._plot_rel(**plot_kwargs)
        return self._plot_line(**plot_kwargs)

    def _plot_avg(self) -> plt.Figure:
        if self._relplot:
            return self._plot_rel()
        return self._plot_line(errorbar="sd")

    def _plot_overlap(self) -> plt.Figure:
        universal_kwargs = dict(estimator=None, units=self.stim_idx, alpha=self.alpha)
        if self._relplot:
            return self._plot_rel(**universal_kwargs)
        return self._plot_line(**universal_kwargs)

    def execute(self) -> MatPlotLibContainer:
        with self.theme:
            if self.mode == WaveformPlotMode.AVERAGE:
                fig = self._plot_avg()
            elif self.mode == WaveformPlotMode.INDIVIDUAL:
                fig = self._plot_overlap()
            else:
                raise NotImplementedError(f"Mode {self.mode} is not implemented")
        return MatPlotLibContainer(fig)

    def set_input(self, data: PandasContainer):
        self.data_container = data
