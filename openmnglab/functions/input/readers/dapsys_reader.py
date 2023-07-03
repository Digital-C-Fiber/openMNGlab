from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
from pandera import SeriesSchema, DataFrameSchema

from openmnglab.datamodel.pandas.model import PandasDataScheme
from openmnglab.datamodel.pandas.schemes import time_waveform, str_float_list, sorted_spikes
from openmnglab.functions.base import SourceFunctionDefinitionBase
from openmnglab.functions.input.readers.funcs.dapsys_reader import DapsysReaderFunc
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class DapsysReader(SourceFunctionDefinitionBase[IProxyData[pd.Series], IProxyData[pd.Series], IProxyData[pd.Series]]):
    def __init__(self, file: str | Path, stim_folder: str, main_pulse: Optional[str] = "Main Pulse",
                 continuous_recording: Optional[str] = "Continuous Recording", responses="responses",
                 tracks: Optional[Sequence[str] | str] = "all", segment_interpolation_strategy="none"):
        super().__init__("net.codingchipmunk.dapsysreader")
        self._file = file
        self._interpol_strategy = segment_interpolation_strategy
        self._stim_folder = stim_folder
        self._main_pulse = main_pulse
        self._continuous_recording = continuous_recording
        self._responses = responses
        self._tracks = tracks

    @property
    def config_hash(self) -> bytes:
        hasher = Hash()
        hasher.str(self._file)
        hasher.str(self._interpol_strategy)
        hasher.str(self._stim_folder)
        hasher.str(self._main_pulse)
        hasher.str(self._continuous_recording)
        hasher.str(self._responses)
        hasher.str(self._tracks)
        return hasher.digest()

    @property
    def produces(self) -> tuple[
        PandasDataScheme[SeriesSchema], PandasDataScheme[SeriesSchema], PandasDataScheme[DataFrameSchema]]:
        return time_waveform(), str_float_list(), sorted_spikes()

    def new_function(self) -> DapsysReaderFunc:
        return DapsysReaderFunc(self._file, self._stim_folder, main_pulse=self._main_pulse,
                                continuous_recording=self._continuous_recording,
                                responses=self._responses, tracks=self._tracks,
                                segment_interpolation_strategy=self._interpol_strategy)
