from pathlib import Path
from typing import Optional, Sequence

import pandas as pd
from pandera import SeriesSchema, DataFrameSchema

from openmnglab.datamodel.pandas.model import PandasDataScheme
from openmnglab.datamodel.pandas.schemes import time_waveform, str_float_list, sorted_spikes, stimulus_list
from openmnglab.functions.base import SourceFunctionDefinitionBase
from openmnglab.functions.input.readers.funcs.dapsys_reader import DapsysReaderFunc
from openmnglab.model.planning.interface import IProxyData
from openmnglab.util.hashing import Hash


class DapsysReader(SourceFunctionDefinitionBase[IProxyData[pd.Series], IProxyData[pd.Series], IProxyData[pd.Series]]):
    """Loads data from a DAPSYS file

    In: nothing

    Out: [Continuous recording, Stimuli list, tracks]

    Produces
    ........
        * Continuous Recording: continuous recording from the file. timestamps as float index, signal values as float
          values pd.Series[[TIMESTAMP: float], float].
        * Stimuli list: list of stimuli timestamps. Indexed by the global stimulus id
          (the stimulus id amongst all stimuli in the file), the label of stimulus and the id of the stimulus type / label
          (the id amongst all other stimuli in the file which have the same label):
          pd.Series[[GLOBAL_STIM_ID: int, STIM_TYPE: str, STIM_TYPE_ID: int], float]
        * tracks: List of all sorted tracks. Indexed by the global stimulus id they are attributed to, the name of the track and their id respective to the track.
          pd.Series[[GLOBAL_STIM_ID: int, TRACK: str, TRACK_SPIKE_IDX: int], float]


    :param file: Path to the DAPSYS file
    :param stim_folder: The stimulator folder inside the DAPSYS file (i.e. "NI Pulse Stimulator")
    :param main_pulse: Name of the main pulse, defaults to "Main Pulse"
    :param continuous_recording: Name of the continuous recording, defaults to "Continuous Recording"
    :param responses: Name of the folder containing the responses, defaults to "responses"
    :param tracks: Define which tracks to load from the file. Tracks must be present in the "Tracks for all Responses" folder. "all" loads all tracks found in that subfolder.
    """
    def __init__(self, file: str | Path, stim_folder: str, main_pulse: Optional[str] = "Main Pulse",
                 continuous_recording: Optional[str] = "Continuous Recording", responses="responses",
                 tracks: Optional[Sequence[str] | str] = "all"):

        super().__init__("net.codingchipmunk.dapsysreader")
        self._file = file
        self._stim_folder = stim_folder
        self._main_pulse = main_pulse
        self._continuous_recording = continuous_recording
        self._responses = responses
        self._tracks = tracks

    @property
    def config_hash(self) -> bytes:
        hasher = Hash()
        hasher.path(self._file)
        hasher.str(self._stim_folder)
        hasher.str(self._main_pulse)
        hasher.str(self._continuous_recording)
        hasher.str(self._responses)
        hasher.str(self._tracks)
        return hasher.digest()

    @property
    def produces(self) -> tuple[
        PandasDataScheme[SeriesSchema], PandasDataScheme[SeriesSchema], PandasDataScheme[DataFrameSchema]]:
        return time_waveform(), stimulus_list(), sorted_spikes()

    def new_function(self) -> DapsysReaderFunc:
        return DapsysReaderFunc(self._file, self._stim_folder, main_pulse=self._main_pulse,
                                continuous_recording=self._continuous_recording,
                                responses=self._responses, tracks=self._tracks)
