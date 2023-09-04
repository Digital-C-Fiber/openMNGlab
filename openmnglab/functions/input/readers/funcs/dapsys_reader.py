import logging
import math
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import quantities as pq
from numba import njit
from numpy import float32, float64
from pydapsys import File, StreamType, WaveformPage, Stream, TextPage, Folder, PageType
from pydapsys.toc.exceptions import ToCPathError

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, CONT_REC, STIM_TS, STIM_LBL, SPIKE_TS, TRACK, \
    TRACK_SPIKE_IDX, GLOBAL_STIM_ID, STIM_TYPE_ID
from openmnglab.functions.base import SourceFunctionBase
from openmnglab.util.dicts import get_and_incr


@njit
def _kernel_offset_assign(target: np.array, calc_add, calc_mul, pos_offset, n):
    for i in range(n):
        target[pos_offset + i] = calc_add + i * calc_mul


@njit
def find_nearest_i(array, value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        return idx-1
    else:
        return idx

class DapsysReaderFunc(SourceFunctionBase):
    """Implementation of a reader for DAPSYS"""
    def __init__(self, file_path: str | Path, stim_folder: str | None = None, main_pulse: str = "Main Pulse",
                 continuous_recording: Optional[str] = "Continuous Recording", responses="responses",
                 tracks: Optional[Sequence[str] | str] = "all", comments="comments", stimdefs="Stim Def Starts"):
        self._log = logging.getLogger("DapsysReaderFunc")
        self._file: Optional[File] = None
        self._file_path = file_path
        self._stim_folder = stim_folder
        self._main_pulse = main_pulse
        self._continuous_recording = continuous_recording
        self._responses = responses
        self._tracks = tracks
        self._comments = comments
        self._stimdefs = stimdefs
        self._log.debug("initialized")

    def _load_file(self) -> File:
        """load and parse the referenced DAPSYS file"""
        self._log.debug("Opening file")
        with open(self._file_path, "rb") as binfile:
            self._log.debug("Parsing file")
            dapsys_file = File.from_binary(binfile)
        return dapsys_file

    @property
    def file(self) -> File:
        """Lazy Property for the file attached to this instance. """
        if self._file is None:
            self._log.debug("File not loaded yet!")
            self._file = self._load_file()
            self._log.debug("File loaded!")
        return self._file

    @property
    def stim_folder(self) -> str:
        """Returns the configured folder of the pulse stimulator. If none is configured, selects the first folder in the file and uses that. """
        if self._stim_folder is None:
            self._log.debug("No stim folder defined!")
            self._stim_folder = next(iter(self.file.toc.f.keys()))
            self._log.info(f"Selected stim folder: {self._stim_folder}")
        return self._stim_folder

    def get_continuous_recording(self) -> pd.Series:
        file = self.file
        self._log.debug("processing continuous recording")
        path = f"{self.stim_folder}/{self._continuous_recording}"
        values, timestamps = tuple(), tuple()
        if self.stim_folder in self.file.toc.f and self._continuous_recording in self.file.toc.f[self._stim_folder]:
            total_datapoint_count = sum(len(wp.values) for wp in file.get_data(path, stype=StreamType.Waveform))
            self._log.debug(f"{total_datapoint_count} datapoints in continuous recording")
            values = np.empty(total_datapoint_count, dtype=float32)
            timestamps = np.empty(total_datapoint_count, dtype=float64)
            current_pos = 0
            self._log.debug("begin load")
            for wp in file.get_data(path, stype=StreamType.Waveform):
                wp: WaveformPage
                n = len(wp.values)
                values[current_pos:current_pos + n] = wp.values
                if wp.is_irregular:
                    timestamps[current_pos:current_pos + n] = wp.timestamps
                else:
                    _kernel_offset_assign(timestamps, wp.timestamps[0], wp.interval, current_pos, n)
                current_pos += n
            self._log.debug("finished loading continuous recording")
        else:
            self._log.warning("No continuous recording in file")
        return pd.Series(data=values, index=pd.Index(data=timestamps, copy=False, name=TIMESTAMP),
                         name=CONT_REC, copy=False)

    def _load_textstream(self, path: str) -> pd.Series:
        file = self.file
        try:
            stream: Stream = file.toc.path(path)
            page_ids = stream.page_ids
        except ToCPathError as e:
            self._log.warning(f"Folder {path} not found in file")
            page_ids = tuple()
        timestamps = np.empty(len(page_ids), dtype=np.double)
        labels = [""] * len(page_ids)
        for i, page in enumerate(file.pages[pid] for pid in page_ids):
            page: TextPage
            timestamps[i] = page.timestamp_a
            labels[i] = page.text
        series_name = path.split('/')[-1]
        return pd.Series(data=labels, copy=False,
                         index=pd.Index(timestamps, copy=False, name=TIMESTAMP), name=series_name)


    def get_main_pulses(self) -> tuple[pd.Series, dict]:
        file = self.file
        self._log.debug("processing stimuli")
        path = f"{self.stim_folder}/pulses"
        if self.stim_folder in self.file.toc.f and self._continuous_recording in self.file.toc.f[self._stim_folder]:
            stream: Stream = file.toc.path(path)
            page_ids = stream.page_ids
        else:
            self._log.warning("pulses not found in file")
            page_ids = tuple()
        timestamps = np.empty(len(page_ids), dtype=float64)
        lbl_num = np.empty(len(page_ids), dtype=np.uint)
        """The sequence number for the entry of the stimulus label (i.e. the second entry of 'main pulse')"""
        labels = [""] * len(page_ids)
        """The label pulse labels"""
        counter = dict()
        """Stores the next number for each label (see lbl_num)"""
        self._log.debug("reading stimuli")
        timestamp_to_stimid = dict()
        """Maps the timestamp of the pulse to the trace that has triggered it"""
        for i, page in enumerate(
                file.pages[page_id] for page_id in page_ids):
            page: TextPage
            timestamps[i] = page.timestamp_a
            labels[i] = page.text
            lbl_num[i] = get_and_incr(counter, page.text)
            timestamp_to_stimid[page.timestamp_a] = i
        self._log.debug("finished stimuli")
        return pd.Series(data=timestamps, copy=False,
                         index=pd.MultiIndex.from_arrays([np.arange(len(page_ids)), labels, lbl_num],
                                                         names=[GLOBAL_STIM_ID, STIM_LBL, STIM_TYPE_ID]),
                         name=STIM_TS), timestamp_to_stimid

    def get_tracks_for_responses(self, idmap: dict) -> pd.Series:
        file = self.file
        self._log.debug("processing tracks")
        tracks: Folder = file.toc.path(f"{self.stim_folder}/{self._responses}")
        all_responses = tracks.f.get("Tracks for all Responses", None)

        if self._tracks is None or all_responses is None:
            if self._tracks is None:
                self._log.info("Should not load any tracks (Tracks is None)")
            else:
                self._log.info("No tracks in file")
            streams = list()
        elif len(idmap) == 0:
            self._log.warning("empty idmap, cannot load responses")
            streams = list()
        else:
            if self._tracks == "all":
                streams: list[Stream] = list(all_responses.s.values())
            else:
                streams: list[Stream] = [all_responses.s[name] for name in self._tracks]
            self._log.info(f"loading {len(streams)} tracks")
        n_responses = sum(len(s.page_ids) for s in streams)
        response_timestamps = np.empty(n_responses, dtype=float64)
        responding_to = np.empty(n_responses, dtype=int)
        track_response_number = np.empty(n_responses, dtype=int)
        track_labels = list()
        if n_responses > 0:
            n = 0
            sorted_ids = np.sort(np.fromiter(idmap.keys(), dtype=float))
            sorted_ids_slice = sorted_ids
            sorted_idx_offset = 0
            self._log.info(f"processing streams ({n_responses} responses total)")
            for stream in streams:
                track_labels.extend(stream.name for _ in range(len(stream.page_ids)))
                for i, stim in enumerate(file.pages[page_id] for page_id in stream.page_ids):
                    stim: TextPage
                    response_timestamps[n] = stim.timestamp_a
                    track_response_number[n] = i
                    nearest_offset_i = find_nearest_i(sorted_ids_slice[sorted_idx_offset:], stim.timestamp_a)
                    responding_to[n] = idmap[sorted_ids_slice[nearest_offset_i]]
                    sorted_ids_slice = sorted_ids_slice[nearest_offset_i:]
                    n += 1
        self._log.debug("streams finished")
        return pd.Series(data=response_timestamps, copy=False, name=SPIKE_TS,
                         index=pd.MultiIndex.from_arrays([responding_to, track_labels, track_response_number],
                                                         names=(GLOBAL_STIM_ID, TRACK, TRACK_SPIKE_IDX)))

    def execute(self) -> tuple[PandasContainer[pd.Series], PandasContainer[pd.Series], PandasContainer[pd.Series], PandasContainer[pd.Series], PandasContainer[pd.Series]]:
        self._log.info("Executing function")
        self._log.info("Loading continuous recording")
        cont_rec = self.get_continuous_recording()
        self._log.info("Loading comments")
        comments = self._load_textstream(self._comments)
        self._log.info("Loading stimdefs")
        stimdefs = self._load_textstream(f"{self.stim_folder}/{self._stimdefs}")
        self._log.info("Loading pulses")
        pulses, idmap = self.get_main_pulses()
        self._log.info("Loading tracks")
        tracks = self.get_tracks_for_responses(idmap)
        self._log.info("Processing finished")
        return PandasContainer(cont_rec, {CONT_REC: pq.V, TIMESTAMP: pq.s}), \
            PandasContainer(pulses, {GLOBAL_STIM_ID: pq.dimensionless, STIM_TYPE_ID: pq.dimensionless, STIM_TS: pq.s,
                                     STIM_LBL: pq.dimensionless}), \
            PandasContainer(tracks,
                            {GLOBAL_STIM_ID: pq.dimensionless, SPIKE_TS: pq.s, TRACK: pq.dimensionless,
                             TRACK_SPIKE_IDX: pq.dimensionless}), \
            PandasContainer(comments, {TIMESTAMP: pq.s, comments.name: pq.dimensionless}),\
            PandasContainer(stimdefs, {TIMESTAMP: pq.s, stimdefs.name: pq.dimensionless})
