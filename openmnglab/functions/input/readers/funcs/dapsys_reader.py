import logging
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd
import quantities as pq
from numba import njit
from numpy import float32, float64
from pydapsys import File, StreamType, WaveformPage, Stream, TextPage, Folder, PageType

from openmnglab.datamodel.pandas.model import PandasContainer
from openmnglab.datamodel.pandas.schemes import TIMESTAMP, CONT_REC, STIM_TS, STIM_LBL, SPIKE_TS, TRACK, \
    TRACK_SPIKE_IDX, GLOBAL_STIM_ID, STIM_TYPE_ID
from openmnglab.functions.base import SourceFunctionBase
from openmnglab.util.dicts import get_and_incr


@njit
def _kernel_offset_assign(target: np.array, calc_add, calc_mul, pos_offset, n):
    for i in range(n):
        target[pos_offset + i] = calc_add + i * calc_mul


class DapsysReaderFunc(SourceFunctionBase):
    def __init__(self, file_path: str | Path, stim_folder: str, main_pulse: Optional[str] = "Main Pulse",
                 continuous_recording: Optional[str] = "Continuous Recording", responses="responses",
                 tracks: Optional[Sequence[str] | str] = "all"):
        self._log = logging.getLogger("DapsysReaderFunc")
        self._file: Optional[File] = None
        self._file_path = file_path
        self._stim_folder = stim_folder
        self._main_pulse = main_pulse
        self._continuous_recording = continuous_recording
        self._responses = responses
        self._tracks = tracks
        self._log.debug("initialized")

    def _load_file(self) -> File:
        self._log.debug("Opening file")
        with open(self._file_path, "rb") as binfile:
            self._log.debug("Parsing file")
            dapsys_file = File.from_binary(binfile)
        return dapsys_file

    @property
    def file(self) -> File:
        if self._file is None:
            self._log.debug("File not loaded yet!")
            self._file = self._load_file()
            self._log.debug("File loaded!")
        return self._file

    def get_continuous_recording(self) -> pd.Series:
        file = self.file
        self._log.debug("processing continuous recording")
        path = f"{self._stim_folder}/{self._continuous_recording}"
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
        return pd.Series(data=values, index=pd.Index(data=timestamps, copy=False, name=TIMESTAMP),
                         name=CONT_REC, copy=False)

    def get_main_pulses(self) -> tuple[pd.Series, dict]:
        file = self.file
        self._log.debug("processing stimuli")
        path = f"{self._stim_folder}/pulses"
        stream: Stream = file.toc.path(path)
        values = np.empty(len(stream.page_ids), dtype=float64)
        lbl_id = np.empty(len(stream.page_ids), dtype=np.uint)
        labels = [""] * len(stream.page_ids)
        counter = dict()
        self._log.debug("reading stimuli")
        id_map = dict()
        for i, page in enumerate(
                file.pages[page_id] for page_id in stream.page_ids):
            page: TextPage
            values[i] = page.timestamp_a
            labels[i] = page.text
            lbl_id[i] = get_and_incr(counter, page.text)
            n = page.id + 1
            while file.pages[n].type != PageType.Waveform:
                n += 1
            id_map[n] = i
        self._log.debug("finished stimuli")
        return pd.Series(data=values, copy=False,
                         index=pd.MultiIndex.from_arrays([np.arange(len(stream.page_ids)), labels, lbl_id],
                                                         names=[GLOBAL_STIM_ID, STIM_LBL, STIM_TYPE_ID]),
                         name=STIM_TS), id_map

    def get_tracks_for_responses(self, idmap: dict) -> pd.Series:
        file = self.file
        self._log.debug("processing tracks")
        tracks: Folder = file.toc.path(f"{self._stim_folder}/{self._responses}")
        all_responses = tracks.f.get("Tracks for all Responses", None)

        if self._tracks is None or all_responses is None:
            if self._tracks is None:
                self._log.info("Should not load any tracks (Tracks is None)")
            else:
                self._log.info("No tracks in file")
            return pd.Series(data=np.array(tuple(), dtype=float64), name=SPIKE_TS,
                             copy=False, index=pd.MultiIndex.from_arrays([[], []],
                                                                         names=(TRACK, TRACK_SPIKE_IDX)))
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
        n = 0
        self._log.info(f"processing streams ({n_responses} responses total)")
        for stream in streams:
            track_labels.extend(stream.name for _ in range(len(stream.page_ids)))
            for i, stim in enumerate(file.pages[page_id] for page_id in stream.page_ids):
                stim: TextPage
                response_timestamps[n] = stim.timestamp_a
                track_response_number[n] = i
                responding_to[n] = idmap[stim.reference_id]
                n += 1
        self._log.debug("streams finished")
        return pd.Series(data=response_timestamps, copy=False, name=SPIKE_TS,
                         index=pd.MultiIndex.from_arrays([responding_to, track_labels, track_response_number],
                                                         names=(GLOBAL_STIM_ID, TRACK, TRACK_SPIKE_IDX)))

    def execute(self) -> tuple[PandasContainer[pd.Series], PandasContainer[pd.Series], PandasContainer[pd.Series]]:
        self._log.info("Executing function")
        self._log.info("Loading continuous recording")
        cont_rec = self.get_continuous_recording()
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
                             TRACK_SPIKE_IDX: pq.dimensionless})
