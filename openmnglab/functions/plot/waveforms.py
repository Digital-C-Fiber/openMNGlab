from typing import Optional, Callable

import matplotlib.pyplot as plt
import pandas as pd
from pandera import DataFrameSchema, Column

from openmnglab.datamodel.matplot.model import MatPlotlibSchema
from openmnglab.datamodel.pandas.model import PandasInputDataScheme
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, GLOBAL_STIM_ID
from openmnglab.functions.base import StaticFunctionDefinitionBase
from openmnglab.functions.plot.funcs.waveforms import WaveformPlotMode, WaveformPlotFunc
from openmnglab.functions.processing.funcs.interval_data import LEVEL_COLUMN
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash
from openmnglab.util.seaborn import Theme


class WaveformPlot(StaticFunctionDefinitionBase[IProxyData[plt.Figure]]):
    """Function to plot waveforms. Can either plot average waveforms or each for its own.
    Multi-plots can be created by using the col and row parameters which are passed to the underlying seaborn function.

    In: IntervalData with normalized timestamps

    Out: figure based on the configuration

    Common use-cases
    ----------------
    * Use  ``col`` or ``row`` to ``TRACK`` to seperate the tracks into columns or rows
    * To plot all waveforms on top of each other, use ``mode="individual"``. Set parameter ``alpha`` to adjust the opacity of individual waveforms.
        - Use  ``col`` or ``row`` to ``GOBAL_STIM_ID`` to plot responses based on the stimulus id in columns or rows respectively

    :param mode: "average" prints the average of the waveforms and their standard deviation, "individual" plots all waveforms individually
    :param selector: function to filter the incoming dataframe (e.g. plotting only a subset of waveforms)
    :param column: column of the signal
    :param fig_args: additional arguments to pass to plt.figure(). Only active when col and row are both None
    :param alpha: Alpha channel for the lines. Only  active when mode is individual. Smaller values will make each individual line more transparent
    :param row: index or column to create supblot rows
    :param theme: custom theme passed to seaborn
    :param col: index or column name to create subplot columns
    :param color_dict: dictionary mapping from track names to mpl-compatible color definitions
    :param time_col: index or column for the timestamps
    :param stim_idx: index to differentiate individual stimuli by
    :param sns_args: additional arguments passed to seaborn
    """

    def __init__(self, mode: WaveformPlotMode | str = WaveformPlotMode.AVERAGE,
                 selector: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None, column: str = LEVEL_COLUMN[0],
                 fig_args: Optional[dict] = None, alpha: Optional[float] = None, row: Optional[str] = None,
                 theme: Optional[Theme] = None,
                 col: Optional[str] = None,
                 color_dict: Optional[dict[str, str]] = None,
                 time_col: str = TIMESTAMP, stim_idx: str = GLOBAL_STIM_ID, **sns_args):

        super().__init__("omnglab.plotting.waveform")
        self.mode = mode if isinstance(mode, WaveformPlotMode) else WaveformPlotMode(mode.lower())
        self.selector = selector
        self.column = column
        self.fig_args = fig_args
        self.alpha = alpha
        self.row = row
        self.theme = theme
        self.col = col
        self.color_dict = color_dict
        self.time_col = time_col
        self.stim_idx = stim_idx
        self.sns_args = sns_args

    @property
    def config_hash(self) -> bytes:
        h = Hash().str(self.mode.name).str(self.column).str(self.stim_idx).str(self.time_col)
        if self.selector is not None:
            h.int(id(self.selector))
        if self.alpha is not None:
            h.float(float(self.alpha))
        if self.fig_args is not None:
            h.dict(self.fig_args, fail=False)
        if self.row is not None:
            h.str(self.row)
        if self.theme is not None:
            h.dynamic(self.theme.context, fail=False)
            h.dynamic(self.theme.style, fail=False)
            h.dynamic(self.theme.palette, fail=False)
            h.str(self.theme.font)
            h.dynamic(self.theme.font_scale, fail=False)
            h.bool(self.theme.color_codes)
            if self.theme.rc is not None:
                h.dict(self.theme.rc, fail=False)
        if self.color_dict is not None:
            h.dict(self.color_dict, fail=False)
        return h.digest()

    @property
    def consumes(self) -> PandasInputDataScheme[pd.DataFrame]:
        return PandasInputDataScheme(DataFrameSchema({
            self.column: Column(float)
        }))

    def new_function(self) -> WaveformPlotFunc:
        return WaveformPlotFunc(mode=self.mode, selector=self.selector, column=self.column, fig_args=self.fig_args,
                                alpha=self.alpha, row=self.row, theme=self.theme, col=self.col, color_dict=self.col,
                                time_col=self.time_col, stim_idx=self.stim_idx, **self.sns_args)

    @property
    def produces(self) -> MatPlotlibSchema:
        return MatPlotlibSchema()
