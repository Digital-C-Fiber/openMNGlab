import numpy as np
from pandas import IntervalDtype
from pandera import Column, Index, DataFrameSchema, SeriesSchema, MultiIndex

from openmnglab.datamodel.pandas.model import PandasDataSchema

TRACK = "track"
SPIKE_TS = "spike_ts"
SPIKE_IDX = "spike_idx"
STIM_IDX = "stim_idx"
STIM_TS = "stim_ts"
STIM_LBL = "stim_label"
RESP_IDX = "resp_idx"
TRACK_SPIKE_IDX = "track_spike_idx"
TIMESTAMP = "timestamp"
SIGNAL = "signal"
TEMPERATURE = "temperature"
MASS = "mass"
CONT_REC = "continuous recording"
GLOBAL_STIM_ID = "global stim id"
STIM_TYPE = "global stim name"
STIM_TYPE_ID = "stime type id"
COMMENT = "comment"


def time_waveform() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(np.float32, index=Index(float)))


def int_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(int, index=Index(int)))


def float_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float, index=Index(float)))


def str_float_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(str, index=Index(float)))


def generic_interval_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(IntervalDtype))


def stimulus_list() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float, index=MultiIndex(
        indexes=[Index(int, name=GLOBAL_STIM_ID), Index(str, name=STIM_TYPE), Index(int, name=STIM_TYPE_ID)]),
                                               name=STIM_TS))


def related_spikes() -> PandasDataSchema[DataFrameSchema]:
    return PandasDataSchema(DataFrameSchema({
        SPIKE_TS: Column(float),
        STIM_IDX: Column(int)
    },
        index=Index(int, name=SPIKE_IDX),
        name="related spikes"))


def sorted_spikes() -> PandasDataSchema[SeriesSchema]:
    return PandasDataSchema(SeriesSchema(float,
                                               index=MultiIndex(
                                                   indexes=[Index(int, name=GLOBAL_STIM_ID), Index(str, name=TRACK),
                                                            Index(int, name=TRACK_SPIKE_IDX)]),
                                               name=SPIKE_TS))
